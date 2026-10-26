# Briefing a subagent to extract one paper

One paper per subagent, fresh context, no shared state. The brief below is the whole
world the subagent sees, so it names the file, the schema, the output path and the
rules. Fill the `<...>` slots and send it as the prompt. Use at least a sonnet-class
model at medium effort (the user's standing rule: never haiku, never low effort).

For dual extraction, send the same brief to two subagents with different output
folders (`passA/`, `passB/`) and do not tell either what the other found. Run
`reconcile.py` on the results and have the reviewer settle every disagreement from the
cited page. If only one subagent pass exists, the reviewer's own check of every number
against the page is the second pass.

---

```
You are extracting ONE study for a systematic review of self-report questionnaires and
screening questions for low vision rehabilitation need. Work only from the text file;
do not open the PDF, do not search the web, do not use your memory of the paper.

Study: Screening ID <ID>, <Surname Year>
Text: "<repo>/data/articles_text/<file>.txt"   (pages are marked [page N])
Schema: <repo>/.claude/skills/data-extraction/references/schema.md  (read it first)
Pitfalls: <repo>/.claude/skills/data-extraction/references/pitfalls.md (read sections 1-4, 8, 10, 14)
Templates with the exact headers: <repo>/.claude/skills/data-extraction/assets/*.csv

Write four CSVs to <repo>/analysis/extraction/<passX>/<ID>/ :
  studies.csv      one row
  dta.csv          one row per index test x threshold x reference standard x unit x subgroup
  effects.csv      one row per correlation / AUC / proportion / mean / mean difference
  instruments.csv  one row per instrument the study uses (facts from THIS paper only)
Use the template headers verbatim. Write an empty file with only the header when a file
has no rows.

Rules
- grep first: grep -n -i 'specificity\|sensitiv\|AUC\|ROC\|cut-off\|cutoff\|correlat\|Table' on the
  text, then read around the hits with offsets. Read the Methods for the reference
  standard definition and the participants table for n and diagnoses.
- Every value gets the page it was read from. Values from tables: cite the table and
  its page.
- Write NR for anything the paper does not report. Do not estimate, do not infer from
  the abstract, do not fill from another paper.
- Copy thresholds and reference-standard definitions verbatim (eye, correction,
  direction, units), then add ref_threshold_logmar from the conversion table.
- Counts: enter TP/FP/FN/TN only when the paper gives them or they follow by subtraction
  from reported totals; put the arithmetic in `derivation`. Leave the cells blank when
  only sens/spec are given; the lead will run reconstruct_2x2.py.
- Run the validator before you finish:
    python3 -I <repo>/.claude/skills/data-extraction/scripts/validate_extraction.py <repo>/analysis/extraction/<passX>/<ID> --quiet-info
  and fix every ERROR that is yours to fix (missing instruments.csv rows are expected
  if the instrument is defined elsewhere; say so).
- Never edit anything under data/.

Report back in under 200 words: the rows you wrote per file, every place the paper was
ambiguous and what you chose, anything you could not find, and the validator's error
count.
```
