# What the search strategy work already established

Summarised from `docs/LVR_search_strategy.md` (20 Oct 2026) and
`data/LVR_Q_Study_Outline.md`, so this skill builds on it rather than
repeating it. Read the doc itself for the full strings.

## The original search (run 4 Oct 2026)

Three concepts ANDed: low vision/visual impairment/legal blindness;
questionnaire/self-report/screening question/survey; accuracy terms
(sensitivity, specificity, ROC, AUC, "diagnostic accuracy"). Limits: 2000
onward, English or French, NOT child*/pediatric/paediatric in title.
PubMed 78, Scopus 88, 166 total, 39 duplicates, 127 screened. It finds
20 of the 36 key sources and none of the 14 held-out papers, partly
because `sensitivity[tiab]` matches "contrast sensitivity" and partly
because the accuracy concept excludes validation, Rasch, referral and
guideline papers.

The two papers `docs/todos/prompt-second-draft.md` names as missed,
10.1167/tvst.13.9.20 (Legge/Wu 2024, PMID 39292468) and
10.1167/iovs.14-14138 (Nguyen 2014, PMID 25052992), are records 128 and
133, hand-added; the revised string finds both (arms #5 and #9).

## The revised strategy (not yet adopted as the review's search)

A union of eight title-focused arms (#5-#12) built from four blocks
(#1 population, #2 population + major MeSH, #3 instrument, #4 measurement),
limited in #14. Each arm answers one of the four questions the key
sources answer: self-report vs measured vision; questionnaire measurement
(validation, Rasch); referral, services, guidelines; glaucoma disability
beyond acuity. The main precision lever is requiring concepts in the
title (or as major MeSH).

Validation figures in the doc (20 Oct 2026):

| | Original | Revised |
|---|---|---|
| PubMed records | 78 | 592 |
| Key sources found (36 in PubMed; record 132 is a web page) | 20 | 35 |
| Held-out papers found (14) | 0 | 12 |
| AI strict-screening Excludes retrieved (88) | 57 | 17 |
| Records not already in the sheet | - | 539 |

Misses: key source 84 (Murro 2017, Stargardt, PMID 28430335; the arm that
finds it costs 58 records); held-out Mangione 2001 (NEI VFQ-25
development, PMID 11448327; title does not mention low vision) and Nelson
2003 (GQL-15, PMID 12671469; would need a glaucoma QoL vs visual field arm
costing 157 records). Both held-out misses are better cited directly, or
reached by snowballing: Mangione 2001 is the most-linked snowball
candidate from the current included set.

Price of each arm (records, key sources only that arm finds): #5 97 (120,
128); #6 62 (30, 92, 93, 112); #7 207 (14 records); #8 28 (129); #9 61
(110, 131, 133); #10 96 (38, 79, 130, 134, 135); #11 59 (52, 72); #12 13
(56). Dropping #11 and #12 saves 53 records and loses 3 key sources.

Noise fixes already tested one at a time and kept: `[ti:~2]` proximity in
#5 (saves 29), excluding diabetic retinopathy / cerebral / cortical from
#6 (17), `screening[ti]` not `screen*[ti]`, guideline arm requiring
rehabilitat*/referral*/management, no `survey*[ti]` in #3, no
`outcome*[ti]` / `performance[ti]` in #4. Keep `predict*[ti]` in #4
(record 76 depends on it). Optional: `schoolchild*[ti]` in the #14
exclusions (about 3 records).

Scopus: translation written but never run (no API key). Put `AND NOT`
last: the original Scopus string had it before the language limit.

## Re-test on 26 Oct 2026 with this skill (`pubmed_recall.py`)

| | Doc (20 Oct) | Obtained (26 Oct) |
|---|---|---|
| Revised: records | 592 | 593 |
| Revised: key sources | 35/36 | 35/36 (miss: 84) |
| Revised: held-out | 12/14 | 12/14 (miss: 11448327, 12671469) |
| Original: records | 78 | 78 |
| Original: key sources | 20 | 20/36 |
| Original: held-out | - | 0/14 |
| Arms #5 #6 #7 #8 #9 #10 #11 #12 | 97 62 207 28 61 96 59 13 | 97 62 207 28 61 97 59 13 |

The per-arm "unique key sources" sets were identical to the doc's table.
The one-record drifts (592 -> 593, #10 96 -> 97) are PubMed indexing new
records between the two dates, not a change in the string. These are the
numbers a revision must beat: at least 35/36 and 12/14 for no more than
about 600 records, or a documented reason to accept less.

## What a reviewer decision could change

28 of the 37 key sources are AI strict-screening Includes the reviewer
has not confirmed. If the reviewer excludes some, the arms that exist
only for them (#8 for 129, #12 for 56, #11 for 52 and 72) can be
dropped, which is why `--arms` reports the unique key sources per arm.
Re-run the recall check whenever the key-source list changes, with the
list as `--pmids` rather than editing the doc's table by hand.
