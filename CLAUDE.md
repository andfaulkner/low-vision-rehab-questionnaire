# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

There is no code here. This is the data folder for a systematic literature review: title/abstract and full-text screening of studies on **self-report questionnaires and screening items for low vision rehabilitation (LVR)**. It has no build, lint or test steps, and it is a git repository pushed to the private GitHub repo `andfaulkner/low-vision-rehab-questionnaire`. Commits and pushes use the `andfaulkner` account through a repo-local identity and credential helper, not the active `gh` account.

- `data/LVR_screening_sheet_2.xlsx` is the **source of truth**: a screening workbook with formulas and drop-down validation.
- `data/LVR_screening_sheet_2_<Sheet>.csv` are flat exports of each tab, one file per tab, for easy reading. They are snapshots: formulas are flattened to their cached values, and they go out of date whenever the xlsx changes. Regenerate them rather than editing them.
- To work with an xlsx, first check whether `openpyxl` is installed (`python3 -c "import openpyxl"`).
  - **If it is,** use it to read xlsx files, and to write xlsx files other than the source workbook. Never save the source workbook with openpyxl: its drop-downs are stored as an Excel extension (`x14:dataValidations`) that openpyxl deletes. Edit its XML directly instead. The DOI hyperlinks are on the cells (`cell.hyperlink`), not in the cell values. Saving any workbook with openpyxl also removes the cached results of its formulas. When you edit the XML, update the cached `<v>` values of any formula whose result changes, because the CSV exports read them.
  - **If it isn't,** unzip the xlsx and parse `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` with the Python standard library. Hyperlinks are stored in `xl/worksheets/_rels/sheet2.xml.rels`, not in the cells. Homebrew `python3` refuses a plain `pip install`; to install openpyxl, run `python3 -m pip install --user --break-system-packages openpyxl`.

## Workbook structure

The tabs depend on each other, so changing one can silently break another.

- **Instructions**: how to screen, plus the inclusion criteria (see below).
- **Screening**: one row per record (135 records, IDs 1–135, rows 2–136). Records 1–127 came from the PubMed and Scopus searches. Records 128–135 are key sources from `data/LVR_Q_Study_Outline.md` that the searches missed and were added by hand. They have no Zotero key or AI suggestions yet.
  - A–G are bibliographic: ID, Year, Authors, Title, Journal, DOI link, Abstract. In the xlsx, the DOI cell shows "Open" and the URL is a hyperlink behind it; the CSV holds the URL itself. "No link" means there is no DOI. "Missing" in Abstract means there is no abstract.
  - **H–L (yellow) are filled in by the human reviewer:** Title/abstract decision, Exclusion reason (T/A), Full-text decision, Exclusion reason (FT), Notes.
  - M is the Zotero key, which links the row back to the reviewer's Zotero library.
  - **N–P (grey) are AI suggestions:** Suggested decision, Suggested reason, and a one-line AI rationale. They are advisory only. Never copy them into H–L as if they were the reviewer's decisions. The review's methods must report that AI assistance was used.
- **Lists**: the allowed values for the drop-downs. T/A decision: Include / Exclude / Maybe. Full-text decision: Include / Exclude. There are 10 fixed exclusion reasons, for example "No questionnaire/screening item" and "Other (see notes)". Values in Screening must match these strings exactly, or the counts will miss them.
- **Counts**: the numbers for the PRISMA flow diagram, computed by `COUNTA`/`COUNTIF`/`SUMPRODUCT` over the Screening ranges `$H$2:$H$136`, `$I`, `$J`, `$K` and `$N`.
  - PubMed (78) and Scopus (88) are typed in by hand from the search log dated 4 Oct 2026. "Other sources" (8) is typed in by hand too: it counts records 128–135.
  - Duplicates removed = total identified − records screened.
  - Exclusion-reason counts look up the label text in column A, so a reason must be spelled exactly as it appears in Lists.
  - The last two rows count how often the reviewer agreed with, or overrode, the AI decision in N.
  - **The ranges stop at row 136.** If you add records, you must extend every Counts formula, plus the data-validation, conditional-formatting and filter ranges on Screening.

## Screening rules (from the Instructions tab)

- **Include:** adults (18+); the study evaluates a self-report questionnaire or screening item against a measure of vision or LVR need; it reports accuracy, validation or clinical use. Glaucoma PROM studies and LVR referral guidelines also count.
- **Exclude:** children only; rehabilitation interventions with no questionnaire data; no questionnaire or screening item; conference abstracts without data; not in English or French; case reports or opinion pieces.
- Include and Maybe at title/abstract both go on to full-text review.
- Every Exclude gets exactly one reason.
- Fill both full-text columns for every Include or Maybe paper.
