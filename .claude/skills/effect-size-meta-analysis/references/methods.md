# Methods implemented in pool.py and convert.py

Notation: k studies, y_i the effect on the analysis scale, v_i its within-study variance,
w_i = 1/v_i, w*_i = 1/(v_i + tau^2).

## 1. Transforms to the analysis scale

**Pearson r -> Fisher z** (Fisher 1921): z = atanh(r), var = 1/(n-3). Back-transform r = tanh(z).
Pooling raw r is biased toward zero and its variance depends on r, so pool on z and report r
(Borenstein 2009 ch. 6; Hedges & Olkin 1985).

**Spearman rho -> Fisher z** with var = (1 + rho^2/2)/(n-3) (Bonett & Wright 2000). The script
uses the sample rho in the formula. Spearman and Pearson estimate different population
quantities; the script refuses to mix them unless `--mix-correlations` is given.

**AUC**: natural scale by default; SE from (a) the reported CI, (b) `se`, or (c) Hanley &
McNeil (1982): with Q1 = A/(2-A), Q2 = 2A^2/(1+A),
SE^2 = [A(1-A) + (n_pos-1)(Q1-A^2) + (n_neg-1)(Q2-A^2)] / (n_pos n_neg).
This assumes an exponential-like score distribution and is usually within a few percent of the
DeLong SE. `--auc-scale logit` uses logit(A) with delta-method variance SE^2/(A(1-A))^2; use it
when AUCs are > 0.9 or a natural-scale CI would exceed 1 (Zhou, Obuchowski & McClish 2011).

**Proportions**:
- logit (default): y = log(e/(n-e)), v = 1/e + 1/(n-e); 0 or n events get a 0.5 continuity
  correction (e + 0.5, n + 1) with a note.
- Freeman-Tukey double arcsine (`--transform ftt`; Freeman & Tukey 1950):
  y = asin(sqrt(e/(n+1))) + asin(sqrt((e+1)/(n+1))), v = 1/(n + 0.5). Back-transform with
  Miller (1978) using the harmonic mean of n (metafor `transf.ipft.hm`). Schwarzer et al. (2019)
  showed the back-transform can be misleading when study sizes differ widely; Barker et al.
  (2021) recommend logit as the default and FTT only when many studies have 0% or 100%, with
  the harmonic-mean inverse and a sensitivity analysis. The script follows that advice: logit
  default, FTT on request, and a note to run both when any study has boundary events.
- `none`: raw p with v = p(1-p)/n, for comparison only.

**Mean**: SE = sd/sqrt(n) or from a CI. **Mean difference**: MD = m1 - m2,
SE^2 = sd1^2/n1 + sd2^2/n2. **SMD**: Cohen d = (m1 - m2)/s_pooled with
s_pooled^2 = [(n1-1)sd1^2 + (n2-1)sd2^2]/(n1+n2-2); Hedges g = J d with J = 1 - 3/(4(n1+n2-2)-1),
var(g) = (n1+n2)/(n1 n2) + g^2/(2(n1+n2)) (Hedges 1981; Borenstein 2009 ch. 4).

**Generic**: y = estimate, v = SE^2 or ((CI_high - CI_low)/(2 z))^2.
**Log ratio**: y = log(OR or RR), SE on the log scale from the CI.

## 2. Fixed-effect and random-effects models

Fixed effect: y_FE = sum(w y)/sum(w), var = 1/sum(w).
Cochran's Q = sum(w (y - y_FE)^2), df = k - 1, p from chi^2.

**tau^2 estimators**
- DerSimonian & Laird (1986): tau^2 = max(0, (Q - df)/C), C = sum(w) - sum(w^2)/sum(w).
- REML (default; Viechtbauer 2005; Raudenbush 2009): maximise
  l_R(tau^2) = -1/2 [ sum log(v_i + tau^2) + log sum 1/(v_i + tau^2) + sum (y_i - mu_hat)^2/(v_i + tau^2) ]
  by bounded scalar optimisation (scipy `minimize_scalar`), with an explicit check of the
  boundary tau^2 = 0. For meta-regression the middle term becomes log|X' W X|.
  REML is the default because DL is biased downward for small k and large heterogeneity, and
  REML was among the estimators recommended by Veroniki et al. (2016) and by the simulation
  study of Langan et al. (2019); it is also metafor's default, which makes the results
  comparable with most published R-based analyses.

Random effects: mu = sum(w* y)/sum(w*), var(mu) = 1/sum(w*).

