# Methods implemented in dta_pool.py

Notation per study i: TP_i, FP_i, FN_i, TN_i; n1_i = TP_i + FN_i (reference positive),
n0_i = TN_i + FP_i (reference negative). sens_i = TP_i / n1_i, spec_i = TN_i / n0_i.
logit(p) = ln(p / (1 − p)); expit is its inverse. z = 1.96 for 95% intervals.

## 1. Per-study estimates

- Exact (Clopper-Pearson) CI for a proportion x/n: lower = Beta(α/2; x, n − x + 1) quantile
  (0 when x = 0), upper = Beta(1 − α/2; x + 1, n − x) quantile (1 when x = n).
- Wilson CI: centre (p + z²/2n) / (1 + z²/n), half-width z·sqrt(p(1 − p)/n + z²/4n²) / (1 + z²/n).
- Continuity correction: 0.5 is added to all four cells of a study only when at least one
  cell is zero (`--cc-all` adds it to every study when any study has a zero, which is
  what `mada::reitsma` does by default). The corrected cells are used only for LR+, LR−,
  DOR, their Wald CIs, and the logits and variances that feed the normal-approximation
  model and the univariate pooling. Sensitivity, specificity and their exact/Wilson CIs
  always use the raw counts; the binomial GLMM uses the raw counts.
- LR+ = sens/(1 − spec); LR− = (1 − sens)/spec; DOR = (TP·TN)/(FP·FN) = LR+/LR−.
  Wald CIs on the log scale with SE(ln LR+) = sqrt((1 − sens)/TP + spec/FP),
  SE(ln LR−) = sqrt(sens/FN + (1 − spec)/TN), SE(ln DOR) = sqrt(1/TP + 1/FP + 1/FN + 1/TN).

## 2. Bivariate random-effects model, normal approximation (Reitsma et al. 2005)

y_i = (logit sens_i, logit spec_i)ᵀ with within-study variances s²_Ai = 1/TP_i + 1/FN_i,
s²_Bi = 1/TN_i + 1/FP_i treated as known (S_i = diag(s²_Ai, s²_Bi)).

y_i ~ N(D_i β, Σ + S_i), where Σ = [[τ²_A, ρ τ_A τ_B], [ρ τ_A τ_B, τ²_B]] is the
between-study covariance and D_i = x_iᵀ ⊗ I_2 maps the fixed effects β (2p values: one
logit sens and one logit spec per covariate column) to the two margins. With an intercept
only, β = (μ_A, μ_B).

Profiled log-likelihood (ML): for given Σ, β̂(Σ) = (Σ_i D_iᵀ V_i⁻¹ D_i)⁻¹ Σ_i D_iᵀ V_i⁻¹ y_i with
V_i = Σ + S_i, and −2ℓ_ML = Σ_i [ln|V_i| + r_iᵀ V_i⁻¹ r_i] + 2k ln 2π with r_i = y_i − D_i β̂.
REML adds ln|Σ_i D_iᵀ V_i⁻¹ D_i|. Σ is parameterised as (ln τ_A, ln τ_B, atanh ρ) and
optimised by Nelder-Mead from three starts followed by BFGS polishing. Var(β̂) =
(Σ_i D_iᵀ V_i⁻¹ D_i)⁻¹ (does not account for uncertainty in Σ, the standard practice).
This is the model fitted by `mada::reitsma` (which uses logit false-positive rate instead
of logit specificity, so its correlation has the opposite sign) and by `metafor::rma.mv`.

## 3. Bivariate binomial GLMM (Chu & Cole 2006; Reitsma model with exact likelihood)

TP_i ~ Binomial(n1_i, expit(x_iᵀβ_A + u_Ai)), TN_i ~ Binomial(n0_i, expit(x_iᵀβ_B + u_Bi)),
(u_Ai, u_Bi) ~ N(0, Σ) independent across studies. The marginal likelihood of study i is
L_i = ∫∫ Bin(TP_i | n1_i, expit(η_Ai + u_A)) Bin(TN_i | n0_i, expit(η_Bi + u_B)) φ(u; 0, Σ) du.

Adaptive Gauss-Hermite quadrature: for each study and each parameter value, the mode û_i of
the log integrand h_i(u) is found by Newton's method (gradient (TP − n1 p_A, TN − n0 p_B) −
Σ⁻¹u, Hessian −diag(n1 p_A(1 − p_A), n0 p_B(1 − p_B)) − Σ⁻¹; h_i is strictly concave so
Newton converges). With H_i = −∇²h_i(û_i) and L_i = chol(H_i⁻¹), the integral is
L_i ≈ 2 |L_i| Σ_{j,k} w_j w_k exp(h_i(û_i + √2 L_i z_jk) + ‖z_jk‖²) over the Q×Q tensor
Gauss-Hermite grid (Q = 15 by default; `--quadrature`). Everything is done in logs with
log-sum-exp. Parameters (β, ln τ_A, ln τ_B, atanh ρ) are maximised by L-BFGS-B with τ bounded
below at 10⁻³ (a hit on that bound is reported as `tau_at_boundary`). Standard errors come
from the inverse of a central-difference numerical Hessian of −ℓ at the optimum; if that
Hessian is not positive definite the script keeps the GLMM point estimates in the comparison
table but uses the REML normal-approximation fit as the primary model, and says so.

