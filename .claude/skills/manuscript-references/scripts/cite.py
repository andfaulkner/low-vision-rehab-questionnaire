#!/usr/bin/env python3
"""Citation keys -> numbered references for the review manuscript.

    python3 -I cite.py resolve paper/manuscript.md --bib paper/bibliography.json [--manual paper/bibliography_manual.csv]
    python3 -I cite.py render  paper/manuscript.md --bib paper/bibliography.json --style ama
    python3 -I cite.py check   paper/manuscript.md --bib paper/bibliography.json --style ama

Keys in the manuscript look like [@doi:10.1167/tvst.13.9.20], [@pmid:39292468]
or [@aao-vision-rehab-ppp] (a key defined in the manual bibliography CSV);
several in one bracket are separated by semicolons: [@doi:a; @pmid:b].

resolve  fetches metadata for every DOI/PMID key (Crossref for DOIs; NCBI
         esearch/esummary for PMIDs and for the NLM journal abbreviation of
         DOIs) and stores it in the JSON bibliography. Already-cached entries
         are not fetched again unless --refresh. Manual CSV entries are
         loaded every run, so edits there take effect immediately.
render   numbers the keys by first appearance, writes a copy of the
         manuscript with the keys replaced by the style's in-text markers
         (superscript ^1,3-5^ for AMA; [1,3-5] for Vancouver), writes the
         reference list in the chosen style, and prints a report of
         unresolved keys, bibliography entries never cited, and duplicates
         (the same paper cited by DOI and by PMID is merged into one number;
         a manual entry whose DOI is also cited by key is flagged).
check    is render without writing anything; exit 2 when there is a problem.

Everything is deterministic and works offline from the cache; resolve
contacts the network only for keys the cache does not hold (never with
--offline). Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request


def _wopen(path):
    """Open for writing, creating the parent directory first."""
    os.makedirs(os.path.dirname(os.path.abspath(str(path))) or ".", exist_ok=True)
    return open(path, "w", encoding="utf-8")


HERE = os.path.dirname(os.path.abspath(__file__))
STYLE_DIR = os.path.join(os.path.dirname(HERE), "assets", "styles")
CROSSREF = "https://api.crossref.org/works/"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TOOL = "lvr-manuscript-references"
USER_AGENT = "lvr-manuscript-references/1.0 (systematic review tooling; mailto:{mailto})"

KEY_BLOCK = re.compile(r"\[(@[^\]]*)\]")
MANUAL_COLUMNS = ["key", "type", "authors", "title", "container_title", "container_abbrev", "year",
                  "month", "volume", "issue", "pages", "edition", "editors", "publisher", "publisher_place",
                  "doi", "pmid", "url", "published", "updated", "accessed", "text_file", "note"]
ENTRY_TYPES = {"journal", "chapter", "book", "report", "guideline", "web", "preprint", "other"}
CROSSREF_TYPES = {"journal-article": "journal", "book-chapter": "chapter", "book": "book", "monograph": "book",
                  "edited-book": "book", "reference-book": "book", "report": "report", "posted-content": "preprint",
                  "proceedings-article": "journal", "dataset": "other", "other": "other"}


def die(msg, code=1):
    print("error: %s" % msg, file=sys.stderr)
    sys.exit(code)


# ----------------------------------------------------------------------------- keys

def clean_doi(s):
    """Strip URL/'doi:' prefixes but keep the published case (for display)."""
    s = (s or "").strip()
    s = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^doi:\s*", "", s, flags=re.I)
    return s.strip().rstrip(".")


def norm_doi(s):
    """Canonical form for matching: DOIs are case-insensitive."""
    return clean_doi(s).lower()


def clean_text(s):
    """Crossref/PubMed titles: HTML entities, Unicode hyphens and runs of whitespace."""
    s = html.unescape(s or "")
    s = s.replace("‐", "-").replace("‑", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def parse_key(raw):
    """'@doi:10.1/x' -> ('doi', '10.1/x'); '@pmid:12' -> ('pmid', '12'); '@foo' -> ('key', 'foo')."""
    k = raw.strip()
    if not k.startswith("@"):
        return None
    k = k[1:].strip()
    m = re.match(r"^(doi|pmid|key)\s*:\s*(.+)$", k, flags=re.I)
    if m:
        kind, ident = m.group(1).lower(), m.group(2).strip()
    else:
        kind, ident = "key", k
    if kind == "doi":
        ident = norm_doi(ident)
    elif kind == "pmid":
        ident = re.sub(r"\D", "", ident)
    return (kind, ident) if ident else None


def canonical(kind, ident):
    return "%s:%s" % (kind, ident)


def scan_keys(text):
    """Yield (match, [canonical keys]) for each [@...] block in document order."""
    for m in KEY_BLOCK.finditer(text):
        parts = re.split(r";|,(?=\s*@)", m.group(1))
        keys = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            pk = parse_key(p)
            if pk is None:
                keys.append("invalid:%s" % p)
            else:
                keys.append(canonical(*pk))
        yield m, keys


# ----------------------------------------------------------------------------- bibliography

def load_bib(path):
    if not path or not os.path.isfile(path):
        return {"entries": {}, "aliases": {}}
    with open(path, encoding="utf-8") as f:
        bib = json.load(f)
    bib.setdefault("entries", {})
    bib.setdefault("aliases", {})
    return bib


def save_bib(path, bib):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with _wopen(path) as f:
        json.dump(bib, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def split_people(s):
    """'Wu, Yueh-Hsun; Legge, Gordon E' or 'Wu YH, Legge GE' -> [{family, given}]."""
    s = (s or "").strip()
    if not s:
        return []
    out = []
    if ";" in s or ("," in s and re.search(r",\s*[A-Z][a-z]", s)):
        for p in [x.strip() for x in re.split(r";", s) if x.strip()]:
            if re.fullmatch(r"(?i)et\s+al\.?|and others", p):
                continue  # "et al." typed into the CSV is not an author; the style adds it when needed
            if "," in p:
                fam, giv = [x.strip() for x in p.split(",", 1)]
            else:
                bits = p.split()
                fam, giv = (bits[-1], " ".join(bits[:-1])) if len(bits) > 1 else (p, "")
            out.append({"family": fam, "given": giv})
    else:
        for p in [x.strip() for x in s.split(",") if x.strip()]:
            if re.fullmatch(r"(?i)et\s+al\.?|and others", p):
                continue
            bits = p.split()
            if len(bits) > 1 and re.fullmatch(r"[A-Z]{1,4}", bits[-1]):
                out.append({"family": " ".join(bits[:-1]), "given": bits[-1]})
            else:
                out.append({"family": p, "given": ""})
    return out


def load_manual(path):
    """Manual CSV -> {canonical id: entry}; also returns problems."""
    entries, problems = {}, []
    if not path:
        return entries, problems
    if not os.path.isfile(path):
        problems.append("manual bibliography not found: %s" % path)
        return entries, problems
    with open(path, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        missing = [c for c in ("key", "type", "title") if c not in (rd.fieldnames or [])]
        if missing:
            problems.append("manual CSV lacks columns %s (expected %s)" % (missing, MANUAL_COLUMNS))
            return entries, problems
        for i, row in enumerate(rd, start=2):
            key = (row.get("key") or "").strip()
            if not key:
                continue
            if re.match(r"^(doi|pmid)\s*:", key, re.I):
                problems.append("manual row %d: key %r must not start with doi:/pmid: (those are resolved online)" % (i, key))
                continue
            typ = (row.get("type") or "other").strip().lower()
            if typ not in ENTRY_TYPES:
                problems.append("manual row %d (%s): unknown type %r, using 'other' (allowed: %s)" % (i, key, typ, sorted(ENTRY_TYPES)))
                typ = "other"
            e = {k: (row.get(k) or "").strip() for k in MANUAL_COLUMNS if k not in ("authors", "editors", "type", "key")}
            e.update({"id": canonical("key", key), "type": typ, "authors": split_people(row.get("authors")),
                      "editors": split_people(row.get("editors")), "source": "manual"})
            e["doi"] = clean_doi(e.get("doi"))
            if e["id"] in entries:
                problems.append("manual row %d: duplicate key %r" % (i, key))
            entries[e["id"]] = e
    return entries, problems


# ----------------------------------------------------------------------------- fetching

class Fetcher:
    """urllib with per-host politeness, retries on 429/5xx, optional offline mode."""

    def __init__(self, mailto, offline=False, verbose=True):
        self.mailto = mailto or "unset@example.org"
        self.offline = offline
        self.verbose = verbose
        self.last = {}
        self.min_gap = {"api.crossref.org": 0.12, "eutils.ncbi.nlm.nih.gov": 0.4}
        self.calls = 0

    def get_json(self, url, params=None):
        if params:
            url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        if self.offline:
            raise RuntimeError("offline: would fetch %s" % url)
        host = urllib.parse.urlparse(url).netloc
        for attempt in range(4):
            gap = self.min_gap.get(host, 0.2) - (time.monotonic() - self.last.get(host, 0))
            if gap > 0:
                time.sleep(gap)
            self.last[host] = time.monotonic()
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT.format(mailto=self.mailto),
                                                       "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    self.calls += 1
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                    wait = 1.5 * (2 ** attempt)
                    if self.verbose:
                        print("  HTTP %d from %s, retrying in %.1fs" % (e.code, host, wait), file=sys.stderr)
                    time.sleep(wait)
                    continue
                raise RuntimeError("HTTP %d for %s" % (e.code, url))
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < 3:
                    time.sleep(1.5 * (2 ** attempt))
                    continue
                raise RuntimeError("network failure for %s: %s" % (url, e))
        return None


def crossref_entry(msg):
    def first(x):
        return html.unescape(x[0]) if isinstance(x, list) and x else (html.unescape(x) if isinstance(x, str) else "")
    issued = (msg.get("issued") or msg.get("published-print") or msg.get("published-online") or {}).get("date-parts") or [[None]]
    dp = issued[0] if issued and issued[0] else [None]
    authors = [{"family": a.get("family", ""), "given": a.get("given", "")} for a in msg.get("author", []) if a.get("family") or a.get("name")]
    for a, src in zip(authors, [x for x in msg.get("author", []) if x.get("family") or x.get("name")]):
        if not a["family"] and src.get("name"):
            a["family"] = src["name"]
    editors = [{"family": a.get("family", ""), "given": a.get("given", "")} for a in msg.get("editor", []) if a.get("family")]
    typ = CROSSREF_TYPES.get(msg.get("type", ""), "other")
    title = clean_text(first(msg.get("title")))
    e = {"type": typ, "authors": authors, "editors": editors, "title": title,
         "container_title": clean_text(first(msg.get("container-title"))), "container_abbrev": "",
         "year": str(dp[0]) if dp and dp[0] else "", "month": str(dp[1]) if len(dp) > 1 and dp[1] else "",
         "volume": msg.get("volume", "") or "", "issue": msg.get("issue", "") or "", "pages": msg.get("page", "") or "",
         "edition": msg.get("edition-number", "") or "", "publisher": msg.get("publisher", "") or "", "publisher_place": msg.get("publisher-location", "") or "",
         "doi": clean_doi(msg.get("DOI", "")), "pmid": "", "url": msg.get("URL", "") or "", "published": "", "updated": "", "accessed": "",
         "text_file": "", "note": "", "source": "crossref"}
    if not e["pages"] and msg.get("article-number"):
        e["pages"] = str(msg["article-number"])
    return e


def pubmed_entry(doc):
    """esummary (db=pubmed, retmode=json) result document -> entry."""
    authors = []
    for a in doc.get("authors", []):
        nm = a.get("name", "")
        bits = nm.split()
        if len(bits) > 1 and re.fullmatch(r"[A-Z]{1,4}", bits[-1]):
            authors.append({"family": " ".join(bits[:-1]), "given": bits[-1]})
        elif nm:
            authors.append({"family": nm, "given": ""})
    doi = ""
    for aid in doc.get("articleids", []):
        if aid.get("idtype") == "doi":
            doi = clean_doi(aid.get("value"))
    if not doi and str(doc.get("elocationid", "")).lower().startswith("doi:"):
        doi = clean_doi(doc["elocationid"])
    m = re.match(r"(\d{4})(?:\s+([A-Za-z]{3}))?", doc.get("pubdate", "") or doc.get("epubdate", "") or "")
    title = clean_text(doc.get("title", ""))
    return {"type": "journal", "authors": authors, "editors": [], "title": title,
            "container_title": clean_text(doc.get("fulljournalname", "")), "container_abbrev": doc.get("source", "") or "",
            "year": m.group(1) if m else "", "month": (m.group(2) or "") if m else "",
            "volume": doc.get("volume", "") or "", "issue": doc.get("issue", "") or "", "pages": doc.get("pages", "") or "",
            "edition": "", "publisher": "", "publisher_place": "", "doi": doi, "pmid": str(doc.get("uid", "")),
            "url": "", "published": "", "updated": "", "accessed": "", "text_file": "", "note": "", "source": "pubmed"}


def merge_entries(cr, pm):
    """Crossref gives full given names and the publisher's data; PubMed gives the NLM abbreviation and PMID."""
    if cr is None:
        return pm
    if pm is None:
        return cr
    e = dict(cr)
    e["container_abbrev"] = pm.get("container_abbrev") or cr.get("container_abbrev")
    e["pmid"] = pm.get("pmid") or cr.get("pmid")
    if pm.get("doi") and norm_doi(pm["doi"]) == norm_doi(cr.get("doi")):
        e["doi"] = pm["doi"]  # PubMed keeps the publisher's case (e.g. ...707X209835); Crossref lower-cases
    for k in ("volume", "issue", "pages", "year", "title", "container_title"):
        if not e.get(k):
            e[k] = pm.get(k, "")
    if not e.get("authors"):
        e["authors"] = pm.get("authors", [])
    e["source"] = "crossref+pubmed"
    return e


