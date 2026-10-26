PROVISIONAL DRAFT (AI-assisted, unverified): built from the provisional included set (reviewer has decided 40/135 at title/abstract, 0 at full text). Every figure comes from the reading notes `paper/_candidates_survey.md` (Wu 2026, ID 92) and `paper/_candidates_other.md` (the other included papers), which cite `[page N]` markers of `data/articles_text/*.txt`. Advisory until the reviewer checks each number against its source page.

# Candidate items to add to the two-question screen for a glaucoma clinic

## 0. What this file can and cannot say

- **No item below has been validated as a stand-alone screening item against a low-vision-rehabilitation (LVR) need reference standard.** The 100-item survey items are validated only against measured acuity, in-sample. The items from other instruments have only correlations or regressions of whole-instrument or domain scores, not item-level accuracy.
- **The survey items track acuity, not field or contrast.** The authors themselves say the items "do not detect legal blindness due to visual-field loss alone" and that field-oriented items are future work (Wu 2026 [page 8]). Any link between a survey item and field or contrast loss is an inference from its wording, not a finding.
- **Only one included study is a glaucoma sample with a perimetric measure** (Sumi 2003, n = 147, monocular HFA 30-2, a Japanese questionnaire; no contrast, glare or driving item) [page 2 to 6]. GAL-9 was developed for peripheral loss, but the included GAL-9 study excluded glaucoma (Agathos 2025 [page 4]). No GQL-15 paper is among the included texts.
- Items marked "probable" or "NR" come from scrambled tables in the text files and need checking against the PDF.

## 1. Top items of the 100-item acuity survey (Wu 2026, ID 92; n = 385, one cohort, in-sample)

The paper tabulates only the top 10 single items per threshold (Table 2 [page 4]); the other 90 are NR. Positive screen = "no" answer. AUC for a single yes/no item is (sensitivity + specificity)/2, not a ROC area [page 3]. Thresholds: low vision = 0.3 logMAR (20/40) or worse; legal blindness = 1.0 logMAR (20/200) or worse, acuity only [pages 1, 3].

### 1.1 Low vision (0.3 logMAR), ranked by AUC [page 4]

| Rank | Item | Wording | AUC | Sens | Spec | Status |
|---|---|---|---|---|---|---|
| 1 | Q97 | In a fast-food restaurant, can you usually read the posted menus? | 0.85 | 0.89 | 0.81 | confirmed in prose |
| 2 | Q46 | When sitting in the passenger seat of a car, are you able to read the license plate of the car in front of you while waiting at a stop light? | 0.85 | 0.79 | 0.91 | confirmed; highest specificity |
| 3 | Q15 | When holding a newspaper at a regular viewing distance of about 16 inches, are you able to read the printed text in the articles? | 0.83 | 0.91 | 0.74 | confirmed; highest sensitivity |
| 4 | Q12 | When stopped at a crosswalk in a residential area, are you able to read the street sign of the road you are about to cross? | 0.82 | 0.74 | 0.89 | probable |
| 5 | Q16 | Would you be able to tell if your neighbor is smiling or frowning if you are standing directly across a residential street from her? | 0.80 | 0.90 | 0.7 | probable |
| 6 to 10 | Q21, Q8, Q17, Q3, Q27 | credit card numbers; aspirin groove; wristwatch time; freckles on a face across the table; recognise a friend across the street | NR | NR | NR | values not assignable from the scrambled table (33 numbers listed in `_candidates_survey.md` section 3.3) |

Average of the 10: AUC 0.81, sens 0.81, spec 0.80 [page 4]. Best pairs: Q97 + Q15 AUC 0.87 (sens 0.86, spec 0.88); Q15 + Q16 highest sensitivity 0.87; Q97 + Q46 specificity 0.94 [page 5]. Best triplet: Q97 + Q15 + Q16 AUC 0.86 (sens 0.84, spec 0.89) [page 5]. Inconsistency to check: as decoded, pair Q46 + Q21 has specificity 0.96, above the 0.94 the text calls highest [page 5].

### 1.2 Legal blindness (1.0 logMAR), ranked by AUC [page 4]

| Rank | Item | Wording | AUC | Sens | Spec | Status |
|---|---|---|---|---|---|---|
| 1 | Q30 | When seated in front of a computer, are you able to read the letters on the keyboard keys? | 0.80 | 0.89 | 0.71 | confirmed |
| 2 | Q38 | When standing barefoot, are you able to see your toenails (if unpainted)? | 0.78 | 0.86 | 0.71 | probable |
| 3 | Q32 | When looking at standard playing cards on a table, are you able to read the numbers on the corners of the cards? | 0.78 | 0.89 | 0.66 | probable |
| 4 | Q62 | When standing an arm's length from a standard light switch, are you able to see whether the switch is flipped up or down? | 0.77 | 0.71 | 0.82 | confirmed; highest specificity |
| 5 to 10 | Q42, Q71, Q18, Q11, Q44, Q59 | coins; elevator buttons; rice grains; ruler marks; dice; bowling pins | NR | NR | NR | not assignable |

