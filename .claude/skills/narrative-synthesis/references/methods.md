# Methods behind the narrative-synthesis scripts, with citations

## 1. Why synthesis without meta-analysis here

The bivariate random-effects model for sensitivity and specificity estimates five
parameters (two means, two between-study variances, a correlation); below four
independent studies the variance components are not identifiable and the prediction
region is meaningless (see dta-meta-analysis `references/methods.md`, Takwoingi 2017).
Papers that re-analyse one cohort are one study for this purpose. Where the primary
question rests on one research group's cohort reported twice (TVST 2024; Wu 2026 IOVS),
the honest synthesis presents that dataset's estimates with CIs and compares other
instruments by structured tabulation. The Cochrane Handbook ch. 12 lists the acceptable
alternatives and warns that "narrative synthesis" without a stated method is not one of
them; SWiM makes the method reportable.

## 2. Independent datasets (`independent_datasets.py`)

Signals and their rationale:

| Signal | Confidence alone | Why |
|---|---|---|
| Cross-reference in `cohort`/`notes` ("same 385 participants as ID 128") | high | the extractor already read it in the paper |
| Same cohort/registry name in `cohort` | high | explicit |
| Author surname overlap (Jaccard >= 0.5 or >= 3 shared surnames) | possible | same group, may be a new sample |
| Author overlap + identical n, overlapping recruitment years, or same country and setting | probable | same group and same sample characteristics |
| Identical n + same country | possible | coincidence is common for small n |

Surnames are parsed from the Screening export's `Authors` column ("Wu YH, Yu D" and
"Wu, Y. H.; Yu, D." forms) or an `authors` column in studies.csv. Pairs at or above
`--merge` are joined with union-find, so A~B and B~C put A, B, C in one dataset even if A
and C were not flagged. The reviewer confirms every grouping: the signals are heuristics,
and the cost of a wrong merge (losing a genuine study) and of a missed one (double
counting) are both real. A filled `dataset_id` column overrides the heuristics on re-runs.

## 3. Per-study accuracy (`accuracy_table.py`)

- Sensitivity = TP / (TP + FN), specificity = TN / (TN + FP) when cells exist; otherwise
  the reported values.
- 95% CI: Wilson score interval (Newcombe 1998, method 3), imported from data-extraction's
  `reconstruct_2x2.py` so both skills give the same numbers; the fallback copy is the same
  formula. For x successes in n with z = 1.96: centre = (p + z²/2n) / (1 + z²/n), half-width
  = z sqrt(p(1-p)/n + z²/4n²) / (1 + z²/n). Wilson is preferred over Wald because it keeps
  the interval inside [0, 1] and has near-nominal coverage at small n and extreme p, both
  common for sensitivity in small accuracy studies.
- When only a proportion and its denominator are known the count is back-calculated as
  round(p x n) and the CI marked approximate (†): the rounding of the reported proportion
  can move the count by one or two.
- "AUC" equal to (sens + spec) / 2 at a single threshold is flagged (§): it is the balanced
  accuracy of one operating point, not an area under a curve, and must not be compared with
  ROC areas from other studies.
- Grouping verdicts: >= 4 independent datasets at one threshold and reference definition ->
  candidate for dta-meta-analysis (its `validate` command decides); 2-3 -> describe with
  range; 1 -> present as-is.
- QUADAS-2 overall per study: High if any domain High, else Unclear if any Unclear (or a
  domain missing), else Low: the same rule as risk-of-bias/`rob_plots.py`.

Forest plot without pooling: Cochrane DTA Handbook ch. 10 recommends paired forest plots
of sensitivity and specificity as the primary display of per-study results, with or
without a summary; omitting the diamond and saying so in the caption is the convention
when no pooled estimate exists. ROC-space scatter: the same chapter's "summary ROC plot
without a curve"; points sized by n so precision is visible without CIs.

## 4. Evidence map (`evidence_map.py`)

An evidence (gap) map tabulates the amount of evidence per cell of a question matrix.
Here: rows = instrument, columns = reference standard (dta.csv) or comparator
(effects.csv); cell = number of independent datasets and participants summed once per
dataset (the largest n a dataset contributes to that cell). Shading is sequential on k with
the numbers written in every cell, so colour is never the only cue. It supports SWiM item 7
and the Discussion of gaps (no study of the single item against clinician-judged need, for
example). Miake-Lye IM, Hempel S, Shanman R, Shekelle PG. What is an evidence map? Syst Rev
2016;5:28 describes the form.

