#!/usr/bin/env python3
"""Best-effort translation of a PubMed search string into Scopus syntax, and
a balance checker for either dialect.

    python3 -I syntax_translate.py --query-file pubmed.txt                 # Scopus string to stdout
    python3 -I syntax_translate.py --from-doc docs/LVR_search_strategy.md --report translation_notes.md
    python3 -I syntax_translate.py --query '"low vision"[ti] AND questionnaire*[tiab]'
    python3 -I syntax_translate.py --check-balance --query-file scopus.txt --dialect scopus

THE OUTPUT IS A DRAFT. Field semantics differ between the two databases
(see the report the script prints), so a human must review the string and
run it in Scopus, then compare the record counts and check that the key
sources are retrieved (Scopus has no E-utilities; export the result list
and match DOIs by hand or with snowball.py's de-duplication).

Field tags handled
  [ti]            -> TITLE()
  [tiab]          -> TITLE-ABS() (or --tiab TITLE-ABS-KEY; Scopus has no abstract-only field)
  [tw], [all]     -> TITLE-ABS-KEY()           (approximation; warned)
  [ab]            -> ABS()
  [au]            -> AUTH(),  [ta]/[jour] -> SRCTITLE(),  [pmid]/[uid] -> PMID()
  [la]            -> LANGUAGE() (reported as a LIMIT-TO suggestion)
  [dp]            -> PUBYEAR (ranges 2000:3000 -> PUBYEAR > 1999; single year -> PUBYEAR = N)
  [Mesh], [mh], [Majr], [MeSH Terms], [MeSH Major Topic]
                  -> INDEXTERMS() with a warning: Scopus indexes MeSH for MEDLINE-sourced
                     records only, cannot restrict to major headings, does not explode the
                     tree, and ignores subheadings ("Blindness/rehabilitation" loses /rehabilitation).
  [pt]            -> DOCTYPE() where a code exists (review -> re, editorial -> ed, letter -> le);
                     "Practice Guideline"[pt] and "Guideline"[pt] have no Scopus equivalent
                     and are listed as untranslatable (keep the title terms that accompany them).
  "a b c"[ti:~N]  -> TITLE(a W/N b W/N c)  (PubMed proximity = all words within N extra words,
                     any order; Scopus W/N = pairwise within N words, either order; close but not
                     identical, and chained W/N is evaluated left to right)
  NOT             -> AND NOT, with the reminder that Scopus evaluates AND NOT after every
                     other operator, so it belongs at the end of the string.
  #N history refs -> expanded first (as PubMed does), unless --no-expand.

Untranslated: an untagged term (PubMed would run Automatic Term Mapping on
it) becomes TITLE-ABS-KEY(term) with a warning, because ATM also adds the
MeSH heading and Scopus has nothing like it. Unknown tags are left as-is
and reported, so the string does not silently change meaning. Exit codes:
0 translated (warnings are not failures), 1 parse or balance error.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrsearch as ls  # noqa: E402

TOKEN = re.compile(r"""
    (?P<space>\s+)
  | (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<quoted>"[^"]*")
  | (?P<tag>\[[^\]]*\])
  | (?P<word>[^\s()\[\]"]+)
""", re.X)

FIELD_MAP = {
    "ti": "TITLE", "title": "TITLE",
    "tiab": "TITLE-ABS", "title/abstract": "TITLE-ABS",
    "ab": "ABS", "abstract": "ABS",
    "tw": "TITLE-ABS-KEY", "text word": "TITLE-ABS-KEY", "all": "TITLE-ABS-KEY", "all fields": "TITLE-ABS-KEY",
    "au": "AUTH", "author": "AUTH", "1au": "FIRSTAUTH",
    "ta": "SRCTITLE", "jour": "SRCTITLE", "journal": "SRCTITLE",
    "pmid": "PMID", "uid": "PMID",
    "mesh": "INDEXTERMS", "mh": "INDEXTERMS", "mesh terms": "INDEXTERMS", "majr": "INDEXTERMS",
    "mesh major topic": "INDEXTERMS", "mesh:noexp": "INDEXTERMS", "sh": "INDEXTERMS", "subheading": "INDEXTERMS",
    "la": "LANGUAGE", "lang": "LANGUAGE", "language": "LANGUAGE",
    "dp": "PUBYEAR", "pdat": "PUBYEAR", "publication date": "PUBYEAR",
    "pt": "DOCTYPE", "publication type": "DOCTYPE",
    "kw": "KEY", "ot": "AUTHKEY",
}
MESH_TAGS = {"mesh", "mh", "mesh terms", "majr", "mesh major topic", "mesh:noexp", "sh", "subheading"}
DOCTYPE_CODES = {"review": "re", "editorial": "ed", "letter": "le", "comment": "ed", "erratum": "er",
                 "note": "no", "conference paper": "cp", "book": "bk", "book chapter": "ch", "article": "ar"}
LANG_NAMES = {"english": "English", "french": "French", "spanish": "Spanish", "german": "German",
              "italian": "Italian", "portuguese": "Portuguese", "dutch": "Dutch", "chinese": "Chinese"}


class ParseError(Exception):
    pass


# --------------------------------------------------------------------------
# tokeniser and parser (AST: ('and'|'or', [children]) | ('not', a, b) | term dict)
# --------------------------------------------------------------------------

def tokenize(text):
    toks = []
    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() != pos:
            raise ParseError("unexpected character at %d: %r" % (pos, text[pos:pos + 10]))
        pos = m.end()
        kind = m.lastgroup
        if kind == "space":
            continue
        toks.append((kind, m.group(kind), m.start()))
    if pos != len(text):
        raise ParseError("unexpected character at %d: %r" % (pos, text[pos:pos + 10]))
    return toks


class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None, None)

    def take(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def is_op(self, name):
        k, v, _ = self.peek()
        return k == "word" and v.upper() == name

    def parse(self):
        node = self.parse_or()
        if self.i != len(self.toks):
            k, v, p = self.peek()
            raise ParseError("unexpected %r at %d" % (v, p))
        return node

    # PubMed precedence: left to right; AND, OR, NOT all equal unless
    # parenthesised. We parse NOT and AND tighter than OR (the usual reading
    # of well-formed strings) and warn when an unparenthesised mix appears.
    def parse_or(self):
        items = [self.parse_and()]
        while self.is_op("OR"):
            self.take()
            items.append(self.parse_and())
        return items[0] if len(items) == 1 else ("or", items)

    def parse_and(self):
        items = [self.parse_not()]
        while self.is_op("AND"):
            self.take()
            items.append(self.parse_not())
        return items[0] if len(items) == 1 else ("and", items)

    def parse_not(self):
        node = self.parse_atom()
        while self.is_op("NOT"):
            self.take()
            node = ("not", node, self.parse_atom())
        return node

    def parse_atom(self):
        k, v, p = self.peek()
        if k is None:
            raise ParseError("unexpected end of query")
        if k == "lparen":
            self.take()
            node = self.parse_or()
            k2, _, p2 = self.peek()
            if k2 != "rparen":
                raise ParseError("missing ')' for '(' at %d" % p)
            self.take()
            k3, v3, _ = self.peek()
            if k3 == "tag":  # (a OR b)[ti] is not legal PubMed, but tolerate
                self.take()
                return apply_tag(node, v3)
            return node
        if k == "rparen":
            raise ParseError("unexpected ')' at %d" % p)
        if k in ("quoted", "word"):
            if k == "word" and v.upper() in ("AND", "OR", "NOT"):
                raise ParseError("operator %s with no left operand at %d" % (v, p))
            self.take()
            text = v
            # unquoted multi-word terms before a tag: PubMed treats `visual acuity[tiab]`
            # as a phrase; gather words until a tag or operator
            words = [text]
            while True:
                k2, v2, _ = self.peek()
                if k2 == "word" and v2.upper() not in ("AND", "OR", "NOT") and k == "word":
                    words.append(self.take()[1])
                else:
                    break
            if len(words) > 1:
                text = '"' + " ".join(words) + '"'
            k2, v2, _ = self.peek()
            tag = None
            if k2 == "tag":
                tag = self.take()[1]
            return {"term": text, "tag": tag, "pos": p}
        if k == "tag":
            raise ParseError("field tag %s with no term at %d" % (v, p))
        raise ParseError("cannot parse at %d" % p)


def apply_tag(node, tag):
    if isinstance(node, dict):
        node["tag"] = node["tag"] or tag
        return node
    if node[0] == "not":
        return ("not", apply_tag(node[1], tag), apply_tag(node[2], tag))
    return (node[0], [apply_tag(c, tag) for c in node[1]])


# --------------------------------------------------------------------------
# translation
# --------------------------------------------------------------------------

class Translator:
    def __init__(self, tiab="TITLE-ABS"):
        self.tiab = tiab
        self.warnings = []
        self.untranslatable = []
        self.limits = []  # (field, value) suggestions for LIMIT-TO
        self.proximity = {}  # (tag, N) -> [phrases]
        self.has_not = False

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def split_tag(self, tag):
        inner = tag[1:-1].strip()
        prox = None
        m = re.match(r"^(.*?):~(\d+)$", inner)
        if m:
            inner, prox = m.group(1), int(m.group(2))
        return inner.strip().lower(), prox

    def term(self, t):
        text, tag = t["term"], t["tag"]
        bare = text.strip('"')
        if tag is None:
            self.warn("untagged term %s: PubMed would apply Automatic Term Mapping (MeSH + all fields); "
                      "translated as TITLE-ABS-KEY, which is narrower" % text)
            return ("TITLE-ABS-KEY", self.scopus_term(text))
        name, prox = self.split_tag(tag)
        field = FIELD_MAP.get(name)
        if field is None:
            self.untranslatable.append("unknown field tag %s on %s (left unchanged)" % (tag, text))
            return (None, text + tag)
        if name in MESH_TAGS:
            note = "MeSH term %s%s -> INDEXTERMS: Scopus has MeSH only for MEDLINE-derived records, " \
                   "no major-topic restriction, no tree explosion" % (text, tag)
            if "/" in bare:
                note += "; the subheading after '/' was dropped"
                bare = bare.split("/", 1)[0]
            if name in ("majr", "mesh major topic"):
                note += "; [Majr] becomes a plain index-term match, so expect more records"
            self.warn(note)
            return ("INDEXTERMS", '"%s"' % bare)
        if field == "PUBYEAR":
            return ("PUBYEAR", self.pubyear(bare))
        if field == "LANGUAGE":
            lang = LANG_NAMES.get(bare.lower(), bare.capitalize())
            self.limits.append(("LANGUAGE", lang))
            return ("LANGUAGE", lang.lower())
        if field == "DOCTYPE":
            code = DOCTYPE_CODES.get(bare.lower())
            if code is None:
                self.untranslatable.append('%s[pt] has no Scopus document type; dropped from the Scopus string, '
                                           'keep the title terms that accompany it' % text)
                return (None, None)
            self.warn("%s[pt] -> DOCTYPE(%s): Scopus document types are broader than PubMed publication types" % (text, code))
            return ("DOCTYPE", code)
        if prox is not None:
            words = bare.split()
            if len(words) < 2:
                return (field, self.scopus_term(text))
            chained = (" W/%d " % prox).join(words)
            self.proximity.setdefault((name, prox), []).append(text)
            return (field, chained)
        if field == "TITLE-ABS":
            field = self.tiab
            if self.tiab == "TITLE-ABS-KEY":
                self.warn("[tiab] -> TITLE-ABS-KEY (includes author and index keywords; --tiab TITLE-ABS to exclude them)")
        if field == "TITLE-ABS-KEY" and name in ("tw", "text word", "all", "all fields"):
            self.warn("[%s] -> TITLE-ABS-KEY: PubMed text words cover more fields (e.g. MeSH, substance names)" % name)
        return (field, self.scopus_term(text))

    @staticmethod
    def scopus_term(text):
        # Scopus: quotes = loose phrase (wildcards allowed), braces = exact.
        # Hyphenated phrases are fine in quotes. Single words need no quotes.
        bare = text.strip('"')
        if " " in bare or "-" in bare:
            return '"%s"' % bare
        return bare

    def pubyear(self, bare):
        m = re.fullmatch(r"(\d{4})(?:/\d{1,2}(?:/\d{1,2})?)?:(\d{4})(?:/\d{1,2}(?:/\d{1,2})?)?", bare)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            parts = []
            if lo > 1800:
                parts.append("PUBYEAR > %d" % (lo - 1))
            if hi < 2999:
                parts.append("PUBYEAR < %d" % (hi + 1))
            return " AND ".join(parts) if parts else "PUBYEAR > 1800"
        m = re.fullmatch(r"(\d{4})(?:/\d{1,2}(?:/\d{1,2})?)?", bare)
        if m:
            return "PUBYEAR = %s" % m.group(1)
        self.untranslatable.append("date %s[dp] could not be read; set the date limit in Scopus by hand" % bare)
        return None

    # -- emit ----------------------------------------------------------------
    def emit(self, node, top=False):
        if isinstance(node, dict):
            field, val = self.term(node)
            if val is None:
                return None
            if field is None:
                return val
            if field in ("PUBYEAR",):
                return val
            return "%s(%s)" % (field, val)
        if node[0] == "not":
            self.has_not = True
            left = self.emit(node[1])
            right = self.emit(node[2])
            if right is None:
                return left
            return "%s AND NOT %s" % (left, self.group(right))
        op = node[0].upper()
        parts = []
        # merge runs of same-field simple terms into one FIELD(a OR b)
        run_field, run = None, []

        def flush():
            if run:
                if len(run) == 1:
                    parts.append("%s(%s)" % (run_field, run[0]))
                else:
                    parts.append("%s(%s)" % (run_field, (" %s " % op).join(run)))
        for child in node[1]:
            if isinstance(child, dict):
                field, val = self.term(child)
                if val is None:
                    continue
                if field in (None, "PUBYEAR"):
                    flush(); run_field, run = None, []
                    parts.append(val)
                    continue
                if field == run_field:
                    run.append(val)
                else:
                    flush()
                    run_field, run = field, [val]
            else:
                flush(); run_field, run = None, []
                sub = self.emit(child)
                if sub is not None:
                    parts.append(self.group(sub))
        flush()
        if not parts:
            return None
        return (" %s " % op).join(parts)

    @staticmethod
    def group(s):
        return s if re.fullmatch(r"[A-Z-]+\([^()]*\)", s) else "( %s )" % s


def translate(text, tiab="TITLE-ABS"):
    toks = tokenize(text)
    ast = Parser(toks).parse()
    tr = Translator(tiab)
    out = tr.emit(ast, top=True)
    for (name, prox), phrases in tr.proximity.items():
        shown = ", ".join(phrases[:3]) + (", ... (%d phrases)" % len(phrases) if len(phrases) > 3 else "")
        tr.warn("proximity [%s:~%d] on %s -> %s(w1 W/%d w2 ...): PubMed allows the words in any order within "
                "%d extra words; Scopus W/%d is pairwise and evaluated left to right, and Scopus also accepts "
                "(a OR b) W/%d (c OR d), which is shorter. Check the counts." % (
                    name, prox, shown, FIELD_MAP.get(name, "TITLE"), prox, prox, prox, prox))
    if tr.has_not:
        tr.warn("the string contains NOT: Scopus applies AND NOT after all other operators regardless of "
                "parentheses, so move every AND NOT clause to the very end of the string and check the count")
    if tr.limits:
        langs = sorted({v for f, v in tr.limits if f == "LANGUAGE"})
        if langs:
            tr.warn("language limit: LANGUAGE(%s) works inside the string; Scopus's own form is %s" % (
                " OR ".join(l.lower() for l in langs),
                " OR ".join('LIMIT-TO ( LANGUAGE , "%s" )' % l for l in langs)))
    return out, tr


# --------------------------------------------------------------------------
# balance checker
# --------------------------------------------------------------------------

def check_balance(text, dialect):
    problems = []
    depth, stack = 0, []
    in_quote = False
    in_brace = False
    i = 0
    for i, ch in enumerate(text):
        if ch == '"':
            in_quote = not in_quote
            continue
        if in_quote:
            continue
        if ch == "(":
            stack.append(i)
        elif ch == ")":
            if not stack:
                problems.append("')' at %d has no matching '('" % i)
            else:
                stack.pop()
        elif dialect == "scopus" and ch == "{":
            in_brace = True
        elif dialect == "scopus" and ch == "}":
            if not in_brace:
                problems.append("'}' at %d has no matching '{'" % i)
            in_brace = False
    if in_quote:
        problems.append("unbalanced double quote (odd number of \")")
    for p in stack:
        problems.append("'(' at %d is never closed" % p)
    if dialect == "pubmed":
        opens = text.count("[")
        closes = text.count("]")
        if opens != closes:
            problems.append("square brackets: %d '[' vs %d ']'" % (opens, closes))
        for m in re.finditer(r"\[([^\]]*)\]", text):
            name = m.group(1).split(":")[0].strip().lower()
            if name not in FIELD_MAP and not re.fullmatch(r"[a-z /]+", name):
                problems.append("odd field tag [%s] at %d" % (m.group(1), m.start()))
        lines = ls.parse_history(text)
        if lines:
            for n, body in lines.items():
                for ref in ls.HISTORY_REF.findall(body):
                    if int(ref) not in lines:
                        problems.append("line #%d refers to #%s, which is not defined" % (n, ref))
                    elif int(ref) >= n:
                        problems.append("line #%d refers to #%s, which comes later" % (n, ref))
    else:
        for m in re.finditer(r"\b(W|PRE)/(\d+)\b", text):
            pass
        for m in re.finditer(r"\bNOT\b", text):
            before = text[max(0, m.start() - 4):m.start()].upper()
            if "AND" not in before:
                problems.append("bare NOT at %d: Scopus needs AND NOT" % m.start())
        for m in re.finditer(r"\b(TITLE|TITLE-ABS|TITLE-ABS-KEY|ABS|KEY|INDEXTERMS|AUTH|SRCTITLE|LANGUAGE|DOCTYPE|PMID)\s+\(", text):
            problems.append("space between field %s and '(' at %d (Scopus wants FIELD(...))" % (m.group(1), m.start()))
    for m in re.finditer(r"\b(AND|OR|NOT)\s*$", text.strip()):
        problems.append("string ends with operator %s" % m.group(1))
    for m in re.finditer(r"\(\s*(AND|OR)\b", text):
        problems.append("operator %s directly after '(' at %d" % (m.group(1), m.start()))
    for m in re.finditer(r"\b(AND|OR|NOT)\s+(AND|OR)\b", text):
        problems.append("two operators in a row at %d: %s %s" % (m.start(), m.group(1), m.group(2)))
    return problems


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", help="the string")
    ap.add_argument("--query-file", help="file with the string or a #N history")
    ap.add_argument("--from-doc", metavar="MD", help="take the #N history from the doc's first fenced block")
    ap.add_argument("--line", type=int, help="with a history: translate this line (default last)")
    ap.add_argument("--no-expand", action="store_true", help="do not expand #N references (they are then errors)")
    ap.add_argument("--tiab", default="TITLE-ABS", choices=["TITLE-ABS", "TITLE-ABS-KEY"], help="Scopus field for [tiab]")
    ap.add_argument("--check-balance", action="store_true", help="only check parentheses/quotes/brackets; no translation")
    ap.add_argument("--dialect", default="pubmed", choices=["pubmed", "scopus"], help="dialect for --check-balance")
    ap.add_argument("--report", metavar="FILE", help="write the warnings and untranslatable list as Markdown")
    ap.add_argument("--out", metavar="FILE", help="write the Scopus string here instead of stdout")
    args = ap.parse_args()
    if not (args.query or args.query_file or args.from_doc):
        ap.error("give --query, --query-file or --from-doc")

    if args.query:
        text = args.query
    elif args.query_file:
        text = ls.read_text(args.query_file)
    else:
        text = ls.query_from_doc(ls.read_text(args.from_doc))

    if args.check_balance:
        problems = check_balance(text, args.dialect)
        if problems:
            for p in problems:
                print("PROBLEM: " + p)
            sys.exit(1)
        print("balanced: parentheses, quotes%s ok" % (", field tags and history references" if args.dialect == "pubmed" else ", braces"))
        return

    try:
        lines = {} if args.no_expand else ls.parse_history(text)
        if lines:
            final = ls.expand_history(lines, args.line or max(lines))
        else:
            final, _ = ls.load_query(text)
            if ls.HISTORY_REF.search(final):
                ls.die("the query refers to a search-history line (#N) but no history was given")
        problems = check_balance(final, "pubmed")
        if problems:
            ls.die("the PubMed string is not well formed:\n  " + "\n  ".join(problems))
        scopus, tr = translate(final, args.tiab)
    except (ParseError, ls.SearchError) as e:
        ls.die(str(e))

    header = ("// DRAFT Scopus translation (%s) of a %d-character PubMed string. Review every clause, run it in\n"
              "// Scopus, compare counts with PubMed and check that the key sources are retrieved. See the report.\n"
              % (ls.today(), len(final)))
    body = scopus + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(header + body)
        sys.stderr.write("wrote %s\n" % args.out)
    else:
        sys.stdout.write(header + body)

    rep = ["# Translation report (%s)\n" % ls.today(),
           "PubMed string: %d characters%s. Scopus draft: %d characters. "
           "This translation is automatic and must be reviewed by a person and tested in Scopus "
           "before it is used or reported.\n" % (len(final), " (history expanded)" if lines else "", len(scopus))]
    rep.append("## Constructs that could not be translated (%d)\n" % len(tr.untranslatable))
    rep.extend("- " + u for u in tr.untranslatable) if tr.untranslatable else rep.append("None.")
    rep.append("\n## Warnings: translated, but semantics differ (%d)\n" % len(tr.warnings))
    rep.extend("- " + w for w in tr.warnings) if tr.warnings else rep.append("None.")
    rep.append("\n## Checks to do in Scopus\n")
    rep.append("1. Paste the string into Advanced search; Scopus reports syntax errors inline.\n"
               "2. Put every `AND NOT` clause and the language/date limits at the end.\n"
               "3. Compare the record count with PubMed's; a large gap in either direction points at a field "
               "whose meaning differs (INDEXTERMS, TITLE-ABS-KEY, W/N).\n"
               "4. Export the results (CSV with DOI) and check that the key sources with a DOI are in it; "
               "`snowball.py`'s de-duplication logic, or a DOI join, does this.\n"
               "5. Record the final string, date and count in the search log (PRISMA-S items 8, 13, 15).")
    rep_text = "\n".join(rep) + "\n"
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(rep_text)
        sys.stderr.write("wrote %s\n" % args.report)
    else:
        sys.stderr.write("\n" + rep_text)


if __name__ == "__main__":
    main()
