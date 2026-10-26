---
name: literature-search
description: Make the search side of the LVR systematic review reproducible and extendable - test the recall of a PubMed string against the key-source PMIDs and the held-out papers (E-utilities), translate PubMed syntax into a Scopus draft and check that a string is balanced, snowball backward references and forward citations from the included studies (OpenAlex, NCBI fallback), de-duplicate candidates against the Screening tab, turn chosen candidates into set_cells.py --add-rows edits, and keep a PRISMA-S search log. Use when asked to re-run, revise, update, extend, test, validate or document the search, "does the string find X", "why did the search miss this paper", recall/precision of a search, "search again with the new string", PubMed vs Scopus syntax, MeSH to Scopus, "check this search string", citation searching, snowballing, reference-list or cited-by checking, "find similar papers to the included ones", search log, PRISMA-S, "other sources" in the PRISMA diagram, or when docs/LVR_search_strategy.md needs re-testing.
---

# Literature search

What exists already: `docs/LVR_search_strategy.md` holds a tested 14-line
PubMed strategy (eight arms), an untested Scopus translation, the 36
key-source PMIDs and 14 held-out PMIDs, and its validation figures
(592 records, 35/36 key sources, 12/14 held-out, 20 Oct 2026). Read
`references/search_notes.md` before touching the string, so you do not
redo that work, and to know the numbers a revision must beat. The original
string (78 records, 20/36 key sources) is in `data/LVR_Q_Study_Outline.md`.

Everything below is advisory output for the reviewer, who decides what the
search is and which records enter the review; and because AI assistance
helped develop and test the strategy, the Methods must say so (the
prisma-reporting skill has the wording).

Where things go: intermediate files under `analysis/search/` (cache,
recall JSON, snowball outputs), the log under `paper/search_log.md`.
Never under `data/`. All scripts are standard-library Python, run with
`python3 -I`, and accept `--cache DIR` plus `--offline`.

```bash
S=.claude/skills/literature-search/scripts
C=analysis/search/cache
```

## 1. Re-run or revise a search and measure recall

Recall against known relevant papers is the only objective test a search
string has: the review cannot know what it never retrieved, so the next
best thing is a list of papers it must retrieve. The key sources are that
list. But the current string was tuned on them, so its 35/36 is
optimistic; the 14 held-out papers, chosen before the string was finished
and never used to tune it, give the honest number (12/14). Keep both sets
separate and never promote a held-out paper into the tuning set.

```bash
python3 -I $S/pubmed_recall.py --from-doc docs/LVR_search_strategy.md --cache $C --out analysis/search/recall_$(date +%F).json
python3 -I $S/pubmed_recall.py --from-doc docs/LVR_search_strategy.md --cache $C --arms 5-12 --final 14   # per-arm table
python3 -I $S/pubmed_recall.py --query-file revised.txt --from-doc docs/LVR_search_strategy.md --cache $C --diff analysis/search/recall_2026-10-26.json
```

- `--from-doc` takes the `#1 ... #14` history from the first fenced block
  and the PMIDs from the tables (first table key sources, second held-out).
  `--query-file` overrides the string, `--pmids FILE` the PMIDs; a plain
  string or a `#N` history both work and the history is expanded as PubMed
  expands it. The expanded string is about 6,000 characters; the script
  POSTs, so URL limits do not matter.
- It reports the count of the string alone, found/missed with titles, the
  per-arm table (`--arms`, with the limits line substituted in by
  `--final`), and `--diff` shows newly found / newly missed PMIDs and the
  change in count against a saved run. `--fail-under 0.95` exits 3 when
  key-source recall drops, for a quick regression check.
- Counts drift by a few records as PubMed indexes (592 on 20 Oct, 593 on
  26 Oct with the same string); a drift of tens means the string changed.

Precision is the reviewer's trade-off, not the script's. Each arm buys
one or more key sources at a price in records to screen (`references/
search_notes.md` lists the price of each). When revising: add an arm only
if it finds a key source or held-out paper nothing else finds, test every
noise fix on its own (the doc did this with `--diff`-style comparisons),
and write down what each change cost. A record the string misses but the
reviewer wants is not a reason to loosen the string if snowballing or a
hand-added "other source" gets it more cheaply (record 84 is the example).

## 2. Translate to Scopus and check syntax

```bash
python3 -I $S/syntax_translate.py --from-doc docs/LVR_search_strategy.md --out analysis/search/scopus_draft.txt --report analysis/search/scopus_translation_notes.md
python3 -I $S/syntax_translate.py --check-balance --query-file scopus_final.txt --dialect scopus
```

The output is a draft. `[ti]` becomes `TITLE()`, `[tiab]` `TITLE-ABS()`
(or `--tiab TITLE-ABS-KEY`), MeSH and Majr become `INDEXTERMS()` with a
warning (Scopus cannot restrict to major headings, explode the tree, or
use subheadings), `[la]` a language limit, `[dp]` `PUBYEAR`, `[ti:~N]` a
`W/N` chain, `NOT` `AND NOT`. `[pt]` publication types mostly have no
equivalent and are listed as untranslatable; `"Practice Guideline"[pt]`
is one. The report lists every construct whose meaning changed. A person
must review the string, run it in Scopus, compare the count with
PubMed's, and check the key sources by exporting the results with DOIs
(a DOI join against the key-source list; snowball.py's dedupe logic does
the same). Put `AND NOT` last: Scopus applies it after everything else.
There is no Scopus API key in this project, so Scopus counts are typed
into the log by hand.

## 3. Snowball from the included studies

