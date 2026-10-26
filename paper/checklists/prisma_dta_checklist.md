# PRISMA-DTA checklist

McInnes MDF, Moher D, Thombs BD, et al. Preferred Reporting Items for a Systematic Review and Meta-analysis of Diagnostic Test Accuracy Studies: the PRISMA-DTA statement. JAMA 2018;319(4):388-396. Explanation and elaboration: Salameh J-P, et al. BMJ 2020;370:m2632.

PRISMA-DTA keeps the numbering of the original (2009) PRISMA: 27 items in total, of which two of the 2009 items were dropped (15 and 22, "risk of bias across studies", which does not transfer to accuracy studies) and two DTA-specific items were added (D1, D2). Wording below is condensed; use the official checklist from prisma-statement.org for submission. Use this checklist when the review pools or tabulates sensitivity/specificity; use it together with PRISMA 2020 when a journal asks for PRISMA 2020 (PRISMA-DTA has not been updated to the 2020 structure, so most authors complete both).

```bash
python3 -I .claude/skills/prisma-reporting/scripts/checklist_status.py paper/checklists/prisma_dta_checklist.md
```

| Item | Section / topic | Checklist item | Where reported (section/page) |
|---|---|---|---|
| 1 | Title | Identify the report as a systematic review (with or without meta-analysis) of diagnostic test accuracy (DTA) studies. | Title and dek (section 1): labelled 'systematic search with narrative synthesis' of test-accuracy and validation studies |
| 2 | Abstract | See PRISMA-DTA for Abstracts (table below). | N/A: magazine dek replaces a structured abstract |
| 3 | Rationale | Describe the rationale for the review in the context of what is already known. | Introduction: the referral gap (section 2); How glaucoma disables beyond visual acuity (section 3) |
| D1 | Clinical role of index test | State the scientific and clinical background, including the intended use and clinical role of the index test, and, if applicable, the rationale for minimally acceptable test accuracy (or minimum difference in accuracy for a comparative design). | Introduction: the referral gap (section 2); Proposed technician work-up protocol (section 7) (intended role: technician work-up screen before LVR referral) |
| 4 | Objectives | Provide an explicit statement of the question(s) being addressed in terms of participants, index test(s) and target condition(s). | Introduction: the referral gap (section 2); Methods paragraph (section 8, Future directions and Methods) |
| 5 | Protocol and registration | Indicate if a review protocol exists, if and where it can be accessed, and, if available, registration information including the registration number. | Methods paragraph (section 8, Future directions and Methods) (protocol/registration statement; [VERIFY]) |
| 6 | Eligibility criteria | Specify study characteristics (participants, setting, index test(s), reference standard(s), target condition(s), study design) and report characteristics (years considered, language, publication status) used as criteria for eligibility, giving rationale. | Methods paragraph (section 8, Future directions and Methods) (Eligibility criteria) |
| 7 | Information sources | Describe all information sources (e.g. databases with dates of coverage, contact with study authors to identify additional studies) in the search and the date last searched. | Methods paragraph (section 8, Future directions and Methods) (Information sources; dates) |
| 8 | Search | Present full search strategies for all electronic databases and other sources, including any limits used, such that they could be repeated. | Supplementary Table S1 (paper/search_log.md) |
| 9 | Study selection | State the process for selecting studies (screening, eligibility, inclusion in the systematic review and, if applicable, in the meta-analysis). | Methods paragraph (section 8, Future directions and Methods) (Selection process, AI-assistance disclosure) |
| 10 | Data collection process | Describe the method of data extraction from reports (e.g. piloted forms, independently, in duplicate) and any processes for obtaining and confirming data from investigators. | Methods paragraph (section 8, Future directions and Methods) (Data collection process: two passes, reconciliation) |
| 11 | Definitions for data extraction | Provide the definitions used in data extraction and the classifications of target condition(s), index test(s), reference standard(s) and other characteristics (e.g. unit of assessment, study design). | Methods paragraph (section 8, Future directions and Methods) (Data items; definitions of low vision and legal blindness thresholds) |
| 12 | Risk of bias and applicability | Describe the methods used for assessing risk of bias in individual studies and concerns regarding applicability to the review question (e.g. QUADAS-2). | Methods paragraph (section 8, Future directions and Methods) (QUADAS-2); Will it work in an LVR clinic? (section 6) (applicability) |
| 13 | Diagnostic accuracy measures | State the principal diagnostic accuracy measure(s) reported (e.g. sensitivity, specificity) and the unit of assessment (e.g. per patient, per eye). | Methods paragraph (section 8, Future directions and Methods) (Effect measures: sensitivity, specificity per person) |
| 14 | Synthesis of results | Describe the methods of handling data, combining results of studies and describing variability between studies, including: (a) multiple definitions of the target condition, (b) multiple thresholds of test positivity, (c) multiple index test readers, (d) indeterminate test results, (e) grouping and comparing tests, (f) different reference standards. | Methods paragraph (section 8, Future directions and Methods) (14(a) target-condition definitions, 14(b) thresholds reported per study and not combined, 14(e)-(f) groups by instrument and reference standard) |
| D2 | Meta-analysis | Report the statistical methods used for meta-analyses, if performed (e.g. bivariate model, HSROC), including software. | N/A: no meta-analysis (fewer than four independent studies per comparison); see Methods paragraph (section 8, Future directions and Methods) |
| 16 | Additional analyses | Describe the methods of additional analyses (e.g. sensitivity or subgroup analyses, meta-regression), if done, indicating which were pre-specified. | N/A: no additional analyses |
| 17 | Study selection | Provide the numbers of studies screened, assessed for eligibility and included in the review (and in the meta-analysis, if applicable), with reasons for exclusion at each stage, ideally with a flow diagram. | The two-question approach (section 5) and Figure 1 (PRISMA flow diagram) |
| 18 | Study characteristics | For each included study provide citations and key characteristics: (a) participant characteristics (presentation, prior testing), (b) clinical setting, (c) study design, (d) target condition definition, (e) index test, (f) reference standard, (g) sample size, (h) funding sources. | Full-length questionnaires (section 4); The two-question approach (section 5): study-characteristics table |
| 19 | Risk of bias and applicability | Present the evaluation of risk of bias and concerns regarding applicability for each study. | The two-question approach (section 5); Will it work in an LVR clinic? (section 6): QUADAS-2 table and traffic-light plot |
| 20 | Results of individual studies | For each analysis in each study (each unique combination of index test, reference standard and positivity threshold) report the 2x2 data (TP, FP, FN, TN) with estimates of diagnostic accuracy and confidence intervals, ideally with a forest or ROC plot. | The two-question approach (section 5): per-study accuracy table (2x2 counts where reconstructable) and unpooled forest plot |
| 21 | Synthesis of results | Describe test accuracy with confidence intervals for each index test (or by index test comparison, if applicable), including summary estimates of accuracy and variability (e.g. heterogeneity) between studies. | The two-question approach (section 5) (per-study accuracy with CIs; no summary estimate) |
| 23 | Additional analysis | Give the results of additional analyses, if done (e.g. sensitivity or subgroup analyses, meta-regression; analysis of index test failure rates, proportion of inconclusive results, adverse events). | N/A: no additional analyses |
| 24 | Summary of evidence | Summarise the main findings including the strength of evidence. | The two-question approach (section 5); Will it work in an LVR clinic? (section 6) (certainty ratings) |
| 25 | Limitations | Discuss limitations from the included studies (e.g. risk of bias and concerns regarding applicability) and from the review process (e.g. incomplete retrieval of identified research). | Will it work in an LVR clinic? (section 6) |
| 26 | Conclusions | Provide a general interpretation of the results in the context of other evidence. Discuss implications for future research and clinical practice (e.g. the intended use and clinical role of the index test). | Will it work in an LVR clinic? (section 6); Proposed technician work-up protocol (section 7) (Future directions) |
| 27 | Funding | For the systematic review, describe the sources of funding and other support and the role of the funders. | Author block and disclosures (section 1); [VERIFY: funding statement] |

