# Screening agreement: Title/abstract decision vs Suggested decision (AI) (title/abstract)

Source: `data/LVR_screening_sheet_2.xlsx`; Lists from data/LVR_screening_sheet_2.xlsx (Lists tab); Maybe treated as **include**.
Records with a decision on both sides: **40** (A only: 0, B only: 95, neither: 0).

## Per-category counts (paired records, before collapsing)

| Decision | Title/abstract decision | Suggested decision (AI) |
|---|---:|---:|
| Include | 4 | 6 |
| Exclude | 27 | 29 |
| Maybe | 9 | 5 |

## Confusion matrix (rows: Title/abstract decision; columns: Suggested decision (AI))

| | Include | Exclude | Total |
|---|---:|---:|---:|
| **Include** | 7 | 6 | 13 |
| **Exclude** | 4 | 23 | 27 |
| **Total** | 11 | 29 | 40 |

## Agreement

| Statistic | Value |
|---|---:|
| Observed agreement | 0.750 (30/40) |
| Expected by chance | 0.579 |
| Cohen's kappa | 0.407 |
| SE (Fleiss-Cohen-Everitt) | 0.155 |
| 95% CI | 0.102 to 0.711 |
| PABAK | 0.500 |
| Prevalence index (Include) | -0.400 |
| Bias index | 0.050 |
| Suggested decision (AI) recall of Title/abstract decision's Include | 0.538 |
| Suggested decision (AI) agreement on Title/abstract decision's Exclude | 0.852 |
| Specific agreement, Include | 0.583 |
| Specific agreement, Exclude | 0.821 |
| Same exclusion reason when both Exclude | 9/23 (0.391) |
| Raw decision differences hidden by collapsing Maybe | 5 |

Kappa bands are rough (Landis and Koch 1977; McHugh 2012) and kappa falls when one category dominates, so read it next to PABAK and the per-category figures; see references/screening-methods.md.

## Disagreements (10)

| ID | Title/abstract decision | reason | Suggested decision (AI) | reason | Title |
|---:|---|---|---|---|---|
| 12 | Exclude | Not about low vision/visual function | Maybe |  | Baseline traits of low vision patients served by private outpatient cl... |
| 16 | Exclude | No questionnaire/screening item | Include |  | Characteristics of Glaucoma Patients Attending a Vision Rehabilitation... |
| 18 | Maybe |  | Exclude | Intervention study only | Clinically Meaningful Rehabilitation Outcomes of Low Vision Patients S... |
| 20 | Maybe |  | Exclude | Review/opinion/editorial | Common Approach to Low Vision: Examination and Rehabilitation of the P... |
| 21 | Exclude | No questionnaire/screening item | Include |  | Community screening for visual impairment in older people. |
| 23 | Exclude | No questionnaire/screening item | Include |  | Concordance between Self-Reported Visual Difficulty and Objective Visu... |
| 29 | Maybe |  | Exclude | No questionnaire/screening item | Development of a battery of functional tests for low vision. |
| 31 | Maybe |  | Exclude | No accuracy/validation data | Different aspects of visual impairment as risk factors for falls and f... |
| 34 | Maybe |  | Exclude | Intervention study only | Economic Evaluation of Low-Vision Rehabilitation for Veterans With Mac... |
| 36 | Maybe |  | Exclude | Intervention study only | Efficacy of MP-3 microperimeter biofeedback fixation training for low ... |

## Unpaired

- Only Suggested decision (AI) decided: IDs 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135

AI decisions are advisory; the reviewer's columns are the decisions of record, and the Methods must say AI assistance was used.
