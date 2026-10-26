# QUADAS-2 for this review

QUADAS-2 (Whiting et al. 2011) is the tool Cochrane recommends for judging risk of bias and
applicability in diagnostic test accuracy (DTA) studies. It has four domains, each judged for
**risk of bias** (Low / High / Unclear); the first three are also judged for **applicability
concerns** (Low / High / Unclear). The judgements are reached through signalling questions
(answered Yes / No / Unclear) that the review team tailors to its question. QUADAS-2 does not
produce a score: domain judgements are reported as they are and used for sensitivity analyses,
never summed.

## The standard signalling questions

Taken from Whiting et al. 2011 (Table and Appendix); wording lightly condensed.

| Domain | Risk-of-bias signalling questions | Applicability question |
|---|---|---|
| 1 Patient selection | Was a consecutive or random sample of patients enrolled? Was a case-control design avoided? Did the study avoid inappropriate exclusions? | Are there concerns that the included patients and setting do not match the review question? |
| 2 Index test | Were the index test results interpreted without knowledge of the results of the reference standard? If a threshold was used, was it pre-specified? | Are there concerns that the index test, its conduct, or its interpretation differ from the review question? |
| 3 Reference standard | Is the reference standard likely to correctly classify the target condition? Were the reference standard results interpreted without knowledge of the results of the index test? | Are there concerns that the target condition as defined by the reference standard does not match the question? |
| 4 Flow and timing | Was there an appropriate interval between index test and reference standard? Did all patients receive the same reference standard? Did all patients receive a reference standard? Were all patients included in the analysis? | (none) |

## Tailored questions for the LVR screening-question review

QUADAS-2 expects reviewers to adapt the questions to their topic and to add or drop questions
(Whiting 2011, phase 2 "tailoring"). The CSV template has four slots per domain
(`signalling_q1..q4`); answer `NA` for a slot that does not apply to a study. Any extra
question must be written into `notes`.

### D1 Patient selection

| q | Question | Why it matters here |
|---|---|---|
| q1 | Was a consecutive, random or whole-population sample of adults enrolled (not a hand-picked or convenience sample)? | Convenience samples from LVR clinics inflate prevalence and sensitivity. |
| q2 | Was a case-control (two-gate) design avoided, i.e. were people with and without the target condition recruited from the same source rather than low-vision patients plus normally-sighted volunteers? | Two-gate designs overestimate both sensitivity and specificity (Rutjes 2006). Purposive sampling "across the spectrum" is a milder version; answer U and explain. |
| q3 | Did the study avoid inappropriate exclusions (e.g. excluding people with cognitive impairment, non-native speakers, or anyone who could not complete the vision test)? | Such exclusions remove exactly the people a brief screen is meant to reach. |
| q4 | Was enrolment into the accuracy analysis independent of the answers to the screening question(s)? | Two-stage surveys that verify all positives and a sample of negatives yield sensitivity/specificity that do not apply to an unselected population unless reweighted. Record here and in D4 q2, but escalate only one domain for it. |

Applicability: adults 18+ in a setting where the screen would be used (community, primary care,
general eye clinic, LVR intake). A sample that is mostly LVR patients, or only one disease
(e.g. glaucoma only), is a High concern if the review question is general screening; say so.

### D2 Index test (the questionnaire or screening item)

| q | Question | Why it matters here |
|---|---|---|
| q1 | Was the questionnaire/item answered before, and without knowledge of, the vision measurement or diagnosis used as reference standard (and, where someone scores it, was the scorer blind)? | Self-report by people who have just been told their acuity is not an independent test. |
| q2 | Was the positive-screen threshold (cut-off score, response pattern, "yes to >= 1 item") pre-specified rather than chosen to maximise accuracy in the same sample? | Data-driven thresholds and best-of-many item selection give optimistic accuracy (Leeflang 2008). |
| q3 | If items or cut-offs were selected from a larger pool, was that done in a separate development sample, or validated in an independent sample? | Same optimism problem one level up: picking the best item of 100 by AUC in the analysis sample. |
| q4 | Was the index test administered in the same way to all participants and as it would be in practice (same wording, mode, interviewer vs self-complete, stand-alone vs embedded in a longer survey)? | Mode and context change the answers to self-report items. |

