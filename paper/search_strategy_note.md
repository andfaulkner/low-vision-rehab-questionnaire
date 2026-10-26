# Search strategy note: why two papers were missed, and the smallest fix

Prepared 2026-10-26 (chain step 3) with AI assistance (Claude Sonnet 5.5, `claude-sonnet-5-5`). Advisory: the reviewer decides which string the review reports. All counts are PubMed on 2026-10-26 with the original limits (English or French, 2000 onward, `NOT child*/pediatric/paediatric` in title).

## 1. Clause-by-clause diagnosis

The original string is three ANDed concepts: C1 population, C2 questionnaire/self-report, C3 accuracy. Each clause was tested against each record with `<clause> AND <PMID>[uid]` (output: `analysis/search/clause_diagnosis.txt`; records: `analysis/search/targets_efetch.xml`). Language, date and the child NOT clause pass for both.

| Clause | PMID 39292468 (TVST 2024, ID 128) | PMID 25052992 (Nguyen 2014, ID 133) |
|---|---|---|
| C1: `"Vision, Low"[Majr]`, `"low vision"[ti]`, `"visual impairment"[ti]`, `"legal blindness"[tiab]`, `"legally blind"[tiab]` | **FAILS.** Title "Estimating Visual Acuity Without a Visual Acuity Chart"; MeSH are Visual Acuity (major), Vision Tests (major), Self Report, Surveys and Questionnaires; no Vision, Low. "Low vision" occurs only in the abstract and "vision impairment" is not "visual impairment". | **FAILS.** Title "Reading ability and reading engagement in older adults with glaucoma"; major MeSH are Reading, and Glaucoma/Vision Disorders only as physiopathology subheadings. "Low vision" is an author keyword, not a title word. |
| C2: `questionnaire*[tiab]`, `"self-report*"[tiab]`, `"screening question*"[tiab]`, `"single question"[tiab]`, `survey[ti]` | passes (abstract says "self-reported ability") | **FAILS.** Abstract says "self-rated" and Rasch; none of the five terms occur. The record is MeSH-indexed to Surveys and Questionnaires, but the string does not use that heading. |
| C3: Sensitivity and Specificity / ROC Curve MeSH, `sensitivity`, `specificity`, AUC, `"diagnostic accuracy"` | **FAILS.** It is an item-response-theory and prediction-error study (r, logMAR error, repeatability); no accuracy term. | passes **by accident**: `sensitivity[tiab]` matches "contrast sensitivity" |

So 39292468 fails C1 and C3; 25052992 fails C1 and C2. Neither could be rescued by changing one clause. Both are valid on-topic papers that simply use different vocabulary from the string's three concepts.

**Scopus (original string, by inspection, no API).** `TITLE("low vision" OR "visual impairment")` fails both titles; `TITLE-ABS-KEY("legal blindness" OR "legally blind")` fails both. Scopus indexes author keywords, so 25052992's keyword "low vision" would not help because the population clause searches TITLE only for "low vision". For 39292468 the questionnaire clause (`TITLE-ABS-KEY`) probably passes on "self-report*", and the accuracy clause (`TITLE-ABS-KEY(sensitivity OR specificity OR "ROC curve" OR "area under the curve" OR "diagnostic accuracy")`) fails. For 25052992 the accuracy clause passes on "contrast sensitivity" but the questionnaire clause fails. The population clause is therefore the common failure in Scopus too. This is inference from the PubMed records; confirm in the Scopus interface.

## 2. Baseline recall (reproduced)

| | Records | Key sources (of 36) | Held-out (of 14) |
|---|---|---|---|
| Original string | 78 | 20 | 0 |
| 8-arm revision (`docs/LVR_search_strategy.md`) | 593 | 35 (miss: ID 84) | 12 (miss: Mangione 2001, Nelson 2003) |

These match `search_notes.md` (JSON: `analysis/search/recall_original_2026-10-26.json`, `analysis/search/recall_8arm_2026-10-26.json`).

## 3. Candidate minimal edits

Each is the original string with only the stated additions. "New" = records not in the original 78 (every candidate retrieves all 78). Both targets = PMIDs 39292468 and 25052992.

