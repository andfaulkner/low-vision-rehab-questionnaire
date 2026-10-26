---
name: data-extraction
description: Extract study characteristics and outcome data (2x2 counts, sensitivity/specificity, AUC, correlations, time to administer, instrument facts) from the included full-text articles in data/articles_text/*.txt into auditable CSV evidence tables with page citations, reconstruct 2x2 tables from sens/spec/prevalence, validate the tables and reconcile two extraction passes. Use when asked to extract data, build an evidence or summary-of-findings table, pull sensitivity/specificity or 2x2 numbers from a paper, fill the data-extraction form, do dual extraction or reconcile extractions, check extraction for errors, or prepare input for dta-meta-analysis, effect-size-meta-analysis or quadas-2.
---

# Data extraction

Turn included papers into four CSVs that the meta-analysis skills read, with every
number traceable to a `[page N]` in the article text. Output goes to
`analysis/extraction/` (never `data/`). Schema: `references/schema.md`; templates with
one worked row each: `assets/*.csv`.

AI-assisted extraction is advisory. The reviewer verifies every pooled number against
the source page before it enters the manuscript, and the Methods section states that AI
assistance was used for extraction and how it was checked. Say this to the user whenever
you hand over extracted numbers.

## Workflow: one study per pass

1. **Find the study.** `study_id` is the Screening-sheet `ID` (column A of
   `data/LVR_screening_sheet_2_Screening.csv`). Confirm the full-text decision is
   Include before extracting; if the decision columns are still empty, say so and extract
   only what the user asks for.
2. **Read the .txt, not the PDF.** `data/articles_text/<Author> - <Year> - <Title>.txt`
   has one `[page N]` marker per page. Grep for the numbers first, then read around the
   hits with `Read` offsets. `sensitivity` also matches *contrast sensitivity*, so grep
   `specificity`, `AUC`, `ROC`, `cut-off|cutoff`, `correlat`, `Table` as well. Read the
   Methods for the reference-standard definition and the participants table for n.
3. **Fill the rows** (templates in `assets/`):
   - `studies.csv`: one row per study (design, n, age, diagnosis mix with % glaucoma,
     recruitment, instruments, administration mode, time to administer, language,
     unit of analysis, overlapping cohort).
   - `dta.csv`: one row per index test x threshold x reference standard x unit x
     subgroup. Copy the test threshold and the reference-standard definition verbatim
     (which eye, presenting vs best-corrected, "worse than" vs "or worse"), then add
     `ref_threshold_logmar` from the table in `references/pitfalls.md`.
   - `effects.csv`: correlations, true ROC AUCs, proportions, means, mean differences.
   - `instruments.csv`: one row per instrument, shared across studies.
4. **Cite a page for every value.** `page` is required on every row. Write `NR` for
   anything the paper does not report. Never estimate, never take the abstract's rounded
   number over the table's, never borrow a value from another paper.
5. **Record derivations.** Anything computed goes in `derivation` with the arithmetic
   (`n_positive = 385 - 121 (Table 1 p3)`). Reported numbers get `reported directly
   (Table N)`.
6. **Reconstruct 2x2 tables** when the paper gives sens/spec but not counts:
   ```bash
   python3 -I .claude/skills/data-extraction/scripts/reconstruct_2x2.py --n 385 --n-positive 264 --sens 0.89 --spec 0.81
   python3 -I .claude/skills/data-extraction/scripts/reconstruct_2x2.py --csv analysis/extraction/dta.csv --in-place
   ```
   It accepts any sufficient subset of n, n_positive, prevalence, sens, spec, PPV, NPV
   and the four cells, checks that integer counts reproduce every reported value at its
   printed precision, lists the alternative tables when rounding leaves more than one,
   flags INCONSISTENT when none fits, and prints sens/spec/PPV/NPV/LR+/LR-/DOR with
   Wilson or log CIs. In CSV mode it fills only blank or NR cells and appends what it did
   to `derivation`; reported values are never overwritten. An INCONSISTENT row means a
   misread (per eye vs per person, different denominators, wrong threshold): re-read the
   paper rather than forcing the numbers.
7. **Validate** before handing over:
   ```bash
   python3 -I .claude/skills/data-extraction/scripts/validate_extraction.py analysis/extraction --report analysis/extraction/readiness.md
   ```
   Errors (exit 1): wrong columns, impossible values (sens > 1, TP + FN != n_positive,
   estimate outside its CI), duplicate keys, missing pages, unknown study_ids. Warnings:
   IDs absent from the Screening sheet, instruments not in `instruments.csv`. The
   readiness section counts studies per instrument x reference standard x threshold and
   says whether a bivariate fit is even possible (k >= 4 with full 2x2) or whether the
   honest answer is "describe, do not pool". Expect the latter often: the included set is
   small and thresholds differ.

## Dual extraction and reconciliation

Two independent passes catch the column-alignment and denominator errors that one pass
reproduces confidently. Run pass A and pass B into `analysis/extraction/passA/` and
`passB/` (a human and a subagent, or two subagents that cannot see each other's work),
then:

```bash
python3 -I .claude/skills/data-extraction/scripts/reconcile.py analysis/extraction/passA/dta.csv analysis/extraction/passB/dta.csv --ignore notes --out analysis/extraction/disagreements_dta.csv
```

It matches rows on the schema key (ignoring case, whitespace and punctuation; fuzzy
match within a study for reworded item text), lists every cell that differs with both
values, rows present in only one pass, and per-column agreement. Exit 2 means there is
something to resolve. The reviewer settles each disagreement from the cited page and
records the choice in the `resolved_value` / `resolved_by` columns of the disagreement
file; the merged result becomes the master CSV. Precision-only differences (0.6857 vs
0.69) are resolved toward the paper's precision.

To extract with a subagent, send the brief in `references/subagent-brief.md`: one paper,
the file path, the schema, the output folder, the NR rule, `python3 -I` for the scripts,
and a 200-word report. Never let a subagent extract several papers in one context, and
never tell pass B what pass A found.

## What to read when

- `references/schema.md`: columns, allowed values, units, the NR convention, duplicate
  keys. Read before the first extraction.
- `references/pitfalls.md`: per-eye counts, threshold direction, multiple thresholds,
  reversed polarity, spectrum bias, reviews vs primary studies, overlapping cohorts,
  single-point "AUC", VA conversion table (logMAR / Snellen ft / m / decimal). Read
  before the first extraction and when a number looks wrong.
- `references/validation.md`: what the scripts were tested against and the numbers to
  expect.
- `references/subagent-brief.md`: the template brief for a one-paper subagent.

## Hand-off to the next skills

- `dta-meta-analysis` reads `dta.csv` (`study_id, label, TP, FP, FN, TN` plus
  `instrument`, `threshold`, `reference_standard` for choosing pooling units).
- `effect-size-meta-analysis` reads `effects.csv` (`study_id, label, outcome_type,
  estimate, ci_low, ci_high, se, n, n_pos, n_neg, events, sd, m1..n2`).
- `risk-of-bias` reads `studies.csv` (`study_id, n, label`) and uses `recruitment`,
  `design`, `ref_threshold` and `unit` to pre-fill QUADAS-2 signalling questions.
Tell the user which groups in the readiness report have enough studies, which do not,
and why, so the review can say "not pooled" with a reason instead of a forced estimate.
