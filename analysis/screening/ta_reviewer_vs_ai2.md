# Screening agreement: Title/abstract decision vs Independent T/A decision (AI) (title/abstract)

Source: `data/LVR_screening_sheet_2.xlsx`; Lists from data/LVR_screening_sheet_2.xlsx (Lists tab); Maybe treated as **separate**.
Records with a decision on both sides: **40** (A only: 0, B only: 87, neither: 8).

## Per-category counts (paired records, before collapsing)

| Decision | Title/abstract decision | Independent T/A decision (AI) |
|---|---:|---:|
| Include | 4 | 7 |
| Exclude | 27 | 31 |
| Maybe | 9 | 2 |

## Confusion matrix (rows: Title/abstract decision; columns: Independent T/A decision (AI))

| | Include | Exclude | Maybe | Total |
|---|---:|---:|---:|---:|
| **Include** | 3 | 1 | 0 | 4 |
| **Exclude** | 1 | 24 | 2 | 27 |
| **Maybe** | 3 | 6 | 0 | 9 |
| **Total** | 7 | 31 | 2 | 40 |

## Agreement

| Statistic | Value |
|---|---:|
| Observed agreement | 0.675 (27/40) |
| Expected by chance | 0.552 |
| Cohen's kappa | 0.275 |
| SE (Fleiss-Cohen-Everitt) | 0.123 |
| 95% CI | 0.033 to 0.516 |
| PABAK | 0.512 |
| Specific agreement, Include | 0.545 |
| Specific agreement, Exclude | 0.828 |
| Specific agreement, Maybe | 0.000 |
| Same exclusion reason when both Exclude | 11/24 (0.458) |

Kappa bands are rough (Landis and Koch 1977; McHugh 2012) and kappa falls when one category dominates, so read it next to PABAK and the per-category figures; see references/screening-methods.md.

## Disagreements (13)

| ID | Title/abstract decision | reason | Independent T/A decision (AI) | reason | Title |
|---:|---|---|---|---|---|
| 12 | Exclude | Not about low vision/visual function | Maybe |  | Baseline traits of low vision patients served by private outpatient cl... |
| 18 | Maybe |  | Exclude | Intervention study only | Clinically Meaningful Rehabilitation Outcomes of Low Vision Patients S... |
| 20 | Maybe |  | Exclude | Review/opinion/editorial | Common Approach to Low Vision: Examination and Rehabilitation of the P... |
| 21 | Exclude | No questionnaire/screening item | Maybe |  | Community screening for visual impairment in older people. |
| 23 | Exclude | No questionnaire/screening item | Include |  | Concordance between Self-Reported Visual Difficulty and Objective Visu... |
| 27 | Maybe |  | Include |  | Development and validation of Visual Impairment as a Risk for Falls Qu... |
| 29 | Maybe |  | Exclude | No questionnaire/screening item | Development of a battery of functional tests for low vision. |
| 30 | Maybe |  | Include |  | Development of a screening tool for reduced vision among inpatients of... |
| 31 | Maybe |  | Exclude | No accuracy/validation data | Different aspects of visual impairment as risk factors for falls and f... |
| 34 | Maybe |  | Exclude | Intervention study only | Economic Evaluation of Low-Vision Rehabilitation for Veterans With Mac... |
| 36 | Maybe |  | Exclude | Intervention study only | Efficacy of MP-3 microperimeter biofeedback fixation training for low ... |
| 37 | Include |  | Exclude | No accuracy/validation data | Estimating the prevalence of visual impairment in the Netherlands, wit... |
| 39 | Maybe |  | Include |  | Evaluating psychometric properties of a clinical and a self-report bli... |

## Unpaired

- Only Independent T/A decision (AI) decided: IDs 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127

AI decisions are advisory; the reviewer's columns are the decisions of record, and the Methods must say AI assistance was used.
