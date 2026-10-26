---
name: narrative-synthesis
description: Synthesise the included studies WITHOUT meta-analysis, following SWiM (Campbell 2020) and Cochrane Handbook chapter 12, and produce what the Results section needs when pooling is not appropriate - per-study accuracy tables with 95% CIs, a "forest plot without pooling", study points in ROC space, an evidence map (instrument x reference standard, independent datasets and n), a harvest / effect-direction plot, direction-only vote counts, narrative heterogeneity and certainty wording, and the nine SWiM reporting items. Detects overlapping cohorts (same group, same n, cross-referenced papers such as the Wu 2024 TVST / Wu 2026 IOVS cohort) and collapses them into independent datasets before anything is counted. Use when asked to "synthesise", "summarise the studies", "write the Results", "narrative synthesis", "SWiM", "we can't pool", "too few studies", "present per study", "structured summary", "evidence map", "harvest plot", "effect direction", "vote count", "which studies overlap", "how many independent datasets", "describe heterogeneity", or "rate certainty without a pooled estimate"; and whenever dta-meta-analysis or effect-size-meta-analysis has said "do not pool".
---

# Narrative synthesis (SWiM)

This review will synthesise its primary question without a meta-analysis: the two index
questions (restaurant menu, keyboard) come from one research group's overlapping cohort
(TVST 2024; Wu 2026 IOVS), so there is about one independent dataset, far below the four
the bivariate model needs. The job is therefore to present each study's accuracy as-is
with CIs, group the other comparisons by instrument and reference standard, and write a
synthesis that follows SWiM (Campbell 2020, nine items) and Cochrane Handbook ch. 12.
Everything here is advisory: the reviewer confirms every grouping and judgement, and
the Methods disclose that AI assistance was used.

Inputs come from `data-extraction` (`analysis/extraction/studies.csv`, `dta.csv`,
`effects.csv`, `instruments.csv`) and `risk-of-bias` (`analysis/risk_of_bias/quadas2.csv`).
Outputs go to `analysis/synthesis/` (never `data/`); copy what the manuscript needs into
`paper/`. Run scripts with `python3 -I`; they re-add the user site directory where
numpy/matplotlib live, and tell you the `pip install --user --break-system-packages`
command if one is missing.

## Workflow

**(a) Define the grouping** before looking at results, and write it down (SWiM item 1).
The unit is question/instrument x reference standard x population. Default groups for
this review: single screening item vs measured VA; single item vs VF; full questionnaire
(VFQ-25, VA LV VFQ-48, LVQOL, IVI, GQL-15, AI) vs VA/VF; any instrument vs clinician-judged
LVR need; questionnaire vs questionnaire (criterion validity, not accuracy). Say which
groups were pre-specified in the protocol and which emerged from the data. `--group-by`
on the scripts takes any dta.csv columns if the reviewer wants a different split.

