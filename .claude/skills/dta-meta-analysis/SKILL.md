---
name: dta-meta-analysis
description: Pool sensitivity and specificity of screening questions or questionnaires across studies from a CSV of 2x2 tables (TP/FP/FN/TN) with the bivariate random-effects model (Reitsma 2005 / Chu & Cole 2006), draw SROC and paired forest plots, derive HSROC parameters, DOR and likelihood ratios, run subgroup meta-regression and Deeks' test, and say plainly when pooling is inappropriate (k < 4, mixed thresholds, mixed reference standards). Use when asked to meta-analyse, pool, combine or synthesise diagnostic accuracy, sensitivity/specificity, screening performance, an SROC/HSROC curve, a forest plot of accuracy, heterogeneity in a DTA review, or to write the statistical Methods/Results of an accuracy review. Also use when someone asks "can we pool these?" about accuracy data. R is not installed; everything runs in Python.
---

# DTA meta-analysis

Pools diagnostic accuracy from a `dta.csv` of 2x2 tables and writes manuscript-ready
tables, figures and a Methods template. All output is advisory: the reviewer decides what
is pooled and what is reported, and the manuscript must disclose that AI assistance was
used for the scripts and drafts.

```bash
python3 -I .claude/skills/dta-meta-analysis/scripts/dta_pool.py validate dta.csv
python3 -I .claude/skills/dta-meta-analysis/scripts/dta_pool.py run dta.csv --name <unit> [options]
```

`-I` keeps the CSV's directory and environment variables off the import path; the script
re-adds the user site directory itself, where numpy lives. Needs numpy, scipy, matplotlib;
if one is missing: `python3 -m pip install --user --break-system-packages <pkg>`.

## Input

One row per 2x2 table. Required: `study_id, TP, FP, FN, TN`. Strongly recommended:
`label` (e.g. "Smith 2019"), `instrument`, `threshold`, `reference_standard`. Any other
column (population, setting, risk of bias) is carried through and can drive `--subgroup`
or `--filter`. TP = positive on the index test AND positive on the reference standard.

The usual source is `analysis/extraction/dta.csv` from the data-extraction skill. That
file has no `label` column (labels fall back to `study_id`, the Screening-sheet ID), so
pass `--label-col citation` after joining the citation in, or add a `label` column. It
also has one row per subgroup and per unit of analysis: keep the whole-sample, per-person
rows with `--filter subgroup= --filter unit=person` (or whatever values it uses), and rows
whose TP/FP/FN/TN are blank are dropped with a warning (run its `reconstruct_2x2.py`
first). Without the extraction skill, extract by hand from `data/articles_text/*.txt`,
keeping the page each cell came from in a notes column.

## Workflow

1. **Validate first.** `validate` lists candidate pooling units (instrument x reference
   standard), studies contributing more than one row (several thresholds), zero cells, and
   a verdict per unit: `bivariate` (k >= 4), `univariate fallback only` (k 2-3), `do not
   pool` (k = 1). Nothing is written.
2. **Decide the pooling unit with the reviewer.** Pool only tables that answer one
   question: same instrument (or same single item), same threshold or a defensible
   threshold rule, same kind of reference standard. Mixing "VA < 6/12" with "clinician
   judged LVR need" in one pool answers no question. Use `--filter instrument=...` and
   `--filter reference_standard=...`, or split the CSV.
