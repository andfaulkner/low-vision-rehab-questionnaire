#!/usr/bin/env python3
"""Measure the recall of a PubMed search string against a set of known
relevant PMIDs (the key sources), using NCBI E-utilities.

    python3 -I pubmed_recall.py --from-doc docs/LVR_search_strategy.md --cache analysis/search/cache
    python3 -I pubmed_recall.py --query-file revised.txt --pmids key_pmids.txt --cache C --out run.json
    python3 -I pubmed_recall.py --from-doc docs/LVR_search_strategy.md --cache C --offline   # replay
    python3 -I pubmed_recall.py --from-doc ... --diff analysis/search/recall_2026-10-20.json
    python3 -I pubmed_recall.py --from-doc ... --arms 5-12 --final 14      # per-arm table

What it does
  1. esearch the query alone (retmax=0) for its total record count.
  2. esearch `(query) AND (pmid1[uid] OR pmid2[uid] ...)` in batches of 100
     PMIDs by POST, so the URL-length limit never bites. The PMIDs that come
     back are the hits; the rest are the misses.
  3. esummary the PMIDs so the report shows titles, not just numbers.

The query is a plain string, or a PubMed Advanced Search history (`#1 ...`,
`#2 #1 AND ...`); history references are expanded recursively, exactly as
PubMed does, and the last line is the final query. `--from-doc` reads the
history from the first fenced code block of the strategy document and the
PMIDs from its tables (first table = key sources, labelled by Screening ID;
second table = held-out papers).

Recall against a held-out set is reported separately from recall against
the key sources, because a string tuned on the key sources will always do
well on them; only the held-out set says whether it generalises.

Output: a Markdown report on stdout; `--out FILE.json` saves everything
(query, counts, hits, misses, summaries, date) so a later run can `--diff`
against it. Exit codes: 0 ok, 1 error, 2 offline cache miss, 3 recall below
--fail-under.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrsearch as ls  # noqa: E402


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    q = ap.add_argument_group("query")
    q.add_argument("--query", help="the PubMed query as one string")
    q.add_argument("--query-file", help="file holding the query, or a #N search history (last line is final)")
    q.add_argument("--from-doc", metavar="MD", help="strategy document: query from its first fenced #N block, "
                                                   "PMIDs from its tables (unless --pmids/--pmid given)")
    q.add_argument("--line", type=int, help="with a history: evaluate this line instead of the last")
    p = ap.add_argument_group("PMIDs")
    p.add_argument("--pmids", metavar="FILE", help="key-source PMIDs: one per line (label pmid # comment) or CSV with a pmid column")
    p.add_argument("--pmid", action="append", default=[], help="a key-source PMID (repeatable)")
    p.add_argument("--held-out", metavar="FILE", help="held-out PMIDs file (same formats); from the doc's second table by default")
    p.add_argument("--no-held-out", action="store_true", help="ignore the held-out table in the doc")
    a = ap.add_argument_group("per-arm table")
    a.add_argument("--arms", help="history lines to evaluate one by one, e.g. 5-12 or 5,6,9")
    a.add_argument("--final", type=int, help="history line that applies the limits (e.g. 14: '#13 AND limits'); "
                                            "each arm is substituted for the first #ref in it")
    n = ap.add_argument_group("network")
    n.add_argument("--cache", metavar="DIR", help="cache every response here (replayable with --offline)")
    n.add_argument("--offline", action="store_true", help="use the cache only; exit 2 on a miss")
    n.add_argument("--refresh", action="store_true", help="ignore cached responses and fetch again")
    n.add_argument("--email", help="contact e-mail for NCBI (default: $LVR_CONTACT_EMAIL / $NCBI_EMAIL / git user.email)")
    n.add_argument("--api-key", help="NCBI API key (default $NCBI_API_KEY); raises the rate limit to 10/s")
    o = ap.add_argument_group("output")
    o.add_argument("--out", metavar="JSON", help="save the full result for --diff and for the search log")
    o.add_argument("--md", metavar="FILE", help="write the Markdown report here as well as stdout")
    o.add_argument("--diff", metavar="JSON", help="compare with a previous --out file")
    o.add_argument("--fail-under", type=float, metavar="R", help="exit 3 if key-source recall < R (0-1)")
    o.add_argument("--no-titles", action="store_true", help="skip esummary (faster, no titles)")
    o.add_argument("--verbose", action="store_true", help="log every request")
    args = ap.parse_args()
    if not (args.query or args.query_file or args.from_doc):
        ap.error("give --query, --query-file or --from-doc")
    return args


def load_inputs(args):
    doc_text = ls.read_text(args.from_doc) if args.from_doc else None
    if args.query:
        qtext = args.query
    elif args.query_file:
        qtext = ls.read_text(args.query_file)
    else:
        qtext = ls.query_from_doc(doc_text)
    final, lines = ls.load_query(qtext)
    if args.line:
        if not lines:
            ls.die("--line needs a #N search history")
        final = ls.expand_history(lines, args.line)

    key, held = [], []
    if args.pmids:
        key = ls.read_pmid_list(args.pmids)
    key += [("", p) for p in args.pmid]
    if args.held_out:
        held = ls.read_pmid_list(args.held_out)
    if doc_text and (not key or (not held and not args.held_out)):
        tables = ls.pmid_tables_from_doc(doc_text)
        if not key:
            if not tables:
                ls.die("no PMID table found in %s" % args.from_doc)
            key = tables[0]
        if not held and not args.held_out and not args.no_held_out and len(tables) > 1:
            held = tables[1]
    if not key:
        ls.die("no key-source PMIDs given (--pmids, --pmid or a doc with a PMID table)")
    key = dedupe_pmids(key)
    held = dedupe_pmids(held)
    return final, lines, key, held


def dedupe_pmids(pairs):
    seen, out = set(), []
    for label, pmid in pairs:
        pmid = ls.norm_pmid(pmid)
        if pmid and pmid not in seen:
            seen.add(pmid)
            out.append((label, pmid))
    return out


def recall_of(client, query, pairs):
    """esearch (query) AND (uids) in batches of 100; return the set found."""
    found = set()
    for i in range(0, len(pairs), 100):
        batch = [p for _, p in pairs[i:i + 100]]
        uid_clause = " OR ".join("%s[uid]" % p for p in batch)
        term = "(%s) AND (%s)" % (query, uid_clause)
        res = ls.esearch(client, term, retmax=len(batch))
        found.update(res.get("idlist", []))
    return found


def arm_list(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def arm_query(lines, n, final_line):
    """Line `final_line` with its first #ref replaced by (#n), expanded."""
    if final_line is None:
        return ls.expand_history(lines, n)
    if final_line not in lines:
        ls.die("--final line #%d is not in the history" % final_line)
    text = lines[final_line]
    m = ls.HISTORY_REF.search(text)
    if not m:
        ls.die("--final line #%d has no #reference to substitute" % final_line)
    text = text[:m.start()] + "(#%d)" % n + text[m.end():]
    tmp = dict(lines)
    tmp[final_line] = text
    return ls.expand_history(tmp, final_line)