Average of the 10: AUC 0.77, sens 0.83, spec 0.70 [pages 4, 5]. Best pairs: Q30 + Q12 AUC 0.82 (sens 0.88, spec 0.77); Q30 + Q38 highest specificity 0.84 [page 5]. Best triplet: Q30 + Q44 + Q12 AUC 0.83 (sens 0.81, spec 0.84) [pages 5, 6]. Q12 is the only item serving both thresholds [page 6].

## 2. Items from the other included instruments that target field, contrast, glare, mobility or driving

Instrument-level or domain-level evidence only. "Glaucoma sample?" is as stated in the paper.

| Instrument | Item or domain | Target | Strongest evidence (statistic, n, page) | Glaucoma sample? |
|---|---|---|---|---|
| Independent Mobility questionnaire (Bibby 2007, ID 120) | 35-item Rasch person measure | Field, contrast, mobility | vs binocular visual field r = -0.762 (n = 30, not stated separately) [page 4]; vs low-contrast VA r = 0.576 (n reduced, number NR; 10 of 30 could not read the chart) [pages 3, 4]; vs high-contrast VA r = 0.410 [page 4]. Stepwise regression: field the only significant predictor, adjusted R2 = 0.565 [page 5]. No CI. | No (4 of 30 with a glaucoma entry by count) [page 2] |
| Same | Item 18 "Walking in high glare areas" (hardest item, -1.58 logits); walking at night (-1.01); walking in dimly lit indoor areas (-0.65) | Glare, low luminance | Rasch item difficulty only [pages 5, 7]; table scrambled, verify | No |
| Japanese revised visual disability questionnaire (Sumi 2003, ID 110) | Walking domain, items 9 to 16 incl. "Do you fail to see people or cars approaching you from the side?" (16) | Field, mobility | Walking DI vs better-eye MD r = -0.61, worse eye -0.58, n = 147 [page 4] (re-aligned from a scrambled table) | **Yes** (POAG 69, NTG 56, angle closure 22) [page 2] |
| Same | Going-out domain, items 17 to 21 incl. "Do you feel uneasy going out at night because of your visual problems?" (21) | Field, low luminance | Going-out DI vs better-eye MD r = -0.63, worse eye -0.60 [page 4]; inferior field within 5 degrees (VFE) standardised beta -0.25, p = 0.0035 [page 6] | Yes |
| Same | Total DI (30 questions) | Field | vs better-eye MD r = -0.64; with acuity, R = 0.87 [pages 4, 6]. No contrast measure, no glare or driving item [page 6]. | Yes |
| GAL-9 (Agathos 2025, ID 55) | Q1 walking after dark; Q2 seeing at night; Q4 adjusting to dim lights; Q5 light-to-dark transitions; Q3 uneven ground; Q6 objects coming from the side | Contrast, low luminance, mobility, field (Q6) | Total vs binocular contrast sensitivity rho = -0.62 (95% CI -0.72 to -0.49), pairs NR [page 15]; regression CS beta = -7.58 (-10.66 to -4.503), R2 = 0.45 [pages 8, 9, 15]. Hardest items Q1, Q2, Q4, Q5, Q3 [page 15]. | Instrument built for peripheral loss; **this sample excluded glaucoma** (maculopathy, n = 125) [page 4] |
| Same | G3 "Do you have mobility problems because of your vision?" | Mobility | Positive in 18.0%, 31.0% and 71.4% of mild, moderate and severe contrast-sensitivity groups [page 13]; 36% overall [page 13] | No |
| Same | G1 falls in past 12 months | Falls | 41.6% at least one fall [page 11]; falls beta 1.077 (0.405 to 1.749) on GAL-9 total [page 9] | No |
| APEDS-VFQ (Gothwal 2012, ID 5) | Item 12 "Noticing objects off to the side, when you are walking and looking straight ahead"; items 6 to 9 (glare, poorly lit, dark-bright adaptation) | Field, glare | Rasch factor analysis only; no field or contrast analysis; score vs VA r = 0.28 in text (0.29 in the Figure 4 caption), n = 351 [pages 2, 7, 9] | No |
| NEI VFQ-25 (Stelmack 2002; Murro 2017; Selivanova 2019) | Item 9 (steps in dim light or at night), item 10 (objects off to the side); driving items 15, 16, A10 | Low luminance, field, driving | Item 9 and 10 did not change after rehabilitation [Stelmack page 17]; driving items dropped or unscored (few drivers) [Stelmack page 9; Murro page 2]. Composite vs Pelli-Robson r = 0.66 (95% CI 0.45 to 0.87), 16 Stargardt patients [Murro page 4]. | No |
| NVQ-10 (Wu 2016, ID 63) | Item 5 "vision at night", item 6 "reading in dim light"; items 1 to 3 driving-related, wording NR | Low luminance, driving | Low luminance deficit beta 0.067 (95% CI 0.005 to 0.130), p = 0.034; BCVA p = 0.984; n = 100 [page 3] | No (glaucoma excluded) |
| IVI (Selivanova 2019, ID 72) | Mobility subscale items 2, 4, 10 to 13, 16 to 20 (wording NR in text) | Mobility, field | Hemianopia or peripheral loss OR 0.82 (95% CI 0.05 to 12.2) for mobility change, 8 participants [pages 5, 6]; authors say the IVI "was designed for patients with poor central vision" [page 6] | No |
| Activity Inventory (Tabrett 2011, ID 46) | Mobility domain person measure | Field, contrast | vs outer 10 to 30 degree HFA field rho = 0.61; vs central 10 degrees 0.49; vs contrast sensitivity 0.47; vs VA -0.27; n = 100 [page 5]; regression outer-ring beta 0.54, R2 = 0.43 [page 6] | Partly (11 eyes with optic neuropathy including glaucoma) [page 3] |
| Activity Inventory (Massof 2007, ID 95) | Driving goal and 21 driving tasks (incl. "Drive at night", "See lane markings") | Driving, contrast | Perceived driving ability vs log contrast sensitivity r = 0.35 and vs logMAR r = -0.28, both p < 0.001, pairs NR [page 6] | 12% glaucoma [page 1] |
| VA LV VFQ-48 (Szlyk 2004; Di Maggio 2020) | Items 21 to 24, 27, 28 (unfamiliar places, night, dim-light steps, bright light, crowds, bumping) | Mobility, glare | Mobility subscale vs contrast sensitivity rho = 0.18, n = 76 (aligned from a scrambled table; verify) [Di Maggio page 4] | Glaucoma 14 of 131 [Di Maggio page 2] |
| Spatial Localization Questionnaire (Subramanian 2006, ID 97) | Crossing the road; changes in ground level; judging the next stair; avoiding obstacles | Contrast, mobility | vs contrast sensitivity r = 0.53, p < 0.01; vs VA r = -0.38; n = 42 [page 6]. Field not measured [page 2]. | 2 of 42 |

