# GRADE for diagnostic test accuracy: the rules `sof_table.py` applies

Sources: Schünemann 2008 BMJ; GRADE Handbook (2013), chapter on diagnostic tests; GRADE guidelines 21 parts 1 and 2 (J Clin Epidemiol 2020;122:129-152); GRADE guidelines 22; Cochrane DTA Handbook ch. 11. Full citations in `citations.md`.

GRADE for test accuracy rates the certainty that the pooled sensitivity and specificity are close to the truth for the review question, not the certainty that the test improves outcomes. Rate sensitivity (TP, FN rows) and specificity (TN, FP rows) separately; they often differ.

## Starting level

- Cross-sectional or cohort accuracy studies that enrol patients with diagnostic uncertainty (consecutive or random sampling) and compare the index test with a reference standard in all participants start at **high**.
- Case-control ("two-gate") designs that take known cases and healthy controls, and studies that only validate a questionnaire against an instrument score without a diagnostic uncertainty population, overstate accuracy. GRADE 2008 treats them as starting lower; GRADE 2020 treats the design as a risk-of-bias problem (QUADAS-2 patient selection, high risk) and downgrades. Either way they cannot end at high. The script's `start` field (default `high`) lets you follow either convention; say which in the Methods.

## Downgrading domains

Each judgement is "not serious" (0), "serious" (−1) or "very serious" (−2); publication bias is "undetected" (0) or "strongly suspected" (−1). Levels: high → moderate → low → very low (floor). Every downgrade needs a lettered footnote stating the reason, which must be specific enough that another reviewer could check it.

1. **Risk of bias** (from QUADAS-2). Downgrade when most of the weight comes from studies at high or unclear risk in a domain that would bias the estimate in question: patient selection (case-control, non-consecutive, inappropriate exclusions) inflates both sensitivity and specificity; index-test domain (threshold chosen after seeing the data, questionnaire administered by the examiner who knows the acuity) inflates accuracy; reference-standard domain (acuity measured without a protocol, LVR need judged by someone who saw the questionnaire) and flow and timing (not all participants received the reference standard, or long delays). A single small study at high risk among several good ones is usually "not serious".
2. **Indirectness**. Population (LVR clinic attenders with established impairment vs unselected glaucoma clinic patients), index test (a different wording or language of the item; self-completed vs interviewer-administered), reference standard (acuity-only when the question is LVR need), and the outcome: accuracy itself is an indirect outcome for a decision about referral. Downgrade once for a clear mismatch, twice if several.
3. **Inconsistency**. Unexplained variability in sensitivity or specificity across studies: wide spread of point estimates, non-overlapping confidence intervals, large between-study variance in the bivariate model, a large prediction region. Threshold differences explain some variability; if they do, say so and consider indirectness instead (results at a threshold the clinic will not use). With k ≤ 3 do not call it "not serious" merely because there is too little data to see inconsistency; rate imprecision instead and say inconsistency "could not be assessed".
4. **Imprecision**. Judge the width of the confidence intervals in terms of the per-1000 consequences: if the CI spans values that would lead to different decisions (e.g. specificity 0.52–0.83 means 170–480 unnecessary referrals per 1000 at 30% prevalence), downgrade. Rules of thumb: fewer than ~100 participants with the target condition for sensitivity, or fewer than ~100 without it for specificity, usually "serious"; k = 1–2 with wide CIs usually "very serious".
5. **Publication bias**. Deeks' funnel test has low power and is unreliable with fewer than 10 studies. With small k, state that it could not be assessed and rate "undetected" unless there is a specific reason (industry-sponsored instrument validations only, selective reporting of the best threshold, grey literature excluded) to rate "strongly suspected".

Upgrading (large effect, dose-response) is not used for test accuracy.

## Per-1000 consequences

For prevalence p, sensitivity Se, specificity Sp: TP = 1000·p·Se; FN = 1000·p·(1 − Se); TN = 1000·(1 − p)·Sp; FP = 1000·(1 − p)·(1 − Sp). Ranges use the CI limits. Choose 2–3 prevalences that represent real settings and say where each comes from: the prevalence of the target condition in the included studies, in a glaucoma clinic series, and in an LVR referral population. Prevalence here is the prevalence of the **target condition as defined by the reference standard** (e.g. VA worse than 6/12, or clinician-judged LVR need), not of glaucoma.

Add a sentence on downstream consequences: what a missed case (FN) and an unnecessary assessment (FP) cost. For a screening item that triggers a 20-minute LVR work-up, FP costs are low and FN costs are high, which justifies weighting sensitivity.

## When a Summary of Findings table is not appropriate

- **No pooled estimate**: `dta_pool.py` writes `"pooled": null` when k < 4 or thresholds/reference standards are mixed. Then do not fabricate a pooled row. Present a per-study table (study, n, setting, threshold, reference standard, Se and Sp with CIs) and rate certainty for the body of evidence narratively per domain, or give a GRADE rating per study if the review will be used for a decision and the studies address the same question.
- **Only correlations or AUCs** (no 2x2 data): the per-1000 framing does not apply. Use the generic GRADE Summary of Findings for continuous outcomes or report certainty in the text; AUC can be rated with the same five domains without the consequence columns.
- **Validation-only studies** (Rasch, reliability): GRADE for test accuracy does not apply; COSMIN's modified GRADE for measurement properties (Prinsen 2018) does, with domains risk of bias, inconsistency, imprecision and indirectness.
- **Narrative or scoping review**: a SoF table implies a systematic body of evidence; include it only if the review's selection was systematic.

## Wording for the Results

"Certainty of evidence for the sensitivity of {index test} against {reference standard} was {low} (downgraded for risk of bias and inconsistency), and for its specificity {very low} (additionally downgraded for imprecision). At a pre-test probability of {30%}, the test would correctly identify {240} of {300} people with {condition} and miss {60}, and would flag {175} of {700} people without it (Table {N})."
