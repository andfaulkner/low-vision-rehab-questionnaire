# Translation report (2026-10-26)

PubMed string: 562 characters. Scopus draft: 559 characters. This translation is automatic and must be reviewed by a person and tested in Scopus before it is used or reported.

## Constructs that could not be translated (0)

None.

## Warnings: translated, but semantics differ (5)

- MeSH term "Vision, Low"[Majr] -> INDEXTERMS: Scopus has MeSH only for MEDLINE-derived records, no major-topic restriction, no tree explosion; [Majr] becomes a plain index-term match, so expect more records
- MeSH term "Sensitivity and Specificity"[Mesh] -> INDEXTERMS: Scopus has MeSH only for MEDLINE-derived records, no major-topic restriction, no tree explosion
- MeSH term "ROC Curve"[Mesh] -> INDEXTERMS: Scopus has MeSH only for MEDLINE-derived records, no major-topic restriction, no tree explosion
- the string contains NOT: Scopus applies AND NOT after all other operators regardless of parentheses, so move every AND NOT clause to the very end of the string and check the count
- language limit: LANGUAGE(english OR french) works inside the string; Scopus's own form is LIMIT-TO ( LANGUAGE , "English" ) OR LIMIT-TO ( LANGUAGE , "French" )

## Checks to do in Scopus

1. Paste the string into Advanced search; Scopus reports syntax errors inline.
2. Put every `AND NOT` clause and the language/date limits at the end.
3. Compare the record count with PubMed's; a large gap in either direction points at a field whose meaning differs (INDEXTERMS, TITLE-ABS-KEY, W/N).
4. Export the results (CSV with DOI) and check that the key sources with a DOI are in it; `snowball.py`'s de-duplication logic, or a DOI join, does this.
5. Record the final string, date and count in the search log (PRISMA-S items 8, 13, 15).