Items 9, 10 and 12 are where the AI-assisted screening, extraction and QUADAS-2 support must be disclosed. Item 14(b) matters for this review: the screening questions and questionnaires are reported at different cut-offs, so say how thresholds were handled (pooled at a common threshold, pooled across thresholds with a caveat, or not pooled).

## PRISMA-DTA for Abstracts

Cohen JF, Deeks JJ, Korevaar DA, et al. Preferred Reporting Items for Journal and Conference Abstracts of Systematic Reviews and Meta-analyses of Diagnostic Test Accuracy Studies (PRISMA-DTA for Abstracts). BMJ 2021;372:n265. Condensed; 11 items.

| Item | Section / topic | Checklist item | Where reported (section/page) |
|---|---|---|---|
| A1 | Title | Identify the report as a systematic review (with or without meta-analysis) of DTA studies. | N/A: abstract word limit |
| A2 | Objectives | Indicate the research question, including the index test(s), target condition(s) and population. | N/A: abstract word limit |
| A3 | Eligibility criteria | Study characteristics used as eligibility criteria (participants, setting, index test, reference standard, target condition, study design). | N/A: abstract word limit |
| A4 | Information sources | Key databases searched and search dates. | N/A: abstract word limit |
| A5 | Risk of bias and applicability | Methods for assessing risk of bias and applicability. | N/A: abstract word limit |
| A6 | Synthesis of results | Methods for data synthesis. | N/A: abstract word limit |
| A7 | Included studies | Number and type of included studies and participants, and relevant characteristics of studies. | N/A: abstract word limit |
| A8 | Synthesis of results | Results for the analysis of diagnostic accuracy, preferably indicating the number of studies and participants, with summary estimates and their precision (e.g. 95% CI) when a meta-analysis was done. | N/A: abstract word limit |
| A9 | Discussion | Brief summary of the strengths and limitations of the evidence. | N/A: abstract word limit |
| A10 | Interpretation | General interpretation of the results and important implications. | N/A: abstract word limit |
| A11 | Funding and registration | Primary source of funding for the review; registration number and registry name. | N/A: abstract word limit |
