# Grouping of studies for synthesis (SWiM item 1)

> PROVISIONAL (AI chain step 7, advisory). Built from the provisional included set of 31 records plus ID 128 (`analysis/screening/provisional_included.csv`; reviewer has decided 40/135 at title/abstract and 0 at full text). The reviewer confirms every group and every overlapping-cohort decision before the Methods state them.

Written before any accuracy or correlation value was tabulated, as SWiM item 1 asks. The unit of grouping is question or instrument x reference standard x population; within a group, a different threshold is a different test and is shown on its own row. The unit of counting is the independent dataset, not the paper (`independent_datasets.md`).

## 1. Pre-specified groups (from the narrative-synthesis skill and the protocol)

| # | Group | Definition | Pre-specified? | Studies that landed here (ID) | Independent datasets |
|---|---|---|---|---|---|
| G1 | Single screening item vs measured visual acuity | One yes/no (or short-scale) self-report item against VA at a stated logMAR / Snellen threshold | yes | Wu 2026 (92) with Wu 2024 (128) as the same cohort; Gresset 2002 (79, two HALS questions); Labreche 2018 (27, VIRFQ items 1, 2, 4, 5, 6 vs a composite that is mostly acuity/contrast) | 3 (D22, D16, D03) but no two share an item, threshold or reference definition |
| G2 | Single screening item vs visual field | One item against perimetry or confrontation fields | yes | Labreche 2018 (27, VIRFQ items 3, 4, 7 vs "peripheral field defect") | 1 (D03) |
| G3 | Full-length questionnaire vs VA or VF (accuracy or correlation) | Total or domain score of a multi-item instrument against measured VA, contrast or field | yes | Accuracy: Pérez-Mañá 2022 (119, SLVQOL cut-off vs VI group membership); Wu 2026 (92, whole 100-item survey). Correlation: Wolffsohn 2000 (26), Gothwal 2012 (5), Tabrett 2011 (46), Massof 2007 (95), Subramanian 2006 (97), La Grow 2007 (76), Murro 2017 (84), Di Maggio 2020 (105), Sumi 2003 (110), Bibby 2007 (120), Wu 2016 (63), Agathos 2025 (55), Wu 2024 (128) | accuracy 2 (D30, D22); correlations 13, but every instrument x comparator cell is k = 1 |
| G4 | Any instrument vs clinician-judged LVR need or referral | Index test against a clinician decision to refer or a documented LVR need | yes | Agathos 2025 (55): GAL-9 total vs referral to O&M / physiotherapy (regression only). Gresset 2002 (79): service use among screen-positives (descriptive). Nothing with sensitivity / specificity. | 0 accuracy datasets; 1 association (D08) |
| G5 | Questionnaire vs questionnaire (criterion / convergent validity, not accuracy) | Two self-report instruments compared | yes | Pérez-Mañá 2022 (119, SLVQOL vs NEI VFQ-25 and EQ-5D-5L); Malkin 2013 (88, EQ-5D vs Activity Inventory); Surawatsatien 2026 (114, EQ-5D bolt-on vs EQ-5D / EQ-VAS); La Grow 2007 (76, NEI VFQ-25 vs single-item QoL); Selivanova 2019 (72, IVI vs NEI VFQ-25 responsiveness) | 5, no two share a pair of instruments |

## 2. Groups that emerged from the data (marked * in the Methods)

| # | Group | Why it was added | Studies |
|---|---|---|---|
| G6* | Symptom questionnaire vs specialist eye examination in stroke | Rowe 2025 (38) tabulates the Cerebral Vision Screening Questionnaire against a specialist visual assessment; the reference is neither VA nor VF but "any post-stroke visual impairment", so it fits none of G1 to G4 | Rowe 2025 (38), a guideline that re-tabulates one primary study (n = 461) |
| G7* | Measurement properties of full-length instruments (COSMIN path) | Not an accuracy group: structural validity, internal consistency, reliability, measurement error, hypotheses testing and responsiveness of the instruments the review contrasts with the two-item screen | IDs 5, 26, 39, 46, 65, 66, 72, 74, 86, 88, 89, 105, 110, 114, 119 (see `analysis/instruments/`) |
| (none) | Single item vs VF in glaucoma | Expected from the protocol; no study found. Recorded as an empty cell of the evidence map | - |

## 3. Decisions recorded here so the Methods can state them

1. **Overlapping cohort.** Wu 2026 (ID 92) and Wu 2024 (ID 128) analyse the same 385 adults (Wu 2026 p2 cites the 2024 cohort; identical n; same authors). They are one dataset (D22). Wu 2026 is the main-table report because it carries the accuracy results; Wu 2024 contributes only the IRT correlation and is shown beside it marked ‡. Stelmack 2002 / 2006 and Smith 2013 / 2020 were flagged "possible" on author overlap only; they are different samples by n, year and design and stay separate.
2. **Which row is primary when a study gives several.** Whole-sample, per-person rows (`--filter unit=person --filter subgroup=`); the Labreche 2018 TICS-M > 21 subgroup and the Gresset 2002 weighted rows are shown only in the supplement. For Wu 2026 the primary rows are the two named items (Q97 at 0.3 logMAR, Q30 at 1.0 logMAR); the other top items, pairs and triplets stay in the table as secondary rows.
3. **Reference-standard constructs are not merged.** VA-only (Wu, Gresset, Pérez-Mañá), composite acuity/contrast/field chart review (Labreche), field only (Labreche items 3, 4, 7) and specialist examination (Rowe) are reported as separate groups even where the index test is a single item.
4. **Metric per group** (SWiM item 2): sensitivity and specificity with 95% Wilson CIs at the study's threshold for G1, G2, G3-accuracy and G6; AUC only where a true ROC area was reported (none: Wu's single-threshold "AUC" is flagged §); Pearson or Spearman r as reported, kept apart, for G3-correlation, G4 and G5. Correlations are never converted to accuracy and PPV/NPV are not compared across settings.
5. **Population.** All groups are adults with mixed causes of low vision unless a study is glaucoma-only (Sumi 2003, ID 110, is the only glaucoma-only sample with perimetry). Glaucoma is a planned subgroup; it could not be formed for accuracy because no accuracy study reports glaucoma separately (Wu 2026: 16.9% glaucoma, no subgroup result).