Applicability: the review is about brief self-report questions and full-length PROMs used to
flag LVR need. An item answered inside a 100-item battery, a performance test, or a clinician
rating is a concern. Note whether the published wording is the one that would be used.

### D3 Reference standard

| q | Question | Why it matters here |
|---|---|---|
| q1 | Is the reference standard likely to classify the target condition correctly: visual acuity with a standard chart (ETDRS/Bailey-Lovie/logMAR or Snellen) with correction status stated; visual field with standard perimetry; LVR need by documented clinician criteria; or a full-length questionnaire with an established cut-off? | A proxy such as self-reported diagnosis or registration status is not a reference standard for this review. |
| q2 | Was the reference standard measured or interpreted without knowledge of the questionnaire answers? | Examiner expectation can change chart-reading encouragement and endpoint. |
| q3 | Was the threshold that defines the target condition (e.g. VA worse than 0.3 logMAR / 6/12 in the better eye, VF < 20 degrees) pre-specified and stated? | Thresholds chosen after seeing the data, or left unstated, make the 2x2 unreproducible. |
| q4 | Was the measurement made under a stated protocol for this study (chart, distance, eye, correction), not pulled from heterogeneous clinical records of unknown provenance? | EHR acuity fields mix charts, eyes and correction states. |

Applicability: the review's target condition is "needs LVR". VA-defined low vision is an
accepted proxy (the review protocol lists measured VA, VF, full questionnaires and clinician
judgement as reference standards), so judge Low when the threshold is a conventional low
vision definition, but note when field loss, contrast or reading performance are ignored.

### D4 Flow and timing

| q | Question | Why it matters here |
|---|---|---|
| q1 | Was the interval between the questionnaire and the vision measurement appropriate (same visit or within about 3 months, with no intervening cataract surgery, LVR or progression)? | Vision in older adults changes over months. |
| q2 | Did all participants receive a reference standard, with verification not dependent on the screening answer (no partial verification, no loss > ~20%)? | Partial verification inflates sensitivity and deflates specificity. |
| q3 | Did all participants receive the same reference standard? | VA for some and records/self-report for others is differential verification. |
| q4 | Were all participants included in the 2x2 / analysis (does the n in the accuracy table equal the n enrolled; are missing data explained)? | Silent exclusions usually remove hard cases. |

## Judgement rules

- Risk of bias per domain: **all answered questions Yes -> Low**; **any No -> High** (QUADAS-2
  says "potential for bias", so the assessor may keep the domain at Unclear when the No is
  minor, but must explain why in `notes`); **otherwise Unclear**. `NA` answers are ignored.
  `scripts/rob_plots.py` recomputes this and warns when the recorded judgement differs.
- Applicability per domain: a single judgement, Low / High / Unclear, with its own quote.
- Overall per study (for text and sensitivity analyses): High if any domain is High, Unclear if
  none High and any Unclear, else Low. Do not compute a score.
- Every judgement cites a verbatim sentence from the article text and the `[page N]` marker of
  `data/articles_text/<file>.txt`. "Not reported" is a finding: quote the nearest passage and
  write "not stated" in notes. Never infer a Yes from silence.

## Using the judgements in the synthesis

- Report the traffic-light plot (per study) and the summary plot (per domain) in Results, and
  the tailored questions in Methods or a supplement (PRISMA-DTA item 12, McInnes 2018).
- Pre-specify a sensitivity analysis: repeat any pooled estimate excluding studies at High risk
  in D2 or D4 (the domains that most often distort accuracy). With the small number of studies
  expected here, state the excluded studies by name instead of fitting a meta-regression.
- Feed D2 q2/q3 (data-driven thresholds) to the data-extraction and DTA skills: such studies
  should be flagged, and often not pooled with pre-specified-threshold studies.
