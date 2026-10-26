# What the papers in data/articles_text say about each instrument

Facts below were read from the `.txt` files (page = the `[page N]` marker in the file, which is
the PDF page, not the journal page). IDs are Screening-sheet IDs. These are candidate
extraction rows for `analysis/extraction/instruments.csv` and `property_results.csv`; the
reviewer confirms each against the page before use, and AI assistance in compiling them is
disclosed in Methods. Whether a paper is *included* is not decided here: the full-text
decision column of the workbook is still empty.

Note: `Anchor article.txt` is a second copy of Wu 2026 (ID 92), not Wu 2024 (ID 128); the
2024 TVST development paper of the 100-item survey is not in `data/articles_text/`.

## LVQOL (Low Vision Quality-of-Life Questionnaire)

**Wolffsohn & Cochrane 2000 (ID 26), development paper.**
- Item pool of 74 items chosen by LVR professionals and patients from earlier questionnaires;
  150 low-vision patients completed them on four occasions; 70 age- and sex-matched controls
  with normal vision; pre/post rehabilitation in 278 patients (p1, abstract).
- Final instrument: 25 items, summed score 0 (low QoL) to 125 (high QoL) (p1, p5).
- Internal consistency alpha = 0.88; "good reliability (0.72)" (p1, p5). The Methods name the
  intraclass correlation coefficient as the reliability statistic (p3) and a 4-week test-retest
  interval chosen to span a rehabilitation episode (p5), so the 0.72 can be entered as an ICC
  (reviewer to confirm the ICC model is not stated: COSMIN RoB box 6 "Adequate" at best).
- Factor analysis (varimax) identified up to four factors, each with alpha > 0.80: general
  vision/mobility/lighting; psychological adjustment; reading and fine work; activities of daily
  living (p5). EFA only, so structural validity rates "?".
- Known groups: low vision 60.9 +/- 25.1 vs normal vision 100.3 +/- 20.8, P < .001 (p5).
- Responsiveness: rehabilitation improved the score by 6.8 +/- 15.6 (17%) (p1).
- Feasibility: "takes 5 to 10 minutes to complete" (p9); culture-specific content deliberately
  excluded so it can be used worldwide without alteration (p9).

**Perez-Mana et al. 2022 (ID 119), Spanish version (SLVQOL).**
- 170 visually impaired patients and 195 healthy subjects; SLVQOL, NEI VFQ-25 and EQ-5D-5L
  administered (p1). Telephone interview at the public hospital, face-to-face at the private
  clinic (p3).
- Structure as in the original: 25 items in four dimensions, 0-5 response options (p3).
- Alpha 0.981 (95% CI 0.978-0.985) over the whole sample; dimension alphas 0.857-0.971 (p5).
- Test-retest: Spearman rho = 0.864 after 19.5 +/- 5.07 days in 73 stable patients (p5). No
  ICC, so COSMIN reliability rates "?".
- Administration time (visually impaired): 393.5 +/- 73.1 s by telephone vs 290.0 +/- 68.7 s
  face-to-face; healthy subjects 345.8 s and 181.0 s; impaired slower than healthy and telephone
  slower than face-to-face, all P < .001 (p5-6).
- Cut-off 105 or 106 detected visual impairment with sensitivity 95.4% and specificity 91.8%
  (p1): an accuracy result against VI status, so QUADAS-2 / DTA path (and spectrum concern:
  healthy volunteers as negatives).
- IRT (generalised partial credit model): discrimination 0.539-3.063 (p1).

## NEI VFQ-25

**Stelmack et al. 2002 (ID 65).**
- 77 legally blind veterans (Hines BRC) and 51 partially sighted veterans (VICTORS) given the
  NEI VFQ-25 plus supplement in interview format at admission and discharge; instructions
  modified to answer as if wearing glasses or using low-vision devices (p1).
- The VFQ-25 plus supplement has 25 + 14 = 39 items drawn from the 51-item NEI VFQ; 6 rate
  general health and vision, 20 rate difficulty with activities, 13 ask agreement with
  statements (p7). Three driving items and the two 10-point items were dropped, leaving 34
  items for Rasch analysis (Wright & Masters rating scale model, Winsteps) (p1, p9).
- Item measures estimated separately in the two programmes correlated r = 0.87 (p10), i.e. the
  items order the same way in different severities of low vision.
- Conclusion for this review: the difficulty-rated items map onto a functional-ability scale;
  the frequency / agreement items "can be mapped ... but with far less reliability" (p17).

**Selivanova et al. 2019 (ID 72).** See IVI below: NEI VFQ-25 used with 12 subscales, the
driving subscale dropped, three near-vision items added, Rasch-scored into visual functioning
and socioemotional subscales (p2); effect sizes after rehabilitation 0.29 (socioemotional) and
0.22 (functioning) (p5-6).

