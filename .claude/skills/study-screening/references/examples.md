# Worked examples: three records at title/abstract

Each example is what a subagent given the Stage 1 brief should return, and
why. The abstracts are from the Screening tab (shortened here). The reviewer's
decision in H is shown afterwards for the one record where it differed from
the AI: that difference is a calibration item for the disagreement list, not a
mistake on either side.

## Record 23: Potter et al. 2024, Ophthalmology

*Concordance between Self-Reported Visual Difficulty and Objective Visual
Impairment: The National Health and Aging Trends Study.*

Abstract (extract): "To examine the performance of self-reported visual
difficulty (VD) in predicting objective visual impairment (VI) in older
adults ... Participants reporting blindness or difficulties with distance or
near vision were characterized as having VD. Presenting binocular distance
visual acuity (VA), near VA, and contrast sensitivity (CS) were assessed ...
Receiver operating characteristic analysis was used to compare performance of
VD in predicting VI ... Visual difficulty achieved an area under the curve
(AUC) of 56.0 (95% CI 55.2-56.9) in predicting VI, with a sensitivity of 15.8
(14.2-17.5) and specificity of 96.3 (95.5-96.9)."

Walk through the rules: older adults (NHATS). A self-report screening item
(the NHATS vision-difficulty questions) is the object of study, evaluated for
accuracy against measured VA and CS with AUC, sensitivity and specificity.
Every Include condition holds, and the record is exactly the kind of brief
self-report screen the review compares the two index questions with.

```
23,Include,,NHATS self-reported visual difficulty vs measured VA/CS in 4999 older adults; AUC 0.56, sens 15.8%, spec 96.3%
```

The reviewer's H for this record is `Exclude` with `No questionnaire/screening
item`. Both AI passes said Include. This is the most useful kind of
disagreement: either the reviewer reads "self-reported difficulty" (a survey
item, not a named questionnaire) as outside the criterion, in which case the
rules file should say so and the two index questions need the same treatment,
or it was a slip. It goes on the calibration list; nobody edits H.

## Record 36: Qian et al. 2022, BMC Ophthalmology

*Efficacy of MP-3 microperimeter biofeedback fixation training for low vision
rehabilitation in patients with maculopathy.*

Abstract (extract): "To evaluate the efficacy of MP-3 microperimeter
biofeedback fixation training (MBFT) in vision rehabilitation of low-vision
patients ... Seventeen eyes of 17 patients were included in this prospective,
interventional study ... Best corrected visual acuity, reading speed, mean
central sensitivity, ... and the 25-item National Eye Institute visual
function questionnaire (NEI-VFQ-25) were recorded pre- and post-training."

Walk through the rules: adults with maculopathy, fine. A vision questionnaire
is present (NEI VFQ-25), so `No questionnaire/screening item` is wrong. But
the questionnaire is only a pre/post outcome of a training intervention; its
accuracy or measurement properties are not analysed. Two reasons could fit,
`Intervention study only` and `No accuracy/validation data`; the rules file
assigns intervention trials where questionnaires are only outcomes to
`Intervention study only`, so that is the one reason.

```
36,Exclude,Intervention study only,Microperimeter biofeedback training in 17 maculopathy patients; NEI VFQ-25 is a pre/post outcome only
```

Reviewer's H: `Maybe`. Both AI passes: Exclude, Intervention study only. At
full text the question is whether the paper reports anything about the VFQ-25
itself (responsiveness, say); the AI rationale tells the reviewer what to look
for.

## Record 12: Goldstein et al. 2012, Archives of Ophthalmology

*Baseline traits of low vision patients served by private outpatient clinical
centers in the United States.*

Abstract (extract): "To characterize the traits of low vision patients who
seek outpatient low vision rehabilitation (LVR) services ... we enrolled 764
new low vision patients ... multiple questionnaires assessing daily living and
vision, physical, psychological, and cognitive health states were administered
by telephone. Baseline clinical visual impairment measures and disorder
diagnoses were recorded ... The VA correlated well with contrast sensitivity
(r = -0.52) but poorly with self-reported vision quality."

Walk through the rules: adults in LVR clinics; self-report vision
questionnaires were administered; measured VA was recorded; and there is a
comparison of VA with "self-reported vision quality". But the purpose is a
descriptive cohort baseline, the questionnaires are not named, and the
comparison reads as reported in passing rather than as a planned evaluation of
what the questionnaire captures. The abstract does not settle whether an
instrument is evaluated, in an adult LVR population with a relevant instrument:
that is the definition of Maybe.

```
12,Maybe,,LVROS baseline cohort of 764 LVR patients; vision questionnaires given and VA correlated poorly with self-reported vision quality, but no instrument is clearly evaluated
```

Reviewer's H: `Exclude`, `Not about low vision/visual function`. Both AI
passes: Maybe. Collapsed with Maybe as Include this is a disagreement; the
reason string the reviewer chose also looks like a slip (the paper is about
low vision patients), which is the kind of thing the disagreement list
surfaces and the reviewer, not the AI, corrects.

## What the three have in common

- The rationale names the instrument (or says none is named), the population
  and what is or is not evaluated, so the reviewer can check it against the
  abstract without re-reading.
- Exactly one reason, spelled from the list; Include and Maybe carry none.
- Maybe is used once, for genuine uncertainty about evaluation, not as a soft
  Exclude for a weak paper or a soft Include for a relevant topic.
