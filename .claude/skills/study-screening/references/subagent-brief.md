# Subagent briefs for screening

One subagent per record. Model: sonnet, effort medium or higher (never haiku,
never low). Give the subagent only what is between the fences, with the
placeholders filled. Do not paste the AI columns, the reviewer's decision, the
strict-screening results or any other record: a screener that sees other
verdicts anchors on them, and the agreement statistics then measure the anchor,
not the model. Run independent subagents in parallel in one turn and collect
their single-line answers into the CSV yourself.

Read `docs/AI_title_abstract_screening_rules.md` before filling the brief, so
the rules path and the tie-breakers you quote are current. If the user asks
for the stricter variant, point the subagent at
`results/AI_strict_screening_rules.md` instead and say which one was used in
the output file name.

## The exact Lists strings

Decisions (title/abstract): `Include` | `Exclude` | `Maybe`
Decisions (full text): `Include` | `Exclude`
Exclusion reasons (pick exactly one, character for character):

```
Wrong population (not adults)
No questionnaire/screening item
No accuracy/validation data
Intervention study only
Not about low vision/visual function
Review/opinion/editorial
Conference abstract only
Language (not English/French)
Full text not available
Other (see notes)
```

## Stage 1: title and abstract

````
You are screening ONE record for a systematic review of self-report
questionnaires and screening items that identify adults who need low vision
rehabilitation (LVR). Decide from the title and abstract only. Do not search
the web, do not open other files, do not guess what the full paper contains.

Rules: read /ABS/PATH/docs/AI_title_abstract_screening_rules.md first and
apply it as written. In short: Include when adults (18+) AND a self-report
vision questionnaire or screening item is itself evaluated (accuracy against
measured vision or LVR need; psychometric validation; a planned comparison of
scores with measured visual function; time to administer, feasibility or use
for LVR referral), plus glaucoma PROM studies, LVR referral guidelines and
systematic reviews that pool such evidence. Exclude otherwise, with exactly
ONE reason from the list below, spelled exactly. Maybe only when a relevant
instrument is used in an adult VI/LVR/eye-clinic sample but the abstract does
not say whether it is evaluated, or when there is no abstract ("Missing") and
the title is plausibly relevant. When several reasons apply, use the most
fundamental one: no self-report vision instrument at all, then children only,
then the design reason (intervention only / no validation data / review).

Allowed decisions: Include | Exclude | Maybe
Allowed reasons (Exclude only): Wrong population (not adults) |
No questionnaire/screening item | No accuracy/validation data |
Intervention study only | Not about low vision/visual function |
Review/opinion/editorial | Conference abstract only |
Language (not English/French) | Full text not available | Other (see notes)

Record ID: {ID}
Title: {TITLE}
Abstract: {ABSTRACT or "Missing"}

Answer with exactly one CSV line and nothing else, quoting fields that
contain commas:
{ID},<decision>,<reason or empty>,<one-line rationale: instrument named,
population, what is or is not evaluated, 25 words or fewer>
````

## Stage 2: full text

````
You are screening ONE paper at full text for a systematic review of
self-report questionnaires and screening items that identify adults who need
low vision rehabilitation. Read the text file below; it has one "[page N]"
marker per page. Use grep for "questionnaire", "sensitivity", "specificity",
"Rasch", "validity", "reliability", "AUC", "items" and the Methods heading
first, then read the pages you need. Do not read other files.

Rules: /ABS/PATH/docs/AI_title_abstract_screening_rules.md (same criteria;
now the full text answers what the abstract left open). Decide Include or
Exclude; there is no Maybe at full text. An Exclude takes exactly ONE reason
from the list, spelled exactly. Use "No accuracy/validation data" when the
instrument is only an outcome, predictor or descriptor and its measurement
properties are not analysed; "Full text not available" only if the file is
empty, the wrong paper or supplementary tables only (say so).

Allowed decisions: Include | Exclude
Allowed reasons (Exclude only): Wrong population (not adults) |
No questionnaire/screening item | No accuracy/validation data |
Intervention study only | Not about low vision/visual function |
Review/opinion/editorial | Conference abstract only |
Language (not English/French) | Full text not available | Other (see notes)

Record ID: {ID}
Citation: {AUTHORS} ({YEAR}). {TITLE}
File: {ABS PATH to data/articles_text/<file>.txt}

Answer with exactly one CSV line and nothing else, quoting fields that
contain commas or quotation marks:
{ID},<decision>,<reason or empty>,<one-line rationale: instrument, sample
size and population, reference standard, what is reported; 30 words or
fewer>,<the ONE sentence from the paper that decided it, verbatim, followed
by its page marker, e.g. "... AUC of 0.81" [page 5]>

Report only what the text says. If the deciding fact is not in the text,
write NOT STATED in the quote field and decide from what is there.
````

## Collecting the answers

Append each line under the header `id,decision,reason,rationale` (title/abstract)
or `id,decision,reason,rationale,quote` (full text) in
`analysis/screening/<stage>_ai_<pass>.csv`. Then `apply_decisions.py` validates
every line against the Lists tab before anything touches the workbook, and
refuses the file with the line numbers of the problems; fix those lines (or
re-run that subagent) rather than editing the decision yourself, so the file
stays the subagents' output. Full-text decisions stay in that CSV; the
workbook has no AI full-text columns.
