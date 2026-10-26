# Glaucoma Today LVR questionnaire review

effort: medium
permissions: auto
category: lvr-review
preflight: cmd=jq, cmd=pdftotext, file=data/LVR_screening_sheet_2.xlsx, file=docs/plans/glaucoma-today-review-plan.md

## Workspace, exports and full texts

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 1 of 10. Its job is to make the inputs trustworthy before anything reads them.

### Tasks

1. Invoke the `screening-workbook` skill. Run `xlsx_to_csv.py --check`; the Screening export is known to be stale (129 rows against 135 in the xlsx). Regenerate all four CSVs. Confirm 135 records, IDs 1–135, and that `included.py` lists the reviewer's 13 Include/Maybe records. Do not write any cell.
2. Create the output tree from the plan doc's Deliverables section: `paper/`, `paper/figures`, `paper/tables`, `paper/checklists`, `paper/sof`, `analysis/search`, `analysis/screening`, `analysis/extraction`, `analysis/risk_of_bias`, `analysis/synthesis`, `analysis/instruments`, `tmp/downloads`. Confirm `tmp/` is git-ignored (it is listed in `.gitignore`).
3. Invoke the `study-screening` skill and run `sample_records.py --retrieval -o analysis/screening/retrieval.csv`. Then extend the check to every record in the workbook, not only the reviewer's Include/Maybe set: with a short `python3 -I` script, match each of the 135 records to a `data/articles_text/*.txt` by first-author surname + year (reuse the matcher imported from `screening-workbook/scripts/included.py`) and write `analysis/screening/text_inventory.csv` with columns `id, year, first_author, pdf, txt, status` where status is `retrieved`, `text-missing`, `not-retrieved` or `suspect` (IDs 48 and 69 are known to hold the wrong paper / supplementary tables only; `Anchor article.txt` is a duplicate of Wu 2026, ID 92, not Wu 2024, ID 128).
4. Retrieve the open-access full texts that are missing and matter most, in this order, into `tmp/downloads/<id>/` first and only then into `data/articles/` with the existing naming convention (`<Surname> et al. - <Year> - <Title truncated to ~50 chars>.pdf`):
   - ID 128, Wu/Legge 2024 TVST, doi 10.1167/tvst.13.9.20, PMC11412607.
   - ID 133, Nguyen 2014 IOVS, doi 10.1167/iovs.14-14138, PMC4142770.
   - ID 30 (Stalin 2025 Optom Vis Sci) and ID 23 (Potter 2024 Ophthalmology): try PMC and the publisher's open-access link only. If paywalled, do not bypass; record `not-retrieved`.
   - Any other `text-missing` record whose T/A decision (H) or both AI passes (N and Q) say Include or Maybe.
   Use `curl -L` with a browser user agent or WebFetch; verify each download is a PDF (`file`), is the right paper (first page title), then move it. Never overwrite an existing file.
5. Invoke the `pdf-to-text` skill and run `pdf2txt.sh` on `data/articles/` (incremental; it skips PDFs that already have a newer `.txt`). Check its summary line for `FAILED`, `Little or no text` and `Words still run together`. Confirm the new `.txt` files carry `[page N]` markers and that the ID 128 text contains the phrase "fast food" or "posted menus".
6. Re-run the inventory script from task 3 and overwrite `analysis/screening/text_inventory.csv`. Record in the status section exactly which IDs are still `not-retrieved` or `suspect`; later steps treat those as "Full text not available" candidates for the reviewer.

### Report

Append the status section to the plan doc with: CSV regeneration result, the 13 reviewer Include/Maybe IDs, PDFs retrieved (ID, file name), PDFs not retrievable and why, `.txt` conversion summary, remaining gaps.

-----[NEXT_PROMPT]-----

## Glaucoma Today format

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 2 of 10: learn the target magazine's format so the manuscript and references match it.

### Tasks

