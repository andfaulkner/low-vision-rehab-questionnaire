PROVISIONAL DRAFT (AI-assisted, unverified): built from Wu 2024 TVST (ID 128) text rebuilt from Europe PMC XML; no page numbers

# Wu et al. 2024, Transl Vis Sci Technol 13(9):20 - "Estimating Visual Acuity Without a Visual Acuity Chart" (Screening ID 128)

Source file: analysis/extraction/sources/Wu_2024_TVST_PMC11412607.txt (read in full: abstract, Introduction, Methods, Results, Discussion, Limitations, Conclusions, Table 1, Figure captions 1-5, reference list). Page numbers are NOT available (the text was rebuilt from open-access Europe PMC XML; the PDF could not be fetched). Every number below is cited as [Section / Table / Figure]. "NR" = not reported in the text. Items marked "(derived)" are simple arithmetic on reported numbers, not reported by the authors. Supplementary Tables S1, S2 and Figure S1 are NOT in the text file and were not seen. This is advisory until the reviewer checks it against the source.

## 1. What the study is

- Design: cross-sectional, multi-site development study of a 100-item yes/no self-report "VA survey", analysed with a two-parameter logistic (2PL) item response theory (IRT) model, then a linear regression of estimated vision ability on measured logMAR VA [Methods / IRT and Analysis; Results / Estimating VA].
- Aim (verbatim): "to determine if a person's VA can be estimated from self-reported answers to questions about their daily viewing experiences" [Discussion, para 1]. Introduction: "This study was designed to develop a VA survey to establish the relationship between measured values of VA and daily viewing experiences" [Introduction].
- It is an IRT / psychometric calibration study, NOT a sensitivity/specificity study.
- Accuracy-type outcomes it DOES report: Pearson r between ability and VA (-0.73 text; -0.72 abstract), R2 = 0.53, regression slope, signed and unsigned prediction error, coefficient of repeatability (Bland-Altman style), % of participants within +/-0.24 logMAR, correlation of signed and unsigned error with measured VA [Results / Estimating VA; Abstract].
- Accuracy-type outcomes it does NOT report: sensitivity, specificity, predictive values, likelihood ratios, AUC/ROC, any 2x2 table, any cut-point classification of "VA worse than X" (a grep of the text finds "sensitivity" only as "contrast sensitivity"). Item-level VA thresholds are given (e.g. 0.29 logMAR for the ant item) but their classification accuracy against a VA criterion is NR [Results / VA Thresholds for Items].
- The instrument is a 100-item survey taking 30-60 min, so it is not a brief screening question; the only "screening" language is in the Conclusions ("promise for clinical applications or as a screening tool within telehealth and broader public health settings") [Conclusions].
- Test-retest reliability of the survey: NR. Internal consistency / Cronbach alpha: NR. Responsiveness: NR.

## 2. The 100-item survey