def resolve_keys(keys, bib, fetcher, refresh=False):
    """Fill bib['entries'] / bib['aliases'] for the given canonical keys. Returns list of problems."""
    problems = []
    today = dt.date.today().isoformat()
    for key in keys:
        kind, ident = key.split(":", 1)
        if kind == "key" or kind == "invalid":
            continue
        target = bib["aliases"].get(key, key)
        if target in bib["entries"] and not refresh:
            continue
        try:
            if kind == "doi":
                cr = fetcher.get_json(CROSSREF + urllib.parse.quote(ident, safe=""), {"mailto": fetcher.mailto})
                cr_e = crossref_entry(cr["message"]) if cr and cr.get("message") else None
                pm_e = None
                es = fetcher.get_json(EUTILS + "esearch.fcgi", {"db": "pubmed", "term": "%s[doi]" % ident, "retmode": "json",
                                                                "tool": TOOL, "email": fetcher.mailto})
                ids = ((es or {}).get("esearchresult") or {}).get("idlist") or []
                if len(ids) == 1:
                    sm = fetcher.get_json(EUTILS + "esummary.fcgi", {"db": "pubmed", "id": ids[0], "retmode": "json",
                                                                     "tool": TOOL, "email": fetcher.mailto})
                    doc = ((sm or {}).get("result") or {}).get(ids[0])
                    if doc and norm_doi(next((a["value"] for a in doc.get("articleids", []) if a.get("idtype") == "doi"), "")) == ident:
                        pm_e = pubmed_entry(doc)
                    elif doc:
                        problems.append("%s: PubMed esearch returned PMID %s whose DOI differs; PubMed data ignored" % (key, ids[0]))
                if cr_e is None and pm_e is None:
                    problems.append("%s: not found in Crossref or PubMed" % key)
                    continue
                e = merge_entries(cr_e, pm_e)
                e["id"], e["fetched"] = key, today
                bib["entries"][key] = e
                if e.get("pmid"):
                    bib["aliases"]["pmid:%s" % e["pmid"]] = key
            elif kind == "pmid":
                sm = fetcher.get_json(EUTILS + "esummary.fcgi", {"db": "pubmed", "id": ident, "retmode": "json",
                                                                 "tool": TOOL, "email": fetcher.mailto})
                doc = ((sm or {}).get("result") or {}).get(ident)
                if not doc or doc.get("error"):
                    problems.append("%s: not found in PubMed" % key)
                    continue
                pm_e = pubmed_entry(doc)
                cr_e = None
                if pm_e["doi"]:
                    cr = fetcher.get_json(CROSSREF + urllib.parse.quote(pm_e["doi"], safe=""), {"mailto": fetcher.mailto})
                    cr_e = crossref_entry(cr["message"]) if cr and cr.get("message") else None
                e = merge_entries(cr_e, pm_e)
                e["fetched"] = today
                if e["doi"]:
                    e["id"] = "doi:%s" % norm_doi(e["doi"])
                    bib["entries"][e["id"]] = e
                    bib["aliases"][key] = e["id"]
                else:
                    e["id"] = key
                    bib["entries"][key] = e
            print("  resolved %s -> %s (%s)" % (key, short_label(bib["entries"][bib["aliases"].get(key, key)]), bib["entries"][bib["aliases"].get(key, key)]["source"]), file=sys.stderr)
        except RuntimeError as ex:
            problems.append("%s: %s" % (key, ex))
    return problems


