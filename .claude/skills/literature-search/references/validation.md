# Validation of the scripts

What was run on 26 Oct 2026, live against NCBI E-utilities and OpenAlex
(responses cached in the job scratch directory and, for the eval cases,
under `evals/*/files/cache`). Expected values come from
`docs/LVR_search_strategy.md` (20 Oct 2026) and from hand checks.
Re-run these after any change to the scripts.

## pubmed_recall.py

**Revised 14-line history, `--from-doc docs/LVR_search_strategy.md`.**
Expected (doc): 592 records, 35/36 key sources with record 84 (PMID
28430335) missed, 12/14 held-out with 11448327 and 12671469 missed.
Obtained: 593 records, 35/36 (miss 28430335), 12/14 (misses 11448327,
12671469). The one-record difference is index drift over six days. The
expanded string was 5,972 characters, sent by POST; `[ti:~2]` proximity
and `2000:3000[dp]` were accepted by esearch. 28 requests for the full
run with `--arms 5-12 --final 14`; the replay with `--offline` made 0.

**Per-arm table.** Expected (doc, limits of #14 applied): #5 97, #6 62,
#7 207, #8 28, #9 61, #10 96, #11 59, #12 13, with the "unique key
sources" sets in the doc's table. Obtained: 97, 62, 207, 28, 61, 97, 59,
13; every unique set identical (e.g. #7: 5, 26, 27, 39, 65, 66, 74, 76,
89, 95, 97, 105, 114, 119; #10: 38, 79, 130, 134, 135).

**Original string from the outline.** Expected: 78 records, 20 key
sources. Obtained: 78, 20/36, 0/14 held-out. `--diff` between the two
runs listed 16 newly found and 1 newly missed (28430335) key sources and
+515 records.

**Bookshelf record.** PMID 20722170 (Chou 2009, AHRQ report) has no
`title` in esummary; the script falls back to `booktitle` so it is no
longer reported as "(no summary)".

**Offline.** The eval cache (4 responses, 148 KB) reproduces the
numbers above with `--offline`; a query not in the cache exits 2 with a
message.

## snowball.py

**Three seeds (IDs 128, 133, 92; DOI, PMID and a doi.org URL).** OpenAlex
resolved all three (backward 32/51/16, forward 18/53/2, matching the
counts seen directly in the API: W4402598085 has 32 references and 18
citers). 161 linked works, 6 already in the Screening tab by DOI (IDs 12,
23, 46, 92, 128, 135, including the seeds themselves), 155 candidates, 6
linked from 2 seeds, 127 with an abstract. 10 requests; offline replay
with `--min-links 2` gave the same 6 rows in the same order.

**Included set (`--included`, 13 records at T/A stage).** 1,171 linked
works, 36 already in the sheet, 1,135 candidates: 1,060 with one link, 68
with two, 6 with three, 1 with five (Mangione 2001, NEI VFQ-25, PMID
11448327, the held-out paper the string misses, which validates the
2+ rule). One flagged possible duplicate at Jaccard 0.83 ("Results of
the basic-VRS trial: clinical outcomes and cost-effectiveness" vs ID 99
"The Basic VRS-Effect Study: Clinical Trial Outcomes and Cost..."),
correctly kept for a human. 37 requests. A seed with 289 citers (ID 26)
needed page-based paging; cursor paging was refused without an API key
and the script now uses `page=`.

**NCBI path (`--ncbi --pmid 25052992`).** elink returned reference and
cited-by lists (JSON gives link ids as strings; fixed), esummary filled
titles; 67 candidates, no abstracts (NCBI esummary has none), as
documented.

**Cache miss offline.** An unknown DOI with `--offline` exits 2.

## candidates_to_edits.py and set_cells.py

The three 2+-link candidates of the eval run converted to 21 edits
(rows 137-139, IDs 136-138, columns A-G) plus a provenance sidecar with
seed IDs, link counts and date. A first version also wrote a Notes line
in column L; `set_cells.py` refused it ("column L is the reviewer's"),
which is why provenance now lives in the sidecar and the search log.
`set_cells.py --edits --add-rows --dry-run` then accepted the plan
("extending ranges from row 136 to row 139", "dry run: nothing written");
the live `--export` step was not run, because the workbook must not be
changed during skill development.

## syntax_translate.py

**Revised history.** 5,972 -> 5,234 characters. Untranslatable: "Practice
Guideline"[pt], "Guideline"[pt] (2). Warnings (10): 7 MeSH/Majr terms
incl. the dropped `/rehabilitation` subheading, the 20 `[ti:~2]` phrases
condensed into one W/2 note, the AND NOT placement, the LIMIT-TO form of
the language limit. Spot checks against the doc's hand translation: the
same TITLE term lists for #1 and #3, `PUBYEAR > 1999`, `TITLE(... )
AND NOT TITLE("diabetic retinopathy" OR cerebral OR cortical)` for #6.
Differences a human must settle: the hand version writes the proximity
arm as `(... OR ...) W/2 (vision OR ...)` and uses TITLE-ABS-KEY for
`[tiab]`, and keeps the guideline arm's title terms (the script does the
same, since only the `[pt]` terms are dropped).

**Original string.** Translated to the three-block form in the outline,
with `INDEXTERMS("Vision, Low")` and `INDEXTERMS("Sensitivity and
Specificity" OR "ROC Curve")` replacing the MeSH terms.

**Balance checker.** `("low vision"[ti] OR (questionnaire*[ti]) AND
"self report[tiab]` -> unbalanced quote and unclosed parenthesis, exit 1.
Scopus `TITLE("low vision") AND NOT TITLE(child*) OR TITLE (screening`
-> unclosed parenthesis and "space between field TITLE and (", exit 1.
The eval's `broken.txt` -> unclosed parenthesis and bare NOT. The
14-line history -> balanced, references all defined and earlier, exit 0.

## Not verified

- The Scopus draft was not run in Scopus (no access); its count and recall
  are unknown.
- Jaccard thresholds were checked on the one real near-duplicate pair
  above and on synthetic variants (subtitle added, trailing period, one
  word changed), not on a labelled duplicate set.
- The eval cases were not run with `claude plugin eval`; their expected
  outcomes come from running the scripts on the case inputs.
- Citations in `methods.md` were written from memory; verify page numbers
  before quoting them in the manuscript.
