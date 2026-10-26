#!/usr/bin/env python3
"""Fact-check every numeric claim in the manuscript against its cited sources.

    python3 -I factcheck.py paper/manuscript.md --bib paper/bibliography.json \\
        [--manual paper/bibliography_manual.csv] [--screening data/LVR_screening_sheet_2_Screening.csv] \\
        [--text-dir data/articles_text] [--extraction analysis/extraction] [--prisma paper/prisma_counts.md] \\
        [--map doi:10.1167/iovs.67.1.28="data/articles_text/Wu et al. - 2026 - ....txt"] \\
        --out paper/factcheck_report.md [--json paper/factcheck_report.json]

For each sentence that contains a number (percentages, proportions, n,
sensitivity/specificity/AUC, counts, years) the script records the citation
keys in that sentence (or, failing that, in its paragraph), finds the source
text for each key (key -> DOI -> Screening row -> "<Surname> et al. - <Year>"
file in data/articles_text/, the same matching as the screening-workbook
skill's included.py; manual CSV rows may name a text_file; --map overrides),
and searches the text for the number with nearby key terms from the sentence.
Numbers are compared numerically, so 89% matches 0.89, 55.7 matches 55.71,
and 1,234 matches 1234. Years are checked against the cited entry's
publication year. The same numbers are then compared with the extraction
CSVs (dta.csv, effects.csv, studies.csv: the cited study's rows, column
chosen from the nearest term such as 'sensitivity' or 'AUC') and, for
sentences about records/studies/duplicates, with the PRISMA counts table.

Results per number: FOUND (number in the source near the sentence's key
terms, with page and quote), WEAK (number present but no key term nearby),
NOT FOUND, NO TEXT (no .txt for that source), NO CITATION; and for the CSVs:
MATCH, MISMATCH (value differs from the extraction CSV), or '-' (nothing to
compare). The Markdown report has a blank Verdict column for the reviewer or
a verifier subagent. Exit 0 when nothing needs attention, 2 when any item is
NOT FOUND, MISMATCH, NO CITATION or unresolved, 1 on an input error.
Standard library only; deterministic.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import cite  # noqa: E402  (key parsing, bibliography loading)


def _wopen(path):
    """Open for writing, creating the parent directory first."""
    os.makedirs(os.path.dirname(os.path.abspath(str(path))) or ".", exist_ok=True)
    return open(path, "w", encoding="utf-8")


KEY_BLOCK = re.compile(r"\[@[^\]]*\]")
STOP = set("""a an the and or of in on at to for with by from as is are was were be been that this these those it its
we our they their there here than then which who whom whose what when where how not no nor but so if into onto over under
about after before between among per each both all any some such also only more most less least very can could may might
should would will shall do does did done has have had having one two three four five six seven eight nine ten
study studies paper papers reported report reports found showed shows show using used use versus vs et al however although
whereas while because since respectively total overall among within without across""".split())
HINTS = [  # (regex over sentence, csv column, csv file)
    (r"\bsensitivit", "sens", "dta"), (r"\bspecificit", "spec", "dta"), (r"\bAUCs?\b|area under", "auc", "dta"),
    (r"\bPPV\b|positive predictive", "ppv", "dta"), (r"\bNPV\b|negative predictive", "npv", "dta"),
    (r"\bprevalence", "prevalence", "dta"), (r"\bcorrelat|\br\s*=", "estimate", "effects"),
    (r"\bmean age|\baged\b|\bage\b", "age_mean", "studies"), (r"\bglaucoma", "pct_glaucoma", "studies"),
    (r"\bitems?\b", "n_items", "studies"), (r"\bminutes?\b|\bmin\b", "time_to_administer_min", "studies"),
    (r"\bparticipants|\badults|\bpatients|\bsubjects|\brespondents|\bsample|\bn\s*=|\bN\s*=|\benrol", "n", "studies"),
]
PRISMA_WORDS = re.compile(r"\b(records?|studies|reports?|duplicates?|screened|identified|eligib\w*|full[- ]text|included|excluded|citations?|articles?|papers?|retriev\w*)\b", re.I)
PRISMA_STAGE = [  # (regex over sentence, regex over the prisma_counts.md stage label)
    (r"duplicate", r"^Duplicate records removed"), (r"\bscreened\b", r"^Records screened"),
    (r"excluded.*(title|abstract)|(title|abstract).*excluded", r"^Records excluded at title/abstract"),
    (r"sought|retriev", r"^Reports sought"), (r"not retrieved", r"^Reports not retrieved"),
    (r"assessed|full[- ]text", r"^Reports assessed"), (r"excluded.*full[- ]text|full[- ]text.*excluded", r"^Reports excluded at full text"),
    (r"\bincluded\b", r"^Studies included"), (r"identified", r"identified"),
]
# a sign counts only when it is not glued to a preceding digit, so "115-123" is two positive numbers but "r = -0.76" is negative
NUM = re.compile(r"(?<![\w./])(?P<sign>(?<![\d.\-–])[-−])?(?:(?P<snellen>\d{1,2}/\d{2,4})|(?P<num>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?|\.\d+))(?P<pct>\s?%)?(?![\w/])")
MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE = re.compile(r"\b\d{1,2}\s+%s\b|\b%s\s+\d{1,2}\b" % (MONTHS, MONTHS))
UNITS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
WORDNUM = re.compile(r"\b(?:(%s)(?:[- ](%s))?|(%s))\b" % ("|".join(TENS), "|".join(k for k in UNITS if UNITS[k] < 10), "|".join(UNITS)), re.I)
REFLIKE = re.compile(r"\b(?:19|20)\d{2}\s*;\s*\d+\s*(?:\(\d+\))?\s*:\s*[eE]?\d+(?:\s*[-–]\s*\d+)?")  # 2003;12(3):213-22
DELTA = re.compile(r"\b(increas\w*|decreas\w*|improv\w*|differen\w*|chang\w*|reduc\w*|gain\w*|by at most|by up to|by about|higher|lower)\b", re.I)


def word_value(m):
    if m.group(3):
        return UNITS[m.group(3).lower()]
    v = TENS[m.group(1).lower()]
    if m.group(2):
        v += UNITS[m.group(2).lower()]
    return v


# ----------------------------------------------------------------------------- helpers copied from screening-workbook/scripts/included.py

def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def first_surname(authors):
    a = (authors or "").strip()
    if not a:
        return ""
    head = re.split(r",|;| and | & ", a, maxsplit=1)[0]
    head = re.sub(r"\bet al\.?$", "", head).strip()
    return norm(head)


def parse_filename(fn):
    stem = os.path.splitext(fn)[0]
    parts = [p.strip() for p in stem.split(" - ")]
    authors = parts[0] if parts else ""
    year = next((p for p in parts[1:] if re.fullmatch(r"\d{4}", p)), "")
    title = " - ".join(p for p in parts[1:] if p != year)
    a = re.sub(r"\bet al\.?$", "", authors).strip()
    a = re.split(r" and | & |,", a, maxsplit=1)[0]
    return norm(a), year, norm(title)


def match_file(surname, year, title, files):
    if not surname:
        return ""
    cands = [f for f, (a, y, t) in files.items() if a == surname]
    if year:
        with_year = [f for f in cands if files[f][1] == year]
        cands = with_year or [f for f in cands if not files[f][1]]
    if not cands:
        head = " ".join(norm(title).split()[:6])
        cands = [f for f, (a, y, t) in files.items() if head and t.startswith(head)]
    if len(cands) > 1:
        tn = norm(title)
        cands.sort(key=lambda f: len(os.path.commonprefix([files[f][2], tn])), reverse=True)
    return cands[0] if cands else ""


# ----------------------------------------------------------------------------- inputs

def load_screening(path):
    """DOI -> {id, authors, year, title} from the Screening CSV export (title line, then header)."""
    out = {}
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8", newline="") as f:
        first = f.readline()
        if "," in first and "ID" in first.split(",")[0]:
            f.seek(0)
        rd = csv.DictReader(f)
        for r in rd:
            if not (r.get("ID") or "").strip().isdigit():
                continue
            doi = cite.norm_doi(r.get("DOI link") or r.get("DOI") or "")
            rec = {"id": r["ID"].strip(), "authors": r.get("Authors", ""), "year": (r.get("Year") or "").strip(), "title": r.get("Title", "")}
            if doi and "doi.org" not in doi and "No link" not in (r.get("DOI link") or ""):
                out[doi] = rec
    return out


def load_text_files(text_dir):
    files = {}
    if text_dir and os.path.isdir(text_dir):
        for fn in sorted(os.listdir(text_dir)):
            if fn.lower().endswith(".txt"):
                files[fn] = parse_filename(fn)
    return files


def to_float(s):
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return None


def load_extraction(d):
    """{study_id: {'dta': [rows], 'effects': [rows], 'studies': [rows]}}"""
    out = {}
    if not d or not os.path.isdir(d):
        return out
    for name in ("dta", "effects", "studies"):
        p = os.path.join(d, name + ".csv")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                sid = (r.get("study_id") or "").strip()
                if sid:
                    out.setdefault(sid, {}).setdefault(name, []).append(r)
    return out


def load_prisma(path):
    """Stage label -> int from the `| Stage | n | Detail |` table of prisma_counts.md."""
    counts = {}
    if not path or not os.path.isfile(path):
        return counts
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([\d,]+)\s*\|", line)
            if m and not re.match(r"^-+$", m.group(2)):
                counts[m.group(1).strip()] = int(m.group(2).replace(",", ""))
    return counts


# ----------------------------------------------------------------------------- manuscript parsing

ABBREV = [("et al.", "et al․"), ("e.g.", "e․g․"), ("i.e.", "i․e․"), ("vs.", "vs․"), ("Fig.", "Fig․"),
          ("Dr.", "Dr․"), ("No.", "No․"), ("approx.", "approx․"), ("ca.", "ca․"), ("cf.", "cf․")]
SENT_END = re.compile(r"[.!?](?:[\"')\]]*)(?:\s*\[@[^\]]*\])*(?:[\"')\]]*)(?=\s+(?:[A-Z0-9(\"\[*_“]|\^)|\s*$)")


def split_sentences(par):
    t = par
    for a, b in ABBREV:
        t = t.replace(a, b)
    out, start = [], 0
    for m in SENT_END.finditer(t):
        out.append(t[start:m.end()].strip())
        start = m.end()
    if t[start:].strip():
        out.append(t[start:].strip())
    return [s.replace("․", ".") for s in out if s]


def iter_sentences(text):
    """Yield dicts: section, paragraph index, sentence, paragraph keys."""
    section, in_code, par_idx = "(start)", False, 0
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        b = block.strip()
        if not b:
            continue
        if b.startswith("```"):
            in_code = not in_code if b.count("```") % 2 else in_code
            continue
        if in_code:
            continue
        lines = b.split("\n")
        if re.match(r"^#{1,6}\s", lines[0]):
            section = re.sub(r"^#{1,6}\s+", "", lines[0]).strip()
            lines = lines[1:]
            if not lines:
                continue
        par_idx += 1
        if all(l.strip().startswith("|") for l in lines if l.strip()):
            header = None
            for l in lines:
                if re.match(r"^\|\s*:?-+", l):
                    continue
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
                if header is None:
                    header = cells
                    continue
                # prefix each cell with its column header so "Specificity: 0.81" carries its own hint
                row = " | ".join("%s: %s" % (header[i], c) if i < len(header) and header[i] else c for i, c in enumerate(cells))
                yield {"section": section, "par": par_idx, "sentence": row, "par_keys": par_keys(b), "table": True}
            continue
        par = " ".join(l.strip() for l in lines)
        par = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", par)
        for s in split_sentences(par):
            yield {"section": section, "par": par_idx, "sentence": s, "par_keys": par_keys(b), "table": False}


def par_keys(block):
    keys = []
    for _, ks in cite.scan_keys(block):
        keys.extend(k for k in ks if k not in keys)
    return keys


def strip_keys(s):
    return KEY_BLOCK.sub("", s)


def numbers_in(sentence):
    """Numbers worth checking: list of dicts {raw, value, kind, pos, precision}."""
    s = strip_keys(sentence)
    s = re.sub(r"\(\s*95\s*%\s*(CI|confidence)[^)]*\)", lambda m: " " * len(m.group(0)), s, flags=re.I)
    s = re.sub(r"\b95\s*%\s*(CI|confidence)", lambda m: " " * len(m.group(0)), s, flags=re.I)
    s = re.sub(r"https?://\S+", lambda m: " " * len(m.group(0)), s)
    s = DATE.sub(lambda m: " " * len(m.group(0)), s)  # "4 October", "Oct 4": dates, not claims
    out = []
    if PRISMA_WORDS.search(s) or re.search(r"\b(participants|patients|adults|subjects|respondents|eyes)\b", s, re.I):
        for m in WORDNUM.finditer(s):  # "Twelve studies", "thirty-two patients"
            out.append({"raw": m.group(0), "value": float(word_value(m)), "kind": "count", "pos": m.start(), "precision": 0})
    for m in NUM.finditer(s):
        start = m.start()
        before = s[max(0, start - 2):start]
        if re.search(r"[A-Za-z]-?$", before) or (m.group("sign") and re.search(r"[A-Za-z]$", before)):  # VFQ-25, QUADAS-2, COVID19
            continue
        if m.group("snellen"):
            out.append({"raw": m.group("snellen"), "value": None, "kind": "snellen", "pos": start, "precision": 0})
            continue
        raw = m.group("num")
        val = to_float(raw)
        if val is None:
            continue
        if m.group("sign"):
            val, raw = -val, "-" + raw
        pct = bool(m.group("pct"))
        text_raw = raw + ("%" if pct else "")
        if pct:
            kind = "percent"
        elif re.fullmatch(r"(19|20)\d{2}", raw) and not s[m.end():m.end() + 1] == ".":
            kind = "year"
        elif "." in raw and -1 <= val <= 1:
            kind = "proportion"
        elif "." in raw:
            kind = "decimal"
        else:
            kind = "count"
        prec = len(raw.split(".")[1]) if "." in raw else 0
        if kind == "count" and val < 2 and not re.search(r"\b(n|N)\s*=\s*$", s[max(0, start - 4):start]):
            continue  # "1" and "0" are rarely claims
        out.append({"raw": text_raw, "value": val, "kind": kind, "pos": start, "precision": prec})
    out.sort(key=lambda d: d["pos"])
    return out


def key_terms(sentence):
    s = strip_keys(sentence).lower()
    toks = re.findall(r"[a-z][a-z\-]{3,}", s)
    terms = []
    for t in toks:
        t = t.strip("-")
        if t in STOP or len(t) < 4:
            continue
        stem = re.sub(r"(ies)$", "y", t)
        stem = re.sub(r"(s|ed|ing)$", "", stem) if len(stem) > 5 else stem
        if stem not in terms:
            terms.append(stem)
    return terms


# ----------------------------------------------------------------------------- source texts

class Source:
    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8", errors="replace") as f:
            self.text = f.read()
        self.pages = [(m.start(), int(m.group(1))) for m in re.finditer(r"^\[page (\d+)\]", self.text, flags=re.M)]
        self.low = self.text.lower()
        self.nums = []
        masked = REFLIKE.sub(lambda m: " " * len(m.group(0)), self.text)  # volume(issue):pages in reference lists
        for m in WORDNUM.finditer(masked):
            self.nums.append((m.start(), m.group(0), float(word_value(m)), "num"))
        for m in NUM.finditer(masked):
            if m.group("snellen"):
                self.nums.append((m.start(), m.group("snellen"), None, "snellen"))
            else:
                v = to_float(m.group("num"))
                if v is not None:
                    if m.group("sign"):
                        v = -v
                    self.nums.append((m.start(), m.group("num"), v, "percent" if m.group("pct") else "num"))

    def page_at(self, pos):
        page = None
        for p, n in self.pages:
            if p <= pos:
                page = n
            else:
                break
        return page

    def snippet(self, pos, width=90):
        a, b = max(0, pos - width), min(len(self.text), pos + width)
        s = re.sub(r"\s+", " ", self.text[a:b]).strip()
        return ("..." if a > 0 else "") + s + ("..." if b < len(self.text) else "")

    def find(self, num, terms, window=260):
        """Best hit for a manuscript number: (score, pos, matched terms)."""
        hits = []
        for pos, raw, v, kind in self.nums:
            if not num_equal(num, raw, v, kind):
                continue
            lo, hi = max(0, pos - window), min(len(self.low), pos + window)
            ctx = self.low[lo:hi]
            matched = [t for t in terms if t in ctx]
            hits.append((len(matched), -pos, pos, matched))
        if not hits:
            return None
        hits.sort(reverse=True)
        sc, _, pos, matched = hits[0]
        return sc, pos, matched


def num_equal(num, raw, v, kind):
    if num["kind"] == "snellen":
        return kind == "snellen" and raw == num["raw"]
    if v is None or kind == "snellen":
        return False
    mv = num["value"]
    cands = [mv]
    if num["kind"] == "percent":
        cands.append(mv / 100.0)
    elif num["kind"] == "proportion":
        cands.append(mv * 100.0)
    for c in cands:
        if abs(v - c) < 1e-9:
            return True
        if num["kind"] in ("percent", "proportion", "decimal") and num["precision"] >= 0:
            p = num["precision"] if abs(c - mv) < 1e-9 else (num["precision"] + 2 if num["kind"] == "percent" else max(0, num["precision"] - 2))
            if round(v, p) == round(c, p) and ("." in raw or kind == "percent"):
                return True
    return False


# ----------------------------------------------------------------------------- checks

def csv_compare(num, sentence, rows_by_file):
    """Compare a number with the extraction rows of the cited study. Returns (status, detail)."""
    if not rows_by_file or num["kind"] in ("year", "snellen"):
        return "-", ""
    s = strip_keys(sentence)
    # nearest hint term to the number
    best = None
    for rx, col, fname in HINTS:
        for m in re.finditer(rx, s, flags=re.I):
            d = abs(m.start() - num["pos"])
            if m.start() < num["pos"]:
                d -= 15  # prefer the term that precedes the number
            if best is None or d < best[0]:
                best = (d, col, fname, m.group(0))
    mv = num["value"]
    if num["kind"] == "percent":
        cand_vals = [mv, mv / 100.0]
    elif num["kind"] == "proportion":
        cand_vals = [mv, mv * 100.0]
    else:
        cand_vals = [mv]

    def same(x):
        fx = to_float(x)
        if fx is None:
            return False
        return any(abs(fx - c) < 1e-9 or round(fx, num["precision"] if abs(c - mv) < 1e-9 else max(0, num["precision"] + (2 if num["kind"] == "percent" else -2))) == round(c, num["precision"] if abs(c - mv) < 1e-9 else max(0, num["precision"] + (2 if num["kind"] == "percent" else -2))) for c in cand_vals)

    def any_cell():
        for fname, rows in rows_by_file.items():
            for r in rows:
                for col, v in r.items():
                    if col in ("study_id", "page", "ci_level") or (col in ("year", "n_items") and num["kind"] != "count"):
                        continue
                    if v and v != "NR" and to_float(v) is not None and same(v):
                        return fname, col, v
        return None

    dm = DELTA.search(s[max(0, num["pos"] - 40):num["pos"] + 20])
    if dm and num["kind"] in ("proportion", "decimal", "percent"):
        return "-", "a change/difference ('%s'), not a reported value" % dm.group(0)
    if best and best[0] < 80:
        _, col, fname, term = best
        rows = rows_by_file.get(fname, [])
        vals = [r.get(col, "") for r in rows if r.get(col, "") not in ("", "NR")]
        if vals:
            if any(same(v) for v in vals):
                return "MATCH", "%s.%s = %s (near '%s')" % (fname, col, ", ".join(sorted(set(vals))), term)
            other = any_cell()
            if other:
                return "CHECK", "sentence %s equals %s.%s = %s, but the nearest term '%s' suggests %s.%s = %s" % (
                    num["raw"], other[0], other[1], other[2], term, fname, col, ", ".join(sorted(set(vals))))
            return "MISMATCH", "sentence %s vs %s.%s = %s (near '%s')" % (num["raw"], fname, col, ", ".join(sorted(set(vals))), term)
    other = any_cell()
    if other:
        return "MATCH", "%s.%s = %s" % other
    return "-", "no comparable value in extraction CSVs"


def prisma_compare(num, sentence, counts):
    if not counts or num["kind"] != "count" or not PRISMA_WORDS.search(strip_keys(sentence)):
        return "-", ""
    s = strip_keys(sentence)
    val = int(num["value"])
    for rx, label_rx in PRISMA_STAGE:
        if re.search(rx, s, flags=re.I):
            labels = [k for k in counts if re.search(label_rx, k, flags=re.I)]
            for k in labels:
                if counts[k] == val:
                    return "MATCH", "prisma_counts '%s' = %d" % (k, val)
            if labels and not any(counts[k] == val for k in counts):
                return "MISMATCH", "sentence %d vs prisma_counts %s" % (val, "; ".join("'%s' = %d" % (k, counts[k]) for k in labels))
    for k, v in counts.items():
        if v == val:
            return "MATCH", "equals prisma_counts '%s'" % k
    return "-", "no PRISMA stage with this count"


def resolve_sources(keys, bib, manual, screening, files, text_dir, overrides):
    """key -> {label, study_id, year, file} (file may be '')."""
    out = {}
    for k in keys:
        if k in out:
            continue
        ident = bib["aliases"].get(k, k)
        e = manual.get(ident) or bib["entries"].get(ident)
        doi = cite.norm_doi((e or {}).get("doi") or (ident[4:] if ident.startswith("doi:") else ""))
        rec = screening.get(doi) if doi else None
        info = {"key": k, "id": ident, "label": cite.short_label(e) if e else k, "study_id": rec["id"] if rec else "",
                "year": (e or {}).get("year") or (rec["year"] if rec else ""), "file": "", "how": ""}
        if k in overrides or ident in overrides:
            info["file"], info["how"] = overrides.get(k) or overrides.get(ident), "--map"
        elif e and e.get("text_file"):
            p = e["text_file"] if os.path.isabs(e["text_file"]) else os.path.join(text_dir or "", e["text_file"])
            info["file"], info["how"] = p, "manual CSV text_file"
        elif rec:
            fn = match_file(first_surname(rec["authors"]), rec["year"], rec["title"], files)
            if fn:
                info["file"], info["how"] = os.path.join(text_dir, fn), "Screening ID %s" % rec["id"]
        elif e and e.get("authors"):
            fn = match_file(norm(e["authors"][0].get("family", "")), e.get("year", ""), e.get("title", ""), files)
            if fn:
                info["file"], info["how"] = os.path.join(text_dir, fn), "author+year (not in Screening)"
        if info["file"] and not os.path.isfile(info["file"]):
            info["how"] += " (file missing)"
            info["file"] = ""
        if not e:
            info["how"] = (info["how"] + "; " if info["how"] else "") + "key not in bibliography"
        out[k] = info
    return out


def run(args):
    text = cite.read_text(args.manuscript)
    bib = cite.load_bib(args.bib)
    manual, mproblems = cite.load_manual(args.manual)
    screening = load_screening(args.screening)
    files = load_text_files(args.text_dir)
    extraction = load_extraction(args.extraction)
    prisma = load_prisma(args.prisma)
    overrides = {}
    for m in args.map or []:
        if "=" not in m:
            cite.die("--map expects KEY=FILE, got %r" % m)
        k, p = m.split("=", 1)
        pk = cite.parse_key(k if k.startswith("@") else "@" + k)
        overrides[cite.canonical(*pk) if pk else k] = p

    all_keys = []
    for _, ks in cite.scan_keys(text):
        all_keys.extend(k for k in ks if k not in all_keys)
    sources = resolve_sources(all_keys, bib, manual, screening, files, args.text_dir, overrides)
    cache = {}

    def source_obj(path):
        if path not in cache:
            cache[path] = Source(path)
        return cache[path]

    items, n_id = [], 0
    for sent in iter_sentences(text):
        nums = numbers_in(sent["sentence"])
        if not nums:
            continue
        own = [k for _, ks in cite.scan_keys(sent["sentence"]) for k in ks]
        keys, inherited = (own, False) if own else (sent["par_keys"], bool(sent["par_keys"]))
        terms = key_terms(sent["sentence"])
        rows_by_file = {}
        for k in keys:
            sid = sources.get(k, {}).get("study_id")
            if sid and sid in extraction:
                for fname, rows in extraction[sid].items():
                    rows_by_file.setdefault(fname, []).extend(rows)
        for num in nums:
            if num["kind"] == "year" and not keys:
                continue  # a date in an uncited sentence (search date, protocol date) is not a claim about a source
            n_id += 1
            item = {"n": n_id, "section": sent["section"], "sentence": sent["sentence"], "number": num["raw"], "kind": num["kind"],
                    "keys": keys, "inherited": inherited, "source": "", "text_status": "", "evidence": "", "page": None,
                    "csv_status": "-", "csv_detail": "", "prisma_status": "-", "prisma_detail": "", "verdict": ""}
            if not keys:
                item["text_status"] = "NO CITATION"
            else:
                best = None
                for k in keys:
                    info = sources[k]
                    if num["kind"] == "year" and info.get("year") and int(num["value"]) == int(info["year"]):
                        best = ("FOUND", "publication year of %s" % info["label"], None, info["label"])
                        break
                    if not info["file"]:
                        cand = ("NO TEXT", info["how"] or "no text file", None, info["label"])
                    else:
                        src = source_obj(info["file"])
                        hit = src.find(num, terms)
                        if hit is None:
                            cand = ("NOT FOUND", "%s not in %s" % (num["raw"], os.path.basename(info["file"])), None, info["label"])
                        else:
                            sc, pos, matched = hit
                            status = "FOUND" if sc >= 1 else "WEAK"
                            cand = (status, "p%s: \"%s\" [terms: %s]" % (src.page_at(pos), src.snippet(pos), ", ".join(matched) or "none"), src.page_at(pos), info["label"])
                    rank = {"FOUND": 3, "WEAK": 2, "NOT FOUND": 1, "NO TEXT": 0}
                    if best is None or rank[cand[0]] > rank[best[0]]:
                        best = cand
                item["text_status"], item["evidence"], item["page"], item["source"] = best
                if inherited:
                    item["evidence"] = "(paragraph citation) " + item["evidence"]
            item["csv_status"], item["csv_detail"] = csv_compare(num, sent["sentence"], rows_by_file)
            item["prisma_status"], item["prisma_detail"] = prisma_compare(num, sent["sentence"], prisma)
            if not keys and item["prisma_status"] == "MATCH":
                # a flow count in the Methods has no source to cite; prisma_counts.md is its source
                item["text_status"], item["evidence"] = "COUNTS", item["prisma_detail"]
            items.append(item)

    unresolved = [k for k, s in sources.items() if "not in bibliography" in s["how"]]
    write_report(args, items, sources, unresolved, mproblems, {"screening": len(screening), "files": len(files),
                                                              "extraction": len(extraction), "prisma": len(prisma)})
    if args.json:
        with _wopen(args.json) as f:
            json.dump({"manuscript": args.manuscript, "items": items, "sources": sources, "unresolved_keys": unresolved}, f, indent=1, ensure_ascii=False)
            f.write("\n")
    attention = [i for i in items if i["text_status"] in ("NOT FOUND", "NO CITATION") or "MISMATCH" in (i["csv_status"], i["prisma_status"])]
    counts = {}
    for i in items:
        counts[i["text_status"]] = counts.get(i["text_status"], 0) + 1
    print("%d numeric claim(s): %s; CSV mismatches %d; PRISMA mismatches %d; unresolved keys %d -> %s" % (
        len(items), ", ".join("%s %d" % kv for kv in sorted(counts.items())),
        sum(i["csv_status"] == "MISMATCH" for i in items), sum(i["prisma_status"] == "MISMATCH" for i in items), len(unresolved), args.out))
    sys.exit(2 if attention or unresolved or mproblems else 0)


def md_cell(s, limit=320):
    s = re.sub(r"\s+", " ", str(s)).replace("|", "\\|")
    return s if len(s) <= limit else s[:limit - 3] + "..."


def write_report(args, items, sources, unresolved, mproblems, avail):
    L = ["# Fact-check report", "",
         "Manuscript: `%s`. Generated %s by factcheck.py. Inputs: bibliography `%s`; Screening rows with DOI %d; text files %d; extraction studies %d; PRISMA counts %d."
         % (args.manuscript, dt.date.today().isoformat(), args.bib, avail["screening"], avail["files"], avail["extraction"], avail["prisma"]), "",
         "Text check: FOUND = the number occurs in the cited source near the sentence's key terms (a FOUND is still only a string match: read the quote); WEAK = the number occurs but none of the key terms are nearby; NOT FOUND = the number does not occur in the source text (the claim is unsupported, or the number was rounded or derived: quote the source or mark NOT SUPPORTED); NO TEXT = no .txt for that source; NO CITATION = numeric claim without a key in its sentence or paragraph; COUNTS = an uncited flow count that matches prisma_counts.md. CSV: MATCH / MISMATCH against the extraction CSVs for the cited study, CHECK = equals a different column than the nearest term suggests. PRISMA: MATCH / MISMATCH against prisma_counts.md. Fill the Verdict column (OK / FIX: ... / NOT SUPPORTED) when verifying.", ""]
    counts = {}
    for i in items:
        counts[i["text_status"]] = counts.get(i["text_status"], 0) + 1
    L += ["## Summary", "", "| Status | n |", "|---|---:|"] + ["| %s | %d |" % kv for kv in sorted(counts.items())]
    L += ["| CSV MATCH / CHECK / MISMATCH | %d / %d / %d |" % (sum(i["csv_status"] == "MATCH" for i in items), sum(i["csv_status"] == "CHECK" for i in items), sum(i["csv_status"] == "MISMATCH" for i in items)),
          "| PRISMA MATCH / MISMATCH | %d / %d |" % (sum(i["prisma_status"] == "MATCH" for i in items), sum(i["prisma_status"] == "MISMATCH" for i in items)), ""]
    if mproblems:
        L += ["Manual bibliography problems:", ""] + ["- %s" % p for p in mproblems] + [""]
    if unresolved:
        L += ["Keys cited but not in the bibliography (run `cite.py resolve`):", ""] + ["- %s" % k for k in unresolved] + [""]
    L += ["## Sources", "", "| Key | Label | Screening ID | Text file | Matched by |", "|---|---|---|---|---|"]
    for k, s in sources.items():
        L.append("| %s | %s | %s | %s | %s |" % (md_cell(k), md_cell(s["label"]), s["study_id"] or "-", md_cell(os.path.basename(s["file"]) if s["file"] else "-"), md_cell(s["how"] or "-")))
    L += ["", "## Items", "", "| # | Section | Sentence | Number | Keys | Text check | Evidence | CSV | PRISMA | Verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    for i in items:
        csvs = i["csv_status"] + (": " + i["csv_detail"] if i["csv_detail"] and i["csv_status"] != "-" else "")
        pr = i["prisma_status"] + (": " + i["prisma_detail"] if i["prisma_detail"] and i["prisma_status"] != "-" else "")
        L.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            i["n"], md_cell(i["section"], 40), md_cell(strip_keys(i["sentence"])), md_cell(i["number"]), md_cell(", ".join(i["keys"]) + (" (par.)" if i["inherited"] and i["keys"] else ""), 120),
            i["text_status"], md_cell(i["evidence"]), md_cell(csvs, 160), md_cell(pr, 120), i["verdict"]))
    todo = [i for i in items if i["text_status"] in ("NOT FOUND", "WEAK", "NO TEXT", "NO CITATION") or i["inherited"]
            or i["csv_status"] in ("MISMATCH", "CHECK") or i["prisma_status"] == "MISMATCH"]
    L += ["", "## To verify by hand or by a verifier subagent", ""]
    if not todo:
        L.append("Nothing: every number was found near its key terms and agrees with the CSVs.")
    for i in todo:
        src = [sources[k] for k in i["keys"] if k in sources]
        where = "; ".join("%s -> %s" % (s["label"], os.path.relpath(s["file"]) if s["file"] else "no text") for s in src) or "no citation"
        why = i["text_status"] + ("; paragraph citation, confirm it covers this sentence" if i["inherited"] and i["keys"] else "")
        if i["csv_status"] in ("MISMATCH", "CHECK"):
            why += "; CSV %s" % i["csv_status"]
        if i["prisma_status"] == "MISMATCH":
            why += "; PRISMA MISMATCH"
        L.append("- item %d (%s; %s): number **%s** in \"%s\" | sources: %s" % (i["n"], why, i["section"], i["number"], md_cell(strip_keys(i["sentence"]), 200), where))
    L.append("")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with _wopen(args.out) as f:
        f.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manuscript", help="manuscript .md with [@keys] (the source, not the rendered copy)")
    ap.add_argument("--bib", default="paper/bibliography.json")
    ap.add_argument("--manual", default=None, help="manual bibliography CSV (may name a text_file per entry)")
    ap.add_argument("--screening", default="data/LVR_screening_sheet_2_Screening.csv", help="Screening tab export (DOI -> ID, author, year)")
    ap.add_argument("--text-dir", default="data/articles_text", help="folder of full-text .txt files with [page N] markers")
    ap.add_argument("--extraction", default="analysis/extraction", help="folder holding dta.csv, effects.csv, studies.csv")
    ap.add_argument("--prisma", default="paper/prisma_counts.md", help="prisma_counts.md from the prisma-reporting skill")
    ap.add_argument("--map", nargs="*", metavar="KEY=FILE", help="force a source text for a key, e.g. doi:10.1/x=path.txt")
    ap.add_argument("--out", default="paper/factcheck_report.md")
    ap.add_argument("--json", help="also write the items as JSON (for a verifier subagent)")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
