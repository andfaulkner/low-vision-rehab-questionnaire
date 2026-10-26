---
name: study-screening
description: Run and document AI-assisted study selection for the LVR questionnaire systematic review - title/abstract screening and full-text screening of the records in data/LVR_screening_sheet_2.xlsx with one subagent per record, writing AI decisions only to the grey AI columns (N-P, Q-S) and never to the reviewer's yellow H-L; measure reviewer-vs-AI and reviewer-vs-reviewer agreement (percent, Cohen's kappa with CI, PABAK, confusion matrix, disagreement list); draw a seeded second-reviewer verification sample; track which Include/Maybe records lack a PDF/.txt (PRISMA "reports not retrieved"); and produce the numbers and sentences the Methods and PRISMA flow need. Use when asked to screen records, "run the AI screen", "second pass", "screen the full texts", "which papers are in", "how much did the AI agree with me", "kappa", "inter-rater", "calibration round", "pick a sample for the second reviewer", "which full texts are missing", "write up the screening", or anything about Include/Exclude/Maybe decisions. Hands off to screening-workbook for the cell edits and to prisma-reporting for the flow diagram and Methods text.
---

# Study screening

Two stages, the same shape each time: an AI pass gives every record an advisory
decision, the reviewer makes the decision of record, and the gap between the two
is measured and reported. The workbook `data/LVR_screening_sheet_2.xlsx` holds
both, in different columns, and the Counts tab turns the reviewer's columns into
the PRISMA numbers. Keeping the two apart is what makes the review's "single
reviewer with an AI second screen" claim true, so:

- AI decisions go in **N-P** (first pass) or **Q-S** (second, independent pass),
  through `apply_decisions.py --target ai1|ai2`. Never in H-L.
- The reviewer's decisions go in **H-L**, only when the reviewer has stated
  them, through `apply_decisions.py --target reviewer-ta|reviewer-ft --reviewer`
  or `screening-workbook`'s `set_cells.py --reviewer`.
- Whatever the AI produced is disclosed in the Methods (PRISMA 2020 item 8:
  how many reviewers, independence, automation tools). The disclosure template
  is in `prisma-reporting/assets/methods_templates.md`.

Every script here is standard-library Python and runs as `python3 -I script.py`
(isolated mode; the scripts re-add their own folder and the screening-workbook
helper themselves). Outputs go under `analysis/screening/` (intermediate) and
feed `paper/` through prisma-reporting; nothing is written to `data/` except
workbook cells, and only through `set_cells.py`. Reading the workbook never
saves it (openpyxl would strip the drop-downs).

## Before screening: the rules and a calibration round

The criteria are on the Instructions tab, and `docs/AI_title_abstract_screening_rules.md`
turns them into tie-breakers (what counts as "evaluating the instrument", what
each of the 10 reasons covers, when Maybe is right; the brief adds an order of
precedence when several reasons apply). Read that file
before briefing any subagent, and `results/AI_strict_screening_rules.md` for the
stricter full-text variant an earlier pass used; `results/LVR_strict_screening.csv`
is that pass's output (Include/Exclude only, 29 includes). The reviewer's earlier
decisions in H-I (40 records today) are the best calibration material there is.

Run a calibration round before the full pass: screen 10-20 records that the
reviewer has already decided, compare with `agreement.py`, read every
disagreement, and tighten the rules file (not the subagent brief) where the AI
read a criterion differently. A rules change after calibration is normal and is
reported ("rules were refined on a pilot of 20 records"); a rules change midway
through the full pass is not, because then records were judged on different
thresholds. Cochrane Handbook 4.6 recommends exactly this pilot for human
screeners too.

## Stage 1: title and abstract

1. **Inputs.** `screening-workbook/scripts/xlsx_to_csv.py --check` first; if the
   export is stale, regenerate it, because the subagents read title and
   abstract from the CSV. Records with "Missing" in Abstract are screened on the
   title alone and default to Maybe when the title is plausibly relevant.
2. **One subagent per record**, sonnet at medium effort or above (never haiku,
   never low), in parallel batches. Fill `references/subagent-brief.md` with the
   record's ID, title, abstract (and nothing else: not the AI columns, not the
   reviewer's decision, not other records), the rules file path and the exact
   Lists strings. The subagent returns one CSV line:
   `ID,decision,reason,rationale`. A narrow brief is the point: a subagent that
   sees other decisions anchors on them, and one that sees ten records drifts
   between them.
