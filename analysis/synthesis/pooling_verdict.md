# Pooling verdict (chain step 7, 2026-10-26)

> PROVISIONAL (AI-assisted, advisory). Built from the provisional included set; the reviewer confirms the overlapping-cohort decision (Wu 2026 + Wu 2024 = one dataset) before the Methods state it.

**Verdict: do not pool anywhere.** No instrument x reference-standard x threshold group holds more than one independent accuracy dataset; no instrument x comparator cell in the correlation data holds more than two. The synthesis is per study, without meta-analysis (SWiM).

## 1. Independent datasets

`independent_datasets.py` (merge threshold `probable`): **32 studies -> 31 independent datasets**. Wu 2026 (ID 92) and Wu 2024 (ID 128) were paired at **high** confidence ("cross-ref: Wu 2026 cohort/notes cite ID 128 | authors: 2 shared surname(s) (wu, yueh hsun); Jaccard 1.00 | identical n: 385 | recruitment years overlap: 2019-2024 vs 2019-2022") and share `dataset_id` D22 in `studies_with_datasets.csv`; nothing was set by hand. Stelmack 2002 / 2006 and Smith 2013 / 2020 were flagged "possible" (author overlap only) and left separate: different n (128 vs 285; 10 vs 44), years and designs.

## 2. Diagnostic accuracy (dta.csv): `dta_pool.py validate`, verbatim

Full output: `dta_pool_validate.txt`.

```
rows: 36 usable of 46; distinct study_id: 3; rows with a zero cell: 4
study_ids with >1 row (thresholds/instruments): 3

candidate pooling units (instrument x reference_standard):
  instrument                     reference_standard           rows studies  thresholds
  100-item Visual Acuity Survey  visual acuity                  13       1  answer No = positive, answer No to all t  -> do not pool
  VIRFQ                          composite                       9       1  answer No = positive (reversed item), an  -> do not pool
  Statistics Canada HALS vision  visual acuity                   8       1  at least one positive response versus tw  -> do not pool
  VIRFQ                          visual field                    6       1  answer Yes = positive  -> do not pool

rules: k < 4 -> no bivariate model (per-study + univariate pooling with warnings); k = 4-10 -> bivariate fit but variance components unstable; k >= 10 -> Deeks' test reported.
```

The 10 rows the validator dropped ("non-numeric 2x2 cell") are Labreche 2018 items without counts (3), the five Rowe 2025 CVSQ rows (proportions only), the Wu 2026 whole-survey legal-blindness row and the Pérez-Mañá 2022 cut-off row; they are shown in the accuracy table with approximate (†) CIs but would not enter a model anyway.

`accuracy_table.py` verdict lines, verbatim (one per group):

```
instrument = 100-item Visual Acuity Survey x reference_standard = visual acuity: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
instrument = Cerebral Vision Screening Questionnaire x reference_standard = ophthalmic exam: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
instrument = Cerebral Vision Screening Questionnaire x reference_standard = other: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
instrument = SLVQOL x reference_standard = visual acuity: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
instrument = Statistics Canada HALS vision questions x reference_standard = visual acuity: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
instrument = VIRFQ x reference_standard = composite: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
instrument = VIRFQ x reference_standard = visual field: 1 studies, 1 independent -> 1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity
```

`analysis/extraction/readiness.md` (step 5) reaches the same verdict for every dta row group: "single study: narrative only".

## 3. Correlations and AUCs (effects.csv)

There is no true ROC AUC in `effects.csv` (the Wu "AUC" values are (sens + spec)/2 and sit in `dta.csv`, flagged § in the table). For correlations, `count_effect_groups.py` counted independent datasets per instrument x comparator *class* (a deliberately coarse grouping: all acuity measures together, all field/perimetry measures together, and so on, so that this is the most generous possible count). Output: `effect_groups_count.txt`. The largest cells:

```
2 | LVQOL | contrast sensitivity | ['D02', 'D09']
2 | NEI VFQ-25 | questionnaire / other | ['D11', 'D15']
2 | VA LV VFQ-48 | questionnaire / other | ['D12', 'D14']
2 | VA LV VFQ-48 | reading | ['D14', 'D26']
max independent datasets in any cell = 2
```

Even the two-study cells are not the same comparison (Wolffsohn 2000 correlates the LVQOL with Pelli-Robson contrast; Sahu 2021 correlates it with improvement in high-contrast acuity with a low-vision aid). The effect-size-meta-analysis threshold of three independent studies of one instrument against one comparator is met nowhere, so no correlation was pooled and no `summary.md` from that skill exists.

## 4. What this means for the Results

- Every accuracy estimate is reported per study with its 95% CI (`accuracy_table.md`, `forest_nopool`, `roc_space`).
- Between-study heterogeneity cannot be described within any group; the Results instead describe *within-study* threshold effects (Wu 2026: 0.3 vs 1.0 logMAR; Gresset 2002: 6/12 vs 6/21; Labreche 2018: composite vs field reference) and the *between-group* differences in reference construct.
- Certainty is rated per group without a pooled estimate (`certainty.md`); inconsistency "could not be assessed" everywhere.
- Vote counting is not used: with k = 1 per cell there is nothing to count, and the structured table is available.
