---
name: effect-size-meta-analysis
description: Pool non-2x2 outcomes from the included studies with a random-effects meta-analysis (REML tau-squared, Hartung-Knapp CI, prediction interval, forest plot) in pure Python, and decide when NOT to pool. Covers correlations between a questionnaire score and visual acuity or visual field (Fisher z), AUCs (Hanley-McNeil SE), proportions such as prevalence of LVR need or referral rates (logit or Freeman-Tukey), means and mean differences (time to administer, questionnaire scores, Hedges g), and any (estimate, SE) pair; plus leave-one-out, subgroups, meta-regression, Egger/funnel, and converters from t/F/p/CI/2x2 to effect sizes. Use when asked to "pool", "meta-analyse", "combine", "summarise across studies", "forest plot", "heterogeneity", "I-squared", "prediction interval", "average correlation/AUC/prevalence", "random effects", or when effects.csv from data-extraction needs a synthesis. Sensitivity/specificity 2x2 data belong to the dta-meta-analysis skill instead.
---

# Effect-size meta-analysis (non-2x2 outcomes)

Pool what questionnaire-validation studies report instead of 2x2 tables: correlations with VA or
VF, AUCs, prevalence/referral proportions, administration times, score differences. Everything
is in `scripts/pool.py` (pooling) and `scripts/convert.py` (turning reported numbers into
estimate + SE). Sensitivity and specificity from 2x2 tables go to `dta-meta-analysis`
(bivariate model); do not pool them here as two separate proportions.

Run the scripts with `python3 -I` because they read CSVs built from article text. numpy, scipy and
matplotlib are required; if an import fails:
`python3 -m pip install --user --break-system-packages numpy scipy matplotlib`.

## Workflow

1. **Start from `effects.csv`** written by the `data-extraction` skill (its schema:
   `study_id, outcome_type, measure, instrument, comparator, estimate, ci_low, ci_high, se, sd,
   events, n, unit, subgroup, ...`). The script maps that schema itself: `mean_diff` is read as
   `md`; a correlation row whose `measure` says Spearman or rho is treated as `spearman`; ICC or
   kappa rows trigger a warning because they are agreement coefficients, not r; and when
   `studies.csv` sits beside the file (or is passed with `--studies`) its `citation` becomes the
   forest-plot label and its `cohort` column drives a warning when two papers share a sample.
   Columns the script also understands: `label`, `n_pos`/`n_neg` or `n_positive` + `n` (needed for
   an AUC with no CI or SE; add `n_positive` by hand from dta.csv), `m1 sd1 n1 m2 sd2 n2`, and
   `direction` (`flip` reverses the sign so all effects point the same way, e.g. VFQ score vs
   logMAR is negative while VFQ vs letters read is positive). Ad-hoc numbers can go in as
   `--row "label=Smith 2019,estimate=0.42,n=110"`.
2. **Decide whether pooling is defensible** (next section). If it is not, say so in the
   write-up and tabulate the studies instead; the script will still draw a forest plot of the
   studies without a diamond if you want one (`k = 1` output, or present per_study.csv).
3. **Pool one outcome, one instrument family, one comparator at a time**:
   ```bash
   python3 -I .claude/skills/effect-size-meta-analysis/scripts/pool.py analysis/extraction/effects.csv \
     --outcome correlation --where instrument=VFQ-25 --where "comparator~VA" \
     --name vfq25_vs_va --loo --subgroup comparator
   ```
   Output lands in `analysis/effects/<name>/`: `summary.md` (pooled estimate on the natural
   scale, CI, prediction interval, heterogeneity, per-study table, a methods-paragraph template),
   `results.json`, `per_study.csv`, `forest.svg/png`, plus `loo.csv`, `subgroups.csv`,
   `metareg.csv`, `funnel.svg/png` when requested. Re-running overwrites; outputs are
   deterministic.
4. **Read `summary.md` and its Warnings section** before quoting anything. The script warns, rather
   than refuses, when instruments or comparators are mixed; the reviewer decides.
5. **Convert awkward reporting first** with `convert.py` (CI to SE on the right scale, AUC + group
   sizes to SE, t/F/p to d, 2x2 to OR/RR, IQR to SD). Put the result into effects.csv rather than
   typing it into `--row`, so the number is traceable.

## Which transform, and why (details and formulas in `references/methods.md`)

