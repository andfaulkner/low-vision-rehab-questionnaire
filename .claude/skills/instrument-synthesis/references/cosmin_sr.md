# The COSMIN systematic-review procedure for PROMs, in brief

Source: Prinsen CAC, Mokkink LB, Bouter LM, Alonso J, Patrick DL, de Vet HCW, Terwee CB.
COSMIN guideline for systematic reviews of patient-reported outcome measures. Qual Life Res
2018;27:1147-1157 (doi:10.1007/s11136-018-1798-3); the user manual (Mokkink et al. 2018,
www.cosmin.nl) has the full wording. The 10 steps fall into three parts.

## Part A: literature search

1. **Formulate the aim**: construct (here, self-reported visual ability / vision-related
   activity limitation / vision-related quality of life, and the acuity-recognition construct
   of the Legge survey), target population (adults seen in eye clinics, with glaucoma as a
   subgroup of interest), type of instrument (self-report questionnaire or single screening
   item), and the measurement properties of interest.
2. **Eligibility criteria**: studies whose aim is to evaluate one or more measurement properties
   of an eligible instrument in the target population (development studies count; studies that
   only *use* an instrument as an outcome do not, unless they report a property such as
   responsiveness).
3. **Search**: usually a dedicated PROM-measurement-property filter (Terwee 2009). This review's
   search was built around diagnostic accuracy, so say in Limitations that COSMIN-type
   validation studies were captured only incidentally, and consider a supplementary search per
   instrument before claiming "no evidence".
4. **Select**: screening-workbook skill.

## Part B: evaluate the measurement properties

5. **Content validity** (PROM development and content validity, boxes 1-2) first, using the
   COSMIN content-validity guideline (Terwee 2018). An instrument with insufficient content
   validity is usually dropped from recommendation regardless of its other properties.
6. **Structural validity, internal consistency, cross-cultural validity** (boxes 3-5): internal
   structure.
7. **Reliability, measurement error, criterion validity, hypotheses testing, responsiveness**
   (boxes 6-10): the remaining properties.
   For steps 6-7, each study x property gets (a) a risk-of-bias rating with the COSMIN RoB
   checklist (worst score counts; risk-of-bias skill), (b) a rating of the *result* against the
   criteria for good measurement properties (`assets/criteria_good_measurement_properties.md`;
   `scripts/rate_properties.py`).

## Part C: summarise, grade, recommend

8. **Summarise per instrument x property across studies**: pool or qualitatively summarise the
   results, then rate the summary (+, -, +-, ?). Pooling of alphas, ICCs or correlations is
   allowed when the studies are similar; with 1-3 heterogeneous studies a range and a narrative
   is the honest option (`rate_properties.py` gives an n-weighted mean labelled descriptive and
   never calls it a meta-analysis; use the effect-size-meta-analysis skill for a real pooled
   correlation).
9. **Grade the quality of the summarised evidence** with the modified GRADE approach below.
10. **Formulate recommendations**: category A (sufficient content validity *and* at least
    low-quality evidence for sufficient internal consistency: can be recommended); category B
    (everything between A and C: promising, needs more research); category C (high-quality
    evidence for an insufficient property: not recommended). Report with PRISMA (prisma-reporting
    skill) and state that AI assistance was used and how it was checked.

## Modified GRADE rule set used by rate_properties.py

Prinsen 2018, Table 4. Start at **High** and downgrade per summarised result; levels High,
Moderate, Low, Very low. Indeterminate ("?") summaries are not graded.

| Factor | -1 serious | -2 very serious | -3 extremely serious |
|---|---|---|---|
| Risk of bias (COSMIN RoB of the contributing studies) | multiple studies of doubtful quality, *or* only one study of adequate quality | multiple studies of inadequate quality, *or* only one study of doubtful quality | only one study of inadequate quality |
| Inconsistency | unexplained inconsistency across studies | (reviewer may deepen to -2 by hand) | |
| Imprecision | total n of the contributing studies 50-100 | total n < 50 | |
| Indirectness | evidence from other populations or an inappropriate study design for the review question | | |

Script conventions (state them in Methods):

- Only studies whose result is "+" or "-" contribute to k, total n and the risk-of-bias count.
- Risk of bias: with >= 2 studies rated Very good or Adequate there is no downgrade, whatever
  the rest; exactly one Very good/Adequate study -> -1; none, but >= 2 Doubtful -> -1; one
  Doubtful -> -2; >= 2 Inadequate -> -2; a single Inadequate -> -3. Studies without a RoB rating
  are listed as "unrated" and ignored in the count; if no study is rated the certainty carries
  "(RoB not applied)".
- Inconsistency: -1 whenever "+" and "-" results coexist, including when `--majority` turned
  the mixture into a single rating.
- Indirectness: 0 unless the reviewer passes `--indirectness "<instrument>=serious"` (for
  example a questionnaire validated only in AMD when the question is about glaucoma).
- Imprecision uses the sum of the contributing n; a study with n = NR counts as 0 and is
  listed, so the reviewer sees the gap.

## When the COSMIN path is the wrong tool

- The paper asks "does a question identify people with VA worse than X?" and reports
  sensitivity/specificity: that is diagnostic accuracy. Use QUADAS-2 (risk-of-bias skill) and
  present or pool it with the dta-meta-analysis skill. COSMIN criterion validity can still take
  the AUC if the review treats the reference standard as a gold standard, but say so once.
- Observed-performance measures (MLVAI Part A) are not PROMs; COSMIN's PROM criteria apply to
  the self-report part only.
- Guidelines (ESO, Dutch multidisciplinary) go to AGREE II, not COSMIN.
- A development paper with no measurement properties beyond item generation only contributes to
  content validity (step 5), which this skill records narratively in `instrument_notes.md`
  rather than scoring.

## Other citations

- Mokkink LB, de Vet HCW, Prinsen CAC, et al. COSMIN Risk of Bias checklist for systematic
  reviews of PROMs. Qual Life Res 2018;27:1171-1179.
- Terwee CB, Prinsen CAC, Chiarotto A, et al. COSMIN methodology for evaluating the content
  validity of PROMs: a Delphi study. Qual Life Res 2018;27:1159-1170.
- Terwee CB, Bot SDM, de Boer MR, et al. Quality criteria were proposed for measurement
  properties of health status questionnaires. J Clin Epidemiol 2007;60:34-42 (origin of the
  0.70 and 75% thresholds).
- Terwee CB, Jansma EP, Riphagen II, de Vet HCW. Development of a methodological PubMed search
  filter for finding studies on measurement properties of measurement instruments. Qual Life
  Res 2009;18:1115-1123.
- Mokkink LB, Terwee CB, Patrick DL, et al. The COSMIN taxonomy of measurement properties.
  J Clin Epidemiol 2010;63:737-745.
- Campbell M, McKenzie JE, Sowden A, et al. Synthesis without meta-analysis (SWiM) in
  systematic reviews: reporting guideline. BMJ 2020;368:l6890 (for the narrative synthesis
  that this review will use for its primary question).
- Guyatt GH, Oxman AD, Vist GE, et al. GRADE: an emerging consensus on rating quality of
  evidence and strength of recommendations. BMJ 2008;336:924-926.