**Perez-Mana 2022 (ID 119)** used the NEI VFQ-25 (25 items, reduced from 51) as a convergent
comparator for the SLVQOL (p3).

## VA LV VFQ-48 (and VA-13)

**Stelmack et al. 2006 (ID 66).**
- Administered by telephone interview before and 3 months after rehabilitation at five VA and
  private-sector sites; VA from near-normal to total blindness (p1, p3).
- Four questions per item: "Is it difficult to ...?" (not difficult / slightly-moderately /
  extremely / impossible / do not do for non-visual reasons = missing), then "because of your
  vision?", "Do you want training?", "How do you usually ...?"; the paper analyses question 1
  (p2). Developed by a modified Delphi process and validated by Rasch analysis with the Andrich
  rating scale model (p2).
- Administration time for all four questions: 25 to 35 minutes; interviewers trained with a
  written script and periodic scoring checks (p5).
- 285 subjects; Rasch with Winsteps; separation reliabilities reported (p5).
- DIF between pre- and post-rehabilitation for 7 of 48 items (two mobility, four reading, one
  distance-vision), small relative to the change in person measures (p1).
- Responsiveness: effect size 1.9 for inpatient BRC, 0.29 for outpatient programmes; no change
  in a test-retest control group before rehabilitation (p1).

**Szlyk et al. 2004 (ID 74).**
- 117 participants (97 men, 20 women) in VA rehabilitation programmes (p1, p3); 48 items
  covering navigation, resolution, peripheral detection, finding and general function (p3);
  administered by telephone before admission (p5).
- Separation and reliability for the three subcomponents: S = 3.91, R = .94 (difficulty);
  S = 3.54, R = .93; S = 3.29, R = .92 (p7). Nine "ineffective" items identified (p7).

**Di Maggio et al. 2020 (ID 105), Italian version.**
- Forward-backward translation; 131 consecutive low-vision patients at three centres, mean VA
  0.91 logMAR, mostly AMD; interviews by trained psychologists (p1, p2).
- Alpha 0.98; median item-test 0.73 and item-rest 0.71 correlations; total and subscale scores
  (reading, visual motor, mobility, visual information) correlated with VA, reading acuity and
  reading speed; best correlation with reading speed, Spearman 0.39-0.49 (p1). No a-priori
  hypotheses stated, so hypotheses testing rates "?" unless the review protocol supplies them.
- Classical analysis only (alpha and correlations); authors plan Rasch analysis of a revised
  version (p5).

**Babcock-Parziale et al. 2005 (ID 39), VA-13 self-report measure.**
- 13 items rated 1-3 for current ability, administered by telephone 4-6 weeks after discharge
  from a Blind Rehabilitation Center as a retrospective pretest and post-test (p2).
- Alpha 0.81 (retrospective pretest) and 0.76 (post-test); Rasch person reliability 0.71 and
  0.27, the latter judged poor (p6).

## IVI (Impact of Vision Impairment)

**Selivanova et al. 2019 (ID 72).**
- 109 low-vision patients completed the IVI and the NEI VFQ-25 before and after vision
  rehabilitation (p1). Questionnaires mailed two weeks before baseline to be completed alone
  or with help; post-rehabilitation copies sent 1 month after discharge; telephone
  administration offered to non-responders (p2).
- IVI: a total scale and three subscales, reading and accessing information, mobility and
  independence, emotional well-being; previously Rasch-validated in a low-vision population
  (p2).
- Effect sizes (Cohen d) after rehabilitation: IVI reading 0.50 (largest), IVI well-being 0.37,
  NEI VFQ-25 socioemotional 0.29; overall range 0.25-0.50 (p5-6). Authors note that such
  questionnaires "are generally lengthy to administer" (p6).

## Activity Inventory (AI)

**Massof et al. 2007 (ID 95).**
- AI used with 50 goal-level items; for each goal the patient rates importance (not / slightly /
  moderately / extremely), then, if important, difficulty (not difficult / slightly /
  moderately / very / impossible), then the tasks under that goal; administered by a trained
  interviewer by telephone before the first clinic visit (p2).
- Rasch analysis (Andrich rating scale) of the driving goal and tasks; person measure
  separation reliability 0.87; SE of person measures 0.17-1.83 logits (p4).

**Goldstein et al. 2012 (ID 12).** The AI, Telephone Interview for Cognitive Status, Geriatric
Depression Scale, SF-36 scales and EuroQoL were administered in one or two telephone interviews
before the first clinical examination; mean total interview time 62 minutes (p2).

