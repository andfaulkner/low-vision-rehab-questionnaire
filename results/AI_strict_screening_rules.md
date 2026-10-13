# AI strict screening rules

These rules produce the "Strict decision (AI)" and "Strict rationale (AI)" columns in `results/LVR_strict_screening.csv`. They tighten the independent title/abstract rules in `docs/AI_title_abstract_screening_rules.md`, which is left unchanged, so that the final set falls in the target range of **15–30 included papers**.

Like the other AI columns, these decisions are advisory only. They are not the reviewer's decisions, and the review's methods must report that AI assistance was used.

Each paper is screened by its own subagent. The subagent reads the full text in `data/articles_text/` when it exists, and falls back to the title and abstract when it doesn't. An orchestrating agent collects the results. Screening runs in up to three steps:

1. **Strict screen** of all 127 records.
2. **Stricter screen**, only if more than 30 papers pass step 1, and only of those papers.
3. **Ranking**, only if more than 30 papers still pass step 2. One agent compares all the survivors and keeps the 30 most relevant.

Every paper gets exactly one decision, Include or Exclude. There is no Maybe.

## Review question (PICO)

From `data/LVR_Q_Study_Outline.md`:

- **Population:** adults seen in ophthalmology or glaucoma clinics who are potential LVR candidates.
- **Index test:** brief self-report screening items (for example, two questions about reading a restaurant menu and a keyboard), and the full-length LVR questionnaires they are compared with.
- **Comparator:** measured visual acuity and visual field, full-length LVR questionnaires, or clinician-judged LVR need.
- **Outcome:** sensitivity, specificity, AUC, time to administer, and feasibility in a technician work-up.

## Step 1: strict screen

### Automatic exclusion

**If the study does not use a vision questionnaire of some kind, Exclude it.** No other criteria are checked. A vision questionnaire is any self-report or interviewer-administered set of questions, or any single screening question, about the person's vision, visual function, visual difficulty or LVR need. For example: NEI VFQ-25, VA LV VFQ-48, LVQOL, Activity Inventory, IVI, GQL-15, GAL-9, LVIM, EQ-5D vision bolt-on, or "Can you see well enough to read a newspaper?".

The following do **not** count as a vision questionnaire:

- performance tests, such as acuity charts, perimetry, contrast tests, reading speed or mobility courses;
- imaging, devices or clinical examination;
- general health, depression, frailty or quality-of-life questionnaires with no vision content;
- questionnaires about symptoms that aren't visual function, such as dry eye or headache;
- questionnaires that clinicians or caregivers fill in about services, rather than about the patient's vision.

### Include (all must hold)

1. **Adults.** The participants are adults (18+), or mainly adults.
2. **A vision questionnaire is used** (see above).
3. **The questionnaire itself is the object of evaluation**, in at least one of these ways:
   - **Accuracy:** it is compared with measured vision (VA, VF, contrast or clinical exam) or with clinician-judged LVR need, and the paper reports sensitivity, specificity, AUC, PPV/NPV, kappa or agreement;
   - **Psychometric validation:** Rasch analysis, reliability, construct or criterion validity, responsiveness or MCID, or cross-cultural adaptation **with** psychometric testing;
   - **Planned comparison:** questionnaire scores are formally compared with measured visual function in order to judge what the questionnaire captures. A correlation reported in passing does not count;
   - **Clinical use:** time to administer, or feasibility as a screening or LVR referral tool.
4. **Original data, a guideline, or a systematic review.** Guidelines, consensus statements and systematic reviews count only if they make explicit recommendations about, or pool evidence on, self-report vision questions or questionnaires for screening or LVR referral.

### Exclude (any one is enough)

- No vision questionnaire (the automatic exclusion above).
- Children only.
- The questionnaire is only an outcome, exposure, predictor or descriptor, and its measurement properties are not analysed. This covers intervention trials, prevalence surveys, risk-factor studies and descriptive clinic audits.
- Translation or cultural adaptation without psychometric testing.
- Narrative review, opinion, editorial, case report or case series.
- A guideline or review that only mentions questionnaires in passing.
- Conference abstract without full data.
- Not in English or French. If the full text is in another language and only the abstract is in English, Exclude.

## Step 2: stricter screen (only if step 1 includes more than 30)

Re-screen each step-1 Include. Keep it only if it **directly informs one of the sections of the planned article**:

