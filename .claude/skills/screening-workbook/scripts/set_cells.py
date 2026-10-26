#!/usr/bin/env python3
"""Set cells on the Screening tab of the screening workbook by editing the
sheet XML in place, then re-evaluate the Counts formulas and patch their
cached values.

    python3 -I set_cells.py --set 12 N Exclude --set 12 O "No questionnaire/screening item"
    python3 -I set_cells.py --edits edits.csv            # columns: id (or row), col, value
    python3 -I set_cells.py --reviewer --set 5 H Include  # H-L need --reviewer
    python3 -I set_cells.py --recount                     # only refresh cached Counts values
    python3 -I set_cells.py --dry-run --set ...           # show what would change, write nothing

Targets: a bare number is a record ID (column A); `row:137` is a sheet row.
A row that does not exist yet is created (use --add-rows to allow this), and
every range that ends at the old last row (Counts formulas, drop-downs,
conditional formatting, autofilter, dimension, _FilterDatabase) is extended.

Columns H-L are the human reviewer's decisions. They are refused unless
--reviewer is passed, which asserts that the reviewer dictated these exact
values. The Counts tab (PRISMA numbers, and the "agreed with / overrode the
AI" rows) treats H-L as human decisions, so an AI writing them would corrupt
the audit trail of reviewer versus AI. AI suggestions go in N-S.

Values for H, I, J, K (and N, O, Q, R) are validated against the Lists tab;
a near miss (wrong case, extra space) is rejected with the exact spelling,
because the Counts formulas use COUNTIF on the exact strings.

The workbook is never saved through openpyxl: all other zip parts are copied
byte for byte, and the script checks after writing that the x14 drop-down
validations, conditional formatting and hyperlinks survived.
"""

import argparse
import csv
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrwb  # noqa: E402

LETTER = re.compile(r"[A-Z]{1,3}")


def parse_target(text, id_rows):
    text = text.strip()
    if text.lower().startswith("row:"):
        return int(text[4:]), None
    if not text.isdigit():
        raise lvrwb.WorkbookError("target %r must be a record ID or row:N" % text)
    rid = int(text)
    return id_rows.get(rid), rid


