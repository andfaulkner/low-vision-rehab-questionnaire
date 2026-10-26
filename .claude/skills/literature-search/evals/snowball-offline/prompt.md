---
tags: [literature-search]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Snowball from the two seed papers in seeds.txt: collect their reference lists and the papers that cite them, using only the cached OpenAlex responses in ./cache (there is no network). Drop anything that is already in our screening sheet (screening_records.csv), and give me a candidates.csv I can screen, with the papers linked to both seeds at the top. Which candidates are linked to both seeds?

Input files: seeds.txt, screening_records.csv, cache/