This is the model fitted by `lme4::glmer` / SAS PROC NLMIXED in the Cochrane DTA
Handbook (Macaskill et al. 2023, ch. 10) and by `meta4diag`/`metadta`. It avoids the
continuity correction and the downward bias of the normal approximation for small studies
or extreme proportions.

## 4. Summary quantities (delta method on the logit scale)

With μ̂_A, μ̂_B and Var(β̂) = [[v_AA, v_AB], [v_AB, v_BB]]:

- Sens = expit(μ̂_A), CI expit(μ̂_A ± z√v_AA); Spec likewise.
- ln DOR = μ̂_A + μ̂_B, Var = v_AA + v_BB + 2v_AB.
- ln LR+ = ln sens − ln(1 − spec); gradient wrt (μ_A, μ_B) = (1 − sens, spec).
- ln LR− = ln(1 − sens) − ln spec; gradient = (−sens, −(1 − spec)).
  Var(ln LR) = gᵀ Var(β̂) g; CI = LR·exp(±z·SE).

Prediction interval for a new study's logit sensitivity: μ̂_A ± z√(v_AA + τ²_A) (and
similarly for specificity).

## 5. Regions on the SROC plot

Confidence region: {μ̂ + c·L·(cos t, sin t)} with L = chol(Var(β̂)), c = √χ²_{2,0.95} = 2.448,
mapped point-wise through (x, y) = (1 − expit(logit spec), expit(logit sens)).
Prediction region: same with chol(Var(β̂) + Σ̂). These are the regions of the Cochrane
Handbook (Macaskill et al.) and of `mada`/`metandi`.

## 6. HSROC parameters from the bivariate fit (Harbord et al. 2007)

Rutter & Gatsonis (2001) HSROC: logit(π_ij) = (θ_i + α_i X_ij) exp(−β X_ij) with X = +½
for diseased and −½ for non-diseased, so logit sens_i = (θ_i + α_i/2)e^{−β/2} and
logit FPR_i = (θ_i − α_i/2)e^{β/2}; θ_i ~ N(Θ, σ²_θ) (positivity/threshold), α_i ~ N(Λ, σ²_α)
(accuracy), independent. Writing the bivariate model on logit sens (A) and logit spec (B)
with σ_AB = Cov(logit sens, logit spec) = ρ τ_A τ_B:

- β = ln(τ_B / τ_A)
- Λ = (τ_B/τ_A)^{1/2} μ_A + (τ_A/τ_B)^{1/2} μ_B
- Θ = ½[(τ_B/τ_A)^{1/2} μ_A − (τ_A/τ_B)^{1/2} μ_B]
- σ²_α = 2(τ_A τ_B + σ_AB)
- σ²_θ = ½(τ_A τ_B − σ_AB)

Derivation: Var(logit sens) = (σ²_θ + σ²_α/4)e^{−β}, Var(logit spec) = (σ²_θ + σ²_α/4)e^{β},
so τ_B/τ_A = e^{β}; Cov(logit sens, logit spec) = Cov((θ + α/2)e^{−β/2}, (α/2 − θ)e^{β/2}) =
σ²_α/4 − σ²_θ, and τ_A τ_B = σ²_θ + σ²_α/4; solve. (Harbord writes the covariance in terms
of logit FPR; the sign of σ_AB flips accordingly. mada reports these same five parameters.)

SROC curve: for false-positive rate x, logit sens = Λ e^{−β/2} + e^{−β} logit(x). It passes
through the summary point. The curve is drawn only between the smallest and largest
observed false-positive rates because extrapolating it is meaningless (Cochrane Handbook).
When ρ → −1, σ²_α → 0 (or when ρ → +1, σ²_θ → 0); the curve is then degenerate and the
script warns.

## 7. Heterogeneity statistics

Primary description: prediction region and intervals, τ_A, τ_B, ρ (sections 4-5).

Optional, printed with caveats:

- Univariate I² for logit sens and logit spec from DerSimonian-Laird (Q − (k − 1))/Q. Not
  recommended for DTA: it conflates threshold variation with heterogeneity, ignores the
  correlation, and is driven up by the typically large within-study precision.
- Multivariate I² of Jackson, White & Riley (2012): R² = |Var_RE(β̂)| / |Var_FE(β̂)| (ratio of
  generalised variances of the pooled estimate under the random- and fixed-effect models),
  I² = 1 − 1/R². Interprets as the proportional inflation of the volume of the confidence
  region due to heterogeneity.
