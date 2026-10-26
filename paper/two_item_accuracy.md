PROVISIONAL DRAFT (AI-assisted, unverified): built from Wu 2026 (ID 92) text; the companion paper Wu 2024 TVST (ID 128) is covered in paper/_wu2024_reading.md

Source: Wu YH, Yu D, Goldstein J, Kwon M, Wang C, Legge GE. Screening questions to identify low vision and acuity-defined legal blindness. Invest Ophthalmol Vis Sci. 2026;67(1):28. All page numbers are the `[page N]` markers in `data/articles_text/Wu et al. - 2026 - Screening Questions to Identify Low Vision and Acu.txt` (8 pages). NR = not reported by the paper. "(derived)" = my arithmetic from paper numbers, not a paper statement. Tables in the text file are column-scrambled; how each value was decoded is in the last section.

## 1. The two items

### Item 1, Q97 (low vision)

- **Wording as printed:** "Q97. In a fast-food restaurant, can you usually read the posted menus?" [page 4, Table 2; same in Table 5, page 6]. The abstract prints it without "usually": "In a fast-food restaurant, can you read the posted menus?" [page 1]. The Results text prints "can you usually read the posted menus?" [page 4].
- **Threshold keyed to:** low vision, not legal blindness [page 1; Table 5 page 6 lists Q97 as "Low vision (single, pair, triplet)"].
  - Paper's words: "low vision (VA ≤ 0.3 logMAR or 20/40)" [page 1]. Introduction: "low vision is defined as a best-corrected visual acuity (BCVA) of 0.3 logMAR (20/40) or worse in the better-seeing eye" [page 1].
  - Operational definition (Table 1, page 3): 121 participants (31.4%) are ">20/40" and 108 (28.1%) are "0.3 to <0.6"; with 83 + 50 + 23 in worse categories. So "low vision" means 0.3 logMAR (20/40) **or worse** (i.e. logMAR 0.3 or higher), consistent with "68.6% had VA worse than 0.3 logMAR" [page 3]. The "≤" in the paper's "VA ≤ 0.3 logMAR" is therefore a notation inversion (it means "0.3 logMAR or poorer"; see section 7).
  - Acuity used: binocular VA with habitual correction, better eye if only monocular was available [page 2].
- **Answer coded positive:** "no". "For a single survey item, a 'no' response classified the participant as likely having low vision or legal blindness, and a 'yes' response classified them otherwise" [page 3].
- **Sensitivity 0.89 [page 4, Table 2 and Results text; page 1 abstract]. Specificity 0.81 [page 4; page 1]. AUC 0.85 [page 4; page 1].** Highest AUC of the 100 items for low vision [page 4].
- **AUC caveat, quoted:** "Because each screening has only one decision threshold (classifying a participant as either meeting or not meeting the VA criterion), the ROC reduces to a single point, and the AUC simplifies to the average of sensitivity and specificity" [page 3]. Check: (0.89 + 0.81) / 2 = 0.85 (derived).
- **PPV / NPV for Q97 alone:** NR. The paper gives only means across the top 10 items, pairs and triplets (see section 2) [page 7].
- **Odds ratio:** 3.28 (95% CI 2.6 to 4.17), "representing 3.28 times increased odds of having low vision given a 'no' response to Q97" [page 7]. How it was computed is NR. See section 7: it is hard to reconcile with sensitivity 0.89 and specificity 0.81.
- **Performance at the other threshold (legal blindness) for Q97:** NR (Q97 is not in the legal-blindness tables) [page 6, Table 5].

### Item 2, Q30 (legal blindness)

