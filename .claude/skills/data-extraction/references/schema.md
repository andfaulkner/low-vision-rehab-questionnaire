# Extraction schema

Four CSVs, UTF-8, header row exactly as below (order matters only for readability; the
validator checks the set). Templates with one worked row each are in `assets/`. The
machine-readable copy lives in `scripts/validate_extraction.py` (`SCHEMA`); change both.

## Conventions that apply to every file

- **Empty cell** = not yet extracted or not applicable. **`NR`** = you looked and the paper
  does not report it. Never leave a cell empty for a value you searched for and could not
  find: the difference between "not looked" and "not reported" is what makes dual
  extraction meaningful.
- **Numbers**: proportions as decimals in [0, 1] (`0.89`, not `89%`); keep the paper's
  precision (write `0.89` if the paper says 0.89, not `0.890`). Percentages only in the
  columns named `pct_*`. Counts are integers. Decimal point, no thousands separator.
- **`page`**: the `[page N]` number(s) of the .txt where each value was read, e.g. `4` or
  `3, 4` or `4 (Table 2)`. Required on every row. If the values on one row come from
  different pages, list them all and say which in `derivation`/`notes`.
- **`derivation`**: how any non-verbatim number was obtained (`n_positive = 385 - 121
  (Table 1 p3)`; `TP = round(0.89 x 264)`; `converted from 6/12 Snellen`). Write
  `reported directly (Table N)` when the numbers are verbatim. `reconstruct_2x2.py`
  appends to this column and never overwrites a filled cell.
- **`subgroup`**: empty for the whole sample; otherwise a short label (`age 65+`,
  `glaucoma only`, `better eye`). Rows with the same key and different subgroups are
  distinct rows.
- **`unit` / `unit_of_analysis`**: `person` or `eye`. Per-eye data double-count people
  and cannot be pooled with per-person data (see pitfalls.md).
- **Multi-valued text** (instruments, languages, validation methods, source_refs):
  separate with `; `.
- Free-text columns may contain commas; quote the field. Keep item text verbatim,
  including the item number if the paper uses one (`Q97. In a fast-food restaurant...`).

## studies.csv (one row per included study)

| column | type | meaning |
|---|---|---|
| study_id | int | the Screening-sheet `ID` (column A). Never invent one; hand-added sources use their 128-135 IDs. |
| label | text | `Surname Year` (`Wu 2026`); add a letter for duplicates (`Wu 2026a`). The surname must appear in the Screening `Authors` cell. The same label goes on every dta/effects row of the study; the meta-analysis skills print it on forest plots. |
| year | int | publication year |
| country | text | country/countries of data collection |
| setting | text | where participants were seen: `low vision clinic`, `eye clinic`, `community`, `population survey`, `primary care`, `veterans`, ... |
| design | enum | `cross-sectional`, `cohort`, `case-control`, `RCT`, `pre-post`, `validation`, `systematic review`, `other` |
| n_enrolled | int | recruited / eligible and consenting |
| n | int | contributing to the main accuracy or validation analysis; must be <= n_enrolled (named `n` because risk-of-bias reads `study_id,n,label` from this file) |
| age_mean, age_sd | number | years; `NR` if only a median is given (put the median in notes) |
| age_range | text | `18-98` |
| pct_female | number | 0-100 |
| pct_glaucoma | number | 0-100; `0` only if the paper says no glaucoma; `NR` if diagnoses are not broken down |
| diagnosis_mix | text | diagnosis breakdown with percentages, verbatim labels |
| recruitment | text | consecutive / convenience / population-based / volunteers, dates, and anything bearing on spectrum bias |
| instruments | text | `; `-separated instrument names, spelled exactly as in instruments.csv |
| n_items | int | items of the index instrument(s) actually analysed |
| administration_mode | enum | `self`, `interviewer`, `telephone`, `online`, `mixed`, `NR` |
| time_to_administer_min | number | minutes; `NR` if not reported |
| language | text | language(s) the instrument was given in |
| unit_of_analysis | enum | `person`, `eye` |
| cohort | text | name of the underlying dataset when the paper re-uses one (`same 385 participants as ID 128`), so overlapping samples are not pooled twice |
| page | text | pages the row was built from |
| notes | text | anything else the reviewer needs; VA measurement protocol, exclusions |

## dta.csv (one row per index test x threshold x reference standard x unit x subgroup)

