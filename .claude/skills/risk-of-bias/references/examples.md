# Two worked QUADAS-2 assessments

Both papers are in `data/articles_text/` and both report sensitivity and specificity of brief
self-report questions against measured visual acuity, so they are the kind of study the review
will pool. Page numbers are the `[page N]` markers in the `.txt` files (PDF pages, not journal
pages). Quotes are verbatim. These assessments were drafted by an AI assistant and are
**advisory until the reviewer confirms them**; the CSV rows are in
`assets/quadas2_example.csv`, which `scripts/rob_plots.py` reads as-is.

The review question used for applicability: *In adults, how accurately do brief self-report
questions or questionnaires identify people who need low vision rehabilitation, with measured
VA/VF, a full-length questionnaire or clinician judgement as reference standard?*

---

## Example 1: Wu et al. 2026, IOVS 67(1):28

File: `data/articles_text/Wu et al. - 2026 - Screening Questions to Identify Low Vision and Acu.txt`
(`Anchor article.txt` is the same paper). Design: 385 adults with measured VA answered a 100-item
acuity survey; each item, pair and triplet was scored against VA <= 0.3 logMAR (low vision) and
VA <= 1.0 logMAR (legal blindness). Headline: "In a fast-food restaurant, can you read the posted
menus?" AUC 0.85, sensitivity 0.89, specificity 0.81 for low vision (page 1).

### D1 Patient selection: risk of bias **Unclear**, applicability **High**

| q | Answer | Evidence |
|---|---|---|
| q1 consecutive/random | U | "Participants were recruited from four U.S. institutions between June 2019 and February 2022." (page 2). How they were sampled is deferred to the earlier publication (ref 7). |
| q2 case-control avoided | U | "The recruitment aimed to include individuals across a broad spectrum of visual function" (page 2). Purposive spectrum sampling, with 68.6% below 0.3 logMAR (page 3): not a two-gate design, but enriched. |
| q3 inappropriate exclusions avoided | Y | "Inclusion criteria required participants to be 18 years or older, have available VA data, and be able to communicate in English to complete the 100-item visual acuity survey." (page 2) |
| q4 enrolment independent of index test | Y | "All participants were naïve to the items at enrollment." (page 2) |

Rule: no N, not all Y -> Unclear. Applicability High because the authors themselves write that the
sample's "composition, with fewer normally sighted individuals than the general population, may
limit the generalizability of our findings to broader screening applications" (page 8): with 69%
prevalence, PPV/NPV and probably specificity will not transfer to a community screen.

### D2 Index test: risk of bias **High**, applicability **High** (reviewer may lower to Unclear)

| q | Answer | Evidence |
|---|---|---|
| q1 answered blind to VA | U | Not stated whether the survey preceded the VA measurement or whether participants knew their acuity; the paper only says the cohort was "previously described" (page 2). |
| q2 threshold pre-specified | N | The response rule is fixed ("For a single survey item, a 'no' response classified the participant as likely having low vision or legal blindness", page 3), but the item itself was chosen by ranking all 100: "The 20 items with the highest AUC at each threshold were retained as primary candidates for subsequent pairing." (page 3) and "Each of the top 20 items was paired with each of the remaining 99 (yielding 1980 unique combinations per threshold)." (page 3). Best-of-100 selection in the analysis sample is a data-driven threshold in the QUADAS-2 sense. |
| q3 selection validated in independent sample | N | "It is possible that the performance of individual items or short combinations might differ if administered independently, outside the context of the longer survey." (page 8). No split-sample or external validation. |
| q4 same administration | U | Mode of survey administration not described in this paper. |

Rule: any N -> High. Applicability: the review is about stand-alone screening questions; here
the item was one of 100 answered in a battery, which the authors flag as a limitation (page 8).
Recorded as High; a reviewer who treats the item wording as the test may call it Unclear. Either
way, extraction should flag the accuracy figures as optimistic (D2 q2/q3) and the DTA synthesis
should not pool them with studies that pre-specified a single item without a sensitivity analysis.

### D3 Reference standard: risk of bias **Unclear**, applicability **Low**

| q | Answer | Evidence |
|---|---|---|
| q1 correctly classifies | Y | "VA with habitual correction was assessed using standardized charts (Bailey–Lovie, ETDRS, or Snellen)." (page 2). Standard charts; habitual rather than best correction is acceptable for a screening question. |
| q2 blind to index test | U | Not stated. |
| q3 threshold pre-specified | Y | "low vision (VA ≤ 0.3 logMAR or 20/40) and legal blindness as defined by the VA criterion (VA ≤ 1 logMAR or 20/200)" (page 1): fixed clinical definitions. |
| q4 measured under a stated protocol | U | "When both monocular and binocular measurements were available, we used binocular VA; when only monocular measurements were available, VA from the better seeing eye was used." (page 2). Protocol details deferred to the earlier paper. |

Applicability Low for a VA-defined target condition, which the review accepts. Caveat for the
Discussion: "our VA-based items may misclassify individuals with preserved acuity but severely
constricted visual fields" (page 8), so glaucoma patients needing LVR for field loss are outside
what this study can show.

### D4 Flow and timing: risk of bias **Unclear** (override documented)

| q | Answer | Evidence |
|---|---|---|
| q1 appropriate interval | U | Not reported. |
| q2 all received reference standard | Y | "have available VA data" was an inclusion criterion (page 2). |
| q3 same reference standard | N | Binocular VA for some, better-eye monocular for others, on three chart types (page 2). |
| q4 all included in analysis | Y | "This analysis included 385 participants" (page 3); Table 1 N = 385. The 2x2 cells are not tabulated, so TP/FP/FN/TN must be back-calculated from sensitivity, specificity and the 264/121 split for extraction. |