def main():
    args = parse_args()
    try:
        client = ls.Client(cache_dir=args.cache, offline=args.offline, email=args.email,
                           ncbi_api_key=args.api_key, verbose=args.verbose, refresh=args.refresh)
        final, lines, key, held = load_inputs(args)
        result = run(client, args, final, lines, key, held)
    except ls.OfflineMiss as e:
        ls.die(str(e) + "\n(run once without --offline to fill the cache)", 2)
    except ls.SearchError as e:
        ls.die(str(e), 1)

    report = render(result, args)
    sys.stdout.write(report)
    if args.md:
        os.makedirs(os.path.dirname(os.path.abspath(args.md)) or ".", exist_ok=True)
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(report)
    if args.out:
        ls.write_json(args.out, result)
        sys.stderr.write("saved %s\n" % args.out)
    sys.stderr.write("requests: %d fetched, %d from cache\n" % (client.requests_made, client.cache_hits))
    if args.fail_under is not None and result["key"]["recall"] < args.fail_under:
        ls.die("key-source recall %.3f is below %.3f" % (result["key"]["recall"], args.fail_under), 3)


def run(client, args, final, lines, key, held):
    total = ls.esearch(client, final, retmax=0)
    count = int(total.get("count", "0"))
    key_found = recall_of(client, final, key)
    held_found = recall_of(client, final, held) if held else set()

    summaries = {}
    if not args.no_titles:
        summaries = ls.esummary(client, [p for _, p in key + held])
    not_in_pubmed = [p for _, p in key + held if p not in summaries] if summaries else []

    result = {
        "date": ls.today(),
        "source": args.from_doc or args.query_file or "--query",
        "query": final,
        "query_chars": len(final),
        "history_lines": {str(k): v for k, v in lines.items()},
        "evaluated_line": args.line or (max(lines) if lines else None),
        "query_translation": total.get("querytranslation", "")[:2000],
        "count": count,
        "key": block(key, key_found, summaries),
        "held_out": block(held, held_found, summaries) if held else None,
        "not_in_pubmed": not_in_pubmed,
        "arms": None,
    }
    if args.arms:
        if not lines:
            ls.die("--arms needs a #N search history")
        arms = []
        for n in arm_list(args.arms):
            q = arm_query(lines, n, args.final)
            c = int(ls.esearch(client, q, retmax=0).get("count", "0"))
            f = recall_of(client, q, key)
            h = recall_of(client, q, held) if held else set()
            arms.append({"line": n, "count": c, "key_found": sorted(f, key=int),
                         "held_out_found": sorted(h, key=int), "text": lines[n][:200]})
        # which key sources only one arm finds
        for a in arms:
            others = set()
            for b in arms:
                if b is not a:
                    others.update(b["key_found"])
            a["key_unique"] = [p for p in a["key_found"] if p not in others]
        result["arms"] = arms
    return result


def block(pairs, found, summaries):
    labels = {p: l for l, p in pairs}
    hits = sorted([p for _, p in pairs if p in found], key=int)
    misses = sorted([p for _, p in pairs if p not in found], key=int)
    n = len(pairs)
    return {"n": n, "found": len(hits), "recall": (len(hits) / n) if n else None,
            "hits": [{"pmid": p, "label": labels.get(p, ""), **summaries.get(p, {})} for p in hits],
            "misses": [{"pmid": p, "label": labels.get(p, ""), **summaries.get(p, {})} for p in misses]}