**Malkin et al. 2013 (ID 88).** The filtered AI (only goals and tasks that LVR would target)
was the comparator for EQ-5D responsiveness; AI change scores showed moderate effect sizes for
functional domains and a large effect size for goal-level visual ability (p1).

## EQ-5D

**Malkin et al. 2013 (ID 88).**
- EQ-5D (US index) administered by telephone to 77 consecutive participants of a 764-patient
  usual-care LVR cohort at baseline and 6-9 months later (p3).
- Utilities correlated weakly with AI measures (best r = 0.48 with goal scores); baseline
  utilities skewed to the ceiling (median 0.77); effect size of change not different from zero;
  conclusion: unresponsive as an LVR outcome and poor at discriminating ability levels (p1).
- This is the EQ-5D without the vision bolt-on; no included paper tests the bolt-on.

## APEDS-VFQ

**Gothwal & Bagga 2012 (ID 5).**
- 16 items, framing question "How much difficulty do you have in ...", 0 (no difficulty) to 4
  (cannot manage); administered face-to-face by trained interviewers to 351 visually impaired
  adults (better-eye VA < 20/60, or >= 20/60 with restricted fields) at LV Prasad rehabilitation
  centres, before any examination (p1, p2).
- Rasch: response categories collapsed from five to three; one item ("reading small prints in
  newspaper/magazines", infit 1.54) misfit; overall fit pattern suggested the construct is not
  unidimensional; items grouped into four functional subsets (resolution, contrast sensitivity,
  illumination, peripheral vision), after which the first principal component explained 72% of
  variance; item separation reliability 0.99 (18 strata); person separation reliability 0.81
  (three strata) (p1). Infit 0.7-1.3 used as the fit criterion (p3).
- Relevance for glaucoma: the only instrument in the set whose items are explicitly organised
  by contrast and peripheral-field demand.

## GAL-9 (and GQL-15)

**Agathos et al. 2025 (ID 55).**
- Used the nine GAL-9 activity-scenario questions with a 5-point Likert difficulty scale in
  patients with maculopathy, chosen "given its focus on mobility scenarios ... and its short
  length, key consideration for an in-consultation screening tool"; developed for peripheral
  vision loss (p5).
- GAL-9 total score rose with vision-loss severity and was predicted by contrast sensitivity,
  female sex and scotoma size (p2). No measurement-property statistics for the GAL-9 itself;
  the paper is a use, not a validation.
- The GQL-15 is not reported by any text in the folder beyond citations.

## 100-item Visual Acuity Survey and the two-item screen

**Wu et al. 2026 (ID 92; duplicate text in `Anchor article.txt`).**
- Participants 18+, English-speaking, with measured binocular habitual-correction VA from -0.3
  to 2.0 logMAR (mean 0.58 +/- 0.44), recruited to span the acuity range; VA from Bailey-Lovie,
  ETDRS or Snellen charts (p2). n = 385 (data-extraction template, Table 1).
- The survey asks yes/no about recognising details of everyday objects at specific distances;
  items were generated by the team, piloted informally and refined; the full list is in the
  supplement and the 2024 development paper (p2).
- Prior IRT work: five items with suboptimal fit, overall "good reliability"; the linear
  relation between IRT item difficulty and logMAR was used to assign each item a VA threshold
  (p3).
- Single-item screens: "In a fast-food restaurant, can you usually read the posted menus?"
  AUC 0.85, sensitivity 0.89, specificity 0.81 for low vision (0.3 logMAR); "When seated in
  front of a computer, are you able to read the letters on the keyboard keys?" AUC 0.80,
  sensitivity 0.89, specificity 0.71 for legal blindness (1.0 logMAR); a second item adds at
  most 0.05 AUC, a third nothing (p1, p4). The AUC of a single yes/no item is
  (sensitivity + specificity) / 2, not a ROC area (p3).
- The 20 best items, pairs and triplets were selected by AUC in the same sample (p3): data-driven
  selection, so QUADAS-2 D2 is High and the estimates are optimistic until validated elsewhere.
- Background (p2): published single-question screens reach sensitivity 0.70 / specificity 0.88
  (legal blindness) and sensitivity 0.25 / specificity 0.92 or 0.20 / 0.97 for milder
  impairment, i.e. high specificity and poor sensitivity.

## Self-reported mobility questionnaire

**Bibby et al. 2007 (ID 120).** Row already in the data-extraction templates: 35 items, 1-5
difficulty, verbal administration, Rasch person measure, person reliability 0.93 (p6),
correlation 0.41 with high-contrast VA and -0.76 with binocular visual field (Table 2, p4). The
field correlation is the strongest field signal in the set and is worth citing in the glaucoma
feasibility column.