1. Fetch the September/October 2026 issue of Glaucoma Today (glaucomatoday.com, Bryn Mawr Communications). If that issue is not online, use the most recent issue available and say so. Read the issue's table of contents and at least two review-style or clinical-feature articles in full, plus the magazine's author guidelines page if one exists.
2. Write `paper/format_notes.md` with: typical word count of a feature/review article (count one real article); title and dek (subtitle) style; the section-heading style and whether headings are used at all; whether an abstract is used (usually not); the "At a Glance" / key-points box convention and its length; how authors, affiliations, financial disclosures and contact lines appear; sidebar, table and figure conventions; the exact reference format, including numbering by first appearance, how many authors are listed before "et al", journal abbreviation style, whether DOIs or URLs appear, and the "Accessed" wording for web sources; any stated policy on AI assistance. Quote **one real reference entry verbatim** and **one real article's title + dek + first paragraph verbatim** as models.
3. Invoke the `manuscript-references` skill. Following its `references/citation_formats.md` section "Matching the journal's real format", copy `.claude/skills/manuscript-references/assets/styles/ama.json` to `paper/style_glaucoma_today.json` and edit the author limits, DOI/URL display, italics, page condensing and "Accessed" wording to match the verbatim entry you quoted. Validate the JSON parses (`python3 -I -c "import json,sys; json.load(open(sys.argv[1]))" paper/style_glaucoma_today.json`).
4. Write a short `paper/format_checklist.md`: a list of yes/no checks the final manuscript must pass (word count range, dek present, box present, heading style, reference style, disclosure line), which step 10 will run.

### Report

Status section: issue used, word-count target, the verbatim reference entry, what you changed in the style file, anything the magazine requires that the plan doc does not mention.

-----[NEXT_PROMPT]-----

## Search strategy: minimal edit and recall

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 3 of 10. Invoke the `literature-search` skill and read `docs/LVR_search_strategy.md` and `.claude/skills/literature-search/references/search_notes.md` before touching any string, so you build on the 20 Oct work instead of redoing it.

### Tasks

1. **Why the originals missed the two papers.** Fetch the PubMed records of PMID 39292468 (TVST 2024, ID 128) and PMID 25052992 (Nguyen 2014, ID 133) through E-utilities (`efetch` XML: title, abstract, MeSH headings with major-topic flags, publication types). Check each AND-clause of the original PubMed string in `data/LVR_Q_Study_Outline.md` against each record and state exactly which clause fails for each paper. Do the same reasoning for the original Scopus string by inspection (no API).
2. **Baseline recall.** Run `pubmed_recall.py` with the original string (`--query-file`) and with the revised 8-arm strategy (`--from-doc`), both with `--cache analysis/search/cache`, saving JSON under `analysis/search/`. Confirm the numbers in `search_notes.md` (78 and ~593 records; 20/36 and 35/36 key sources; 0/14 and 12/14 held-out).
3. **Minimal edit.** The user asked for a *slightly modified* version of the original string. Propose at most three candidate edits to the original three-concept string (for example: adding `"visual acuity"[ti]` and `glaucoma*[ti]` to concept 1; adding `"screening question*"[tiab]` and `reading[ti]` to concept 2; adding `"item response"[tiab]` or `Rasch[tiab]` or dropping the accuracy concept for title-level matches). Test each with `pubmed_recall.py --query-file ... --diff <baseline json>` and record, per candidate: total records, whether PMIDs 39292468 and 25052992 are retrieved, key-source recall, held-out recall, and the number of new records over the original 78. Pick the candidate with the best recall of the two targets for the fewest added records, and give its Scopus translation with `syntax_translate.py` (`AND NOT` last).
4. **Write it up.**
   - `paper/search_strategy_note.md`: the clause-by-clause diagnosis, the candidate table, the chosen minimal edit (PubMed and Scopus strings verbatim), and a one-paragraph comparison with the 8-arm revision (recall, cost in records, which the review should adopt and why). Do not decide for the reviewer; recommend.
   - `paper/search_log.md`: copy `.claude/skills/literature-search/assets/search_log_template.md` and fill every placeholder you can from the runs above (dates, counts, recall JSON paths, strategy-development paragraph, AI assistance line naming the model ids from the plan doc). Leave Scopus counts as "to be typed from the interface" since there is no API.
   - List, in `analysis/search/minimal_edit_new_records.csv`, the PMIDs and titles the chosen edit adds beyond the original 78 so the reviewer can triage them. Do **not** add rows to the workbook and do not screen them in this step.