- Number of items: 100 yes/no questions [Abstract; Methods / VA Survey].
- Item content: self-reported ability to recognise object details at a stated, typical viewing distance (e.g. "Would you be able to see the eye of a needle, if you hold it at arm's length?") [Methods / VA Survey]. Respondents answered "assuming good lighting and normal viewing conditions" [Methods / VA Survey].
- How items were written/selected: "iterative process" in which "the Minnesota team members developed a pool of possible items, aiming to include a wide range of acuity levels"; selection for broad familiarity to US participants, avoiding unfamiliar objects; informal pilot testing with normally sighted and low-vision individuals, with items added/removed on feedback; example removed item "Can you see someone's footprints in the snow on a snowy day?" [Methods / VA Survey]. Number of items in the initial pool: NR. Number pilot-tested: NR. Formal cognitive interviewing: NR.
- Response format: yes / no; "not applicable" allowed if the scenario was unfamiliar [Methods / VA Survey]. Number or handling of "not applicable" responses: NR (the handling in the IRT is NR).
- Administration mode: interviewer-administered, "over the phone or in a clinic" [Methods / VA Survey]. The Limitations/Discussion also say the survey "can be administered over the phone or via a website easily" [Discussion / Limitations]; no website administration was reported in the Methods (the website statement is a prospect, not a tested mode).
- Time: "30 to 60 minutes to complete" [Methods / VA Survey]; "ranged from 30 to 60 minutes, which may contribute to response fatigue" [Limitations].
- Wording of the review's target items: grep of the text for "restaurant", "menu" and "keyboard" returns NO hits. The restaurant-menu and keyboard items do not appear anywhere in the text. The full list of 100 questions is in Supplementary Table S1 [Methods / VA Survey], and per-item VA thresholds are in Supplementary Table S2 [Results / VA Thresholds for Items]; both are supplementary-only and were not available to me. Whether a menu or keyboard item is among the 100 is therefore UNKNOWN from this text.
- Items quoted in the body text (all with section label): needle eye at arm's length (b = 1.29; VA threshold 0.15 logMAR; hardest) [Results / 2PL IRT Results; VA Thresholds]; parking-space white lines (b = -2.65; 1.47 logMAR; easiest) [same]; toothbrush bristles on the counter (a = 5.45, b = -1.31; highest discrimination) [Results / 2PL IRT]; soccer-ball black hexagons at arm's length (a = 1.43, b = -2.22; lowest discrimination) [same]; person across the dinner table wearing glasses (poorest fit, P < 0.01) [same]; ant on a sidewalk (0.29 logMAR) and bananas on a table, counting individual bananas (1.0 logMAR) [Results / VA Thresholds]; credit card dropped on the floor (discussed as a low-contrast task) [Discussion]; full vs half moon on a clear night (example in Abstract; its VA limit is 1.0 logMAR [Abstract]; the moon item is not discussed in the body text).
- Other data collected with the survey: race, ethnicity, age, etiology and age of onset of visual impairment, presence of central or peripheral field loss, and contrast sensitivity if available [Methods / VA Survey]. Race/ethnicity, onset age and field-loss results: NR.

## 3. The sample

- n = 385 [Results / Sample Characteristics; Table 1 "All"].
- Sites: 4 US sites (University of Minnesota n = 65; Ohio State n = 151; Johns Hopkins n = 130; University of Alabama at Birmingham n = 39) [Table 1]. Sum 385 (checks).
- Recruitment: June 2019 to February 2022; "Researchers contacted participants from previous studies or patients at each site"; consent signed or electronic; IRB approval at all four sites; Declaration of Helsinki [Methods / Participants]. Consecutive vs convenience sampling: NR (not stated; contact from previous studies suggests convenience).
- Inclusion criteria: age 18+; VA measurement available "from laboratory, clinic, or electronic health records"; able to hear and respond to questions in English in person or by phone. "No specific requirements for VA, visual field, or diagnosis were imposed" [Methods / Participants]. Exclusion criteria: NR. Language: English only [Methods / Participants].
- Age: all participants mean 55.71 +/- 20.54 years [Table 1]; abstract says mean 56.7 [Abstract] (see Ambiguities). Age range: NR. By site: 48.71 +/- 20.7 (MN), 48.89 +/- 18.76 (OSU), 66.65 +/- 17.61 (JHU), 59.18 +/- 21.28 (UAB) [Table 1].
- Sex: 57% female overall [Table 1]; by site 62% / 54% / 54% / 62% (MN / OSU / JHU / UAB) [Table 1].
- Diagnosis mix: "three main ocular diagnoses" overall: macular degeneration n = 74, glaucoma n = 65, cataract n = 25 [Table 1]. Glaucoma n = 65 of 385 (16.9%, derived). By site: Minnesota RP 12, AMD 8, cataract 8; Ohio State AMD 32, albinism 17, cataract 16; Johns Hopkins AMD 29, glaucoma 21, diabetic retinopathy 6, RP 6; Alabama glaucoma 21, AMD 5, cone dystrophy 2 [Table 1]. Full diagnosis distribution (beyond the three main ones), glaucoma stage/severity, visual field loss and glaucoma subtype: NR. Results stratified by diagnosis: NR (the authors say "we didn't explore other influencing factors like specific diagnoses, and central or peripheral visual field loss" [Limitations]).
- VA: range -0.3 to 2.0 logMAR; mean 0.58, SD 0.44, median 0.51 [Results / Sample Characteristics; Table 1]. By site mean +/- SD: 0.83 +/- 0.51 (MN), 0.60 +/- 0.38 (OSU), 0.51 +/- 0.44 (JHU), 0.33 +/- 0.36 (UAB) [Table 1]. A VA histogram is in Figure S1 (supplementary, not seen).
- How VA was measured: "The majority of the VA measurements were performed using the Bailey-Lovie or ETDRS charts, except for some measurements using Snellen charts"; all converted to logMAR [Methods / Participants]. Source was lab, clinic or electronic health record [Methods / Participants]. In the Discussion: at OSU and JHU "some VA data were extracted from existing electronic health records and may, in some cases, have been measured with Snellen charts. Accordingly, as many as 20% to 30% of our study participants might have been tested with Snellen charts" [Discussion]. Which eye / binocular vs better eye / presenting vs best-corrected VA: NR. Time between VA measurement and the survey: NR.
- Contrast sensitivity: measured in a subset, n = 291 of 385 (75.6%, derived); correlation of CS with VA r = -0.51, P < 0.001 [Discussion]. CS test used, scale and how it was measured: NR. A further subgroup with VA 0.3-0.4 logMAR and CS measured, n = 33: no significant correlation between CS and unsigned prediction error (r = -0.3; P > 0.05) [Discussion].
- Visual field: collected as presence of central or peripheral field loss [Methods / VA Survey]; no field data reported (NR).
- Cognitive status, education, reading level: NR.