- **Wording as printed:** "Q30. When seated in front of a computer, are you able to read the letters on the keyboard keys?" [page 4, Table 2]. Identical in Table 5 [page 6] and in the abstract [page 1].
- **Threshold keyed to:** legal blindness defined by acuity only [page 1; Table 5 page 6: "Legal blindness (single, pair, triplet)"].
  - Paper's words: "legal blindness as defined by the VA criterion (VA ≤ 1 logMAR or 20/200)" [page 1]. "In the present study, we operationalized legal blindness exclusively by the VA criterion (VA ≤ 1.0 logMAR)" [page 1]. The usual legal definition also includes a visual field of 20 degrees or less [page 1], which this study does not test [page 8].
  - Operational definition (Table 1, page 3): "1.0 to <1.3 (20/400)" 50 (12.99%) and "≤1.3 logMAR (20/400)" 23 (6%). So 50 + 23 = 73 participants (derived) are at or worse than 1.0 logMAR (20/200); text: "19.0% met or exceeded the threshold for legal blindness (≤1.0 logMAR)" [page 3]. The row label "≤1.3" reads as 1.3 or worse (see section 7). Same notation inversion as for low vision: "≤ 1.0 logMAR" means 1.0 logMAR or poorer.
- **Answer coded positive:** "no" [page 3].
- **Sensitivity 0.89 [page 4; page 5 Results text; page 1]. Specificity 0.71 [page 4; page 1]. AUC 0.80 [page 4; page 1].** Highest AUC and highest sensitivity of the legal-blindness items [page 5].
- **AUC caveat:** same as Item 1 [page 3]. Check: (0.89 + 0.71) / 2 = 0.80 (derived).
- **PPV / NPV for Q30 alone:** NR. Means across top-10 sets only: legal-blindness PPV 0.40 (one item), 0.48 (two items), 0.54 (three items); NPV about 0.95 across one to three items [page 7].
- **Odds ratio:** NR for Q30 (an OR is given only for Q97) [page 7].
- **Performance at the low-vision threshold for Q30:** NR (Q30 is not in the low-vision tables) [page 6, Table 5].

## 2. The pair, and what a second or third item adds

- **Are Q97 and Q30 ever evaluated together?** No. Q97 appears only in low-vision tables and Q30 only in legal-blindness tables [pages 4, 5, 6, Table 5]. No pair or triplet in Tables 3 and 4 contains both [page 5]. Their combined performance is NR. The paper never proposes Q97 + Q30 as a pair or as a two-threshold screen.
- **Best pair, low vision:** Q97 + Q15 (newspaper): AUC 0.87, sensitivity 0.86, specificity 0.88 [page 5]. Positive only if the answer to both is "no" [page 3]. For comparison, Q97 alone is AUC 0.85 [page 4], so the gain is 0.02 (derived).
- **Highest-specificity pair, low vision:** Q97 + Q46 (license plate): specificity 0.94, AUC 0.86, sensitivity 0.77 [page 5]. **Highest-sensitivity pair:** Q15 + Q16 (facial expression): sensitivity 0.87, AUC 0.85, specificity 0.83 [page 5].
- **Best pair, legal blindness:** Q30 + Q12 (street sign at a crosswalk): AUC 0.82, sensitivity 0.88, specificity 0.77 [page 5]. **Highest-specificity pair:** Q30 + Q38 (toenails): specificity 0.84, AUC 0.82, sensitivity 0.79 [page 5]. Q30 alone is AUC 0.80 [page 4], so the gain is 0.02 (derived).
- **Group-level effect of a second item (top 10 single vs top 10 pairs):**
  - Low vision: mean AUC 0.81 to 0.85 (t18 = 4.02, P < 0.001), specificity 0.80 to 0.90, sensitivity 0.82 to 0.79 (P > 0.05) [page 4, continuing page 4 to 5 in the text].
  - Legal blindness: mean AUC 0.77 to 0.81 (t18 = 7.17, P < 0.001), specificity 0.70 to 0.79, sensitivity 0.83 to 0.83 [page 5].
