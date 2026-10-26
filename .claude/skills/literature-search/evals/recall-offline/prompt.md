---
tags: [literature-search]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Measure how well the revised PubMed string in LVR_search_strategy.md recalls its key sources and the held-out papers, using only the cached E-utilities responses in ./cache (there is no network; do not try to fetch anything). Tell me the total number of records the string retrieves, how many key sources and held-out papers it finds, and exactly which ones it misses.

Input files: LVR_search_strategy.md, cache/
