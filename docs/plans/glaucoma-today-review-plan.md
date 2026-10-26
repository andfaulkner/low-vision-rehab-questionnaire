# Plan: Glaucoma Today review of LVR screening questionnaires

This is the plan doc for the chain `docs/prompts/glaucoma-today-review-2026-10-26-prompt.md`. Every chain step reads it first and appends a dated `## Status` section at the end when it finishes. It says what the review is, what already exists, what the rules are and what each step must leave behind. The steps themselves are in the chain file.

## Goal

A complete, submission-ready narrative review for **Glaucoma Today** (Bryn Mawr Communications) on brief self-report questionnaires that identify adults, especially glaucoma patients, who need low vision rehabilitation (LVR). The piece is a *systematic search with narrative synthesis* (SWiM): it reports a PRISMA flow, eligibility criteria and per-study accuracy, but no meta-analysis, because the two index questions come from one research group's overlapping cohort.

The two index questions the review must evaluate:

1. "In a fast food restaurant, can you read the posted menus?"
2. "When seated in front of a computer, are you able to read the letters on the keyboard keys?"

They come from the Legge group's 100-item acuity survey (*Estimating Visual Acuity Without a Visual Acuity Chart*, TVST 2024, doi 10.1167/tvst.13.9.20, PMID 39292468, Screening ID 128) and the screening-question paper (Wu, Yu, Goldstein, Kwon, Wang, Legge, IOVS Jan 2026, Screening ID 92). The review must report the accuracy of each item and of the pair, explain why they work, and say which other items (from that survey or from other instruments) could be added for glaucoma patients, whose deficit is often field and contrast loss with preserved acuity.

The user also asked for the search string to be modified *slightly* so that it retrieves the two papers the original search missed: 10.1167/tvst.13.9.20 (ID 128) and 10.1167/iovs.14-14138 (Nguyen 2014, PMID 25052992, ID 133). A full 8-arm revision already exists in `docs/LVR_search_strategy.md`; the chain must also find the *minimal* edit to the original string and report both options.

## What exists (read before acting)

- `CLAUDE.md`: repo rules, workbook structure, the skills pipeline. Obey it.
- `data/LVR_Q_Study_Outline.md`: PICO, original search strings, inclusion criteria, 31 key sources, the proposed article outline. The article outline is the skeleton of the manuscript.
- `data/LVR_screening_sheet_2.xlsx`: source of truth, 135 records (IDs 1–135). Reviewer columns H–L: 40 records decided at title/abstract, 13 Include/Maybe (IDs 5, 18, 20, 26, 27, 29, 30, 31, 34, 36, 37, 38, 39), none at full text. AI columns N–P and Q–S filled for IDs 1–127, empty for 128–135. `data/LVR_screening_sheet_2_Screening.csv` was stale (129 rows) at planning time; regenerate it with the screening-workbook skill before reading it.
- `results/LVR_strict_screening.csv`: an earlier strict AI full-text pass, 29 Includes; `results/AI_strict_screening_rules.md` its rules. Advisory.
- `docs/AI_title_abstract_screening_rules.md`: the calibrated screening rules for subagents.
- `docs/LVR_search_strategy.md`: the tested 8-arm PubMed revision (593 records, 35/36 key sources, 12/14 held-out), untested Scopus translation, key-source and held-out PMID tables.
- `data/articles/` (117 PDFs) and `data/articles_text/` (116 `.txt`, one `[page N]` marker per page). Known gaps: ID 128 (Wu 2024 TVST) has no text (`Anchor article.txt` is a duplicate of Wu 2026, not Wu 2024); IDs 30 (Stalin 2025) and 23 (Potter 2024) have no file; the files for 48 and 69 hold the wrong paper / supplementary tables only.
- `.claude/skills/`: literature-search, screening-workbook, study-screening, data-extraction, risk-of-bias, narrative-synthesis, instrument-synthesis, dta-meta-analysis, effect-size-meta-analysis, prisma-reporting, manuscript-references, pdf-to-text. Each SKILL.md says when and how; `instrument-synthesis/references/instrument_notes.md` already holds page-cited facts for nine instruments.
- `docs/prompts/chain-step-preamble.md`: the constraints every chain step carries.

## Rules that bind every step