| Candidate | Edit | Records | New | Both targets | Key sources /36 | Held-out /14 |
|---|---|---|---|---|---|---|
| Original | none | 78 | 0 | neither | 20 | 0 |
| **1 (minimal)** | C1: `"low vision"[ti]` becomes `[tiab]`; C2 += `"self-rated"[tiab]`; C3 += `"item response"[tiab]` | 137 | 59 | **yes, both** | 22 | 0 |
| 2 (title-level) | C1 += `"visual acuity"[ti]`, `glaucoma*[ti]`; C2 += `"self-rated"[tiab]`; C3 += `"item response"[tiab]`, `Rasch[tiab]` | 381 | 303 | yes, both | 23 | 5 |
| 3 (drop accuracy) | C1 as candidate 1; C2 += `"self-rated"[tiab]`; C3 removed | 1,180 | 1,102 | yes, both | 27 | 4 |

Single-edit probes (`analysis/search/clause_diagnosis.txt` and the run log in the status section) show why the edits come as a set: widening C1 alone adds 47 records and retrieves neither paper; `"self-rated"[tiab]` alone adds 1; `"item response"[tiab]` alone adds 9. Each paper needs its own C2/C3 fix plus the C1 fix. Adding `Rasch[tiab]` to candidate 1 raised the total to 213 with no gain in the two targets.

JSON per run: `analysis/search/recall_cand1.json`, `recall_cand2.json`, `recall_cand3.json`; strings: `cand1_minimal.txt`, `cand2_title_level.txt`, `cand3_drop_accuracy.txt`.

## 4. Chosen minimal edit (candidate 1)

It retrieves both missed papers for the fewest added records (59), and no candidate retrieves them for less. Caveat: it is tuned to these two papers (its gain in key sources is 2 of 36 and in held-out papers 0 of 14), so it should not be described as a general improvement in recall.

PubMed (verbatim; `analysis/search/cand1_minimal.txt`):

```
("Vision, Low"[Majr] OR "low vision"[tiab] OR "visual impairment"[ti] OR "legal blindness"[tiab] OR "legally blind"[tiab]) AND (questionnaire*[tiab] OR "self-report*"[tiab] OR "screening question*"[tiab] OR "single question"[tiab] OR survey[ti] OR "self-rated"[tiab]) AND ("Sensitivity and Specificity"[Mesh] OR "ROC Curve"[Mesh] OR sensitivity[tiab] OR specificity[tiab] OR "area under the curve"[tiab] OR "diagnostic accuracy"[tiab] OR "item response"[tiab]) AND (english[la] OR french[la]) AND 2000:3000[dp] NOT (child*[ti] OR pediatric[ti] OR paediatric[ti])
```

Scopus (draft from `syntax_translate.py`, `AND NOT` last; balanced; **not run**, so it has not been checked in Scopus; `analysis/search/cand1_scopus.txt`):

```
( INDEXTERMS("Vision, Low") OR TITLE-ABS("low vision") OR TITLE("visual impairment") OR TITLE-ABS("legal blindness" OR "legally blind") ) AND ( TITLE-ABS(questionnaire* OR "self-report*" OR "screening question*" OR "single question" OR "self-rated") OR TITLE(survey) ) AND ( INDEXTERMS("Sensitivity and Specificity" OR "ROC Curve") OR TITLE-ABS(sensitivity OR specificity OR "area under the curve" OR "diagnostic accuracy" OR "item response") ) AND LANGUAGE(english OR french) AND PUBYEAR > 1999 AND NOT TITLE(child* OR pediatric OR paediatric)
```

Scopus differences: no major-topic restriction on MeSH (expect extra records from `INDEXTERMS("Vision, Low")`), no abstract-only field (`TITLE-ABS` also matches title). The original Scopus string used `TITLE-ABS-KEY`; this draft uses `TITLE-ABS`, which is narrower (it ignores author keywords). Switch to `TITLE-ABS-KEY` if the reviewer wants parity with the 4 Oct run (the count will rise).

The 59 new records are listed in `analysis/search/minimal_edit_new_records.csv` for triage. They are not screened and not in the workbook.

## 5. Minimal edit versus the 8-arm revision

The 8-arm revision retrieves 35/36 key sources and 12/14 held-out papers for 593 records (539 not already in the sheet), while candidate 1 retrieves the two missed papers and 22/36 key sources and 0/14 held-out for 137 records (59 new). I recommend the reviewer adopt the 8-arm revision as the review's search, because it is the only option that generalises to the held-out papers and its 593-record screening load was judged acceptable on 20 Oct; if the review must keep a "slightly modified" original string for methodological continuity, candidate 1 is the cheapest valid way to do it, and the Methods should then cite Mangione 2001 and similar papers via citation searching instead. This is a recommendation; the reviewer decides.
