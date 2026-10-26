PROVISIONAL DRAFT (AI-assisted, unverified): built from Wu 2026 (ID 92) text; the companion paper Wu 2024 TVST (ID 128) is covered in paper/_wu2024_reading.md

# Other top-performing items of the 100-item acuity survey, as tabulated in Wu 2026 (IOVS 2026;67(1):28)

Source text: `data/articles_text/Wu et al. - 2026 - Screening Questions to Identify Low Vision and Acu.txt`. [page N] are that file's page markers. NR = not reported. Sens = sensitivity, Spec = specificity. For a single yes/no item the paper's "AUC" is (sens + spec) / 2 [page 3], so it is not a ROC area.

## 1. What the paper tabulates

- **Per threshold, 10 single items (Table 2, page 4), 10 pairs (Table 3, page 5) and 10 triplets (Table 4, page 5)**, each ranked by AUC. So 10 + 10 + 10 per threshold, 60 rows over the two thresholds.
- The selection kept the top 20 at each level but only the top 10 are shown [page 3]; ranks 11 to 20 and the other 80 single items are NR.
- Table 5 [page 6] lists the **21 distinct items** that occur in Tables 2 to 4.
- The full 100-item wording is said to be in "the Supplementary Material and our previous publication" [page 2]. The supplement is not in the text file, so any per-item results there are unverified; the article body reports none beyond the 10 per level.
- Thresholds: low vision = 0.3 logMAR (20/40) or worse; legal blindness = 1.0 logMAR (20/200) or worse, acuity only, no field criterion [pages 1, 3 and Table 1]. Positive screen = "no" answer (all items "no" for pairs and triplets) [page 3]. Reference: binocular habitual-correction VA [page 2]. n = 385 [page 2]. The prevalence of low vision was 68.6% and of legal blindness 19.0% [page 3].
- All ranking, selection and evaluation used the same 385 participants, so these are in-sample figures (see paper/two_item_accuracy.md).

## 2. Decoding confidence for Table 2

The text file scrambles Table 2 (numbers and item text are interleaved out of order). Table 3 and Table 4 were fully decoded and checked by arithmetic. For Table 2:

- **Confirmed by the Results prose (pages 4 and 5):** Q97, Q46, Q15 (low vision); Q30, Q62 (legal blindness).
- **Probable (from position in the text stream and arithmetic, not stated in prose):** Q12 and Q16 (low vision); Q38 and Q32 (legal blindness). Q16 sensitivity at least 0.87 is also implied, because the pair Q15 + Q16 has sensitivity 0.87 and an AND rule cannot exceed either member (my inference).
- **Not assignable:** low vision Q21, Q8, Q17, Q3, Q27; legal blindness Q42, Q71, Q18, Q11, Q44, Q59. The 33 unassigned numbers cannot be matched to items without guessing. They are listed in section 3.3 so a reviewer can check against the PDF. I did not estimate them.

## 3. Single items (Table 2, page 4)

### 3.1 Low-vision threshold (0.3 logMAR), ranked by AUC; table order is the rank [page 4]

| Rank | Item | Wording as printed [page 4] | AUC | Sens | Spec | Status |
|---|---|---|---|---|---|---|
| 1 | Q97 | In a fast-food restaurant, can you usually read the posted menus? | 0.85 | 0.89 | 0.81 | confirmed [page 4] |
| 2 | Q46 | When you are sitting in the passenger seat of a car, are you able to read the license plate of the car in front of you while waiting at a stop light? | 0.85 | 0.79 | 0.91 | confirmed [page 4]; highest specificity |
| 3 | Q15 | When holding a newspaper at a regular viewing distance of about 16 inches (40 centimeters), are you able to read the printed text in the articles? | 0.83 | 0.91 | 0.74 | confirmed [page 4]; highest sensitivity |
| 4 | Q12 | When stopped at a crosswalk in a residential area, are you able to read the street sign of the road you are about to cross? | 0.82 | 0.74 | 0.89 | probable [page 4] |
| 5 | Q16 | Would you be able to tell if your neighbor is smiling or frowning if you are standing directly across a residential street from her? | 0.80 | 0.90 | 0.70 (printed "0.7") | probable [page 4] |
| 6 | Q21 | When looking at a traditional credit card (the kind with raised numbers), are you able to read the numbers on the card when it is on the table in front of you? | NR (not assignable) | NR | NR | [page 4] |
| 7 | Q8 | When looking at an aspirin pill on the table in front of you, are you able to see the groove that allows you to cut the pill in half? | NR | NR | NR | [page 4] |
| 8 | Q17 | If you are wearing an average sized wristwatch (the kind with hands and numbers), would you be able to read the time with your wrist at arm's length? | NR | NR | NR | [page 4] |
| 9 | Q3 | Would you be able to see if the person sitting directly across the table from you has freckles on their face? | NR | NR | NR | [page 4] |
| 10 | Q27 | If you are standing on the sidewalk next to a residential street, would you be able to recognize a friend by their face across the street? | NR | NR | NR | [page 4] |
| | Average of the 10 | | 0.81 | 0.81 | 0.80 | [page 4]; text: mean AUC 0.81, sens 0.81, spec 0.80 [page 4] |

