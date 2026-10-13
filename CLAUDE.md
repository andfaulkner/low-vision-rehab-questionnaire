# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

There is no code here. This is the data folder for a systematic literature review: title/abstract and full-text screening of studies on **self-report questionnaires and screening items for low vision rehabilitation (LVR)**. It has no build, lint or test steps, and it is not a git repository.

- `data/LVR_screening_sheet_2.xlsx` is the **source of truth**: a screening workbook with formulas and drop-down validation.
- `data/LVR_screening_sheet_2_<Sheet>.csv` are flat exports of each tab, one file per tab, for easy reading. They are snapshots: formulas are flattened to their cached values, and they go out of date whenever the xlsx changes. Regenerate them rather than editing them.
- `openpyxl` is not installed. To read the xlsx, unzip it and parse `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` with the Python standard library. Hyperlinks are stored in `xl/worksheets/_rels/sheet2.xml.rels`, not in the cells.

## Workbook structure

The tabs depend on each other, so changing one can silently break another.

- **Instructions**: how to screen, plus the inclusion criteria (see below).
- **Screening**: one row per record (127 records, IDs 1–127, rows 2–128).
  - A–G are bibliographic: ID, Year, Authors, Title, Journal, DOI link, Abstract. In the xlsx, the DOI cell shows "Open" and the URL is a hyperlink behind it; the CSV holds the URL itself. "No link" means there is no DOI. "Missing" in Abstract means there is no abstract.
  - **H–L (yellow) are filled in by the human reviewer:** Title/abstract decision, Exclusion reason (T/A), Full-text decision, Exclusion reason (FT), Notes.
  - M is the Zotero key, which links the row back to the reviewer's Zotero library.
  - **N–P (grey) are AI suggestions:** Suggested decision, Suggested reason, and a one-line AI rationale. They are advisory only. Never copy them into H–L as if they were the reviewer's decisions. The review's methods must report that AI assistance was used.
- **Lists**: the allowed values for the drop-downs. T/A decision: Include / Exclude / Maybe. Full-text decision: Include / Exclude. There are 10 fixed exclusion reasons, for example "No questionnaire/screening item" and "Other (see notes)". Values in Screening must match these strings exactly, or the counts will miss them.
- **Counts**: the numbers for the PRISMA flow diagram, computed by `COUNTA`/`COUNTIF`/`SUMPRODUCT` over the Screening ranges `$H$2:$H$128`, `$I`, `$J`, `$K` and `$N`.
  - PubMed (78) and Scopus (88) are typed in by hand from the search log dated 4 Oct 2026.
  - Duplicates removed = total identified − records screened.
  - Exclusion-reason counts look up the label text in column A, so a reason must be spelled exactly as it appears in Lists.
  - The last two rows count how often the reviewer agreed with, or overrode, the AI decision in N.
  - **The ranges stop at row 128.** If you add records, you must extend every Counts formula and the data-validation ranges on Screening.

## Screening rules (from the Instructions tab)

- **Include:** adults (18+); the study evaluates a self-report questionnaire or screening item against a measure of vision or LVR need; it reports accuracy, validation or clinical use. Glaucoma PROM studies and LVR referral guidelines also count.
- **Exclude:** children only; rehabilitation interventions with no questionnaire data; no questionnaire or screening item; conference abstracts without data; not in English or French; case reports or opinion pieces.
- Include and Maybe at title/abstract both go on to full-text review.
- Every Exclude gets exactly one reason.
- Fill both full-text columns for every Include or Maybe paper.
