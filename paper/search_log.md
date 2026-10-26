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
| 4 | Online resources and browsing | HealthLink BC page (record 132), listed among the key sources in `data/LVR_Q_Study_Outline.md`; how it was first found is not recorded |
| 5 | Citation searching | Backward references and forward citations of the included studies via OpenAlex (NCBI elink where OpenAlex lacked the record); see "Citation searching" below |
| 6 | Contacts | None |
| 7 | Other methods | Key sources known to the authors (records 128-135); AI-assisted development and recall testing of the strategy (see "Strategy development") |
| 10 | Search filters | None |
| 11 | Prior work | None; original strings written by the reviewer, revision developed from them |
| 14 | Peer review of the search | Not peer reviewed (no PRESS checklist done) |

## Strategy development (item 7)

- Original strings: `data/LVR_Q_Study_Outline.md`, run 4 Oct 2026 (PubMed 78, Scopus 88).
- Revised strategy: `docs/LVR_search_strategy.md`, developed 20 Oct 2026 with AI assistance, validated against 36 key sources and 14 held-out papers; re-tested 26 Oct 2026 with `pubmed_recall.py` on Claude Sonnet 5.5 (`claude-sonnet-5-5`) (`analysis/search/recall_8arm_2026-10-26.json`: 593 records, 35/36, 12/14).
- Minimal edit of the original string, tested 26 Oct 2026: three candidates (`analysis/search/cand1_minimal.txt`, `cand2_title_level.txt`, `cand3_drop_accuracy.txt`); candidate 1 retrieves the two papers the original missed (PMIDs 39292468, 25052992; records 128, 133) at 137 records, 59 new. Diagnosis and table: `paper/search_strategy_note.md`.
- Decision: Pending: the reviewer has not decided between the original, candidate 1 and the 8-arm revision (recommendation in `paper/search_strategy_note.md`). Nothing below was run as the review's search except the 4 Oct 2026 original..

## Runs (items 8, 9, 12, 13, 15)

One block per database per run. Paste the string exactly as run; for
PubMed keep the Advanced Search history line numbers.

### PubMed, 2026-10-04 (original search, as run by the reviewer)

- Platform: NCBI PubMed.
- Limits (item 9): publication date 2000 onward; language English or French; titles with child*/pediatric/paediatric excluded. Justification: adult population; reviewer languages; modern instruments. (Adapted from the outline; the stated justification is not recorded by the reviewer.)
- Records retrieved (item 15): 78 on 4 Oct 2026; 78 again on 26 Oct 2026 via E-utilities.
- Recall (key sources 20/36; held-out 0/14): `analysis/search/recall_original_2026-10-26.json`.
- Strategy:

```
("Vision, Low"[Majr] OR "low vision"[ti] OR "visual impairment"[ti] OR "legal blindness"[tiab] OR "legally blind"[tiab]) AND (questionnaire*[tiab] OR "self-report*"[tiab] OR "screening question*"[tiab] OR "single question"[tiab] OR survey[ti]) AND ("Sensitivity and Specificity"[Mesh] OR "ROC Curve"[Mesh] OR sensitivity[tiab] OR specificity[tiab] OR "area under the curve"[tiab] OR "diagnostic accuracy"[tiab]) AND (english[la] OR french[la]) AND 2000:3000[dp] NOT (child*[ti] OR pediatric[ti] OR paediatric[ti])
```

### Scopus, 2026-10-04 (original search)

- Platform: Scopus Advanced Search (Elsevier). No API; count typed from the interface.
- Records retrieved: 88 (4 Oct 2026, from the outline).
- Key sources with a DOI present in the export: to be typed from the interface.
- Strategy: see `data/LVR_Q_Study_Outline.md` ("String for Scopus").

### PubMed, 2026-10-26 (re-test, not run as the review's search): 8-arm revision

- Platform: NCBI PubMed via E-utilities (`pubmed_recall.py`), line #14 of `docs/LVR_search_strategy.md`.
- Limits: as #14 (English or French; 2000 onward; child*/pediatric/paediatric/preschool*/infant*/neonat* excluded from titles).
- Records retrieved: 593.
- Recall (key sources 35/36; held-out 12/14): `analysis/search/recall_8arm_2026-10-26.json`.
- Strategy:

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

### PubMed, 2026-10-26 (candidate minimal edit 1, not adopted yet)

