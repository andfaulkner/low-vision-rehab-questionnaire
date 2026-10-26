# Criteria for good measurement properties (COSMIN, updated 2018)

A paraphrase of Table 1 in Prinsen CAC, Mokkink LB, Bouter LM, et al. COSMIN guideline for
systematic reviews of patient-reported outcome measures. Qual Life Res 2018;27:1147-1157
(doi:10.1007/s11136-018-1798-3), with the Terwee 2007 origins noted where the thresholds come
from there. Each *result* (one study, one instrument, one property) is rated **+ sufficient**,
**- insufficient** or **? indeterminate**. These ratings come *after* and *separately from* the
COSMIN risk-of-bias rating of the study (risk-of-bias skill): a sufficient result from a
doubtful study is still "+", but the quality of evidence is downgraded later.

`scripts/rate_properties.py` applies exactly the rules below. Where the script has to choose a
convention that COSMIN leaves to the reviewer, it is marked **(convention)**.

| Property | + sufficient | - insufficient | ? indeterminate |
|---|---|---|---|
| **Structural validity** | CTT (CFA): CFI or TLI or comparable > 0.95, *or* RMSEA < 0.06, *or* SRMR < 0.08. IRT/Rasch: *all four* of (1) no violation of unidimensionality (CFI/TLI > 0.95 or RMSEA < 0.06 or SRMR < 0.08, or a comparable measure such as PCA of residuals); (2) no violation of local independence (residual correlations after the dominant factor < 0.20, or Q3 < 0.37); (3) no violation of monotonicity (adequate-looking graphs or item scalability > 0.30); (4) adequate model fit (IRT chi-square p > 0.01; Rasch infit and outfit MNSQ 0.5-1.5, or Z-standardised fit between -2 and 2) | Criteria for "+" not met (one violated index for CFA; any violated aspect for Rasch/IRT) | Not all the information for "+" reported. EFA or PCA alone is "?" because the 2018 criterion names CFA or IRT/Rasch |
| **Internal consistency** | At least low-quality evidence for sufficient structural validity *and* Cronbach's alpha (or omega, KR-20, or an IRT/Rasch reliability) >= 0.70 for *each* unidimensional (sub)scale | At least low evidence for sufficient structural validity *and* alpha < 0.70 for a (sub)scale | The structural-validity precondition is not met (no evidence, or insufficient) |
| **Cross-cultural validity / measurement invariance** | No important differences between group factors (age, sex, language, culture) in multi-group CFA, *or* no important DIF (McFadden's R2 < 0.02) | Important differences or important DIF found | No multi-group analysis or DIF analysis reported. **(convention)** A count of DIF items without an importance judgement is "?"; the reviewer uses `override` to settle it |
| **Reliability** | ICC or weighted kappa >= 0.70 | ICC or weighted kappa < 0.70 | ICC or weighted kappa not reported. A Pearson or Spearman test-retest correlation is "?" because it ignores systematic change between occasions |
| **Measurement error** | SDC or limits of agreement < MIC (minimal important change) | SDC or LoA > MIC | MIC not defined. **(convention)** SDC is derived from a reported SEM as 1.96 x sqrt(2) x SEM when a MIC is given |
| **Criterion validity** | Correlation with the gold standard >= 0.70, *or* AUC >= 0.70 | Correlation or AUC < 0.70 | Not all information reported. Sensitivity and specificity alone are not rated here: an accuracy result against measured VA/VF belongs on the QUADAS-2 / DTA path (SKILL.md) |
| **Hypotheses testing for construct validity** | At least 75% of the *a-priori* hypotheses (direction and size of correlations, or of group differences) are confirmed | Less than 75% confirmed | No hypotheses defined; "correlated with VA, p < 0.05" without a stated expectation is "?" |
| **Responsiveness** | At least 75% of the a-priori hypotheses about change confirmed, *or* AUC (changed vs not changed) >= 0.70 | Less than 75% confirmed, or AUC < 0.70 | No hypotheses defined; an effect size on its own is "?" |

## Notes that matter for this review

- **Rasch person separation.** COSMIN's internal-consistency criterion is written for alpha but
  accepts an IRT/Rasch reliability. **(convention)** The script treats person separation
  reliability (PSR, Winsteps "person reliability") like alpha (>= 0.70), and converts a person
  separation *index* G to reliability with G^2 / (1 + G^2), so G >= 1.53 passes (G = 2.0 is
  reliability 0.80). Say which statistic the paper reported.
- **Hypotheses must be pre-specified.** COSMIN allows the review team to formulate generic
  hypotheses in the protocol (for example "correlation with logMAR VA between 0.30 and 0.60;
  correlation with visual-field MD at least 0.30 in glaucoma samples; LVR patients score lower
  than normally sighted controls"). Put those in `hypothesis` or set `confirmed` and cite the
  protocol; otherwise the result stays "?".
- **A questionnaire validated against measured VA** is hypotheses testing for COSMIN (there is
  no gold standard for a PROM) unless the review protocol declares VA/VF the reference standard
  of an accuracy question, in which case it is a QUADAS-2 study and the sensitivity/specificity
  go to the DTA path. Both can be true for one paper.
- **Subscales.** The alpha criterion applies per unidimensional (sub)scale: one alpha over a
  multidimensional total (NEI VFQ-25 composite, APEDS-VFQ total) does not meet it. Put one row
  per subscale with the `subscale` column.
- **Summary across studies** (Prinsen 2018 step 8): all "+" (ignoring "?") -> "+"; all "-" ->
  "-"; a mixture -> "+-" inconsistent, unless an explanation (population, language, mode) lets
  you summarise per subgroup (`--by`). **(convention)** The script summarises strictly by
  default; `--majority 0.75` applies a 75% rule and still downgrades for inconsistency.
- **Quality of evidence** is graded per summarised result with the modified GRADE rules in
  `references/cosmin_sr.md`. Indeterminate summaries are not graded.

## Thresholds in one line, for the Methods

"Results were rated against the COSMIN updated criteria for good measurement properties
(Prinsen 2018): structural validity CFI/TLI > 0.95 or RMSEA < 0.06 or SRMR < 0.08 (Rasch: fit
0.5-1.5, residual correlations < 0.20, scalability > 0.30, unidimensionality); internal
consistency alpha or person-separation reliability >= 0.70 given sufficient structural validity;
reliability ICC or weighted kappa >= 0.70; measurement error SDC < MIC; criterion validity r or
AUC >= 0.70; hypotheses testing and responsiveness >= 75% of pre-specified hypotheses confirmed."
