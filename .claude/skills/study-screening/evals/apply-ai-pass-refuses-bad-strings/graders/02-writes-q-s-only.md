---
type: llm
focus: trace
weight: 1
---

After the run, the Screening sheet of LVR_screening_sheet_2.xlsx holds the decisions in the independent AI columns Q/R/S (e.g. Q6 = "Include" for ID 5, Q3 = "Exclude" with R3 = "Intervention study only" for ID 2, Q10 = "Exclude" with R10 = "No questionnaire/screening item" for ID 9), the reviewer's columns H-L are still empty, the writes went through set_cells.py (directly or via apply_decisions.py --apply) and never through openpyxl's save, and the CSV exports were regenerated.
