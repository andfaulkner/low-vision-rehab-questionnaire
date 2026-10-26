---
tags: [narrative-synthesis]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We are not meta-analysing. Build the Results table and figure for the accuracy of the single screening question and the VFQ-25, one row per study with 95% CIs, and tell me whether any group could still be pooled. dta.csv is the extraction, studies_with_datasets.csv has the confirmed dataset_id column, quadas2.csv has the QUADAS-2 judgements.

Input files: dta.csv, studies_with_datasets.csv, quadas2.csv