def short_label(e):
    fam = e["authors"][0]["family"] if e.get("authors") else (e.get("publisher") or "Anon")
    return "%s %s" % (fam, e.get("year") or "n.d.")


# ----------------------------------------------------------------------------- styles

def load_style(name_or_path):
    p = name_or_path
    if not os.path.isfile(p):
        p = os.path.join(STYLE_DIR, name_or_path + ".json")
    if not os.path.isfile(p):
        die("style not found: %s (looked in %s)" % (name_or_path, STYLE_DIR))
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def initials(given, style):
    given = re.sub(r"[.]", " ", given or "")
    parts = [p for p in re.split(r"[\s]+", given) if p]
    out = []
    for p in parts:
        sub = [s for s in p.split("-") if s]
        out.append("-".join(s[0].upper() for s in sub) if style.get("keep_hyphen", False) else "".join(s[0].upper() for s in sub))
    sep = style.get("initials_separator", "")
    return sep.join(out) + (style.get("initials_suffix", "") if out else "")


def format_person(p, style):
    fam, giv = p.get("family", ""), p.get("given", "")
    if not giv:
        return fam
    if giv and re.fullmatch(r"[A-Z]{1,4}", giv):
        ini = giv if not style.get("initials_separator") else style["initials_separator"].join(giv)
        ini += style.get("initials_suffix", "")
    else:
        ini = initials(giv, style)
    return ("%s %s" % (fam, ini)).strip() if style.get("family_first", True) else ("%s %s" % (ini, fam)).strip()