Citation searching finds the papers a string cannot: titles that do not
name the population (Mangione 2001, the NEI VFQ-25 paper, is cited by
five of the thirteen currently included records yet no arm finds it).
Cochrane and PRISMA-S expect it, and it is reported as its own line in
the flow diagram ("other methods").

```bash
python3 -I $S/snowball.py --included --cache $C --out analysis/search/snowball            # seeds = included.py output
python3 -I $S/snowball.py --doi 10.1167/tvst.13.9.20 --pmid 25052992 --cache $C --out analysis/search/snowball_test
python3 -I $S/snowball.py --included --cache $C --offline --min-links 2 --out analysis/search/snowball_2plus
```

- `--included` runs the screening-workbook skill's `included.py` (reviewer
  columns only; `--stage ft` once full-text screening is done) or reads a
  saved copy; `--seeds FILE` takes DOIs or PMIDs one per line.
- OpenAlex gives references and citing works with abstracts; NCBI elink is
  the fallback for anything OpenAlex cannot resolve (`--ncbi` forces it;
  its cited-by covers PubMed Central only). Without a key OpenAlex shares
  a small daily budget per IP; a free key in `$OPENALEX_API_KEY` removes
  that. Both services get a contact e-mail from `git config user.email`
  or `--email`.
- Each candidate gets `times_linked` (how many seeds cite or are cited by
  it), `link_type` (backward, forward, both) and `source_ids`.
  `candidates.csv` is sorted by `times_linked`; `excluded.csv` holds the
  candidates already in the Screening tab with the match reason;
  `snowball_log.json` has the per-seed counts for the log.
- De-duplication reads the xlsx through `lvrwb` (the CSV export may be
  stale): DOI match, PMID match via the key-source table, and normalised
  title identical or token-set Jaccard >= 0.85; 0.60-0.85 is flagged
  "possible duplicate" and kept for the screener. `references/methods.md`
  says why those thresholds.

The usual rule: screen the candidates linked from two or more seeds first
(`--min-links 2`; 75 of 1,135 in the 26 Oct test run), because a paper
tied to two included studies is far likelier to be relevant, and then
decide with the reviewer whether the one-link tail (a thousand records
here) is worth a title pass or whether a `--since` year cut makes it
manageable. Seeds with hundreds of citers (a 2000 LVQOL paper has 289)
dominate the tail; `--direction backward` is a cheaper first pass.

## 4. Screen the candidates and add the keepers

Candidates are not records yet. Hand `candidates.csv` to the
**study-screening** skill, which applies the Instructions-tab criteria
to title and abstract and writes suggestions, never decisions. Only
records the reviewer wants in the review go into the workbook:

```bash
python3 -I $S/candidates_to_edits.py analysis/search/snowball/candidates.csv --doi 10.1001/archopht.119.7.1050 --out analysis/search/add_rows.csv
python3 -I .claude/skills/screening-workbook/scripts/set_cells.py --edits analysis/search/add_rows.csv --add-rows --dry-run
python3 -I .claude/skills/screening-workbook/scripts/set_cells.py --edits analysis/search/add_rows.csv --add-rows --export
python3 -I .claude/skills/screening-workbook/scripts/set_cells.py --counts B5 <8 + number added>
```

`candidates_to_edits.py` picks rows (`--doi`, `--pmid`, `--min-links`),
gives them consecutive IDs after the last one in the workbook, and
writes only A-G; it never writes H-L (Notes is the reviewer's) or N-S.
Where each record came from (seed IDs, link counts, date) goes to
`add_rows.provenance.csv` next to the edits file; copy those rows into
the search log's citation-searching table, which is how the PRISMA
"other methods" records stay traceable. `--add-rows` extends every range
(Counts formulas, drop-downs, filters); the DOI hyperlink itself is added
by hand (screening-workbook reference). Then update B5 ("Other sources")
so "Duplicates removed" stays right. A fresh database run goes in B3/B4
instead, with the new dates in the log.

## 5. Log everything (PRISMA-S)

Copy `assets/search_log_template.md` to `paper/search_log.md` the first
time and keep it current: every run gets its date, exact string, limits,
count and the recall figures; every snowball its seeds, date, counts from
`snowball_log.json` and how many went on to screening; de-duplication
method; updates. `references/prisma_s.md` maps the 16 PRISMA-S items to
these fields and to the script outputs. The prisma-reporting skill reads
the log to write the Methods and Supplementary Table S1 and takes the
"other methods" numbers for the flow diagram from the Counts tab, so keep
the log and B5 in agreement.

## When not to use this

- To decide what is in the review: that is screening (study-screening
  skill) and the reviewer's columns (screening-workbook skill).
- For a Scopus run: there is no API; translate, then run it in the Scopus
  UI and type the count in.
- To loosen the string for one paper: compare the arm's cost first; cite
  the paper directly or add it as an "other source" if cheaper.

## Files

- `scripts/lvrsearch.py`: shared client (cache, 3 req/s NCBI, retry on
  429/5xx), history expansion, DOI/PMID/title normalisation, Screening reader.
- `scripts/pubmed_recall.py`, `scripts/snowball.py`,
  `scripts/syntax_translate.py`, `scripts/candidates_to_edits.py`: each has `--help`.
- `assets/search_log_template.md`: the PRISMA-S log.
- `references/search_notes.md`: what the strategy doc established, the numbers to beat, the 26 Oct re-test.
- `references/prisma_s.md`: the 16 items and which output fills each.
- `references/methods.md`: why held-out recall, snowballing rules, dedupe thresholds, Scopus syntax notes, citations.
- `references/validation.md`: what was run and expected vs obtained.
- `evals/`: three offline cases replaying cached responses.