def load_edits(args, wb):
    id_rows = wb.id_to_row()
    edits = []  # (row, col, value, label)
    for target, col, value in args.set or []:
        row, rid = parse_target(target, id_rows)
        edits.append((row, col.strip().upper(), value, target))
    if args.edits:
        with open(args.edits, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            cols = [c.strip().lower() for c in rd.fieldnames or []]
            if "col" not in cols or "value" not in cols or not ({"id", "row"} & set(cols)):
                lvrwb.die("%s needs a header with id (or row), col, value" % args.edits)
            for n, rec in enumerate(rd, 2):
                rec = {k.strip().lower(): (v or "") for k, v in rec.items()}
                if rec.get("row", "").strip():
                    target = "row:" + rec["row"].strip()
                elif rec.get("id", "").strip():
                    target = rec["id"].strip()
                else:
                    lvrwb.die("%s line %d: no id or row" % (args.edits, n))
                row, rid = parse_target(target, id_rows)
                edits.append((row, rec["col"].strip().upper(), rec["value"], target))
    return edits, id_rows


def validate(wb, edits, args):
    lists = wb.lists()
    headers = wb.header_map()
    last_row = wb.dimension_last_row(lvrwb.SCREENING)
    problems, warnings = [], []
    for row, col, value, target in edits:
        if not LETTER.fullmatch(col):
            problems.append("%s: bad column %r" % (target, col))
            continue
        if row is None:
            problems.append("%s: no record with this ID (use row:N to add a row, with --add-rows)" % target)
            continue
        if row < 2:
            problems.append("%s: row 1 is the header row" % target)
            continue
        if row > last_row and not args.add_rows:
            problems.append("%s: row %d is beyond the last record row %d; pass --add-rows to append" % (target, row, last_row))
        if col in lvrwb.REVIEWER_COLS and not args.reviewer:
            problems.append("%s: column %s (%s) is the reviewer's; pass --reviewer only if the reviewer dictated this value"
                            % (target, col, headers.get(col, "?")))
        if col in lvrwb.LIST_FOR_COL and value not in (None, ""):
            allowed = lists.get(lvrwb.LIST_FOR_COL[col], [])
            if value not in allowed:
                near = [a for a in allowed if a.strip().casefold() == value.strip().casefold()]
                hint = (" (did you mean %r?)" % near[0]) if near else ""
                problems.append("%s: %r is not an allowed value for %s (%s)%s; allowed: %s"
                                % (target, value, col, headers.get(col, "?"), hint, " | ".join(allowed)))
    # Decision/reason consistency, as warnings.
    by_row = {}
    for row, col, value, target in edits:
        if row is not None:
            by_row.setdefault(row, {})[col] = value
    cells = wb.cells(lvrwb.SCREENING)

    def after(row, col):
        if col in by_row.get(row, {}):
            return by_row[row][col] or ""
        c = cells.get("%s%d" % (col, row))
        return (c.value or "") if c else ""

    for row in by_row:
        for dec, reason in (("H", "I"), ("J", "K"), ("N", "O"), ("Q", "R")):
            d, r = after(row, dec), after(row, reason)
            if d == "Exclude" and not r:
                warnings.append("row %d: %s=Exclude but %s (reason) is empty" % (row, dec, reason))
            if d and d != "Exclude" and r:
                warnings.append("row %d: %s=%s but %s has a reason (%r)" % (row, dec, d, reason, r))
    return problems, warnings


def snapshot(wb):
    """The parts of the Screening XML that must survive an edit untouched."""
    xml = wb.text(wb.sheet_part(lvrwb.SCREENING))
    out = {}
    for tag in ("extLst", "hyperlinks", "autoFilter", "cols", "sheetViews"):
        m = re.search(r"<%s[ >].*?</%s>|<%s [^>]*/>" % (tag, tag, tag), xml, re.S)
        out[tag] = m.group(0) if m else None
    out["conditionalFormatting"] = re.findall(r"<conditionalFormatting .*?</conditionalFormatting>", xml, re.S)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=lvrwb.DEFAULT_XLSX, help="workbook to edit (default: data/LVR_screening_sheet_2.xlsx)")
    ap.add_argument("--set", nargs=3, action="append", metavar=("TARGET", "COL", "VALUE"),
                    help="ID (or row:N), column letter, value; '' clears the cell")
    ap.add_argument("--edits", help="CSV of edits with columns id (or row), col, value")
    ap.add_argument("--counts", nargs=2, action="append", metavar=("REF", "NUMBER"),
                    help="set a hand-typed number on the Counts tab (B3 PubMed, B4 Scopus, B5 other sources); formula cells are refused")
    ap.add_argument("--reviewer", action="store_true", help="allow writing H-L: the reviewer dictated these values")
    ap.add_argument("--add-rows", action="store_true", help="allow creating rows beyond the last record, extending every range")
    ap.add_argument("--text", action="store_true", help="store every value as text, even in numeric columns A/B")
    ap.add_argument("--recount", action="store_true", help="re-evaluate Counts and patch cached values (implied by any edit)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and write nothing")
    ap.add_argument("--verbose", action="store_true", help="list every cell even for large edit sets")
    ap.add_argument("--out", help="write to this path instead of editing --xlsx in place")
    ap.add_argument("--export", action="store_true", help="also regenerate the CSV exports afterwards")
    args = ap.parse_args()

    if not os.path.isfile(args.xlsx):
        lvrwb.die("workbook not found: %s" % args.xlsx)
    try:
        wb = lvrwb.Workbook(args.xlsx)
        edits, id_rows = load_edits(args, wb)
    except lvrwb.WorkbookError as e:
        lvrwb.die(str(e))
    counts_edits = []
    for ref, number in args.counts or []:
        ref = ref.strip().upper()
        c = wb.cells(lvrwb.COUNTS).get(ref)
        if c is not None and c.formula:
            lvrwb.die("Counts!%s holds a formula (%s); only hand-typed inputs can be set" % (ref, c.formula))
        if not re.fullmatch(r"-?\d+(\.\d+)?", number.strip()):
            lvrwb.die("Counts!%s: %r is not a number" % (ref, number))
        counts_edits.append((ref, number.strip(), c.value if c else None))
    if not edits and not counts_edits and not args.recount:
        lvrwb.die("nothing to do: give --set, --edits, --counts or --recount")

    problems, warnings = validate(wb, edits, args)
    for w in warnings:
        print("warning: %s" % w, file=sys.stderr)
    if problems:
        for p in problems:
            print("refused: %s" % p, file=sys.stderr)
        sys.exit(2)

    before = snapshot(wb)
    old_last = wb.dimension_last_row(lvrwb.SCREENING)
    new_last = max([old_last] + [row for row, _, _, _ in edits])
    headers = wb.header_map()
    cells = wb.cells(lvrwb.SCREENING)
    verbose = args.verbose or len(edits) <= 25
    changed = 0
    for row, col, value, target in edits:
        old = cells.get("%s%d" % (col, row))
        old_v = old.value if old else None
        changed += (old_v or "") != (value or "")
        if verbose:
            label = target if target.lower().startswith("row:") else "ID %s" % target
            print("%s%d (%s, %s): %r -> %r" % (col, row, headers.get(col, col), label, old_v, value))
    if not verbose:
        print("%d edit(s) on %d row(s), %d of them change a value (use --verbose to list)" %
              (len(edits), len({r for r, _, _, _ in edits}), changed))
    for ref, number, old_v in counts_edits:
        print("Counts!%s (hand-typed input): %r -> %r" % (ref, old_v, number))
    if new_last > old_last:
        print("extending ranges from row %d to row %d" % (old_last, new_last))

    if args.dry_run:
        try:
            for ref, (cached, fresh) in sorted(wb.recompute().items()):
                if cached != lvrwb.fmt_number(fresh):
                    print("Counts!%s cached %s, currently evaluates to %s (before these edits)" % (ref, cached, lvrwb.fmt_number(fresh)))
        except lvrwb.FormulaError as e:
            print("warning: %s" % e, file=sys.stderr)
        print("dry run: nothing written")
        return

    if new_last > old_last:
        wb.extend_ranges(new_last)
    for row, col, value, target in edits:
        wb.set_cell(lvrwb.SCREENING, "%s%d" % (col, row), value, as_number=False if args.text else None)
    for ref, number, _ in counts_edits:
        wb.set_cell(lvrwb.COUNTS, ref, number, as_number=True)
    if edits or counts_edits:
        wb.fix_sst_count()
    try:
        changes = wb.patch_cached(lvrwb.COUNTS)
    except lvrwb.FormulaError as e:
        lvrwb.die("could not re-evaluate Counts, nothing written: %s" % e)
    for ref, old, new in changes:
        print("Counts!%s: %s -> %s" % (ref, old, new))
    if not changes:
        print("Counts: cached values already correct")

    # Self-check before writing: well-formed XML and the protected blocks intact.
    import xml.etree.ElementTree as ET
    for part in (wb.sheet_part(lvrwb.SCREENING), wb.sheet_part(lvrwb.COUNTS), "xl/workbook.xml", "xl/sharedStrings.xml"):
        if part in wb.parts:
            try:
                ET.fromstring(wb.parts[part])
            except ET.ParseError as e:
                lvrwb.die("internal error: %s is no longer well-formed (%s); nothing written" % (part, e))
    after = snapshot(wb)
    if new_last > old_last:
        bump = re.compile(r"(:\$?[A-Z]{1,3}\$?)%d(?!\d)" % old_last)
        before = {k: (bump.sub(r"\g<1>%d" % new_last, v) if isinstance(v, str) else
                      [bump.sub(r"\g<1>%d" % new_last, x) for x in v] if v else v) for k, v in before.items()}
    for k in before:
        if before[k] != after[k]:
            lvrwb.die("internal error: the %s block changed unexpectedly; nothing written" % k)

    out = args.out or args.xlsx
    wb.save(out)
    print("wrote %s" % os.path.relpath(out))

    if args.export:
        import subprocess
        sys.stdout.flush()
        cmd = [sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "xlsx_to_csv.py"), "--xlsx", out]
        sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
