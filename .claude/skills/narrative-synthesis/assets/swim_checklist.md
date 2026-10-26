# SWiM checklist (Campbell et al. 2020, BMJ 368:l6890)

Nine items for reporting a synthesis without meta-analysis. Fill the "Where reported" column
with the manuscript section and page (or "not applicable, because ..."). Items 1 to 7 belong
in the Methods, 8 in the Results, 9 in the Discussion. Submit the filled table as a
supplement; PRISMA 2020 item 13 (synthesis methods) points to it.

| # | Item | What to state | Where reported |
|---|---|---|---|
| 1a | Grouping studies for synthesis | How studies were grouped (instrument/question x reference standard x population) and whether this was pre-specified in the protocol | |
| 1b | | How papers sharing participants were identified and handled (independent_datasets.py signals, reviewer confirmation, which report was used) | |
| 2 | Standardised metric and transformation | The metric per group (sens/spec with 95% Wilson CI at a stated threshold; AUC with CI; Pearson r), how CIs were computed when not reported, and what was NOT converted (no sens/spec from correlations, no (sens+spec)/2 as AUC) | |
| 3 | Synthesis methods | Structured tabulation and visual display per group; narrative comparison; direction-only vote counting only where estimates were not comparable, with the sign test; why meta-analysis was not used (independent datasets < 4 per threshold; mixed thresholds/reference standards) | |
| 4 | Criteria used to prioritise results | Which result is reported when a study gives several (pre-specified threshold nearest the review's cut-off; whole-sample per-person rows; the larger/more complete report of an overlapping pair; the validated rather than derivation sample) | |
| 5 | Investigation of heterogeneity | The characteristics examined narratively: test and reference thresholds, reference-standard construct, setting/spectrum (prevalence), administration mode, population; and that I² was not computed | |
| 6 | Certainty of evidence | GRADE for test accuracy applied to each group without a pooled estimate (Murad 2017): the five domains, starting level, how inconsistency and publication bias were handled with k <= 3 | |
| 7 | Data presentation methods | Per-study accuracy table; forest plot without pooling; ROC-space scatter; evidence map; harvest/effect-direction plot for non-2x2 outcomes; what each conveys | |
| 8 | Reporting results | For each group: the synthesised finding in language matching the method ("ranged from", "the largest low-risk study found"), the contributing studies by name, the independent datasets count, and the certainty rating | |
| 9 | Limitations of the synthesis | Overlapping cohorts; small k; mixed thresholds; reliance on VA-defined reference standards; vote counting where used; AI assistance and how outputs were checked | |

Source: Campbell M, McKenzie JE, Sowden A, et al. Synthesis without meta-analysis (SWiM) in
systematic reviews: reporting guideline. BMJ 2020;368:l6890. The explanation and elaboration
for each item is in that paper's supplementary file; `references/swim.md` summarises it for
this review.
