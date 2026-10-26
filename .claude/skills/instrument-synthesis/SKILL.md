---
name: instrument-synthesis
description: Build the "what tools exist" part of the LVR questionnaire review - a structured comparison of self-report instruments and screening items (NEI VFQ-25, VA LV VFQ-48/20, Activity Inventory, IVI, LVQOL, GQL-15, GAL-9, APEDS-VFQ, MLVAI, VF-14, EQ-5D vision bolt-on, the Legge 100-item acuity survey and its two-item screen, single self-rated vision items), their measurement properties rated with the COSMIN criteria (sufficient / insufficient / indeterminate / inconsistent) and summarised per instrument with a modified-GRADE quality of evidence, and their feasibility for a technician work-up in a glaucoma or LVR clinic (items, minutes, mode, reading level, languages, licensing, scoring burden, field/contrast coverage). Use when asked to compare instruments or questionnaires, "which questionnaire should the clinic use", instrument table, feasibility table, COSMIN rating, measurement properties, psychometrics, Rasch / alpha / ICC evidence, "is the VFQ-25 validated", quality of evidence for a PROM, recommendation categories, or to write the instruments section of the review. Accuracy pooling stays with dta-meta-analysis; this skill covers the validation (COSMIN) side and says where the two meet.
---

# Instrument synthesis

The review has two kinds of evidence about every tool: **how accurately it finds people who
need LVR** (sensitivity, specificity, AUC against VA/VF or LVR need: the QUADAS-2 / DTA path)
and **how well it measures** (reliability, structure, validity, responsiveness: the COSMIN
path). This skill runs the COSMIN path, builds the comparison and feasibility tables, and
writes the section in which the two paths meet. Intermediate files go to
`analysis/instruments/`, manuscript tables to `paper/tables/`; nothing is written under
`data/`. Run scripts as `python3 -I <script>` because every input is data, not code; both
scripts are standard-library only.

AI-compiled instrument facts and AI-drafted ratings are advisory. The reviewer verifies every
catalogue cell against the development paper and every rating against the cited page, and the
Methods state that AI assistance was used and how it was checked.

## The two paths, and where they meet

| Question | Tool | Skill | Output |
|---|---|---|---|
| Does answering "No" to the menu question identify VA worse than 0.3 logMAR? | QUADAS-2; per-study sens/spec/AUC; bivariate pooling only with k >= 4 | risk-of-bias, data-extraction, dta-meta-analysis | accuracy table, SoF (prisma-reporting) |
| Is the VA LV VFQ-48 reliable, unidimensional, responsive to LVR? | COSMIN RoB, then criteria for good measurement properties, then modified GRADE | risk-of-bias (RoB), **this skill** (criteria, summary, GRADE) | `summary_of_findings.md` |
| Which tool should a technician use, and for whom? | both, plus feasibility | **this skill** | comparison + feasibility tables, section text |

One paper can sit on both paths (Perez-Mana 2022: alpha and test-retest -> COSMIN; cut-off
105/106 with sensitivity 95% -> QUADAS-2). COSMIN does not rate sensitivity/specificity on their
own, and a questionnaire compared with measured VA is *hypotheses testing* for COSMIN because a
PROM has no gold standard; the script says so when it meets such a row. The recommendation
joins them: a screen is only worth adopting if its accuracy is acceptable *and* the construct it
measures is the one the clinic needs (in glaucoma: field and contrast loss with preserved
acuity, which an acuity-only item cannot see), and a full instrument is only worth adopting if
its measurement properties are sufficient with at least low-quality evidence (COSMIN category A)
*and* it fits a technician work-up.

## Workflow

1. **Collect instrument facts.** Start from `assets/instrument_catalogue.csv` (one row per
   instrument, `verified = no` by default, `uncertain_fields` names what to check). For each
   included study, extract the instrument facts it reports into
   `analysis/extraction/instruments.csv` with the data-extraction skill (page cites required).
   The catalogue extends that schema with `administration_mode, reading_level,
   development_citation, development_doi, development_pmid, rasch_validated, licence,
   scoring_burden, field_contrast_coverage, glaucoma_specific, short_forms, verified,
   uncertain_fields`; add those columns to `instruments.csv` when a study reports them. Then
   read each development paper (Crossref / PubMed by DOI or PMID) and set `verified` to `yes`
   only after checking items, scoring, time and licence. `references/instrument_notes.md` lists
   what the texts in `data/articles_text/` say about nine instruments, with pages.
2. **Extract measurement-property results** into `analysis/instruments/property_results.csv`
   (template with worked rows: `assets/property_results_template.csv`): one row per reported
   statistic with `study_id, instrument, property, statistic, value, n, page`, plus `subscale`,
   `model` (CFA/EFA/Rasch/IRT), `mic`, `hypothesis` or `confirmed` for hypotheses testing and
   responsiveness, and `override` + `override_reason` for a judgement the rules cannot make.
   Hypotheses must be pre-specified (in the protocol if the authors gave none) or the result
   stays indeterminate; write the protocol hypotheses once and cite them in `notes`.
3. **Risk of bias first.** Run the COSMIN RoB checklist with the risk-of-bias skill
   (`cosmin_table.py` -> `analysis/risk_of_bias/cosmin_ratings.csv`). The RoB rating and the
   result rating are separate: a doubtful study can still show a sufficient result; it just
   earns less certainty.