## 4. Results

### 4.1 IRT model
- 2PL IRT (item difficulty b and discriminability a both free; Rasch would constrain a equal), fitted with the R package mirt v1.40 [Methods / IRT and Analysis]. Reported text says "mirt package v1.4018" (the "18" is the reference superscript run into the version).
- Ability (theta): mean 0.01 logit, SD 0.94, range -2.81 to 2.03 [Results / 2PL IRT Results].
- Item difficulty: range -2.65 to 1.29 logit; mean 0.81, SD 0.82 [Results / 2PL IRT Results].
- 86% of participants had ability within the range of item difficulties; the other 14% were mostly above the hardest item (average measured VA of those above 0.05 logMAR, SD 0.17), and one was below the easiest item [Results / 2PL IRT Results].
- Item discrimination: mean 2.91, SD 0.76, range 1.43 to 5.45; "The items on the two ends of the distribution of difficulty had lower discriminability than those in the middle" [Results / 2PL IRT Results; Figure 2B].
- Wright map: Figure 2A (distributions of theta and item difficulty).

### 4.2 Item difficulty versus VA
- Regression of measured VA on theta: slope = -0.33 (95% CI -0.37 to -0.30), r = -0.73, R2 = 0.53 [Results / Estimating VA; Figure 3]. Equation 2: Estimated VA = 0.59 - 0.33 x theta [Results / Estimating VA].
- The same equation converts item difficulty b to an item VA threshold ("where a participant has a 50/50 chance of a yes response") [Results / VA Thresholds for Items]. Range of item thresholds: 0.15 logMAR (needle, hardest) to 1.47 logMAR (parking lines, easiest) [Results / VA Thresholds for Items; Limitations]. Thresholds for all 100 items: Supplementary Table S2 (not seen).
- Items near common criteria: ant on sidewalk 0.29 logMAR ("close to the VA boundary of logMAR 0.3 (Snellen 20/40)"); bananas 1.0 logMAR ("close to the criterion for legal blindness in the United States") [Results / VA Thresholds for Items]. Abstract: moon item VA limit 1.0 logMAR [Abstract].
- Coverage limit (verbatim): "Participants with VA better than 0.15 logMAR and poorer than 1.47 logMAR show poorer predictions due to the lack of items in these ranges" [Limitations].