Bounds on the unassigned low-vision items from the pair and triplet tables (AND rule: pair sensitivity cannot exceed a member's, pair specificity cannot fall below a member's; my inference, not paper statements): Q21 sensitivity at least 0.80 and specificity at most 0.87 (from Q16 + Q21, 0.80 / 0.87 [page 5]); Q27 sensitivity at least 0.74 and specificity at most 0.93 (from Q46 + Q27, 0.74 / 0.93 [page 5]).

### 3.2 Legal-blindness threshold (1.0 logMAR), ranked by AUC [page 4]

| Rank | Item | Wording as printed [page 4] | AUC | Sens | Spec | Status |
|---|---|---|---|---|---|---|
| 1 | Q30 | When seated in front of a computer, are you able to read the letters on the keyboard keys? | 0.80 | 0.89 | 0.71 | confirmed [page 5]; highest AUC and sensitivity |
| 2 | Q38 | When you are standing barefoot, are you able to see your toenails (if they are unpainted)? | 0.78 | 0.86 | 0.71 | probable [page 4] |
| 3 | Q32 | When looking at standard playing cards on a table in front of you, are you able to read the numbers on the corners of the cards? | 0.78 | 0.89 | 0.66 | probable [page 4] |
| 4 | Q62 | When you are standing an arm's length away from a standard light switch, are you able to see whether the switch is flipped up or down? | 0.77 | 0.71 | 0.82 | confirmed [page 5]; highest specificity |
| 5 | Q42 | When standing at a check-out counter, are you able to see the difference between the coins—dimes, nickels, and quarters—on the counter? | NR (not assignable) | NR | NR | [page 4] |
| 6 | Q71 | When you are in an elevator, ready to press a button, are you able to read the numbers on the buttons for the different floors. | NR | NR | NR | [page 4] |
| 7 | Q18 | If you have a bowl of rice on the table in front of you, would you be able to see the individual grains of rice? | NR | NR | NR | [page 4] |
| 8 | Q11 | When looking at a ruler on the table in front of you, are you able to see the marks that indicate inches? | NR | NR | NR | [page 4] |
| 9 | Q44 | If you are looking at a pair of dice on a table in front of you, are you able to tell what numbers are on the dice? | NR | NR | NR | [page 4] |
| 10 | Q59 | At a bowling alley, are you able to see the individual pins at the end of the lane when you are standing at the line ready to bowl? | NR | NR | NR | [page 4] |
| | Average of the 10 | | 0.77 | 0.83 | 0.70 | [page 4]; text: mean AUC 0.77, sens 0.83, spec 0.70 [page 5] |

The rank order of the items is the order in which the item texts appear in the table column, and the rank-4 position of Q62 is confirmed by its stated AUC of 0.77 (after 0.80, 0.78, 0.78). The ranks 5 to 10 order rests on the item-text order only (AUC for those rows is NR).

Bounds on the unassigned legal-blindness items (same AND-rule inference): Q11 sensitivity at least 0.84, specificity at most 0.77 (from Q32 + Q11, 0.84 / 0.77 [page 5]); Q44 sensitivity at least 0.82, specificity at most 0.81 (Q30 + Q44, 0.82 / 0.81 [page 5]); Q18 sensitivity at least 0.79, specificity at most 0.81 (Q30 + Q18, 0.79 / 0.81 [page 5]).

### 3.3 Unassigned Table 2 numbers (for the reviewer to check against the PDF)

