# Revised search strategy (multi-arm)

This is a proposed replacement for the PubMed and Scopus strings in the "Lit review strategy" section of `data/LVR_Q_Study_Outline.md`. It was developed and tested on 20 Oct 2026, with AI assistance, so that it finds all the key sources in the outline while retrieving as few out-of-scope records as possible. It has not been run as the review's search yet, and the review's methods must report that AI assistance was used to develop it.

## Why the original string could not be fixed by loosening or tightening it

The key sources answer four different questions:

1. Does self-report agree with measured vision?
2. How are low-vision questionnaires measured (validation, Rasch, psychometrics)?
3. Who is referred to LVR, and what do the services and guidelines say?
4. How does glaucoma disable beyond visual acuity?

A single "low vision AND questionnaire AND accuracy" chain has to be loose enough for the most loosely titled paper in every group, so it lets everything in. Tightening it drops whole groups. The original string's accuracy terms also worked partly by accident: `sensitivity[tiab]` matches "contrast sensitivity".

The revised strategy is a union of 8 narrow **arms**, one or more per question. Each arm needs its concepts in the **title** (or as a major MeSH heading), not just the abstract. That is the main precision lever: each arm stays small, so the total stays small.

## PubMed string

Clear the search history in PubMed Advanced Search, then enter each line in order so the `#` numbers line up. Line #14 is the final result.

```
#1  "low vision"[ti] OR "visual impairment*"[ti] OR "vision impairment*"[ti] OR "visually impaired"[ti] OR "impaired vision"[ti] OR "reduced vision"[ti] OR "visual disabilit*"[ti] OR "legal blindness"[ti] OR "legally blind"[ti] OR "vision loss"[ti] OR "sight loss"[ti] OR "partially sighted"[ti] OR "vision rehabilitation"[ti] OR "visual rehabilitation"[ti] OR "blind rehabilitation"[ti]
#2  #1 OR "Vision, Low"[Majr] OR "Persons with Visual Disabilities"[Majr] OR "Blindness/rehabilitation"[Majr]
#3  questionnaire*[ti] OR "self-report*"[ti] OR "self report*"[ti] OR "self-rated"[ti] OR "self-assess*"[ti] OR "screening question*"[ti] OR "patient-reported"[ti] OR PROM[ti] OR PROMs[ti] OR "quality of life"[ti] OR "quality-of-life"[ti] OR "activity limitation*"[ti] OR "activities of daily living"[ti] OR "visual function*"[ti] OR "independence measure"[ti] OR "outcome measure*"[ti] OR VFQ*[ti] OR "activity inventory"[ti] OR LVQOL[ti] OR "impact of vision impairment"[ti] OR LVIM*[ti] OR "VF-14"[ti] OR "EQ-5D"[ti] OR "GQL-15"[ti] OR "GAL-9"[ti] OR "glaucoma symptom scale"[ti] OR "ADL index"[ti]
#4  validat*[ti] OR validity[ti] OR psychometric*[ti] OR Rasch[ti] OR "measurement properties"[ti] OR reliab*[ti] OR reproducib*[ti] OR responsive*[ti] OR accuracy[ti] OR concordance[ti] OR agreement[ti] OR "item response"[ti] OR version[ti] OR translat*[ti] OR "cross-cultural"[ti] OR design[ti] OR development[ti] OR measuring[ti] OR measurement[ti] OR predict*[ti]
#5  (("self reported vision"[ti:~2] OR "self reported visual"[ti:~2] OR "self reported sight"[ti:~2] OR "self reported eyesight"[ti:~2] OR "self reported blindness"[ti:~2] OR "self rated vision"[ti:~2] OR "self rated visual"[ti:~2] OR "self rated sight"[ti:~2] OR "self rated eyesight"[ti:~2] OR "self rated blindness"[ti:~2] OR "self assessed vision"[ti:~2] OR "self assessed visual"[ti:~2] OR "self assessed sight"[ti:~2] OR "self assessed eyesight"[ti:~2] OR "self assessed blindness"[ti:~2] OR "self perceived vision"[ti:~2] OR "self perceived visual"[ti:~2] OR "self perceived sight"[ti:~2] OR "self perceived eyesight"[ti:~2] OR "self perceived blindness"[ti:~2]) AND ("Visual Acuity"[Mesh] OR "visual acuity"[tiab])) OR ("Visual Acuity"[Majr] AND "Self Report"[Mesh])
#6  (#1 AND screening[ti]) NOT ("diabetic retinopathy"[ti] OR cerebral[ti] OR cortical[ti])
#7  (#2 AND #3 AND #4) OR (#2 AND Rasch[tiab])
#8  glaucoma*[ti] AND #3 AND (validat*[ti] OR validity[ti] OR psychometric*[ti] OR Rasch[ti] OR "measurement properties"[ti] OR reliab*[ti] OR responsive*[ti] OR version[ti] OR translat*[ti])
#9  glaucoma*[ti] AND (reading[ti] OR "Reading"[Majr] OR disabilit*[ti])
#10 (("low vision"[ti] OR "vision rehabilitation"[ti] OR "visual rehabilitation"[ti]) AND (referral*[ti] OR refer[ti] OR referred[ti] OR "practice pattern*"[ti])) OR (#1 AND (guideline*[ti] OR "Practice Guideline"[pt] OR "Guideline"[pt]) AND (rehabilitat*[tiab] OR referral*[tiab] OR management[tiab])) OR (#1 AND (service*[ti] OR utili*[ti] OR uptake[ti] OR barrier*[ti]) AND rehabilitat*[ti])
#11 #1 AND ("vision-related quality of life"[ti] OR "vision related quality of life"[ti] OR "vision-related"[ti] OR "vision-specific"[ti])
#12 "low vision"[ti] AND predict*[ti]
#13 #5 OR #6 OR #7 OR #8 OR #9 OR #10 OR #11 OR #12
#14 #13 AND (english[la] OR french[la]) AND 2000:3000[dp] NOT (child*[ti] OR pediatric[ti] OR paediatric[ti] OR preschool*[ti] OR infant*[ti] OR neonat*[ti])
```

