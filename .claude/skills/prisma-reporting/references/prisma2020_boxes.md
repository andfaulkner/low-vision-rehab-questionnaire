# PRISMA 2020 flow diagram: box definitions and how the workbook maps to them

Source: Page et al. 2021 (BMJ 372:n71, Fig. 1 and Box 1) and the explanation paper (BMJ 372:n160, item 16a). The diagram has two templates: "databases and registers only" (one column) and "databases, registers and other methods" (two columns). `prisma_flow.py` picks the two-column template whenever other sources > 0.

## Vocabulary

- **Record**: the title or abstract (or both) of a report indexed in a database or website. One article found in PubMed and in Scopus is two records until de-duplication.
- **Report**: a document (journal article, preprint, thesis, conference abstract, web page) supplying information about a study. One report can describe several studies; one study can be described in several reports.
- **Study**: an investigation with a defined group of participants and methods. The unit of the "Studies included" count.
- **Records screened** are title/abstract decisions; **reports** are what you fetch and read in full.

## Boxes, left column (identification via databases and registers)

| Box | Definition | Workbook source (Counts tab) |
|---|---|---|
| Records identified from Databases (n per database) | Number of records retrieved from each database, before de-duplication. | "Records identified – PubMed" (78), "– Scopus" (88): typed from the search log dated 4 Oct 2026. If the search is re-run, these numbers change by hand. |
| Records identified from Registers | Trial registers (ClinicalTrials.gov, ICTRP). | None in this review; the script draws "Registers (n = 0)" only if you add one. |
| Records removed before screening: duplicates | Records removed because they are the same report as another record. | "Duplicates removed" = total identified − records screened (39). |
| Records marked as ineligible by automation tools | Removed by a classifier or filter without a human decision. | 0. The AI suggestions in columns N–P did **not** remove anything, because every record was screened by the reviewer, so this stays 0. Only put a number here if records were discarded on the model's say-so alone. |
| Records removed for other reasons | e.g. retracted, published before the date limit. | 0 unless the reviewer logs some. |
| Records screened | Records whose title/abstract was examined. | "Records screened (title/abstract)" (135 rows). "Screened so far" is a progress counter and never goes in the diagram. |
| Records excluded | Excluded at title/abstract; reasons are optional in the diagram but the Counts tab has them. | "Excluded at title/abstract". |
| Reports sought for retrieval | Records not excluded, for which the full text was sought. | "Included + Maybe → full text". |
| Reports not retrieved | Full text could not be obtained. | The full-text exclusion reason "Full text not available"; the script moves it here and subtracts it from "assessed" because PRISMA treats it as a retrieval failure, not an eligibility exclusion. |
| Reports assessed for eligibility | Full texts read against the criteria. | "Full texts assessed" minus not retrieved. |
| Reports excluded, with reasons | One reason per excluded report. | The "Full text" column of the exclusion-reasons table. |
| Studies included in review / Reports of included studies | Count both. They differ when a study has several reports or a report has several studies. | "Studies included" counts rows with Full-text decision = Include, i.e. reports. Override `studies_included` by hand if the two differ. |

## Boxes, right column (identification via other methods)

Websites, organisations, citation searching (reference lists, citing articles), hand-added sources. The official template takes these records straight to "Reports sought for retrieval", with their own "not retrieved", "assessed" and "excluded" boxes, because they were usually identified by someone who already judged them relevant, not by a database query.

This review's 8 hand-added key sources (records 128–135) were put into the Screening tab and title/abstract-screened with the rest, and the workbook's duplicate count is defined as total identified (174) − records screened (135), so the 8 are inside the "Records screened" figure. Two honest ways to draw that:

- `--other-mode same-pipeline` (default): draw the other-methods identification box and an arrow from it into "Records screened"; the left column's arithmetic is databases + other − duplicates = screened. State in the figure legend that hand-added records were screened together with the database records.
- `--other-mode separate` (official layout): give the right column its own counts (`other.sought`, `other.not_retrieved`, `other.assessed`, `other.excluded`, `other.included`) and reduce the left column accordingly (records screened = 127, etc.). You have to derive those numbers from the Screening tab by filtering IDs 128–135; the script will not guess them.

Either is acceptable under PRISMA 2020 as long as the legend says what was done; the explanation paper only requires that the counts be reported and reconcilable.

## Arithmetic the script checks

1. sum(databases) + sum(registers) [+ other sources in same-pipeline mode] − duplicates − automation − other reasons = records screened.
2. records screened − records excluded = reports sought.
3. reports sought − reports not retrieved = reports assessed.
4. reports assessed − sum(exclusion reasons) [+ other-method reports included] = reports of included studies.
5. Title/abstract exclusion reasons (if given) sum to records excluded; full-text reasons sum to the workbook's "Excluded at full text" minus not retrieved.
6. The workbook's stated total identified equals the sum of the sources.

While screening is incomplete the "Records screened" box is the number of rows (135) but the excluded and sought boxes count only the decided rows, so checks 2–4 fail: that is the expected state until column H is complete. The script reports it as "screening is incomplete: 40 of 135" and stamps the diagram DRAFT.

## Legend text

"Figure {N}. PRISMA 2020 flow diagram (Page et al. 2021). {Eight records known to the authors from the study outline were added by hand and screened together with the database records.} {Reports not retrieved were those for which no full text could be obtained.} AI-assisted screening suggestions were advisory; no record was removed by an automation tool."
