# Screening agreement: Suggested decision (AI) vs Independent T/A decision (AI) (title/abstract)

Source: `data/LVR_screening_sheet_2.xlsx`; Lists from data/LVR_screening_sheet_2.xlsx (Lists tab); Maybe treated as **include**.
Records with a decision on both sides: **127** (A only: 8, B only: 0, neither: 0).

## Per-category counts (paired records, before collapsing)

| Decision | Suggested decision (AI) | Independent T/A decision (AI) |
|---|---:|---:|
| Include | 21 | 30 |
| Exclude | 90 | 84 |
| Maybe | 16 | 13 |

## Confusion matrix (rows: Suggested decision (AI); columns: Independent T/A decision (AI))

| | Include | Exclude | Total |
|---|---:|---:|---:|
| **Include** | 33 | 4 | 37 |
| **Exclude** | 10 | 80 | 90 |
| **Total** | 43 | 84 | 127 |

## Agreement

| Statistic | Value |
|---|---:|
| Observed agreement | 0.890 (113/127) |
| Expected by chance | 0.567 |
| Cohen's kappa | 0.745 |
| SE (Fleiss-Cohen-Everitt) | 0.064 |
| 95% CI | 0.621 to 0.870 |
| PABAK | 0.780 |
| Prevalence index (Include) | -0.370 |
| Bias index | -0.047 |
| Independent T/A decision (AI) recall of Suggested decision (AI)'s Include | 0.892 |
| Independent T/A decision (AI) agreement on Suggested decision (AI)'s Exclude | 0.889 |
| Specific agreement, Include | 0.825 |
| Specific agreement, Exclude | 0.920 |
| Same exclusion reason when both Exclude | 54/80 (0.675) |
| Raw decision differences hidden by collapsing Maybe | 9 |

Kappa bands are rough (Landis and Koch 1977; McHugh 2012) and kappa falls when one category dominates, so read it next to PABAK and the per-category figures; see references/screening-methods.md.

## Disagreements (14)

| ID | Suggested decision (AI) | reason | Independent T/A decision (AI) | reason | Title |
|---:|---|---|---|---|---|
| 16 | Include |  | Exclude | No accuracy/validation data | Characteristics of Glaucoma Patients Attending a Vision Rehabilitation... |
| 37 | Maybe |  | Exclude | No accuracy/validation data | Estimating the prevalence of visual impairment in the Netherlands, wit... |
| 43 | Exclude | No accuracy/validation data | Maybe |  | Exploring vision tests as a surrogate for depression screening in pati... |
| 51 | Exclude | No accuracy/validation data | Maybe |  | Identifying low vision rehabilitation priorities using a conjoint anal... |
| 52 | Exclude | Not about low vision/visual function | Maybe |  | Impact of Visual Impairment on Vision-Related Quality of Life in Parki... |
| 56 | Exclude | Intervention study only | Maybe |  | Is the high contrast visual acuity chart a good predictor of improveme... |
| 67 | Maybe |  | Exclude | Review/opinion/editorial | Measuring reading performance. |
| 76 | Exclude | No accuracy/validation data | Maybe |  | Predicting perceived quality of life scores from the National Eye Inst... |
| 85 | Exclude | No accuracy/validation data | Maybe |  | Refinement of the Low Vision Independence Measure: A Qualitative Study |
| 88 | Exclude | Intervention study only | Maybe |  | Responsiveness of the EQ‐5D to the Effects of Low Vision Rehabilitation |
| 95 | Exclude | No accuracy/validation data | Include |  | Self-reported importance and difficulty of driving in a low-vision cli... |
| 97 | Exclude | No accuracy/validation data | Include |  | Spatial localization in visual impairment. |
| 114 | Exclude | Other (see notes) | Include |  | Translation and Testing Psychometric Properties of the Thai Version of... |
| 117 | Maybe |  | Exclude | Not about low vision/visual function | Utilizing visual symptoms to distinguish dry eye from glaucoma, catara... |

## Unpaired

- Only Suggested decision (AI) decided: IDs 128, 129, 130, 131, 132, 133, 134, 135

AI decisions are advisory; the reviewer's columns are the decisions of record, and the Methods must say AI assistance was used.