3. **One table per study.** The bivariate model assumes each study contributes one 2x2.
   If a study reports several thresholds, pick one with `--one-per-study closest:X`
   (threshold nearest X, the review's pre-specified cut-off), `youden`, `largest` or
   `first`, and state the rule in Methods. Without a rule the script still runs but
   warns that precision is overstated. The Steinhauser 2016 multiple-thresholds model is
   the proper tool for using every threshold; it is not implemented here, so say so if it
   would have mattered.
4. **Run.** Outputs land in `analysis/dta/<name>/` (change with `--out`):
   `results.json` (everything), `summary.md` (tables, warnings, methods paragraph),
   `per_study.csv`, `sroc.svg/png`, `forest.svg/png`. Re-running overwrites.
5. **Read the warnings before the estimates.** Every WARNING line is something that has
   to be reported or acted on; copy the relevant ones into the manuscript's limitations.
6. **Interpret and write up** using the template paragraph in `summary.md` and the
   reporting notes below. The reviewer edits it; it is a draft.

Options: `--method auto|glmm|reml|ml` (auto = binomial GLMM, falling back to the
normal-approximation REML fit when the GLMM's information matrix is not positive
definite), `--subgroup COL` (bivariate meta-regression with a likelihood-ratio test),
`--cc-all` (mada-style correction of every study when any cell is zero, for cross-checks
against R), `--quadrature N`, `--title`. `run --help` lists them all.

## When not to pool, and what to do instead

The script refuses or warns; the reviewer still has to decide. Decision rules:

- **k < 4 in the unit**: no bivariate model (three variance parameters cannot be
  estimated from fewer than four pairs). The script reports per-study estimates with exact
  CIs, the forest plot, and univariate fixed/DerSimonian-Laird pooling labelled "for
  description only". In the paper give the range ("sensitivity ranged from 0.71 to 0.96
  across three studies"), not a pooled number, unless the studies are near-identical in
  design and the reviewer argues it explicitly (Takwoingi 2017).
- **k = 4-10**: fit, but the between-study SDs and especially the correlation are
  unstable; the script flags a correlation at the boundary (|rho| > 0.98) and warns that
  the prediction region and HSROC curve are then not trustworthy. Report sensitivity and
  specificity with CIs, show the SROC with study points, and present the prediction
  region with that caveat. Compare the GLMM, REML and univariate rows in the
  model-comparison table; if they disagree materially, say so.
- **Mixed thresholds** without a selection rule, or **mixed reference standards**:
  treat as separate units or as a subgroup; do not present one pooled point.
- **Different constructs** (a single screening item vs a 25-item questionnaire score):
  never pool; present side by side.
- **Case-control style studies** or studies with a zero cell: keep them, but the forest
  plot and a sentence about the continuity correction belong in the results.
- **Deeks' test** is reported only when k >= 10; below that it is underpowered and the
  script says so rather than printing a p-value.

## Heterogeneity

Do not lead with I². In DTA meta-analysis, sensitivity and specificity vary together
through threshold effects, so a univariate I² on either one describes a mixture of
threshold variation and genuine heterogeneity, is inflated by the large within-study
precision of accuracy studies, and ignores the correlation (Cochrane DTA Handbook ch. 10;
Zhou & Dendukuri 2014). Report instead: the 95% prediction region on the SROC plot, the
marginal 95% prediction intervals for sensitivity and specificity, and the between-study
SDs (tau_A, tau_B) with the correlation. The script also prints a multivariate I² (Jackson,
White & Riley 2012) and a Zhou & Dendukuri-style generalised-variance I² for readers who
ask; `references/methods.md` says what each is and why they are optional. Explore
heterogeneity with `--subgroup` only for pre-specified covariates and only with enough
studies per level (the script warns below three).

## Reporting (PRISMA-DTA, McInnes 2018)

Methods must state: the model and estimation method (GLMM by ML with adaptive
Gauss-Hermite quadrature, or Reitsma normal approximation by REML), the software, how
multiple thresholds and zero cells were handled, the pre-specified subgroups, what was
done with units that had too few studies, that Deeks' test was used only with >= 10
studies, and that AI assistance (Claude, Anthropic) produced the analysis scripts and
draft text with all decisions made and checked by the authors. Results must give, per
unit: k, the per-study table (`summary.md` has it), pooled sensitivity and specificity
with 95% CIs, LR+, LR-, DOR, the SROC figure with confidence and prediction regions, and
the heterogeneity description above. Copy the methods paragraph from `summary.md`, then
edit; cite Reitsma 2005, Chu & Cole 2006, Harbord 2007, Macaskill et al. (Cochrane DTA
Handbook ch. 10), Deeks 2005 and Takwoingi 2017 as listed in `references/methods.md`.

## Files

- `scripts/dta_pool.py`: the analysis (`validate`, `run`).
- `scripts/simulate_dta.py`: simulate a dta.csv from known parameters (for tests and demos).
- `scripts/check_recovery.py`: parameter-recovery check across seeds; re-run after
  changing the fitting code and update `references/validation.md`.
- `references/methods.md`: model definitions, likelihoods, delta-method formulas, the
  HSROC conversion, the I² variants, and full citations. Read when writing Methods or
  when a reviewer questions a formula.
- `references/validation.md`: what was checked against what (quadrature vs brute force,
  limiting cases, parameter recovery, a recalled published dataset) and the numbers.
  Read before claiming the implementation is validated.
