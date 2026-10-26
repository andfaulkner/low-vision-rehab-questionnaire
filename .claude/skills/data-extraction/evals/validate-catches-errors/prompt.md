---
tags: [data-extraction]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

The extraction tables for our low vision questionnaire review are in extraction/ (studies.csv, dta.csv, effects.csv, instruments.csv). Check them for problems before we try to pool anything, tell me exactly what needs fixing, and tell me whether any instrument has enough studies to pool. Don't change the numbers yourself.

Input files: extraction/studies.csv, extraction/dta.csv, extraction/effects.csv, extraction/instruments.csv
