# Validation of pool.py

Run on 2026-10-25 with numpy 2.5.4, scipy 1.18.1, Python 3.15, from the synthetic data
described below (kept outside the repo). Re-run these checks after any change to `pool.py`.

## 1. BCG vaccine trials (Colditz 1994; metafor `dat.bcg`, 13 trials, log risk ratio)

The raw 2x2 counts were typed from memory of metafor's `dat.bcg` (tpos, tneg, cpos, cneg,
absolute latitude) and converted to log RR with Woolf SE. Expected values are those printed in
Viechtbauer (2010, J Stat Softw 36(3)) and the metafor documentation. Confidence that the
recalled data are exact: high, because every statistic below agrees with the published output
to the printed precision, which would not happen with a wrong cell.

| Quantity | Expected (metafor) | Obtained | Match |
|---|---|---|---|
| REML tau^2 | 0.3132 | 0.3132 | yes |
| REML pooled log RR (SE) | -0.7145 (0.1798) | -0.7145 (0.1798) | yes |
| REML 95% CI, log scale (z) | -1.0669 to -0.3622 | -1.0669 to -0.3622 | yes |
| REML RR and CI | 0.49 (0.34-0.70) | 0.489 (0.344-0.696) | yes |
| I^2, H^2 | 92.22%, 12.86 | 92.22%, 12.86 | yes |
| Q (12 df) | 152.23, p < .0001 | 152.23, p < 0.001 | yes |
| DL tau^2, pooled log RR | 0.3088, -0.7141 | 0.3088, -0.7141 | yes |
| Fixed-effect log RR (SE), CI | -0.4303 (0.0405), -0.5097 to -0.3509 | -0.4303 (0.0405), -0.5097 to -0.3509 | yes |
| Meta-regression on latitude, REML: intercept (SE) | 0.2515 (0.2491) | 0.2515 (0.2491) | yes |
| slope (SE) | -0.0291 (0.0072) | -0.0291 (0.0072) | yes |
| residual tau^2, R^2 | 0.0764, 75.62% | 0.0763, 75.63% | yes (rounding) |
| QM(1) | 16.36, p < .0001 | 16.36, p < 0.001 | yes |
| QE(11) | 30.73, p = 0.0012 | 30.73, p = 0.0012 | yes |

Obtained but not checked against a remembered reference (reported for the record):
HKSJ 95% CI on the log scale -1.1084 to -0.3206 (SE 0.1808, t with 12 df); 95% prediction
interval RR 0.13 to 1.79; Knapp-Hartung meta-regression slope SE 0.0082, p = 0.0046,
F(1, 11) = 12.59; Egger weighted regression t = -1.40 on 11 df, p = 0.19.
These are consistent with metafor's `test="knha"` behaviour (wider than z) but the exact
figures were not recalled, so treat them as unverified.

Commands (paths relative to the repo; `bcg.csv` holds study_id, label, outcome_type=logratio,
estimate=RR, se=log SE, ablat):

```
python3 -I .claude/skills/effect-size-meta-analysis/scripts/pool.py bcg.csv --name bcg_reml --no-hksj --loo --egger --moderators ablat
python3 -I .claude/skills/effect-size-meta-analysis/scripts/pool.py bcg.csv --name bcg_dl --method DL --no-hksj
```

## 2. Molloy 2014 (conscientiousness-adherence correlations)

Not reproduced: the 16 raw r and n values could not be recalled exactly, so no claim is made.

## 3. Parameter recovery on simulated data (seed 20261025)

| Set | Truth | Obtained (REML, HKSJ) | Comment |
|---|---|---|---|
| 40 Pearson correlations, rho = 0.40, tau_z = 0.10 (tau^2 = 0.010), n 50-400 | r 0.40, tau^2 0.010 | r 0.403 [0.365, 0.440], tau^2 0.0145 | truth inside CI; tau^2 within sampling error for k = 40 |
| 40 proportions, logit mean log(0.3/0.7), tau_logit = 0.30 (tau^2 = 0.09), n 40-400 | median p 0.30, tau^2 0.09 | logit: 0.315 [0.291, 0.339], tau^2 0.0858; FTT: 0.315 [0.291, 0.338] | logit-normal mean is above the median, so 0.315 is expected; both transforms agree with large, balanced n |
| 40 two-group studies, d = 0.50, tau_d = 0.20 (tau^2 = 0.04), n 30-150 per arm | g 0.50, tau^2 0.04 | g 0.467 [0.389, 0.546], tau^2 0.0341 | truth inside CI |

Small synthetic sets (5-8 studies) exercised every outcome type, k = 1 and k = 2 handling, the
Pearson/Spearman separation (selection with `--outcome`, refusal when ambiguous, merge with
`--mix-correlations`), a file in the data-extraction schema (`measure`, `mean_diff`,
studies.csv labels and a shared cohort), the meta-regression refusal below 10 studies per covariate,
the Egger refusal for proportions and for k < 10, `--where`, `--subgroup`, `--loo`, `--row`
ad-hoc input, and every `convert.py` subcommand. Hand checks: convert.py `auc-se` for
AUC 0.78, 40 cases, 160 controls gives SE 0.0456 (Hanley-McNeil table value 0.046);
`means-to-smd` for (62, 18, 50) vs (75, 16, 55) gives g = -0.760 with J = 0.9927;
`rr-from-2x2 --a 4 --b 119 --c 11 --d 128` reproduces the first BCG trial's RR 0.411.

On the 6-study proportion set with one 0/25 study, logit (0.242) and FTT (0.176) pooled
values differ markedly: the zero-event study carries 1.3% of the logit weight after continuity
correction but a near-equal share of the FTT weight once tau^2 is large. This is the behaviour
Schwarzer 2019 and Barker 2021 describe and is why SKILL.md asks for both transforms whenever a
study has 0% or 100% events.