- **Third item:** low vision, best triplet Q97 + Q15 + Q16: AUC 0.86, sensitivity 0.84, specificity 0.89 [page 5]. Mean AUC 0.85 vs 0.85, P = 0.54 [page 5]. Legal blindness, best triplet Q30 + Q44 (dice) + Q12: AUC 0.83, sensitivity 0.81, specificity 0.84 [page 6]; mean AUC 0.81 to 0.82 (P < 0.01) but sensitivity 0.83 to 0.8 (P < 0.01) [page 6].
- **The "<= 0.05" statement, verbatim (abstract):** "For both screening thresholds, adding a second item increased AUC by ≤0.05; a third item gave no further improvement." [page 1]. The body shows mean AUC increases of 0.04 (0.81 to 0.85 and 0.77 to 0.81) [pages 4 and 5], so the abstract's bound is a ceiling on group-mean gains, not a statement about any named item.
- **PPV / NPV across sets (means over top 10), the only PPV / NPV in the paper [page 7]:**
  - Low vision PPV: 0.93 (one item), 0.96 (two), 0.98 (three). NPV: 0.582, 0.576, 0.537.
  - Legal blindness PPV: 0.40, 0.48, 0.54. NPV about 0.95 across one to three items.
- **Authors' interpretation:** "a two-item screen appears to offer the best balance between brevity and predictive performance, with one item often being sufficient for short screening and three items providing only marginal additional benefit" [page 7]. Abstract: "a two-item pair offers a compact option when higher specificity is desired" [page 1].
- **Pair rule:** "no" to both items is positive; any "yes" is negative [page 3]. This is an AND rule, so sensitivity can only fall and specificity can only rise relative to the weaker single item (my inference from the rule).

## 3. The sample

- **n = 385 adults** [pages 1, 2, 3]. "a cohort of 385 participants whose recruitment and detailed characteristics were previously described" (ref. 7, Wu 2024 TVST) [page 2]. The cohort is the same one as the TVST paper (my inference from the shared citation; the paper says "data from a cohort ... previously described").
- **Recruitment:** four U.S. institutions, June 2019 to February 2022 [page 2]. Inclusion: 18 years or older, available VA data, able to communicate in English for the 100-item survey. "All participants were naive to the items at enrollment." "The recruitment aimed to include individuals across a broad spectrum of visual function" [page 2]. Named sites, clinic vs community source, and exclusion criteria: NR here (deferred to ref. 7) [page 2].
- **Language:** English [page 2].
- **Mode of administration** (self-, interviewer-, phone, online): NR in this paper [pages 2 to 3]. Participants "completed the survey" [page 1].
- **Age:** mean 55.71, SD 20.54, range 18 to 98 [page 3, Table 1]. 18 to 39: 99 (25.7%); 40 to 64: 132 (34.3%); 65 to 84: 122 (31.7%); 85 or older: 30 (7.8%) [page 3]. These counts sum to 383, not 385 (see section 7).
- **Sex:** female 221 (57.4%) [page 3].
- **Diagnosis** ("not mutually exclusive"): macular degeneration 74 (19.2%); **glaucoma 65 (16.9%)**; cataract 25 (6.5%) [page 3]. Other diagnoses and the proportion with no ocular disease: NR. Diagnoses came from "physician exam notes and participant self-report entries ... may still be subject to recall bias" [page 2].
- **Acuity measurement:** VA with habitual correction, "standardized charts (Bailey–Lovie, ETDRS, or Snellen)"; binocular VA when both monocular and binocular were available; otherwise VA from the better-seeing eye [page 2]. Which chart was used for which participant: NR.
- **VA range and distribution:** binocular VA mean ± SD 0.58 ± 0.44 logMAR, range −0.3 to 2.0 [page 2; page 3, Table 1]. Table 1 [page 3]: >20/40 121 (31.4%); 0.3 to <0.6, 108 (28.1%); 0.6 to <1.0, 83 (21.6%); 1.0 to <1.3 (20/400), 50 (12.99%); ≤1.3 logMAR (20/400), 23 (6%). Sums to 385 (derived).
- **Reference categories (derived from Table 1 [page 3]):**
  - Low vision (0.3 logMAR or worse): 108 + 83 + 50 + 23 = 264 (68.6%, stated as a percentage on page 3; the count is derived). Not low vision: 121.
  - Legal blindness (1.0 logMAR or worse): 50 + 23 = 73 (19.0%, percentage stated on page 3; the count is derived). Not legally blind: 312 (derived).