4. **Rate, summarise, grade.**
   ```bash
   python3 -I .claude/skills/instrument-synthesis/scripts/rate_properties.py \
       analysis/instruments/property_results.csv \
       --rob analysis/risk_of_bias/cosmin_ratings.csv --out-dir analysis/instruments
   ```
   It rates each result against the criteria in `assets/criteria_good_measurement_properties.md`
   (+ / - / ?), combines rows per study x instrument x property (Rasch needs all four aspects;
   alpha needs structural-validity evidence; >= 75% of hypotheses), summarises across studies
   (all + -> +; all - -> -; mixed -> +- unless `--majority 0.75`; ignore ?), and grades each
   summary with the modified GRADE rules in `references/cosmin_sr.md` (risk of bias,
   inconsistency, imprecision by total n, indirectness via `--indirectness "GQL-15=serious"`).
   `--structural-ok INSTRUMENT` asserts structural validity shown outside the CSV (cite it);
   `--by language` summarises per subgroup when inconsistency is explained; `--check` prints
   the row ratings without writing. Outputs: `property_ratings.csv`,
   `study_property_ratings.csv`, `summary_of_findings.csv` and `.md`. Expect many "?" and
   "Low / Very low": most LVR validation studies have n < 100, one study per property, and no
   a-priori hypotheses. Report that as the finding rather than softening it.
5. **Feasibility.** Copy `assets/feasibility_template.csv` to
   `analysis/instruments/feasibility.csv` and fill one row per candidate instrument from the
   catalogue and the included studies (minutes with the source, mode, reading level, languages,
   licence, scoring burden, equipment, technician-ready yes/no with the reason, field/contrast
   coverage). Minutes are rarely reported; when they are (LVQOL 5-10, VA LV VFQ-48 25-35),
   cite the page.
6. **Tables.**
   ```bash
   python3 -I .claude/skills/instrument-synthesis/scripts/instrument_table.py \
       --instruments analysis/extraction/instruments.csv --studies analysis/extraction/studies.csv \
       --ratings analysis/instruments/summary_of_findings.csv \
       --feasibility analysis/instruments/feasibility.csv --for glaucoma --out-dir paper/tables
   ```
   Merges catalogue < extracted facts < feasibility file, counts included studies per
   instrument, adds one compact COSMIN cell per instrument, marks every unverified row with a
   dagger and a footnote, and writes `comparison_table.md/.csv` and `feasibility_table.md/.csv`.
   `--columns` and `--feasibility-columns` set the column list; `--included-only` drops
   instruments no included study reports; `--for glaucoma` adds the field/contrast coverage and
   glaucoma-specific columns to both tables. Read the daggers before pasting anything.
7. **Write the section** (SWiM: Campbell 2020; COSMIN steps 8-10). Structure: (a) which
   instruments the included studies evaluated and in whom; (b) per instrument, the summarised
   properties with certainty, in two or three sentences each, leading with what is *not*
   known; (c) the accuracy evidence for the screening items, per study, from the DTA path;
   (d) feasibility for a technician work-up; (e) recommendation using COSMIN categories: A
   (content validity sufficient and at least low-quality evidence for sufficient internal
   consistency: recommendable), B (promising, needs validation), C (high-quality evidence of an
   insufficient property: not recommended). Say which category each instrument falls into and
   why, and say plainly when the answer is "no instrument has been validated in a glaucoma
   clinic for this purpose".

## Pitfalls specific to this review

- One alpha over a multidimensional total (NEI VFQ-25 composite, APEDS-VFQ total) does not meet
  the internal-consistency criterion; rate per unidimensional subscale, or leave it "?".
- Person separation reliability counts as internal consistency; a separation *index* is
  converted to reliability (G^2 / (1 + G^2)) and the derivation is written to the output.
- A Pearson/Spearman test-retest correlation is "?" (no ICC); say so rather than calling the
  LVQOL "reliable in Spanish".
- Items and cut-offs selected by AUC in the same sample (Wu 2026) make the accuracy optimistic:
  that is a QUADAS-2 D2 concern, not a COSMIN one, and the comparison table should say
  "derivation sample only".
- EQ-5D without the vision bolt-on was unresponsive to LVR (Malkin 2013); do not let a generic
  utility measure into the feasibility shortlist without that caveat.
- Field and contrast: GQL-15 / GAL-9 and APEDS-VFQ have explicit field or contrast items; the
  acuity survey and the two-item screen have none by design. Make that column visible whenever
  the audience is a glaucoma clinic.
- Do not grade an indeterminate summary, do not average ratings, and do not write ratings into
  the screening workbook.

## Files and what to read when

- `assets/instrument_catalogue.csv`: 19 instruments, AI-compiled, `verified = no`; read the
  `uncertain_fields` column before quoting a number.
- `assets/criteria_good_measurement_properties.md`: the Prinsen 2018 criteria in plain words,
  with the script's conventions marked. Read before step 4 and when a rating surprises you.
- `assets/property_results_template.csv`, `assets/feasibility_template.csv`: input layouts.
- `references/cosmin_sr.md`: the 10-step COSMIN review procedure, the modified GRADE rule set
  the script implements, when COSMIN is the wrong tool, citations.
- `references/instrument_notes.md`: page-cited facts from the article texts for LVQOL,
  NEI VFQ-25, VA LV VFQ-48 / VA-13, IVI, Activity Inventory, EQ-5D, APEDS-VFQ, GAL-9, the
  100-item survey and the Bibby mobility questionnaire.
- `references/validation.md`: what the scripts were tested on and the numbers to expect.

## Hand-offs

- In: `analysis/extraction/{instruments,studies,effects}.csv` (data-extraction),
  `analysis/risk_of_bias/cosmin_ratings.csv` (risk-of-bias), per-study accuracy from
  `dta.csv` / dta-meta-analysis for the recommendation text.
- Out: `paper/tables/*.md` for the manuscript; `summary_of_findings.md` for the supplement;
  the section text for prisma-reporting's Methods/Results scaffolding (its SoF table is for
  pooled accuracy, not for COSMIN summaries).
