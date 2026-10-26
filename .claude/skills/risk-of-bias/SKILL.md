---
name: risk-of-bias
description: Assess methodological quality / risk of bias of the included studies with QUADAS-2 (questionnaire or screening item evaluated against a vision reference standard, reporting sensitivity/specificity/AUC), the COSMIN Risk of Bias checklist (reliability, validity, Rasch/IRT or responsiveness of a questionnaire) or AGREE II (guidelines), one subagent per study, then draw the robvis-style traffic-light plot and summary bar plot and write the Markdown table for the manuscript. Use when asked for risk of bias, quality assessment, QUADAS, QUADAS-2, COSMIN, AGREE, critical appraisal, study quality, methodological quality, traffic-light plot, "assess the included studies", signalling questions, applicability concerns, or GRADE inputs for a DTA review.
---

# Risk of bias (QUADAS-2 / COSMIN)

Every included study gets a reproducible quality judgement with the supporting sentence and page
from `data/articles_text/*.txt`, recorded in a CSV, drawn with `scripts/rob_plots.py`. AI
judgements are advisory: the reviewer confirms each row, and the review's Methods must say that
AI assistance was used for drafting the assessments. Outputs go in `analysis/risk_of_bias/`
(never in `data/`).

## 1. Pick the tool per study

| Study contributes | Tool | Why |
|---|---|---|
| Accuracy of a questionnaire, score cut-off or screening item against measured VA/VF, a full-length questionnaire or clinician-judged LVR need (sensitivity, specificity, AUC, PPV/NPV, 2x2) | **QUADAS-2** (this skill, `references/quadas2.md`) | It is the DTA tool; its domains map onto the biases that distort accuracy: spectrum, data-driven thresholds, unblinded reference standard, partial verification. |
| Measurement properties of a questionnaire: internal consistency, test-retest, Rasch/IRT fit, factor structure, construct validity (correlation with VA, known groups), responsiveness to LVR, translations | **COSMIN RoB checklist** (`references/cosmin.md`, `assets/cosmin_template.csv`, `scripts/cosmin_table.py`) | QUADAS-2 has nothing to say about reliability or dimensionality; COSMIN rates each property's standards and takes the worst score. |
| A guideline or recommendation on LVR referral (e.g. ESO stroke guideline, Dutch multidisciplinary guideline, AAO PPP) | **AGREE II** | Rate the six domains at https://www.agreetrust.org by hand; no tooling here. |
| Both accuracy and measurement properties | QUADAS-2 for the accuracy result, COSMIN for the rest; keep the rows in the two CSVs. | |
| Prediction model combining items with age, diagnosis etc. | PROBAST, not QUADAS-2 (pointer only). | |
| Comparative accuracy (two questionnaires head-to-head in the same people) | QUADAS-2 plus QUADAS-C (pointer only). | |

Use the full-text decision column (J) of `data/LVR_screening_sheet_2.xlsx` (or its CSV export)
to get the included set. If it is still empty, say so and ask which studies to assess rather
than assessing Maybe papers as if they were included.

## 2. QUADAS-2 in one screen

Four domains, each with a **risk-of-bias** judgement; the first three also get an
**applicability** judgement. Low / High / Unclear only; no scores.

| Domain | Tailored signalling questions for this review (answer Y / N / U; NA if not applicable) |
|---|---|
| D1 Patient selection | q1 consecutive, random or whole-population sample of adults? q2 case-control / two-gate design avoided (not LVR patients plus normally-sighted volunteers)? q3 no inappropriate exclusions (cognitive impairment, language, unable to do VA test)? q4 enrolment independent of the screening-question answers? |
| D2 Index test | q1 questionnaire answered before and without knowledge of the vision measurement/diagnosis (and scorer blind)? q2 positive-screen threshold or response rule pre-specified, not optimised on this sample? q3 if items/cut-offs were picked from a larger pool, was that done in a separate or validation sample? q4 administered the same way to everyone and as it would be used (stand-alone wording, mode)? |
| D3 Reference standard | q1 likely to classify the target condition correctly (VA with standard chart and stated correction; VF with standard perimetry; documented LVR-need criteria; full questionnaire with established cut-off)? q2 measured/interpreted blind to the questionnaire? q3 defining threshold pre-specified and stated (e.g. VA worse than 0.3 logMAR, better eye)? q4 measured under a stated protocol for the study, not from mixed clinical records? |
| D4 Flow and timing | q1 appropriate interval between questionnaire and vision measurement (same visit or about 3 months, no intervening surgery/LVR)? q2 all participants received a reference standard, with verification not dependent on the screening answer? q3 all received the same reference standard? q4 all participants in the 2x2 / analysis, with the n reconciled to the n enrolled? |

Applicability asks whether the people and setting (D1), the test as administered (D2) and the
target condition (D3) match the review question: adults; a brief self-report question or PROM
as it would be used; "needs LVR" with VA/VF-defined low vision as an accepted proxy.

**Judgement rule** per domain: all answered questions Y -> **Low**; any N -> **High** (the
assessor may keep Unclear when the No is minor, with the reason in `notes`); otherwise
**Unclear**. Overall per study: High if any domain High, else Unclear if any Unclear, else
Low. `rob_plots.py` recomputes the rule and warns on disagreements, so overrides stay visible.
Full standard questions, tailoring rationale and citations: `references/quadas2.md`. Two
complete assessments of real papers from this repo: `references/examples.md`.

## 3. Run one assessment per study with a subagent

One study per subagent keeps the brief narrow and stops judgements bleeding between papers.
Use at least a sonnet-class model at medium effort (never haiku or low effort). Give each
subagent exactly this, filled in:

