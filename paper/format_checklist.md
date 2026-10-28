# Format checklist (step 10 runs this)

Answer yes or no for each line against `paper/manuscript_rendered.md`. Every line must be yes, or carry a written reason. Basis: `paper/format_notes.md`.

## Length and front matter

- [ ] Body text is 2,200 to 3,000 words (target 2,400 to 2,700), counted without references, author block, figure captions and boxes.
- [ ] Title is one line, no colon-subtitle, and states the topic plainly.
- [ ] A dek is present: one sentence, 8 to 20 words, ends with a period, states the clinical point.
- [ ] Byline is "BY Name, Degree; Name, Degree; AND Name, Degree" (placeholders allowed).
- [ ] No abstract is present.
- [ ] If a key-points box is present, it has 3 bullets of one sentence each; if absent, each main section ends with a short "Clinical Takeaways" paragraph.

## Headings and body

- [ ] The introduction has no heading; later headings are short (2 to 6 words), unnumbered, rendered in capitals.
- [ ] 8 to 12 headings in total; the last is CONCLUSION; one is a "PUTTING IT INTO PRACTICE"-type section holding the work-up protocol.
- [ ] The introduction ends with a sentence stating what the article does.
- [ ] Abbreviations are spelled out on first use.
- [ ] Statistics follow the house form: "95% CI, 1.84-6.00", "P = .01", en-dash ranges, "mm Hg".
- [ ] Figures and tables are cited in the text and have numbered one-sentence captions; no more than two tables.
- [ ] The Methods paragraph (search, screening, synthesis, AI disclosure) is present, short, and placed as a sidebar or section before CONCLUSION.
- [ ] A visible DRAFT note is present while the reviewer's H-L decisions are incomplete.

## References

- [ ] References are numbered by first appearance; superscript markers sit after punctuation.
- [ ] 20 to 30 references; none uncited, none duplicated (`cite.py check` exits 0).
- [ ] Rendered with `paper/style_glaucoma_today.json`.
- [ ] Authors: all up to 6; first 3 then "et al" for 7 or more; initials without periods.
- [ ] Titles in sentence case; NLM journal abbreviations; full page ranges; DOI as "doi:..." with no URL and no closing period.
- [ ] Every web or guideline source has an "Accessed" date and URL in the form `Accessed {date}. {URL}`; flag the wording as unconfirmed to the editor.
- [ ] Every number in the text passes `factcheck.py`, or is written `[VERIFY]`.

## Author block and disclosure

- [ ] An author block follows the references: NAME in capitals, role and institution and city, email, "Financial disclosure: ..." for each author.
- [ ] Every author has a disclosure line, even if "None".
- [ ] The AI-assistance disclosure names the model ids (`claude-fable-5-1`, `claude-sonnet-5-5`), the tasks and the reviewer-override counts.
- [ ] The text says the search was systematic with narrative synthesis (SWiM) and that no meta-analysis was done, with the reason.

## Step 9 self-check (2026-10-26, AI-drafted; step 10 re-runs the list against `paper/manuscript_rendered.md`)

Length and front matter: body 2,700 words (target 2,400 to 2,700; counted by section with citation keys, VERIFY tags, boxes, tables, captions, references and author block excluded) — yes. Title one line, no colon — yes. Dek 16 words, one sentence, ends with a period — yes. Byline in house form with placeholders — yes. No abstract — yes. Key-points box (AT A GLANCE) with 3 one-sentence bullets — yes; the per-section "Clinical Takeaways" paragraphs were therefore dropped to meet the word count.

Headings and body: introduction unheaded; 10 later headings of 1 to 6 words, unnumbered, in capitals, last is CONCLUSION, one is PUTTING IT INTO PRACTICE — yes. Introduction ends by stating what the article does — yes. Abbreviations spelled out at first use (LVR, AAO, PPP, NEI VFQ-25, VA LV VFQ-48, IVI, LVQOL, GQL-15, GAL-9, APEDS-VFQ, COSMIN, CI, AUC, QUADAS-2, GRADE, PRISMA) — yes. Statistics in house form ("95% CI, 0.85-0.92"; no P values used) — yes. Figures 1 to 4 and Tables 1 to 3 cited in the text with numbered captions — yes. **No more than two tables — no:** the step 9 brief requires Table 1 (comparison), Table 2 (feasibility) and Table 3 (per-study accuracy); the editor may merge Tables 1 and 2 or move Table 2 to the supplement. Methods paragraph (HOW WE SEARCHED, with the AI disclosure) placed before FUTURE DIRECTIONS and CONCLUSION — yes. DRAFT note at the top — yes.

