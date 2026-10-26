# Search log

Keep this file current at search time; it is the source for the Methods
"Search strategy" paragraph, Supplementary Table S1, and the PRISMA 2020
flow diagram's identification boxes. Item numbers refer to PRISMA-S
(Rethlefsen et al. 2021). Replace every {placeholder}; write "None" where
nothing applies rather than deleting the row.

## Overview (items 1-7, 10, 11, 14)

| Item | Field | Entry |
|---|---|---|
| 1 | Databases and platforms | PubMed (MEDLINE, NCBI); Scopus (Elsevier) |
| 2 | Multi-database searching | None |
| 3 | Study registries | None |
| 4 | Online resources and browsing | {e.g. HealthLink BC page (record 132) found by {how}; or None} |
| 5 | Citation searching | Backward references and forward citations of the included studies via OpenAlex (NCBI elink where OpenAlex lacked the record); see "Citation searching" below |
| 6 | Contacts | None |
| 7 | Other methods | Key sources known to the authors (records 128-135); AI-assisted development and recall testing of the strategy (see "Strategy development") |
| 10 | Search filters | None |
| 11 | Prior work | {None, or the review the string was adapted from} |
| 14 | Peer review of the search | {Not peer reviewed / PRESS checklist by {who}, {date}} |

## Strategy development (item 7)

- Original strings: `data/LVR_Q_Study_Outline.md`, run 4 Oct 2026 (PubMed 78, Scopus 88).
- Revised strategy: `docs/LVR_search_strategy.md`, developed {dates} with AI assistance ({model and version}), validated against 36 key sources and 14 held-out papers (`analysis/search/recall_{date}.json`).
- Decision: {original kept / revised adopted on {date}}.

## Runs (items 8, 9, 12, 13, 15)

One block per database per run. Paste the string exactly as run; for
PubMed keep the Advanced Search history line numbers.

### PubMed, {YYYY-MM-DD}

- Platform: NCBI PubMed (web / E-utilities esearch via `pubmed_recall.py`).
- Limits (item 9): publication date 2000 onward; language English or French; titles with child*/pediatric/paediatric/preschool*/infant*/neonat* excluded. Justification: {adult population; reviewer languages; date of the modern instruments}.
- Records retrieved (item 15): {n}.
- Recall (key sources {k}/36; held-out {h}/14): `analysis/search/recall_{date}.json`.
- Strategy:

```
#1  ...
#14 ...
```

### Scopus, {YYYY-MM-DD}

- Platform: Scopus Advanced Search (Elsevier). No API; count typed from the interface.
- Limits: PUBYEAR > 1999; LIMIT-TO LANGUAGE English, French; AND NOT TITLE(child* ...) placed last.
- Records retrieved: {n}.
- Key sources with a DOI present in the export: {k}/{of}.
- Strategy (as pasted, after human review of the `syntax_translate.py` draft):

```
...
```

## Updates (item 12)

| Date | What | PubMed | Scopus | New records to screening |
|---|---|---|---|---|
| 2026-10-04 | original search | 78 | 88 | 127 after de-duplication |
| {date} | {re-run / revised string / alert} | {n} | {n} | {n} |

## Citation searching (item 5)

| Date | Seeds (stage) | Backward | Forward | Linked works | Already in sheet | New candidates | 2+ links | Screened | Added (IDs) |
|---|---|---|---|---|---|---|---|---|---|
| {date} | {n} included at {T/A or FT} | {n} | {n} | {n} | {n} | {n} | {n} | {n} | {IDs} |

Numbers from `analysis/search/snowball*/snowball_log.json`. "Added" records carry "Citation searching (snowball)" in their Notes cell and are counted in Counts!B5 "Other sources".

## De-duplication (item 16)

- Between databases: Zotero 7 duplicate detection, each pair verified by title, year and journal (4 Oct 2026: 39 removed).
- Snowball candidates against the Screening tab: `snowball.py` (DOI, PMID, normalised-title Jaccard >= 0.85; 0.60-0.85 flagged for the screener).
- {Any re-run: method and count}.

## Grey literature and other sources (items 4, 7)

- {Guidelines, reports, web pages consulted; how found; whether they are records in the sheet.}

## AI assistance (report in Methods)

{Model and version} assisted with: strategy development and recall testing (`pubmed_recall.py`), Scopus syntax drafting (reviewed by {who}), citation searching and de-duplication (`snowball.py`), title/abstract screening suggestions. All inclusion decisions were made by the reviewer.