def format_people(people, st):
    if not people:
        return ""
    mx, first_n = st.get("max_listed", 6), st.get("list_first_if_more", 3)
    names = [format_person(p, st) for p in people]
    if len(names) > mx:
        names = names[:first_n]
        return st.get("separator", ", ").join(names) + st.get("et_al_separator", ", ") + st.get("et_al", "et al")
    if len(names) == 1:
        return names[0]
    return st.get("separator", ", ").join(names[:-1]) + st.get("final_separator", st.get("separator", ", ")) + names[-1]


PROTECTED = None


def protected_words():
    global PROTECTED
    if PROTECTED is None:
        PROTECTED = set()
        p = os.path.join(os.path.dirname(HERE), "assets", "protected_words.txt")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith("#"):
                        PROTECTED.add(w)
    return PROTECTED


def sentence_case(title):
    """Lower-case a Title Case title, keeping the first word, words after ':' or '?', acronyms,
    words with digits or inner capitals, and words/phrases in assets/protected_words.txt."""
    prot = protected_words()
    for phrase in sorted(prot, key=len, reverse=True):
        if " " in phrase:
            title = re.sub(r"\b%s\b" % re.escape(phrase), lambda m, ph=phrase: ph.replace(" ", "⁠"), title)
    words = title.split(" ")
    out, new_sentence = [], True
    for w in words:
        core = re.sub(r"^[\"'(\[]+|[\"')\]:;,.?!]+$", "", w)
        keep = (new_sentence or core in prot or re.search(r"\d", core) or re.fullmatch(r"[A-Z]{2,}[A-Za-z]*", core)
                or re.search(r"[a-z][A-Z]", core) or re.search(r"[A-Z]-[A-Z]", core) or "⁠" in core
                or core.isupper() or len(core) <= 1 or re.fullmatch(r"[A-Z]\.", core))
        out.append(w if keep else w.lower())
        new_sentence = bool(re.search(r"[:?]$", w))
    return " ".join(out).replace("⁠", " ")


