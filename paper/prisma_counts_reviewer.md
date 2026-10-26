# PRISMA 2020 flow diagram counts

Source: `/Users/andfaulkner/projects/research/brilliant-cutie/low-vision-rehab-questionnaire/data/LVR_screening_sheet_2_Counts.csv`. Diagram: `paper/figures/prisma_flow.png`. Other-methods mode: `same-pipeline`.

> **DRAFT: the counts do not reconcile.** Fix the workbook or pass `--override` before using these numbers.

> - records screened (135) - excluded (27) = 108, but reports sought = 13
> - reports sought (13) - not retrieved (0) = 13, but reports assessed = 0

> Notes:

> - screening is incomplete: 40 of 135 records have a title/abstract decision, so everything below 'Records screened' is provisional

| Stage | n | Detail |
|---|---:|---|
| Records identified from databases and registers | 166 | PubMed 78; Scopus 88 |
| Records identified from other methods | 8 | Other sources 8 |
| Total records identified | 174 |  |
| Duplicate records removed | 39 |  |
| Records removed by automation tools | 0 |  |
| Records removed for other reasons | 0 |  |
| Records screened (title/abstract) | 135 |  |
| Records excluded at title/abstract | 27 |  |
| Reports sought for retrieval | 13 |  |
| Reports not retrieved | 0 |  |
| Reports assessed for eligibility | 0 |  |
| Reports excluded at full text | 0 |  |
| Reports of included studies | 0 |  |
| Studies included in review | 0 |  |

## Exclusion reasons

| Reason | Title/abstract | Full text |
|---|---:|---:|
| Intervention study only | 1 | 0 |
| No questionnaire/screening item | 18 | 0 |
| Not about low vision/visual function | 6 | 0 |
| Wrong population (not adults) | 2 | 0 |

- The workbook counts included reports; studies = reports unless you override studies_included (several reports of one study, or one report of several studies).
- Records identified from other sources were title/abstract-screened together with the database records (--other-mode same-pipeline), so the arrow from the other-methods box joins 'Records screened'. Say so in the figure legend.

## Results text

The searches identified 166 records (PubMed, n = 78; Scopus, n = 88), and 8 further records were identified from other sources (Other sources). After 39 duplicate records were removed, 135 records were screened by title and abstract and 27 were excluded. The full texts of 13 reports were sought, and 0 were assessed for eligibility. In total, zero studies (0 reports) were included in the review (Figure {N}).

_Screening is still in progress; regenerate this file when the workbook is complete._
