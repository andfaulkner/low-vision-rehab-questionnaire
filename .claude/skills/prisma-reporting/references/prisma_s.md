# PRISMA-S: what the search log must record

Rethlefsen ML, et al. PRISMA-S: an extension to the PRISMA statement for reporting literature searches in systematic reviews. Syst Rev 2021;10:39. Sixteen items; most reviewers fail items 8, 13, 15 and 16 because the information was never written down at search time. Keep a search log (`docs/LVR_search_strategy.md` is the current one) with the fields below, so the Methods and Supplementary Table S1 can be written from it.

| Item | What to record | This review |
|---|---|---|
| 1 Database name | Each database and its platform (PubMed via NCBI; Scopus via Elsevier). | PubMed (NCBI), Scopus (Elsevier). |
| 2 Multi-database searching | If several databases were searched at once on one platform, say which. | N/A. |
| 3 Study registries | Registries searched, or none. | None: say so. |
| 4 Online resources and browsing | Websites, tables of contents, print sources browsed, and how. | HealthLink BC page (record 132), if kept; otherwise none. |
| 5 Citation searching | Whether reference lists or citing articles were checked, and how (which tool, which studies). | Key sources from the outline (records 128–135): describe how they were identified (prior knowledge of the authors, reference lists). |
| 6 Contacts | Authors, experts or manufacturers contacted. | None: say so. |
| 7 Other methods | Anything else (e.g. AI-assisted strategy development; the held-out test set used to validate the string). | Describe the revised multi-arm strategy's development and its validation against 36 key sources and 14 held-out papers, and that AI assistance was used. |
| 8 Full search strategies | Every strategy, copied and pasted exactly as run, for every database, with the line numbers. | Paste the PubMed line-by-line history and the Scopus string verbatim into Supplementary Table S1. |
| 9 Limits and restrictions | Date, language, publication-type limits, with justification. | 2000 onward; English or French; `NOT child*/pediatric/paediatric` in titles. Justify each. |
| 10 Search filters | Published filters used, as designed or modified, with citation. | None. |
| 11 Prior work | Strategies adapted from previous reviews, cited. | None, unless the outline's string came from an earlier review. |
| 12 Updates | How searches were updated (re-run, alerts) and when. | If the revised string replaces the original, report both runs with their dates and counts, or report only the final one and say the original was superseded before screening. |
| 13 Dates of searches | The date each search was last run. | 4 Oct 2026 (original); {date} for any re-run. |
| 14 Peer review | Whether the search was peer-reviewed (e.g. PRESS checklist) and by whom. | Say "not peer reviewed" if so. |
| 15 Total records | Records identified from each database and other source, before de-duplication. | PubMed 78, Scopus 88, other 8 (from the Counts tab; these feed the flow diagram). |
| 16 Deduplication | Process and software used. | Zotero 7 duplicate detection, each pair verified by title, year and journal. |

Items 1, 7, 8, 9, 13, 15 and 16 map onto PRISMA 2020 items 6–7 and PRISMA-DTA items 7–8; the rest go in the supplement. If the search is re-run with the revised strategy, the flow diagram's database counts, the duplicate count and the screening numbers all change: re-export the Counts tab and re-run `prisma_flow.py` rather than editing the figure.