- Risk of bias is one of the GRADE domains for DTA evidence (Schünemann 2008; 2020): downgrade
  when most weight comes from High-risk studies.

## When QUADAS-2 is the wrong tool

- **Comparative accuracy** (two questionnaires compared head-to-head in the same participants):
  add QUADAS-C (Yang et al. 2021), which supplies comparison-specific signalling questions.
- **Prediction models** (logistic regression combining items and covariates, with AUC): use
  PROBAST (Wolff et al. 2019) rather than QUADAS-2.
- **Measurement-property studies** (reliability, validity, Rasch): COSMIN RoB checklist, see
  `cosmin.md`.
- **Guidelines**: AGREE II. **Interventions/RCTs**: RoB 2. **Prevalence surveys** that report no
  accuracy data: not eligible for this question.
- **Reviews of self-report vs measured vision in general** (e.g. the Cochrane screening review
  in `data/articles_text/`): a review is not a primary study; assess with AMSTAR 2 only if its
  conclusions are used.

## References

- Whiting PF, Rutjes AWS, Westwood ME, Mallett S, Deeks JJ, Reitsma JB, Leeflang MMG, Sterne JAC,
  Bossuyt PMM; QUADAS-2 Group. QUADAS-2: a revised tool for the quality assessment of diagnostic
  accuracy studies. Ann Intern Med. 2011;155(8):529-536. doi:10.7326/0003-4819-155-8-201110180-00009.
  Tool, background document and tailoring guidance: https://www.bristol.ac.uk/population-health-sciences/projects/quadas/
- Yang B, Mallett S, Takwoingi Y, et al. QUADAS-C: a tool for assessing risk of bias in
  comparative diagnostic accuracy studies. Ann Intern Med. 2021;174(11):1592-1599.
  doi:10.7326/M21-2234. Use as an add-on to QUADAS-2 when a study compares two index tests.
- Reitsma JB, Rutjes AWS, Whiting P, Yang B, Leeflang MM, Bossuyt PM, Deeks JJ. Chapter 8:
  Assessing risk of bias and applicability. In: Deeks JJ, Bossuyt PM, Leeflang MM, Takwoingi Y
  (eds). Cochrane Handbook for Systematic Reviews of Diagnostic Test Accuracy, version 2.
  Cochrane, 2023. https://training.cochrane.org/handbook-diagnostic-test-accuracy
- Rutjes AWS, Reitsma JB, Di Nisio M, Smidt N, van Rijn JC, Bossuyt PMM. Evidence of bias and
  variation in diagnostic accuracy studies. CMAJ. 2006;174(4):469-476.
- Leeflang MMG, Moons KGM, Reitsma JB, Zwinderman AH. Bias in sensitivity and specificity caused
  by data-driven selection of optimal cutoff values. Clin Chem. 2008;54(4):729-737.
- McInnes MDF, Moher D, Thombs BD, et al. Preferred Reporting Items for a Systematic Review and
  Meta-analysis of Diagnostic Test Accuracy Studies: the PRISMA-DTA statement. JAMA.
  2018;319(4):388-396.
- Schünemann HJ, Oxman AD, Brozek J, et al. GRADE: grading quality of evidence and strength of
  recommendations for diagnostic tests and strategies. BMJ. 2008;336:1106-1110; and Schünemann
  HJ, Mustafa RA, Brozek J, et al. GRADE guidelines: 21 part 1 and part 2 (test accuracy).
  J Clin Epidemiol. 2020;122:129-141 and 142-152.
- Wolff RF, Moons KGM, Riley RD, et al. PROBAST: a tool to assess the risk of bias and
  applicability of prediction model studies. Ann Intern Med. 2019;170(1):51-58.
- Brouwers MC, Kho ME, Browman GP, et al. AGREE II: advancing guideline development, reporting
  and evaluation in health care. CMAJ. 2010;182(18):E839-E842. https://www.agreetrust.org
