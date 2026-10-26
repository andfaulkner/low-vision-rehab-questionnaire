# Validation of the risk-of-bias tooling

Risk-of-bias assessment is a judgement procedure, not a statistical estimator, so there is no
published numerical worked example to reproduce. What can be checked is that the scripts apply
the published rules exactly and that the figures are legible and accessible. All checks below
were run on 2026-10-25 with Python 3.15 and matplotlib 3.11.2.

## 1. QUADAS-2 judgement rule (`rob_plots.py`)

Rule from Whiting et al. 2011: all signalling questions Yes -> Low; any No -> High ("potential
for bias"); otherwise Unclear. `expected_judgement()` ignores NA and empty answers.

| Answers (q1..q4) | Expected | Obtained |
|---|---|---|
| Y Y Y NA | Low | Low |
| Y N Y U | High | High |
| Y U Y NA | Unclear | Unclear |
| U Y N Y | High | High (warning issued because the CSV recorded Unclear with an override note) |
| Y U NA Y | Unclear | Unclear (warning issued because the eval CSV recorded Low on purpose) |

Validation errors were triggered as intended by a deliberately broken 5-study CSV: a judgement
string `Lowish` (rejected), a duplicated `Index test` row (rejected), a study missing its
`Index test` row (rejected); exit status 1 and nothing written. `--weight` without any `n`
exits 1 naming each study without a sample size. The blank template exits 1 (empty judgements).

## 2. Weighted summary percentages

Synthetic 6-study CSV with n = 412, 65, 385, 1200, 48, 230 (total 2340). Patient selection:
Low = Alpha (412) + Delta (1200) + Foxtrot (230) = 1842 / 2340 = 78.7% (script: 79%);
High = Bravo (65) + Echo (48) = 113 / 2340 = 4.8% (script: 5%); Unclear = Charlie 385 / 2340 =
16.5% (script: 16%). Unweighted counts in `quadas2_summary.csv` were 3 / 1 / 2 (50.0 / 16.7 /
33.3%), as constructed.

## 3. Determinism

Two consecutive runs on the same CSV produced byte-identical `quadas2_traffic_light.svg` and
`quadas2_summary.png` (`cmp` silent). SVG ids use `svg.hashsalt = "quadas2"` and the SVG
`Date` metadata is suppressed.

## 4. Colour-blind safety of the traffic-light palette

Okabe-Ito colours Low `#009E73`, Unclear `#E69F00`, High `#D55E00` were run through the
dataviz skill's `validate_palette.js` (light surface): lightness band PASS, chroma floor PASS,
CVD separation PASS (worst adjacent pair ΔE 11.4 protan, 14.8 tritan; target >= 8), normal-vision
floor PASS (15.6; threshold 15), contrast WARN for the amber (2.19:1), which is why every mark
also carries a symbol (+ ? −) and the legend names each level in text. An alternative green/
yellow/orange set (`#1B9E77,#E6AB02,#D95F02`) failed the lightness band and was not used.

## 5. Rendering check

The 6-study synthetic plot and the 2-study real-paper plot (`assets/quadas2_example.csv`) were
rendered to PNG and inspected: rows alternate shading, risk-of-bias and applicability blocks are
separated by a rule with headers that stay a fixed distance above the column labels whatever
the study count, legend and footnote do not collide, and the title clears the block headers.
Segments below 8% in the summary bars carry no percentage label (the counts are in the CSV and
Markdown table).

## 6. COSMIN worst-score-counts (`cosmin_table.py`)

Synthetic ratings for two studies; expected overall = lowest rating among the property's rated
standards (Mokkink et al. 2018):

| Study / property | Standards rated | Expected | Obtained |
|---|---|---|---|
| StudyA Structural validity | VG, Adequate (3.2), VG, VG | Adequate (3.2) | Adequate (3.2) |
| StudyA Internal consistency | VG, VG, VG | Very good | Very good |
| StudyA Reliability | Doubtful (6.1), VG x4 | Doubtful (6.1) | Doubtful (6.1) |
| StudyB Reliability | VG, VG, Adequate, Doubtful (6.4), VG | Doubtful (6.4) | Doubtful (6.4) |
| StudyB Criterion validity | VG, NA, Inadequate (8.3) | Inadequate (8.3) | Inadequate (8.3) |

An invalid rating (`Dubious`) is rejected with exit 1; a property whose standards are all NA is
rejected as "no standard was rated".

## 7. Worked examples against the source text

Every `support_quote` in `assets/quadas2_example.csv` and every double-quoted passage followed
by "(page N)" in `references/examples.md` was searched for in the corresponding
`data/articles_text/*.txt` file after collapsing whitespace (the text wraps mid-sentence), and
checked to lie under the stated `[page N]` marker: 0 problems. Three quotes had to be made to
match PDF-extraction artefacts (a curly apostrophe in "subjects’", reference superscripts
flattened into "charts17" and "box.18", and "≤" extracted as "ⱕ"); the examples say so where it
happens, because a reviewer grepping the text will hit the same thing.

## 8. Hand-off from data-extraction

`--studies .claude/skills/data-extraction/assets/studies.csv --weight` on a copy of the Wu rows
re-keyed to Screening ID `92` picked up `n_analysed = 385` and the `citation` "Wu 2026" as the
row label without any option; `--n-col nope` is refused with exit 1.

## Not verified

- The worked assessments are AI drafts. The judgements that most need a reviewer's eye are
  Wu 2026 D2 applicability (High vs Unclear) and D4 (Unclear kept despite a No on q3).
- The COSMIN standards in `assets/cosmin_template.csv` are paraphrases of the 2018 checklist
  from memory; the IRT/Rasch sample-size rule is deliberately left as "see the manual".
- `python3 -I` hides the user site directory where matplotlib is installed on this machine;
  the script re-adds that one directory on ImportError so `-I` is what SKILL.md documents.
