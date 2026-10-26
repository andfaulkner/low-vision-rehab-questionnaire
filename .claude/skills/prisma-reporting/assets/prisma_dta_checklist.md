# PRISMA-DTA checklist

McInnes MDF, Moher D, Thombs BD, et al. Preferred Reporting Items for a Systematic Review and Meta-analysis of Diagnostic Test Accuracy Studies: the PRISMA-DTA statement. JAMA 2018;319(4):388-396. Explanation and elaboration: Salameh J-P, et al. BMJ 2020;370:m2632.

PRISMA-DTA keeps the numbering of the original (2009) PRISMA: 27 items in total, of which two of the 2009 items were dropped (15 and 22, "risk of bias across studies", which does not transfer to accuracy studies) and two DTA-specific items were added (D1, D2). Wording below is condensed; use the official checklist from prisma-statement.org for submission. Use this checklist when the review pools or tabulates sensitivity/specificity; use it together with PRISMA 2020 when a journal asks for PRISMA 2020 (PRISMA-DTA has not been updated to the 2020 structure, so most authors complete both).

```bash
python3 -I .claude/skills/prisma-reporting/scripts/checklist_status.py paper/checklists/prisma_dta_checklist.md
```

| Item | Section / topic | Checklist item | Where reported (section/page) |
|---|---|---|---|
| 1 | Title | Identify the report as a systematic review (with or without meta-analysis) of diagnostic test accuracy (DTA) studies. |  |
| 2 | Abstract | See PRISMA-DTA for Abstracts (table below). |  |
| 3 | Rationale | Describe the rationale for the review in the context of what is already known. |  |
| D1 | Clinical role of index test | State the scientific and clinical background, including the intended use and clinical role of the index test, and, if applicable, the rationale for minimally acceptable test accuracy (or minimum difference in accuracy for a comparative design). |  |
| 4 | Objectives | Provide an explicit statement of the question(s) being addressed in terms of participants, index test(s) and target condition(s). |  |
| 5 | Protocol and registration | Indicate if a review protocol exists, if and where it can be accessed, and, if available, registration information including the registration number. |  |
| 6 | Eligibility criteria | Specify study characteristics (participants, setting, index test(s), reference standard(s), target condition(s), study design) and report characteristics (years considered, language, publication status) used as criteria for eligibility, giving rationale. |  |
| 7 | Information sources | Describe all information sources (e.g. databases with dates of coverage, contact with study authors to identify additional studies) in the search and the date last searched. |  |
| 8 | Search | Present full search strategies for all electronic databases and other sources, including any limits used, such that they could be repeated. |  |
| 9 | Study selection | State the process for selecting studies (screening, eligibility, inclusion in the systematic review and, if applicable, in the meta-analysis). |  |
| 10 | Data collection process | Describe the method of data extraction from reports (e.g. piloted forms, independently, in duplicate) and any processes for obtaining and confirming data from investigators. |  |
| 11 | Definitions for data extraction | Provide the definitions used in data extraction and the classifications of target condition(s), index test(s), reference standard(s) and other characteristics (e.g. unit of assessment, study design). |  |
| 12 | Risk of bias and applicability | Describe the methods used for assessing risk of bias in individual studies and concerns regarding applicability to the review question (e.g. QUADAS-2). |  |
| 13 | Diagnostic accuracy measures | State the principal diagnostic accuracy measure(s) reported (e.g. sensitivity, specificity) and the unit of assessment (e.g. per patient, per eye). |  |
| 14 | Synthesis of results | Describe the methods of handling data, combining results of studies and describing variability between studies, including: (a) multiple definitions of the target condition, (b) multiple thresholds of test positivity, (c) multiple index test readers, (d) indeterminate test results, (e) grouping and comparing tests, (f) different reference standards. |  |
| D2 | Meta-analysis | Report the statistical methods used for meta-analyses, if performed (e.g. bivariate model, HSROC), including software. |  |
| 16 | Additional analyses | Describe the methods of additional analyses (e.g. sensitivity or subgroup analyses, meta-regression), if done, indicating which were pre-specified. |  |
| 17 | Study selection | Provide the numbers of studies screened, assessed for eligibility and included in the review (and in the meta-analysis, if applicable), with reasons for exclusion at each stage, ideally with a flow diagram. |  |
| 18 | Study characteristics | For each included study provide citations and key characteristics: (a) participant characteristics (presentation, prior testing), (b) clinical setting, (c) study design, (d) target condition definition, (e) index test, (f) reference standard, (g) sample size, (h) funding sources. |  |
| 19 | Risk of bias and applicability | Present the evaluation of risk of bias and concerns regarding applicability for each study. |  |
| 20 | Results of individual studies | For each analysis in each study (each unique combination of index test, reference standard and positivity threshold) report the 2x2 data (TP, FP, FN, TN) with estimates of diagnostic accuracy and confidence intervals, ideally with a forest or ROC plot. |  |
| 21 | Synthesis of results | Describe test accuracy with confidence intervals for each index test (or by index test comparison, if applicable), including summary estimates of accuracy and variability (e.g. heterogeneity) between studies. |  |
| 23 | Additional analysis | Give the results of additional analyses, if done (e.g. sensitivity or subgroup analyses, meta-regression; analysis of index test failure rates, proportion of inconclusive results, adverse events). |  |
| 24 | Summary of evidence | Summarise the main findings including the strength of evidence. |  |
| 25 | Limitations | Discuss limitations from the included studies (e.g. risk of bias and concerns regarding applicability) and from the review process (e.g. incomplete retrieval of identified research). |  |
| 26 | Conclusions | Provide a general interpretation of the results in the context of other evidence. Discuss implications for future research and clinical practice (e.g. the intended use and clinical role of the index test). |  |
| 27 | Funding | For the systematic review, describe the sources of funding and other support and the role of the funders. |  |

Items 9, 10 and 12 are where the AI-assisted screening, extraction and QUADAS-2 support must be disclosed. Item 14(b) matters for this review: the screening questions and questionnaires are reported at different cut-offs, so say how thresholds were handled (pooled at a common threshold, pooled across thresholds with a caveat, or not pooled).

## PRISMA-DTA for Abstracts

Cohen JF, Deeks JJ, Korevaar DA, et al. Preferred Reporting Items for Journal and Conference Abstracts of Systematic Reviews and Meta-analyses of Diagnostic Test Accuracy Studies (PRISMA-DTA for Abstracts). BMJ 2021;372:n265. Condensed; 11 items.

| Item | Section / topic | Checklist item | Where reported (section/page) |
|---|---|---|---|
| A1 | Title | Identify the report as a systematic review (with or without meta-analysis) of DTA studies. |  |
| A2 | Objectives | Indicate the research question, including the index test(s), target condition(s) and population. |  |
| A3 | Eligibility criteria | Study characteristics used as eligibility criteria (participants, setting, index test, reference standard, target condition, study design). |  |
| A4 | Information sources | Key databases searched and search dates. |  |
| A5 | Risk of bias and applicability | Methods for assessing risk of bias and applicability. |  |
| A6 | Synthesis of results | Methods for data synthesis. |  |
| A7 | Included studies | Number and type of included studies and participants, and relevant characteristics of studies. |  |
| A8 | Synthesis of results | Results for the analysis of diagnostic accuracy, preferably indicating the number of studies and participants, with summary estimates and their precision (e.g. 95% CI) when a meta-analysis was done. |  |
| A9 | Discussion | Brief summary of the strengths and limitations of the evidence. |  |
| A10 | Interpretation | General interpretation of the results and important implications. |  |
| A11 | Funding and registration | Primary source of funding for the review; registration number and registry name. |  |
