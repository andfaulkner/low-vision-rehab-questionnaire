# Validation of the scripts

All runs with `python3 -I` (Python 3.15, standard library only), 2026-10-25.

## reconstruct_2x2.py

**Real paper, Wu 2026 (Screening ID 92), Q97 "fast-food menus", low-vision threshold.**
Inputs read from the text: N = 385 (Table 1 p3); 121 participants better than 20/40, so
n_positive = 264; sens 0.89, spec 0.81, "AUC" 0.85 (Table 2 p4, Results p5).

| quantity | expected (by hand) | obtained |
|---|---|---|
| TP | 0.89 x 264 = 234.96 -> 235; 234-236 all round to 0.89 | 235, alternatives 234 and 236 flagged |
| TN | 0.81 x 121 = 98.01 -> 98 | 98 |
| FP, FN | 23, 29 | 23, 29 |
| (sens + spec) / 2 | 0.85 (the paper's single-point "AUC") | 0.8500 |
| LR+ | 0.8902 / 0.1901 = 4.68 | 4.683 (3.234 to 6.781) |
| DOR | (235 x 98) / (23 x 29) = 34.5 | 34.53 |

**Wu 2026, Q30 "keyboard keys", legal-blindness threshold.** n_positive = 50 + 23 = 73,
sens 0.89, spec 0.71. Expected TP = 65 (65/73 = 0.890), TN = 221.5, so 221 and 222 both
reproduce 0.71 (0.7083, 0.7115). Obtained 65/90/8/222 with FP 89-92 / TN 220-223 listed
as alternatives. This is the ambiguity the script is meant to surface.

**Wilson intervals.** 0/20 gives an upper limit of z^2 / (n + z^2) = 3.8415 / 23.8415 =
0.1611 algebraically; obtained 0.8389-1.0000 for a specificity of 20/20, i.e. 1 - 0.1611.
81/263 gives 0.2553-0.3662, which matches the Wilson entry for that example in Newcombe
(1998, Statistics in Medicine 17:857-872, Table I) as remembered; the Wald interval for
the same data is 0.252-0.364 and the exact interval 0.253-0.367, so the obtained limits
are at least in the right place between them. 7/10 gives 0.3968-0.8922, matching the
hand calculation of the closed form.

**PPV route.** n = 200, sens 0.80, spec 0.90, PPV 0.667: Bayes gives prevalence 0.20,
so 40 positives, TP = 32, FP = 16, TN = 144, FN = 8. Obtained exactly that.

**Inconsistency detection.** 235/23/29/98 with sens claimed as 0.95: flagged
INCONSISTENT, "nearest table gives 0.8902". A dta.csv row with n = 385 and n_positive =
400 was flagged with "reported n=385 but nearest table gives 400".

**CSV mode.** On a 7-row synthetic dta.csv: rows with sens/spec/n/n_positive were filled
(TP..TN, prevalence, PPV, NPV, Wilson CIs) and the derivation column got the arithmetic
and the alternatives; a row with the four counts and matching sens/spec was verified and
only its blank derived cells filled; a row with sens 1.2 was flagged; a row with sens/spec
only was reported as insufficient and left untouched; a row with a reported CI but no n
was left untouched (CI-based estimation is CLI-only and labelled approximate).

Unverified: the LR and DOR confidence limits were checked only for internal consistency
(log method, Simel 1991 / Woolf), not against a published table.

## validate_extraction.py

The four `assets/` templates validate with 0 errors and 0 warnings (one INFO: the Wu
2026 "AUC" equals (sens + spec) / 2). A synthetic 6-study set with deliberate faults
produced exactly the expected errors: n_analysed > n_enrolled; TP+FP+FN+TN != n; sens =
1.2 out of range and not matching TP/(TP+FN); missing page; duplicate key; TP + FN !=
n_positive; study_id absent from studies.csv; sens outside its CI; correlation -1.3 out
of range; proportion not equal to events/n; plus warnings for a validation_method token
outside the list and for study_ids absent from the Screening sheet. Study IDs 92 and 120
matched the Screening sheet and their citation surnames. The readiness report counted
k = 4 for the single-question x VA 20/40 group and called the bivariate fit possible,
and k = 1 for the rest.

## reconcile.py

Pass A (3 rows) vs pass B (2 rows) of the Wu 2026 rows: matched 2 rows even though one
item text differed by a comma, listed the row only in A, and reported 4 cell
disagreements (prevalence 0.6857 vs 0.69, FP 90 vs 91, TN 222 vs 221, derivation text),
40/44 cells agreeing; exit status 2. The disagreement CSV has empty
`resolved_value` / `resolved_by` columns for the reviewer.
