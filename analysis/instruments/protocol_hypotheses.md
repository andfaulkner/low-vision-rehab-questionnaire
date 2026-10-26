# Protocol hypotheses and provenance for property_results.csv

This block was the `notes` row of `property_results.csv`; `rate_properties.py` requires every row to be a result, so it lives here and the hypothesis column cites H1-H6.

PROVISIONAL (AI chain step 7, advisory; reviewer confirms every cell against the cited page). Sources: analysis/extraction/effects.csv, analysis/extraction/instruments.csv, .claude/skills/instrument-synthesis/references/instrument_notes.md and the support quotes in analysis/risk_of_bias/cosmin.csv; page = [page N] marker of the article .txt (ID 128: section label, no page breaks). Instrument names follow analysis/risk_of_bias/cosmin_ratings.csv so the RoB join works. 

**Protocol hypotheses** (written once here, cited as H1-H6 in the hypothesis column; the authors of the primary studies stated none): H1 the questionnaire score correlates with logMAR distance VA (or letter score) at |r| >= 0.30, worse vision = worse score;
- H2 correlation with contrast sensitivity |r| >= 0.30;
- H3 correlation with a visual-field measure (mean deviation, binocular field, perimetric sensitivity) |r| >= 0.30;
- H4 known groups: visually impaired or LVR patients score worse than normally sighted controls, P < 0.05;
- H5 convergent validity: |r| >= 0.50 with another vision-specific PROM, 0.30-0.60 with a generic health measure;
- H6 responsiveness: the score improves after LVR with Cohen d >= 0.50 or P < 0.05 in a paired test, and does not change in an untreated control group. A questionnaire compared with measured VA is Hypotheses testing (no gold standard for a PROM); the single exception is the 100-item acuity survey (ID 128), which is built to estimate VA, so its r with measured VA is entered as Criterion validity and the reviewer may reclassify.

## Adoption

On 2026-10-26 the reviewer, told that H1-H6 were written by the AI chain after the data had been seen, decided to **keep them as the protocol hypotheses** ("These are reasonable cutoffs"). The Methods must say that the hypotheses were formulated by the review team (COSMIN allows generic review-team hypotheses when authors state none), state the thresholds, and acknowledge that they were fixed after data extraction. Borderline calls the thresholds decide: Di Maggio 2020 contrast rho 0.29 (ID 105 p4) counted as not confirmed under H2; Stelmack 2006 outpatient d = 0.29 with P = .0022 (ID 66 p7) and Selivanova 2019 well-being d = 0.37 with P = .0003 (ID 72 p4) counted as confirmed under H6's P-value arm.
