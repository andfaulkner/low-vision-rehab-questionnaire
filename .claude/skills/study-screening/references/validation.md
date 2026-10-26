# Validation: what was tested and the numbers obtained

All runs were made on 2026-10-26 against a copy of
`data/LVR_screening_sheet_2.xlsx` in a scratch directory (the repository's
workbook and exports were never written) and against the CSV export of that
copy. The committed `data/LVR_screening_sheet_2_Screening.csv` was stale at
the time (128 records against 135 in the workbook), which is why the scripts
read the xlsx by default.

## agreement.py against a hand-computed 2x2

Reviewer's `Title/abstract decision` (H) vs `Suggested decision (AI)` (N),
40 records decided on both sides, Maybe collapsed to Include. The raw
cross-tabulation read off the sheet:

| H \ N | Include | Exclude | Maybe |
|---|---:|---:|---:|
| Include | 1 | 0 | 3 |
| Exclude | 3 | 23 | 1 |
| Maybe | 2 | 6 | 1 |

Collapsed: a = 7 (both Include/Maybe), b = 6 (reviewer in, AI out), c = 4
(reviewer out, AI in), d = 23.

Hand computation:
- p_o = (7 + 23) / 40 = 0.75
- p_e = (13 x 11 + 27 x 29) / 40^2 = (143 + 783) / 1600 = 0.57875
- kappa = (0.75 - 0.57875) / (1 - 0.57875) = 0.17125 / 0.42125 = 0.40653
- PABAK = 2 x 0.75 - 1 = 0.50
- SE (Fleiss-Cohen-Everitt 1969, written in its kappa form, evaluated
  separately from the script's p_o/p_e form): 0.15546; 95% CI 0.1018 to 0.7112

Script output (`agreement.py <copy>.xlsx --bootstrap 2000`):

| Statistic | Hand | Script |
|---|---:|---:|
| Observed agreement | 0.750 | 0.750 (30/40) |
| Expected | 0.57875 | 0.579 |
| kappa | 0.40653 | 0.407 |
| SE | 0.15546 | 0.155 |
| 95% CI | 0.1018 to 0.7112 | 0.102 to 0.711 |
| PABAK | 0.500 | 0.500 |
| Bootstrap 95% CI (2000 resamples, seed 20261004) | - | 0.079 to 0.696 |

The asymptotic and bootstrap intervals agree to about 0.02 at each end, as
expected for n = 40 with no empty cell. The 3x3 run (`--maybe-as separate`)
gives observed agreement 25/40 = 0.625, which equals the Counts tab's "Rows
where you agreed with the AI" (25), kappa 0.198 (95% CI -0.014 to 0.410),
PABAK 0.438. `--maybe-as exclude` gives 0.800 agreement, kappa 0.091,
PABAK 0.600: the low kappa with high agreement is the prevalence effect the
methods note describes (36 of 40 collapse to Exclude on the reviewer's side).

The two AI passes (`--a N --b Q --maybe-as separate`) agree on 104/127
(kappa 0.622, PABAK 0.728), 23 disagreements.

## Other checks

- Malformed strings: a CSV copy with `include` (wrong case) in H and
  `No questionnaire` (truncated) in I stops the script with exit 2, naming
  both records and the intended spelling of the first.
- `--b-file`: a five-row second-reviewer sheet joined on ID gives n = 5 paired,
  35 unpaired on the reviewer's side, and the expected two disagreements.
- `--stage ft`: a CSV copy with J set on three records vs an AI full-text CSV
  gives a 2x2 on 3 records (kappa 0.400, CI -0.368 to 1.000) and refuses
  Maybe.
- sample_records.py: `--fraction 0.2 --seed 7 --stratify "Suggested decision
  (AI)"` on the 135-record copy draws 27 records (blank 2, Exclude 18,
  Include 4, Maybe 3; largest-remainder allocation) and the same 27 IDs on a
  second run; `--pool ft --n 4 --seed 3` draws 4 of the 13 reviewer
  Include/Maybe records.
- sample_records.py `--retrieval` on the copy, with the repository's
  `data/articles` and `data/articles_text`: 13 reviewer Include/Maybe records,
  12 retrieved, 1 not retrieved (ID 30); by the second AI pass's column, 43
  records, 41 retrieved, 2 not retrieved (IDs 23, 30). Matching was done by
  the imported `included.py` functions.
- apply_decisions.py: dry run of four pass-2 decisions prints the 12 cells
  (Q/R/S of rows 129-132) and writes nothing; a CSV with a misspelt reason, a
  Maybe carrying a reason, an Exclude without one and a duplicate ID is
  refused with exit 2 and all four problems listed; `--target reviewer-ta`
  without `--reviewer` is refused with exit 2; `--apply --export --out
  <scratch>.xlsx` writes Q129:S132 (verified by reading the copy with
  openpyxl read-only), leaves H empty, keeps the Counts cache correct and
  regenerates the four CSVs beside the output.

## Not verified

- No published worked example of the Fleiss-Cohen-Everitt SE with its
  numbers was reproduced; the check is the independent algebraic form plus
  the bootstrap. If a textbook example is to hand (Fleiss, Levin and Paik
  2003, section 18.2), run `agreement.py` on it and add the numbers here.
- The subagent briefs were not executed against live subagents in this
  session; the examples in `references/examples.md` were written by hand
  from the rules.
