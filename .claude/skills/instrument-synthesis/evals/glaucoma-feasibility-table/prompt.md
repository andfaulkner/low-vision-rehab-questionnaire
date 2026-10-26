---
tags: [instrument-synthesis]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Build the instrument comparison table and the feasibility table for a technician work-up in our glaucoma clinic. Use the skill's instrument catalogue plus the instrument facts and study list we extracted (instruments.csv, studies.csv) and the COSMIN summary of findings (summary_of_findings.csv). I want Markdown I can paste into the manuscript, and I need to know which instruments actually cover visual-field and contrast loss, because our glaucoma patients often have good acuity.

Input files: instruments.csv, studies.csv, summary_of_findings.csv