- **A. Screening accuracy.** It reports the accuracy (sensitivity, specificity, AUC or agreement) of brief self-report vision questions, or of a questionnaire used as a screener, against measured VA/VF or LVR need.
- **B. Full-length LVR questionnaires.** It reports psychometric validation, responsiveness or score-to-measured-vision relationships for a vision-specific questionnaire used in LVR or glaucoma (NEI VFQ-25, VA LV VFQ-48, LVQOL, Activity Inventory, IVI, GQL-15, GAL-9, LVIM and similar), in a low-vision, LVR, glaucoma or eye-clinic population.
- **C. Clinic workflow.** It is a guideline, consensus statement or systematic review that gives recommendations or pooled evidence on using self-report vision questions in screening or LVR referral, or it reports the time or feasibility of giving such questions in a clinic.

Exclude at step 2 if any of these apply:

- The population is mainly outside LVR, glaucoma, eye clinics or older-adult vision screening, for example Parkinson's disease, stroke wards or dementia. The exception is when the paper reports screening accuracy (section A).
- The instrument is not specific to vision. A generic HRQoL tool with no vision items doesn't count, but a vision bolt-on does.
- The evaluation of the questionnaire is a minor, secondary part of the paper.
- The paper adds little to the article that other included papers don't already cover, such as a second analysis of the same cohort and instrument with no new measurement property.

Also give each kept paper a **relevance score from 1 to 5** (5 = central to the article), to be used in step 3.

## Step 3: ranking (only if step 2 still includes more than 30)

One agent sees the step-2 summaries of all survivors and keeps the 30 most relevant. It ranks by section A first, then B, then C, and within each section by relevance score and strength of evidence. Every paper it drops is marked Exclude, with the reason "Lower priority in final ranking" plus a one-line justification.

## Output columns

- **Strict decision (AI):** `Include` or `Exclude`.
- **Strict rationale (AI):** 1–3 sentences that give the step the decision was made at (Step 1, 2 or 3), the instrument (if any), the evidence type, and the specific reason. They also say whether the full text or only the abstract was used.
- **Article link:** for each Include, a link to the article: the DOI link, or for the two records that have no DOI, the PubMed record (65, PMID 12202503) or the NCBI Bookshelf report (93, NBK35192). It is blank for every Exclude.

## Outcome of the run on 13 Oct 2026

- 127 subagents screened one paper each: 113 from the full text and 14 from the title and abstract only. Records 1, 9, 11, 16, 23, 30, 42, 57, 58, 70, 103 and 127 have no text file. For record 48, the text file contains a different paper, and for record 69, it contains only the supplementary tables.
- Step 1 included **29** papers and excluded 98. 31 of the exclusions had no vision questionnaire at all, so they were excluded automatically.
- 29 is inside the 15–30 target range, so steps 2 and 3 were not run.

## Key sources added by hand

Eight of the key sources in `data/LVR_Q_Study_Outline.md` were not found by the PubMed and Scopus searches, so they were not among the 127 records. They were added to the results as records 128–135, below the 29 screened includes, and marked Include **without being screened**. Their "Strict rationale (AI)" says so. They were not added to the screening workbook (`data/LVR_screening_sheet_2.xlsx`), so its Counts tab and PRISMA numbers do not include them.

| ID | Source |
|---|---|
| 128 | Wu et al. 2024, *Estimating Visual Acuity Without a Visual Acuity Chart* (TVST) |
| 129 | Vinokurtseva et al. 2023, *Evaluating Measurement Properties of Patient-Reported Outcome Measures in Glaucoma: A Systematic Review* (Ophthalmol Glaucoma) |
| 130 | Ernst et al. 2025, *Factors Associated with Referral to Low Vision for Patients with Advanced Glaucoma* (Life, vol. 16, 2026) |
| 131 | Swenor et al. 2017, *Impact of the Ability to Divide Attention on Reading Performance in Glaucoma* (IOVS) |
| 132 | HealthLink BC, *Legal blindness* (web page, current as of 12 Oct 2022) |
| 133 | Nguyen et al. 2014, *Reading ability and reading engagement in older adults with glaucoma* (IOVS) |
| 134 | Kaleem et al. 2017, *Referral to Low Vision Services for Glaucoma Patients* (J Glaucoma) |
| 135 | Jackson et al. 2023, *Vision Rehabilitation Preferred Practice Pattern* (Ophthalmology) |

With these, the results list 37 Includes.