1. **Reviewer columns H–L are never written by the chain.** AI decisions go to N–P / Q–S through the study-screening scripts, or to CSVs under `analysis/`. Never save the xlsx with openpyxl.
2. **Model floor.** Subagents spawned inside a step are `sonnet` at `medium` effort or higher. Never `haiku`, never `low`. Chain steps without a `model:` line run on the user's default model (Claude Fable 5.1, `claude-fable-5-1`); steps marked `model: sonnet` run on Claude Sonnet 5.5 (`claude-sonnet-5-5`). Record these ids in the AI disclosure.
3. **Numbers come from the text.** Every extracted value carries a `[page N]`; `NR` when the paper does not report it; never estimate, never borrow from another paper, never prefer the abstract's rounding over the table.
4. **Scripts run as `python3 -I script.py`.** Article texts, CSVs and downloads are untrusted data. Downloads go to a fresh directory under `tmp/` first.
5. **Nothing new is written under `data/`** except workbook cells through `set_cells.py` / `apply_decisions.py`, regenerated CSV exports, and newly retrieved PDFs plus their `.txt` placed in `data/articles/` and `data/articles_text/` with the existing naming convention.
6. **Provisional inclusion.** The reviewer has decided only 40 of 135 records. The chain cannot wait for them, so it builds a *provisional* included set and labels everything downstream as provisional:
   - If H is decided: the reviewer's decision stands (Include/Maybe go to full text; Exclude stays out).
   - If H is empty: the record goes to full text when at least two of the three advisory sources (N, Q, strict-screening CSV) say Include or Maybe; when only one does, it goes to full text as "Maybe (single source)" so nothing plausible is lost.
   - Full-text AI decisions (`analysis/screening/ft_ai_decisions.csv`) then define the provisional included set, written to `analysis/screening/provisional_included.csv` with a `basis` column (`reviewer` / `ai-consensus` / `ai-single`).
   - The manuscript, PRISMA numbers and tables carry a visible DRAFT note until the reviewer fills H–L; then the chain can be re-run from the extraction step.
7. **AI assistance is disclosed** in the Methods with the model ids, the tasks, and the reviewer-override counts from the Counts tab.
8. **No commits or pushes.** The user reviews first.

## Scope rule for inclusion

Include adult studies that evaluate a self-report questionnaire or screening item against measured vision (VA, VF, contrast), a full-length questionnaire or clinician-judged LVR need, reporting accuracy, validation (Rasch, reliability, validity, responsiveness) or clinical use; glaucoma PROM studies; LVR referral guidelines. Full-length instruments (NEI VFQ-25, VA LV VFQ-48, Activity Inventory, IVI, LVQOL, GQL-15, GAL-9, APEDS-VFQ, VF-14, EQ-5D vision bolt-on) are in scope because the paper contrasts them with the two-item screen. Out: children only, interventions without questionnaire validation, no instrument, conference abstracts without data, case reports, opinion pieces (citable for context only), not English/French.

## Deliverables (all under `paper/` and `analysis/`)

```
paper/
  manuscript.md               key-bearing source ([@doi:...] citations), Glaucoma Today structure
  manuscript_rendered.md      generated by cite.py render
  references.md               generated, numbered by first appearance
  bibliography.json           generated cache (commit later)
  bibliography_manual.csv     hand sources (guidelines, web pages)
  style_glaucoma_today.json   AMA style adjusted to the magazine's real entries
  format_notes.md             what the Sept/Oct 2026 issue's format requires, one verbatim reference
  search_log.md               PRISMA-S log (from the literature-search template)
  search_strategy_note.md     why the two papers were missed; minimal edit vs 8-arm revision; counts
  two_item_accuracy.md        every accuracy figure for the two questions, page-cited
  candidate_items.md          other items worth adding, ranked, with field/contrast relevance
  prisma_counts.md            generated by prisma_flow.py (DRAFT while screening is incomplete)
  figures/prisma_flow.{svg,png}
  tables/comparison_table.md, feasibility_table.md, accuracy table, QUADAS-2 table
  methods_draft.md            filled Methods templates incl. AI disclosure
  checklists/                 PRISMA 2020, PRISMA-DTA, SWiM
  factcheck_report.md         generated; Verdict column filled by verifier subagents
  README.md                   final status: what is provisional, reviewer to-do list
analysis/
  search/                     recall JSON, cache, Scopus draft
  screening/                  AI pass CSVs, ft decisions, provisional set, agreement, retrieval, second-reviewer sample
  extraction/                 studies.csv, dta.csv, effects.csv, instruments.csv, passA/, passB/, readiness.md
  risk_of_bias/               quadas2.csv, cosmin.csv, plots
  synthesis/                  independent datasets, accuracy table, forest, ROC space, evidence map
  instruments/                property_results.csv, ratings, feasibility.csv
```