After removing the values assigned above, the text file leaves 33 values that belong to Q21, Q8, Q17, Q3, Q27 (low vision) and Q42, Q71, Q18, Q11, Q44, Q59 (legal) as 11 AUC / sens / spec triples. As a multiset, with how many times each occurs: 0.61 x1, 0.63 x1, 0.66 x1, 0.71 x1, 0.72 x1, 0.74 x3, 0.75 x4, 0.76 x2, 0.77 x2, 0.78 x3, 0.79 x5, 0.80 x2, 0.82 x2, 0.83 x2, 0.85 x1, 0.88 x1, 0.89 x1. These cannot be put into triples and items unambiguously from the text file. A reviewer should read these 11 rows from the PDF.

## 4. Pairs (Table 3, page 5), fully decoded, ranked by AUC within each threshold

Check: AUC = (sens + spec) / 2 holds within rounding for every row; the highest-AUC, highest-sensitivity and highest-specificity pairs match the Results prose [page 5]. Rows give item 1 + item 2.

### 4.1 Low vision

| Rank | Pair | AUC | Sens | Spec |
|---|---|---|---|---|
| 1 | Q97 + Q15 | 0.87 | 0.86 | 0.88 |
| 2 | Q97 + Q46 | 0.86 | 0.77 | 0.94 |
| 3 | Q97 + Q16 | 0.85 | 0.86 | 0.84 |
| 4 | Q15 + Q16 | 0.85 | 0.87 | 0.83 |
| 5 | Q46 + Q15 | 0.85 | 0.77 | 0.93 |
| 6 | Q46 + Q16 | 0.85 | 0.77 | 0.92 |
| 7 | Q46 + Q21 | 0.84 | 0.72 | 0.96 |
| 8 | Q97 + Q21 | 0.84 | 0.78 | 0.89 |
| 9 | Q46 + Q27 | 0.83 | 0.74 | 0.93 |
| 10 | Q16 + Q21 | 0.83 | 0.80 | 0.87 |
| | Average | 0.85 | 0.79 | 0.90 |

All [page 5]. Highest sensitivity: Q15 + Q16 (0.87; AUC 0.85; spec 0.83). Highest specificity among pairs: Q97 + Q46 (0.94; AUC 0.86; sens 0.77) [page 5, text]. **Inconsistency:** as decoded, row 7 Q46 + Q21 has specificity 0.96, higher than the 0.94 the text calls "the highest specificity" [page 5]. Either the text claim is wrong or my column decode of that row is wrong (AUC 0.84 is consistent with (0.72 + 0.96) / 2, which supports the decode). Check against the PDF.

### 4.2 Legal blindness

| Rank | Pair | AUC | Sens | Spec |
|---|---|---|---|---|
| 1 | Q30 + Q12 | 0.82 | 0.88 | 0.77 |
| 2 | Q30 + Q44 | 0.82 | 0.82 | 0.81 |
| 3 | Q30 + Q38 | 0.82 | 0.79 | 0.84 |
| 4 | Q30 + Q32 | 0.81 | 0.82 | 0.80 |
| 5 | Q38 + Q11 | 0.81 | 0.81 | 0.80 |
| 6 | Q38 + Q32 | 0.80 | 0.81 | 0.80 |
| 7 | Q38 + Q12 | 0.80 | 0.85 | 0.76 |
| 8 | Q30 + Q18 | 0.80 | 0.79 | 0.81 |
| 9 | Q32 + Q11 | 0.80 | 0.84 | 0.77 |
| 10 | Q30 + Q37 | 0.80 | 0.85 | 0.75 |
| | Average | 0.81 | 0.83 | 0.79 |

All [page 5]. Highest AUC and sensitivity of the pairs: Q30 + Q12. Highest specificity: Q30 + Q38 (0.84) [page 5, text]. Q12 and Q37 are not among the legal single top 10, and they appear in 3 of the 10 pairs, matching the text "Seven out of the top 10 pairs were composed exclusively of combinations from the top 10 individual items" [page 5].
Q37 wording [page 6, Table 5]: "Are you able to read the numbers on a microwave key pad at arm's length?"

## 5. Triplets (Table 4, page 5), fully decoded

Check: AUC = (sens + spec) / 2 within rounding for every row; best triplets match the text [pages 5, 6].

### 5.1 Low vision

