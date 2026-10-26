# Validation of the narrative-synthesis scripts

All checks were run on a synthetic study set (eight studies: the Wu 2024 / Wu 2026 overlapping
pair with cross-reference, identical n = 385, five shared surnames and the same recruitment
window; five independent single-question vs VA studies at one threshold; one VFQ-25 study
with two thresholds and a separate ROC AUC), built in a scratch directory, not in the repo.
The same files are the inputs of the eval cases under `evals/`.

## independent_datasets.py

| Check | Expected | Obtained |
|---|---|---|
| Wu 2026 / Wu 2024 pair | one dataset, confidence high, reasons: cross-ref, 5 shared surnames (Jaccard 0.83), identical n, years overlap, same site | as expected (D07) |
| Five single-question studies with distinct authors, n, countries | each its own dataset | 7 datasets from 8 studies |
| `--merge possible` on the same set | no additional merges (no author overlap elsewhere) | 7 datasets |
| Re-run on the `--assign` copy (dataset_id filled) | existing ids kept, confidence "reviewer", no conflicts | 8 rows marked reviewer |
| Missing input file | exit 1 with message | exit 1 |
| Determinism | identical outputs on re-run | identical |

Surname parsing was checked on "Wu YH, Yu D, Goldstein JE, Kwon M, Wang C, Legge GE" and
"Wu YH, Legge GE, Yu D, Goldstein JE, Kwon M" (intersection = 5, union = 6).

## accuracy_table.py

Wilson 95% intervals are imported from data-extraction's `reconstruct_2x2.py` and were
cross-checked against an independent implementation, `scipy.stats.binomtest(x, n)
.proportion_ci(method="wilson")`:

| x / n | script | scipy |
|---|---|---|
| 66 / 80 (Smith sens) | 0.7274-0.8928 | 0.7274-0.8928 |
| 28 / 40 (Garcia sens, back-calculated from 0.70 x 40) | 0.5457-0.8193 | 0.5457-0.8193 |
| 243 / 270 (Garcia spec, back-calculated from 0.90 x 270) | 0.8584-0.9304 | 0.8584-0.9304 |

Hand check of 66/80 with the closed form (z = 1.96): centre 0.8102, half-width 0.0827 ->
0.7275-0.8929 (rounding of z). Reported CIs (Lee 2018: 0.62-0.86) are kept, not replaced.
The back-calculated rows carry the "approx" flag (†). The Wu 2026 "AUC" of 0.85 with sens
0.89 and spec 0.81 is flagged § as (sens+spec)/2. The Nguyen AUC with CI is pulled from
effects.csv (‡) for both threshold rows. Group verdicts: VFQ-25 vs clinician judgement = 1
dataset -> present as-is; single question vs VA = 7 reports, 6 datasets over 2 threshold
definitions, largest comparable subset 5 datasets -> candidate for dta-meta-analysis.
QUADAS-2 overall: Smith Low, Lee Unclear (D2 U), Patel High (D2 N), Wu 2026 High, others
"not assessed". Forest and ROC figures were opened and checked for label collisions; SVG
and PNG are byte-identical across runs.

## evidence_map.py

| Check | Expected | Obtained |
|---|---|---|
| dta map, single question x VA | k = 6 (Wu pair counted once), n = 1482 = 385 + 202 + 160 + 310 + 250 + 175 | k = 6, n = 1482 |
| effects map, single question x VA correlation | k = 4, n = 787 | k = 4, n = 787 |
| Direction with `direction = flip` (Patel r = -0.35, CI -0.45 to -0.24) | positive | ▲ positive, moderate |
| Lee r = 0.12, CI -0.04 to 0.27 | null (CI includes 0) | ◄► null, small |
| Brown r = 0.31, no CI | positive by trivial-band rule | ▲ positive, moderate |
| Vote count 3 positive, 0 negative, 1 null | exact sign test p = 2 x 0.5^3 = 0.25 | p = 0.250 |
| Proportion row (completion rate) | listed under "not plotted" | listed |
| Size classes | r 0.45 moderate (0.3-0.5), AUC 0.82 moderate (0.8-0.9) | as expected |

Harvest plot checked visually: bars placed by direction, heights by class, colours and
hatches by QUADAS-2 overall, legend present.

## Not verified

- No published worked example of a SWiM synthesis has numeric outputs to reproduce; the
  checks above are internal consistency, cross-implementation (Wilson) and hand calculation.
- Surname parsing was tested on the "Surname Initials" form used by the Screening export and
  on "Surname, I.; Surname, I."; unusual formats (particles such as "van der", hyphenated
  initials) may need an `authors` column written by hand.
- Label placement in the ROC scatter is heuristic; with more than ~12 points in one corner,
  some labels will still touch. Check the PNG.
