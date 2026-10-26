# SWiM: the nine items, and how this review meets them

SWiM (Synthesis Without Meta-analysis) is a reporting guideline, not a method: it tells a
review what to state when studies are synthesised by any approach other than
meta-analysis, so that readers can judge whether the grouping, the metric, the summary and
the certainty claims are sound. It was developed because reviews that "narratively
synthesised" rarely said how, and because the Cochrane Handbook ch. 12 methods (summary
statistics of effect estimates, combining P values, direction-only vote counting) are easy
to misuse. Source: Campbell M, McKenzie JE, Sowden A, et al. BMJ 2020;368:l6890, with an
explanation-and-elaboration supplement. Items 1-7 belong in Methods, 8 in Results, 9 in
Discussion. The checklist table to fill is `assets/swim_checklist.md`.

## Item 1. Grouping studies for synthesis

1a: describe how studies were grouped and whether this was pre-specified. 1b: describe
and justify any changes made after seeing the data. For an accuracy review the grouping is
the question answered: index test (single screening item; full-length instrument; which
one) x reference standard (VA; VF; full questionnaire; clinician-judged need) x
population. Within instruments, thresholds are a second level: a different threshold is a
different test. Overlapping cohorts belong here too: SWiM expects the unit of analysis to
be the independent dataset, so say how overlap was detected (`independent_datasets.py`
signals: cross-references, cohort name, author overlap, identical n, dates, site), who
confirmed it, and which report was used.

## Item 2. Standardised metric and transformation methods

State the metric used for comparison in each group and any transformations. Here:
sensitivity and specificity with Wilson 95% CIs at the study's threshold (computed from 2x2
counts when not reported, back-calculated and marked approximate when only proportions and
group sizes exist); AUC with the reported CI (only true ROC areas; a single-threshold
(sens+spec)/2 is flagged and not treated as an AUC); correlation coefficients as reported
(Pearson and Spearman kept apart). Say what was not converted: correlations are not turned
into accuracy, PPV/NPV are not tabulated across settings with different prevalence.

## Item 3. Synthesis methods

Name the method per group and justify it: structured tabulation and visual display with
narrative comparison (the default here); summary statistics of effect estimates (range,
median) where there are enough studies; direction-only vote counting with a sign test only
where estimates are not comparable; and the reason meta-analysis was not done (independent
datasets < 4 per threshold; mixed thresholds or reference-standard constructs; one study
per group). Vote counting by statistical significance is not an acceptable method.

## Item 4. Criteria used to prioritise results for summary and synthesis

When a study reports several results (thresholds, subgroups, eyes vs persons, derivation vs
validation samples, two reports of one cohort), state the rule that picked one for the
main table: the threshold nearest the review's pre-specified cut-off; whole-sample
per-person results; the validation rather than derivation sample; the larger or more
complete report of an overlapping pair. Show the rest in the supplement.

## Item 5. Investigation of heterogeneity in reported effects

State which study characteristics were examined as explanations of variation and how.
For accuracy data the ordered list is: test threshold; reference threshold (which eye,
correction, direction of inequality); reference-standard construct; setting and spectrum
(prevalence as the marker); administration mode and context (stand-alone vs inside a long
survey); population (diagnosis mix, age). Narrative examination means comparing estimates
and CI overlap across those characteristics in the table and ROC plot, not computing I².

## Item 6. Certainty of evidence

Describe the methods used to assess certainty. GRADE for diagnostic accuracy can be applied
to a group without a pooled estimate (Murad 2017; GRADE guidelines 21): rate risk of bias,
indirectness, inconsistency, imprecision and publication bias on the body of evidence,
starting at high for cross-sectional accuracy designs. With k <= 2, inconsistency "could not
be assessed"; publication bias "could not be assessed" below ~10 studies. Say that the
rating refers to the range of estimates shown, not to a pooled value.

## Item 7. Data presentation methods

Describe the tables and figures and what each conveys: per-study accuracy table (the
primary display); forest plot without pooling (precision and overlap at a glance); ROC-space
scatter (threshold effects and spread); evidence map (where evidence exists and where it does
not); harvest or effect-direction plot (direction, rough size and risk of bias for outcomes on
unlike scales). Every figure that omits a pooled estimate should say so in its caption.

## Item 8. Reporting results

For each group: the synthesised finding, the certainty, and the contributing studies by
name, in language that matches the method. "Sensitivity ranged from 0.70 to 0.89 across five
independent datasets" is a narrative finding; "pooled sensitivity was 0.82" is not available
and must not appear. Name the independent datasets count, not the number of papers, when
describing the weight of evidence; state when the only low-risk study disagrees.

## Item 9. Limitations of the synthesis

Report the limitations that follow from the methods: dependence on one research group's
cohort; small k; thresholds that could not be harmonised; VA-defined reference standards
that miss field loss; vote counting where used; the approximate CIs; and that AI assistance
drafted tables and text, with the checks the authors applied.

## Where SWiM sits with the other guidelines

PRISMA 2020 item 13 (synthesis methods) and PRISMA-DTA items 13-14 and 20-21 are satisfied
by pointing at the SWiM items; SWiM does not replace PRISMA. The Cochrane Handbook ch. 12
(McKenzie & Brennan) is the methods source SWiM refers to; its Table 12.2.a lists the
acceptable summary methods and their limitations, and its guidance on the effect-direction
plot was refined by Boon & Thomson 2021. Full citations: `references/methods.md`.