| outcome_type | analysis scale | input needed | why |
|---|---|---|---|
| `correlation` | Fisher z, var 1/(n-3) | estimate + n (or se / CI) | variance-stabilising; r itself has variance that depends on r |
| `spearman` | Fisher z, var (1 + rho^2/2)/(n-3) | estimate + n | Bonett & Wright 2000; Spearman z is more variable than Pearson z |
| `auc` | natural (default) or `--auc-scale logit` | estimate + CI, or se, or n_pos + n_neg (Hanley-McNeil 1982) | AUCs near 0.5-0.9 are approximately normal; use logit when values are > 0.9 or CIs would cross 1 |
| `proportion` | logit (default), `--transform ftt`, or `none` | events + n (or estimate + n) | logit keeps CIs in (0,1) and is interpretable; FTT handles 0% / 100% studies without continuity corrections but its back-transform is sensitive to unequal n (Schwarzer 2019; Barker 2021). Run both when any study has 0 or 100% events and report the disagreement |
| `mean` | natural | estimate + sd + n (or se / CI) | administration time, mean score |
| `md` | natural | m1 sd1 n1 m2 sd2 n2, or estimate + se/CI | same instrument, same units |
| `smd` | Hedges g | m1 sd1 n1 m2 sd2 n2, or d + n1 n2 | different instruments or units; g includes the small-sample correction J |
| `generic` | natural | estimate + se/CI | anything already on a normal scale |
| `logratio` | log | OR/RR/HR + CI or log-SE | ratios are pooled on the log scale |

Model defaults, all overridable: REML tau^2 (`--method DL` or `FE`), Hartung-Knapp-Sidik-Jonkman
CI when k >= 3 (`--no-hksj`), 95% prediction interval from t with k-2 df, I^2 and H^2 consistent
with the tau^2 estimator. REML is the default because DerSimonian-Laird underestimates tau^2 when
k is small or effects are heterogeneous, and REML was the estimator recommended by Veroniki 2016
and Langan 2019. HKSJ is the default because with few studies the z-based random-effects CI is
too narrow (IntHout 2014); it can be wider than the fixed-effect CI and that is the point.

## When not to pool (say why instead)

- **k < 3.** With k = 2 the script prints a fixed-effect average marked "descriptive only" and no
  tau^2; prefer reporting both studies side by side. k = 1 is written up, not pooled.
- **Different constructs.** A correlation of VFQ-25 composite with logMAR VA and a correlation of a
  single screening item with VF mean deviation answer different questions. Pool within one
  instrument family and one comparator; use `--where` or `--subgroup`, and treat an all-instruments
  pool as "do questionnaires of this kind track vision" at most.
- **Pearson and Spearman mixed.** `--outcome correlation` pools the Pearson rows and sets the
  Spearman rows aside with a note (and vice versa); with no `--outcome` on a file holding both,
  the script refuses. `--mix-correlations` merges them, each row keeping its own variance
  formula. They estimate different quantities; pool separately or justify in the text.
- **Agreement coefficients (ICC, kappa).** They sit in effects.csv as `correlation` rows with
  `measure = ICC`; the script warns. Filter them in or out with `--where "measure~ICC"` /
  `--where "measure=Pearson r"`; never pool them with validity correlations.
- **Different reference standards or thresholds** for AUC/proportions (VA < 20/40 vs < 20/60,
  clinician-judged LVR need vs questionnaire cut-off). Subgroup or narrate.
- **Several effects from one sample** (same study, two subscales). They are not independent;
  pick one per study (pre-specify which) or note the double counting. The script warns on repeated
  `study_id`.
- **Overlapping cohorts** across papers: keep the larger or more complete report.
- **k < 5 with I^2 > 75%:** report the prediction interval and the individual studies; the pooled
  mean is not a useful summary of a distribution that wide.

## Sensitivity and small-study tools

- `--loo`: leave-one-out table (k >= 3). Flag any study whose omission moves the estimate across
  a decision boundary (for instance r from "moderate" to "weak").
- `--subgroup COL`: separate random-effects fits per level, between-groups Q with separate tau^2
  (Borenstein 2009 ch. 19). With 2-3 studies per level the test has almost no power; present the
  subgroup estimates descriptively.
- `--moderators COL[,COL]`: mixed-effects meta-regression, REML + Knapp-Hartung. Refused below
  10 studies per covariate (Cochrane Handbook 10.11.5.1); `--force-metareg` overrides and labels the
  result exploratory. Expect this to be refused in this review.
- `--egger`: Egger's test and funnel plot only when k >= 10 (Sterne 2011) and never for
  proportions, where estimate and SE are linked and the test gives false positives (Hunter 2014).
  Otherwise the script writes the reason into summary.md so the manuscript can say "not assessed".

## Writing it up

Use the methods-paragraph template at the end of `summary.md` and edit it; the citations it names
are listed with full references in `references/methods.md`. Report, per pooled outcome: k, the
pooled estimate on the natural scale with the HKSJ 95% CI, the 95% prediction interval, tau^2 and
I^2 (with the caveat that both are imprecise below ~10 studies), and what was not pooled and why.
Paste `forest.svg` (vector) into the manuscript; `per_study.csv` is the supplementary table.

AI disclosure: the pooling script was written and run by an AI assistant, and any numbers it
produces are advisory. The Methods must state that AI assistance was used for data analysis
scripting and that the reviewers verified the inputs and made the analytic decisions; the
template paragraph already includes this sentence.

## Validation

`references/validation.md` records the reproduction of the BCG vaccine dataset (Colditz 1994,
metafor `dat.bcg`) under REML, DL, fixed-effect and latitude meta-regression, all matching
metafor to the printed precision, plus parameter-recovery simulations for correlations,
proportions and Hedges g. Re-run those checks if you change `pool.py`.