### 4.3 Correlation of ability with VA
- r = -0.73 (ability vs VA; text) [Results / Estimating VA; Discussion; Conclusions]; abstract gives r = -0.72 [Abstract]. Estimated VA vs measured VA r = 0.73, P < 0.001 [Results / Estimating VA; Figure 4].
- Comparison with other VFQs as given by the authors [Discussion]: Activity Inventory r = 0.57 (and 0.6); NEI VFQ-25 r = 0.52 (low vision) and r = -0.50 (AMD); Activities of Daily Vision Scale r = 0.20; VF-14 r = 0.27; Visual Activities Questionnaire r = 0.14-0.36; Impact of Vision Impairment R2 = 0.19. The authors attribute their higher correlation to "including viewing distance and object size" [Discussion].

### 4.4 Prediction error (estimated VA from the survey minus measured VA)
- Signed prediction error: mean 0 logMAR (SD 0.3) [Results / Estimating VA; Abstract: "0"].
- Unsigned prediction error: mean 0.24 logMAR (SD 0.19) [Results / Estimating VA; Abstract]. Authors translate to "approximately 2 lines on a typical VA chart or 12 letters" [Discussion].
- Coefficient of repeatability (95%): 0.59 logMAR [Results / Estimating VA; Abstract; Figure 5A]; compared in the Discussion with 0.2 logMAR for chart test-retest in low vision (Kiser et al., ref 19) and judged larger [Discussion]. (Derived check: 1.96 x 0.3 = 0.59.)
- Percent within +/-0.24 logMAR: 60% of participants [Results / Estimating VA]. Percent within other bands (e.g. +/-0.1 or +/-0.3): NR.
- Bias: signed error correlated with measured VA r = -0.69, P < 0.01: "participants with better VA tended to have estimated VA that were worse than their actual VA measurements, whereas those with worse measured VA were more likely to have estimated VA that were better" (regression to the mean) [Results / Estimating VA; Figure 5A]. Unsigned error correlated with measured VA r = 0.33, P < 0.001: worse VA, larger errors [Results / Estimating VA; Figure 5B].
- Error by misfit: 60 misfitting participants had larger unsigned error (mean 0.33 logMAR) than others (mean 0.22), t(75.71) = 3.71, P < 0.05 [Discussion].
- Accuracy in subgroups by site, age, diagnosis (including glaucoma): NR. External validation or cross-validation (the equation was fitted and tested on the same 385): NR; there is no train/test split reported, so the error figures are in-sample.

### 4.5 Contrast sensitivity finding
- "Although the questions in our survey were designed to target participants' VA, it is likely that other factors, such as contrast sensitivity, also influenced their responses." [Discussion]
- CS vs VA r = -0.51 (P < 0.001) in n = 291 [Discussion]. "Some survey items could be considered as low-contrast tasks... it is expected that contrast sensitivity sometimes interacts with VA in determining object visibility." [Discussion] In the n = 33 subgroup (VA 0.3-0.4 logMAR), CS did not correlate with unsigned prediction error (r = -0.3; P > 0.05) [Discussion]. "Further studies are needed to determine the precise impact of VA versus contrast sensitivity on participant responses to our items." [Discussion]. Contrast sensitivity was not entered into the IRT or prediction model [Methods / IRT and Analysis] (NR as a predictor).

### 4.6 Misfit
- Items: 5 of 100 items (Q12, Q23, Q35, Q49, Q79) with significantly worse fit (P < 0.05; signed chi-squared test); the poorest was "Can you see if the person eating dinner directly across the table from you is wearing glasses?" (P < 0.01) [Results / 2PL IRT Results]. Item wording for Q12, Q23, Q35, Q49, Q79 other than the glasses item: NR in the body (likely in Table S1; which of the five the glasses item is, is NR).
- Persons: 60 of 385 misfit by the Zh statistic (|Zh| > 1.96); about 15% [Results / 2PL IRT Results; Discussion]. Misfitting items and persons were not removed from the analysis [Results / 2PL IRT Results].

