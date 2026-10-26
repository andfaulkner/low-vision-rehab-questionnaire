---
tags: [data-extraction]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Two independent extraction passes of the same papers are in passA/dta.csv and passB/dta.csv. Compare them and give me the list of disagreements I need to resolve. Don't decide them for me.

Input files: passA/dta.csv, passB/dta.csv