5. **Snowball check (bounded).** Run `snowball.py --included --cache analysis/search/cache --min-links 2 --direction backward --out analysis/search/snowball_2plus` and report only the count of candidates linked from two or more included records, and the top ten titles. This feeds the Methods "citation searching" line; it is not a new screening task.

### Report

Status section: the failing clauses per paper; the candidate table; the chosen edit; the 8-arm comparison in two sentences; snowball counts; paths written.

-----[NEXT_PROMPT]-----

## Screening: provisional included set

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 4 of 10. Invoke the `study-screening` skill and the `screening-workbook` skill and follow them exactly; read `docs/AI_title_abstract_screening_rules.md` and `.claude/skills/study-screening/references/subagent-brief.md` before briefing any subagent. Every subagent is `sonnet` at `medium` effort or higher; one record per subagent; never show a subagent another record's decision, the reviewer's decision or the AI columns.

### Tasks

1. **Fill the empty first-pass AI columns for IDs 128–135.** Run one title/abstract subagent per record with the Stage 1 brief (abstracts from the regenerated Screening CSV; "Missing" means title only). Collect into `analysis/screening/ta_ai_pass1_128-135.csv`, dry-run `apply_decisions.py --target ai1`, fix any Lists-string problems by re-running the offending subagent, then `--apply --export`. Report the Counts lines the script prints.
2. **Agreement for the Methods.** Run `agreement.py` for H vs N (`--name ta_reviewer_vs_ai1`), H vs Q (`--maybe-as separate`, `--name ta_reviewer_vs_ai2`) and N vs Q (`--name ai1_vs_ai2`) into `analysis/screening/`. Note percent agreement, kappa with CI, PABAK and "B recall of A's Include" for each.
3. **Second-reviewer sample.** `sample_records.py --fraction 0.2 --seed 20261004 --stratify "Suggested decision (AI)" -o analysis/screening/second_reviewer_sample.csv`. Record the seed and the ID list.
4. **Build the full-text pool** by the plan doc's provisional-inclusion rule (section "Rules that bind every step", item 6). Read H, N, Q from the xlsx through `lvrwb` (not the CSV) and the strict pass from `results/LVR_strict_screening.csv`. Write `analysis/screening/ft_pool.csv` with `id, basis, h, n, q, strict, text_file, text_status` (text status from `analysis/screening/text_inventory.csv`). Sanity check: IDs 92, 128 and 133 must be in the pool; if not, say why and add them with basis `key-source`.
5. **Full-text AI screening.** One subagent per paper in the pool that has a usable `.txt`, with the Stage 2 brief (Include/Exclude, exactly one Lists reason, the deciding sentence with its `[page N]`). Collect into `analysis/screening/ft_ai_decisions.csv` (`id,decision,reason,rationale,quote`). Papers with no usable text get `Exclude, Full text not available` with the quote field `NOT RETRIEVED`, so the reviewer sees them. Validate the file with `apply_decisions.py ... --target ai2 --dry-run`-style checks for Lists spelling (do not apply full-text decisions to the workbook; it has no AI full-text columns).
6. **Provisional included set.** Write `analysis/screening/provisional_included.csv` with the columns of `included.py` plus `basis` and `ft_ai_decision`, `ft_ai_reason`, `ft_ai_quote`: every pool record whose full-text AI decision is Include. Add a header comment line (`# PROVISIONAL: reviewer has decided 40/135 at T/A and 0 at FT; see plan doc rule 6`). Then run `independent_datasets`-style sanity: flag the Wu 2024 / Wu 2026 overlap in a `notes` column.
7. **Agreement at full text** against the earlier strict pass: `agreement.py --stage ft --b-file analysis/screening/ft_ai_decisions.csv --b decision --b-reason reason` will not work without reviewer J values; instead compute, with a short `python3 -I` script, the overlap between your FT Include set and the strict pass's 29 Includes, and list the disagreements with both rationales in `analysis/screening/ft_vs_strict.md`.

### Report

Status section: Counts lines after the N–P write; the three agreement summaries; pool size and provisional included count with the ID list and basis breakdown; disagreements with the strict pass; which included records lack text. State plainly that all of this is advisory until the reviewer fills H–L.

-----[NEXT_PROMPT]-----