### 4.7 Which kinds of items track acuity well or poorly
- The text gives NO systematic statement of item types that track acuity well or poorly (nothing about items depending on field, lighting, glare, colour). What it does say:
  - Items at the extremes of difficulty had lower discriminability than middle items [Results / 2PL IRT Results; Figure 2B].
  - Highest discrimination: toothbrush bristles item (a = 5.45); lowest: soccer-ball hexagons item (a = 1.43) [Results / 2PL IRT Results].
  - Poorest-fitting item: the person-with-glasses item; no reason is given for the misfit of any item [Results / 2PL IRT Results].
  - Contrast is offered as a possible contaminant for some items (credit card on the floor "might have had a different impact on contrast sensitivity depending on the card and the flooring") [Discussion].
  - Authors' ideas for the unexplained error: letter-chart acuity may not represent everyday recognition; different charts give different results; Snellen charts for 20-30%; real life has "a wider range of viewing conditions" than the controlled VA test [Discussion]. Scotoma and peripheral field loss are suggested but untested explanations of person misfit: "Further evaluation into the participants (e.g., the presence of scotomas, peripheral visual field loss) with higher misfit values could also help" [Discussion].
  - Lighting: the instruction was to assume good lighting [Methods / VA Survey]; no analysis of lighting.
- Whether any item set (e.g. "menu" or "keyboard"-type reading/near-detail items) performs better than others: NR.

## 5. The authors' stated limitations and conclusions

Limitations [Discussion; Limitations]:
- Less accurate for VA better than 0.15 or poorer than 1.47 logMAR "due to the lack of items in these ranges"; larger errors with worse VA [Limitations].
- Linear transformation gives worse predicted VA for better-VA participants and better predicted VA for worse-VA participants; nonlinear mapping or an added regression correction might help [Limitations].
- Measured VA explains only about 53% of variance (R2 = 0.53); diagnosis, central and peripheral field loss not explored [Limitations].
- 30-60 min testing time; possible response fatigue; plan for computer-adaptive testing and dropping misfit items [Limitations].
- VA data heterogeneity (Snellen vs ETDRS/Bailey-Lovie; EHR-extracted VA at two sites), letter-chart acuity not equal to everyday object recognition [Discussion].
- 2PL model needs larger samples than Rasch for stable estimates [Discussion].
- Coefficient of repeatability (0.59) larger than chart test-retest (0.2 logMAR) [Discussion].
- Not listed by the authors but visible in the text (my observations, flagged as such): no independent validation sample; recruitment from prior-study contacts and clinic patients; English only; survey test-retest NR.

Conclusions (verbatim where short): "we found a strong correlation between the estimated abilities to answer the questionnaire and the measured VA"; "This VA survey shows promise for clinical applications or as a screening tool within telehealth and broader public health settings"; further work to add items extending the VA range, consider contrast sensitivity, and develop computer-adaptive testing [Conclusions]. Abstract: "Yes/no questions about everyday visual activities have the potential to estimate an individual's VA. Future refinements may enhance reliability." [Abstract]. The abstract's "Translational Relevance" claims potential use for telehealth [Abstract].

## 6. Relationship to Wu 2026

- The text file contains NO mention of Wu 2026, of a companion IOVS paper, of a restaurant-menu or keyboard item, or of any later reanalysis (grep for "2026", "restaurant", "menu", "keyboard" found nothing; the only "iovs" hits are journal abbreviations in the reference list, e.g. refs 5, 12, 21, 22, 25).
- Whether the same participants were used in Wu 2026: NOT STATED in this text. I do not assume overlap. The recruitment description (385 participants, 4 sites, June 2019 to February 2022, 100-item survey) is what a reviewer would compare with the Wu 2026 text. The only link in the text is the future-work paragraph: items to extend the VA range and a computer-adaptive version that would "automatically picking informative items contingent on prior responses while excluding the misfit items" [Limitations; Conclusions]; this is a plan, not a reference to Wu 2026.
- Overlap decision must be made from the Wu 2026 text, not from this paper.

## 7. Ambiguities and what I chose

