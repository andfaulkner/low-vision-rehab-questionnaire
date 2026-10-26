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
  - **N–P (grey) are AI suggestions:** Suggested decision, Suggested reason, and a one-line AI rationale. Q–S hold a second, independent AI pass (decision, reason, rationale) for IDs 1–127; see `.claude/skills/screening-workbook/references/workbook-layout.md`. They are advisory only. Never copy them into H–L as if they were the reviewer's decisions. The review's methods must report that AI assistance was used.
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

## Systematic-review skills

The skills under `.claude/skills/` form a pipeline from the search to the manuscript. Each one's SKILL.md says when to use it; the order below is the order of the work.

1. `literature-search`: test search-string recall against the key-source PMIDs, snowball from included studies, deduplicate candidates against the Screening tab, keep the PRISMA-S search log.
2. `screening-workbook`: read, edit and re-export the source xlsx safely, and list the included records.
3. `study-screening`: AI-assisted title/abstract and full-text screening into the AI columns, reviewer-vs-AI agreement (kappa), second-reviewer sample, full-text retrieval tracking.
4. `data-extraction`: extract study characteristics, 2x2 tables and other effect sizes from `data/articles_text/` into evidence CSVs under `paper/`.
5. `risk-of-bias`: QUADAS-2 (and COSMIN) assessments with traffic-light plots.
6. `narrative-synthesis`: synthesis without meta-analysis (SWiM): independent-dataset grouping, per-study accuracy tables and unpooled forest plots, evidence maps, vote-counting rules.
7. `instrument-synthesis`: the instrument comparison: COSMIN ratings of measurement properties per questionnaire, feasibility table for a technician work-up.
8. `dta-meta-analysis` and `effect-size-meta-analysis`: pooling, only for a comparison with at least four independent studies.
9. `prisma-reporting`: PRISMA 2020 flow diagram from the Counts tab, checklists, GRADE summary of findings, Methods text including the AI-assistance disclosure.
10. `manuscript-references`: citation keys to a numbered reference list via Crossref/PubMed, and a fact-check of every cited number against the source text and the extraction CSVs.

The primary question cannot be meta-analysed: the two screening items (restaurant menu, keyboard) come from one research group's overlapping cohort (TVST 2024 and Wu 2026), so their accuracy is reported per study and the synthesis follows SWiM. Pool only where a comparison has four or more independent studies of the same test against the same reference standard.

Scripts run as `python3 -I script.py`; those that need numpy, scipy or matplotlib re-add the user site-packages directory themselves. Install with `python3 -m pip install --user --break-system-packages numpy scipy matplotlib` if an import still fails. Every number an AI extracts, screens, rates or pools is advisory until the reviewer has checked it against the source text.