## Data extraction

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 5 of 10. Invoke the `data-extraction` skill; read its `references/schema.md`, `references/pitfalls.md` and `references/subagent-brief.md` before briefing anyone. The included set is `analysis/screening/provisional_included.csv` (provisional; say so in every output header). Subagents: `sonnet`, `medium` or higher, one paper per subagent, fresh context each.

### Tasks

1. **Pass A** for every provisional included paper with a usable `.txt`: send the subagent brief verbatim with the slots filled, output under `analysis/extraction/passA/<ID>/`. Run them in parallel batches of six.
2. **Pass B** for the accuracy-bearing papers only: ID 92 (Wu 2026), ID 128 (Wu 2024 TVST), and every paper whose pass A `dta.csv` has a row or whose `effects.csv` has an AUC or a cut-off. Different subagents, told nothing about pass A, output under `analysis/extraction/passB/<ID>/`.
3. **Reconcile and merge.** `reconcile.py` for each dual-extracted paper (`--ignore notes`), write the disagreement files, and resolve each cell *from the cited page yourself*, recording `resolved_value` and `resolved_by = "AI chain step 5 (advisory)"`. Merge all pass A rows (with resolutions applied) into `analysis/extraction/studies.csv`, `dta.csv`, `effects.csv`, `instruments.csv`. Then `reconstruct_2x2.py --csv analysis/extraction/dta.csv --in-place`, and `validate_extraction.py analysis/extraction --report analysis/extraction/readiness.md`; fix every ERROR.
4. **Instrument catalogue.** Extend `instruments.csv` with the columns of `.claude/skills/instrument-synthesis/assets/instrument_catalogue.csv` for every instrument an included study reports; take page-cited facts from `.claude/skills/instrument-synthesis/references/instrument_notes.md` where the paper is included, and leave `verified = no`.
5. **The two questions, in depth.** One dedicated subagent reads the ID 92 text and another the ID 128 text (full read, not grep-only) and writes, with `[page N]` for every number:
   - `paper/two_item_accuracy.md`: for each of the two items and for the pair: the exact item wording, the acuity threshold it was keyed to, sensitivity, specificity, AUC (and the paper's caveat that a single yes/no item's "AUC" is (sens+spec)/2), PPV/NPV if given, the sample (n, VA range, recruitment, % glaucoma or diagnosis mix), how the items were chosen from the 100 (selection in the same sample: note the QUADAS-2 D2 concern), what a second or third item adds, and the authors' stated limitations. Include a short table.
   - `paper/candidate_items.md`: the other top-performing items from the 100-item survey with their figures, ranked by AUC at the 0.3 and 1.0 logMAR thresholds; then, from the other included instruments (APEDS-VFQ, GAL-9/GQL-15, Bibby mobility questionnaire, NEI VFQ-25 peripheral/contrast items, IVI mobility items), the items that target field loss, contrast, glare, mobility or driving, with the strongest field/contrast evidence cited (e.g. Bibby 2007 binocular-field correlation). End with a ranked shortlist of 3–5 items to add for a glaucoma clinic and the evidence (or lack of it) for each.
6. Report what the readiness section says: which instrument x reference-standard x threshold groups have k >= 4 independent studies (expect none) and why the honest answer is "describe, do not pool".

### Report

Status section: papers extracted (A and B), disagreement counts and how resolved, validator result, readiness verdicts, paths of the two Markdown files, every place the Wu papers were ambiguous.

-----[NEXT_PROMPT]-----

## Risk of bias

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 6 of 10. Invoke the `risk-of-bias` skill and follow it. Studies come from `analysis/extraction/studies.csv` (provisional set). Subagents: `sonnet`, `medium` or higher, one study per subagent, the exact brief from the skill's section 3.

### Tasks

