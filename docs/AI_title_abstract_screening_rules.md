# AI title/abstract screening rules

These are the calibrated rules used to produce the AI columns Q–S on the Screening tab of `data/LVR_screening_sheet_2.xlsx`: "Independent T/A decision (AI)", "Independent exclusion reason (AI)" and "Independent rationale (AI)". They apply the criteria in the Instructions tab and `data/LVR_Q_Study_Outline.md`, and add tie-breakers so that every record is judged on the same threshold.

Like columns N–P, these decisions are advisory only. They are not the reviewer's decisions, and the review's methods must report that AI assistance was used.

Decide Include / Exclude / Maybe from the title and abstract only.

## Include (all must hold)

- Adults (18+). Mixed-age samples that are mainly adult, and adult eye/LVR clinics, count.
- The object of study is a **self-report questionnaire or screening item about vision, visual function or LVR need**. The study evaluates the instrument itself in at least one of these ways:
  - accuracy against measured vision (VA, VF, contrast, clinical exam): sensitivity, specificity, AUC, PPV/NPV, agreement;
  - psychometric validation: Rasch, reliability, validity, responsiveness, MCID, or cross-cultural adaptation *with* psychometric testing;
  - a planned comparison of questionnaire scores with measured visual function, done to judge what the questionnaire captures;
  - practical clinical use of the instrument, such as time to administer, feasibility, or use for LVR referral.
- These also count as Include: glaucoma PROM measurement studies; LVR referral guidelines, consensus statements or clinical practice guidelines; systematic reviews that report pooled accuracy or measurement properties of such instruments.

## Exclude: pick exactly ONE reason, spelled exactly as in the Lists tab

- `Wrong population (not adults)`: children only.
- `No questionnaire/screening item`: no self-report vision instrument is involved, for example performance tests, imaging, devices or epidemiology from exams only.
- `No accuracy/validation data`: a self-report vision instrument is used, but only as an exposure, predictor, descriptor or plain outcome, and the instrument itself is not evaluated. Translation/adaptation without psychometric testing also goes here.
- `Intervention study only`: tests a rehab or therapy intervention; questionnaires are only outcomes, with no measurement-property analysis.
- `Not about low vision/visual function`: the self-report or the topic is not about vision (dry eye symptoms, driving skill, general health only, and so on).
- `Review/opinion/editorial`: narrative reviews, opinion pieces, editorials.
- `Conference abstract only`
- `Language (not English/French)`
- `Other (see notes)`: anything else, for example case reports or case series. Say what it is in the rationale.

## Maybe

A relevant self-report vision instrument in an adult VI/LVR/eye-clinic population, but the abstract doesn't make clear whether the instrument is evaluated against vision or has psychometric data. Also use Maybe when there is no abstract ("Missing") and the title is plausibly relevant. Include and Maybe both go on to full-text review.
