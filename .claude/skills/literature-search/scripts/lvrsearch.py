#!/usr/bin/env python3
"""Shared helpers for the literature-search skill: a cached, rate-limited,
retrying HTTP client for NCBI E-utilities and OpenAlex; PubMed search-history
expansion (#1, #2 ... lines into one string); DOI / PMID / title
normalisation; and a reader for the Screening tab of the review workbook.

Standard library only. Imported by pubmed_recall.py, snowball.py and
syntax_translate.py; not meant to be run on its own.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
OPENALEX = "https://api.openalex.org/"
TOOL = "lvr-literature-search"
USER_AGENT = "lvr-literature-search/1.0 (systematic review tooling; python-urllib)"

HERE = os.path.dirname(os.path.abspath(__file__))
# .claude/skills/literature-search/scripts -> repo root
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DEFAULT_XLSX = os.path.join(REPO, "data", "LVR_screening_sheet_2.xlsx")
DEFAULT_SCREENING_CSV = os.path.join(REPO, "data", "LVR_screening_sheet_2_Screening.csv")
DEFAULT_STRATEGY_DOC = os.path.join(REPO, "docs", "LVR_search_strategy.md")
WORKBOOK_SCRIPTS = os.path.join(REPO, ".claude", "skills", "screening-workbook", "scripts")


class SearchError(Exception):
    pass


class OfflineMiss(SearchError):
    """Raised in --offline mode when a response is not in the cache."""


def die(msg, code=1):
    sys.stderr.write("error: %s\n" % msg)
    sys.exit(code)


def warn(msg):
    sys.stderr.write("warning: %s\n" % msg)


def contact_email(explicit=None):
    """E-mail for the NCBI `email` and OpenAlex `mailto` parameters. Both
    services ask for one so they can contact you before blocking a misbehaving
    client; neither needs an account."""
    if explicit:
        return explicit
    for var in ("LVR_CONTACT_EMAIL", "NCBI_EMAIL", "OPENALEX_MAILTO"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


# --------------------------------------------------------------------------
# HTTP client with cache, rate limit and retry
# --------------------------------------------------------------------------

class Client:
    """GET/POST JSON with a disk cache keyed on the full request.

    - `cache_dir`: every response is written to <cache_dir>/<sha1>.json with
      the request that produced it, so a run can be replayed offline and the
      eval cases need no network.
    - `offline=True`: never touch the network; a missing entry raises
      OfflineMiss (callers turn that into exit code 2).
    - Rate limit: NCBI allows 3 requests/s without an API key (10 with one);
      OpenAlex asks for <= 10/s and a `mailto`. We keep a per-host minimum
      interval and sleep as needed.
    - Retry: 429 and 5xx and connection errors are retried with exponential
      back-off (1, 2, 4, 8, 16 s); other HTTP errors are raised at once.
    """

    def __init__(self, cache_dir=None, offline=False, email=None, ncbi_api_key=None,
                 openalex_api_key=None, verbose=False, refresh=False):
        self.cache_dir = cache_dir
        self.offline = offline
        self.email = contact_email(email)
        self.ncbi_api_key = ncbi_api_key or os.environ.get("NCBI_API_KEY")
        self.openalex_api_key = openalex_api_key or os.environ.get("OPENALEX_API_KEY")
        self.verbose = verbose
        self.refresh = refresh
        self._last = {}
        self.requests_made = 0
        self.cache_hits = 0
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        if offline and not cache_dir:
            raise SearchError("--offline needs --cache DIR")

    # -- cache ---------------------------------------------------------------
    def _key(self, method, url, params):
        canon = json.dumps([method, url, sorted(params.items())], sort_keys=True)
        return hashlib.sha1(canon.encode("utf-8")).hexdigest()

    def _cache_path(self, key):
        return os.path.join(self.cache_dir, key + ".json")

    def _read_cache(self, key):
        if not self.cache_dir:
            return None
        path = self._cache_path(key)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _write_cache(self, key, method, url, params, data):
        if not self.cache_dir:
            return
        rec = {"method": method, "url": url, "params": self._redact(params),
               "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "data": data}
        tmp = self._cache_path(key) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False)
        os.replace(tmp, self._cache_path(key))

    @staticmethod
    def _redact(params):
        return {k: ("<redacted>" if k in ("api_key", "email", "mailto") else v) for k, v in params.items()}

    # -- rate limit ----------------------------------------------------------
    def _throttle(self, host):
        if host.endswith("nih.gov"):
            interval = 0.11 if self.ncbi_api_key else 0.35
        else:
            interval = 0.12
        last = self._last.get(host, 0.0)
        wait = last + interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    # -- request -------------------------------------------------------------
    def request_json(self, url, params, method="GET", cacheable=True):
        """Return parsed JSON for url+params. Identity parameters (email,
        api keys) are added here and excluded from the cache key."""
        params = {k: v for k, v in params.items() if v is not None}
        key = self._key(method, url, params)
        if cacheable and not self.refresh:
            hit = self._read_cache(key)
            if hit is not None:
                self.cache_hits += 1
                if self.verbose:
                    sys.stderr.write("cache  %s %s\n" % (method, _short(url, params)))
                return hit["data"]
        if self.offline:
            raise OfflineMiss("not in cache (%s): %s %s" % (self.cache_dir, method, _short(url, params)))
        send = dict(params)
        host = urllib.parse.urlsplit(url).netloc
        if host.endswith("nih.gov"):
            send["tool"] = TOOL
            if self.email:
                send["email"] = self.email
            if self.ncbi_api_key:
                send["api_key"] = self.ncbi_api_key
        elif host.endswith("openalex.org"):
            if self.email:
                send["mailto"] = self.email
            if self.openalex_api_key:
                send["api_key"] = self.openalex_api_key
        data = self._fetch(url, send, method)
        if cacheable:
            self._write_cache(key, method, url, params, data)
        return data

    def _fetch(self, url, params, method):
        body = urllib.parse.urlencode(params, doseq=True).encode("utf-8")
        delays = [1, 2, 4, 8, 16]
        attempt = 0
        while True:
            self._throttle(urllib.parse.urlsplit(url).netloc)
            if method == "GET":
                req = urllib.request.Request(url + "?" + body.decode("utf-8"), headers={"User-Agent": USER_AGENT})
            else:
                req = urllib.request.Request(url, data=body, method="POST",
                                             headers={"User-Agent": USER_AGENT,
                                                      "Content-Type": "application/x-www-form-urlencoded"})
            if self.verbose:
                sys.stderr.write("fetch  %s %s\n" % (method, _short(url, params)))
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    raw = resp.read()
                self.requests_made += 1
                try:
                    return json.loads(raw.decode("utf-8"))
                except ValueError:
                    return {"_raw": raw.decode("utf-8", "replace")}
            except urllib.error.HTTPError as e:
                self.requests_made += 1
                retry = e.code == 429 or e.code >= 500
                detail = ""
                try:
                    detail = e.read().decode("utf-8", "replace")[:300]
                except Exception:
                    pass
                if not retry or attempt >= len(delays):
                    raise SearchError("HTTP %s from %s: %s" % (e.code, _short(url, params), detail))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt >= len(delays):
                    raise SearchError("network error for %s: %s" % (_short(url, params), e))
            time.sleep(delays[attempt])
            attempt += 1


def _short(url, params):
    s = url.split("/")[-1] or url
    shown = {k: (v if len(str(v)) < 60 else str(v)[:57] + "...") for k, v in params.items()
             if k not in ("email", "api_key", "mailto", "tool")}
    return "%s %s" % (s, shown)


# --------------------------------------------------------------------------
# NCBI E-utilities
# --------------------------------------------------------------------------

def esearch(client, term, retmax=0, retstart=0, quiet=False):
    """PubMed esearch by POST (long queries are fine). Returns the
    esearchresult dict: count, idlist, querytranslation, warnings."""
    data = client.request_json(EUTILS + "esearch.fcgi",
                               {"db": "pubmed", "term": term, "retmode": "json",
                                "retmax": str(retmax), "retstart": str(retstart)},
                               method="POST")
    res = data.get("esearchresult")
    if res is None:
        raise SearchError("esearch returned no result: %s" % json.dumps(data)[:300])
    if "ERROR" in res:
        raise SearchError("esearch error: %s" % res["ERROR"])
    if not quiet:
        for msg in res.get("errorlist", {}).get("phrasesnotfound", []):
            warn("PubMed phrase not found: %r" % msg)
        for msg in res.get("warninglist", {}).get("outputmessages", []):
            if msg != "No items found.":
                warn("PubMed: %s" % msg)
        for msg in res.get("warninglist", {}).get("quotedphrasenotfound", []):
            warn("PubMed quoted phrase not found: %r" % msg)
    return res


def esummary(client, pmids):
    """PubMed summaries (title, pubdate, source, authors, DOI) for a list of
    PMIDs, in batches of 200 via POST. Returns {pmid: summary}."""
    out = {}
    pmids = [str(p) for p in pmids]
    for i in range(0, len(pmids), 200):
        batch = pmids[i:i + 200]
        data = client.request_json(EUTILS + "esummary.fcgi",
                                   {"db": "pubmed", "id": ",".join(batch), "retmode": "json"},
                                   method="POST")
        result = data.get("result", {})
        for uid in result.get("uids", []):
            rec = result.get(uid, {})
            if "error" in rec:
                continue
            out[uid] = summary_fields(uid, rec)
    return out


def summary_fields(uid, rec):
    doi = ""
    for a in rec.get("articleids", []):
        if a.get("idtype") == "doi":
            doi = norm_doi(a.get("value", ""))
    authors = [a.get("name", "") for a in rec.get("authors", [])]
    year = ""
    m = re.match(r"(\d{4})", rec.get("pubdate", "") or rec.get("epubdate", ""))
    if m:
        year = m.group(1)
    # NCBI Bookshelf records (reports, guidelines) keep their title in booktitle
    title = (rec.get("title") or rec.get("booktitle") or "").strip()
    journal = rec.get("fulljournalname") or rec.get("source") or rec.get("publishername") or ""
    return {"pmid": uid, "title": title, "year": year, "authors": "; ".join(authors),
            "journal": journal, "doi": doi}


def elink(client, pmids, linkname):
    """pubmed -> pubmed links. linkname: pubmed_pubmed_refs (references) or
    pubmed_pubmed_citedin (cited by, PMC-derived). Returns {pmid: [pmids]}."""
    out = {}
    pmids = [str(p) for p in pmids]
    for i in range(0, len(pmids), 50):
        batch = pmids[i:i + 50]
        data = client.request_json(EUTILS + "elink.fcgi",
                                   {"dbfrom": "pubmed", "db": "pubmed", "linkname": linkname,
                                    "id": batch, "retmode": "json"},
                                   method="POST")
        for ls in data.get("linksets", []):
            ids = ls.get("ids", [])
            links = []
            for ldb in ls.get("linksetdbs", []):
                if ldb.get("linkname") == linkname:
                    # retmode=json gives plain id strings; XML-derived dicts have an "id" key
                    links = [str(l["id"] if isinstance(l, dict) else l) for l in ldb.get("links", [])]
            for src in ids:
                out[str(src)] = links
    return out


# --------------------------------------------------------------------------
# PubMed search history expansion
# --------------------------------------------------------------------------

HISTORY_LINE = re.compile(r"^\s*#(\d+)\s+(.*\S)\s*$")
HISTORY_REF = re.compile(r"#(\d+)\b")


def parse_history(text):
    """Return an ordered dict {n: line_text} for lines of the form `#N query`.
    Returns {} if the text is not in history format (then it is one query)."""
    lines = {}
    for line in text.splitlines():
        m = HISTORY_LINE.match(line)
        if m:
            lines[int(m.group(1))] = m.group(2)
    return lines


def expand_history(lines, n, _stack=()):
    """Substitute #k references recursively; each reference becomes a
    parenthesised copy of line k, which is exactly what PubMed does."""
    if n not in lines:
        raise SearchError("search history refers to #%d, which is not defined" % n)
    if n in _stack:
        raise SearchError("search history loops through #%d" % n)

    def sub(m):
        return "(" + expand_history(lines, int(m.group(1)), _stack + (n,)) + ")"
    return HISTORY_REF.sub(sub, lines[n])


def load_query(text):
    """Text is either one query or a `#N` history. Returns (final_query, lines).
    lines is {} for a plain query."""
    lines = parse_history(text)
    if not lines:
        q = " ".join(l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("//"))
        return q, {}
    last = max(lines)
    return expand_history(lines, last), lines


FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)


def query_from_doc(doc_text):
    """The first fenced code block whose lines look like a PubMed history."""
    for block in FENCE.findall(doc_text):
        if parse_history(block):
            return block
    raise SearchError("no fenced code block with #N search-history lines found in the document")


def pmid_tables_from_doc(doc_text):
    """Parse Markdown tables that contain PMIDs. Returns a list of tables,
    each a list of (label, pmid) in document order. In docs/LVR_search_strategy.md
    the first is the key-source table (label = Screening ID) and the second is
    the held-out table (label = paper name)."""
    tables = []
    current = []
    in_table = False
    for line in doc_text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells if c) and cells:
                in_table = True
                continue
            if not in_table:
                in_table = True  # header row
                current = []
                continue
            # pair up label/PMID cells: any cell that is 7-8 digits is a PMID,
            # its label is the cell before it
            for i, c in enumerate(cells):
                if re.fullmatch(r"\d{7,8}", c):
                    label = cells[i - 1] if i > 0 else ""
                    current.append((label, c))
        else:
            if in_table:
                if current:
                    tables.append(current)
                current = []
                in_table = False
    if in_table and current:
        tables.append(current)
    return tables


def read_pmid_list(path):
    """PMIDs from a file: one per line (comments with #), or a CSV with a
    `pmid`/`PMID` column. Returns [(label, pmid)]."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    first = text.splitlines()[0] if text.strip() else ""
    if "," in first and re.search(r"(?i)\bpmid\b", first):
        rows = list(csv.DictReader(text.splitlines()))
        col = next(k for k in rows[0] if k and k.strip().lower() == "pmid")
        lab = next((k for k in rows[0] if k and k.strip().lower() in ("id", "label", "record")), None)
        return [((r.get(lab) or "").strip() if lab else "", r[col].strip()) for r in rows if (r.get(col) or "").strip()]
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = re.split(r"[\s,;]+", line)
        pm = next((p for p in parts if re.fullmatch(r"\d{7,8}", p)), None)
        if pm:
            label = " ".join(p for p in parts if p != pm)
            out.append((label, pm))
    return out


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

def norm_doi(s):
    s = (s or "").strip().lower()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s)
    s = re.sub(r"^doi:\s*", "", s)
    s = s.rstrip(".,;)")
    return s if s.startswith("10.") else ""


