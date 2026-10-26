#!/usr/bin/env python3
"""Regenerate the per-tab CSV exports of the screening workbook from the
cached cell values in the xlsx, or check whether they are stale.

    python3 -I xlsx_to_csv.py            # rewrite data/LVR_screening_sheet_2_<Sheet>.csv
    python3 -I xlsx_to_csv.py --check    # exit 0 if up to date, 3 if stale, 1 on error

Formulas are not evaluated: the export reads the cached <v> of each formula,
exactly as Excel left it (or as set_cells.py patched it). The Counts tab is
re-evaluated and compared against those cached values, and a warning is
printed if they disagree, because that means the exports would carry stale
numbers.
"""

import argparse
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrwb  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=lvrwb.DEFAULT_XLSX, help="workbook to export (default: data/LVR_screening_sheet_2.xlsx)")
    ap.add_argument("--out-dir", default=None, help="where the CSVs live (default: the workbook's folder)")
    ap.add_argument("--sheet", action="append", help="only this tab (repeatable; default: all tabs)")
    ap.add_argument("--check", action="store_true", help="report stale exports without writing; exit 3 if any is stale")
    ap.add_argument("--diff", action="store_true", help="with --check, print a unified diff of each stale file")
    args = ap.parse_args()

    if not os.path.isfile(args.xlsx):
        lvrwb.die("workbook not found: %s" % args.xlsx)
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.xlsx))
    try:
        wb = lvrwb.Workbook(args.xlsx)
    except Exception as e:  # zip or xml trouble
        lvrwb.die("cannot read %s: %s" % (args.xlsx, e))

    sheets = args.sheet or list(wb.sheet_files)
    for s in sheets:
        if s not in wb.sheet_files:
            lvrwb.die("no tab named %r; tabs are %s" % (s, ", ".join(wb.sheet_files)))

    # Cached Counts values vs a fresh evaluation.
    if lvrwb.COUNTS in sheets:
        try:
            stale = [(ref, c, lvrwb.fmt_number(v)) for ref, (c, v) in wb.recompute(lvrwb.COUNTS).items()
                     if c != lvrwb.fmt_number(v)]
        except lvrwb.FormulaError as e:
            stale = []
            print("warning: could not re-evaluate Counts: %s" % e, file=sys.stderr)
        for ref, cached, fresh in stale:
            print("warning: Counts!%s cached value %s but the formula now gives %s "
                  "(run set_cells.py --recount, or open and save in Excel)" % (ref, cached, fresh), file=sys.stderr)

    stale_files = 0
    for sheet in sheets:
        path = lvrwb.sheet_csv_path(out_dir, args.xlsx, sheet)
        text = lvrwb.export_text(wb, sheet, args.xlsx)
        current = None
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as f:
                current = f.read()
        if args.check:
            if current == text:
                print("up to date  %s" % os.path.relpath(path))
            else:
                stale_files += 1
                print("STALE       %s%s" % (os.path.relpath(path), "" if current is not None else " (missing)"))
                if args.diff and current is not None:
                    import difflib
                    sys.stdout.writelines(difflib.unified_diff(
                        current.splitlines(True), text.splitlines(True),
                        fromfile=path, tofile=path + " (regenerated)", n=0))
            continue
        if current == text:
            print("unchanged   %s" % os.path.relpath(path))
            continue
        os.makedirs(out_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print("wrote       %s (%d rows)" % (os.path.relpath(path), len(wb.grid(sheet))))

    if args.check and stale_files:
        print("%d export(s) stale; run without --check to regenerate" % stale_files)
        sys.exit(3)


if __name__ == "__main__":
    main()