- **Ceiling:** "a ceiling effect impacting 14% of the sample", mostly normal or near-normal VA (average measured VA 0.05 logMAR) [page 4]. The authors also write "its composition, with fewer normally sighted individuals than the general population" [page 8].
- **Item bank context:** 100 yes/no items; IRT-derived item difficulties −2.65 to 1.69 logits; participant ability −2.81 to 2.03 logits [page 4]. Five items showed "suboptimal IRT model fit" in the earlier work [page 3].

## 4. How the items were chosen from the 100

- **Same sample for selection and evaluation; no external validation.** All 100 items were scored against measured VA in the same 385 participants, the top items were picked on the same data, and the performance reported is for those picks [page 3 (steps); page 4 (results)]. No hold-out set, split-sample or cross-validation is described anywhere in the paper (I found none after reading all 8 pages). The authors' own limitation: "external validation in other countries, with cultural/linguistic adaptation and empirical item assessment, is warranted" [page 8]. Optimism bias in the reported accuracy is therefore likely (my inference). For QUADAS-2 domain 2 (index test), the index test positivity rule and item choice were data-driven and not prespecified; the paper does not call this out itself.
- **Ranking criterion: AUC**, i.e. (sensitivity + specificity) / 2 for a single cut point [page 3]. Pairs were ranked by AUC "which combines information across all response patterns" [page 3]; the primary classification rule stayed "no to all items" [page 3].
- **Steps** [page 3]:
  1. Each of the 100 items scored separately at each threshold; the **20 highest-AUC items** kept per threshold.
  2. Each of those 20 paired with each of the remaining 99 items = "1980 unique combinations per threshold"; the **top 20 pairs** kept.
  3. Each of the top 20 pairs combined with each of the remaining 98 items = 1960 triplets per threshold [page 5]; the 20 highest-AUC triplets identified.
- **How many tabulated:** the top 10 only, per threshold, at each level: Table 2 (10 single items per threshold), Table 3 (10 pairs per threshold), Table 4 (10 triplets per threshold) [pages 4, 5]. So 10 of the 20 retained at each level are shown; the 11th to 20th are NR. Table 5 lists the 21 distinct items that occur in Tables 2 to 4 [page 6].
- **Whole survey for comparison:** predicted VA = 0.59 − 0.33 × ability [page 6, Equation 1]. Low vision: AUC 0.80, sensitivity 0.94, specificity 0.66. Legal blindness: AUC 0.53, sensitivity 0.06, specificity 1.00 [page 6]. The authors note the whole survey (AUC 0.80) fell "slightly below that of the single best item, Q97 (AUC = 0.85)" [page 7].
- **Statistics:** t-tests (df = 18) comparing the top-10 means across single, pair and triplet levels treat the items as independent samples [pages 4 to 6] (my observation; the paper does not discuss it). No confidence intervals for any sensitivity, specificity or AUC; none for 2x2 counts; NR throughout, except the OR for Q97 [page 7].

## 5. The authors' stated limitations and cautions (verbatim where short)

