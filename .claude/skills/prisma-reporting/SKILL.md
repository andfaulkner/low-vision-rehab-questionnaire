---
name: prisma-reporting
description: Produce the reporting scaffolding of the systematic review: the PRISMA 2020 flow diagram (SVG/PNG) generated from the screening workbook's Counts tab with its arithmetic checked, PRISMA 2020 and PRISMA-DTA checklists mapped to the manuscript, a PRISMA-S search-log note, a GRADE Summary of Findings table for test accuracy (true/false positives/negatives per 1000 at chosen prevalences, certainty rated over five domains), and Methods-section templates including the mandatory AI-assistance disclosure. Use when asked for a PRISMA diagram, flow chart, "how many records/studies", checklist, reporting guideline, GRADE, certainty of evidence, summary of findings, SoF table, Methods paragraph, study selection text, "write up the search/screening", AI disclosure wording, or whether a narrative review needs PRISMA. Run it after screening is complete and after dta-meta-analysis / risk-of-bias, before writing Results.
---

# PRISMA reporting

Everything here produces manuscript-facing artefacts under `paper/` (never `data/`): `paper/figures/` for the flow diagram, `paper/prisma_counts.md` for the numbers and Results sentences, `paper/checklists/` for the filled checklists, `paper/sof/` for Summary of Findings tables, `paper/methods_draft.md` for the Methods text. Inputs come from `data/` (the Counts export) and from the other skills' outputs under `analysis/` (`analysis/dta/<name>/results.json`, `analysis/risk_of_bias/`). The diagram and tables are generated, not hand-edited: when a count changes, re-run the script.

