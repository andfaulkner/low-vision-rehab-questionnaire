# PubMed recall check (2026-10-26)

Source: `docs/LVR_search_strategy.md`. Query: 369 characters.

| | n | found | missed | recall |
|---|---|---|---|---|
| **Records retrieved by the query alone** | | **1180** | | |
| Key sources | 36 | 27 | 9 | 75.0% |
| Held-out papers | 14 | 4 | 10 | 28.6% |

## Key sources missed (9)

| label | PMID | first author, year | title |
|---|---|---|---|
| 79 | 12137395 |   | (no summary) |
| 134 | 27977474 |   | (no summary) |
| 131 | 28460047 |   | (no summary) |
| 89 | 32804622 |   | (no summary) |
| 135 | 36543605 |   | (no summary) |
| 129 | 37142217 |   | (no summary) |
| 38 | 40401755 |   | (no summary) |
| 114 | 40972235 |   | (no summary) |
| 130 | 41598168 |   | (no summary) |

## Held-out papers missed (10)

| label | PMID | first author, year | title |
|---|---|---|---|
| Melbourne Low-Vision ADL Index (2001) | 11328730 |   | (no summary) |
| GQL-15 (Nelson 2003) | 12671469 |   | (no summary) |
| Glaucoma and reading speed (Ramulu 2009) | 19139345 |   | (no summary) |
| Low-vision rehabilitation services in the US (Owsley 2009) | 19433720 |   | (no summary) |
| GAL-9 (Khadka 2011) | 21810983 |   | (no summary) |
| Salisbury self-report vs. VA concordance (2012) | 21962256 |   | (no summary) |
| Italian Glaucoma Symptom Scale (2013) | 23076040 |   | (no summary) |
| Salisbury self-rated vision score (El-Gasim 2013) | 23812494 |   | (no summary) |
| Vision Rehabilitation PPP (2018) | 29108747 |   | (no summary) |
| Referral pathways to low vision services (2023) | 36681848 |   | (no summary) |

<details><summary>Key sources found (27)</summary>

| label | PMID | first author, year | title |
|---|---|---|---|
| 26 | 11124300 |   | (no summary) |
| 65 | 12202503 |   | (no summary) |
| 110 | 12578777 |   | (no summary) |
| 74 | 15505037 |   | (no summary) |
| 39 | 16320144 |   | (no summary) |
| 97 | 16384947 |   | (no summary) |
| 66 | 16877389 |   | (no summary) |
| 120 | 17311573 |   | (no summary) |
| 76 | 17700341 |   | (no summary) |
| 95 | 17962445 |   | (no summary) |
| 93 | 20722170 |   | (no summary) |
| 46 | 21613370 |   | (no summary) |
| 5 | 22978532 |   | (no summary) |
| 112 | 23803778 |   | (no summary) |
| 133 | 25052992 |   | (no summary) |
| 84 | 28430335 |   | (no summary) |
| 27 | 29385405 |   | (no summary) |
| 72 | 30589760 |   | (no summary) |
| 86 | 30776848 |   | (no summary) |
| 105 | 31113297 |   | (no summary) |
| 119 | 33879374 |   | (no summary) |
| 56 | 34146047 |   | (no summary) |
| 52 | 35466953 |   | (no summary) |
| 23 | 38871087 |   | (no summary) |
| 128 | 39292468 |   | (no summary) |
| 30 | 39951057 |   | (no summary) |
| 92 | 41528105 |   | (no summary) |

</details>

## Difference from analysis/search/recall_original_2026-10-26.json (2026-10-26)

- Records: 78 -> 1180 (+1102)
- key: 20/36 -> 27/36 found
  - newly found: 11124300 
  - newly found: 15505037 
  - newly found: 17311573 
  - newly found: 25052992 
  - newly found: 31113297 
  - newly found: 34146047 
  - newly found: 39292468 
- held-out: 0/14 -> 4/14 found
  - newly found: 11448327 
  - newly found: 17065481 
  - newly found: 17700334 
  - newly found: 17700339 
- The query text changed (513 -> 369 characters).

Notes: recall against the key sources is optimistic when the string was tuned on them; the held-out row is the honest figure. Precision (records retrieved per relevant record) is the reviewer's trade-off: every extra arm buys recall with screening time. Record the date, the count and this report in the search log (PRISMA-S items 8, 12, 13, 15).