The q3 "No" would trigger High under the algorithm. It was judged minor (same construct; chart and
binocular/monocular differences are of the order of 0.1 logMAR, small relative to the 0.3 logMAR
threshold) and the domain kept at Unclear, with the reason in `notes`. `rob_plots.py` prints a
warning for this row; that is the intended audit trail, not an error.

---

## Example 2: Gresset and Baumgarten 2002, Optom Vis Sci 79(7):416-423

File: `data/articles_text/Gresset and Baumgarten - 2002 - Prevalence of Visual Impairment and Utilization of.txt`.
Design: two Statistics Canada HALS questions ("Do you have trouble reading ordinary newsprint
with glasses...?"; "Do you have trouble seeing clearly the face of someone 12 feet away...?")
asked of 1777 community-dwelling Quebecers aged >= 65; a subsample of 65 had a home eye
examination with ETDRS charts. Sensitivity 75-100%, specificity 75-98% depending on item and
threshold (Table 4, page 5).

### D1 Patient selection: risk of bias **High**, applicability **Low**

| q | Answer | Evidence |
|---|---|---|
| q1 consecutive/random | Y | "A random sample of individuals aged at least 65 years was drawn for each selected area, with predetermined sampling fractions for age and sex categories." (page 2) |
| q2 case-control avoided | Y | Sampling was by questionnaire answer, not by vision status. |
| q3 inappropriate exclusions avoided | Y | Validation subsample restricted to "subjects in the Montreal area not eligible for other components of the CSHA" (page 2): a logistic, not vision-related, exclusion. |
| q4 enrolment independent of index test | N | "all positive subjects, along with a random sample of negative subjects, were selected to undergo a visual examination at home." (page 2). The authors state the consequence: "the sensitivity and specificity estimated in this study cannot be applied to an unselected population." (page 2) |

Applicability Low: community-dwelling older adults are the population in which a two-question
screen would be used; the index test is the test, not a research instrument.

### D2 Index test: risk of bias **Low**, applicability **Low**

| q | Answer | Evidence |
|---|---|---|
| q1 answered blind to VA | Y | "Data on visual impairment were collected during a home interview carried out as part of the CSHA study." (page 2), about six months before the examination (page 6). |
| q2 threshold pre-specified | Y | Four fixed test criteria listed under "Test Criteria" (page 3): near item; distance item; at least one positive; two positive. |
| q3 no data-driven item selection | Y | Items taken unchanged from HALS: "As defined in previous Statistics Canada surveys such as the Health and Activity Limitations Survey (HALS)" (page 2). |
| q4 same administration | Y | Interviewer-administered home interview for all. |

### D3 Reference standard: risk of bias **Low**, applicability **Low**

| q | Answer | Evidence |
|---|---|---|
| q1 correctly classifies | Y | "Distance VA was measured at 4 m using the Early Treatment Diabetic Retinopathy Survey charts17 in a back-lighted box.18 Near VA was measured at 0.4 m with a modified near Early Treatment Diabetic Retinopathy Survey chart." (page 2; the 17 and 18 are reference superscripts flattened into the text) |
| q2 blind to index test | Y | "The first author (JG), an optometrist who was not aware of the subjects’ questionnaire responses at the time of the examination, carried out the visual assessment." (page 2) |
| q3 threshold pre-specified | Y | ICD-9 categories: "Individuals with a best VA between 6/12 and 6/18 were considered to have a mild visual impairment" (page 2) and four diagnostic criteria (pages 2-3). |
| q4 stated protocol | Y | Measured for the study, presenting and best-corrected. |

Applicability Low, and unusually close to the review's target condition: "To be eligible for the
services offered at rehabilitation centers in Quebec, individuals must have a distance VA ⱕ 6/21
(moderate impairment or worse)." (page 4; the PDF's "≤" extracted as "ⱕ"), so the 6/21 analysis
is accuracy for LVR eligibility.

### D4 Flow and timing: risk of bias **High**

| q | Answer | Evidence |
|---|---|---|
| q1 appropriate interval | N | "the long interval (approximately 6 months) before recontacting the subjects" (page 6), in people aged >= 65. |
| q2 all received reference standard | N | "Among the 144 subjects eligible for the second stage of the study, 31 were lost to follow-up and 42 refused to participate. We were unable to schedule an eye examination before the end of the study for six of the remaining 71 subjects. Among the 65 subjects who received the visual examination, 19 had at least one positive response to the questionnaire, and 46 had two negative responses. The final participation rate was 45.1%" (page 3). Partial verification on top of index-test-dependent sampling. |
| q3 same reference standard | Y | One examination protocol for all 65. |
| q4 all included | Y | All 65 examined appear in Table 4, but cell counts are not printed: "Due to the small number of true positives, the precision of the crude sensitivity and of the PPV was very low." (page 4) |

Consequence for synthesis: crude sensitivity/specificity from this design are not estimates for a
screened population. Either reconstruct the 2x2 from the 19/46 split and the reported values and
reweight by the sampling fractions (not reported in enough detail), or keep the study in the
narrative table and out of the pooled estimate, stating why.

---

## What the two examples show

- The modern, large study (Wu) is at High risk in the index-test domain because of data-driven
  item selection, which is invisible if you only look at sample size and AUC.
- The old, small study (Gresset) has a cleaner index test and reference standard, but its flow
  (6-month gap, 45% verification) makes its numbers unusable for pooling.
- Neither is "better"; the point of the table is to carry these differences into the
  sensitivity analyses and the GRADE judgement, with the quotes so the reviewer can check them
  in a minute each.