```
Assess risk of bias for study <study_id> with QUADAS-2, tailored for a review of self-report
screening questions/questionnaires for low vision rehabilitation need.
Read only: <absolute path to data/articles_text/<file>.txt> (grep -n, then Read with offset/limit;
each page starts with a "[page N]" line) and .claude/skills/risk-of-bias/references/quadas2.md
(the tailored questions are in the section "Tailored questions"). Do not read other studies.
Answer every signalling question Y/N/U (NA if it cannot apply) from the text alone; never infer
a Yes from silence. For each of the 4 domains quote one verbatim supporting sentence with its
[page N], give the risk-of-bias judgement by the rule (all Y -> Low; any N -> High unless you
justify Unclear in notes; else Unclear) and, for D1-D3, an applicability judgement with its reason.
Return ONLY 4 CSV rows (no header) in the column order of
.claude/skills/risk-of-bias/assets/quadas2_template.csv, assessor = "AI (advisory; confirm)",
plus one line giving the analysed n. Put every judgement call you were unsure about in notes.
```

Append the returned rows to `analysis/risk_of_bias/quadas2.csv` (start it from
`assets/quadas2_template.csv`; drop the STUDY_ID placeholder rows; an optional `n` column may
be added). Use the same `study_id` as `analysis/extraction/studies.csv` from the
data-extraction skill (the Screening-sheet ID, e.g. `92`), so `--studies` can supply
`n_analysed` and the `citation` label; the examples use `Wu2026`-style ids only because they
stand alone. Run `--check` after each append so a malformed row is caught at once:

```bash
python3 -I .claude/skills/risk-of-bias/scripts/rob_plots.py analysis/risk_of_bias/quadas2.csv --check
```

`-I` keeps the script from importing anything planted in the CSV's folder or the working
directory; the script re-adds the user site directory itself, where matplotlib lives on this
machine.

**Reviewer reconciliation.** The reviewer opens the CSV, reads each quote against the paper, and
either keeps the row (changing `assessor` to their initials) or edits it. Disagreements are
resolved on the quote, not on the AI rationale. Keep the AI rows in git history, or in an
`assessor` value such as "AI draft; confirmed by AF", so the Methods can say how many
judgements changed. If a second human assessor is used, add their rows with a different
`assessor` value and report agreement in the text; the script keeps the first row per
study x domain, so make a reconciled copy before plotting.

## 4. Draw the figures and table

```bash
python3 -I .claude/skills/risk-of-bias/scripts/rob_plots.py analysis/risk_of_bias/quadas2.csv \
    --out-dir analysis/risk_of_bias --studies analysis/extraction/studies.csv --weight
```

- Validates first: allowed judgement strings, four domains per study exactly once, Y/N/U/NA
  answers, applicability `NA` on flow and timing; exits 1 and writes nothing on an error.
  Empty quotes/pages and algorithm disagreements are warnings (`--strict` makes them errors).
- Writes `quadas2_traffic_light.svg/.png` (studies x domains, risk of bias left, applicability
  right, Okabe-Ito green/amber/vermillion with + ? − symbols so colour is never the only cue),
  `quadas2_summary.svg/.png` (% of studies Low/Unclear/High per domain, weighted by n when
  `--weight` is given with an `n` column in the CSV or a `--studies` file; the extraction
  `studies.csv` works as-is, taking `n_analysed` and `citation`, or name columns with
  `--n-col`/`--label-col`),
  `quadas2_table.md` (per-study table and summary counts, paste into the manuscript or
  supplement) and `quadas2_summary.csv`.
- Output is deterministic (fixed SVG ids, no timestamps) so figures diff cleanly in git.
- Open the PNG and check it before using it: long study labels, more than ~25 studies, or
  a single study are the cases most likely to need `--title` or a label column.

For COSMIN rows: `python3 -I .claude/skills/risk-of-bias/scripts/cosmin_table.py
analysis/risk_of_bias/cosmin.csv` validates the ratings, applies worst-score-counts per
study x instrument x property and writes `cosmin_ratings.csv` and `cosmin_table.md`.

## 5. Write it up

- Methods: name the tools (QUADAS-2, Whiting 2011; COSMIN RoB, Mokkink 2018), that the
  signalling questions were tailored (list them in a supplement), who assessed and how
  disagreements were resolved, that AI drafting was used and every judgement was confirmed by
  the reviewer, and the pre-specified sensitivity analysis (e.g. exclude studies High in D2 or
  D4 from pooled estimates).
- Results: the traffic-light figure, the summary figure or table, and one paragraph naming the
  dominant problems (expect: data-driven item or cut-off selection, spectrum-enriched clinic
  samples, partial verification, VA-only reference standards that miss field loss).
- Hand the per-study judgements to the DTA synthesis and GRADE steps; with 2-6 studies per
  pooled estimate, a High-risk study is a reason to not pool, or to pool and show both.

## Pitfalls specific to this review

- "Best item out of N" and "optimal cut-off by Youden" in the same sample are D2 q2/q3 = N even
  when the final rule is a single fixed yes/no.
- Two-stage surveys (all positives verified, a sample of negatives) give crude sensitivity and
  specificity that do not describe an unselected population: D1 q4 / D4 q2, and a note for the
  extraction that the 2x2 needs reweighting or the study stays unpooled.
- A questionnaire validated against another questionnaire is accuracy for QUADAS-2 only if the
  review protocol accepts that questionnaire as a reference standard; otherwise it is COSMIN
  hypotheses testing.
- Glaucoma-only or AMD-only samples are an applicability concern (D1), not a bias.
- Do not score, rank or average domains. Do not copy AI rows into the manuscript without the
  reviewer's confirmation, and do not write judgements into the screening workbook.
