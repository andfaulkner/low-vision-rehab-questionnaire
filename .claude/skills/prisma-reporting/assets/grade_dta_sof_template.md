# GRADE Summary of Findings table: diagnostic test accuracy (template)

Layout follows the GRADE approach for test accuracy (Schünemann HJ, et al. BMJ 2008;336:1106-10; GRADE Handbook, chapter on diagnostic tests; Schünemann HJ, et al. J Clin Epidemiol 2020;122:129-141 and 142-152) as used in Cochrane DTA reviews and GRADEpro. One table per index test x reference standard comparison (or one table with one block per comparison). `scripts/sof_table.py` fills the per-1000 cells and the certainty column from pooled estimates; this file shows what the finished table should look like and what each placeholder means. Keep placeholders in {braces} until they are replaced.

**Question:** Should {index test} be used to identify {target condition, e.g. adults who need low vision rehabilitation} in {population and setting}?

**Index test:** {name; positive if {threshold}}. **Reference standard:** {measured visual acuity worse than X / visual field criterion / clinician-judged LVR need / full-length questionnaire cut-off}. **Target condition:** {definition}.

**Pooled sensitivity:** {0.xx (95% CI 0.xx to 0.xx)}. **Pooled specificity:** {0.xx (95% CI 0.xx to 0.xx)}. {k} studies, {n} participants. Model: {bivariate random-effects (Reitsma 2005) / none, estimates shown per study}.

**Pre-test probabilities:** {10%, 30%, 50%}: {say where each comes from, e.g. the median prevalence in the included studies, the prevalence of VA < 6/12 in a glaucoma clinic series, a plausible upper bound in a tertiary LVR referral population}.

| Outcome | No. of studies (participants) | Study design | Risk of bias | Indirectness | Inconsistency | Imprecision | Publication bias | Per 1000 at {10%} | Per 1000 at {30%} | Per 1000 at {50%} | Certainty of evidence |
|---|---|---|---|---|---|---|---|---:|---:|---:|---|
| True positives (people with {condition} correctly identified) | {k} ({n}) | {cross-sectional / cohort / case-control} | {not serious / serious^a / very serious} | {…} | {…} | {…} | {undetected / strongly suspected} | {TP (lo to hi)} | {…} | {…} | {⊕⊕⊕◯ MODERATE} |
| False negatives (people with {condition} who are missed and would not be referred) | {k} ({n}) | {…} | {…} | {…} | {…} | {…} | {…} | {FN (lo to hi)} | {…} | {…} | {same as TP row} |
| True negatives (people without {condition} correctly identified) | {k} ({n}) | {…} | {…} | {…} | {…} | {…} | {…} | {TN (lo to hi)} | {…} | {…} | {⊕⊕◯◯ LOW} |
| False positives (people without {condition} who would be referred or assessed unnecessarily) | {k} ({n}) | {…} | {…} | {…} | {…} | {…} | {…} | {FP (lo to hi)} | {…} | {…} | {same as TN row} |
| Inconclusive or missing index test results | {k} ({n}) | | | | | | | {n per 1000, if reported} | | | {rate only if used in the decision} |

**Certainty:** ⊕⊕⊕⊕ high; ⊕⊕⊕◯ moderate; ⊕⊕◯◯ low; ⊕◯◯◯ very low. Sensitivity (TP, FN rows) and specificity (TN, FP rows) are rated separately because their evidence can differ.

**Explanations (one letter per downgrade, cite the QUADAS-2 domain or the statistic that drove it):**

^a {e.g. Three of four studies enrolled a case-control sample (QUADAS-2 patient selection, high risk) and two did not blind the reference standard to the questionnaire.}
^b {e.g. Participants were LVR clinic attenders with established visual impairment, whereas the review question concerns unselected clinic patients (indirectness of population).}
^c {e.g. Sensitivity ranged from 0.55 to 0.92 with non-overlapping confidence intervals and no explanation from threshold or setting.}
^d {e.g. The 95% CI for specificity spans 0.52 to 0.83, i.e. between 170 and 480 unnecessary referrals per 1000 at 30% prevalence, which would change the decision.}
^e {e.g. Fewer than 10 studies, so funnel-plot asymmetry (Deeks' test) could not be assessed; small positive studies predominate.}

**How the numbers per 1000 are computed** (prevalence p, sensitivity Se, specificity Sp): TP = 1000·p·Se; FN = 1000·p·(1−Se); TN = 1000·(1−p)·Sp; FP = 1000·(1−p)·(1−Sp). Ranges use the CI limits of Se or Sp.

**Downstream consequences (optional row or paragraph; GRADE prefers it when the review informs a decision):** {What happens to a false negative (missed LVR need, continued disability) and a false positive (an unnecessary 20-minute LVR assessment)? The asymmetry justifies prioritising sensitivity for a screening item.}

**When not to produce this table:** when no pooled estimate exists and the studies use incompatible thresholds or reference standards, give instead a per-study table (study, n, threshold, reference standard, Se, Sp with CIs) and rate certainty narratively per domain; see references/grade_dta.md.