def condense_pages(pages):
    m = re.fullmatch(r"\s*(\d+)\s*[-–—]+\s*(\d+)\s*", pages or "")
    if not m:
        return pages or ""
    a, b = m.group(1), m.group(2)
    if len(b) < len(a) or int(b) < int(a):
        return "%s-%s" % (a, b)
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return "%s-%s" % (a, b[i:] or b[-1])


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def format_date(s, fmt):
    """ISO yyyy-mm-dd (or yyyy-mm, yyyy) -> style date; anything else is returned as given."""
    m = re.fullmatch(r"\s*(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?\s*", s or "")
    if not m:
        return s or ""
    y, mo, d = m.group(1), m.group(2), m.group(3)
    month = MONTHS[int(mo) - 1] if mo else ""
    rep = {"YYYY": y, "Month": month, "Mon": month[:3], "D": str(int(d)) if d else "", "MM": mo or "", "DD": d or ""}
    out = fmt
    for k, v in sorted(rep.items(), key=lambda kv: -len(kv[0])):
        out = out.replace("{%s}" % k, v)
    out = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", out)).strip(" ,")
    return out


def fill_template(tpl, fields):
    """{name} placeholders; [ ... ] groups are dropped when any placeholder inside is empty;
    write \\[ and \\] for literal brackets (Vancouver's [Internet], [cited ...])."""
    def group(m):
        inner = m.group(1)
        names = re.findall(r"\{(\w+)\}", inner)
        if any(not fields.get(n) for n in names):
            return ""
        return re.sub(r"\{(\w+)\}", lambda mm: fields.get(mm.group(1), ""), inner)
    t = tpl.replace("\\[", "\x01").replace("\\]", "\x02")
    out = re.sub(r"\[([^\[\]]*)\]", group, t)
    out = re.sub(r"\{(\w+)\}", lambda mm: fields.get(mm.group(1), ""), out)
    out = out.replace("\x01", "[").replace("\x02", "]")
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\.\s*\.", ".", out)
    return out.strip()