1. Field loss not covered [page 8]: "our screening questions target low vision (VA ≤ 0.3 logMAR) and legal blindness as defined by VA (VA ≤ 1.0 logMAR) and do not detect legal blindness due to visual-field loss alone (e.g., ≤20°)." "our VA-based items may misclassify individuals with preserved acuity but severely constricted visual fields." Diagnosis-specific effects: "central vision loss in AMD vs. peripheral field loss in glaucoma, potentially producing item-level differences even at similar VA". "Future work should incorporate items designed to reflect functional consequences of field loss (e.g., navigation in crowds, bumping into obstacles outside central vision) and validate combined VA- and field-oriented item sets against gold standard perimetry."
2. Sample [page 8]: "our study sample of 385 participants is relatively small compared to population studies, and its composition, with fewer normally sighted individuals than the general population, may limit the generalizability". "Further studies are needed to validate these items in larger, more diverse cohorts."
3. Context effect [page 8]: "the performance metrics reported here are based on responses collected within the context of the full 100-item survey. It is possible that the performance of individual items or short combinations might differ if administered independently".
4. Cultural and object familiarity, naming Q97 and Q30 [page 8]: "some of the best-performing items identified for screening rely on familiarity with specific objects or settings. Examples include question Q97, which refers to reading fast-food menus, and question Q30, involving letters on computer keyboards." "Accordingly, external validation in other countries, with cultural/linguistic adaptation and empirical item assessment, is warranted."
5. Comparison with earlier studies [page 7]: "direct comparisons should be interpreted cautiously due to inherent differences in study samples and designs."
6. Reference and self-report caveats [page 7]: self-report brings "less accurate categorization results and overestimated prevalence of visual impairment"; diagnoses may suffer recall bias [page 2].
7. Measurement ceiling [page 4]: "measurement precision may be reduced for individuals at the extremes of the ability spectrum in this sample".
8. The paper calls the results "promising, although imperfect" [page 7] and its list of items "a list of items that can be tested for their performance in future studies" [page 8].

## 6. Summary table

All values are from the paper (Table 2, 3 or 4 and Results text) unless marked. Rows use the paper's AUC = (sens + spec) / 2.

| Item or set | Threshold | Sens | Spec | AUC | Page |
|---|---|---|---|---|---|
| Q97 menus (single) | low vision (0.3 logMAR or worse) | 0.89 | 0.81 | 0.85 | 4 (abstract 1) |
| Q30 keyboard (single) | legal blindness (1.0 logMAR or worse) | 0.89 | 0.71 | 0.80 | 4 (abstract 1) |
| Q97 + Q15 (best LV pair, AUC) | low vision | 0.86 | 0.88 | 0.87 | 5 |
| Q30 + Q12 (best legal pair, AUC) | legal blindness | 0.88 | 0.77 | 0.82 | 5 |
| Q97 + Q15 + Q16 (best LV triplet) | low vision | 0.84 | 0.89 | 0.86 | 5 |
| Q30 + Q44 + Q12 (best legal triplet) | legal blindness | 0.81 | 0.84 | 0.83 | 6 |
| Q97 + Q30 (the two named items together) | either | NR | NR | NR | not evaluated |
| Q97 at legal blindness | legal blindness | NR | NR | NR | not tabulated |
| Q30 at low vision | low vision | NR | NR | NR | not tabulated |
| Whole 100-item survey | low vision | 0.94 | 0.66 | 0.80 | 6 |
| Whole 100-item survey | legal blindness | 0.06 | 1.00 | 0.53 | 6 |

## 7. Ambiguities in the paper

