# PRISMA-S and what this skill supplies for each item

Rethlefsen ML, Kirtley S, Waffenschmidt S, Ayala AP, Moher D, Page MJ,
Koffel JB; PRISMA-S Group. PRISMA-S: an extension to the PRISMA Statement
for Reporting Literature Searches in Systematic Reviews. Systematic
Reviews 2021;10:39. doi:10.1186/s13643-020-01542-z. Sixteen items, meant
to make a search reproducible from the report alone. The companion
checklist is at osf.io/ygn9w. Items 1, 7, 8, 9, 13, 15 and 16 are also
what PRISMA 2020 items 6-7 (Page 2021) and PRISMA-DTA items 7-8 (McInnes
2018) need; the rest go in a supplement.

The prisma-reporting skill's `references/prisma_s.md` gives the same
items with this review's current answers. This file says which field of
`assets/search_log_template.md` and which script output fills each item,
so the log is complete at search time rather than reconstructed later
(the items most often missing from published reviews are 8, 13, 15 and
16: the exact strings, dates and counts nobody wrote down).

| Item | Content | Log field | Produced by |
|---|---|---|---|
| 1 Database name | each database with its platform | Overview row 1 | hand |
| 2 Multi-database searching | platform-level searches of several databases | Overview row 2 | hand (None) |
| 3 Study registries | registries searched | Overview row 3 | hand (None) |
| 4 Online resources and browsing | web sites, journals, tables of contents browsed | Overview row 4, Grey literature | hand |
| 5 Citation searching | backward/forward, tool, which studies | Citation searching table | `snowball.py` -> `snowball_log.json` (seeds, backward, forward, linked, already in sheet, new) |
| 6 Contacts | authors/experts contacted | Overview row 6 | hand (None) |
| 7 Other methods | anything else, including automation and AI | Overview row 7, Strategy development, AI assistance | `pubmed_recall.py` runs (recall figures, dates) |
| 8 Full search strategies | every strategy verbatim, line numbers kept | Runs: strategy blocks | `docs/LVR_search_strategy.md`; `syntax_translate.py` draft after review |
| 9 Limits and restrictions | date, language, type, with justification | Runs: limits | hand; the script reports what `[la]`, `[dp]` and `NOT` lines do |
| 10 Search filters | published filters, as used or modified | Overview row 10 | hand (None) |
| 11 Prior work | strategies adapted from other reviews | Overview row 11 | hand |
| 12 Updates | how and when the search was updated | Updates table | `pubmed_recall.py --diff` (count and recall change between runs) |
| 13 Dates of searches | date each search was last run | Runs headings | `recall_<date>.json` "date"; `snowball_log.json` "date" |
| 14 Peer review | PRESS or other review of the strategy, by whom | Overview row 14 | hand |
| 15 Total records | per database and per other source, before de-duplication | Runs: records retrieved; Citation searching: new candidates | `pubmed_recall.py` "count"; Scopus typed from the UI; `snowball_log.json` |
| 16 Deduplication | process and tool | De-duplication section | Zotero (hand); `snowball.py` excluded.csv and thresholds |

## Flow diagram

PRISMA 2020 shows database records in the left column and "records
identified from other methods" (websites, organisations, citation
searching) in a separate right-hand column that bypasses de-duplication
and goes straight to "reports sought for retrieval". In this workbook
those are Counts!B5 "Other sources" (hand-added key sources 128-135 plus
any snowball additions), so when records are added by
`candidates_to_edits.py` + `set_cells.py --add-rows`, update B5 and the
Citation searching table together; `prisma_flow.py` (prisma-reporting)
reads B5.

## Wording for the Methods (adapt)

"We searched PubMed (NCBI) and Scopus (Elsevier) on {date} for records
from 2000 onward in English or French (full strategies in Supplementary
Table S1). The strategy was developed in several rounds with AI
assistance ({model}) and checked against 36 known relevant records and
14 further records held out from development; it retrieved {k}/36 and
{h}/14. We screened the reference lists and citing articles (OpenAlex,
{date}) of all included studies, prioritising candidates linked to two or
more included studies, and added {n} records. Records were de-duplicated
in Zotero 7 with manual verification. The search was not peer reviewed."