3. **Collect** the lines into `analysis/screening/ta_ai_pass2.csv` (header
   `id,decision,reason,rationale`), then validate and write:

   ```bash
   python3 -I .claude/skills/study-screening/scripts/apply_decisions.py analysis/screening/ta_ai_pass2.csv --target ai2          # dry run: prints every cell
   python3 -I .claude/skills/study-screening/scripts/apply_decisions.py analysis/screening/ta_ai_pass2.csv --target ai2 --apply --export
   ```

   The dry run is the default on purpose: it validates against the Lists tab
   (exact spelling, exactly one reason for Exclude, none for Include/Maybe, no
   Maybe at full text, IDs exist, no duplicates) and shows the plan. Fix the CSV
   until it is clean; `--apply` writes through `set_cells.py`, which recomputes
   the Counts cache, and `--export` refreshes the CSVs. `--target ai1` fills N-P
   instead; use it when N-P are empty (records 128-135 today) or when the
   reviewer asks for the first-pass columns to be redone.
4. **The reviewer decides.** They read each record with the AI suggestion
   beside it and fill H (and I for an Exclude) in Excel, or dictate decisions
   that you record with `--target reviewer-ta --reviewer`. Include and Maybe
   both go to full text; Maybe is for "relevant instrument, evaluation unclear
   from the abstract" and is resolved at full text, never carried into J.
5. **Measure** as soon as the reviewer has decided a batch (see Agreement).

## Stage 2: full text

1. **What goes forward**: `screening-workbook/scripts/included.py --stage ta`
   (reviewer's Include + Maybe, with the matched `.txt`). Only H decides this;
   if H is incomplete, say so and do not substitute N or Q.
2. **Retrieval tracking** feeds the PRISMA "reports sought / not retrieved"
   boxes:

   ```bash
   python3 -I .claude/skills/study-screening/scripts/sample_records.py --retrieval -o analysis/screening/retrieval.csv
   ```

   Status per record: `retrieved` (PDF and `.txt`), `text-missing` (PDF only:
   run the pdf-to-text skill), `not-retrieved` (neither: look for the PDF, ask
   the reviewer, or record `Full text not available` at FT). Matching is by
   first-author surname + year, imported from `included.py`. On the current
   sheet, record 30 (Stalin 2025, Optom Vis Sci) is the one reviewer
   Include/Maybe record with no file, record 23 (Potter 2024) has none either,
   and the files for 48 and 69 hold the wrong paper and supplementary tables
   only (see `results/AI_strict_screening_rules.md`); a matched file is not
   proof of the right content, so the full-text subagent reports a mismatch.
3. **One subagent per paper**, with the full-text brief in
   `references/subagent-brief.md`: it reads the `.txt` (grep first, then the
   relevant pages), decides Include or Exclude (no Maybe), picks exactly one
   reason, and quotes the sentence that decided it with its `[page N]`. The
   quote is what lets the reviewer check a decision in ten seconds and what
   turns a disagreement into something resolvable. The subagent returns
   `ID,decision,reason,rationale,quote`.
4. **Where AI full-text decisions live**: `analysis/screening/ft_ai_decisions.csv`,
   not the workbook, which has no AI full-text columns. Compare them with
   `agreement.py --stage ft --b-file`.
5. **The reviewer records J and K** for every Include/Maybe paper (`--target
   reviewer-ft --reviewer`, or Excel). Full-text exclusion reasons are the same
   10 strings; the ones that only make sense here are `Full text not
   available`, `Conference abstract only`, `Language (not English/French)`
   and `No accuracy/validation data` (the abstract promised data the paper does
   not report). "Studies included" on Counts is the count of J = Include.

## Agreement

```bash
python3 -I .claude/skills/study-screening/scripts/agreement.py -o analysis/screening --name ta_reviewer_vs_ai1              # H vs N, Maybe as Include
python3 -I .claude/skills/study-screening/scripts/agreement.py --a H --b Q --maybe-as separate -o analysis/screening       # reviewer vs second AI pass, 3x3
python3 -I .claude/skills/study-screening/scripts/agreement.py --a N --b Q -o analysis/screening --name ai1_vs_ai2         # the two AI passes
python3 -I .claude/skills/study-screening/scripts/agreement.py --b-file analysis/screening/second_reviewer_sample.csv \
    --b "Second reviewer decision" --b-reason "Second reviewer reason" -o analysis/screening --name ta_two_humans
python3 -I .claude/skills/study-screening/scripts/agreement.py --stage ft --b-file analysis/screening/ft_ai_decisions.csv \
    --b decision --b-reason reason -o analysis/screening --name ft_reviewer_vs_ai
```

It reads the xlsx (default) or a Screening CSV export, compares only records
decided on both sides, lists the unpaired ones, and stops with exit 2 on any
string not in the Lists tab (the Counts formulas would miss it just as
silently). Output per run: `<name>.md` (counts, confusion matrix, statistics,
disagreements with the reason on each side), `_summary.csv`, `_confusion.csv`,
`_disagreements.csv`. `--maybe-as include` is the PRISMA reading (Include and
Maybe both go to full text) and the default; `exclude` asks "did the AI lose
anything the reviewer kept"; `separate` keeps the 3x3 and asks whether the AI
hedges where the reviewer does; its observed-agreement count is the same
number as the Counts tab's "Rows where you agreed with the AI" (25 of 40
today), which compares H and N string for string.