## 5. Harvest plot and effect-direction plot

- Harvest plot (Ogilvie et al. 2008; extended by Crowther et al. 2011): for each outcome,
  studies are placed in columns by direction of effect (negative / null / positive), each as
  a bar whose height encodes quality (here the effect-size class) and whose colour encodes a
  second attribute (here QUADAS-2 overall; hatching repeats the encoding for print and
  colour-vision deficiency). Use it when outcomes are reported on different scales so that
  only direction and rough magnitude are comparable, and when risk of bias must be visible
  alongside them.
- Effect-direction plot (Thomson & Thomas 2013; Boon & Thomson 2021): a table of arrows per
  study x outcome (▲ expected direction, ▼ opposite, ◄► null/unclear), with arrow size for
  sample size in the original. Boon & Thomson 2021 revised the rules to follow the Handbook:
  direction is defined from the point estimate relative to the null (not from statistical
  significance), with a stated rule for "no effect"; here: CI excludes the null, or without a
  CI the estimate is beyond the trivial band (|r| >= 0.1, AUC >= 0.7, |d| >= 0.2, OR >= 1.5).
  `effect_direction.md` is that table.
- Size classes: Cohen 1988 for r (0.1 / 0.3 / 0.5) and d (0.2 / 0.5 / 0.8); AUC bands 0.7 /
  0.8 / 0.9 from Hosmer, Lemeshow & Sturdivant 2013 (acceptable / excellent / outstanding),
  labelled small / moderate / large here; odds ratios 1.5 / 2.5 / 4 (Chen, Cohen & Chen
  2010). These are conventions, not thresholds of clinical importance; say so.

## 6. Vote counting on direction, and why significance counting is wrong

The Handbook (ch. 12, Table 12.2.a) accepts vote counting based on direction of effect as a
method of last resort, when effect estimates cannot be extracted or standardised. Each
independent dataset contributes one vote: expected direction, opposite, or null; the
question "is the proportion in the expected direction different from 0.5?" can be tested with
an exact binomial sign test on the directional votes (null votes excluded, which the text
must say). Limitations the Handbook requires reporting: no information on magnitude or
precision; small studies count as much as large ones; a result near the null in a huge study
is a "vote". Counting statistically significant results instead is rejected because the
power of each study, not the size of the effect, determines its vote: Hedges & Olkin (1980)
showed the procedure's power can fall toward zero as the number of small studies grows, and
that a set of studies with the same true effect can produce almost any count. Bushman & Wang
(2009) review the corrected procedures that remain usable.

## 7. Heterogeneity without I²

With narrative groups, heterogeneity is described, not estimated: ranges, overlap of CIs,
and the characteristics that line up with the spread, in the order threshold -> reference
construct -> spectrum -> administration -> population (the order in which DTA reviews find
explanations; Cochrane DTA Handbook ch. 10 and 11). I² is not computed for narrative groups
because in accuracy data it mixes threshold effects with true heterogeneity and is inflated
by large within-study precision (see dta-meta-analysis SKILL.md, Heterogeneity).

## 8. Certainty without a pooled estimate

Murad et al. 2017 set out how GRADE applies when there is no single estimate: rate the body of
evidence per outcome on the usual domains, using the range of estimates and overlap of CIs
for inconsistency and the CI widths and event counts for imprecision, and state that the
rating refers to the direction/range described rather than to a pooled magnitude. GRADE for
diagnostic accuracy (Schünemann 2008; GRADE guidelines 21, 2020) supplies the DTA-specific
considerations; the prisma-reporting skill's `references/grade_dta.md` has the per-domain
rules and the per-1000 framing, and its "When a SoF table is not appropriate" section covers
exactly the no-pooled-row case.

## 9. Figures, determinism and accessibility

Figures use the same palette as the sibling skills (dataviz reference palette for series;
Okabe-Ito green/amber/vermillion for Low/Unclear/High risk of bias, as in risk-of-bias),
encode category with marker shape and hatch as well as colour, label every point and cell
with text, and are written with a fixed SVG hash salt and no timestamp metadata so that
re-running on the same inputs produces byte-identical files.