1. Correlation: abstract r = -0.72 vs body r = -0.73 [Abstract; Results / Estimating VA; Discussion]. Chose -0.73 (stated three times in the body; R2 = 0.53 consistent with r = 0.73, since 0.73^2 = 0.533).
2. Mean age: abstract 56.7 years vs Table 1 "All" 55.71 +/- 20.54. Chose Table 1 (55.71). A sample-size-weighted mean of the four site means is about 55.9 (derived), which matches neither exactly (small difference, possibly rounding or missing age).
3. Female %: Table 1 overall 57%; weighted site percentages give about 56% (derived). Chose 57% as reported.
4. Coefficient of repeatability: the text writes "coefficient of repeatability (0.95)" and "coefficient of repeatability of 0.95 of 0.59 logMAR", where "0.95" appears to denote the 95% limit (1.96 SD), not a value; the Discussion sentence "coefficient of repeatability = 0.95 = 0.2 logMAR" is garbled in the same way. Chose CoR = 0.59 logMAR (agrees with the abstract and with 1.96 x SD 0.3). The "0.2 logMAR" comparator is from ref 19 as written.
5. Within +/-0.24 logMAR: 60% [Results / Estimating VA]; no abstract figure. Note +/-0.24 is the mean unsigned error, so this is "within the average error", not a pre-set tolerance; reported as given.
6. Item difficulty summary: mean b = 0.81 (SD 0.82) with range -2.65 to 1.29 [Results / 2PL IRT Results] while ability mean is 0.01 (SD 0.94). A mean of 0.81 with SD 0.82 and max 1.29 implies a strongly skewed item distribution. It is not impossible, but it looks odd; I report it as given and flag it for checking against Figure 2A. (Also, a theta mean of 0.01 against item mean 0.81 would mean most items are "too hard" for the average respondent, yet the VA thresholds derived from b run 0.15 to 1.47 around a mean VA of 0.58; this is consistent only if the sign convention of b is as stated. Not resolved.)
7. Item-threshold direction: "needle... had an estimated VA threshold of 0.15 logMAR, the highest threshold among the 100 items" and parking lines "represented the lowest item measure" with 1.47 logMAR [Results / VA Thresholds]. "Highest threshold" here means the hardest item (best acuity needed), i.e. the lowest logMAR value. Check: 0.59 - 0.33 x 1.29 = 0.16 and 0.59 - 0.33 x (-2.65) = 1.46 (derived), consistent. Chose to report them as "hardest = 0.15 logMAR, easiest = 1.47 logMAR".
8. Misfit percentage: "about 15%" [Discussion] vs 60/385 = 15.6% (derived). Fine; reported 60 of 385.
9. Software version: "mirt package v1.4018" in the text is v1.40 plus a run-in reference number (18); reported as v1.40 with this caveat.
10. "Discussion" sentence "Eighty-six percent ... The other 14%": 14% of 385 is about 54 participants (derived); the count is NR.
11. Moon item: appears in the abstract (VA limit 1.0 logMAR) but not in the body or in any quoted item list; its b value is NR. Chose to quote the abstract only.
12. "Mirt: signed chi-squared test.6 ... Zh statistic.7" cite refs 6 and 7 (Massof & Fletcher; Mangione), which appear to be citation-numbering carry-overs from an earlier draft (ref 7 is the Activities of Daily Vision Scale paper, not a Zh statistic source). Not a numerical issue; noted for completeness.
13. Items Q12, Q23, Q35, Q49, Q79 and the full 100-item list: supplementary only; cannot confirm whether restaurant-menu or keyboard items exist in the 100.
14. A claim in the Limitations that the VA range covers "the majority of patients with low vision in the United States" cites refs 23 and 28; not verified here.
15. P values: "t(75.71) = 3.71, P < 0.05" is as printed (a t of 3.71 on 75 df would be much smaller than 0.05; probably a loosely stated threshold). Reported as printed.
16. No page numbers exist in the source text; the "[page 1]" at the top of the text file is a placeholder, not a real page.