Report percent agreement, kappa with its 95% CI, and PABAK together: with 27
Exclude to 13 Include/Maybe, kappa is dragged down by prevalence (Byrt 1993),
and the reviewer cares more about the AI's recall of their Includes (the "B
recall of A's Include" line) than about the chance-corrected summary. The
disagreement list is the deliverable for the calibration meeting; the kappa is
the sentence in the Methods. Bands (Landis and Koch 1977) are a convention,
not a threshold: `references/screening-methods.md` has them and the caveats.

## Second-reviewer verification sample

```bash
python3 -I .claude/skills/study-screening/scripts/sample_records.py --fraction 0.2 --seed 20261004 --stratify "Suggested decision (AI)" \
    -o analysis/screening/second_reviewer_sample.csv
python3 -I .claude/skills/study-screening/scripts/sample_records.py --pool ft --fraction 0.2 --seed 20261004 -o analysis/screening/ft_second_reviewer_sample.csv
```

The sheet is blind (bibliographic columns plus empty decision/reason/notes),
the seed and the ID list are printed for the Methods, and stratifying by the
AI decision keeps the rare Includes in the sample. The second reviewer screens
from title and abstract with the same Instructions tab, and `agreement.py
--b-file` gives the two-human kappa. Aim for 20% at title/abstract and all
Include/Maybe papers at full text if the second reviewer has time; the
evidence for why is below.

## What to report, and why

Single-reviewer screening misses studies: Gartlehner 2020 (crowd RCT, 2000
abstracts) found single screening missed 13% of relevant studies (sensitivity
86.6%) against 3% for dual screening, and Waffenschmidt 2019 (methodological
review) a median 5% missed, 3% for experienced reviewers and 13% for
inexperienced ones, with meta-analysis conclusions changed in 3 of 7 single
screenings by one inexperienced reviewer. An AI second screen plus a human
verification sample is the mitigation this review uses, and the Methods should
say so in those terms rather than claim dual review. The Methods paragraph
needs: one reviewer; the model name and version; the rules file; that
suggestions were recorded separately and every record was read and decided by
the reviewer; n and % of records where the reviewer's decision differed from
the suggestion (Counts rows "agreed with / changed the AI decision", or
`agreement.py`); the second reviewer's sample size, seed, and kappa; the
calibration round; and the full-text retrieval count. Then hand the numbers to
prisma-reporting (`prisma_flow.py` reads the Counts tab; `methods_templates.md`
has the paragraph with {placeholders}).

## Files

- `scripts/agreement.py`: two decision columns (or a joined CSV) to percent agreement, kappa + CI, PABAK, confusion matrix, disagreements; exit 2 on strings not in Lists.
- `scripts/sample_records.py`: seeded, optionally stratified verification sample as a blind decision sheet; `--retrieval` lists Include/Maybe records without PDF/.txt.
- `scripts/apply_decisions.py`: subagent CSV to workbook columns via `set_cells.py`; dry run by default; H-L only with `--reviewer`.
- `scripts/screening_common.py`: shared loader (xlsx via lvrwb, or CSV export) and Lists validation.
- `references/subagent-brief.md`: the per-record briefs for both stages, with the exact Lists strings.
- `references/screening-methods.md`: Cochrane Handbook ch. 4, PRISMA 2020 item 8, kappa and its caveats, single-screening evidence, AI disclosure.
- `references/examples.md`: three records screened at title/abstract with the rules, including one the reviewer and AI disagreed on.
- `references/validation.md`: hand-computed 2x2 against the script, bootstrap cross-check, what was tested.

AI decisions are advisory; the reviewer decides; the Methods say AI assistance was used.
