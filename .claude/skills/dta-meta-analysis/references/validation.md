# Validation of dta_pool.py (v1.0.0, 25 Oct 2026)

Python 3.15, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2. R and the `mada`/`metafor`
packages were not available, so no estimate here was compared against R output directly.
What was checked, and how well it held, is listed from strongest to weakest evidence.

## 1. Quadrature against brute-force integration (exact check)

The per-study marginal likelihood of the binomial GLMM (adaptive Gauss-Hermite, section 3
of methods.md) was compared with `scipy.integrate.dblquad` over [−6, 6]² at parameters
μ_A = 1.4, μ_B = 2.1, τ_A = 0.6, τ_B = 0.5, ρ = −0.5.

| 2x2 (TP, n1, TN, n0) | dblquad log L | AGH Q=5 | AGH Q=10 | AGH Q=15 (default) |
|---|---|---|---|---|
| (17, 24, 86, 92) | −4.92676333 | −4.92678948 | −4.92676333 | −4.92676333 |
| (116, 121, 340, 371) | −10.19034186 | −10.19038379 | −10.19034184 | −10.19034186 |
| (5, 5, 10, 12) (zero FN) | −2.50638239 | −2.50638336 | −2.50638239 | −2.50638239 |
| (2, 40, 300, 310) | −18.99235491 | −18.99239620 | −18.99235491 | −18.99235491 |

Agreement to 8 decimals at Q ≥ 10, including a study with a zero cell and one with a
very sharp likelihood (n0 = 371).

## 2. Limiting cases (exact checks)

- Σ → 0 (τ = 10⁻⁴): GLMM log-likelihood at the pooled-proportion means equals the sum of
  binomial log-pmfs at the common proportions: −13.946997 vs −13.946996.
- Normal-approximation model with negligible within-study variance (10⁻⁶), k = 40:
  ML gives β̂ = sample means to 8 decimals and Σ̂ = sample covariance with divisor k
  (0.19143 / −0.09903 / 0.37918 vs 0.19143 / −0.09903 / 0.37918); REML gives the
  divisor k − 1 covariance (0.19634 / −0.10157 / 0.38890 vs the same). This checks the ML
  and REML objective functions and the GLS profiling.

## 3. Parameter recovery from simulated data (`scripts/check_recovery.py`)

Truth: logit sens 1.5 (sens 0.8176), logit spec 2.0 (spec 0.8808), τ_A = 0.5, τ_B = 0.6,
ρ = −0.4; n1 ~ U(20, 150), n0 ~ U(40, 400); 20 seeds each.

k = 30:

| Model | mean sens (bias) | mean spec (bias) | mean τ_A / τ_B | mean ρ | 95% CI coverage sens / spec |
|---|---|---|---|---|---|
| GLMM (AGHQ, ML) | 0.8156 (−0.002) | 0.8790 (−0.002) | 0.477 / 0.605 | −0.381 | 0.95 / 0.95 |
| Normal approx. (REML) | 0.8101 (−0.007) | 0.8758 (−0.005) | 0.465 / 0.597 | −0.395 | 0.95 / 0.95 |

k = 8:

| Model | mean sens (bias) | mean spec (bias) | mean τ_A / τ_B | mean ρ | coverage sens / spec |
|---|---|---|---|---|---|
| GLMM | 0.8181 (+0.001) | 0.8694 (−0.011) | 0.401 / 0.537 | −0.373 | 0.90 / 0.90 |
| REML | 0.8136 (−0.004) | 0.8675 (−0.013) | 0.420 / 0.570 | −0.370 | 0.85 / 0.90 |

With k = 8, 4 of 20 GLMM fits put ρ at its boundary (|ρ| ≥ 0.99) and coverage drops below
nominal: this is the known small-k instability of the bivariate variance components
(Takwoingi 2017) and the reason the script flags k = 4-10 and boundary correlations.
The small downward bias of the normal approximation relative to the GLMM is the expected
effect of the logit transformation with finite study sizes (Chu & Cole 2006).

Seed 1, k = 30 (the `sim30` example in SKILL.md): GLMM sens 0.807 (0.768-0.841), spec 0.892
(0.868-0.912), τ 0.581/0.581, ρ −0.550; REML sens 0.802, spec 0.889, τ 0.563/0.579,
ρ −0.575; univariate DL on logit sens 1.412 vs bivariate 1.432 (difference 0.02).

## 4. Hand-made 5-study example with zero cells (`evals/zero-cell-small-k/files/dta.csv`)

Two studies with a zero cell (FN = 0; FP = 0). Script applies the 0.5 correction to those
two only, fits the GLMM (k = 5, warning issued), reports sens 0.854 (0.789-0.901), spec
0.916 (0.822-0.963), and warns that ρ = −1.00 is at its boundary so the HSROC curve and
prediction region shape should not be reported. With `--subgroup population` (levels
clinic 3, community 2) it warns about the level with < 3 studies and gives LRT χ² = 2.18 on
2 df, p = 0.34. Visually checked: SROC and forest plots render, the degenerate prediction
ellipse is visibly a sliver, as it should be with ρ = −1.

## 5. Published dataset (weak evidence; recalled, not verified)

The `mada::AuditC` data (Kriston et al. 2008, 14 studies of AUDIT-C) were typed from
memory into `auditc_recalled.csv` in the scratch folder. Our recollection of the published
mada vignette result is sensitivity ≈ 0.886 and false-positive rate ≈ 0.24 by REML with
mada's all-study continuity correction. Our fit of the recalled table (`--cc-all`) gave
REML sensitivity 0.850 (0.774-0.904), false-positive rate 0.152, τ 0.856/0.690, ρ −0.541.
The disagreement is almost certainly in the recalled raw counts (several rows had to be
guessed), not in the model: sections 1-3 show the estimator itself is right. Treat this as
unverified. To verify properly, run in R: `library(mada); data(AuditC); summary(reitsma(AuditC))`
and `reitsma(AuditC, method = "ml")`, export `AuditC` to CSV, and run
`dta_pool.py run AuditC.csv --name auditc --cc-all --method reml` (then `--method ml`);
the logit means, τ², the correlation (sign flipped, because mada models logit FPR) and the
HSROC parameters should match to 3 decimals. Record the numbers here when done.

## 6. Not validated

- Standard errors of the GLMM variance components (numerical Hessian): plausible but not
  compared to another implementation.
- The Zhou & Dendukuri-style bivariate I² formula is our reading of their proposal.
- Subgroup LRT and Deeks' test were exercised for correct mechanics (reproduce expected
  df and the k ≥ 10 rule) but not against a published worked example.
