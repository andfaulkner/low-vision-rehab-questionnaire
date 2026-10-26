# PROVISIONAL: PRISMA 2020 flow diagram counts

**PROVISIONAL.** The reviewer has decided 40 of 135 records at title/abstract and none at full text (workbook version: `paper/figures/prisma_flow_reviewer.png`, `paper/prisma_counts_reviewer.md`, which fails its arithmetic checks by construction). The numbers below combine the reviewer's decisions where they exist with AI suggestions for the rest (plan doc rule 6): excluded at title/abstract = 135 minus the 54-record full-text pool (`analysis/screening/ft_pool.csv`); full-text exclusions and inclusions are the AI full-text decisions (`analysis/screening/ft_ai_decisions.csv`); the 31 included records are `analysis/screening/provisional_included.csv`. The 6 reports with no usable text (IDs 30, 128, 129, 132, 133, 135) are counted as not retrieved, not as excluded. Title/abstract exclusion reasons are not tabulated because 95 of the 135 decisions are not the reviewer's. Replace everything here once H-L are complete.

Source: `analysis/screening/*.csv` via a hand-built JSON (provisional). Diagram: `paper/figures/prisma_flow.png`. Other-methods mode: `same-pipeline`.

| Stage | n | Detail |
|---|---:|---|
| Records identified from databases and registers | 166 | PubMed 78; Scopus 88 |
| Records identified from other methods | 8 | Key sources from the study outline 8 |
| Total records identified | 174 |  |
| Duplicate records removed | 39 |  |
| Records removed by automation tools | 0 |  |
| Records removed for other reasons | 0 |  |
| Records screened (title/abstract) | 135 |  |
| Records excluded at title/abstract | 81 |  |
| Reports sought for retrieval | 54 |  |
| Reports not retrieved | 6 |  |
| Reports assessed for eligibility | 48 |  |
| Reports excluded at full text | 17 |  |
| Reports of included studies | 31 |  |
| Studies included in review | 31 |  |

## Exclusion reasons

| Reason | Title/abstract | Full text |
|---|---:|---:|
| Intervention study only | 0 | 3 |
| No accuracy/validation data | 0 | 11 |
| Not about low vision/visual function | 0 | 1 |
| Review/opinion/editorial | 0 | 2 |

- Records identified from other sources were title/abstract-screened together with the database records (--other-mode same-pipeline), so the arrow from the other-methods box joins 'Records screened'. Say so in the figure legend.

## Results text

The searches identified 166 records (PubMed, n = 78; Scopus, n = 88), and 8 further records were identified from other sources (Key sources from the study outline). After 39 duplicate records were removed, 135 records were screened by title and abstract and 81 were excluded. The full texts of 54 reports were sought; 6 could not be retrieved, and 48 were assessed for eligibility. Of these, 17 were excluded (no accuracy/validation data, n = 11; intervention study only, n = 3; review/opinion/editorial, n = 2; not about low vision/visual function, n = 1). In total, 31 studies (31 reports) were included in the review (Figure 1).