def render_entry(e, style):
    st = style
    typ = e.get("type", "other")
    tpl = st["templates"].get(typ) or st["templates"].get("other")
    ital = "*" if st.get("journal", {}).get("italic", True) else ""
    journal = e.get("container_abbrev") if st.get("journal", {}).get("abbreviate", True) and e.get("container_abbrev") else e.get("container_title", "")
    title = e.get("title", "")
    if st.get("title", {}).get("case") == "sentence" and typ in st.get("title", {}).get("sentence_case_types", ["journal", "chapter"]):
        title = sentence_case(title)
    if st.get("title", {}).get("strip_trailing_period", True):
        title = re.sub(r"\.\s*$", "", title)
    pages = condense_pages(e.get("pages", "")) if st.get("pages", {}).get("condense") else re.sub(r"\s*[–—]\s*", "-", e.get("pages", "") or "")
    eds = e.get("editors") or []
    datefmt = st.get("dates", {}).get("format", "{Month} {D}, {YYYY}")
    fields = {
        "authors": format_people(e.get("authors") or [], st["authors"]),
        "title": title, "journal": (ital + journal + ital) if journal else "",
        "container_title": e.get("container_title", ""), "book_title": (ital + e.get("container_title", "") + ital) if e.get("container_title") else "",
        "year": e.get("year", ""), "month": e.get("month", ""), "volume": e.get("volume", ""), "issue": e.get("issue", ""),
        "pages": pages, "edition": e.get("edition", ""), "editors": format_people(eds, st["authors"]),
        "eds": (st.get("editors", {}).get("plural", "eds") if len(eds) > 1 else st.get("editors", {}).get("single", "ed")) if eds else "",
        "publisher": e.get("publisher", ""), "publisher_place": e.get("publisher_place", ""),
        "doi": e.get("doi", ""), "doi_url": ("https://doi.org/" + e["doi"]) if e.get("doi") else "",
        "pmid": e.get("pmid", ""), "url": e.get("url", "") if typ != "journal" or not e.get("doi") else "",
        "published": format_date(e.get("published", ""), datefmt), "updated": format_date(e.get("updated", ""), datefmt),
        "accessed": format_date(e.get("accessed", ""), datefmt), "note": e.get("note", ""),
    }
    u, acc = fields["updated"], fields["accessed"]
    fields["updated_cited"] = ("updated %s; cited %s" % (u, acc)) if u and acc else (("cited %s" % acc) if acc else (("updated %s" % u) if u else ""))
    if not fields["authors"] and typ in ("web", "guideline", "report", "book") and e.get("publisher"):
        fields["authors"] = e["publisher"]  # organisation as author
    if st.get("doi", {}).get("omit_when_url") and fields["url"]:
        fields["doi"] = fields["doi_url"] = ""
    return fill_template(tpl, fields)


# ----------------------------------------------------------------------------- numbering and rendering

def collapse(nums, style):
    nums = sorted(set(nums))
    sep, dash = style["in_text"].get("separator", ","), style["in_text"].get("range_dash", "-")
    if not style["in_text"].get("collapse_ranges", True):
        return sep.join(str(n) for n in nums)
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i < 2:
            out.extend(str(n) for n in nums[i:j + 1])
        else:
            out.append("%d%s%d" % (nums[i], dash, nums[j]))
        i = j + 1
    return sep.join(out)


