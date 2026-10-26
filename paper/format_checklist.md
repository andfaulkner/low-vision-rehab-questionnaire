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
