---
name: screening-workbook
description: Read, update and export the systematic-review screening workbook data/LVR_screening_sheet_2.xlsx (tabs Instructions, Screening, Lists, Counts) without breaking its drop-downs, conditional formatting, DOI links or PRISMA counts. Use whenever a task touches the screening sheet or its CSV exports - "which records are included", "what did the reviewer decide", "regenerate/refresh the CSVs", "are the exports stale", "mark record N as Exclude/Include/Maybe", "add an AI suggestion or rationale", "fix the counts", "add a record", "list the included studies and their full texts", or anything that would otherwise open the xlsx with openpyxl or pandas. Also the first stop before data extraction, QUADAS-2 or meta-analysis, which all start from the included set.
---

# Screening workbook

`data/LVR_screening_sheet_2.xlsx` is the source of truth for which records are
in the review. Everything downstream (data extraction, risk of bias, pooling)
starts from it, so edit it only through this skill's scripts, which rewrite
the sheet XML in place and leave every other part of the file byte for byte
as Excel wrote it. Never save it with openpyxl: openpyxl drops the x14
drop-down validations and every cached formula value (it prints the warning
"Data Validation extension is not supported and will be removed" when it
loads this file). Never hand-edit the CSV exports: they are snapshots.

Read `references/workbook-layout.md` when you need the concrete XML (which
sheetN.xml is which tab, the validation and formatting snippets, every Counts
formula with its cell, style indexes, the CSV conventions).

## Who owns which columns

| Columns | Owner | May Claude write them? |
|---|---|---|
| A-G, M | bibliographic record, Zotero key | only to fix a record or add one |
| **H-L** (yellow) | the **human reviewer**: T/A decision, T/A reason, FT decision, FT reason, Notes | **only when the reviewer dictated the exact value**, via `--reviewer` |
| N-P (grey) | AI suggestion: decision, reason, one-line rationale | yes, when asked to screen or suggest |
| Q-S (grey) | second, independent AI pass (same three fields) | yes, when asked |