def number_keys(text, bib, manual):
    """Return (order: list of canonical ids by first appearance, key->id map, problems, cited_keys)."""
    order, keymap, problems, cited = [], {}, [], []
    for m, keys in scan_keys(text):
        for k in keys:
            cited.append(k)
            if k.startswith("invalid:"):
                problems.append("invalid key %r (expected @doi:..., @pmid:... or @key)" % k[8:])
                continue
            target = bib["aliases"].get(k, k)
            if target not in bib["entries"] and k not in manual:
                target = k
            keymap[k] = target
            if target not in order:
                order.append(target)
    return order, keymap, problems, cited


def entry_for(ident, bib, manual):
    if ident in manual:
        return manual[ident]
    return bib["entries"].get(ident)


def duplicates(order, bib, manual, keymap):
    """Same paper reachable under two numbers: manual entry whose DOI/PMID is also a cited id, or same title+year."""
    notes = []
    by_doi, by_title = {}, {}
    for ident in order:
        e = entry_for(ident, bib, manual)
        if not e:
            continue
        d = norm_doi(e.get("doi"))
        if d:
            if d in by_doi and by_doi[d] != ident:
                notes.append("duplicate: %s and %s share DOI %s; cite one of them" % (by_doi[d], ident, d))
            by_doi.setdefault(d, ident)
        t = re.sub(r"[^a-z0-9]+", " ", (e.get("title") or "").lower()).strip()
        if t:
            k = (t, e.get("year"))
            if k in by_title and by_title[k] != ident:
                notes.append("possible duplicate: %s and %s have the same title and year" % (by_title[k], ident))
            by_title.setdefault(k, ident)
    merged = {}
    for k, ident in keymap.items():
        if k != ident:
            merged.setdefault(ident, []).append(k)
    for ident, ks in sorted(merged.items()):
        notes.append("merged: %s cited as %s (one reference number)" % (ident, ", ".join(sorted(ks))))
    return notes


def render(text, bib, manual, style):
    order, keymap, problems, cited = number_keys(text, bib, manual)
    numbers = {ident: i + 1 for i, ident in enumerate(order)}
    it = style["in_text"]

    def repl(m):
        keys = [k for k in next(ks for mm, ks in scan_keys(m.group(0)))]
        nums = [numbers[keymap[k]] for k in keys if k in keymap]
        if not nums:
            return m.group(0)
        marker = it.get("open", "^") + collapse(nums, style) + it.get("close", "^")
        punct = m.group(2) or ""
        if it.get("after_punctuation", True) and punct:
            return punct + marker
        return marker + punct

    pattern = re.compile(r"\s*(\[@[^\]]*\])([.,;:]?)")
    rendered = pattern.sub(repl, text)

    refs, unresolved = [], []
    for ident in order:
        e = entry_for(ident, bib, manual)
        n = numbers[ident]
        if not e:
            unresolved.append(ident)
            refs.append(style["reference_list"].get("number_format", "{n}. ").format(n=n) + "[UNRESOLVED %s]" % ident)
        else:
            refs.append(style["reference_list"].get("number_format", "{n}. ").format(n=n) + render_entry(e, style))
    uncited = sorted(set(list(bib["entries"].keys()) + list(manual.keys())) - set(order))
    report = {"n_refs": len(order), "unresolved": unresolved, "uncited": uncited, "problems": problems,
              "duplicates": duplicates(order, bib, manual, keymap), "numbers": {ident: numbers[ident] for ident in order},
              "n_citations": len(cited)}
    return rendered, refs, report


def write_refs(path, refs, style, report):
    head = style["reference_list"].get("heading", "## References")
    lines = [head, ""] + refs + [""]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with _wopen(path) as f:
        f.write("\n".join(lines))


def print_report(report, style_name):
    print("style: %s; %d citation(s) -> %d numbered reference(s)" % (style_name, report["n_citations"], report["n_refs"]))
    for p in report["problems"]:
        print("PROBLEM: %s" % p)
    for u in report["unresolved"]:
        print("UNRESOLVED: %s (run `cite.py resolve`, or add it to the manual CSV)" % u)
    for d in report["duplicates"]:
        print("NOTE: %s" % d)
    for u in report["uncited"]:
        print("never cited: %s" % u)
    bad = bool(report["problems"] or report["unresolved"] or any(d.startswith("duplicate") for d in report["duplicates"]))
    return 2 if bad else 0


# ----------------------------------------------------------------------------- CLI

def read_text(path):
    if not os.path.isfile(path):
        die("manuscript not found: %s" % path)
    with open(path, encoding="utf-8") as f:
        return f.read()