Run the scripts with `python3 -I` (isolated mode: the script's own directory and the environment are kept off `sys.path`, so a planted `json.py` next to an input file cannot be imported). `prisma_flow.py` re-adds the user site-packages directory itself, where matplotlib is installed, so `-I` works. `checklist_status.py` is standard-library only. If an import fails: `python3 -m pip install --user --break-system-packages matplotlib openpyxl`.

## Workflow

1. **Flow diagram first, and reconcile it with the workbook before writing any Results.** Re-export the Counts tab (or read the xlsx read-only) and run:

   ```bash
   python3 -I .claude/skills/prisma-reporting/scripts/prisma_flow.py \
       --counts-csv data/LVR_screening_sheet_2_Counts.csv \
       --footnote "Records from other sources were screened together with the database records."
   ```

   It writes `paper/figures/prisma_flow.{svg,png}` and `paper/prisma_counts.md` (table, exclusion reasons, Results sentences). It checks that identified − removed = screened, screened − excluded = sought, sought − not retrieved = assessed, assessed − excluded = included, and that reason counts sum correctly. Every failure is printed as `DISCREPANCY:`, the diagram gets a red DRAFT banner, and the exit status is 2. Until column H of the Screening tab is complete the checks fail by construction ("screening is incomplete: 40 of 135"); say so to the user and do not present the numbers as results. When a count is genuinely right but the workbook cannot express it (studies ≠ reports, a retrieval failure logged as an exclusion), use `--override key=value` and record the reason in the figure legend. `--json-schema` prints the JSON layout for `--json` input; `--xlsx` reads the workbook's cached values without saving it. Open the PNG and check it before using it.

   The 8 hand-added key sources are drawn in the "other methods" column. By default (`--other-mode same-pipeline`) their arrow joins "Records screened", because that is how the workbook counts them; `--other-mode separate` gives the official right-hand column but needs `other.sought/not_retrieved/assessed/included` from a filter of IDs 128–135. `references/prisma2020_boxes.md` defines every box and the workbook cell that feeds it.

2. **Risk of bias and pooling** come from the `risk-of-bias`, `dta-meta-analysis` and `effect-size-meta-analysis` skills. This skill only reports them.

3. **Summary of Findings (GRADE for test accuracy)**, one block per index test × reference standard that was pooled:

   ```bash
   python3 -I .claude/skills/prisma-reporting/scripts/sof_table.py \
       --results-json analysis/dta/two_questions/results.json \
       --index-test "Two screening questions" --reference "VA worse than 6/12" \
       --prevalence 0.1 0.3 0.5 --risk-of-bias serious --inconsistency serious \
       --footnote "risk_of_bias=Three of five studies used a case-control design." \
       --footnote "inconsistency=Sensitivity ranged from 0.55 to 0.92." \
       --out paper/sof/two_questions.md
   ```

   or `--entries sof.json` for several blocks (`--entries-schema` prints the layout; each entry may point at its own `results_json`). The script computes TP/FN/TN/FP per 1000 from the pooled sensitivity/specificity and their CIs, and the certainty from the domain judgements you give it (high minus one level per "serious", two per "very serious"). The judgements are yours: take risk of bias from the QUADAS-2 table, inconsistency from the forest plot and between-study variance, imprecision from the per-1000 ranges, and write a footnote for every downgrade. Rules, starting levels for case-control designs, and when a SoF table is wrong (no pooled estimate, AUC-only or validation-only evidence) are in `references/grade_dta.md`; the finished layout is in `assets/grade_dta_sof_template.md`. If `results.json` says `"pooled": null`, the script refuses, and the right output is a per-study table with narrative certainty.

4. **Methods text.** Copy the paragraphs you need from `assets/methods_templates.md` into `paper/methods_draft.md`, fill the {placeholders} from the workbook, the search log and the analysis outputs, and keep the SWiM narrative-synthesis paragraph or the bivariate paragraph, not both. The AI-assistance disclosure is mandatory wherever AI output fed the manuscript (search strategy, screening suggestions, extraction, QUADAS-2 drafts, scripts, drafting): name the model and version, list the tasks, state that the reviewer made every decision, and give the percentage of AI suggestions the reviewer overrode (the Counts tab's last two rows). Check Glaucoma Today's author instructions for their own AI and reporting requirements; if silent, disclose anyway.

5. **Checklists last**, once section numbers and pages exist. Copy `assets/prisma2020_checklist.md` and `assets/prisma_dta_checklist.md` to `paper/checklists/`, fill the "Where reported" column (section/page, or "N/A: reason"), then:

   ```bash
   python3 -I .claude/skills/prisma-reporting/scripts/checklist_status.py paper/checklists/*.md --strict
   ```

   lists every item still blank and exits 1 while any remain. PRISMA-DTA items 14(b) (thresholds) and D1 (clinical role of the index test) and PRISMA 2020 items 8, 9, 11 (automation tools) are the ones this review most easily forgets. `references/prisma_s.md` lists what the search log must contain for items 6–7 to be reportable.

## Does this paper need PRISMA at all?

If the article claims to be a systematic review, or reports a database search with counts, eligibility criteria and a flow of records, then yes: PRISMA 2020 applies, PRISMA-DTA applies if it tabulates or pools sensitivity/specificity, and a flow diagram and checklist are expected even in a clinical magazine. If the authors decide the piece is a narrative or clinical review, do not call it systematic anywhere (title, abstract, methods), do not present a PRISMA diagram as if the selection were exhaustive, and describe the search honestly as "a structured search of PubMed and Scopus (date) supplemented by sources known to the authors; studies were selected for relevance and not systematically appraised". A middle path, "a systematic search with narrative synthesis", is legitimate: it still needs the flow diagram, the eligibility criteria and the SWiM items, but not a meta-analysis or a SoF table. Whatever the label, the AI disclosure stays.

## Files

- `scripts/prisma_flow.py`: Counts CSV / xlsx / JSON → PRISMA 2020 diagram (SVG+PNG) + `prisma_counts.md`; arithmetic checks; `--override`; exit 2 on discrepancies.
- `scripts/sof_table.py`: pooled sens/spec (CLI, entries JSON or `results.json`) → GRADE DTA Summary of Findings Markdown with per-1000 cells and certainty.
- `scripts/checklist_status.py`: filled checklist → list of blank items; `--strict`.
- `assets/prisma2020_checklist.md`, `assets/prisma_dta_checklist.md`: 27 + 12 and 27 + 11 items with a "Where reported" column.
- `assets/grade_dta_sof_template.md`: the finished SoF layout with placeholders and explanation footnotes.
- `assets/methods_templates.md`: Protocol, Eligibility, Search, Selection (single reviewer + AI), Data collection, Risk of bias, Synthesis (SWiM or bivariate), Certainty, AI disclosure.
- `references/prisma2020_boxes.md`: box definitions and workbook mapping; `references/grade_dta.md`: certainty rules; `references/prisma_s.md`: search-log items; `references/citations.md`: the guideline and method papers; `references/validation.md`: what was tested and the expected vs obtained numbers.

AI outputs here are drafts: the reviewer owns every count, judgement and sentence that reaches the manuscript, and the Methods must say that AI assistance was used.
