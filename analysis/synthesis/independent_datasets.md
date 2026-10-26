# Independent datasets (31 from 32 studies)

Grouping rule: pairs at confidence >= **probable** share a dataset_id. These are suggestions from surname, cohort, n, year and site matching; the reviewer confirms each grouping against the papers and records the decision in the `dataset_id` column of studies.csv (the `--assign` copy is the place to do it). Confirmed groupings are reported in the Methods as the unit of counting for the synthesis.

| dataset_id | studies | confidence | why |
|---|---|---|---|
| D01 | Gothwal 2012 (ID 5, n=351) | independent |  |
| D02 | Wolffsohn 2000 (ID 26, n=278) | independent |  |
| D03 | Labreche 2018 (ID 27, n=89) | independent |  |
| D04 | Rowe 2025 (ID 38, n=NR) | independent |  |
| D05 | Babcock-Parziale 2005 (ID 39, n=190) | independent |  |
| D06 | Oviedo-Cáceres 2023 (ID 41, n=NR) | independent |  |
| D07 | Tabrett 2011 (ID 46, n=100) | independent |  |
| D08 | Agathos 2025 (ID 55, n=125) | independent |  |
| D09 | Sahu 2021 (ID 56, n=46) | independent |  |
| D10 | Wu 2016 (ID 63, n=100) | independent |  |
| D11 | Stelmack 2002 (ID 65, n=128) | independent |  |
| D12 | Stelmack 2006 (ID 66, n=285) | independent |  |
| D13 | Selivanova 2019 (ID 72, n=109) | independent |  |
| D14 | Szlyk 2004 (ID 74, n=117) | independent |  |
| D15 | La Grow 2007 (ID 76, n=184) | independent |  |
| D16 | Gresset 2002 (ID 79, n=65) | independent |  |
| D17 | Murro 2017 (ID 84, n=16) | independent |  |
| D18 | Smith 2013 (ID 85, n=10) | independent |  |
| D19 | Macnaughton 2019 (ID 86, n=60) | independent |  |
| D20 | Malkin 2013 (ID 88, n=77) | independent |  |
| D21 | Smith 2020 (ID 89, n=44) | independent |  |
| D22 | Wu 2026 (ID 92, n=385), Wu 2024 (ID 128, n=385) | high | Wu 2026 / Wu 2024: cross-ref: Wu 2026 cohort/notes cite ID 128; authors: 2 shared surname(s) (wu, yueh hsun); Jaccard 1.00; identical n: 385; recruitment years overlap: 2019-2024 vs 2019-2022 |
| D23 | Chou 2009 (ID 93, n=NR) | independent |  |
| D24 | Massof 2007 (ID 95, n=405) | independent |  |
| D25 | Subramanian 2006 (ID 97, n=42) | independent |  |
| D26 | Di Maggio 2020 (ID 105, n=131) | independent |  |
| D27 | Sumi 2003 (ID 110, n=147) | independent |  |
| D28 | Dickson 2012 (ID 112, n=69) | independent |  |
| D29 | Surawatsatien 2026 (ID 114, n=301) | independent |  |
| D30 | Pérez-Mañá 2022 (ID 119, n=365) | independent |  |
| D31 | Bibby 2007 (ID 120, n=30) | independent |  |

**1** dataset(s) contain more than one study and need confirmation.

## Flagged but not merged (below --merge probable)

- Stelmack 2002 / Stelmack 2006 (possible): authors: 2 shared surname(s) (joan, stelmack); Jaccard 1.00
- Smith 2013 / Smith 2020 (possible): authors: 2 shared surname(s) (smith, theresa); Jaccard 1.00

Check these against the papers too; re-run with `--merge possible` to join them, or set `dataset_id` by hand.

Rule for synthesis: when two papers share a dataset, count it once; take the larger or more complete report for the main table and present the other beside it, never as a second data point (SWiM item 1; Cochrane Handbook ch. 12 on the unit of analysis).
