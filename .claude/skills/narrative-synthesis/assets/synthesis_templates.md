# Text templates for a synthesis without meta-analysis

Every bracket is a value to fill from `analysis/synthesis/` outputs; every sentence is a draft
the reviewer edits. Keep the language consistent with the method: "ranged from", "was", "the
largest study" for narrative groups; "pooled" only for groups that went through
dta-meta-analysis or effect-size-meta-analysis.

## Methods paragraph (SWiM items 1-7)

> **Data synthesis.** Studies were grouped by index instrument or screening question, reference
> standard (measured visual acuity, visual field, a full-length questionnaire, or clinician-judged
> need for low vision rehabilitation) and population, as pre-specified in the protocol [or: groups
> marked * were defined after data extraction]. Papers reporting the same participants were
> identified from author overlap, sample size, recruitment dates and cross-references, confirmed
> by [initials], and counted once; where two reports overlapped we tabulated the [larger / more
> complete] report and present the other beside it. For each 2x2 comparison the standardised
> metric was sensitivity and specificity at the study's stated threshold with 95% Wilson score
> confidence intervals, computed from the 2x2 counts when the paper did not report them; for
> ROC studies the area under the curve with its reported CI; for validation studies the
> correlation coefficient as reported. Meta-analysis was not undertaken because [no group
> contained four or more independent datasets at a common threshold and reference standard /
> thresholds and reference standards differed across the k = [k] studies] (Campbell 2020;
> Cochrane Handbook ch. 12). Results are presented per study in tables and forest plots without
> a pooled estimate, in ROC space, and as an evidence map of independent datasets by instrument
> and reference standard. Heterogeneity was examined narratively against test and reference
> thresholds, reference-standard construct, setting and disease spectrum, administration mode
> and population. [Where estimates could not be compared, direction of effect was summarised by
> vote counting with an exact sign test; statistical significance was not counted.] Certainty
> of evidence was rated per group with GRADE for diagnostic accuracy adapted to the absence of a
> pooled estimate (Murad 2017). Reporting follows SWiM (Supplementary Table S[n]). Analysis
> scripts and first drafts of tables and text were produced with AI assistance (Claude,
> Anthropic); all groupings, judgements and numbers were checked against the source papers by
> the authors, who made every analytic decision.

## Results structure per group (SWiM item 8)

For each group, in this order:

1. **Evidence base.** "[k_ind] independent dataset(s) in [k] report(s) ([n_total] participants)
   evaluated [instrument] against [reference standard] (Table [N], Figure [N]). [Study A and
   Study B analysed the same cohort and are counted once.]"
2. **Finding, led by the strongest study.** "In the largest study at low risk of bias ([Study],
   n = [n], prevalence [p]), sensitivity was [se] (95% CI [lo]-[hi]) and specificity [sp]
   ([lo]-[hi]) at [threshold]. Across the [k_ind] datasets sensitivity ranged from [min] to
   [max] and specificity from [min] to [max]; confidence intervals [overlapped / did not
   overlap for Study X]."
3. **Heterogeneity, by explanation in order.** "The lowest sensitivity ([Study]) used
   [stricter reference threshold / a population sample with prevalence [p] / interviewer
   administration]; the remaining spread is within the width of the individual CIs."
4. **Risk of bias and what it would do.** "[Study] selected the best of 100 items in the same
   sample (QUADAS-2 index test: high), which would inflate both estimates; [Study] verified only
   screen-positives, which would inflate sensitivity."
5. **Certainty.** "Certainty was [low] for sensitivity (downgraded for risk of bias and
   imprecision) and [very low] for specificity (additionally for inconsistency)."
6. **One-sentence bottom line** in the review question's language: "A single question about
   reading a posted menu identifies acuity-defined low vision with sensitivity around [x] in
   enriched research samples; its performance as a stand-alone screen in a glaucoma clinic has
   not been tested."

## "Could not be pooled because" wording

- "Meta-analysis was not possible for [group]: the [k] reports derive from [k_ind] independent
  dataset(s), below the four needed to estimate the between-study variances of the bivariate
  model."
- "The [k] studies used [three] different reference thresholds ([20/40 binocular; worse than 6/12
  better eye; MD < -6 dB]); pooling across them would answer no clinical question, so results
  are presented by threshold."
- "[Study] reported only sensitivity and specificity without counts or group sizes; its CIs are
  approximate (back-calculated from the reported n) and it is shown but not combined."
- "The single-item results of [Study A] and [Study B] come from the same 385 participants; they
  are one dataset and are presented together."
- "Reference standards differed in construct (measured acuity vs clinician-judged need for
  rehabilitation); these are reported as separate groups."

## Vote-counting sentences (direction only; last resort)

- "Effect sizes were not comparable across the [k] studies ([Pearson r, Spearman rho, mean
  difference in logits]); we therefore summarised direction of effect only. [x] of [k]
  independent datasets found an association in the expected direction, [y] found none and [z]
  the opposite (exact sign test p = [p]). This summary ignores the size and precision of each
  effect and should be read with Table [N]."
- Never: "[x] of [k] studies found a statistically significant association."

## Heterogeneity sentences

- "Sensitivity ranged from [min] to [max]; the two lowest values came from studies that defined
  the reference standard as [better-eye acuity worse than 6/12], a stricter criterion than the
  [binocular 20/40 or worse] used by the others."
- "Prevalence of the target condition ranged from [13%] (population sample) to [69%] (research
  cohort recruited to span the acuity range), so positive predictive values are not comparable
  and are not tabulated."
- "With [two] datasets, inconsistency could not be assessed; imprecision is rated instead."

## Certainty sentences (GRADE without a pooled estimate)

- "The certainty of evidence that [instrument] identifies [target condition] with the sensitivity
  shown in Table [N] was [low]: downgraded once for risk of bias ([k] of [k] studies at high
  risk in the index-test domain) and once for imprecision (fewer than 100 reference-positive
  participants in every study). Inconsistency could not be assessed with [k] datasets;
  publication bias could not be assessed."
- "For [instrument] vs [clinician-judged need], certainty was [very low]: one study, enriched
  sample (indirectness), wide confidence intervals (imprecision)."

## Evidence-map and figure captions

- "Figure [N]. Evidence map. Cells show the number of independent datasets (papers sharing
  participants counted once) and the total participants for each instrument x reference
  standard. Empty cells are gaps in the evidence."
- "Figure [N]. Sensitivity and specificity per study with 95% CIs. No pooled estimate is shown;
  rows marked ‡ share participants. Squares scale with sample size."
- "Figure [N]. Harvest plot. Bar height is the effect-size class, colour the QUADAS-2 overall
  judgement; studies are placed by direction of effect relative to the null."

## AI-assistance disclosure (once, in Methods)

> Tables, figures, the overlapping-cohort screen and first drafts of synthesis text were produced
> with AI assistance (Claude, Anthropic). The authors confirmed every grouping of studies,
> checked each number against the source paper, made all judgements of heterogeneity, risk of
> bias and certainty, and edited the text.
