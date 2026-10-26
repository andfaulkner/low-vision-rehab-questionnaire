# Prompt: write the Glaucoma Today literature review with tiered subagents

You are the orchestrator. Your job is to produce a complete, submission-ready narrative review for **Glaucoma Today** on brief self-report questionnaires that identify adults (especially glaucoma patients) who need low vision rehabilitation (LVR). Delegate every data-heavy or repetitive step to subagents on lower model tiers and effort levels, as specified below. Reserve your own context for synthesis, judgement calls and the final writing.

Read `CLAUDE.md` first and obey it throughout. In particular: never fill the reviewer's yellow columns H–L in the screening sheet, never save the source xlsx with openpyxl, treat AI suggestions as advisory only, and the paper's Methods must disclose that AI assistance was used.

## Ground truth you start from

- `data/LVR_Q_Study_Outline.md` is the study outline: PICO, search strings, the inclusion/exclusion criteria, 31 key sources, and a proposed article structure. Start here. Its proposed outline is the skeleton of the paper.
- `data/LVR_screening_sheet_2_Screening.csv` holds the 135 screening records (IDs 1–135; 127 from PubMed + Scopus, 128–135 added by hand from the outline). The user calls this "the 129-article CSV"; use the file as it is and note the actual count in your report. Columns N–S are AI triage suggestions from earlier passes; they are hints, not decisions.
- `data/articles/` holds 117 PDFs and `data/articles_text/` holds 116 matching `.txt` extractions, named `<First author> et al. - <year> - <truncated title>`. If a PDF has no `.txt`, use the `pdf-to-text` skill to make one. Read `.txt` files, not PDFs.
- `docs/todos/todo.md` is the running to-do list for this review.
- Today is 2026-10-25. The searches were run 2026-10-04.

The two index questions the review must evaluate are:

1. "In a fast food restaurant, can you read the posted menus?"
2. "When seated in front of a computer, are you able to read the letters on the keyboard keys?"

They come from the Legge group's work: the 100-item acuity survey in *Estimating Visual Acuity Without a Visual Acuity Chart* (TVST 2024, doi 10.1167/tvst.13.9.20) and the screening-question paper by Wu, Yu, Goldstein, Kwon, Wang and Legge (IOVS, Jan 2026). The review must report the accuracy of each item, of the pair, and identify which other items from that work (or from other included instruments) could be added for glaucoma patients, whose deficit is often field and contrast loss with preserved acuity.

## Scope rule

Include only articles about **self-report questionnaires or screening items used to detect low vision / visual impairment or LVR need in adults**, plus glaucoma PROM studies and LVR referral guidelines, exactly as the Instructions tab defines. Full-length instruments (NEI VFQ-25, VA LV VFQ-48, Activity Inventory, IVI, LVQOL, GQL-15, GAL-9, APEDS-VFQ, etc.) are in scope because the paper contrasts them with the two-item screen. Intervention studies with no questionnaire validation, paediatric-only studies, case reports and opinion pieces are out, though opinion pieces and guidelines may be cited for context in the Introduction.

## Subagent tiers (apply these exactly)

| Task kind | subagent model | effort | why |
|---|---|---|---|
| Format lookup, file inventory, sharded CSV triage, PRISMA reconciliation | `sonnet` | `medium` | mechanical, high volume |
| Full-text eligibility checks, data extraction, search-string testing | `sonnet` | `medium` | needs reading comprehension, not synthesis |
| Fact-check of the drafted manuscript against source texts | `sonnet` | `high` | must catch wrong numbers |
| Section drafting and final assembly | you (the orchestrator) | — | voice and judgement |

Never use `haiku` for any task, and never use `low` effort; `medium` is the minimum. Run independent subagents in parallel in the same turn. Give each one a narrow brief with explicit file paths, the exact output format, and the rule "report only what the source text says; if a number is not in the text, write NOT REPORTED, never estimate." Have every subagent read untrusted data with `python3 -I` when it writes scripts, and keep its scripts out of `data/`.

## Phases

### Phase 0: workspace

Create a new top-level directory `paper/` (the untracked empty `lvr/` directory can be removed or ignored). Everything the review produces goes there:

```
paper/
  manuscript.md            the full article
  references.md            numbered reference list in Glaucoma Today style
  included_studies.csv     final inclusion list with ID, citation, instrument, reason included
  evidence_table.csv       one row per included study (columns below)
  two_item_accuracy.md     every accuracy figure for the two questions, with source and page
  candidate_items.md       other screening items worth adding, with evidence
  search_strategy.md       original strings, the gap analysis, the revised strings, test results
  format_notes.md          what the Sept/Oct 2026 Glaucoma Today format requires
  prisma_counts.md         flow numbers reconciled with the Counts tab
  ai_disclosure.md         exactly how AI was used, for the Methods section
```

### Phase 1: Glaucoma Today format (sonnet, medium)

Fetch the September/October 2026 issue of Glaucoma Today (glaucomatoday.com, Bryn Mawr Communications) and at least two review-style articles from it. Record in `paper/format_notes.md`: typical word count, title and dek style, section headings used, whether abstracts are used, how authors and affiliations and disclosures appear, the "At a Glance" / key-points box convention, sidebar and table conventions, figure style, and the exact reference format (numbering, author limits, journal abbreviation, DOI usage). If the Sept/Oct 2026 issue is not online yet, use the most recent issue available and say so. Quote one real reference entry verbatim as the model to copy.

### Phase 2: search-string gap analysis (sonnet, medium)