Lines #1–#4 are building blocks (population, instrument, measurement, self-report). Lines #5–#12 are the arms.

## What each arm finds

Counts are from PubMed on 20 Oct 2026, with the limits in #14 applied. "Unique" means records that no other arm finds. Record numbers are the IDs in the Screening tab.

| Arm | Question | Records | Unique | Key sources that only this arm finds |
|---|---|---|---|---|
| #5 | Self-report vs. measured acuity | 97 | 93 | 120 Bibby, 128 Legge 2024 |
| #6 | Screening for low vision | 62 | 59 | 30 Stalin, 92 Wu 2026, 93 Chou, 112 Dickson |
| #7 | Low-vision questionnaires and their measurement | 207 | 181 | 5, 26, 27, 39, 65, 66, 74, 76, 89, 95, 97, 105, 114, 119 |
| #8 | Glaucoma PROMs | 28 | 28 | 129 PROMs review 2023 |
| #9 | Glaucoma disability beyond acuity | 61 | 60 | 110 Sumi, 131 Swenor, 133 Nguyen |
| #10 | LVR referral, services and guidelines | 96 | 89 | 38 ESO stroke, 79 Gresset, 130 Life 2026, 134 Kaleem, 135 PPP 2023 |
| #11 | Vision-related quality of life in visual impairment | 59 | 41 | 52 Pengo, 72 Selivanova |
| #12 | Predicting low-vision outcomes | 13 | 12 | 56 Sahu |

## How it was validated

| | Original string | Revised string |
|---|---|---|
| PubMed records | 78 | **592** |
| Key sources found (36 in PubMed) | 20 | **35** |
| Held-out similar papers found (14) | — | **12** |
| Records the AI strict screening excluded (88 in PubMed) | 57 | **17** |
| Records not already in the Screening tab | — | 539 |

- **Key sources (the test set):** the 37 records marked Include in `results/LVR_strict_screening.csv` (IDs 5–135). 36 are in PubMed; record 132 (HealthLink BC) is a web page. 28 of them are AI strict-screening Includes, which the reviewer has not confirmed yet. If the reviewer excludes some of them, the arms that exist only for those papers can be dropped (see below).
- **Held-out papers:** 14 papers similar to the key sources, chosen before the string was finished and never used to tune it. The string finds 12. It misses:
  - **GQL-15** (Nelson 2003, PMID 12671469). Finding it would need a "glaucoma quality of life vs. visual field" arm that adds 157 records and no key sources.
  - **NEI VFQ-25 development** (Mangione 2001, PMID 11448327). Its title does not mention low vision.

  Both are better cited directly.
- **Precision:** in a random sample of 60 new records, judged by title, about 35–40% were clearly on-topic and about 25% were borderline. In the original string, 20 of the 78 PubMed records (26%) were key sources.
- **The one key source missed:** record 84 (Murro 2017, Stargardt quality of life). Adding the arm `"Vision, Low"[Majr] AND "quality of life"[ti]` finds it, but adds 58 records for that one paper. It is already in the Screening tab, so this arm is left out.

