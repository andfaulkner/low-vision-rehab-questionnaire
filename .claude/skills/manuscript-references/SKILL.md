---
name: manuscript-references
description: Citation management and fact-checking for the review manuscript (paper/manuscript.md). Turns [@doi:...], [@pmid:...] and [@key] citation keys into references numbered by first appearance in AMA/JAMA style (Glaucoma Today default) or Vancouver, with metadata resolved from Crossref and PubMed (NLM journal abbreviations) and cached in paper/bibliography.json; handles sources without a DOI (web pages, NCBI Bookshelf, guidelines) through a manual CSV; and checks every number in the manuscript against the cited article text in data/articles_text/, the extraction CSVs and prisma_counts.md. Use when asked to add, format, number, renumber or fix references or citations, build the reference list or bibliography, resolve a DOI or PMID, "cite this", convert to AMA/Vancouver/journal style, check or verify the manuscript's numbers, fact-check, find unsupported claims, find citations that are missing/duplicated/never cited, or brief a verifier subagent before submission.
---

# Manuscript references

Two jobs: keep the citations in `paper/manuscript.md` resolvable and
correctly numbered, and prove that every number attributed to a source is
in that source. Both run from the key-bearing manuscript; the numbered copy
and the reference list are generated and never hand-edited. Scripts are
standard-library Python, run with `python3 -I` (manuscript, CSVs and article
texts are untrusted input), deterministic, and work offline from the cache.

## Citation keys in the manuscript

Write keys where the citation belongs, before or after the full stop:

```
...sensitivity of 0.89 and specificity of 0.81 [@doi:10.1167/iovs.67.1.28].
...earlier work on mobility [@doi:10.1111/j.1444-0938.2007.00120.x; @pmid:18280134].
...the AAO referral model [@aao-vision-rehab-ppp].
```

- `@doi:` is the primary form: it is what the Screening tab holds, so it links
  the citation to the record and to its full text. Case does not matter.
- `@pmid:` when you only have a PubMed ID. It resolves to the paper's DOI, and a
  paper cited both ways gets one number (the report says "merged").
- `@key` (no colon) for anything without a DOI or PMID: web pages, NCBI Bookshelf
  chapters, guidelines, reports, hand-typed records such as Screening ID 14. The
  key is defined in `paper/bibliography_manual.csv`
  (`assets/bibliography_manual_template.csv` has one worked row per type).
  Keys are lower-case slugs; never reuse a key for a different source.
- Several keys in one bracket are separated by `;`. Keep the keys in the source
  manuscript forever; the rendered copy is a build product.

## Workflow

```bash
S=.claude/skills/manuscript-references/scripts
python3 -I $S/cite.py resolve paper/manuscript.md --bib paper/bibliography.json --manual paper/bibliography_manual.csv
python3 -I $S/cite.py check   paper/manuscript.md --bib paper/bibliography.json --manual paper/bibliography_manual.csv --style ama
python3 -I $S/wordcount.py    paper/manuscript.md   # body words per section; excludes keys, [VERIFY] tags, <!-- box --> blocks, tables, captions, references, author block
python3 -I $S/cite.py render  paper/manuscript.md --bib paper/bibliography.json --manual paper/bibliography_manual.csv --style ama --numbering paper/reference_numbers.csv
python3 -I $S/factcheck.py    paper/manuscript.md --bib paper/bibliography.json --manual paper/bibliography_manual.csv --out paper/factcheck_report.md --json paper/factcheck_report.json
```

1. **resolve** scans the manuscript for keys and fetches what the cache lacks:
   Crossref for a DOI (authors with given names, title, volume, pages), then
   PubMed esearch `<doi>[doi]` and esummary for the PMID and the NLM journal
   abbreviation (`source`), which is the abbreviation AMA and Vancouver want;
   Crossref's `short-container-title` is the publisher's own and is used only
   as a fallback. A PMID key goes the other way round. Results land in
   `paper/bibliography.json` (commit it: it makes everything else offline and
   reproducible). Polite by construction: one request at a time, 0.4 s between
   NCBI calls, retries on 429/5xx, `--mailto` or `CITE_MAILTO` for the contact
   address. `--offline` never touches the network; `--refresh` re-fetches.
   Manual CSV rows are read every run, so editing the CSV is enough.
2. **check** is the dry run: how many citations map to how many numbers, keys
   that resolve to nothing, entries never cited, duplicates. Exit 2 means fix
   something before rendering.
3. **render** numbers references by first appearance, writes
   `paper/manuscript_rendered.md` with the keys replaced by the style's
   markers (`.^1,3-5^` after punctuation for AMA; `[1,3-5].` for Vancouver) and
   `paper/references.md` in the chosen style. `--numbering` writes `n,id,label`
   so a reviewer can go from a number back to the key. Re-run after any edit;
   numbering shifts whenever a first citation moves. An unresolved key still gets
   a number and a `[UNRESOLVED ...]` line, so a draft can be read, but the exit
   code stays 2 until it is fixed.
4. **factcheck** (below) once the text is stable, then again after the fixes.

Sentence-case conversion of article titles (both styles) keeps acronyms,
words with digits, inner capitals and the entries of
`assets/protected_words.txt`; it will lower-case a proper noun it has not met
("Retimax"), so read the reference list once and add such words to that file.