## 3. Ranked shortlist for a glaucoma clinic (3 to 5 items to add to the two questions)

Ranking is my reading of the evidence above and is advisory. The ordering weighs (a) whether the item's content matches the glaucoma deficit (field, contrast, glare, mobility), (b) the strength of the best linked evidence, and (c) whether the evidence comes from a glaucoma sample. **No item has item-level accuracy against an LVR-need standard, so every entry is a candidate for a pilot, not a recommendation.**

1. **A peripheral-field mobility item: "Do you fail to see people or cars approaching you from the side?"** (Sumi 2003, item 16; GAL-9 Q6 "Seeing objects come from the side" is the closest alternative.) Evidence: the walking domain that contains it correlated with better-eye mean deviation at r = -0.61 in 147 glaucoma patients [Sumi page 4]; this is domain-level, not item-level, and Japanese-language. GAL-9 Q6 has no glaucoma data in the included paper (it was the least difficult item in a central-loss sample) [Agathos page 15].
2. **A low-light / night item: "Do you feel uneasy going out at night because of your visual problems?"** (Sumi 2003, item 21) or GAL-9 Q2 "Seeing at night" and Q4 "Adjusting to dim lights". Evidence: the Sumi going-out domain r = -0.63 with better-eye mean deviation [page 4]; GAL-9 total vs contrast sensitivity rho = -0.62, with the night and dim-light items among the hardest [Agathos page 15], but in maculopathy, not glaucoma.
3. **A glare item: "Walking in high glare areas"** (Bibby 2007, item 18, the hardest of 35 items) or APEDS-VFQ items 6 to 9. Evidence is weak: Rasch item difficulty in 30 mixed low-vision patients [Bibby pages 5, 7]; the instrument's whole-score correlation with binocular field is r = -0.762 [page 4]. No included paper tests glare sensitivity against an item.
4. **A global mobility item: "Do you have mobility problems because of your vision?"** (GAL-9 companion question G3). Evidence: positive in 18.0%, 31.0% and 71.4% across mild, moderate and severe contrast-sensitivity groups [Agathos page 13], in maculopathy; no sensitivity or specificity.
5. **From the survey itself, Q12 "street sign at a crosswalk"** (low vision AUC 0.82 as decoded, probable; the top legal-blindness pair is Q30 + Q12, AUC 0.82 [Wu 2026 page 5]). It is the only survey item that serves both thresholds and puts the task in a street-crossing context, but its link to field or contrast is an inference, and the authors name field-oriented items as future work [page 8].

**What is missing for all five:** a glaucoma sample with visual field (ideally binocular or Esterman), contrast sensitivity and an LVR-need reference standard; item-level (not domain-level) statistics; an external validation sample. The reviewer should decide whether to propose these items as a pilot instead of a recommendation.