**(b) Collapse overlapping cohorts** into independent datasets. Papers that re-analyse
the same participants are one data point, not two; counting them twice inflates every
"k" and every n in the synthesis.
```bash
python3 -I .claude/skills/narrative-synthesis/scripts/independent_datasets.py analysis/extraction/studies.csv \
    --dta analysis/extraction/dta.csv --out-dir analysis/synthesis --assign
```
It flags pairs by cross-references in `cohort`/`notes`, same cohort name, author-surname
overlap (from the Screening export's Authors column), identical n, overlapping recruitment
years and same site, assigns a confidence (high / probable / possible) with the reasons,
joins pairs at `--merge` (default probable) into `dataset_id` groups and writes
`independent_datasets.md/.csv`, `overlap_pairs.csv` and `studies_with_datasets.csv`.
**The reviewer confirms each grouping** against the papers and edits `dataset_id` in that
copy; a filled `dataset_id` column is treated as the reviewer's answer on re-runs. Pass
the confirmed copy as `--studies` to every later script. For a merged pair, use the larger
or more complete report in the main table and show the other beside it (marked ‡).

**(c) Choose the standardised metric per group** (SWiM item 2) and keep it the same for
every study in the group: sensitivity and specificity with 95% CIs at a stated threshold
for 2x2 data; AUC with CI for ROC studies (never the single-threshold `(sens+spec)/2`
that one paper calls AUC; the table flags it §); Pearson/Spearman r for correlations;
direction of effect only when nothing better is comparable. Do not convert a correlation
into an accuracy statement or vice versa.

**(d) Tabulate and plot without pooling** (SWiM item 7):
```bash
python3 -I .claude/skills/narrative-synthesis/scripts/accuracy_table.py analysis/extraction/dta.csv \
    --effects analysis/extraction/effects.csv --studies analysis/synthesis/studies_with_datasets.csv \
    --rob analysis/risk_of_bias/quadas2.csv --filter unit=person --filter subgroup= --out-dir analysis/synthesis
python3 -I .claude/skills/narrative-synthesis/scripts/evidence_map.py --dta analysis/extraction/dta.csv \
    --effects analysis/extraction/effects.csv --studies analysis/synthesis/studies_with_datasets.csv \
    --rob analysis/risk_of_bias/quadas2.csv --out-dir analysis/synthesis
```
`accuracy_table.py` writes `accuracy_table.md/.csv` (one row per study x threshold, grouped;
Wilson CIs computed from the 2x2 when the paper gave none, † when counts had to be
back-calculated; QUADAS-2 overall per study), `forest_nopool.svg/.png` (paired sens/spec
with CIs, no diamond, labelled "no pooled estimate") and `roc_space.svg/.png` (study points
sized by n, by instrument). `evidence_map.py` writes `evidence_map_dta` and
`evidence_map_effects` (matrix of independent datasets and n per instrument x reference
standard: use it to show where the evidence is and the empty cells readers would assume
exist), `harvest_plot.svg/.png` and `effect_direction.md` (direction, size class and risk
of bias per study for effects.csv outcomes: use them when outcomes are reported on
different scales and only direction and rough size are comparable). Open each PNG and
check labels before pasting; long thresholds are truncated in the forest labels, so cite
the table for the full wording.

**(e) Decide whether any group can be pooled.** The table's "Verdict" line counts
independent datasets per group and per threshold. Hand a group to `dta-meta-analysis`
only if >= 4 independent datasets share a threshold and reference-standard definition
(`dta_pool.py validate` is the arbiter); hand correlations/AUCs with >= 3 independent
studies to `effect-size-meta-analysis`. Everything else stays narrative. Expect the
single-item vs VA group to be k = 1 here. When a group is pooled elsewhere, still show it
in these tables so the Results have one consistent per-study layout.

**(f) Describe heterogeneity narratively** (SWiM item 5), in this order, because each
explains spread before any "true" heterogeneity is invoked: threshold (test and
reference: 20/40 vs 20/60, better eye vs binocular, worse-than vs or-worse), reference
standard construct (VA-only misses field loss; clinician-judged need is broader),
setting and spectrum (low vision clinic vs population; prevalence in the table is the
clue), administration (self vs interviewer, stand-alone item vs inside a 100-item survey),
population (glaucoma-only, age). Describe the range of estimates and whether CIs overlap;
do not compute I² for a narrative group.

**(g) Weigh studies in the text by size and risk of bias**, not by a formula. Lead with
the largest low-risk study; say when the only low-risk study disagrees with the rest;
state when a High QUADAS-2 judgement (data-driven item selection, spectrum-enriched
sample, partial verification) would push accuracy upward, so the reader can discount it.
Never average, rank or score the studies.

**(h) Rate certainty** (SWiM item 6). GRADE applies to a narrative synthesis (Murad 2017):
rate each group for risk of bias, indirectness, inconsistency (range and overlap of CIs
instead of I²; "could not be assessed" with k <= 2), imprecision (CI width and number of
reference-positive/negative participants) and publication bias ("could not be assessed"
below 10 studies), starting at high for cross-sectional accuracy designs. For 2x2 groups use
`prisma-reporting`'s `sof_table.py` per study, or its narrative SoF layout when there is no
pooled row; for correlation/AUC groups rate in the text. Wording: `assets/synthesis_templates.md`.

**(i) Write the SWiM items into Methods and Results.** Fill `assets/swim_checklist.md`
(nine items, "where reported" column) and use the paragraph templates in
`assets/synthesis_templates.md`: the Methods paragraph, a Results structure per group,
"could not be pooled because ..." wording, vote-count sentences, certainty sentences, and
the AI-assistance disclosure. Item 8 requires that each synthesised finding names the
contributing studies and uses language that matches what was done (describe, not
"pooled sensitivity was").

## Vote counting: last resort, direction only

Vote counting compares the number of studies whose effect favours one direction with the
number favouring the other. The Cochrane Handbook allows it only when effect sizes
cannot be extracted or compared at all, and only on **direction**, with an exact sign
test if a p-value is wanted. Never count how many studies were "significant": that
conflates size with sample size, treats p = 0.06 as evidence against, and gets less
reliable as studies get smaller (Hedges & Olkin 1980). It is a last resort because it
discards magnitude, precision and risk of bias; prefer a structured table of estimates
with CIs (this skill's default) or pooling where allowed. `effect_direction.md` already
applies the rule: direction from the sign relative to the null (CI excluding the null
when a CI exists, otherwise beyond the trivial band; `direction = flip` rows reversed),
null/unclear counted separately, one vote per independent dataset, sign test on
positive vs negative only, and a sentence saying it is a last resort.

## Files

- `scripts/independent_datasets.py`: overlapping-cohort detection and dataset_id
  assignment (standard library).
- `scripts/accuracy_table.py`: grouped per-study accuracy table, forest without pooling,
  ROC-space scatter. Imports `wilson()` from data-extraction's `reconstruct_2x2.py`.
- `scripts/evidence_map.py`: evidence map, harvest plot, effect-direction table and
  direction-only vote count.
- `assets/swim_checklist.md`: the nine SWiM items with a "where reported" column.
- `assets/synthesis_templates.md`: Methods paragraph, Results structures, not-pooled
  wording, vote-count sentences, certainty sentences, AI disclosure.
- `references/swim.md`: the nine items explained, with how each is met in this review.
  Read before writing the Methods.
- `references/methods.md`: methods and citations (SWiM, Handbook ch. 12, effect-direction
  and harvest plots, vote counting, Wilson CI, size classes, GRADE without a pooled
  estimate). Read when a reviewer asks why.
- `references/validation.md`: what the scripts were checked against.

## Hand-offs and boundaries

- `data-extraction` must have run first; this skill never reads the article text.
- `risk-of-bias` supplies QUADAS-2 rows; without them the tables say "not assessed".
- `dta-meta-analysis` / `effect-size-meta-analysis` take any group the verdict line
  marks as a candidate; their refusals come back here as narrative groups.
- `prisma-reporting` takes the per-study table for the Summary of Findings and the
  PRISMA-DTA items on synthesis; its Methods templates already carry the AI disclosure.
- Do not write decisions into the screening workbook, and do not present AI-drafted
  groupings or certainty ratings as the reviewer's without their confirmation.
