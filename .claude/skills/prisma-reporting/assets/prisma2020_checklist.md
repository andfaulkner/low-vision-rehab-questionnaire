# PRISMA 2020 checklist

Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ 2021;372:n71. Item wording is condensed from the published checklist; the official PDF/Word versions are at prisma-statement.org and should be the ones submitted if a journal asks for the checklist itself.

Fill the last column with the manuscript section and page (or line) where the item is reported, "N/A: reason" when it does not apply (e.g. 13d when no meta-analysis was done; say "no meta-analysis, see Synthesis"), and leave it blank until it is reported. Check progress with:

```bash
python3 -I .claude/skills/prisma-reporting/scripts/checklist_status.py paper/checklists/prisma2020_checklist.md
```

| Item | Section / topic | Checklist item | Where reported (section/page) |
|---|---|---|---|
| 1 | Title | Identify the report as a systematic review. |  |
| 2 | Abstract | See the PRISMA 2020 for Abstracts checklist (table below). |  |
| 3 | Rationale | Describe the rationale for the review in the context of existing knowledge. |  |
| 4 | Objectives | Provide an explicit statement of the objective(s) or question(s) the review addresses. |  |
| 5 | Eligibility criteria | Specify the inclusion and exclusion criteria for the review and how studies were grouped for the syntheses. |  |
| 6 | Information sources | Specify all databases, registers, websites, organisations, reference lists and other sources searched or consulted to identify studies. Specify the date when each source was last searched or consulted. |  |
| 7 | Search strategy | Present the full search strategies for all databases, registers and websites, including any filters and limits used. |  |
| 8 | Selection process | Specify the methods used to decide whether a study met the inclusion criteria, including how many reviewers screened each record and each report retrieved, whether they worked independently, and, if applicable, details of automation tools used in the process. |  |
| 9 | Data collection process | Specify the methods used to collect data from reports, including how many reviewers collected data from each report, whether they worked independently, any processes for obtaining or confirming data from study investigators, and, if applicable, details of automation tools used. |  |
| 10a | Data items (outcomes) | List and define all outcomes for which data were sought. Specify whether all results compatible with each outcome domain in each study were sought (e.g. for all measures, time points, analyses), and if not, the methods used to decide which results to collect. |  |
| 10b | Data items (other variables) | List and define all other variables for which data were sought (e.g. participant and intervention characteristics, funding sources). Describe any assumptions made about missing or unclear information. |  |
| 11 | Study risk of bias assessment | Specify the methods used to assess risk of bias in the included studies, including details of the tool(s) used, how many reviewers assessed each study and whether they worked independently, and, if applicable, details of automation tools used. |  |
| 12 | Effect measures | Specify for each outcome the effect measure(s) (e.g. risk ratio, mean difference) used in the synthesis or presentation of results. |  |
| 13a | Synthesis methods (eligibility) | Describe the processes used to decide which studies were eligible for each synthesis (e.g. tabulating study characteristics and comparing against the planned groups for each synthesis, item 5). |  |
| 13b | Synthesis methods (data preparation) | Describe any methods required to prepare the data for presentation or synthesis, such as handling of missing summary statistics or data conversions. |  |
| 13c | Synthesis methods (display) | Describe any methods used to tabulate or visually display results of individual studies and syntheses. |  |
| 13d | Synthesis methods (synthesis) | Describe any methods used to synthesize results and provide a rationale for the choice(s). If meta-analysis was performed, describe the model(s), method(s) to identify the presence and extent of statistical heterogeneity, and software package(s) used. |  |
| 13e | Synthesis methods (heterogeneity) | Describe any methods used to explore possible causes of heterogeneity among study results (e.g. subgroup analysis, meta-regression). |  |
| 13f | Synthesis methods (sensitivity) | Describe any sensitivity analyses conducted to assess robustness of the synthesized results. |  |
| 14 | Reporting bias assessment | Describe any methods used to assess risk of bias due to missing results in a synthesis (arising from reporting biases). |  |
| 15 | Certainty assessment | Describe any methods used to assess certainty (or confidence) in the body of evidence for an outcome. |  |
| 16a | Study selection (flow) | Describe the results of the search and selection process, from the number of records identified in the search to the number of studies included in the review, ideally using a flow diagram. |  |
| 16b | Study selection (near-misses) | Cite studies that might appear to meet the inclusion criteria but which were excluded, and explain why they were excluded. |  |
| 17 | Study characteristics | Cite each included study and present its characteristics. |  |
| 18 | Risk of bias in studies | Present assessments of risk of bias for each included study. |  |
| 19 | Results of individual studies | For all outcomes, present, for each study: (a) summary statistics for each group (where appropriate) and (b) an effect estimate and its precision (e.g. confidence/credible interval), ideally using structured tables or plots. |  |
| 20a | Results of syntheses (overview) | For each synthesis, briefly summarise the characteristics and risk of bias among contributing studies. |  |
| 20b | Results of syntheses (estimates) | Present results of all statistical syntheses conducted. If meta-analysis was done, present for each the summary estimate and its precision (e.g. confidence/credible interval) and measures of statistical heterogeneity. If comparing groups, describe the direction of the effect. |  |
| 20c | Results of syntheses (heterogeneity) | Present results of all investigations of possible causes of heterogeneity among study results. |  |
| 20d | Results of syntheses (sensitivity) | Present results of all sensitivity analyses conducted to assess the robustness of the synthesized results. |  |
| 21 | Reporting biases | Present assessments of risk of bias due to missing results (arising from reporting biases) for each synthesis assessed. |  |
| 22 | Certainty of evidence | Present assessments of certainty (or confidence) in the body of evidence for each outcome assessed. |  |
| 23a | Discussion (interpretation) | Provide a general interpretation of the results in the context of other evidence. |  |
| 23b | Discussion (evidence limitations) | Discuss any limitations of the evidence included in the review. |  |
| 23c | Discussion (process limitations) | Discuss any limitations of the review processes used. |  |
| 23d | Discussion (implications) | Discuss implications of the results for practice, policy, and future research. |  |
| 24a | Registration | Provide registration information for the review, including register name and registration number, or state that the review was not registered. |  |
| 24b | Protocol | Indicate where the review protocol can be accessed, or state that a protocol was not prepared. |  |
| 24c | Amendments | Describe and explain any amendments to information provided at registration or in the protocol. |  |
| 25 | Support | Describe sources of financial or non-financial support for the review, and the role of the funders or sponsors in the review. |  |
| 26 | Competing interests | Declare any competing interests of review authors. |  |
| 27 | Availability of data, code and other materials | Report which of the following are publicly available and where they can be found: template data collection forms; data extracted from included studies; data used for all analyses; analytic code; any other materials used in the review. |  |

