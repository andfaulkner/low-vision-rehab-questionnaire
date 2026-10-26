# Extraction pitfalls seen in this literature

Read this once before the first paper and again whenever a number looks too good.

## 1. Per eye vs per person

Ophthalmology papers often count eyes. A 2x2 built on 200 eyes from 100 people has
correlated observations and roughly double the apparent precision. Record `unit = eye`,
never silently halve, and do not pool eye-level rows with person-level rows. Also note
which eye the reference standard uses: better eye (most VA definitions of impairment),
worse eye, or binocular. Wu 2026 used binocular VA, falling back to the better eye.

## 2. "20/40 or worse" is not "worse than 20/40"

The threshold direction changes who is positive. Copy the paper's wording into
`ref_threshold` verbatim, then add the logMAR number. Wu 2026 writes "VA <= 0.3 logMAR"
for low vision, which taken literally means 20/40 or *better*; Table 1 shows that
participants with VA 0.3 to < 0.6 logMAR were counted as low vision, so the operational
definition is "0.3 logMAR (20/40) or worse". Resolve such conflicts from the tables, say
so in `notes`, and never from the abstract alone.

## 3. Multiple thresholds, items and item sets

One paper can yield dozens of rows (Wu 2026: 100 items x 2 thresholds, plus pairs and
triplets). Extract every row the review question needs, one per combination, and let the
readiness report show which combinations have enough studies. For pooling, a study
contributes **one** row per instrument x reference standard group; choose by a rule
fixed in advance (the paper's primary or recommended cut-off), not by the best-looking
accuracy. Rows selected post hoc inflate pooled estimates.

## 4. Reversed polarity

For most difficulty items a "yes/no difficulty" answer is positive; for ability items
("can you read the menu?") the "No" answer is positive. Some scales score higher =
better (NEI VFQ-25), others higher = worse (IVI, Activity Inventory difficulty). Write the
positive direction in `threshold` ("answer No = positive", "composite < 70 = positive")
and keep the sign of correlations as reported. A negative r between a questionnaire
score and logMAR is the expected direction when higher score = better function.

## 5. Spectrum and prevalence inflation

Low-vision-clinic and research samples recruited to span the VA range have prevalences
of 50-70% (Wu 2026: 69% at 20/40). Sensitivity and specificity still transfer poorly
across spectra, and PPV/NPV do not transfer at all. Record `recruitment` and
`prevalence` so the readiness report and QUADAS-2 can judge applicability. Case-control
designs (known impaired vs known normal) are flagged in `design` and get a
high-risk-of-bias rating for patient selection.

## 6. Reviews are not primary studies

Chou 2009 (USPSTF) tabulates sensitivity and specificity of screening questions from
Hiller 1983, Eekhof 2000, Teh 2006 and McMurdo 1988. Do not enter those as study 93. Use
the review to find the primary papers, decide whether they are in scope, and extract
from the primary text; if a primary paper is unobtainable, a row may cite the review in
`derivation` ("as tabulated in Chou 2009 Table 5, p49") with `notes` saying the primary
source was not checked.

## 7. Overlapping cohorts

Wu 2024 (ID 128) and Wu 2026 (ID 92) analyse the same 385 participants. Fill `cohort` in
studies.csv so the meta-analysis takes one estimate per cohort, not per paper.

## 8. "AUC" from one threshold

A yes/no item has one operating point. Some papers still report an "AUC" equal to
(sens + spec) / 2 (Wu 2026, Methods). It is not a ROC area and must not be pooled with
ROC AUCs. The validator flags `auc == (sens + spec) / 2`; keep it in `dta.csv` with a note,
not in `effects.csv` as `outcome_type = auc`.

## 9. The CI tells you the denominator

When only sens with a CI is reported, `reconstruct_2x2.py --sens-ci LO,HI` estimates
`n_positive` from the Wald width. It is approximate (authors may have used Wilson or
exact intervals) and the output says so; use it to sanity-check a count read elsewhere in
the paper, and record the estimate as `~114` with the method in `derivation`.

## 10. Rounding does not uniquely fix the counts

sens 0.89 with 264 positives is reproduced by TP = 234, 235 or 236. The script picks the
nearest to the exact product and lists the alternatives; put the range in `derivation`.
If **no** integer table reproduces all reported values, something else is wrong:
different denominators (missing data per item), per-eye counts, or a misread threshold.
Do not force it; flag the row and read the paper again.

## 11. Grep traps

`sensitivity` matches *contrast sensitivity* in most of these papers; grep
`specificity`, `AUC`, `ROC`, `cut-off`, `cutoff`, `2 x 2`, `true positive` as well.
Tables extracted from PDFs are column-scrambled: the numbers in Wu 2026 Table 2 appear
as a run of values after the item list, so read the column headers (`AUC SEN SPE`) and
count positions, and cross-check against the Results text, which repeats the headline
numbers.

## 12. Minor differences that break a merge

Instrument names must match `instruments.csv` exactly (`NEI VFQ-25`, not `VFQ-25` in one
file and `NEI-VFQ 25` in another). `reconcile.py` ignores case, whitespace and
punctuation in keys, but the validator's instrument check is exact after lower-casing.

## 13. Presenting vs best-corrected acuity

Screening studies in older adults usually use presenting (habitual) VA because
uncorrected refractive error is what screening finds; clinic validation studies often use
best-corrected VA. These are different reference standards; say which in
`ref_threshold` and keep them in separate pooling groups if the question is LVR need
(best-corrected) rather than any impairment (presenting).

## 14. Visual acuity notation conversion

logMAR = log10(MAR); Snellen fraction = 1/MAR; decimal = 1/MAR. Metres and feet are the
same ratio (6/12 = 20/40). Round logMAR to 0.1 only when the chart line is a standard
line; keep the paper's own figure otherwise.

| logMAR | Snellen (ft) | Snellen (m) | decimal | MAR | common label |
|---|---|---|---|---|---|
| -0.3 | 20/10 | 6/3 | 2.0 | 0.5 | |
| -0.1 | 20/16 | 6/4.8 | 1.25 | 0.8 | |
| 0.0 | 20/20 | 6/6 | 1.0 | 1 | normal |
| 0.1 | 20/25 | 6/7.5 | 0.8 | 1.25 | |
| 0.2 | 20/32 | 6/9.5 | 0.63 | 1.6 | (20/30 is 0.18) |
| 0.3 | 20/40 | 6/12 | 0.5 | 2 | driving limit (many jurisdictions); USPSTF impairment threshold |
| 0.4 | 20/50 | 6/15 | 0.4 | 2.5 | |
| 0.5 | 20/63 | 6/19 | 0.32 | 3.2 | (20/60 is 0.48; WHO moderate VI starts at worse than 6/18, 0.48) |
| 0.6 | 20/80 | 6/24 | 0.25 | 4 | |
| 0.7 | 20/100 | 6/30 | 0.2 | 5 | |
| 0.8 | 20/125 | 6/38 | 0.16 | 6.3 | |
| 0.9 | 20/160 | 6/48 | 0.125 | 8 | |
| 1.0 | 20/200 | 6/60 | 0.1 | 10 | US legal blindness (20/200 or worse); WHO severe VI starts at worse than 6/60 |
| 1.3 | 20/400 | 6/120 | 0.05 | 20 | WHO blindness starts at worse than 3/60 (1.3) |
| 1.5 | 20/630 | 6/190 | 0.032 | 32 | |
| 2.0 | 20/2000 | 6/600 | 0.01 | 100 | counting fingers, roughly |

Snellen lines that are not on the logMAR ladder: 20/30 = 0.18, 20/60 = 0.48, 20/70 =
0.54, 20/300 = 1.18. Convert with `log10(denominator / numerator)` and keep two decimals.

Visual field: mean deviation (MD) in dB is negative for loss; "MD worse than -6 dB" means
MD < -6. Esterman binocular score is a percentage of points seen. Record exactly as
written; there is no conversion between them.

## 15. Time to administer

Report in minutes, as a mean or median with its spread, and say whether it includes
scoring. "Brief" without a number is `NR`.

## 16. Things AI extraction gets wrong more often than humans

Column alignment in scrambled tables; mixing n for the whole study with n for a
sub-analysis (Bibby 2007 reduced n for the low-contrast correlation); copying the
abstract's rounded number instead of the table's; treating "data not shown" as a value.
Every pooled number is traced back to its page by the reviewer before it enters the
manuscript, and the Methods state that AI-assisted extraction was used and verified.