## Reference style

`--style ama` (default) and `--style vancouver` load `assets/styles/*.json`:
author limits (AMA: up to 6, else first 3 + et al; Vancouver: 6 then et al),
initials, title case, italics, page condensing, date and DOI display, the
in-text marker, and one template per entry type (journal, chapter, book,
report, guideline, web, preprint, other). A template is a string of
`{fields}`; a `[ ... ]` group disappears when any field inside is empty, and
`\[ \]` are literal brackets. Glaucoma Today is a Bryn Mawr Communications
clinical magazine whose references are AMA-like, but the exact house format
(author count, whether DOIs appear, "Accessed" wording) must be copied from a
real entry in the target issue: `references/citation_formats.md` shows one
worked example per style and per entry type and how to edit the template.
Copy a style file, adjust it, and pass its path to `--style`. The same
templates render the manual entries, so a web page or Bookshelf chapter comes
out in the same voice as a journal article.

## Fact-checking numbers

```bash
python3 -I $S/factcheck.py paper/manuscript.md --bib paper/bibliography.json --manual paper/bibliography_manual.csv \
    --screening data/LVR_screening_sheet_2_Screening.csv --text-dir data/articles_text \
    --extraction analysis/extraction --prisma paper/prisma_counts.md \
    --out paper/factcheck_report.md --json paper/factcheck_report.json
```

For every sentence (and table cell) that contains a number the script records
the keys in that sentence, or failing that in its paragraph, and:

- finds the source text: key → DOI → Screening row → "Surname et al. - Year"
  file in `data/articles_text/`, the same matching as the screening-workbook
  skill's `included.py`; a manual CSV row may name a `text_file`; `--map
  doi:...=path.txt` overrides. Then it searches the text for the number with
  the sentence's key terms nearby, comparing numerically (89% = 0.89, 55.7 =
  55.71, 1,234 = 1234, "twelve" = 12), ignoring `volume(issue):pages` patterns
  in reference lists, and reports FOUND with page and quote, WEAK (number
  present, no key term near it), NOT FOUND, NO TEXT or NO CITATION. A year is
  checked against the cited entry's publication year.
- compares the number with the cited study's rows in `dta.csv`, `effects.csv`
  and `studies.csv` (column from the nearest term: sensitivity → `sens`, AUC →
  `auc`, participants → `n`, mean age → `age_mean`; table cells carry their
  column header): MATCH, MISMATCH, or CHECK when the number equals a different
  column than the term suggests (264 "participants" that is really
  `n_positive`). Changes ("increased by 0.05") are not compared.
- compares counts in sentences about records, studies, duplicates or screening
  with the stage table in `paper/prisma_counts.md` (prisma-reporting skill).

The Markdown report has a Summary, a Sources table (which text each key
mapped to and how), an Items table with an empty **Verdict** column, and a
"To verify" list of everything not cleanly FOUND and MATCHed, with the file
to open. Exit 2 while anything is NOT FOUND, MISMATCH, NO CITATION or
unresolved. FOUND is a string match near the right words, not a reading: the
reviewer or a verifier reads the quote. The one thing the script cannot do is
tell whether a sentence's *interpretation* of a number is right; that stays
with the reviewer.

### Verifying the open items with a subagent

Give one sonnet subagent (medium effort or higher, never haiku) the "To
verify" list in batches of 10 to 15 items, the article text paths, and the
brief in `references/verifier-brief.md`. For each item it must quote the
sentence from the source (with page) that supports the number, or write
`NOT SUPPORTED`, or `DERIVED: <arithmetic>` when the number follows from
reported ones, and never estimate or search the web for a substitute. Put its
answers in the Verdict column; the reviewer then fixes the manuscript (edit
the key-bearing `manuscript.md`, re-render) and re-runs the check until exit 0
or every remaining item has a written justification in `paper/factcheck_report.md`.

## What goes where

- `paper/manuscript.md`: source with keys (reviewer-owned).
- `paper/bibliography.json`: resolved metadata cache (generated; commit).
- `paper/bibliography_manual.csv`: hand-entered sources (reviewer-owned).
- `paper/manuscript_rendered.md`, `paper/references.md`,
  `paper/reference_numbers.csv`: generated by `render`.
- `paper/factcheck_report.md` / `.json`: generated by `factcheck`; the Verdict
  column is filled by the verifier and kept with the submission files.

Inputs come from the other skills: `analysis/extraction/*.csv`
(data-extraction), `paper/prisma_counts.md` (prisma-reporting), and the
Screening export plus `data/articles_text/` (screening-workbook, pdf-to-text).
Nothing here writes under `data/`.

## Disclosure

Reference resolution and fact-checking by these scripts, and any verifier
subagent, are AI assistance: the review's Methods must say so (the
prisma-reporting skill's `assets/methods_templates.md` has the paragraph), and
the reviewer remains responsible for every reference and every number.
Metadata from Crossref and PubMed can be wrong (publisher typos in titles,
missing issue numbers, authors listed as groups); read the rendered list once
against the PDFs before submission.

`references/validation.md` lists what was tested live and what to expect.