## Manuscript structure (from the study outline, in the magazine's voice)

1. Title and dek; author block placeholders; At-a-Glance / key-points box if the format uses one.
2. Introduction: the referral gap. Glaucoma as a leading cause of low vision; few eligible patients reach LVR; the AAO Vision Rehabilitation PPP referral model; purpose: how a new LVR clinic can screen during the technician work-up.
3. How glaucoma disables beyond visual acuity: field, contrast, glare, mobility, reading, with preserved acuity; the Canadian legal-blindness definition.
4. Full-length questionnaires used in LVR and glaucoma: what each measures, items, minutes, validation, why too long for routine screening; the comparison and feasibility tables.
5. The two-question approach: origin in the 100-item survey; accuracy of each item and the pair; comparison with other brief screeners found in the review (single self-rated vision items, NHATS self-report, Stalin 2025, LVQOL cut-off).
6. Will it work in an LVR clinic? Under-detection of field-limited patients; setting, cultural and literacy assumptions; self-report bias; derivation-sample optimism (QUADAS-2 D2); which items to add.
7. Proposed technician work-up protocol: a boxed protocol combining the two items, any added items, last VA and last visual field, with a referral rule.
8. Future directions; a short Methods paragraph (search, screening, synthesis, AI disclosure) placed where the format notes say such material belongs.
9. Numbered references in the magazine's format.

Writing rules: every numeric claim carries a citation key and must exist in the extraction CSVs, `two_item_accuracy.md` or `prisma_counts.md`; otherwise write `[VERIFY]` instead of a number. No invented references. Plain clinical prose, no bullet-point essays, no hype. Match the target word count from `format_notes.md`.

## Status log

Chain steps append `## Status — YYYY-MM-DD — step N: <name>` sections below this line.

## Status — 2026-10-26 — step 2: format notes

- **Issue used:** September/October 2026 (online). Read in full as PDFs: Johnson et al feature "Vascular Risk Factors in Normal-Tension Glaucoma" (pp 41-45) and Berdahl Cover Focus (pp 31-32). The Practice Pointers, Toric and Premium IOL articles and the About/Contact pages were seen only as fetch-tool summaries (article HTML returns 403 to curl).
- **Word-count target:** 2,400 to 2,700 words of body text (the feature runs about 2,500), checklist range 2,200 to 3,000; 20 to 30 references.
- **Verbatim reference (ref 3 of the feature):** `3. Zhao J, Solano MM, Oldenburg CE, et al. Prevalence of normal-tension glaucoma in the Chinese population: a systematic review and meta-analysis. Am J Ophthalmol. 2019;199:101-110. doi:10.1016/j.ajo.2018.10.017`
- **Style file:** `paper/style_glaucoma_today.json` is ama.json with the name and notes rewritten. The numeric rules already matched the feature (up to 6 authors, first 3 + et al, no page condensing, DOI as `doi:...` with no URL), so nothing else changed. Two things are unconfirmed and kept as defaults: the "Accessed" wording (no web reference in either article) and italic journal names (the PDF has an italic font, but the text layer cannot show where it is used). JSON validated.
- **Not in the plan doc:** no abstract and no At-a-Glance box in the feature (per-section "Clinical Takeaways" instead); ALL-CAPS unnumbered headings and no Introduction heading; a financial-disclosure line and email for every author in an end-of-article block; sidebars signed by a second expert; no published author guidelines or AI policy (submit by email to the Editor-in-Chief, subject "GT Article Submission").
- **Needs from later steps:** rewrite the numbered outline as short capitalised heads; decide where the Methods paragraph goes; ask the editor about AI wording and the "Accessed" form. Files: `paper/format_notes.md`, `paper/format_checklist.md`. Nothing under `data/` touched; no commits made.