## References

- Campbell M, McKenzie JE, Sowden A, Katikireddi SV, Brennan SE, Ellis S, Hartmann-Boyce J, Ryan R, Shepperd S, Thomas J, Welch V, Thomson H. Synthesis without meta-analysis (SWiM) in systematic reviews: reporting guideline. BMJ 2020;368:l6890.
- McKenzie JE, Brennan SE. Chapter 12: Synthesizing and presenting findings using other methods. In: Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA (eds). Cochrane Handbook for Systematic Reviews of Interventions, version 6.4 (2023). Cochrane. www.training.cochrane.org/handbook
- Boon MH, Thomson H. The effect direction plot revisited: application of the 2019 Cochrane Handbook guidance on alternative synthesis methods. Res Synth Methods 2021;12(1):29-33.
- Thomson HJ, Thomas S. The effect direction plot: visual display of non-standardised effects across multiple outcome domains. Res Synth Methods 2013;4(1):95-101.
- Crowther M, Avenell A, MacLennan G, Mowatt G. A further use for the Harvest plot: a novel method for the presentation of data synthesis. Res Synth Methods 2011;2(2):79-83.
- Ogilvie D, Fayter D, Petticrew M, Sowden A, Thomas S, Whitehead M, Worthy G. The harvest plot: a method for synthesising evidence about the differential effects of interventions. BMC Med Res Methodol 2008;8:8.
- Hedges LV, Olkin I. Vote-counting methods in research synthesis. Psychol Bull 1980;88(2):359-369.
- Bushman BJ, Wang MC. Vote-counting procedures in meta-analysis. In: Cooper H, Hedges LV, Valentine JC (eds). The Handbook of Research Synthesis and Meta-Analysis, 2nd ed. Russell Sage Foundation, 2009.
- Murad MH, Mustafa RA, Schünemann HJ, Sultan S, Santesso N. Rating the certainty in evidence in the absence of a single estimate of effect. Evid Based Med 2017;22(3):85-87.
- Schünemann HJ, Oxman AD, Brozek J, et al. Grading quality of evidence and strength of recommendations for diagnostic tests and strategies. BMJ 2008;336:1106-1110.
- Schünemann HJ, Mustafa RA, Brozek J, et al. GRADE guidelines: 21 part 1 and part 2. Test accuracy: study design, risk of bias, indirectness, inconsistency, imprecision, publication bias and certainty of evidence. J Clin Epidemiol 2020;122:129-152.
- Newcombe RG. Two-sided confidence intervals for the single proportion: comparison of seven methods. Stat Med 1998;17(8):857-872.
- Cohen J. Statistical Power Analysis for the Behavioral Sciences, 2nd ed. Lawrence Erlbaum, 1988.
- Hosmer DW, Lemeshow S, Sturdivant RX. Applied Logistic Regression, 3rd ed. Wiley, 2013 (section on assessing the fit of the model: AUC bands).
- Chen H, Cohen P, Chen S. How big is a big odds ratio? Interpreting the magnitudes of odds ratios in epidemiological studies. Commun Stat Simul Comput 2010;39(4):860-864.
- Miake-Lye IM, Hempel S, Shanman R, Shekelle PG. What is an evidence map? A systematic review of published evidence maps and their definitions, methods, and products. Syst Rev 2016;5:28.
- Macaskill P, Takwoingi Y, Deeks JJ, Gatsonis C. Chapter 10: Understanding meta-analysis; and Deeks JJ, Bossuyt PM, Leeflang MM, Takwoingi Y (eds). Cochrane Handbook for Systematic Reviews of Diagnostic Test Accuracy, version 2 (2023). Cochrane.
- Takwoingi Y, Guo B, Riley RD, Deeks JJ. Performance of methods for meta-analysis of diagnostic test accuracy with few studies or sparse data. Stat Methods Med Res 2017;26(4):1896-1911.
- McInnes MDF, Moher D, Thombs BD, et al. Preferred Reporting Items for a Systematic Review and Meta-analysis of Diagnostic Test Accuracy Studies: the PRISMA-DTA statement. JAMA 2018;319(4):388-396.
- Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement. BMJ 2021;372:n71.