- Platform: NCBI PubMed via E-utilities. Limits as the original.
- Records retrieved: 137 (59 beyond the original 78; list in `analysis/search/minimal_edit_new_records.csv`).
- Recall (key sources 22/36; held-out 0/14; PMIDs 39292468 and 25052992 both retrieved): `analysis/search/recall_cand1.json`.
- Candidates 2 (381 records, 23/36, 5/14) and 3 (1,180 records, 27/36, 4/14) were also tested: `recall_cand2.json`, `recall_cand3.json`.
- Strategy:

```
("Vision, Low"[Majr] OR "low vision"[tiab] OR "visual impairment"[ti] OR "legal blindness"[tiab] OR "legally blind"[tiab]) AND (questionnaire*[tiab] OR "self-report*"[tiab] OR "screening question*"[tiab] OR "single question"[tiab] OR survey[ti] OR "self-rated"[tiab]) AND ("Sensitivity and Specificity"[Mesh] OR "ROC Curve"[Mesh] OR sensitivity[tiab] OR specificity[tiab] OR "area under the curve"[tiab] OR "diagnostic accuracy"[tiab] OR "item response"[tiab]) AND (english[la] OR french[la]) AND 2000:3000[dp] NOT (child*[ti] OR pediatric[ti] OR paediatric[ti])
```

### Scopus, candidate minimal edit 1 (draft, not run)

- Platform: Scopus Advanced Search. No API; the string below has not been run.
- Limits: PUBYEAR > 1999; LANGUAGE English, French; AND NOT TITLE(child* ...) placed last.
- Records retrieved: to be typed from the interface.
- Key sources with a DOI present in the export: to be typed from the interface.
- Strategy (draft from `syntax_translate.py`; review before running):

```
( INDEXTERMS("Vision, Low") OR TITLE-ABS("low vision") OR TITLE("visual impairment") OR TITLE-ABS("legal blindness" OR "legally blind") ) AND ( TITLE-ABS(questionnaire* OR "self-report*" OR "screening question*" OR "single question" OR "self-rated") OR TITLE(survey) ) AND ( INDEXTERMS("Sensitivity and Specificity" OR "ROC Curve") OR TITLE-ABS(sensitivity OR specificity OR "area under the curve" OR "diagnostic accuracy" OR "item response") ) AND LANGUAGE(english OR french) AND PUBYEAR > 1999 AND NOT TITLE(child* OR pediatric OR paediatric)
```

## Updates (item 12)

| Date | What | PubMed | Scopus | New records to screening |
|---|---|---|---|---|
| 2026-10-04 | original search | 78 | 88 | 127 after de-duplication |
| 2026-10-26 | re-test of original, 8-arm revision and three minimal-edit candidates (no run adopted) | 78 / 593 / 137 | to be typed from the interface | none yet |

## Citation searching (item 5)

| Date | Seeds (stage) | Backward | Forward | Linked works | Already in sheet | New candidates | 2+ links | Screened | Added (IDs) |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-26 | 13 included at T/A (reviewer: IDs 5, 18, 20, 26, 27, 29, 30, 31, 34, 36, 37, 38, 39), backward only, `--min-links 2` | 516 candidates in total | 0 (not run) | 516 | 9 | 507 | 36 | 0 (not screened in this step) | none |

Numbers from `analysis/search/snowball*/snowball_log.json`. "Added" records carry "Citation searching (snowball)" in their Notes cell and are counted in Counts!B5 "Other sources".

## De-duplication (item 16)

- Between databases: Zotero 7 duplicate detection, each pair verified by title, year and journal (4 Oct 2026: 39 removed).
- Snowball candidates against the Screening tab: `snowball.py` (DOI, PMID, normalised-title Jaccard >= 0.85; 0.60-0.85 flagged for the screener).
- No re-run of the Zotero de-duplication. Snowball run 2026-10-26: 9 of 516 candidates were already in the Screening tab.

## Grey literature and other sources (items 4, 7)

- Key sources added by hand as records 128-135 (TVST 2024, HealthLink BC web page, guidelines, glaucoma reading and referral papers); these are the "other sources" (8) in the Counts tab.

## AI assistance (report in Methods)

Claude Fable 5.1 (`claude-fable-5-1`, default chain model) and Claude Sonnet 5.5 (`claude-sonnet-5-5`, this step) assisted with: strategy development and recall testing (`pubmed_recall.py`), Scopus syntax drafting (not yet reviewed by the reviewer), citation searching and de-duplication (`snowball.py`), and title/abstract screening suggestions. All inclusion decisions are made by the reviewer.