def fmt_row(rec):
    t = rec.get("title") or "(no summary)"
    if len(t) > 90:
        t = t[:87] + "..."
    first = (rec.get("authors") or "").split(";")[0]
    return "| %s | %s | %s %s | %s |" % (rec.get("label", ""), rec["pmid"], first, rec.get("year", ""), t)


def render(r, args):
    out = []
    out.append("# PubMed recall check (%s)\n" % r["date"])
    out.append("Source: `%s`%s. Query: %d characters%s." % (
        r["source"], (", line #%s" % r["evaluated_line"]) if r["evaluated_line"] else "",
        r["query_chars"], " (history expanded)" if r["history_lines"] else ""))
    out.append("")
    out.append("| | n | found | missed | recall |")
    out.append("|---|---|---|---|---|")
    out.append("| **Records retrieved by the query alone** | | **%d** | | |" % r["count"])
    k = r["key"]
    out.append("| Key sources | %d | %d | %d | %.1f%% |" % (k["n"], k["found"], k["n"] - k["found"], 100 * k["recall"]))
    h = r.get("held_out")
    if h:
        out.append("| Held-out papers | %d | %d | %d | %.1f%% |" % (h["n"], h["found"], h["n"] - h["found"], 100 * h["recall"]))
    out.append("")
    if r["not_in_pubmed"]:
        out.append("PMIDs with no PubMed summary (typo, or not a PubMed record): %s\n" % ", ".join(r["not_in_pubmed"]))

    for name, b in (("Key sources", k), ("Held-out papers", h)):
        if not b:
            continue
        out.append("## %s missed (%d)\n" % (name, len(b["misses"])))
        if b["misses"]:
            out.append("| label | PMID | first author, year | title |")
            out.append("|---|---|---|---|")
            out.extend(fmt_row(m) for m in b["misses"])
        else:
            out.append("None.")
        out.append("")
    out.append("<details><summary>Key sources found (%d)</summary>\n" % k["found"])
    out.append("| label | PMID | first author, year | title |")
    out.append("|---|---|---|---|")
    out.extend(fmt_row(m) for m in k["hits"])
    out.append("\n</details>\n")

    if r.get("arms"):
        out.append("## Per-arm results\n")
        out.append("Counts are for the arm %s. 'Unique' = key sources no other listed arm finds.\n" %
                   ("with the limits of line #%d applied" % args.final if args.final else "alone"))
        out.append("| Arm | Records | Key sources | Unique to this arm | Held-out |")
        out.append("|---|---|---|---|---|")
        labels = {x["pmid"]: x.get("label", "") for x in k["hits"] + k["misses"]}
        for a in r["arms"]:
            uniq = ", ".join((labels.get(p) or p) for p in a["key_unique"])
            out.append("| #%d | %d | %d | %s | %d |" % (a["line"], a["count"], len(a["key_found"]), uniq or "-",
                                                      len(a["held_out_found"])))
        out.append("")

    if args.diff:
        out.append(render_diff(r, args.diff))

    out.append("Notes: recall against the key sources is optimistic when the string was tuned on them; "
               "the held-out row is the honest figure. Precision (records retrieved per relevant record) "
               "is the reviewer's trade-off: every extra arm buys recall with screening time. "
               "Record the date, the count and this report in the search log (PRISMA-S items 8, 12, 13, 15).")
    out.append("")
    return "\n".join(out)


def render_diff(r, prev_path):
    import json
    with open(prev_path, encoding="utf-8") as fh:
        prev = json.load(fh)
    lines = ["## Difference from %s (%s)\n" % (prev_path, prev.get("date", "?"))]
    lines.append("- Records: %d -> %d (%+d)" % (prev["count"], r["count"], r["count"] - prev["count"]))
    for name in ("key", "held_out"):
        a, b = prev.get(name), r.get(name)
        if not a or not b:
            continue
        ah = {x["pmid"] for x in a["hits"]}
        bh = {x["pmid"] for x in b["hits"]}
        lines.append("- %s: %d/%d -> %d/%d found" % (name.replace("_", "-"), a["found"], a["n"], b["found"], b["n"]))
        for p in sorted(bh - ah, key=int):
            lines.append("  - newly found: %s %s" % (p, title_of(b, p)))
        for p in sorted(ah - bh, key=int):
            lines.append("  - newly missed: %s %s" % (p, title_of(b, p)))
    if prev.get("query") != r["query"]:
        lines.append("- The query text changed (%d -> %d characters)." % (len(prev.get("query", "")), r["query_chars"]))
    else:
        lines.append("- The query text is unchanged; any difference is PubMed's index moving.")
    lines.append("")
    return "\n".join(lines)


def title_of(b, pmid):
    for x in b["hits"] + b["misses"]:
        if x["pmid"] == pmid:
            return (x.get("title") or "")[:80]
    return ""


if __name__ == "__main__":
    main()