- Zhou & Dendukuri (2014)-style bivariate I²: 1 − sqrt(|S̄| / |Σ̂ + S̄|) with S̄ the mean
  within-study covariance matrix. This generalises τ²/(τ² + s̄²) with determinants. It is
  our reading of the generalised-variance proposal in that paper; check the exact
  definition against the paper before citing it as theirs.

## 8. Subgroup analysis / bivariate meta-regression

A categorical covariate with G levels enters as G indicator columns in X, giving a separate
(μ_A, μ_B) per level with a shared Σ. The null model has common means. The likelihood-ratio
statistic 2(ℓ_full − ℓ_null) is referred to χ² with 2(G − 1) df; both fits use ML (GLMM or
normal approximation), never REML, because REML likelihoods are not comparable between
different fixed-effect designs. Level estimates below three studies are flagged. Testing
sensitivity and specificity separately (1 df each) is a reasonable follow-up but not
implemented.

## 9. Small-study effects: Deeks' test (Deeks, Macaskill & Irwig 2005)

Weighted regression of ln DOR_i on 1/√ESS_i with weights ESS_i, where
ESS_i = 4 n1_i n0_i / (n1_i + n0_i) is the effective sample size. The slope's t-test
(k − 2 df) with p < 0.10 suggests asymmetry. Performed only when k ≥ 10.

## 10. Univariate fallback (k < 4) and sanity check

DerSimonian-Laird on logit sens and logit spec separately: fixed-effect weights 1/s², Q,
τ² = max(0, (Q − (k − 1))/C), random weights 1/(s² + τ²). The script compares the bivariate
pooled logit sensitivity with the DL value and warns if they differ by more than 0.5 on
the logit scale.

## 11. Not implemented (say so when relevant)

- Multiple-thresholds model (Steinhauser, Schumacher & Rücker 2016; `diagmeta`), which
  uses all thresholds a study reports.
- Comparative accuracy of two index tests within the same model (Cochrane Handbook ch. 11).
- Bayesian bivariate / HSROC fitting (`meta4diag`, `bamdit`); latent-class models for
  imperfect reference standards.
- Trivariate models with prevalence.

## References

- Reitsma JB, Glas AS, Rutjes AW, Scholten RJ, Bossuyt PM, Zwinderman AH. Bivariate analysis
  of sensitivity and specificity produces informative summary measures in diagnostic reviews.
  J Clin Epidemiol 2005;58:982-990.
- Chu H, Cole SR. Bivariate meta-analysis of sensitivity and specificity with sparse data: a
  generalized linear mixed model approach. J Clin Epidemiol 2006;59:1331-1332.
- Rutter CM, Gatsonis CA. A hierarchical regression approach to meta-analysis of diagnostic
  test accuracy evaluations. Stat Med 2001;20:2865-2884.
- Harbord RM, Deeks JJ, Egger M, Whiting P, Sterne JA. A unification of models for
  meta-analysis of diagnostic accuracy studies. Biostatistics 2007;8:239-251.
- Macaskill P, Takwoingi Y, Deeks JJ, Gatsonis C. Chapter 10: Understanding meta-analysis.
  In: Deeks JJ, Bossuyt PM, Leeflang MM, Takwoingi Y (eds). Cochrane Handbook for Systematic
  Reviews of Diagnostic Test Accuracy, version 2. Cochrane 2023.
- Deeks JJ, Macaskill P, Irwig L. The performance of tests of publication bias and other
  sample size effects in systematic reviews of diagnostic test accuracy was assessed.
  J Clin Epidemiol 2005;58:882-893.
- Takwoingi Y, Guo B, Riley RD, Deeks JJ. Performance of methods for meta-analysis of
  diagnostic test accuracy with few studies or sparse data. Stat Methods Med Res
  2017;26:1896-1911.
- Jackson D, White IR, Riley RD. Quantifying the impact of between-study heterogeneity in
  multivariate meta-analyses. Stat Med 2012;31:3805-3820.
- Zhou Y, Dendukuri N. Statistics for quantifying heterogeneity in univariate and bivariate
  meta-analyses of binary data: the case of meta-analyses of diagnostic accuracy. Stat Med
  2014;33:2701-2717.
- Steinhauser S, Schumacher M, Rücker G. Modelling multiple thresholds in meta-analysis of
  diagnostic test accuracy studies. BMC Med Res Methodol 2016;16:97.
- McInnes MDF, Moher D, Thombs BD, et al. Preferred Reporting Items for a Systematic Review
  and Meta-analysis of Diagnostic Test Accuracy Studies: the PRISMA-DTA statement. JAMA
  2018;319:388-396.
- Doebler P, Holling H. Meta-analysis of diagnostic accuracy with mada. R package vignette.
- Glas AS, Lijmer JG, Prins MH, Bonsel GJ, Bossuyt PM. The diagnostic odds ratio: a single
  indicator of test performance. J Clin Epidemiol 2003;56:1129-1135.
