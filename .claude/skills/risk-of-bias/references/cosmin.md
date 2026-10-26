# COSMIN Risk of Bias checklist (summary)

Use this for included studies whose contribution is a **measurement property** of a
questionnaire (NEI VFQ-25, VA LV VFQ-48, LVQOL, IVI, GQL-15, Activity Inventory, translations
and short forms): reliability, internal consistency, measurement error, structural validity
(factor analysis, Rasch/IRT), criterion validity, hypotheses testing for construct validity,
cross-cultural validity, responsiveness. Such studies tell the review how trustworthy a
full-length questionnaire is as a reference standard or as an index test, but they usually
do not give a 2x2 table, so they are not pooled with the accuracy studies.

Source: Mokkink LB, de Vet HCW, Prinsen CAC, Patrick DL, Alonso J, Bouter LM, Terwee CB.
COSMIN Risk of Bias checklist for systematic reviews of Patient-Reported Outcome Measures.
Qual Life Res. 2018;27(5):1171-1179. doi:10.1007/s11136-017-1765-4. The full checklist and
user manual (with the verbatim standards and rating rules) are free at https://www.cosmin.nl.
The wording in `assets/cosmin_template.csv` is a paraphrase; when a rating hinges on exact
wording, check the manual.

## How the checklist works

- One **box per measurement property** (Box 1 PROM development, 2 content validity,
  3 structural validity, 4 internal consistency, 5 cross-cultural validity / measurement
  invariance, 6 reliability, 7 measurement error, 8 criterion validity, 9 hypotheses testing
  for construct validity, 10 responsiveness). Assess only the boxes for properties the study
  actually reports.
- Each box lists **standards** about design and statistics, rated on a four-point scale:
  **Very good, Adequate, Doubtful, Inadequate**. "NA" is allowed when a standard does not
  apply (e.g. the kappa standard when scores are continuous).
- **Worst score counts**: the rating of a box is the lowest rating given to any of its
  standards. This is deliberate; one fatal flaw makes the result untrustworthy regardless
  of how well the rest was done. `scripts/cosmin_table.py` applies this rule and names the
  standard(s) that drove it, so the reviewer can see whether a single Doubtful rating is
  defensible.
- The ratings are then used in two further COSMIN steps that this skill only points to:
  (1) rate each **result** against the *criteria for good measurement properties*
  (sufficient +, insufficient -, indeterminate ?), and (2) summarise and grade the evidence
  (modified GRADE: risk of bias, inconsistency, imprecision, indirectness). See Prinsen et
  al. 2018 for the full guideline.

## Standards that matter most in this review

- **Structural validity (Box 3).** Factor analysis needs a sample of at least 7 times the
  number of items and at least 100 participants for Very good (5 times and >= 100, or 7 times
  but < 100, is Adequate; 5 times but < 100 is Doubtful; fewer is Inadequate). The IRT/Rasch
  sample-size rule is different and is given in the manual; quote it rather than reusing the
  factor-analysis rule. Rasch studies need fit statistics (item/person fit, unidimensionality,
  DIF) reported, or the rating is Doubtful.
- **Internal consistency (Box 4).** Cronbach's alpha is only interpretable for a
  unidimensional (sub)scale; a single alpha over a multidimensional questionnaire is a
  Doubtful design. For Rasch-based scales the person separation reliability counts.
- **Reliability and measurement error (Boxes 6-7).** Need a test-retest design with a stated
  interval, stable patients, and an ICC (model and formula stated) for continuous scores or
  (weighted) kappa for categorical scores; Pearson/Spearman correlations are Doubtful at best.
  SEM, SDC or limits of agreement are needed for measurement error. Both boxes are Inadequate
  when the "retest" is a different mode or setting.
- **Criterion validity (Box 8).** COSMIN accepts a gold standard only when one exists; for
  PROMs that is essentially a long form when a short form is evaluated. A questionnaire tested
  against measured VA is treated by COSMIN as **hypotheses testing (Box 9)**, not criterion
  validity. For this review the accuracy of a questionnaire against VA is also assessed with
  QUADAS-2, which is the tool that handles blinding, thresholds and verification.
- **Hypotheses testing (Box 9).** The study needs a priori hypotheses (direction and size of
  correlations or group differences) and comparator instruments whose own properties are
  adequate. "Correlated with VA, p < 0.05" without a hypothesis is Doubtful.
- **Responsiveness (Box 10).** Pre-post LVR studies (e.g. VA LV VFQ-48 before/after
  rehabilitation) need the intervention described and hypotheses about expected change, or a
  criterion for change; an effect size alone is Doubtful.

## Criteria for good measurement properties (for the step after risk of bias)

From Prinsen et al. 2018, Table 1. Stated here so the reviewer can see what "sufficient"
means; the risk-of-bias rating comes first and separately.

| Property | Sufficient (+) if |
|---|---|
| Structural validity | CFA: CFI or TLI > 0.95, RMSEA < 0.06, SRMR < 0.08; Rasch/IRT: no violation of unidimensionality, local independence, monotonicity, adequate model fit (e.g. infit/outfit 0.5-1.5) |
| Internal consistency | At least low evidence for sufficient structural validity AND alpha >= 0.70 for each unidimensional (sub)scale |
| Reliability | ICC or weighted kappa >= 0.70 |
| Measurement error | SDC or LoA < MIC |
| Criterion validity | Correlation with gold standard >= 0.70, or AUC >= 0.70 |
| Hypotheses testing | At least 75% of pre-stated hypotheses confirmed |
| Responsiveness | At least 75% of hypotheses about change confirmed, or AUC >= 0.70 |

Imprecision in the evidence-grading step is driven by the total sample size: downgrade one
level when the total n for a property is 50-100, two levels when it is below 50. Many LVR
questionnaire studies fall in that range; say so rather than reporting a confident summary.

## Definitions (COSMIN taxonomy, Mokkink et al. 2010)

- Reliability: the proportion of total variance that is true between-person variance.
- Measurement error: systematic and random error of a score not attributable to true change.
- Internal consistency: interrelatedness among items.
- Structural validity: the degree to which scores reflect the dimensionality of the construct.
- Cross-cultural validity / measurement invariance: performance of translated or adapted items
  is equivalent to the original.
- Criterion validity: agreement with a gold standard.
- Hypotheses testing for construct validity: consistency with hypotheses based on the
  assumption that the instrument measures the construct.
- Responsiveness: ability to detect change over time in the construct.

## References

- Mokkink LB, de Vet HCW, Prinsen CAC, et al. COSMIN Risk of Bias checklist for systematic
  reviews of Patient-Reported Outcome Measures. Qual Life Res. 2018;27(5):1171-1179.
- Prinsen CAC, Mokkink LB, Bouter LM, et al. COSMIN guideline for systematic reviews of
  patient-reported outcome measures. Qual Life Res. 2018;27(5):1147-1157.
- Terwee CB, Prinsen CAC, Chiarotto A, et al. COSMIN methodology for evaluating the content
  validity of patient-reported outcome measures: a Delphi study. Qual Life Res. 2018;27(5):1159-1170.
- Mokkink LB, Terwee CB, Patrick DL, et al. The COSMIN study reached international consensus
  on taxonomy, terminology, and definitions of measurement properties for health-related
  patient-reported outcomes. J Clin Epidemiol. 2010;63(7):737-745.
- COSMIN manual for systematic reviews of PROMs (2018) and the COSMIN Risk of Bias tool to
  assess the quality of studies on reliability and measurement error of outcome measurement
  instruments (Mokkink et al. 2020, BMC Med Res Methodol 20:293) at https://www.cosmin.nl.
