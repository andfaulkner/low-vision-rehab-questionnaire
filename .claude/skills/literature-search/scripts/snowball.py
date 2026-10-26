#!/usr/bin/env python3
"""Citation snowballing: backward references and forward citations of a set
of seed papers (normally the included studies), counted, de-duplicated
against the Screening tab, and written to candidates.csv.

    python3 -I snowball.py --included --out analysis/search/snowball --cache analysis/search/cache
    python3 -I snowball.py --doi 10.1167/tvst.13.9.20 --pmid 25052992 --out OUT --cache C
    python3 -I snowball.py --seeds seeds.txt --min-links 2 --out OUT --cache C --offline
    python3 -I snowball.py --included analysis/included.csv --ncbi --out OUT --cache C

Seeds: --doi / --pmid (repeatable), --seeds FILE (one DOI or PMID per line,
or a CSV with doi/DOI/pmid columns), or --included [CSV] which runs the
screening-workbook skill's included.py (or reads its saved output) and
takes every record's DOI.

Sources: OpenAlex (works/doi:..., works/pmid:..., referenced_works and
filter=cites:) by default; NCBI elink (pubmed_pubmed_refs,
pubmed_pubmed_citedin) for seeds OpenAlex cannot resolve, or for all seeds
with --ncbi. NCBI's cited-by only covers PubMed Central full texts, so it
is the fallback, not the first choice. OpenAlex needs no key, but without
one all callers on the same IP share a small daily budget; set
$OPENALEX_API_KEY (free) if runs start failing with HTTP 429.

De-duplication against the Screening tab (read from the xlsx through the
screening-workbook skill's lvrwb module, so the stale CSV export cannot
mislead): a candidate is already in the review if its DOI matches, its PMID
matches a key-source PMID from docs/LVR_search_strategy.md, or its
normalised title (lower-case, accents and punctuation removed) is identical
or has token-set Jaccard >= 0.85 with a sheet title (--title-threshold).
Jaccard 0.60-0.85 is flagged as a possible duplicate but kept, for the
screener to judge. Candidates are also merged with each other on
OpenAlex id, DOI and PMID.

Output (in --out DIR): candidates.csv sorted by times_linked then year
(columns: doi, pmid, year, authors, title, journal, abstract, times_linked,
link_type, source_ids, openalex_id, cited_by_count, status, matched_id),
excluded.csv (the candidates dropped as duplicates, with the reason), and
snowball_log.json (date, seeds, per-seed link counts, totals) for the
PRISMA-S search log and the flow diagram's "citation searching" box.

--min-links N keeps candidates linked from at least N seeds. The usual
rule: screen the 2+ group first (a paper cited by, or citing, two included
studies is far more likely to be relevant), then decide whether the 1-link
tail is worth screening given its size. Exit codes: 0 ok, 1 error,
2 offline cache miss.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrsearch as ls  # noqa: E402

OA_SELECT = "id,doi,ids,title,display_name,publication_year,authorships,primary_location,cited_by_count,referenced_works,abstract_inverted_index,type"
OA_SELECT_LITE = "id,doi,ids,title,display_name,publication_year,authorships,primary_location,cited_by_count,abstract_inverted_index,type"


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = ap.add_argument_group("seeds")
    s.add_argument("--doi", action="append", default=[], help="seed DOI (repeatable)")
    s.add_argument("--pmid", action="append", default=[], help="seed PMID (repeatable)")
    s.add_argument("--seeds", metavar="FILE", help="DOIs/PMIDs one per line, or CSV with doi/pmid columns")
    s.add_argument("--included", nargs="?", const="__run__", metavar="CSV",
                   help="seeds = the included set: run screening-workbook's included.py, or read its CSV")
    s.add_argument("--stage", default="any", choices=["any", "ta", "ft"], help="included.py --stage (default any)")
    d = ap.add_argument_group("direction and source")
    d.add_argument("--direction", default="both", choices=["both", "backward", "forward"])
    d.add_argument("--ncbi", action="store_true", help="use NCBI elink for every seed, not only as fallback")
    d.add_argument("--no-ncbi", action="store_true", help="never fall back to NCBI elink")
    d.add_argument("--max-citers", type=int, default=1000, help="cap on forward citations fetched per seed (default 1000)")
    x = ap.add_argument_group("de-duplication")
    x.add_argument("--xlsx", help="screening workbook (default data/LVR_screening_sheet_2.xlsx)")
    x.add_argument("--screening-csv", help="use this Screening CSV export instead of the xlsx")
    x.add_argument("--no-screening", action="store_true", help="do not de-duplicate against the Screening tab")
    x.add_argument("--pmid-map", metavar="MD", help="strategy doc with the ID/PMID table (default docs/LVR_search_strategy.md)")
    x.add_argument("--title-threshold", type=float, default=0.85, help="Jaccard at or above which titles match (default 0.85)")
    x.add_argument("--possible-threshold", type=float, default=0.60, help="Jaccard at or above which a match is flagged (default 0.60)")
    x.add_argument("--keep-dupes", action="store_true", help="keep duplicates in candidates.csv with their status")
    f = ap.add_argument_group("filters")
    f.add_argument("--min-links", type=int, default=1, help="keep candidates linked from at least N seeds (default 1)")
    f.add_argument("--since", type=int, help="drop candidates published before this year")
    f.add_argument("--no-abstracts", action="store_true", help="leave the abstract column empty (smaller file)")
    n = ap.add_argument_group("network")
    n.add_argument("--cache", metavar="DIR", help="cache every response here (replayable with --offline)")
    n.add_argument("--offline", action="store_true", help="use the cache only; exit 2 on a miss")
    n.add_argument("--refresh", action="store_true", help="ignore cached responses and fetch again")
    n.add_argument("--email", help="contact e-mail for NCBI/OpenAlex (default: $LVR_CONTACT_EMAIL / git user.email)")
    n.add_argument("--openalex-key", help="OpenAlex API key (default $OPENALEX_API_KEY)")
    n.add_argument("--ncbi-key", help="NCBI API key (default $NCBI_API_KEY)")
    n.add_argument("--verbose", action="store_true")
    ap.add_argument("--out", required=True, metavar="DIR", help="output directory (e.g. analysis/search/snowball)")
    args = ap.parse_args()
    if not (args.doi or args.pmid or args.seeds or args.included):
        ap.error("give seeds: --doi, --pmid, --seeds FILE or --included")
    return args


# --------------------------------------------------------------------------
# seeds
# --------------------------------------------------------------------------

def collect_seeds(args):
    """[(label, doi, pmid)] in input order, de-duplicated."""
    seeds = []
    for d in args.doi:
        seeds.append(("", ls.norm_doi(d), ""))
    for p in args.pmid:
        seeds.append(("", "", ls.norm_pmid(p)))
    if args.seeds:
        seeds.extend(read_seed_file(args.seeds))
    if args.included:
        seeds.extend(included_seeds(args))
    out, seen = [], set()
    for label, doi, pmid in seeds:
        if not doi and not pmid:
            ls.warn("seed %r has neither a DOI nor a PMID; skipped" % (label,))
            continue
        key = doi or ("pmid:" + pmid)
        if key in seen:
            continue
        seen.add(key)
        out.append((label, doi, pmid))
    return out


def read_seed_file(path):
    text = ls.read_text(path)
    first = text.splitlines()[0] if text.strip() else ""
    if "," in first and re.search(r"(?i)\b(doi|pmid)\b", first):
        return seeds_from_rows(list(csv.DictReader(text.splitlines())))
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        doi = pmid = ""
        label = ""
        for p in parts:
            if ls.norm_doi(p):
                doi = ls.norm_doi(p)
            elif re.fullmatch(r"\d{7,8}", p):
                pmid = p
            else:
                label = (label + " " + p).strip()
        out.append((label, doi, pmid))
    return out


def seeds_from_rows(rows):
    out = []
    for r in rows:
        low = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        doi = ls.norm_doi(low.get("doi") or low.get("doi link") or "")
        pmid = ls.norm_pmid(low.get("pmid") or "")
        label = low.get("id") or low.get("label") or ""
        if not label and low.get("authors"):
            label = low["authors"].split(",")[0] + " " + low.get("year", "")
        out.append((label, doi, pmid))
    return out


def included_seeds(args):
    if args.included == "__run__":
        script = os.path.join(ls.WORKBOOK_SCRIPTS, "included.py")
        cmd = [sys.executable, "-I", script, "--stage", args.stage]
        if args.xlsx:
            cmd += ["--xlsx", args.xlsx]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ls.REPO)
        if res.returncode != 0:
            ls.die("included.py failed: %s" % res.stderr.strip())
        sys.stderr.write(res.stderr)
        rows = list(csv.DictReader(res.stdout.splitlines()))
    else:
        rows = list(csv.DictReader(ls.read_text(args.included).splitlines()))
    if not rows:
        ls.die("the included set is empty (screening not done yet?); give --doi/--pmid/--seeds instead")
    seeds = seeds_from_rows(rows)
    sys.stderr.write("included set: %d record(s), %d with a DOI or PMID\n" % (len(rows), sum(1 for s in seeds if s[1] or s[2])))
    return seeds


# --------------------------------------------------------------------------
# OpenAlex
# --------------------------------------------------------------------------

def oa_work(client, doi="", pmid=""):
    ident = ("doi:" + doi) if doi else ("pmid:" + pmid)
    try:
        return client.request_json(ls.OPENALEX + "works/" + ident, {"select": OA_SELECT})
    except ls.SearchError as e:
        if "HTTP 404" in str(e):
            return None
        raise


def oa_batch(client, ids, select=OA_SELECT_LITE):
    """Fetch works by OpenAlex id, 50 per request. Returns {id: work}."""
    out = {}
    ids = sorted(set(ids))
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        data = client.request_json(ls.OPENALEX + "works",
                                   {"filter": "openalex:" + "|".join(w.rsplit("/", 1)[-1] for w in batch),
                                    "per-page": "50", "select": select})
        for w in data.get("results", []):
            out[w["id"]] = w
    return out


def oa_citers(client, work_id, cap):
    """Works citing work_id. Page-based paging (page=1,2,...) is used because
    cursor paging needs an API key; pages reach 10,000 results, far beyond
    --max-citers for any paper this review would seed from."""
    out = []
    page = 1
    wid = work_id.rsplit("/", 1)[-1]
    while len(out) < cap:
        data = client.request_json(ls.OPENALEX + "works",
                                   {"filter": "cites:" + wid, "per-page": "200", "page": str(page),
                                    "select": OA_SELECT_LITE})
        results = data.get("results", [])
        out.extend(results)
        total = (data.get("meta") or {}).get("count") or 0
        if not results or len(out) >= total or page >= 50:
            break
        page += 1
    if total > cap:
        ls.warn("%s has %d citing works; only the first %d (OpenAlex default order) were fetched; raise --max-citers to get all" % (wid, total, cap))
    return out[:cap]


def oa_fields(w):
    ids = w.get("ids") or {}
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    authors = []
    for a in w.get("authorships") or []:
        name = (a.get("author") or {}).get("display_name")
        if name:
            authors.append(name)
    return {"openalex_id": w.get("id", ""), "doi": ls.norm_doi(w.get("doi") or ids.get("doi") or ""),
            "pmid": ls.norm_pmid(ids.get("pmid") or ""), "year": str(w.get("publication_year") or ""),
            "authors": "; ".join(authors), "title": (w.get("title") or w.get("display_name") or "").strip(),
            "journal": src.get("display_name") or "", "abstract": inverted_to_text(w.get("abstract_inverted_index")),
            "cited_by_count": w.get("cited_by_count") or 0, "type": w.get("type") or ""}


def inverted_to_text(inv):
    if not inv:
        return ""
    pos = []
    for word, places in inv.items():
        for p in places:
            pos.append((p, word))
    pos.sort()
    return " ".join(w for _, w in pos)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    args = parse_args()
    try:
        client = ls.Client(cache_dir=args.cache, offline=args.offline, email=args.email,
                           ncbi_api_key=args.ncbi_key, openalex_api_key=args.openalex_key,
                           verbose=args.verbose, refresh=args.refresh)
        seeds = collect_seeds(args)
        if not seeds:
            ls.die("no usable seeds")
        cands, log = gather(client, args, seeds)
        screening = [] if args.no_screening else ls.load_screening(args.xlsx, args.screening_csv)
        pmid_map = {} if args.no_screening else ls.pmid_map_from_doc(args.pmid_map)
        kept, dropped = dedupe(cands, screening, pmid_map, args)
    except ls.OfflineMiss as e:
        ls.die(str(e) + "\n(run once without --offline to fill the cache)", 2)
    except ls.SearchError as e:
        ls.die(str(e), 1)

    kept = [c for c in kept if c["times_linked"] >= args.min_links and (not args.since or not c["year"] or int(c["year"]) >= args.since)]
    kept.sort(key=lambda c: (-c["times_linked"], -(int(c["year"]) if c["year"] else 0), c["title"]))
    os.makedirs(args.out, exist_ok=True)
    cols = ["doi", "pmid", "year", "authors", "title", "journal", "abstract", "times_linked", "link_type",
            "source_ids", "openalex_id", "cited_by_count", "status", "matched_id"]
    write_csv(os.path.join(args.out, "candidates.csv"), cols, kept, args.no_abstracts)
    write_csv(os.path.join(args.out, "excluded.csv"), cols, dropped, True)
    log.update({"screening_rows": len(screening), "candidates_total": len(cands),
                "duplicates_of_screening": len(dropped), "written": len(kept), "min_links": args.min_links,
                "title_threshold": args.title_threshold,
                "by_times_linked": histogram(kept), "requests_made": client.requests_made,
                "cache_hits": client.cache_hits})
    ls.write_json(os.path.join(args.out, "snowball_log.json"), log)
    two_plus = sum(1 for c in kept if c["times_linked"] >= 2)
    sys.stderr.write("seeds %d (%d resolved); candidates %d; already in Screening %d; written %d "
                     "(%d linked from 2+ seeds) -> %s\n" % (
                         len(seeds), log["seeds_resolved"], len(cands), len(dropped), len(kept), two_plus,
                         os.path.join(args.out, "candidates.csv")))
    sys.stderr.write("requests: %d fetched, %d from cache\n" % (client.requests_made, client.cache_hits))


def histogram(rows):
    h = {}
    for c in rows:
        h[str(c["times_linked"])] = h.get(str(c["times_linked"]), 0) + 1
    return h


def gather(client, args, seeds):
    """Return (candidates dict keyed by an identity key, log)."""
    cands = {}
    log = {"date": ls.today(), "direction": args.direction, "seeds": [], "seeds_resolved": 0}
    for label, doi, pmid in seeds:
        name = label or doi or ("PMID " + pmid)
        entry = {"label": label, "doi": doi, "pmid": pmid, "source": None, "backward": 0, "forward": 0}
        work = None if args.ncbi else oa_work(client, doi, pmid)
        if work is not None:
            entry["source"] = "openalex"
            entry["openalex_id"] = work["id"]
            wf = oa_fields(work)
            entry["pmid"] = entry["pmid"] or wf["pmid"]
            entry["doi"] = entry["doi"] or wf["doi"]
            if args.direction in ("both", "backward"):
                refs = work.get("referenced_works") or []
                meta = oa_batch(client, refs)
                for rid in refs:
                    w = meta.get(rid)
                    if w:
                        add(cands, oa_fields(w), name, "backward")
                entry["backward"] = len(refs)
            if args.direction in ("both", "forward"):
                citers = oa_citers(client, work["id"], args.max_citers)
                for w in citers:
                    add(cands, oa_fields(w), name, "forward")
                entry["forward"] = len(citers)
        elif not args.no_ncbi and (pmid or entry["pmid"]):
            entry["source"] = "ncbi"
            pm = pmid or entry["pmid"]
            got = {}
            if args.direction in ("both", "backward"):
                got["backward"] = ls.elink(client, [pm], "pubmed_pubmed_refs").get(pm, [])
            if args.direction in ("both", "forward"):
                got["forward"] = ls.elink(client, [pm], "pubmed_pubmed_citedin").get(pm, [])
            all_ids = sorted({p for v in got.values() for p in v})
            summ = ls.esummary(client, all_ids) if all_ids else {}
            for kind, ids in got.items():
                for p in ids:
                    s = summ.get(p) or {"pmid": p, "title": "", "year": "", "authors": "", "journal": "", "doi": ""}
                    s = dict(s, openalex_id="", abstract="", cited_by_count="", type="")
                    add(cands, s, name, kind)
                entry[kind] = len(ids)
        else:
            entry["source"] = "unresolved"
            ls.warn("seed %s could not be resolved in OpenAlex%s" % (name, "" if args.no_ncbi else " and has no PMID for NCBI"))
        if entry["source"] in ("openalex", "ncbi"):
            log["seeds_resolved"] += 1
        log["seeds"].append(entry)
    # merge entries that turned out to be the same work under different keys
    return merge_same(cands), log


def identity(rec):
    if rec.get("openalex_id"):
        return "oa:" + rec["openalex_id"]
    if rec.get("doi"):
        return "doi:" + rec["doi"]
    if rec.get("pmid"):
        return "pmid:" + rec["pmid"]
    return "title:" + ls.norm_title(rec.get("title", ""))


def add(cands, rec, seed_name, kind):
    key = identity(rec)
    c = cands.get(key)
    if c is None:
        c = dict(rec)
        c["links"] = {}
        cands[key] = c
    else:
        for f in ("doi", "pmid", "abstract", "journal", "year"):
            if not c.get(f) and rec.get(f):
                c[f] = rec[f]
    c["links"].setdefault(seed_name, set()).add(kind)


def merge_same(cands):
    """Two candidates with the same DOI or PMID (one from OpenAlex, one from
    NCBI) are one work."""
    by_doi, by_pmid, out = {}, {}, {}
    for key, c in cands.items():
        target = None
        if c.get("doi") and c["doi"] in by_doi:
            target = by_doi[c["doi"]]
        elif c.get("pmid") and c["pmid"] in by_pmid:
            target = by_pmid[c["pmid"]]
        if target is None:
            out[key] = c
            if c.get("doi"):
                by_doi[c["doi"]] = c
            if c.get("pmid"):
                by_pmid[c["pmid"]] = c
        else:
            for seed, kinds in c["links"].items():
                target["links"].setdefault(seed, set()).update(kinds)
            for f in ("doi", "pmid", "abstract", "journal", "year", "openalex_id"):
                if not target.get(f) and c.get(f):
                    target[f] = c[f]
    for c in out.values():
        c["times_linked"] = len(c["links"])
        kinds = {k for ks in c["links"].values() for k in ks}
        c["link_type"] = "both" if len(kinds) == 2 else next(iter(kinds))
        c["source_ids"] = "; ".join(sorted(c["links"]))
    return list(out.values())


def dedupe(cands, screening, pmid_map, args):
    by_doi = {r["doi"]: r for r in screening if r["doi"]}
    by_pmid = {}
    for r in screening:
        if r["pmid"]:
            by_pmid[r["pmid"]] = r
        pm = pmid_map.get(r["id"])
        if pm:
            by_pmid[pm] = r
    titles = [(r, ls.norm_title(r["title"]), ls.title_tokens(r["title"])) for r in screening if r["title"]]
    seed_dois = set()
    kept, dropped = [], []
    for c in cands:
        match, how, score = None, "", 0.0
        if c.get("doi") and c["doi"] in by_doi:
            match, how = by_doi[c["doi"]], "doi"
        elif c.get("pmid") and c["pmid"] in by_pmid:
            match, how = by_pmid[c["pmid"]], "pmid"
        else:
            nt = ls.norm_title(c.get("title", ""))
            tok = set(nt.split())
            best, best_r = 0.0, None
            for r, rnt, rtok in titles:
                if nt and nt == rnt:
                    best, best_r = 1.0, r
                    break
                j = ls.jaccard(tok, rtok)
                if j > best:
                    best, best_r = j, r
            if best_r is not None and best >= args.title_threshold:
                match, how, score = best_r, "title", best
            elif best_r is not None and best >= args.possible_threshold:
                c["status"] = "possible duplicate of ID %s (Jaccard %.2f)" % (best_r["id"], best)
                c["matched_id"] = best_r["id"]
        if match is not None:
            c["status"] = "in Screening (%s%s)" % (how, " %.2f" % score if score else "")
            c["matched_id"] = match["id"]
            if args.keep_dupes:
                kept.append(c)
            else:
                dropped.append(c)
        else:
            c.setdefault("status", "new")
            c.setdefault("matched_id", "")
            kept.append(c)
    return kept, dropped


def write_csv(path, cols, rows, no_abstracts):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = {k: r.get(k, "") for k in cols}
            if no_abstracts:
                row["abstract"] = ""
            w.writerow(row)


if __name__ == "__main__":
    main()