| Rank | Triplet | AUC | Sens | Spec |
|---|---|---|---|---|
| 1 | Q97 + Q15 + Q16 | 0.86 | 0.84 | 0.89 |
| 2 | Q97 + Q46 + Q15 | 0.85 | 0.75 | 0.96 |
| 3 | Q46 + Q15 + Q16 | 0.85 | 0.75 | 0.94 |
| 4 | Q97 + Q46 + Q16 | 0.85 | 0.75 | 0.94 |
| 5 | Q97 + Q16 + Q21 | 0.84 | 0.77 | 0.91 |
| 6 | Q97 + Q46 + Q27 | 0.84 | 0.71 | 0.97 |
| 7 | Q15 + Q16 + Q21 | 0.84 | 0.77 | 0.90 |
| 8 | Q97 + Q46 + Q21 | 0.84 | 0.71 | 0.97 |
| 9 | Q46 + Q15 + Q21 | 0.84 | 0.71 | 0.97 |
| 10 | Q97 + Q15 + Q21 | 0.84 | 0.76 | 0.91 |
| | Average | 0.85 | 0.75 | 0.94 |

All [page 5]. Q97 + Q15 + Q16 AUC 0.86, sens 0.84, spec 0.89 is stated in the text [page 5].

### 5.2 Legal blindness

| Rank | Triplet | AUC | Sens | Spec |
|---|---|---|---|---|
| 1 | Q30 + Q44 + Q12 | 0.83 | 0.81 | 0.84 |
| 2 | Q30 + Q32 + Q12 | 0.82 | 0.81 | 0.83 |
| 3 | Q30 + Q38 + Q44 | 0.82 | 0.75 | 0.89 |
| 4 | Q30 + Q44 + Q37 | 0.82 | 0.81 | 0.82 |
| 5 | Q30 + Q38 + Q12 | 0.82 | 0.78 | 0.85 |
| 6 | Q32 + Q11 + Q12 | 0.82 | 0.82 | 0.81 |
| 7 | Q30 + Q18 + Q44 | 0.82 | 0.77 | 0.87 |
| 8 | Q38 + Q11 + Q12 | 0.82 | 0.79 | 0.84 |
| 9 | Q30 + Q32 + Q11 | 0.82 | 0.78 | 0.85 |
| 10 | Q30 + Q12 + Q37 | 0.81 | 0.84 | 0.79 |
| | Average | 0.82 | 0.80 | 0.84 |

All [page 5]. Best triplet stated in text [page 6]: Q30 + Q44 + Q12, AUC 0.83, sens 0.81, spec 0.84. The text reports 3 of the 10 triplets as built only from the legal top-10 singles [page 6]; the table shows exactly three (ranks 3, 7, 9), matching.

## 6. Which threshold each item serves (Table 5, page 6)

| Item | Wording as printed in Table 5 [page 6] | Threshold(s) and level(s) |
|---|---|---|
| Q3 | Would you be able to see if the person sitting directly across the table from you has freckles on their face? | Low vision (single) |
| Q8 | When looking at an aspirin pill on the table in front of you, are you able to see the groove that allows you to cut the pill in half? | Low vision (single) |
| Q11 | When looking at a ruler on the table in front of you, are you able to see the marks that indicate inches? | Legal blindness (single, pair, triplet) |
| Q12 | When stopped at a crosswalk in a residential area, are you able to read the street sign of the road you are about to cross? | Low vision (single); legal blindness (pair, triplet) |
| Q15 | When holding a newspaper at a regular viewing distance of about 16 inches (40 centimeters), are you able to read the printed text in the articles? | Low vision (single, pair, triplet) |
| Q16 | Would you be able to tell if your neighbor is smiling or frowning if you are standing directly across a residential street from her? | Low vision (single, pair, triplet) |
| Q17 | If you are wearing an average sized wrist watch (the kind with hands and numbers), would you be able to read the time with your wrist at arm's length? | Low vision (single) |
| Q18 | If you have a bowl of rice on the table in front of you, would you be able to see the individual grains of rice? | Legal blindness (single, pair, triplet) |
| Q21 | When looking at a traditional credit card (the kind with raised numbers), are you able to read the numbers on the card when it is on the table in front of you? | Low vision (single, pair, triplet) |
| Q27 | If you are standing on the sidewalk next to a residential street, would you be able to recognize a friend by their face across the street? | Low vision (single, pair, triplet) |
| Q30 | When seated in front of a computer, are you able to read the letters on the keyboard keys? | Legal blindness (single, pair, triplet) |
| Q32 | When looking at standard playing cards on a table in front of you, are you able to read the numbers on the corners of the cards? | Legal blindness (single, pair, triplet) |
| Q37 | Are you able to read the numbers on a microwave key pad at arm's length? | Legal blindness (pair, triplet) |
| Q38 | When you are standing barefoot, are you able to see your toenails (if they are unpainted)? | Legal blindness (single, pair, triplet) |
| Q42 | When standing at a check-out counter, are you able to see the difference between the coins—dimes, nickels, and quarters—on the counter? | Legal blindness (single) |
| Q44 | If you are looking at a pair of dice on a table in front of you, are you able to tell what numbers are on the dice? | Legal blindness (single, pair, triplet) |
| Q46 | When you are sitting in the passenger seat of a car, are you able to read the license plate of the car in front of you while waiting at a stop light? | Low vision (single, pair, triplet) |
| Q59 | At a bowling alley, are you able to see the individual pins at the end of the lane when you are standing at the line ready to bowl? | Legal blindness (single) |
| Q62 | When you are standing an arm's length away from a standard light switch, are you able to see whether the switch is flipped up or down? | Legal blindness (single) |
| Q71 | When you are in an elevator, ready to press a button, are you able to read the numbers on the buttons for the different floors? | Legal blindness (single) |
| Q97 | In a fast-food restaurant, can you usually read the posted menus? | Low vision (single, pair, triplet) |