| column | type | meaning |
|---|---|---|
| study_id | int | as above |
| label | text | the study label from studies.csv (`Wu 2026`) |
| instrument | text | instrument name as in instruments.csv |
| item_text | text | verbatim question for a single item or item set; `total score` for a summed scale; `NR` if the paper does not give the wording |
| threshold | text | what counts as test-positive, verbatim: `answer No = positive`, `composite < 70`, `any of 3 items = yes`. **Required.** |
| reference_standard | enum | `visual acuity`, `visual field`, `contrast sensitivity`, `full questionnaire`, `clinician judgement`, `ophthalmic exam`, `composite`, `other` |
| ref_threshold | text | the reference-standard positive definition, verbatim and complete: which eye (better / worse / binocular), correction (presenting / habitual / best-corrected), direction (`worse than 20/40` vs `20/40 or worse`), units (`MD < -6 dB`) |
| ref_threshold_logmar | number | the VA cut-off in logMAR when the reference standard is VA (conversion table in pitfalls.md); blank otherwise |
| unit | enum | `person`, `eye` |
| subgroup | text | see conventions |
| n | int | participants (or eyes) in this 2x2 |
| n_positive | int | reference-standard positives (= TP + FN) |
| prevalence | number | n_positive / n |
| TP, FP, FN, TN | int | the 2x2 cells, test row x reference column |
| sens, spec | number | as reported, at the paper's precision |
| ppv, npv | number | as reported |
| sens_ci_low, sens_ci_high, spec_ci_low, spec_ci_high | number | reported CI limits (both or neither); say in derivation if the script filled them (Wilson) |
| auc | number | ROC area as reported. If the paper computed `(sens + spec) / 2` for a single threshold (Wu 2026 does), record it but say so in notes; the validator flags the pattern |
| auc_ci_low, auc_ci_high | number | |
| ci_level | number | 95 unless the paper says otherwise |
| page, derivation, notes | text | see conventions |

Key for duplicates: `study_id, instrument, item_text, threshold, reference_standard,
ref_threshold, unit, subgroup`. Two rows with the same key are an error: merge them or
make the subgroup explicit.

Consistency rules the validator enforces: `TP + FN = n_positive`; `TP + FP + FN + TN =
n`; `sens` rounds to `TP / (TP + FN)` at the precision written; same for `spec` and
`prevalence`; point estimates lie inside their CIs; every proportion in [0, 1].

## effects.csv (one row per non-2x2 estimate)

| column | type | meaning |
|---|---|---|
| study_id | int | |
| label | text | the study label from studies.csv |
| outcome_type | enum | `correlation` (Pearson r, ICC, kappa in [-1, 1]), `spearman` (rho; pooled with a different variance), `auc` (true ROC area, with its CI, SE, or `n_pos`/`n_neg`), `proportion` (feasibility: completion rate, % referred, % with LVR need), `mean` (a single-group mean: time to administer, score), `md` (mean difference between groups or before/after), `generic` (any estimate + SE already on a normal scale), `logratio` (OR / RR / HR with CI). These names are the ones effect-size-meta-analysis understands. |
| measure | text | the exact statistic: `Pearson r`, `Spearman rho`, `ROC AUC (DeLong CI)`, `minutes`, `mean score difference (impaired - not)` |
| instrument | text | as in instruments.csv |
| comparator | text | what the instrument is related to: `VA (logMAR, better eye)`, `MD (dB)`, `NEI VFQ-25 composite`, `none` for single-group means and proportions |
| estimate | number | the value; sign as reported (a negative r between a difficulty score and logMAR is expected and must be kept) |
| ci_low, ci_high | number | both or neither |
| se | number | standard error if reported |
| sd | number | standard deviation for `mean` |
| events | int | numerator for `proportion` |
| n | int | sample size behind the estimate (for a correlation the pairs; for a proportion the denominator) |
| n_pos, n_neg | int | for `auc`: reference-positive and reference-negative counts (Hanley-McNeil SE) |
| m1, sd1, n1, m2, sd2, n2 | number | for `md`: the two group summaries (group 1 minus group 2) |
| unit, subgroup, page, derivation, notes | | see conventions |
| p_value | number | as reported (`0.000` is fine; put `< 0.001` in notes) |

Key for duplicates: `study_id, outcome_type, measure, instrument, comparator, unit, subgroup`.

## instruments.csv (one row per instrument, shared across studies)

| column | type | meaning |
|---|---|---|
| instrument | text | the short name used in every other file (`NEI VFQ-25`, `VA LV VFQ-48`, `LVQOL`, `IVI`, `GQL-15`, `Activity Inventory`, `Single question`) |
| full_name | text | |
| n_items | int | |
| domains | text | subscales or content areas |
| response_scale | text | `1-5 difficulty`, `yes/no`, ... |
| scoring | text | how a score is obtained (sum, 0-100 transform, Rasch logits, IRT theta) |
| validation_method | tokens | `; `-separated from: `Rasch`, `IRT`, `CTT`, `factor analysis`, `test-retest`, `internal consistency`, `criterion validity`, `ROC`, `none reported` |
| languages | text | validated translations |
| time_to_administer_min | number | typical minutes, if any source reports it |
| target_population | text | |
| source_refs | text | Screening IDs (and DOIs for sources outside the review) that the row is built from |
| notes | text | |

## Where the files live

Default: `analysis/extraction/` at the repo root (`studies.csv`, `dta.csv`,
`effects.csv`, `instruments.csv`), with `passA/` and `passB/` subfolders during dual
extraction and `disagreements_<file>.csv` from `reconcile.py`. Nothing under `data/` is
ever written.