1. **Choose the tool per study** with the skill's table: QUADAS-2 for every study with a `dta.csv` row or an accuracy result in `effects.csv` (ID 92 and ID 128 certainly; Perez-Mana 2022's cut-off; Stalin 2025 if retrieved; Potter 2024 if retrieved); COSMIN RoB for validation studies (LVQOL, VA LV VFQ-48, APEDS-VFQ, IVI, Activity Inventory, VA-13, etc.); AGREE II by hand, six-domain narrative only, for guidelines (ESO stroke guideline, AAO PPP if included). Write the mapping to `analysis/risk_of_bias/tool_map.csv`.
2. **QUADAS-2**: one subagent per study, append rows to `analysis/risk_of_bias/quadas2.csv` (from the template, STUDY_ID placeholders removed, `assessor = "AI (advisory; confirm)"`, an `n` column), `rob_plots.py --check` after every append. Expect D2 High for ID 92 and 128 (items and cut-offs selected in the same sample) and D1 applicability concerns for enriched research samples; let the subagents find that from the text rather than telling them.
3. **COSMIN RoB**: fill `analysis/risk_of_bias/cosmin.csv` from the template, one subagent per study, then `cosmin_table.py` to produce `cosmin_ratings.csv` and `cosmin_table.md`.
4. **Plots and table**: `rob_plots.py analysis/risk_of_bias/quadas2.csv --out-dir analysis/risk_of_bias --studies analysis/extraction/studies.csv --weight`. Open the PNG (Read tool) and check labels. Copy `quadas2_table.md` and `cosmin_table.md` to `paper/tables/`.
5. Write `analysis/risk_of_bias/summary.md`: one paragraph naming the dominant problems across studies (expected: data-driven item selection, spectrum-enriched samples, VA-only reference standards that cannot see field loss), and the per-study judgements that step 9 must mention when it weighs the evidence.

### Report

Status section: tool map; number of QUADAS-2 and COSMIN assessments; the overall judgement per study; paths of plots and tables; any study the subagent could not assess and why.

-----[NEXT_PROMPT]-----

## Synthesis: instruments and accuracy

effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 7 of 10. Invoke the `narrative-synthesis` skill and the `instrument-synthesis` skill and follow both. Inputs: `analysis/extraction/*.csv`, `analysis/risk_of_bias/*.csv`. Outputs: `analysis/synthesis/`, `analysis/instruments/`, tables to `paper/tables/`. Do not read article texts in this step except to confirm a specific number a script flags.

### Tasks

1. **Grouping first, written down** (SWiM item 1): write `analysis/synthesis/grouping.md` with the default groups from the narrative-synthesis skill (single item vs VA; single item vs VF; full questionnaire vs VA/VF; any instrument vs clinician-judged LVR need; questionnaire vs questionnaire) and which emerged from the data.
2. **Independent datasets**: `independent_datasets.py analysis/extraction/studies.csv --dta analysis/extraction/dta.csv --out-dir analysis/synthesis --assign`. Confirm it pairs Wu 2024 (ID 128) and Wu 2026 (ID 92) as one dataset; if it does not, set `dataset_id` by hand in `studies_with_datasets.csv` and say so.
3. **Can anything be pooled?** Run `dta_pool.py validate analysis/extraction/dta.csv` (dta-meta-analysis skill) and, for correlation/AUC rows, check `effects.csv` for any outcome with >= 3 independent studies of one instrument against one comparator. Expect "do not pool" everywhere; record the verdict lines verbatim in `analysis/synthesis/pooling_verdict.md`. If any group does qualify, run the pooling script with the skill's rules and keep its `summary.md`; otherwise do not pool.
4. **Per-study tables and figures without pooling**: `accuracy_table.py` (with `--effects`, `--studies analysis/synthesis/studies_with_datasets.csv`, `--rob analysis/risk_of_bias/quadas2.csv`, `--filter unit=person --filter subgroup=`) and `evidence_map.py`. Open each PNG and check labels. Copy `accuracy_table.md` and the evidence map Markdown to `paper/tables/`; copy `forest_nopool.svg`, `roc_space.svg` and the evidence-map figure to `paper/figures/`.
5. **COSMIN path**: build `analysis/instruments/property_results.csv` from `instruments.csv`, the extraction `effects.csv` and `instrument_notes.md` (page cites required; write the protocol hypotheses once in a `notes` block); run `rate_properties.py` with `--rob analysis/risk_of_bias/cosmin_ratings.csv`; expect many "?" and Low/Very low and report that as the finding.
6. **Feasibility table for a glaucoma clinic**: copy `feasibility_template.csv` to `analysis/instruments/feasibility.csv` and fill one row per candidate instrument (items, minutes with source page, mode, reading level, languages, licence, scoring burden, equipment, technician-ready yes/no with reason, field/contrast coverage, glaucoma-specific). Then `instrument_table.py ... --for glaucoma --out-dir paper/tables`. Read the daggers.
7. **Certainty without pooling**: for each group, draft the GRADE sentence using `assets/synthesis_templates.md` into `analysis/synthesis/certainty.md`; fill `assets/swim_checklist.md` into `paper/checklists/swim_checklist.md` with "where reported" pointing at the manuscript sections of the plan doc.
8. **Synthesis notes for the writer**: `analysis/synthesis/results_notes.md`, structured per group exactly as the "Results structure per group" template (evidence base; finding led by the strongest study; heterogeneity; risk of bias and what it would do; certainty; one-sentence bottom line), with every number carrying its study ID and page so step 9 can cite it. Include a dedicated section "Why the two questions work and what they miss" that joins `paper/two_item_accuracy.md`, `paper/candidate_items.md`, the feasibility table's field/contrast column and the QUADAS-2 D2 judgement, and a section "Other brief screeners found" (single self-rated vision items, LVQOL cut-off, Stalin 2025, NHATS/Potter if retrieved) with their numbers side by side.