def norm_pmid(s):
    s = (s or "").strip()
    s = re.sub(r"^https?://pubmed\.ncbi\.nlm\.nih\.gov/", "", s).strip("/")
    return s if re.fullmatch(r"\d{1,8}", s) else ""


def norm_title(s):
    """Lower-case, accent-stripped, punctuation-free, single-spaced. Used
    for exact matching and for the token-set Jaccard similarity."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_tokens(s):
    return set(norm_title(s).split())


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


# --------------------------------------------------------------------------
# The Screening tab
# --------------------------------------------------------------------------

def load_screening(xlsx=None, csv_path=None):
    """Rows of the Screening tab as dicts with keys id, year, authors, title,
    journal, doi (normalised), url, pmid ('' unless a PMID column exists).

    Reads the xlsx through the screening-workbook skill's lvrwb module (the
    source of truth); falls back to the CSV export, which may be stale."""
    if csv_path and not xlsx:
        return _screening_from_csv(csv_path)
    path = xlsx or DEFAULT_XLSX
    if os.path.exists(path):
        sys.path.insert(0, WORKBOOK_SCRIPTS)
        try:
            import lvrwb  # noqa: E402
        except ImportError:
            lvrwb = None
        if lvrwb is not None:
            wb = lvrwb.Workbook(path)
            grid = wb.grid("Screening", links_as_urls=True)
            header = [h.strip() for h in grid[0]]
            return _rows_from_table(header, grid[1:], "xlsx:" + path)
    if csv_path or os.path.exists(DEFAULT_SCREENING_CSV):
        return _screening_from_csv(csv_path or DEFAULT_SCREENING_CSV)
    raise SearchError("no screening workbook or CSV found (%s)" % path)


def _screening_from_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    lines = text.splitlines(True)
    # exports start with a stem line (the sheet title) before the header
    if lines and "," not in lines[0]:
        lines = lines[1:]
    reader = csv.reader(lines)
    header = [h.strip() for h in next(reader)]
    return _rows_from_table(header, list(reader), "csv:" + path)


def _rows_from_table(header, rows, source):
    idx = {h.lower(): i for i, h in enumerate(header)}

    def get(row, *names):
        for n in names:
            i = idx.get(n.lower())
            if i is not None and i < len(row):
                return (row[i] or "").strip()
        return ""
    out = []
    for row in rows:
        rid = get(row, "ID")
        title = get(row, "Title")
        if not rid and not title:
            continue
        url = get(row, "DOI link", "DOI")
        out.append({"id": rid, "year": get(row, "Year"), "authors": get(row, "Authors"), "title": title,
                    "journal": get(row, "Journal"), "doi": norm_doi(url), "url": url,
                    "pmid": norm_pmid(get(row, "PMID")), "source": source})
    return out


def pmid_map_from_doc(path=None):
    """{screening ID: PMID} from the key-source table of the strategy doc,
    so candidates can be matched by PMID even though the sheet has no PMID
    column. Returns {} if the doc is missing."""
    path = path or DEFAULT_STRATEGY_DOC
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        tables = pmid_tables_from_doc(fh.read())
    if not tables:
        return {}
    return {label: pmid for label, pmid in tables[0] if re.fullmatch(r"\d+", label)}


# --------------------------------------------------------------------------
# misc
# --------------------------------------------------------------------------

def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def today():
    return time.strftime("%Y-%m-%d")