1. **"≤" direction.** The paper writes "VA ≤ 0.3 logMAR" and "VA ≤ 1.0 logMAR" [pages 1, 3, 7, 8] but means 0.3 logMAR or worse (higher logMAR). The introduction says "0.3 logMAR (20/40) or worse" [page 1] and Table 1 groups ">20/40" as the non-low-vision stratum [page 3]. **I chose:** low vision = 0.3 logMAR or poorer; legal blindness = 1.0 logMAR or poorer. Because of the same notation, the text "68.6% had VA worse than 0.3 logMAR" [page 3] includes people exactly at 0.3 (the 0.3 to <0.6 band is counted in the 68.6%: 28.1 + 21.6 + 12.99 + 6 = 68.7, consistent). Whether participants at exactly 0.3 logMAR count as positive is therefore settled only by that sum, not stated.
2. **Table 1 row labels.** ">20/40" (121) is never given a logMAR value (it means better than 0.3 logMAR). The last row "≤1.3 logMAR (20/400)" (23) must mean 1.3 or worse, since the row above is "1.0 to <1.3". I read it that way. "12.99" is printed to two decimals while the others use one (a typo for 13.0).
3. **Age bands.** 99 + 132 + 122 + 30 = 383, not 385; the percentages sum to 99.5%. Two participants are unaccounted for in age (missing data or error). Text says ages "18 to over 85", Table 1 says 18 to 98 [page 3].
4. **Item wording.** Abstract Q97 omits "usually" [page 1]; Tables 2 and 5 include it [pages 4, 6]. Table 5 prints "wrist watch" for Q17 and Table 2 prints "wristwatch" [pages 4, 6]. The Results text paraphrases Q16 with "if you were standing" while Table 2 has "if you are standing" [pages 4, 5]. **I chose** the Table 2 / Table 5 wording as the item text.
5. **Q97 odds ratio vs sensitivity and specificity.** Sensitivity 0.89 and specificity 0.81 imply a diagnostic odds ratio of about 34 (derived: (0.89 / 0.11) / (0.19 / 0.81)). The paper's OR is 3.28 (CI 2.6 to 4.17) [page 7], with no method given (possibly an IRT or continuous-ability model, a per-unit OR, or a different definition). I could not reconcile them. **I chose** to report the paper's OR as printed and not use it for the 2x2.
6. **Unique combinations.** "1980 unique combinations" = 20 × 99 [page 3] counts a pair twice when both members are in the top 20; the real number of distinct pairs is smaller. Same for 1960 triplets [page 5]. The paper does not note this. The top-10 table contents are unaffected.
7. **Pair composition claims.** For low vision, "all top 10 pairs were composed exclusively of combinations from the top 10 individual items" [page 5]. For legal blindness, "Seven out of the top 10 pairs" and "Three out of the top 10 triplets" were [pages 5, 6]. I checked these against my decoded Tables 3 and 4: pairs with Q12 or Q37 (not in the legal top 10 singles) are 3, so 7 of 10 are exclusive; triplets with Q12 or Q37 are 7, so 3 of 10 are exclusive. Consistent.
8. **Low-vision "AUC = 0.85" for pairs near the top.** Several pairs in Table 3 have rounded AUC that differs by 0.01 from (sens + spec) / 2 of the rounded values (e.g. Q38 + Q11 and Q38 + Q32 in the legal column). I attribute this to rounding of unrounded inputs. No action.
9. **"Significantly" language.** The abstract and text report t-tests across top-10 lists (df 18) as evidence that pairs beat singles [pages 4, 5]; the items are selected on the outcome, so these P values are not interpretable as inference (my judgement, not the paper's).
10. **NPV for low vision.** Text says it "decreased modestly ... from 0.582 to 0.576 to 0.537" [page 7], while PPV is 0.93 to 0.98; NPV of about 0.58 in a sample with 68.6% positives is consistent with that prevalence but the paper never states the prevalence-dependence caveat. PPV and NPV in this sample are not transferable to a general population (my inference); the authors do not say so.
11. **"Highest specificity" low-vision pair.** The text says Q97 + Q46 "attained the highest specificity (0.94; AUC = 0.86; sensitivity = 0.77)" [page 5]. In my decode of Table 3 the pair Q46 + Q21 has specificity 0.96 (sens 0.72, AUC 0.84) [page 5]. I cannot tell which is right from the text file; this affects only which pair is called "highest specificity", not the Q97 + Q15 result. **I chose** to quote the paper's text for the Q97 + Q46 figures and flag the conflict.
12. **Table 2 scrambling.** The Table 2 numbers in the text file are out of order. Q97, Q46, Q15 (low vision) and Q30, Q62 (legal) are confirmed by the Results prose [pages 4, 5]. Every Table 3 and Table 4 row was decoded by column count and checked that AUC ≈ (sens + spec) / 2, and by the Results prose (best, highest-sensitivity and highest-specificity pairs and triplets). Mode of administration and sites are simply NR (see section 3).
