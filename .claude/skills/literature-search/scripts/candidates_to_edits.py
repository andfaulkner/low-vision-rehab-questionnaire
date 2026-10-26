#!/usr/bin/env python3
"""Turn chosen rows of snowball.py's candidates.csv into the edits CSV that
the screening-workbook skill's set_cells.py --edits --add-rows consumes, so
new records land in the Screening tab with consecutive IDs and the right
columns.

    python3 -I candidates_to_edits.py analysis/search/snowball/candidates.csv --min-links 2 --out edits.csv
    python3 -I candidates_to_edits.py candidates.csv --doi 10.1001/archopht.119.7.1050 --doi ... --out edits.csv
    python3 -I candidates_to_edits.py candidates.csv --min-links 2 --start-id 136 --start-row 137 --out edits.csv
    # then, from the repo root:
    python3 -I .claude/skills/screening-workbook/scripts/set_cells.py --edits edits.csv --add-rows --dry-run
    python3 -I .claude/skills/screening-workbook/scripts/set_cells.py --edits edits.csv --add-rows --export
    python3 -I .claude/skills/screening-workbook/scripts/set_cells.py --counts B5 <new other-sources total>

By default the next ID and row are read from the workbook (last ID + 1,
last row + 1), so IDs stay consecutive. Columns written: A ID, B Year,
C Authors ("Surname, Given et al."), D Title, E Journal, F DOI (as the
URL text; the clickable hyperlink is added by hand, see the
screening-workbook reference), G Abstract. Nothing else: H-L belong to the
reviewer (Notes included) and N-S to screening, which comes after adding.
Where each record came from (seed IDs, link counts, date) goes to
<out>.provenance.csv beside the edits file, for the search log's
citation-searching table and the PRISMA "other methods" count (Counts!B5).

Records flagged by snowball.py as already in the sheet are refused unless
--include-flagged is given.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrsearch as ls  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates", help="candidates.csv from snowball.py")
    ap.add_argument("--min-links", type=int, default=1, help="take candidates linked from at least N seeds")
    ap.add_argument("--doi", action="append", default=[], help="take this DOI (repeatable); combined with --min-links as OR")
    ap.add_argument("--pmid", action="append", default=[], help="take this PMID (repeatable)")
    ap.add_argument("--limit", type=int, help="take at most this many, in candidates.csv order")
    ap.add_argument("--include-flagged", action="store_true", help="also take rows whose status is not 'new'")
    ap.add_argument("--xlsx", default=ls.DEFAULT_XLSX, help="workbook to read the next ID/row from")
    ap.add_argument("--start-id", type=int, help="first new ID (default: last ID in the workbook + 1)")
    ap.add_argument("--start-row", type=int, help="first new sheet row (default: last row + 1)")
    ap.add_argument("--note", default="", help="extra text for the Notes column")
    ap.add_argument("--out", required=True, help="edits CSV for set_cells.py --edits")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.candidates, encoding="utf-8", newline="")))
    want_doi = {ls.norm_doi(d) for d in args.doi}
    want_pmid = {ls.norm_pmid(p) for p in args.pmid}
    chosen = []
    for r in rows:
        pick = (want_doi and ls.norm_doi(r.get("doi", "")) in want_doi) or \
               (want_pmid and r.get("pmid", "") in want_pmid) or \
               (not want_doi and not want_pmid and int(r.get("times_linked") or 0) >= args.min_links) or \
               (bool(want_doi or want_pmid) and args.min_links > 1 and int(r.get("times_linked") or 0) >= args.min_links)
        if not pick:
            continue
        if (r.get("status") or "new") != "new" and not args.include_flagged:
            ls.warn("skipping %r: status %s (use --include-flagged to add anyway)" % (r.get("title", "")[:60], r["status"]))
            continue
        chosen.append(r)
    if args.limit:
        chosen = chosen[:args.limit]
    if not chosen:
        ls.die("no candidates selected")

    start_id, start_row = args.start_id, args.start_row
    if start_id is None or start_row is None:
        if not os.path.exists(args.xlsx):
            ls.die("workbook %s not found; give --start-id and --start-row" % args.xlsx)
        sys.path.insert(0, ls.WORKBOOK_SCRIPTS)
        import lvrwb  # noqa: E402
        wb = lvrwb.Workbook(args.xlsx)
        id_rows = wb.id_to_row()
        last_id = max(id_rows) if id_rows else 0
        last_row = max(id_rows.values()) if id_rows else 1
        start_id = start_id if start_id is not None else last_id + 1
        start_row = start_row if start_row is not None else last_row + 1

    prov_path = re.sub(r"\.csv$", "", args.out) + ".provenance.csv"
    with open(args.out, "w", encoding="utf-8", newline="") as fh, \
            open(prov_path, "w", encoding="utf-8", newline="") as ph:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["row", "col", "value"])
        pw = csv.writer(ph, lineterminator="\n")
        pw.writerow(["id", "row", "doi", "pmid", "times_linked", "link_type", "source_ids", "method", "date", "note"])
        for k, r in enumerate(chosen):
            rid, row = start_id + k, start_row + k
            target = str(row)  # the `row` column takes a bare number; set_cells.py adds "row:"
            doi = ls.norm_doi(r.get("doi", ""))
            cells = [("A", str(rid)), ("B", r.get("year", "")), ("C", authors_sheet_style(r.get("authors", ""))),
                     ("D", r.get("title", "")), ("E", r.get("journal", "")),
                     ("F", ("https://doi.org/" + doi) if doi else "No link"),
                     ("G", r.get("abstract", "") or "Missing")]
            for col, val in cells:
                w.writerow([target, col, val])
            pw.writerow([rid, row, doi, r.get("pmid", ""), r.get("times_linked", ""), r.get("link_type", ""),
                         r.get("source_ids", ""), "citation searching (snowball)", ls.today(), args.note])
    sys.stderr.write("%d record(s) -> %s as IDs %d-%d, rows %d-%d; provenance in %s (copy its rows into the "
                     "search log's citation-searching table).\nNext: set_cells.py --edits %s --add-rows --dry-run\n" % (
                         len(chosen), args.out, start_id, start_id + len(chosen) - 1, start_row,
                         start_row + len(chosen) - 1, prov_path, args.out))


def authors_sheet_style(authors):
    """'Yueh-Hsun Wu; Deyue Yu' -> 'Wu, Yueh-Hsun et al.' (the sheet's style).
    NCBI style 'Wu YH; Yu D' -> 'Wu, YH et al.'"""
    names = [a.strip() for a in (authors or "").split(";") if a.strip()]
    if not names:
        return ""
    first = names[0]
    if "," in first:
        head = first
    else:
        parts = first.split()
        if len(parts) >= 2 and parts[-1].isupper() and len(parts[-1]) <= 3:   # NCBI 'Wu YH'
            head = "%s, %s" % (" ".join(parts[:-1]), parts[-1])
        elif len(parts) >= 2:
            head = "%s, %s" % (parts[-1], " ".join(parts[:-1]))
        else:
            head = first
    return head + (" et al." if len(names) > 1 else "")


if __name__ == "__main__":
    main()
