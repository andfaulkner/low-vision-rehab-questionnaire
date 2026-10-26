---
tags: [data-extraction]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Extract the screening-question accuracy data from paper.txt into the data-extraction CSVs (studies.csv, dta.csv, instruments.csv) in a folder called extraction/. Treat the study as Screening ID 999 (a test ID that is not in the screening sheet). The paper only reports sensitivity and specificity, so reconstruct the 2x2 table. Tell me what you could not find in the paper.

Input files: paper.txt
