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

## Status — 2026-10-26 — step 8: PRISMA flow, Methods draft, checklists

Run on Claude Sonnet 5.5 (`claude-sonnet-5-5`), no subagents, in the worktree `.claude/worktrees/chain-step8-prisma` (branch `worktree-chain-step8-prisma`). The flow diagrams and counts were already in the worktree from an earlier attempt at this step; I re-checked them (Counts export regenerated from the main checkout's current xlsx into a temp dir: identical numbers), opened both PNGs, and did tasks 3 to 5 here. The step 5 to 7 outputs (`analysis/extraction`, `risk_of_bias`, `synthesis`, `paper/tables`) were read from `.claude/worktrees/chain-step7-synthesis`, because the main checkout still lacks them. **Everything is PROVISIONAL and advisory.** H-L untouched, xlsx not saved, nothing under `data/` written, nothing committed (plan rule 8).

- **Reviewer flow** (`paper/figures/prisma_flow_reviewer.{svg,png}`, `paper/prisma_counts_reviewer.md`): identified 174 (78 + 88 + 8), duplicates 39, screened 135, excluded 27, sought 13, assessed 0, included 0. `DISCREPANCY`: 135 - 27 = 108 but sought = 13; 13 - 0 = 13 but assessed = 0; plus "screening is incomplete: 40 of 135". Red DRAFT banner present. T/A reasons: no questionnaire/screening item 18, not about low vision 6, wrong population 2, intervention only 1. Reviewer agreed with the AI on 25, changed 15 (37.5%).
- **Provisional flow** (`paper/figures/prisma_flow.{svg,png}`, `paper/prisma_counts.md`; PROVISIONAL in the legend and at the top of the .md): identified 174, duplicates 39, screened 135, excluded at T/A 81, sought 54, not retrieved 6 (IDs 30, 128, 129, 132, 133, 135), assessed 48, excluded at full text 17 (no accuracy/validation data 11, intervention only 3, review/opinion 2, not about low vision 1), included 31. Arithmetic checks pass (174-39=135; 135-81=54; 54-6=48; 48-17=31; reasons sum to 17). T/A exclusion reasons are not tabulated, because 95 of the 135 decisions are not the reviewer's. Built with `--json` and `--override`; the JSON itself was not kept in the repo.
- **Methods draft** (`paper/methods_draft.md`): decision note first (label "systematic search with narrative synthesis"; what changes if called a narrative review), then the templates filled, SWiM paragraph kept and bivariate deleted, SoF per-1000 sentence dropped, AI disclosure written, provisional-inclusion sentence marked for deletion.
- **Checklists** (`paper/checklists/`): `prisma2020_checklist.md`, `prisma_dta_checklist.md` filled with section names from the manuscript structure, no page numbers; `swim_checklist.md` copied from step 7. `checklist_status.py` (not strict): 0 blank in all three; 16 (PRISMA 2020) and 15 (DTA) marked N/A (abstract items "abstract word limit", 2, 13f, 20d, 21, D2, 16, 23). Items carrying a [VERIFY] flag: PRISMA 2020 24a, 24b, 25, 26; DTA 5, 27.
- **Discrepancy to know about:** the flow's 31 included records are the provisional set (ID 128 excluded as not retrieved); extraction and synthesis used 32 records (31 + ID 128) and collapsed them to 31 independent datasets (IDs 92 and 128 are one cohort). Same number, different sets. The flow does not show ID 128 as included although the manuscript relies on it.
- **Placeholders I could not fill** (all marked [VERIFY] or [PENDING] in `methods_draft.md`): registration status and protocol location; reviewer's initials; model id and date of the earlier AI passes on IDs 1-127 (N-P, Q-S) and of chain steps 1 and 2; the reviewer's decision on which search string the review reports; second-reviewer initials, kappa and resolution (sample of 27, seed 20261004, has no decisions yet); counts of extracted values corrected and risk-of-bias judgements changed (no reviewer checking done); funding statement and competing interests; whether the overlap decision for Wu 2024/2026 is confirmed; Scopus counts "to be typed from the interface".
- **AI disclosure, verbatim** (from `paper/methods_draft.md`): "We used large language models from Anthropic for the following tasks: Claude Fable 5.1 (`claude-fable-5-1`) as the default model for the coordinating chain steps of risk of bias and of synthesis on 26 October 2026; and Claude Sonnet 5.5 (`claude-sonnet-5-5`) for the steps run on that model and for every subagent, all at medium effort or higher, on 26 October 2026 [VERIFY: model ids for chain steps 1 and 2 and for the earlier AI screening passes on records 1 to 127, not recorded in the project files]. The tasks were: (1) diagnosing why the original search missed two papers, testing a minimal edit and an eight-arm revision of the PubMed string against key sources and held-out papers, drafting a Scopus translation (not run), and running a backward citation search; (2) producing advisory include, exclude or maybe suggestions with reasons for each title and abstract, recorded separately from the reviewer's decisions, and applying the full-text criteria to 48 articles (one subagent per record); (3) converting PDF articles to text and rebuilding one article's text from XML; (4) producing two passes of data extraction for 32 and 6 papers respectively, reconstructing 2x2 tables, and building the instrument catalogue; (5) drafting QUADAS-2, COSMIN and AGREE II assessments from the article text; (6) writing and running the analysis scripts for agreement statistics, independent-dataset detection, accuracy tables, plots, COSMIN rating summaries and the PRISMA flow diagram; and (7) drafting the Methods text, checklists and manuscript text [VERIFY: the manuscript drafting steps follow this one; revise this list to what was actually done]. Every screening decision, extracted value, risk-of-bias judgement and analytic choice was made or verified by the authors against the source documents [VERIFY: not yet true for the provisional items above; it becomes true only when the reviewer has completed columns H to L and checked the extraction and risk-of-bias tables, and this sentence must not be published before then]. The reviewer's decision differed from the model's first-pass suggestion in 15 of 40 records at title/abstract screening (37.5%) [UPDATE when all 135 are decided]; the proportion of extracted values corrected and of risk-of-bias judgements changed is not yet available because that checking has not been done. The model was not used to generate or interpret study results beyond the tasks listed, and no unpublished patient data were entered into it. The full texts of published articles were supplied to the model for extraction and appraisal. The authors take full responsibility for the content of this article."
- **Next step needs:** merge this worktree's `paper/` into the main checkout alongside step 7's (`paper/figures/` has no name clash: step 7 wrote forest/roc/evidence-map files; mine are `prisma_flow*`); the plan doc copies in the step 5 to 8 worktrees need merging by hand. Step 9 should cite Figure 1 as the provisional diagram and keep the [VERIFY] flags until the reviewer answers.
