---
tags: [manuscript-references]
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Fact-check every number in manuscript.md against the cited article texts in articles_text/, the extraction tables in extraction/ and the PRISMA counts in prisma_counts.md. The screening export is screening.csv and the bibliography cache is bibliography.json (do not go online). Write the report to factcheck_report.md and tell me which claims are not supported or disagree with the tables. Do not change the manuscript or the tables.

Input files: manuscript.md, bibliography.json, screening.csv, prisma_counts.md, articles_text/Wu et al. - 2026 - Screening Questions to Identify Low Vision and Acu.txt, extraction/dta.csv, extraction/studies.csv
