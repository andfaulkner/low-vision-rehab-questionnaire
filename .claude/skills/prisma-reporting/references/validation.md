# Validation of the scripts

What was run on 25 Oct 2026, with expected vs obtained values. No published worked example with exact numbers was available from memory for the flow diagram or the per-1000 table, so the checks use arithmetic that can be verified by hand, plus the repository's real Counts export. Re-run these after any change to the scripts.

## prisma_flow.py

**Real Counts CSV (`data/LVR_screening_sheet_2_Counts.csv`, screening 40/135 done).** Expected: parsed PubMed 78, Scopus 88, other 8, duplicates 39, screened 135, excluded 27, sought 13, assessed 0, included 0; reasons parsed (18 no questionnaire, 6 not about low vision, 2 wrong population, 1 intervention); the note "screening is incomplete: 40 of 135"; two discrepancies (135 − 27 ≠ 13; 13 − 0 ≠ 0); DRAFT banner; exit 2. Obtained: exactly that. Reading the same tab from the xlsx with `--xlsx` gave a byte-identical `prisma_counts.md` apart from the source line.

**Synthetic complete CSV (`evals/flow-from-complete-counts/files/`).** Hand arithmetic: 166 + 8 − 39 = 135; 135 − 110 = 25; "Full text not available" 1 → not retrieved, so 25 − 1 = 24 assessed; full-text reasons 9 + 2 + 1 = 12 and 12 + 1 = 13 = the workbook's "Excluded at full text"; 24 − 12 = 12 included; T/A reasons 8 + 60 + 7 + 30 + 5 = 110. Obtained: no discrepancies, exit 0, table and Results sentence with those numbers.

**Synthetic JSON (`--json`), same-pipeline and separate modes.** Separate mode with `other = {sought 8, not_retrieved 0, assessed 8, excluded {2}, included 6}` and left column 127 → 105 excluded → 22 sought → 1 not retrieved → 21 assessed → 11 excluded → 10, plus 6 = 16 reports included: no discrepancies, exit 0; the diagram showed the official right-hand column with its own four boxes and an arrow into the Included box.

**Deliberate errors.** `--override reports_not_retrieved=2` on the complete JSON produced "25 − 2 = 23 but assessed = 24" and "24 − 11 = 13 but included = 12" (the second because `--override "reports_excluded.Other (see notes)=0"` removed one reason), exit 2. Removing `other_sources` but leaving T/A reasons summing to 110 against 102 excluded produced the reason-sum discrepancy. A missing CSV path exits 1 with a message.

**Layout.** PNGs were opened and checked for: side labels aligned to their rows, no arrow crossing a box (the same-pipeline arrow runs below the identification row), no `(n = 0)` split across lines, figure cropped to content, DRAFT banner when discrepancies exist, single-column template when other sources = 0.

## sof_table.py

**Per-1000 cells.** Input sens 0.80 (0.70–0.88), spec 0.75 (0.65–0.83). Hand calculation at prevalence 0.30: TP = 300 × 0.80 = 240 (210–264); FN = 60 (36–90); TN = 700 × 0.75 = 525 (455–581); FP = 175 (119–245). At 0.10: TP 80 (70–88), FN 20 (12–30), TN 675 (585–747), FP 225 (153–315). Obtained: identical.

**Certainty arithmetic.** high − serious (risk of bias) − serious (inconsistency) → low: obtained LOW with footnotes a and b. high − serious − very serious → very low: obtained VERY LOW (floor). Per-row specificity override (`ratings_specificity: imprecision very serious` vs sensitivity serious) gave MODERATE for TP/FN and LOW for TN/FP.

**Readers.** (1) `dta_pool.py` layout: `{"k": 5, "pooled": {"sens": .., "sens_lo": .., "sens_hi": .., "spec": ..}}` with participants summed from `per_study.csv` (861 = TP+FP+FN+TN over 5 rows): read correctly. (2) nested `analyses.<name>.sensitivity.{estimate, ci_low, ci_high}` and `summary.sens: [est, lo, hi]`: read correctly via `--analysis` / entries `analysis`. (3) `"pooled": null` refuses with the not-pooled message, exit 1. (4) A CI with lo > est (`--sens 0.9 0.95 0.8`) is rejected, exit 1.

## checklist_status.py

Blank asset checklists: 54 items (42 PRISMA 2020 + 12 abstract) and 38 (27 PRISMA-DTA + 11 abstract) all blank, exit 0. A copy with item 1 filled, 13d "N/A: no meta-analysis", 16a `{Results, Figure 1}` and 24a "TBD": 1 filled, 1 N/A, 52 blank (placeholders and TBD counted as blank), `--strict` exit 1. A file with no checklist table: exit 2.

## Not verified

- The exact item wording of PRISMA 2020, PRISMA-DTA, PRISMA-S and the abstract checklists is condensed from memory; the official checklists should be used for submission.
- The citations in `citations.md` were written from memory; a few are marked "verify".
- The eval cases were not run with `claude plugin eval`; their expected outcomes were checked by running the scripts directly on the case inputs.