## Options to make it smaller

| Change | Records saved | Key sources lost |
|---|---|---|
| Drop #12 | 12 | 56 Sahu |
| Drop #11 | 41 | 52 Pengo, 72 Selivanova |

Each noise fix already in the string was tested on its own and lost no key sources or held-out papers:

- Proximity search in #5 (`[ti:~2]`) ties "self-reported" to "vision", so self-reported sleep, driving and so on are not found. It saves 29 records.
- Excluding diabetic retinopathy and cerebral/cortical topics from the screening arm (#6) saves 17.
- `screening[ti]` instead of `screen*[ti]` leaves out "screen readers".
- Requiring rehabilitation, referral or management with `guideline*` in #10 leaves out web-accessibility, pharmacy and dietary guidelines.
- `survey*[ti]` is left out of #3, because it found epidemiological prevalence surveys.
- `outcome*[ti]` and `performance[ti]` are left out of #4. Do not remove `predict*[ti]` from #4: without it, record 76 (La Grow 2007) is lost.

Optional: `child*` does not match "schoolchildren" (record 32 got in this way). Adding `schoolchild*[ti]` to the exclusions in #14 removes about 3 records. It is not in the tested string.

## Scopus string

**This has not been run.** No Scopus API key was available. Scopus cannot restrict MeSH to major headings or filter by publication type, so this version uses title terms and `INDEXTERMS` instead. The same MeSH-free logic run in PubMed gave 594 records and the same 35 key sources. Expect a higher count in Scopus, because it indexes more journals.

```
( ( TITLE( ( "self report*" OR "self rated" OR "self assessed" OR "self perceived" ) W/2 ( vision OR visual OR sight OR eyesight OR blindness ) ) AND TITLE-ABS-KEY( "visual acuity" ) )
 OR ( TITLE( "visual acuity" ) AND TITLE-ABS-KEY( "self report*" ) )
 OR ( TITLE( "low vision" OR "visual impairment*" OR "vision impairment*" OR "visually impaired" OR "impaired vision" OR "reduced vision" OR "visual disabilit*" OR "legal blindness" OR "legally blind" OR "vision loss" OR "sight loss" OR "partially sighted" OR "vision rehabilitation" OR "visual rehabilitation" OR "blind rehabilitation" ) AND TITLE( screening ) AND NOT TITLE( "diabetic retinopathy" OR cerebral OR cortical ) )
 OR ( ( TITLE( "low vision" OR "visual impairment*" OR "vision impairment*" OR "visually impaired" OR "impaired vision" OR "reduced vision" OR "visual disabilit*" OR "legal blindness" OR "legally blind" OR "vision loss" OR "sight loss" OR "partially sighted" OR "vision rehabilitation" OR "visual rehabilitation" OR "blind rehabilitation" ) OR INDEXTERMS( "Vision, Low" OR "low vision" OR "Persons with Visual Disabilities" OR "Visually Impaired Persons" ) ) AND ( ( TITLE( questionnaire* OR "self report*" OR "self rated" OR "self assess*" OR "screening question*" OR "patient reported" OR prom OR proms OR "quality of life" OR "activity limitation*" OR "activities of daily living" OR "visual function*" OR "independence measure" OR "outcome measure*" OR vfq* OR "activity inventory" OR lvqol OR "impact of vision impairment" OR lvim* OR "VF-14" OR "EQ-5D" OR "GQL-15" OR "GAL-9" OR "glaucoma symptom scale" OR "ADL index" ) AND TITLE( validat* OR validity OR psychometric* OR rasch OR "measurement properties" OR reliab* OR reproducib* OR responsive* OR accuracy OR concordance OR agreement OR "item response" OR version OR translat* OR "cross-cultural" OR design OR development OR measuring OR measurement OR predict* ) ) OR TITLE-ABS-KEY( rasch ) ) )
 OR ( TITLE( glaucoma* ) AND TITLE( questionnaire* OR "self report*" OR "self rated" OR "self assess*" OR "patient reported" OR prom OR proms OR "quality of life" OR "activity limitation*" OR "visual function*" OR vfq* OR "EQ-5D" OR "GQL-15" OR "GAL-9" OR "glaucoma symptom scale" ) AND TITLE( validat* OR validity OR psychometric* OR rasch OR "measurement properties" OR reliab* OR responsive* OR version OR translat* ) )
 OR ( TITLE( glaucoma* ) AND TITLE( reading OR disabilit* ) )
 OR ( TITLE( "low vision" OR "vision rehabilitation" OR "visual rehabilitation" ) AND TITLE( referral* OR refer OR referred OR "practice pattern*" ) )
 OR ( TITLE( "low vision" OR "visual impairment*" OR "vision impairment*" OR "visually impaired" OR "vision loss" OR "sight loss" OR "vision rehabilitation" OR "visual rehabilitation" ) AND TITLE( guideline* OR "practice pattern*" ) AND TITLE-ABS-KEY( rehabilitat* OR referral* OR management ) )
 OR ( TITLE( "low vision" OR "visual impairment*" OR "vision impairment*" OR "visually impaired" OR "vision loss" OR "sight loss" OR "vision rehabilitation" OR "visual rehabilitation" ) AND TITLE( service* OR utili* OR uptake OR barrier* ) AND TITLE( rehabilitat* ) )
 OR ( TITLE( "low vision" OR "visual impairment*" OR "vision impairment*" OR "visually impaired" OR "impaired vision" OR "vision loss" OR "sight loss" ) AND TITLE( "vision-related quality of life" OR "vision related quality of life" OR "vision-related" OR "vision-specific" ) )
 OR ( TITLE( "low vision" ) AND TITLE( predict* ) ) )
AND PUBYEAR > 1999 AND ( LIMIT-TO ( LANGUAGE , "English" ) OR LIMIT-TO ( LANGUAGE , "French" ) )
AND NOT TITLE( child* OR pediatric OR paediatric OR preschool* OR infant* OR neonat* )
```

**Put `AND NOT` last.** Scopus applies `AND NOT` after all the other operators. The original Scopus string has `AND NOT TITLE(child…)` before the language limit, so the language limit may have been swallowed into the exclusion. The screened records include no non-English papers, so it does not seem to have mattered.

## Re-testing the string

To check recall after changing the string, search PubMed for the string `AND` the PMIDs below (for example `... AND (22978532[uid] OR 38871087[uid] OR ...)`) and count how many come back. NCBI's E-utilities API (`esearch.fcgi`) does the same thing from a script.

Key sources, by Screening-tab ID:

| ID | PMID | ID | PMID | ID | PMID | ID | PMID |
|---|---|---|---|---|---|---|---|
| 5 | 22978532 | 56 | 34146047 | 89 | 32804622 | 119 | 33879374 |
| 23 | 38871087 | 65 | 12202503 | 92 | 41528105 | 120 | 17311573 |
| 26 | 11124300 | 66 | 16877389 | 93 | 20722170 | 128 | 39292468 |
| 27 | 29385405 | 72 | 30589760 | 95 | 17962445 | 129 | 37142217 |
| 30 | 39951057 | 74 | 15505037 | 97 | 16384947 | 130 | 41598168 |
| 38 | 40401755 | 76 | 17700341 | 105 | 31113297 | 131 | 28460047 |
| 39 | 16320144 | 79 | 12137395 | 110 | 12578777 | 133 | 25052992 |
| 46 | 21613370 | 84 | 28430335 | 112 | 23803778 | 134 | 27977474 |
| 52 | 35466953 | 86 | 30776848 | 114 | 40972235 | 135 | 36543605 |

Held-out papers:

| Paper | PMID | Found? |
|---|---|---|
| NEI VFQ-25 development (Mangione 2001) | 11448327 | No |
| The Activity Inventory (Massof 2007) | 17700339 | Yes |
| IVI Rasch analysis (Lamoureux 2006) | 17065481 | Yes |
| GQL-15 (Nelson 2003) | 12671469 | No |
| GAL-9 (Khadka 2011) | 21810983 | Yes |
| Melbourne Low-Vision ADL Index (2001) | 11328730 | Yes |
| VA LV VFQ-48 and LV VFQ-20 in LVR (2007) | 17700334 | Yes |
| Italian Glaucoma Symptom Scale (2013) | 23076040 | Yes |
| Salisbury self-rated vision score (El-Gasim 2013) | 23812494 | Yes |
| Salisbury self-report vs. VA concordance (2012) | 21962256 | Yes |
| Glaucoma and reading speed (Ramulu 2009) | 19139345 | Yes |
| Vision Rehabilitation PPP (2018) | 29108747 | Yes |
| Low-vision rehabilitation services in the US (Owsley 2009) | 19433720 | Yes |
| Referral pathways to low vision services (2023) | 36681848 | Yes |

## For the methods section

The search can be described as developed in several rounds and checked against a test set of 36 known relevant records, with 14 further records held out to check that it generalizes. If it is adopted, record the new search date, the counts from each database, and that AI assistance was used to develop it.
