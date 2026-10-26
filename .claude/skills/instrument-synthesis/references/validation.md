# Validation of the scripts

There is no published numerical worked example of the COSMIN rating step (the criteria are
threshold rules, not an estimator), so validation is by hand-derived expectations on synthetic
data plus a run on real facts from three instruments in `data/articles_text/`. Both input files
live in the eval cases (`evals/rate-synthetic-properties/files/`,
`evals/glaucoma-feasibility-table/files/`) and can be re-run at any time.

## rate_properties.py on synthetic results (5 studies, 2 instruments, 19 rows)

Expected ratings were written down from Prinsen 2018 Table 1 and Table 4 before the script
ran; obtained values are from the run on 2026-10-26.

| Study x instrument x property | Input | Expected | Obtained |
|---|---|---|---|
| S1 VFQ-X structural validity (Rasch) | infit 0.7-1.3, residual r 0.15, unidimensional yes, monotonic yes | + (all four aspects) | + |
| S3 VFQ-X structural validity | EFA only | ? | ? |
| S1 VFQ-X internal consistency | alpha 0.91, structural + available | + | + |
| S2 VFQ-X internal consistency | person separation index 2.3 -> reliability 0.84 | + | + (derivation written: 2.3 -> 0.84) |
| S1 VFQ-X reliability | ICC 0.85 | + | + |
| S3 VFQ-X reliability | ICC 0.62 | - | - |
| S2 VFQ-X reliability | Pearson test-retest 0.86 | ? | ? |
| S1 VFQ-X hypotheses testing | r 0.45 vs >= 0.30 (yes); r -0.20 vs abs >= 0.30 (no); known groups confirmed | 2/3 = 67% -> - | - |
| S4 SHORT-Q internal consistency | alpha 0.82, no structural evidence | ? | ? |
| S4 / S5 SHORT-Q criterion validity | AUC 0.78; r 0.81 | + / + | + / + |
| S4 SHORT-Q measurement error | SDC 4.2, MIC 5 | + | + |
| S5 SHORT-Q responsiveness | effect size 0.6, no hypothesis | ? | ? |
| S2 VFQ-X cross-cultural validity | McFadden R2 0.01 | + | + |

Summary and modified GRADE (RoB from the synthetic `cosmin_ratings.csv`):

| Instrument x property | k, total n (definitive studies) | Expected summary / certainty | Obtained |
|---|---|---|---|
| VFQ-X structural validity | 1 of 2 definitive, n 200 | + ; RoB -1 (one Very good study) -> Moderate | + ; Moderate |
| VFQ-X internal consistency | 2, n 320 | + ; Very good + Adequate -> no downgrade -> High | + ; High |
| VFQ-X reliability | 2 definitive (+, -), n 105 | +- ; inconsistency -1, RoB -1 (one Adequate) -> Low | +- ; Low |
| VFQ-X hypotheses testing | 1, n 200 | - ; RoB -1 -> Moderate | - ; Moderate |
| SHORT-Q internal consistency | indeterminate | not graded | not graded |
| SHORT-Q criterion validity | 2, n 70 | + ; RoB -1 (one Adequate), imprecision -1 -> Low | + ; Low |
| SHORT-Q measurement error | 1, n 40 | + ; RoB -2 (one Doubtful), imprecision -2 -> Very low | + ; Very low |
| SHORT-Q responsiveness | indeterminate | not graded | not graded |
| VFQ-X cross-cultural validity | 1, n 120 | + ; RoB -1 -> Moderate | + ; Moderate |

All 23 expectations matched. A malformed file (misspelled property, non-numeric n) exits 1
with both errors listed; a row with an extra unquoted comma exits with the line number.

## rate_properties.py on real facts (LVQOL, VA LV VFQ-48, APEDS-VFQ; 15 rows from the texts)

Inputs are the page-cited facts in `references/instrument_notes.md`. Obtained, with
`--structural-ok "VA LV VFQ-48"` (asserting the Stelmack 2004 Rasch development paper, which is
not in the folder) and no RoB file:

- LVQOL: structural validity ? (EFA only, Wolffsohn 2000); internal consistency ? in both
  studies (no structural evidence); reliability + (ICC 0.72, Wolffsohn) and ? (Spearman 0.864,
  Perez-Mana) -> summary + from the one definitive study, n 150, "High (RoB not applied)";
  hypotheses testing + (known groups, reviewer-confirmed); criterion validity ? (AUC NR).
- VA LV VFQ-48: internal consistency + in Szlyk 2004 (PSR 0.94) and Di Maggio 2020 (alpha 0.98)
  -> + , k 2, n 248; hypotheses testing ? (no hypotheses); responsiveness ? (effect size 1.9
  without a hypothesis); cross-cultural validity ? (7/48 DIF items, reviewer to judge).
- APEDS-VFQ: structural validity - (infit up to 1.54; authors report non-unidimensionality);
  internal consistency ? because the structural precondition failed, although PSR is 0.81.

These are the behaviours the criteria require; the reviewer should expect to supply
protocol hypotheses and the development-paper Rasch evidence to move "?" ratings.

## instrument_table.py

Run on the 19-row catalogue, the data-extraction `instruments.csv` and `studies.csv`
templates, the real `summary_of_findings.csv` above and `feasibility_template.csv` with
`--for glaucoma`: 19 instruments written, all 19 daggered (none verified), 11 catalogue cells
overridden by extracted values (all for the two instruments the templates contain, listed on
stdout), k = 1 for the 100-item survey and the Bibby questionnaire, k = 0 elsewhere, the two
glaucoma columns appended to both tables, the COSMIN cell filled for the three rated
instruments. `--included-only` with `--columns` reduced the output to the two extracted
instruments; `--only` with unknown rated instruments added bare rows with a warning; a missing
file exits 2. All three asset CSVs parse with a constant field count.

## Not verified

- Catalogue facts (items, minutes, languages, DOIs, PMIDs, licences) are compiled from memory
  of the development papers and are marked `verified = no`; `uncertain_fields` lists the cells
  most likely to be wrong. They must be checked before any number is quoted.
- The 75% majority rule (`--majority`) and the person-separation conversion are conventions,
  flagged as such in the criteria file; COSMIN leaves both to the reviewer.
- No live network call is made by either script, so nothing here depends on Crossref or
  PubMed availability.
