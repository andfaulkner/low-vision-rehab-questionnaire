---
tags: [risk-of-bias]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Do a QUADAS-2 risk-of-bias assessment of Gresset and Baumgarten 2002 (study_id Gresset2002) for our systematic review of self-report screening questions for low vision rehabilitation need. The full text is in gresset2002.txt (each page starts with a "[page N]" line). Write the four domain rows to quadas2.csv in the layout of the skill's template and tell me the judgements.

Input files: gresset2002.txt
