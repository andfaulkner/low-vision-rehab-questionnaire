---
type: llm
focus: trace
weight: 1
---

The workbook was never saved through openpyxl (no Workbook.save / wb.save on LVR_screening_sheet_2.xlsx); every write went through the skill's set_cells.py or an in-place XML edit that keeps the x14 data validations.