**Hartung-Knapp-Sidik-Jonkman** (Hartung & Knapp 2001; Sidik & Jonkman 2002; IntHout 2014):
var_HK(mu) = q / sum(w*) with q = sum(w* (y - mu)^2)/(k-1), CI = mu +/- t_{k-1} sqrt(var_HK).
Default when k >= 3. The z-based random-effects CI has below-nominal coverage when k is small
or heterogeneity is large; HKSJ corrects this and performs well across tau^2 estimators.
`--hksj-truncate` applies the modification q = max(q, 1) so the HKSJ CI is never narrower than
the z-based CI (Röver 2015; discussed by Jackson 2017). `--no-hksj` reverts to z.

**Heterogeneity**: I^2 = tau^2/(tau^2 + s^2) and H^2 = (tau^2 + s^2)/s^2 with the "typical"
within-study variance s^2 = (k-1) sum(w) / [ (sum w)^2 - sum w^2 ] (Higgins & Thompson 2002).
This equals (Q - df)/Q for DL and keeps I^2 consistent with the REML tau^2, as in metafor.
Both are very imprecise with fewer than ~10 studies (Ioannidis 2007; von Hippel 2015).

**Prediction interval** (Higgins, Thompson & Spiegelhalter 2009; IntHout 2016):
mu +/- t_{k-2} sqrt(tau^2 + var(mu)), using the HKSJ var(mu) when HKSJ is on. Reported only for
k >= 3; it answers "what effect might the next study show" and is the honest summary when I^2
is high.

**Small k**: k = 2 gives a fixed-effect average flagged descriptive only (tau^2 cannot be
estimated usefully from two points); k = 1 is not pooled.

## 3. Leave-one-out, subgroups, meta-regression

Leave-one-out refits the same model without each study (Viechtbauer & Cheung 2010 for the wider
set of influence diagnostics; this script implements only the omission table).

Subgroups: separate random-effects model per level (own tau^2), between-groups
Q_B = sum_g W_g (mu_g - mu_bar)^2 with W_g = 1/var(mu_g), df = G - 1 (Borenstein 2009 ch. 19,
"separate estimates of tau^2"). A shared-tau^2 alternative is the dummy-variable meta-regression.

Meta-regression: mixed-effects model y = X beta + u + e, tau^2 by REML, beta = (X'WX)^-1 X'Wy,
Knapp-Hartung variance scaling by sum(w* r^2)/(k-p) with t_{k-p} tests and an F_{m, k-p} omnibus
test (Knapp & Hartung 2003; Viechtbauer 2010). QE for residual heterogeneity uses fixed-effect
weights (as metafor). R^2 analogue = (tau^2_null - tau^2_model)/tau^2_null. Rule adopted: at least
10 studies per covariate (Cochrane Handbook 10.11.5.1; Higgins & Thompson 2004 on inflated
false positives), overridable with `--force-metareg` and then labelled exploratory.

## 4. Small-study effects

Egger's test (Egger 1997) as the weighted regression of y on SE with weights 1/v (Sterne &
Egger 2005); the SE coefficient's t-test on k-2 df is the asymmetry test. Run only with k >= 10
(Sterne et al. 2011, BMJ) and never for proportions, where the estimate and its variance are
functionally related so the test is misleading (Hunter et al. 2014); for log odds ratios Peters
et al. (2006) is the alternative, not implemented here. The funnel plot is drawn on the analysis
scale with back-transformed tick labels and pseudo-95% limits. Asymmetry has causes other than
publication bias: true heterogeneity, choice of effect measure, chance.

## 5. Conversions (convert.py)

- CI -> SE: (upper - lower)/(2 z_{alpha/2}) on the stated scale (normal, log, logit, Fisher z),
  with a check that the point estimate sits at the CI midpoint on that scale.
- t -> d: d = t sqrt((n1+n2)/(n1 n2)); F (1 df) -> d = sqrt(F) * same factor, sign supplied;
  p -> t via the t quantile with n1+n2-2 df (Borenstein 2009 ch. 7; Lipsey & Wilson 2001).
- d <-> r: r = d/sqrt(d^2 + a), a = (n1+n2)^2/(n1 n2); d = 2r/sqrt(1-r^2) (Borenstein 2009 ch. 7).
- OR, RR from 2x2 with Woolf log SE; 0.5 added to all cells when any is zero.
- IQR -> SD = IQR/1.35; range -> SD by Wan et al. (2014) eq. 9.
- Visual-acuity unit conversions are in the data-extraction skill, not here.

## References

