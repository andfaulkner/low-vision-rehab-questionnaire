# Citation formats: worked examples and how to adapt a style

Both built-in styles are numbered, by order of first appearance, and reuse the
same number every time a source is cited. They differ in the in-text marker,
the author cut-off, italics, page condensing and date wording. Everything
below was produced by `cite.py render` from the live Crossref/PubMed metadata
(journal articles) and from `assets/bibliography_manual_template.csv` (the
rest); check the manual rows before quoting them, they are examples.

## AMA (11th ed.), `assets/styles/ama.json`, default

In text, superscript after the punctuation: `...for low vision.^4^` and
`...earlier work.^3,6^`; three or more consecutive numbers collapse: `^2-5^`.

Journal article (Crossref + PubMed; six authors are listed in full, seven or
more become the first three + et al):

> 4. Wu YH, Yu D, Goldstein J, Kwon M, Wang C, Legge GE. Screening questions to identify low vision and acuity-defined legal blindness. *Invest Ophthalmol Vis Sci*. 2026;67(1):28. doi:10.1167/iovs.67.1.28

> 5. Wu YH, Yu D, Goldstein JE, et al. Estimating visual acuity without a visual acuity chart. *Transl Vis Sci Technol*. 2024;13(9):20. doi:10.1167/tvst.13.9.20

Journal article without a DOI (manual row of type `journal`, Screening ID 14):

> 7. Verdina T, Rossi A, Bianchi L. Biofeedback low vision rehabilitation with Retimax vision trainer in patients with macular disease. *J Low Vis Pract*. 2020;4(2):55-61.

Book chapter / NCBI Bookshelf (type `chapter`; Bookshelf chapters have no DOI,
so the URL and the accessed date carry the locator; `editors` may be empty):

> 9. Smith JA, Doe JB. Vision impairment in adults. In: *StatPearls*. StatPearls Publishing; 2024. Accessed October 26, 2026. https://www.ncbi.nlm.nih.gov/books/NBK000000/

Guideline (type `guideline`; the AAO PPP also exists as an *Ophthalmology*
article with a DOI; cite one form, not both):

> 1. Fontenot JL, Bona MD, Kaleem MA, Melia BM, Mukkamala L, Shaw K. Vision Rehabilitation Preferred Practice Pattern. Preferred Practice Pattern Guidelines. American Academy of Ophthalmology; 2018. Accessed October 26, 2026. https://www.aao.org/preferred-practice-pattern/vision-rehabilitation-ppp-2017

Web page (type `web`; no personal author, so the organisation in `publisher`
becomes the author; `published`/`updated` are optional ISO dates):

> 2. CNIB Foundation. Legal blindness in Canada. CNIB Foundation. Published March 1, 2023. Accessed October 26, 2026. https://www.cnib.ca/en/legal-blindness

Report (type `report`):

> 10. World Health Organization. World report on vision. World Health Organization; 2019. Accessed October 26, 2026. https://www.who.int/publications/i/item/9789241516570

## Vancouver / NLM, `assets/styles/vancouver.json`

In text, bracketed before the punctuation: `...for low vision[4].`
Condensed end pages (115-23), `doi: ` with a space, no italics, dates as
`2023 Mar 1`, `[Internet]` and `[cited ...]` for web material.

> 3. Bibby SA, Maslin ER, Mcilraith R, Soong GP. Vision and self-reported mobility performance in patients with low vision. Clin Exp Optom. 2007;90(2):115-23. doi: 10.1111/j.1444-0938.2007.00120.x

> 5. Wu YH, Yu D, Goldstein JE, Kwon M, Gobeille M, Watson E, et al. Estimating visual acuity without a visual acuity chart. Transl Vis Sci Technol. 2024;13(9):20. doi: 10.1167/tvst.13.9.20

> 9. Smith JA, Doe JB. Vision impairment in adults. In: StatPearls. Treasure Island FL: StatPearls Publishing; 2024. Available from: https://www.ncbi.nlm.nih.gov/books/NBK000000/