### Report

Status section: independent dataset count; pooling verdicts; tables and figures written; COSMIN summary in three lines; the recommendation category (COSMIN A/B/C) per instrument; the ranked add-on items for glaucoma.

-----[NEXT_PROMPT]-----

## PRISMA, Methods and disclosure

model: sonnet
effort: medium

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 8 of 10. Invoke the `prisma-reporting` skill and follow it.

### Tasks

1. **Flow diagram from the workbook as it is.** Regenerate the Counts export (`screening-workbook` skill, `xlsx_to_csv.py`) and run `prisma_flow.py --counts-csv data/LVR_screening_sheet_2_Counts.csv --footnote "Records from other sources were screened together with the database records."`. It will report `DISCREPANCY` because the reviewer has screened 40 of 135; keep that diagram as `paper/figures/prisma_flow_reviewer.{svg,png}` (rename) with its DRAFT banner.
2. **Provisional flow.** Build a second diagram from the provisional numbers: identified 174 (78 + 88 + 8), duplicates 39, screened 135, excluded at T/A = 135 minus the full-text pool size from `analysis/screening/ft_pool.csv`, reports sought = pool size, not retrieved = pool records with no usable text, assessed = retrieved, excluded at full text with reasons from `analysis/screening/ft_ai_decisions.csv`, included = `provisional_included.csv` count. Use `--json` input (`--json-schema` shows the layout) and `--override` where the workbook cannot express a box; write `paper/figures/prisma_flow.{svg,png}` and `paper/prisma_counts.md`, and put the word PROVISIONAL in the figure legend and at the top of `prisma_counts.md`. Check the arithmetic lines the script prints. Open the PNG.
3. **Methods draft.** Copy the paragraphs from `.claude/skills/prisma-reporting/assets/methods_templates.md` into `paper/methods_draft.md` and fill every placeholder from: `paper/search_log.md` and `paper/search_strategy_note.md` (search; say the original strings were run on 4 Oct 2026 and the minimal edit and 8-arm revision were tested but not yet adopted, unless the reviewer's status says otherwise), `analysis/screening/*` (selection: single reviewer, AI suggestions in separate columns, override counts from Counts rows "agreed with / changed the AI decision", second-reviewer sample seed and size, retrieval counts), `analysis/extraction/readiness.md` (data items, dual extraction and reconciliation counts), `analysis/risk_of_bias/` (tools, counts), `analysis/synthesis/pooling_verdict.md` (keep the SWiM paragraph, delete the bivariate one), and the certainty paragraph. Write the AI-assistance disclosure with the model ids from the plan doc (default steps: Claude Fable 5.1, `claude-fable-5-1`; sonnet steps and subagents: Claude Sonnet 5.5, `claude-sonnet-5-5`), the dates of this chain run, the task list as actually performed, and the override percentages. Add one sentence that inclusion is provisional pending the reviewer's full-text decisions, marked for deletion once H–L are complete.
4. **Checklists.** Copy `prisma2020_checklist.md` and `prisma_dta_checklist.md` to `paper/checklists/` and fill "Where reported" with the manuscript section names from the plan doc's structure; leave page numbers blank. Run `checklist_status.py paper/checklists/*.md` (not `--strict` yet) and list what remains blank.
5. **Does the piece need PRISMA at all?** Write a short decision note at the top of `paper/methods_draft.md`, following the skill's "Does this paper need PRISMA at all?" section: the recommended label is "systematic search with narrative synthesis", with the flow diagram, eligibility criteria and SWiM items but no SoF table; say what changes if the authors call it a narrative review instead.

### Report

Status section: both flow diagrams' key numbers; discrepancies found; placeholders you could not fill (name them); checklist blanks; the disclosure paragraph verbatim.

-----[NEXT_PROMPT]-----

## Write the manuscript

effort: high

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 9 of 10: write the full article. Read, in this order, before writing a word: `paper/format_notes.md`, `data/LVR_Q_Study_Outline.md` (the proposed article outline), `analysis/synthesis/results_notes.md`, `paper/two_item_accuracy.md`, `paper/candidate_items.md`, `paper/tables/*.md`, `analysis/risk_of_bias/summary.md`, `paper/methods_draft.md`, `paper/prisma_counts.md`, `paper/search_strategy_note.md`, and `.claude/skills/instrument-synthesis/references/instrument_notes.md`. Invoke the `manuscript-references` skill for the citation-key syntax and the render/check commands.

### Writing rules

- Structure and content follow the plan doc's "Manuscript structure" section and the magazine's conventions in `format_notes.md` (title + dek, At-a-Glance box if used, heading style, word-count target, disclosure lines). Write for a clinical readership of glaucoma specialists: plain, concrete, no hype, no bullet-point essays; tables and the boxed protocol carry the detail.
- Cite with keys: `[@doi:...]` for every record that has a DOI (the Screening CSV's DOI column), `[@pmid:...]` when only a PMID is known, `[@slug]` for sources without either, which you define in `paper/bibliography_manual.csv` (template in `.claude/skills/manuscript-references/assets/bibliography_manual_template.csv`; the AAO Vision Rehabilitation PPP, the CNIB/Canadian legal-blindness definition and any web source go here).
- Every number carries a citation key and must exist in `analysis/extraction/*.csv`, `paper/two_item_accuracy.md`, `paper/tables/*.md` or `paper/prisma_counts.md`. If you cannot source a number, write `[VERIFY]` instead. Never invent a reference. Describe accuracy per study ("sensitivity was 0.89") and never as "pooled".
- Say in the text what the evidence cannot say: the two items were derived and tested in one enriched research cohort, keyed to acuity, never tested in a glaucoma clinic, and an acuity item cannot see field loss. The add-on items are proposals, with their evidence named.
- The technician protocol is a box: the two items verbatim, the proposed add-on items, how to combine with last VA and last visual field, the referral rule, and the time it should take. Mark anything untested as such.
- Put the Methods paragraph (search, screening with AI disclosure, synthesis) where `format_notes.md` says such material belongs (often a short "Methods" box or an end note); keep the full version in `paper/methods_draft.md` and the supplement.
- A visible one-line DRAFT note at the top: inclusion is provisional (reviewer has decided 40/135 at title/abstract and none at full text), to be removed when H–L are complete.

### Tasks

1. Write `paper/manuscript.md` in full, including figure and table call-outs (`Figure 1. PRISMA flow`, the forest-without-pooling plot, the evidence map, the QUADAS-2 traffic light; `Table 1` comparison, `Table 2` feasibility, `Table 3` per-study accuracy), legends, the At-a-Glance box, the protocol box, author/affiliation/disclosure placeholders, and a "Supplementary material" list (search strings, checklists, COSMIN summary).
2. Create `paper/bibliography_manual.csv` for the non-DOI sources you cite.
3. Run `cite.py resolve`, then `cite.py check` (fix every unresolved key, duplicate or never-cited entry), then `cite.py render ... --style paper/style_glaucoma_today.json --numbering paper/reference_numbers.csv`. Read `paper/references.md` once against the citations and add proper nouns the sentence-case rule lower-cased to `protected_words.txt` under `paper/` (copy the asset) if needed.
4. Count words of the body (excluding references, tables and boxes) and compare with the target in `format_notes.md`; trim or expand to land within the range. Record the count.
5. Run the checks in `paper/format_checklist.md` and fix what fails.

### Report

Status section: word count vs target; section list with word counts; number of references; `[VERIFY]` tags remaining with their sentences; anything the synthesis could not support that the outline asked for.

-----[NEXT_PROMPT]-----

## Fact-check and finish

effort: high

**Standard chain-step constraints — follow these before and during the task below:**

1. **Read `CLAUDE.md` and the plan doc first.** Read `CLAUDE.md` in full and
   obey it throughout. If this step (or the chain) references a plan, outline
   or to-do doc (usually under `docs/` or `data/`), read it in full before doing
   anything else. Follow what it establishes; do not rediscover or contradict it.
2. **Never touch the reviewer's decisions.** Columns H–L of the screening sheet
   belong to the human reviewer. Never fill them, never copy AI suggestions into
   them, and never save the source workbook with openpyxl.
3. **Append a dated status section on completion.** When this step's work is
   done, append a status section to the referenced plan doc (e.g.
   `## Status — YYYY-MM-DD — step N: <name>`) recording what was done, what was
   verified, and anything the next step needs. Use today's real date. If the
   step has no plan doc, put the same summary in your final message instead.
4. **End your final message with a `result:` line.** The very last line must be
   `result: <one-line summary of what this step did>` — nothing after it, not a
   sign-off, not a question, not a tool tally. The chain reads that line to know
   the step finished. Without it the runner has to infer completion from how
   your closing sentence is phrased, which is what makes chains stall.

Plan doc: `docs/plans/glaucoma-today-review-plan.md`. This is step 10 of 10. Invoke the `manuscript-references` skill and follow its fact-checking section; read `references/verifier-brief.md` before briefing verifiers. You are a fresh reader: do not assume the writer was right.

### Tasks

1. **Scripted check.** `factcheck.py paper/manuscript.md --bib paper/bibliography.json --manual paper/bibliography_manual.csv --screening data/LVR_screening_sheet_2_Screening.csv --text-dir data/articles_text --extraction analysis/extraction --prisma paper/prisma_counts.md --out paper/factcheck_report.md --json paper/factcheck_report.json`. Read the Summary and the "To verify" list.
2. **Verifier subagents.** `sonnet`, `medium` or higher, batches of 10–15 items from the "To verify" list, each given only the items, the article text paths and the verifier brief. Each item comes back as a verbatim supporting quote with page, `NOT SUPPORTED`, or `DERIVED: <arithmetic>`; never an estimate, never a web substitute. Fill the Verdict column of `paper/factcheck_report.md`.
3. **Fix the manuscript**, not the report: for every NOT SUPPORTED, MISMATCH, NO CITATION or wrong year, edit the key-bearing `paper/manuscript.md` (correct the number, change the citation, or replace the claim with `[VERIFY]` and a note), then `cite.py check` and `cite.py render` again, then re-run `factcheck.py`. Repeat once. Anything still open gets a written justification line in `paper/factcheck_report.md`.
4. **Independent read.** Read `paper/manuscript_rendered.md` end to end against the plan doc's structure and `paper/format_notes.md`; run `paper/format_checklist.md`; check that the two index questions are quoted verbatim, that no sentence calls any estimate "pooled", that every table and figure is called out, that the DRAFT note and the provisional-inclusion sentence are present, and that the AI disclosure names model ids and tasks. Fix what you find and re-render.
5. **Reporting checklists.** `checklist_status.py paper/checklists/*.md --strict`; fill what you can with section names; list the rest.
6. **Hand-over.** Write `paper/README.md`: what the package contains, what is provisional and why, the reviewer's to-do list in order (fill H–L for records 41–135 and J–K for the pool, confirm the extraction disagreements in `analysis/extraction/disagreements_*.csv`, confirm QUADAS-2/COSMIN rows, decide on the search-string option, type the Scopus counts, remove the DRAFT notes), the command to re-run the chain from the extraction step once H–L are complete (`./lvr chain docs/prompts/glaucoma-today-review-2026-10-26-prompt.md --start-from 5`), and the list of files that are generated and must never be hand-edited. Do not commit or push.

### Report

Status section: fact-check summary before and after fixes (FOUND / WEAK / NOT FOUND / MISMATCH counts); items still open with justification; checklist blanks; final word count; the path `paper/manuscript_rendered.md`.