The threshold column was read from a scrambled list in the text file [page 6]; I matched its 21 entries to the 21 items in order, and the matching agrees with Tables 2 to 4 for every item I could check (all pair and triplet memberships above). Q12 is the only item serving both thresholds; no item is a single at both.

## 7. Items bearing on field loss, contrast, glare or mobility, flagged

**Caution that governs this whole section: every item here was selected and evaluated for how well it tracks measured visual acuity (low vision 0.3 logMAR, legal blindness 1.0 logMAR), in a sample where no visual-field, contrast sensitivity or glare measure was taken [pages 2, 3, 8]. Any link between an item's content and field loss, contrast loss, glare or mobility is my reading of the item wording (an inference), not a finding of the paper.** The authors themselves say these items "do not detect legal blindness due to visual-field loss alone" and that field-oriented items are future work [page 8]. The paper reports no glare item among the 21 tabulated items.

| Item | Why it might touch on the domain (inference) | Rank / tabulated | Notes |
|---|---|---|---|
| Q16 facial expression across a residential street | face and expression recognition at distance; low-contrast detail; outdoors | LV single 5 (probable), in LV pairs and triplets | The authors call recognizing a facial expression across a residential street "more context agnostic" [page 8] |
| Q27 recognizing a friend by face across the street | face recognition at distance; outdoors | LV single 10, in LV pair Q46 + Q27 [page 5] | |
| Q3 freckles across a table | fine low-contrast facial detail | LV single 9 | |
| Q8 aspirin pill groove | low-contrast small detail | LV single 7 | |
| Q12 street sign at a crosswalk | outdoor; involves crossing a street (mobility context) | LV single 4 (probable); legal pairs and triplets (rank 1 pair and rank 1 triplet) [pages 5, 6] | The paper treats this as reading |
| Q46 license plate from the passenger seat | outdoor, in a vehicle; distance | LV single 2 | |
| Q59 bowling pins at the end of the lane | distance and object detection | Legal single 10 | |
| Q71 elevator floor buttons | public-space navigation task | Legal single 6 | |
| Q62 light switch up or down | contrast and a pale-on-pale target | Legal single 4 | highest specificity of the legal singles [page 5] |
| Q38 unpainted toenails | low-contrast target (nail on skin) | Legal single 2, rank-3 pair [page 5] | The authors call it "context agnostic" [page 8] |
| Q42 coins (dimes, nickels, quarters) | discriminating small shiny objects by detail; may also involve colour or luminance | Legal single 5 | |
| Q44 dice | high-contrast pips on a table | Legal single 9, in rank-1 legal triplet | |
| Q18 rice grains | small, low-contrast detail | Legal single 7 | |

No tabulated item asks directly about peripheral vision, bumping into things, falls, glare, night vision or contrast. Those are the gaps the authors name [page 8].

The paper's own comment on content: "six out of the top 10 performing individual screening questions (Q97, Q46, Q15, Q12, Q21, Q17) directly involved reading in various contexts" [page 7]. This is for the low-vision single items; two of the six (Q21, Q17) are not assignable in Table 2 from the text file but are named here in the prose, which confirms they are in the low-vision top 10.