> 1. Fontenot JL, Bona MD, Kaleem MA, Melia BM, Mukkamala L, Shaw K. Vision Rehabilitation Preferred Practice Pattern. Preferred Practice Pattern Guidelines. San Francisco CA: American Academy of Ophthalmology; 2018. Available from: https://www.aao.org/preferred-practice-pattern/vision-rehabilitation-ppp-2017

> 2. CNIB Foundation. Legal blindness in Canada [Internet]. CNIB Foundation; 2023 Mar 1 [cited 2026 Oct 26]. Available from: https://www.cnib.ca/en/legal-blindness

(Mcilraith is how Crossref and PubMed spell the author; the paper has
McIlraith. Metadata errors like this are why the list is read once against
the PDFs.)

## Matching the journal's real format

1. Find one reference from a recent Glaucoma Today review (the Phase 1
   `paper/format_notes.md` of the review prompt quotes one verbatim).
2. Copy `assets/styles/ama.json` to `paper/style_glaucoma_today.json` and edit:
   - `authors.max_listed` / `list_first_if_more` (many magazines list 3 then
     et al; Glaucoma Today often lists all up to a limit);
   - `journal.italic` (Markdown `*...*`; the typesetter will restyle);
   - `templates.journal`: drop `[ doi:{doi}]` if the magazine prints no DOIs,
     or replace with `[ {doi_url}]` for a clickable URL;
   - `pages.condense`, `dates.format`, `in_text.after_punctuation`.
3. `cite.py render ... --style paper/style_glaucoma_today.json`.

Fields a template may use: `authors`, `title`, `journal` (abbreviated,
italicised per style), `container_title`, `book_title` (italicised),
`year`, `month`, `volume`, `issue`, `pages`, `edition`, `editors`, `eds`
(ed/eds or editor/editors), `publisher`, `publisher_place`, `doi`,
`doi_url`, `pmid`, `url` (suppressed for journal articles that have a DOI),
`published`, `updated`, `accessed`, `updated_cited`, `note`.

## Sources with no DOI

| Source | Type | What to fill |
|---|---|---|
| Screening record with "No link" | journal | authors, title, container_title, container_abbrev (NLM form if the journal is indexed; else the full name), year, volume, issue, pages; note the Screening ID; `text_file` if a .txt exists |
| NCBI Bookshelf chapter | chapter | authors, chapter title, book in container_title, editors if any, publisher, year, NBK URL, accessed |
| Guideline / PPP / consensus | guideline | organisation as authors or publisher, title, series in container_title, year, url, accessed; if a journal version with a DOI exists, prefer `@doi:` |
| Web page | web | publisher (organisation) and/or authors, title, site name in container_title, published/updated/accessed as ISO dates, url |
| Report (WHO, Statistics Canada) | report | organisation as publisher, title, place, year, url, accessed |
| Preprint | use `@doi:` (Crossref type `posted-content` renders with the preprint template) |

Dates in the CSV are ISO (`2026-10-26`); the style formats them. A manual row
that also has a DOI is allowed (for a web version of a DOI'd document), but if
the same DOI is cited with `@doi:` elsewhere, `check` reports a duplicate.

## AMA specifics implemented

- Authors: surname + initials without periods, comma-separated, no "and".
- Titles: sentence case for articles and chapters; books, reports, guidelines
  and web pages keep their case (AMA uses title case for those).
- Journal: NLM abbreviation, italic; no issue parentheses when the issue is
  unknown; article numbers (e.g. `20`, `e0245`) take the place of pages.
- DOI: `doi:10.xxxx` without URL; no "Accessed" for journal articles.

## Vancouver specifics implemented

- Six authors then `et al.`; end page condensed (`449-61`); journal
  abbreviation without punctuation; `doi: ` with a space; `[Internet]`,
  `[cited YYYY Mon D]`, `Available from:`.
- PMID is not printed by default; add `[ PMID: {pmid}]` to the template if
  the journal wants it.