The Counts tab turns H-L into the PRISMA flow numbers and into "rows where
you agreed with / changed the AI decision" (B31/B32). If an AI wrote H-L the
review would be reporting machine decisions as the reviewer's and the
agreement check would be meaningless. So: screening by Claude goes in N-P (or
Q-S), the reviewer reads it and decides, and the review's Methods must say
that AI assistance was used. `set_cells.py` refuses H-L without `--reviewer`;
pass it only to record a decision the reviewer has actually stated ("mark 12
as Include", "I've excluded 30-35 for no questionnaire").

## Allowed values (Lists tab)

Decisions H, N, Q: `Include` | `Exclude` | `Maybe`. Full-text decision J:
`Include` | `Exclude`. Reasons I, K, O, R: exactly one of

`Wrong population (not adults)` · `No questionnaire/screening item` ·
`No accuracy/validation data` · `Intervention study only` ·
`Not about low vision/visual function` · `Review/opinion/editorial` ·
`Conference abstract only` · `Language (not English/French)` ·
`Full text not available` · `Other (see notes)`

Spelling, case and spacing must match character for character: Counts uses
`COUNTIF` on these strings, the drop-downs validate against them, and a
near-miss ("include", "No questionnaire") simply vanishes from the counts.
`set_cells.py` validates every value against the Lists tab and names the
correct spelling. An `Exclude` needs exactly one reason; Include/Maybe have
none (the script warns about mismatches). Both Include and Maybe at
title/abstract go on to full text.

## Reading

Prefer the CSV exports, but check they are current first, because they go
stale the moment the reviewer saves the workbook:

```bash
python3 -I .claude/skills/screening-workbook/scripts/xlsx_to_csv.py --check   # exit 3 = stale
python3 -I .claude/skills/screening-workbook/scripts/xlsx_to_csv.py           # regenerate all four
```

For ad-hoc reads of the xlsx itself, openpyxl read-only is fine
(`openpyxl.load_workbook(path, read_only=True)`; DOI URLs are in
`cell.hyperlink.target`, not the cell value), or use the helper module:

```python
import sys; sys.path.insert(0, ".claude/skills/screening-workbook/scripts"); import lvrwb
wb = lvrwb.Workbook("data/LVR_screening_sheet_2.xlsx")
wb.value("Screening", "H6"), wb.hyperlinks("Screening")["F6"], wb.lists(), wb.recompute("Counts")
```

## The included set (what extraction consumes)

```bash
python3 -I .claude/skills/screening-workbook/scripts/included.py                 # T/A Include or Maybe, not excluded at FT
python3 -I .claude/skills/screening-workbook/scripts/included.py --stage ft      # Full-text decision = Include only
python3 -I .claude/skills/screening-workbook/scripts/included.py -o analysis/included.csv
```

CSV columns: ID, Year, Authors, Title, Journal, DOI, Zotero key, the four
decision/reason columns, Notes, and `text_file`, the matching file in
`data/articles_text/` found by first-author surname + year (accents and
punctuation ignored, ties broken on title). It reads the xlsx, not the CSV,
and looks only at H-L, never at the AI columns. An empty `text_file` means
the full text has not been converted yet (see the pdf-to-text skill). Until
full-text screening is done, `--stage ft` is empty by design; say so rather
than substituting the T/A set.

## Writing cells

```bash
S=.claude/skills/screening-workbook/scripts
python3 -I $S/set_cells.py --dry-run --set 12 N Exclude --set 12 O "No questionnaire/screening item" --set 12 P "Prevalence survey, no self-report tool"
python3 -I $S/set_cells.py --set 12 N Exclude --set 12 O "No questionnaire/screening item" --set 12 P "..." --export
python3 -I $S/set_cells.py --edits suggestions.csv --export           # header: id,col,value  (or row,col,value)
python3 -I $S/set_cells.py --reviewer --set 5 H Include --export       # the reviewer said so
python3 -I $S/set_cells.py --counts B5 9                               # hand-typed Counts inputs B3/B4/B5
python3 -I $S/set_cells.py --recount                                   # only refresh cached Counts values
```

The first token of `--set` is the record ID (column A), or `row:N` for a
sheet row (row = ID + 1 today, but look it up rather than assume). `''`
clears a cell. Always `--dry-run` first when touching more than a few cells,
then run with `--export` so the CSVs follow. Report what changed, including
the Counts lines the script prints, and remind the user that suggestions in
N-S are advisory until the reviewer decides.

What the script does under the hood, so you can judge its output or do a
one-off edit by hand with `lvrwb.Workbook.set_cell`:

- Rewrites just the `<c>` element in `xl/worksheets/sheet2.xml`, keeping its
  `s` style (yellow/grey fill) or copying the column's usual style for a new
  cell. Strings are written as inline strings (`t="inlineStr"`), which Excel
  reads fine and which avoids renumbering `sharedStrings.xml`; numbers (ID,
  Year) as plain `<v>`. The `count` attribute of sharedStrings is recomputed.
- Leaves `<extLst>` (x14 validations), `<conditionalFormatting>`,
  `<hyperlinks>`, `<cols>`, styles and the sheet rels untouched, and refuses
  to write if any of them changed or the XML is no longer well-formed.
- Re-evaluates all 31 Counts formulas (`COUNTA`, `COUNTIF`, `SUMPRODUCT`,
  `+`/`-` over `$H$2:$H$136`, `$I`, `$J`, `$K`, `$N`) with `lvrwb.Evaluator`
  and patches their cached `<v>` in sheet3.xml. Excel would do this on the
  next open, but the CSV exports and anyone reading the file without Excel
  see only the cached values, so a write without a recount leaves the PRISMA
  numbers wrong. A formula the evaluator cannot handle aborts the write.
- Writes a new zip with the original entry order, timestamps and compression
  for every unchanged part, via a temp file and `os.replace`.

## Adding records (beyond row 136)

Every range stops at row 136: the Counts formulas, the three x14 validation
`sqref`s (H, I+K, J), the four conditional-formatting blocks (H, J, N, Q),
`autoFilter`, `dimension` and the `_FilterDatabase` name. `set_cells.py
--add-rows --set row:137 A 136 --set row:137 D "Title" ...` creates the row
with the right styles and extends all of them in one go (`extend_ranges`),
then recounts. Afterwards update the hand-typed source count on Counts
(`--counts B5 9` for a hand-added key source, or B3/B4 for a new database
search) so "Duplicates removed" (B7 = B6 - B8) stays meaningful, and give the
new record its DOI hyperlink by hand (a `<hyperlink>` plus a rels entry; see
the reference) or leave F as "No link". Keep IDs consecutive.

## Checklist after any write

1. `xlsx_to_csv.py --check` is clean (the script's `--export` does this).
2. `python3 -W ignore -c "import openpyxl; openpyxl.load_workbook('data/LVR_screening_sheet_2.xlsx')"` opens it (read only, never save).
3. The Counts lines printed by the script make sense (e.g. "Screened so far" rose by the number of new H values).
4. Tell the user which cells changed and whether the reviewer's columns were touched; committing is their call.

## When not to use the scripts

- Bulk re-screening by the reviewer in Excel: let Excel do it, then run
  `xlsx_to_csv.py` to refresh the exports.
- Changing formulas, layout, styles or drop-down lists: do it in Excel, or
  edit the XML by hand following `references/workbook-layout.md`; the
  evaluator only knows the formula shapes listed there.
- Anything on other workbooks: `lvrwb` is generic enough to read them, but
  the column rules and Counts logic here are specific to this file.