def cmd_resolve(a):
    bib = load_bib(a.bib)
    manual, mproblems = load_manual(a.manual)
    keys = []
    for p in a.manuscript:
        for _, ks in scan_keys(read_text(p)):
            keys.extend(ks)
    for k in a.keys or []:
        pk = parse_key(k if k.startswith("@") else "@" + k)
        if pk:
            keys.append(canonical(*pk))
    keys = sorted(set(keys))
    fetcher = Fetcher(a.mailto or os.environ.get("CITE_MAILTO"), offline=a.offline)
    todo = [k for k in keys if k.split(":")[0] in ("doi", "pmid") and (a.refresh or bib["aliases"].get(k, k) not in bib["entries"])]
    print("%d key(s) in manuscript; %d manual; %d to fetch%s" % (len(keys), len(manual), len(todo), " (offline: none fetched)" if a.offline else ""), file=sys.stderr)
    problems = list(mproblems)
    if todo and not a.offline:
        problems += resolve_keys(todo, bib, fetcher, refresh=a.refresh)
        print("%d network call(s)" % fetcher.calls, file=sys.stderr)
    elif todo:
        problems += ["%s: not in cache (offline)" % k for k in todo]
    for k in keys:
        if k.startswith("key:") and k not in manual:
            problems.append("%s: not defined in the manual bibliography CSV%s" % (k, "" if a.manual else " (pass --manual)"))
    save_bib(a.bib, bib)
    print("bibliography: %s (%d entries, %d aliases)" % (a.bib, len(bib["entries"]), len(bib["aliases"])))
    for p in problems:
        print("PROBLEM: %s" % p)
    sys.exit(2 if problems else 0)


def cmd_render(a, dry=False):
    text = read_text(a.manuscript)
    bib = load_bib(a.bib)
    manual, mproblems = load_manual(a.manual)
    style = load_style(a.style)
    rendered, refs, report = render(text, bib, manual, style)
    report["problems"] = mproblems + report["problems"]
    if not dry:
        out_m = a.out_manuscript or os.path.join(os.path.dirname(a.manuscript) or ".", "manuscript_rendered.md")
        out_r = a.out_refs or os.path.join(os.path.dirname(a.manuscript) or ".", "references.md")
        with _wopen(out_m) as f:
            f.write(rendered)
        write_refs(out_r, refs, style, report)
        print("wrote %s and %s" % (out_m, out_r))
        if a.numbering:
            with open(a.numbering, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(["n", "id", "label"])
                for ident, n in sorted(report["numbers"].items(), key=lambda kv: kv[1]):
                    e = entry_for(ident, bib, manual)
                    w.writerow([n, ident, short_label(e) if e else "UNRESOLVED"])
    code = print_report(report, style.get("name", a.style))
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, many=False):
        if many:
            p.add_argument("manuscript", nargs="*", help="manuscript .md file(s) to scan for [@keys]")
        else:
            p.add_argument("manuscript", help="manuscript .md with [@keys]")
        p.add_argument("--bib", default="paper/bibliography.json", help="JSON bibliography cache (default paper/bibliography.json)")
        p.add_argument("--manual", default=None, help="CSV of hand-entered sources (see assets/bibliography_manual_template.csv)")

    p = sub.add_parser("resolve", help="fetch metadata for DOI/PMID keys into the JSON bibliography")
    common(p, many=True)
    p.add_argument("--keys", nargs="*", help="extra keys to resolve, e.g. doi:10.1167/tvst.13.9.20 pmid:39292468")
    p.add_argument("--refresh", action="store_true", help="re-fetch keys already in the cache")
    p.add_argument("--offline", action="store_true", help="never touch the network; report what is missing")
    p.add_argument("--mailto", help="contact e-mail for Crossref/NCBI politeness (or env CITE_MAILTO)")
    p.set_defaults(func=cmd_resolve)

    for name, dry in (("render", False), ("check", True)):
        p = sub.add_parser(name, help="number keys and write the reference list" if not dry else "report problems only")
        common(p)
        p.add_argument("--style", default="ama", help="ama | vancouver | path/to/style.json (default ama)")
        p.add_argument("--out-manuscript", help="rendered manuscript (default <dir>/manuscript_rendered.md)")
        p.add_argument("--out-refs", help="reference list (default <dir>/references.md)")
        p.add_argument("--numbering", help="also write n,id,label CSV (for fact-checking by number)")
        p.set_defaults(func=lambda a, dry=dry: cmd_render(a, dry=dry))

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