- Barker TH, Migliavaca CB, Stein C, et al. Conducting proportional meta-analysis in different types of systematic reviews: a guide for synthesisers of evidence. BMC Med Res Methodol 2021;21:189.
- Bonett DG, Wright TA. Sample size requirements for estimating Pearson, Kendall and Spearman correlations. Psychometrika 2000;65:23-28.
- Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. Wiley 2009.
- Colditz GA, Brewer TF, Berkey CS, et al. Efficacy of BCG vaccine in the prevention of tuberculosis. JAMA 1994;271:698-702.
- DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials 1986;7:177-188.
- Egger M, Davey Smith G, Schneider M, Minder C. Bias in meta-analysis detected by a simple, graphical test. BMJ 1997;315:629-634.
- Freeman MF, Tukey JW. Transformations related to the angular and the square root. Ann Math Stat 1950;21:607-611.
- Hanley JA, McNeil BJ. The meaning and use of the area under a receiver operating characteristic (ROC) curve. Radiology 1982;143:29-36.
- Hartung J, Knapp G. On tests of the overall treatment effect in meta-analysis with normally distributed responses. Stat Med 2001;20:1771-1782.
- Hedges LV. Distribution theory for Glass's estimator of effect size and related estimators. J Educ Stat 1981;6:107-128.
- Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Stat Med 2002;21:1539-1558.
- Higgins JPT, Thompson SG. Controlling the risk of spurious findings from meta-regression. Stat Med 2004;23:1663-1682.
- Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc A 2009;172:137-159.
- Higgins JPT, Thomas J, et al. (eds). Cochrane Handbook for Systematic Reviews of Interventions, version 6.4, 2023; sections 10.10-10.11.
- Hunter JP, Saratzis A, Sutton AJ, et al. In meta-analyses of proportion studies, funnel plots were found to be an inaccurate method of assessing publication bias. J Clin Epidemiol 2014;67:897-903.
- IntHout J, Ioannidis JPA, Borm GF. The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method. BMC Med Res Methodol 2014;14:25.
- IntHout J, Ioannidis JPA, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. BMJ Open 2016;6:e010247.
- Jackson D, Law M, Rücker G, Schwarzer G. The Hartung-Knapp modification for random-effects meta-analysis: a useful refinement but are there any residual concerns? Stat Med 2017;36:3923-3934.
- Knapp G, Hartung J. Improved tests for a random effects meta-regression with a single covariate. Stat Med 2003;22:2693-2710.
- Langan D, Higgins JPT, Jackson D, et al. A comparison of heterogeneity variance estimators in simulated random-effects meta-analyses. Res Synth Methods 2019;10:83-98.
- Miller JJ. The inverse of the Freeman-Tukey double arcsine transformation. Am Stat 1978;32:138.
- Peters JL, Sutton AJ, Jones DR, Abrams KR, Rushton L. Comparison of two methods to detect publication bias in meta-analysis. JAMA 2006;295:676-680.
- Raudenbush SW. Analyzing effect sizes: random-effects models. In Cooper, Hedges, Valentine (eds) Handbook of Research Synthesis and Meta-Analysis, 2nd ed. 2009.
- Röver C, Knapp G, Friede T. Hartung-Knapp-Sidik-Jonkman approach and its modification for random-effects meta-analysis with few studies. BMC Med Res Methodol 2015;15:99.
- Schwarzer G, Chemaitelly H, Abu-Raddad LJ, Rücker G. Seriously misleading results using inverse of Freeman-Tukey double arcsine transformation in meta-analysis of single proportions. Res Synth Methods 2019;10:476-483.
- Sidik K, Jonkman JN. A simple confidence interval for meta-analysis. Stat Med 2002;21:3153-3159.
- Sterne JAC, Egger M. Regression methods to detect publication and other bias in meta-analysis. In Rothstein, Sutton, Borenstein (eds) Publication Bias in Meta-Analysis. Wiley 2005.
- Sterne JAC, Sutton AJ, Ioannidis JPA, et al. Recommendations for examining and interpreting funnel plot asymmetry in meta-analyses of randomised controlled trials. BMJ 2011;343:d4002.
- Veroniki AA, Jackson D, Viechtbauer W, et al. Methods to estimate the between-study variance and its uncertainty in meta-analysis. Res Synth Methods 2016;7:55-79.
- Viechtbauer W. Bias and efficiency of meta-analytic variance estimators in the random-effects model. J Educ Behav Stat 2005;30:261-293.
- Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw 2010;36(3):1-48.
- Viechtbauer W, Cheung MWL. Outlier and influence diagnostics for meta-analysis. Res Synth Methods 2010;1:112-125.
- Wan X, Wang W, Liu J, Tong T. Estimating the sample mean and standard deviation from the sample size, median, range and/or interquartile range. BMC Med Res Methodol 2014;14:135.
- Zhou X-H, Obuchowski NA, McClish DK. Statistical Methods in Diagnostic Medicine, 2nd ed. Wiley 2011.