The two Legge-group papers were missed by both searches. Determine why by retrieving their PubMed records (MeSH terms, title, abstract) via E-utilities and checking each clause of the PubMed and Scopus strings in the outline against them. Then propose the smallest modification to each string that retrieves both papers (likely candidates: adding `"visual acuity"[ti]` or `"vision impairment"` to concept 1, or `"screening question*"` to concept 2 with acuity terms, or relaxing the diagnostic-accuracy clause). Test each candidate with `esearch` and report: whether both target DOIs are now hit, total yield, and how many new records that adds over the original 78. Pick the revision with the best precision and write all of this, with the before/after strings and counts, to `paper/search_strategy.md`. Do not rerun screening on the new records; just list the new PMIDs and titles so the human reviewer can triage them.

### Phase 3: screening-sheet triage (sonnet, medium, sharded)

Split the 135 rows of `data/LVR_screening_sheet_2_Screening.csv` into four shards of ~34 rows. For each row the agent returns: ID, first author, year, `candidate: yes/no/maybe`, one-line reason, and the exact exclusion reason string from the Lists tab when it says no. The agent must apply the Instructions-tab criteria, must not read columns N–S until it has formed its own view, and must then note where it disagrees with the AI columns. Merge the shards. Rows marked yes or maybe go to Phase 4.

Separately, compare the 31 key sources in the outline against the merged list and against the 117 PDFs; report any key source with no PDF and no text, and any article in `data/articles/` that is not in the CSV at all.

### Phase 4: full-text verification and extraction (sonnet, medium, parallel)

For every yes/maybe candidate (batch 5–6 per agent), the agent opens the `.txt` and answers in a fixed template:

- Eligible under the inclusion criteria? yes/no, one reason, exclusion string if no.
- Instrument(s), number of items, administration time if stated.
- Population: n, setting, mean age, % glaucoma, country, language.
- Reference standard (VA threshold, visual field, clinician-judged LVR need, full questionnaire).
- Accuracy: sensitivity, specificity, AUC, PPV/NPV, cut-offs, with CIs and the page/section they come from.
- Validation method (Rasch, ROC, test–retest, concurrent validity) and any item-level results.
- Any individual question whose wording resembles the restaurant-menu or keyboard items, or that targets field loss, contrast, glare, mobility or driving.
- One sentence on relevance to a technician-led screen in a glaucoma clinic.

Write the merged results to `paper/evidence_table.csv` and the final list to `paper/included_studies.csv`. Separately, one sonnet agent at medium effort reads the Wu 2026 and TVST 2024 texts in full and writes `paper/two_item_accuracy.md` (every sens/spec/AUC/threshold for each item alone and combined, how the items were selected from the 100, the sample, and the stated limitations) and `paper/candidate_items.md` (the other top-performing items from the 100-item set, with their figures, ranked, and which of them address non-acuity deficits relevant to glaucoma).

### Phase 5: PRISMA numbers (sonnet, medium)

Reconcile the flow numbers: 78 PubMed + 88 Scopus + 8 other = 174 identified, 39 duplicates, 135 screened, then the counts from Phase 3/4 for excluded at title/abstract, full texts assessed, excluded at full text with reasons, and studies included. Write `paper/prisma_counts.md` and flag any mismatch with `data/LVR_screening_sheet_2_Counts.csv`. Do not edit the xlsx.

### Phase 6: write the manuscript (you)

Write `paper/manuscript.md` in the voice and structure Glaucoma Today uses, following the outline in the study outline file:

1. Title and dek, author block placeholders, At-a-Glance box.
2. Introduction: the referral gap. Glaucoma as a leading cause of low vision; how few eligible patients reach LVR; the AAO vision-rehabilitation referral model; purpose: how a new LVR clinic can screen during the technician work-up.
3. How glaucoma disables beyond visual acuity: field loss, contrast loss, glare, mobility and reading, often with preserved acuity; the Canadian legal-blindness definition.
4. Full-length questionnaires used in LVR and glaucoma: NEI VFQ-25, VA LV VFQ-48, Activity Inventory, IVI, LVQOL, GQL-15, GAL-9 and others found in Phase 4; what each measures, item counts, administration time, validation; why they are too long for routine screening. Include the evidence table as a Glaucoma Today-style table.
5. The two-question approach: origin in the 100-item acuity survey; accuracy of each item and of the pair; comparison with other brief screeners found in the review (single-question self-rated vision, NHATS self-report, Stalin 2025 inpatient tool, etc.).
6. Will it work in an LVR clinic? Under-detection of field-limited patients; setting, cultural and literacy assumptions; self-report bias; what other items could be added (from `candidate_items.md`).
7. Proposed technician work-up protocol: a concrete, boxed protocol combining the two items, any added items, last VA and last visual field, with a referral rule.
8. Future directions, and a short Methods paragraph (search, screening, AI disclosure) placed where the format notes say such material belongs.
9. Numbered references in the Phase 1 format.

Writing rules: every numeric claim carries a citation and must exist in `evidence_table.csv` or `two_item_accuracy.md`; if you cannot source it, write `[VERIFY]` rather than a number. No invented references. Match the target word count from `format_notes.md`. Plain clinical prose, no bullet-point essays, no hype.

### Phase 7: fact-check (sonnet, high)

Give one agent `manuscript.md`, `evidence_table.csv`, `two_item_accuracy.md` and access to `data/articles_text/`. It checks every citation-bearing sentence against the source text and returns a list of: wrong numbers, claims not supported by the cited source, references cited but not in the list or vice versa, and remaining `[VERIFY]` tags. Fix everything it finds, then rerun the check once.

## Final report to the user

Keep it short: the inclusion count and list, the revised search strings and whether they retrieve both missing papers, the headline accuracy of the two items, the extra items you recommend, the target word count versus actual, anything still tagged `[VERIFY]`, and the path to `paper/manuscript.md`. Do not commit or push; the user will review first.
