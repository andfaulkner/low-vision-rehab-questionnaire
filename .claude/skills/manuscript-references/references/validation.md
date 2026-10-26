# Validation of the scripts

Run on 26 Oct 2026 from the repository worktree against the live Crossref and
NCBI E-utilities services and the real `data/articles_text/` files, on a
synthetic manuscript kept (with its cached bibliography) in
`evals/render-ama-offline/files/`. No published worked example exists for a
citation renderer, so the checks are: known metadata for known DOIs, hand-set
expectations for numbering and the planted errors in the synthetic data.
Re-run these after any change to the scripts.

## cite.py resolve (live)

Keys scanned from the synthetic manuscript: 9 (4 DOIs, 1 PMID, 3 manual
keys, 1 undefined key). Five records from the Screening tab were used:

| Key | Screening ID | Expected | Obtained |
|---|---|---|---|
| doi:10.1167/iovs.67.1.28 | 92 | Wu YH ... Legge GE (6 authors), Invest Ophthalmol Vis Sci 2026;67(1):28 | identical; PMID found via esearch; source crossref+pubmed |
| doi:10.1167/tvst.13.9.20 | 128 | Wu YH ... (8 authors), Transl Vis Sci Technol 2024;13(9):20, PMID 39292468 | identical; NLM abbreviation came from PubMed (Crossref's short title was "Trans. Vis. Sci. Tech.") |
| pmid:39292468 | 128 | alias to doi:10.1167/tvst.13.9.20, one entry | alias written; one reference number in render ("merged" note) |
| doi:10.1111/j.1444-0938.2007.00120.x | 120 | Bibby SA, Maslin ER, Mcilraith R, Soong GP; Clin Exp Optom 2007;90(2):115-123 | identical; Crossref's U+2010 hyphen in "self‐reported" normalised to "-" |
| doi:10.1348/135910707X209835 | 19 | Dreer LE et al, Br J Health Psychol 2008;13(3):449-461, DOI displayed with the X | identical after the fix that keeps PubMed's DOI case (Crossref lower-cases DOIs) |
| key:verdina-retimax (ID 14, "No link") | 14 | rendered from the manual CSV | rendered; matched to its .txt by author + year |
| key:missing-key | - | reported as not defined | "PROBLEM: key:missing-key: not defined in the manual bibliography CSV", exit 2 |

12 network calls for 4 DOIs (Crossref + esearch + esummary each); a second
`resolve` made 0 calls (all cached). `--offline` on an empty cache listed the
4 DOI/PMID keys as "not in cache (offline)" and exited 2 without a request.

## cite.py render / check

Synthetic manuscript: 19 citation instances → 8 numbers, in the expected
first-appearance order (AAO guideline 1, CNIB web 2, Bibby 3, Wu 2026 4,
Wu 2024 5, Dreer 6, Verdina 7, unresolved 8). A sentence citing
`[@doi:iovs; @pmid:39292468]` rendered `.^4,5^` (a bug that printed only `^4^`
for a run of exactly two numbers was found by this test and fixed);
`[@doi:bibby; @doi:dreer]` rendered `^3,6^`. AMA output places the marker
after the full stop; Vancouver places `[4,5]` before it and condenses
`449-461` to `449-61`. The Vancouver web entry renders `[Internet]` and
`[cited 2026 Oct 26]` after the template-escape fix. `check` printed the
same report as `render` without writing files and exited 2 (unresolved key).
Duplicate detection: a manual row given the same DOI as a cited `@doi:` key
produced "duplicate: ... share DOI" and exit 2 (`evals/check-finds-duplicates`).

Sentence case lower-cased "Retimax" (not in `protected_words.txt`), as
documented; "Veterans Affairs" and acronyms are kept.

## factcheck.py

Synthetic manuscript, real texts for Wu 2026 (ID 92), Bibby 2007 (ID 120),
Dreer 2008 (ID 19) and Verdina 2020 (ID 14), synthetic `dta.csv` with the
restaurant-menu specificity deliberately entered as 0.78 (paper: 0.81) and a
synthetic `prisma_counts.md` with 10 included studies. 25 numeric items.

| Planted claim | Expected | Obtained |
|---|---|---|
| "385 adults ... 100-item survey" | FOUND p1; CSV MATCH studies.n = 385, n_items = 100 | as expected |
| "sensitivity of 0.89 and a specificity of 0.81" | both FOUND p1; 0.89 MATCH dta.sens; 0.81 MISMATCH vs dta.spec 0.78 | as expected (0.71 of the keyboard row is listed too) |
| "264 of 385 participants had low vision" | 264 NOT FOUND (the paper gives 121 better than 20/40, 264 is derived); CSV CHECK equals dta.n_positive | as expected |
| table cell "Specificity: 0.81" | FOUND; MISMATCH vs CSV (column header used as the hint) | as expected |
| "increased the AUC by at most 0.05" | FOUND; not compared with dta.auc (a change) | as expected |
| "Mean age ... 55.7 years" | FOUND p3 (55.71 rounds to 55.7); MATCH age_mean | as expected |
| "Wu et al. (2026)" | year = publication year | FOUND |
| "Twelve studies were included" (Methods, uncited) | PRISMA MISMATCH vs 10 | as expected, number word parsed |
| "135 records ... 39 duplicates" | PRISMA MATCH | as expected; "4 October 2026" no longer yields a bogus "4" or a year |
| "20/200 ... 20 degrees" cited to a web page | NO TEXT | as expected |
| "Roughly 10% ... without a source" | no own key: paragraph keys used, flagged for verification | listed under "To verify" as paragraph citation |
| "r = -0.76" (Bibby) | number is in the text as -0.762 | FOUND via rounding |

Known false positives, kept because the verifier reads the quote: "44% of
the variance" matched ".44" in Dreer's item-total correlations (FOUND with key
terms nearby); "12 words per minute" matched a "12" in Verdina's text.
Masking `year;vol(issue):pages` patterns removed the reference-list hits
that appeared before the fix.

Exit codes: 2 with the planted errors; 0 on a copy of the manuscript with the
planted sentences removed, "Twelve" changed to "Ten" and the CSV specificity
restored to 0.81 (18 items: 15 FOUND, 3 COUNTS; the uncited Methods counts
that match `prisma_counts.md` are reported as COUNTS and not as problems).

## Template CSV

Rendering `assets/bibliography_manual_template.csv` (chapter, report, web,
guideline rows) in both styles produced the entries quoted in
`citation_formats.md`. An "et al." typed as an author in the CSV was first
rendered as the author "al. E"; `split_people` now drops it.

## Not verified

- The AMA and Vancouver rules are implemented from memory of the AMA Manual
  (11th ed.) and NLM Citing Medicine; compare the output with one real entry
  from the target issue before submission (see citation_formats.md).
- NCBI Bookshelf records were not fetched (they are manual entries); the
  Bookshelf example row is fictitious.
- The eval cases were not run with `claude plugin eval`; their expected
  outcomes were checked by running the scripts on the case files.