References: numbered by first appearance, superscript after punctuation — yes. 29 references, none uncited or duplicated, `cite.py check` exit 0 — yes. Rendered with `paper/style_glaucoma_today.json` — yes. Author limits and initials — yes. Sentence-case titles (proper nouns added to `protected_words.txt`), NLM abbreviations, full page ranges (four IOVS/Arch Ophthalmol entries patched from PubMed because Crossref gave first pages only), DOI as `doi:` — yes. One web source (HealthLink BC) carries `Accessed October 26, 2026.` and a URL; the wording is unconfirmed for the magazine and the URL is marked [VERIFY] in `bibliography_manual.csv` — yes with flag. **Every number passes `factcheck.py` or is [VERIFY] — partly:** 342 numeric claims, 259 FOUND and 4 COUNTS; the rest are figure/table/box labels and placeholders (NO CITATION), the PRISMA and reviewer-override counts in HOW WE SEARCHED (NO TEXT; they match `prisma_counts.md` and the Counts tab, and the script's PRISMA "mismatches" compare PubMed 78 and Scopus 88 against the 166 total), and the Sumi 2003 domain correlations (-0.61 to -0.63), which come from a column-scrambled table and carry [VERIFY]. `factcheck.py` exits 2; the Verdict column is for the step 10 verifier.

Author block and disclosure: block after the references with name, role, email and "Financial disclosure" placeholders for three authors — yes. AI disclosure names `claude-fable-5-1` and `claude-sonnet-5-5`, the tasks and 15 of 40 overrides — yes. Systematic search with narrative synthesis (SWiM) and no meta-analysis, with the reason — yes.

## Step 10 run (2026-10-26, against `paper/manuscript_rendered.md` after the fact-check fixes)

Length and front matter: body **2,696** words (`wordcount.py`; target 2,400 to 2,700) — yes. Title one line, no colon — yes. Dek one sentence, 16 words, ends with a period — yes. Byline in house form with placeholders — yes. No abstract — yes. AT A GLANCE box with 3 one-sentence bullets — yes.

Headings and body: introduction unheaded; 10 later headings of 2 to 6 words, unnumbered, in capitals; last is CONCLUSION; PUTTING IT INTO PRACTICE holds the Box — yes. Introduction ends by stating what the article does — yes. Abbreviations spelled out at first use — yes. Statistics in house form — **partly:** "95% CI, 0.85-0.92" and all ranges use hyphens, not en-dashes; left for typesetting so that DOIs and citation keys are not touched; no P values occur. Figures 1 to 4 and Tables 1 to 3 cited in the text with one-sentence numbered captions — yes. **No more than two tables — no** (three; editor may merge Tables 1 and 2 or move Table 2 to the supplement; unchanged from step 9). Methods paragraph (HOW WE SEARCHED, with the AI disclosure) before CONCLUSION — yes. DRAFT note present — yes. No sentence calls any estimate "pooled" ("no pooled estimate" only) — yes. The two index questions quoted as printed in Wu 2026 Table 2 and Discussion (the abstract omits "usually") — yes. Provisional-inclusion sentence present (DRAFT note and Figure 1 legend) — yes.

References: numbered by first appearance; superscripts after punctuation (the PPP sentence fixed in this step; markers after instrument names inside table cells are unavoidable) — yes. 29 references, `cite.py check` exit 0 — yes. Rendered with `paper/style_glaucoma_today.json` — yes. Author limits and initials — yes. Sentence-case titles, NLM abbreviations, full page ranges, DOI as `doi:` — yes, **with one flag for the editor:** the renderer keeps a capital after a colon in a title (refs 4, 20, 23: "Referral patterns", "Further improvements", "A revised tool") while the magazine's model entry has lower case after the colon. One web source with `Accessed October 26, 2026.` and URL; wording unconfirmed for the magazine; URL marked [VERIFY] in `bibliography_manual.csv` — yes with flag. **Every number passes `factcheck.py` or is [VERIFY] — partly:** exit 2 remains; every item in the "To verify" list now carries a verifier verdict or a written justification (`paper/factcheck_report.md`, Verification summary). Remaining [VERIFY] tags: 4, plus one [UPDATE] and one [untested].

Author block and disclosure: block after the references with name, role, email and "Financial disclosure" placeholders for three authors — yes. AI disclosure names `claude-fable-5-1` and `claude-sonnet-5-5`, the tasks and the 15 of 40 override count — yes. Systematic search with narrative synthesis (SWiM), no meta-analysis, with the reason — yes.