Items 8, 9 and 11 are where the AI-assisted screening, extraction and risk-of-bias support belong ("details of automation tools used"): name the tool and model, what it did, and that the reviewer made every decision. Item 27 is where to say whether the screening workbook, extraction CSVs and scripts are shared.

## PRISMA 2020 for Abstracts

Page MJ, et al. BMJ 2021;372:n71, Table 2. Needed if the journal uses a structured abstract; for a short trade-journal abstract, cover as many items as the word limit allows and note the rest here as "N/A: abstract word limit".

| Item | Section / topic | Checklist item | Where reported (section/page) |
|---|---|---|---|
| A1 | Title | Identify the report as a systematic review. |  |
| A2 | Objectives | Provide an explicit statement of the main objective(s) or question(s) the review addresses. |  |
| A3 | Eligibility criteria | Specify the inclusion and exclusion criteria for the review. |  |
| A4 | Information sources | Specify the information sources (e.g. databases, registers) used to identify studies and the date when each was last searched. |  |
| A5 | Risk of bias | Specify the methods used to assess risk of bias in the included studies. |  |
| A6 | Synthesis of results | Specify the methods used to present and synthesise results. |  |
| A7 | Included studies | Give the total number of included studies and participants and summarise relevant characteristics of studies. |  |
| A8 | Synthesis of results | Present results for main outcomes, preferably indicating the number of included studies and participants for each. If meta-analysis was done, report the summary estimate and confidence/credible interval. If comparing groups, indicate the direction of the effect. |  |
| A9 | Limitations of evidence | Provide a brief summary of the limitations of the evidence included in the review (e.g. study risk of bias, inconsistency and imprecision). |  |
| A10 | Interpretation | Provide a general interpretation of the results and important implications. |  |
| A11 | Funding | Specify the primary source of funding for the review. |  |
| A12 | Registration | Provide the register name and registration number. |  |
