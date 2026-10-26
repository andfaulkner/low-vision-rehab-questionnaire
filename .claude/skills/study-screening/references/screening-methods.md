# Screening methods: what the guidance says and what the statistics mean

## Study selection in guidance

**Cochrane Handbook, chapter 4 (Lefebvre C, Glanville J, Briscoe S, et al.
Searching for and selecting studies. In: Higgins JPT, Thomas J, et al., eds.
Cochrane Handbook for Systematic Reviews of Interventions, version 6.4, 2023),
section 4.6 "Selecting studies".** Selection should be done by at least two
people working independently, at both the title/abstract and the full-text
stage, with disagreements resolved by consensus or a third person; eligibility
criteria should be piloted on a sample before the full screen; the process and
the number of reviewers must be reported. The Handbook accepts a single
screener with a second person checking a sample, or machine-assisted
screening, as a compromise that must be described, and it notes that reviewers
should err on the side of inclusion at title/abstract (hence Maybe). Chapter
4 also says automation tools may be used to support screening, provided they
are described and their outputs are checked by a human.

**PRISMA 2020 (Page MJ, McKenzie JE, Bossuyt PM, et al. BMJ 2021;372:n71),
item 8, Selection process.** "Specify the methods used to decide whether a
study met the inclusion criteria of the review, including how many reviewers
screened each record and each report retrieved, whether they worked
independently, and if applicable, details of automation tools used in the
process." Items 9 (data collection) and 11 (risk of bias) repeat the automation
clause. The explanation paper (Page et al. BMJ 2021;372:n160) asks reviews
that used a tool to say how it was trained or configured, how its
performance was checked, and what role its output had. For this review that
means: the model and version, the rules file, that suggestions were stored
apart from decisions, the percentage overridden, and the verification sample.

**PRISMA-DTA (McInnes MDF, Moher D, Thombs BD, et al. JAMA 2018;319:388-396)**
keeps item 8 unchanged and adds nothing about selection; it matters here for
the full-text stage, where eligibility turns on whether an accuracy or
measurement-property analysis exists at all.

## The evidence on single-reviewer screening

- Gartlehner G, Affengruber L, Titscher V, Noel-Storr A, Dooley G, Ballarini
  N, König F. Single-reviewer abstract screening missed 13 percent of relevant
  studies: a crowd-based, randomized controlled trial. J Clin Epidemiol
  2020;121:20-28. doi:10.1016/j.jclinepi.2020.01.005. 280 participants, 24,942
  decisions on 2,000 abstracts from two published reviews. Single-reviewer
  sensitivity 86.6% (95% CI 80.6-91.2), dual-reviewer 97.5% (95.1-98.8);
  specificities 79.2% and 68.7%. Conclusion: single screening "does not appear
  to fulfill the high methodological standards that decision makers expect
  from systematic reviews" but may suit rapid reviews.
- Waffenschmidt S, Knelangen M, Sieben W, Bühn S, Pieper D. Single screening
  versus conventional double screening for study selection in systematic
  reviews: a methodological systematic review. BMC Med Res Methodol
  2019;19:132. doi:10.1186/s12874-019-0782-0. Four evaluations, 23 single
  screenings. Median proportion of relevant studies missed 5% (range 0-58%):
  3% (0-21%) for six experienced reviewers, 13% (0-58%) for three less
  experienced ones. In 3 of 7 single screenings whose meta-analyses were
  re-run, all by the same inexperienced reviewer, the findings would have
  changed substantially. Conclusion: not equivalent to double screening, but
  an acceptable shortcut in rapid reviews when done by an experienced reviewer.

Both abstracts were retrieved from PubMed (PMIDs 31972274 and 31253092) on
2026-10-26 and the figures above are quoted from them.

What this means for the review: the design is one experienced clinician
reviewer plus an AI second screen plus a second human on a sample. Report it
that way, with the numbers, and do not call it dual screening. The AI pass is
closest in spirit to the "second screener who flags possible misses": its
Includes that the reviewer excluded are the list to re-check, and its recall of
the reviewer's Includes is the number that says how useful it was as a safety
net. The honest limitation sentence is that records excluded by both the
reviewer and the AI were not seen by a second human unless they fell in the
verification sample.

## AI assistance and its disclosure

Say in the Methods: the model name and version; the tasks it did (title/abstract
suggestions, full-text suggestions, scripts, drafting); the written rules it
followed; that its outputs were stored separately and were advisory; that the
reviewer read and decided every record; the number and percentage of records
where the reviewer's decision differed from the suggestion; and that AI
outputs were not used to exclude any record without a human decision. Check
the journal's own AI policy (Glaucoma Today's author instructions) and follow
it where stricter. Guidance on reporting AI in evidence synthesis is still
settling (the 2024-2025 joint position of Cochrane, Campbell, JBI and the
Collaboration for Environmental Evidence on responsible AI in evidence
synthesis, and the RAISE recommendations, ask for these elements; verify the
exact citation and version before quoting either); when in doubt, say more.

## Agreement statistics

**Percent agreement** is the share of paired records where both sides gave the
same (collapsed) decision. It is what readers understand, and it is inflated
when one category dominates.

**Cohen's kappa** (Cohen J. Educ Psychol Meas 1960;20:37-46) corrects for the
agreement expected from the two raters' marginal frequencies:
kappa = (p_o - p_e) / (1 - p_e). The script gives the large-sample standard
error of Fleiss JL, Cohen J, Everitt BS (Psychol Bull 1969;72:323-327; the
form in Fleiss, Levin and Paik, Statistical Methods for Rates and Proportions,
3rd ed. 2003, eq. 18.15), which holds for k categories and is the one to use
for a confidence interval (the simpler variance under kappa = 0 is for
testing against zero only). The CI is kappa +/- 1.96 SE, truncated to [-1, 1].
With 40 paired records the CI is wide (0.10 to 0.71 on the current sheet);
with 135 it narrows but stays a rough guide.

**Interpretation bands** are conventions, not thresholds:

| kappa | Landis and Koch 1977 (Biometrics 33:159-174) | McHugh 2012 (Biochem Med 22:276-282) |
|---|---|---|
| < 0 | poor | none |
| 0.00-0.20 | slight | none |
| 0.21-0.40 | fair | minimal |
| 0.41-0.60 | moderate | weak |
| 0.61-0.80 | substantial | moderate |
| 0.81-0.90 | almost perfect | strong |
| 0.91-1.00 | almost perfect | almost perfect |

The Cochrane Handbook (section 4.6) quotes Orwin's bands (0.40-0.59 fair,
0.60-0.74 good, 0.75+ excellent). Landis and Koch called their own divisions
"clearly arbitrary". Three reasons the bands are rough:

1. **Prevalence.** When one category dominates (27 Exclude to 13 Include/Maybe
   here), p_e is high and kappa is low even at good percent agreement; the
   same raters would score higher on a balanced set (Feinstein AR, Cicchetti
   DV. J Clin Epidemiol 1990;43:543-549, the "kappa paradoxes").
2. **Bias.** Kappa rises when the two raters' marginals differ, which is the
   opposite of what one wants (Byrt T, Bishop J, Carlin JB. J Clin Epidemiol
   1993;46:423-429). The script prints the prevalence index (a - d)/n and bias
   index (b - c)/n so these effects are visible.
3. **Number of categories and collapsing.** A 3x3 kappa (Maybe separate) is
   not comparable to the 2x2 after collapsing, and Maybe is by construction a
   hedge, so the 3x3 is always lower. Say which was computed.

**PABAK** (prevalence-adjusted bias-adjusted kappa, Byrt 1993) is
(k p_o - 1)/(k - 1): the kappa the data would give with balanced marginals.
Report it next to kappa; the gap between the two is the size of the
prevalence effect. It is not a replacement, because it is just a rescaling of
percent agreement.

**Specific agreement** (2 n_ii / (n_i. + n_.i)) says how well the raters agree
on each category separately; for a screen the Include row is the one that
matters, and the "B recall of A's Include" line (the share of the reviewer's
Includes that the AI also kept) is the plain-language version of it.

**Bootstrap.** `--bootstrap 2000` resamples records with replacement and
reports the 2.5th and 97.5th percentiles of kappa; use it when n is small or
a cell is empty, where the asymptotic SE is least trustworthy. On the current
sheet the two intervals agree to about 0.02.

## Reporting sentence (fill from agreement.py and sample_records.py)

"One reviewer (XX) screened all N records; a large language model (model,
version) produced an advisory suggestion for each record from the written rules
(docs/AI_title_abstract_screening_rules.md), stored separately from the
reviewer's decisions. The reviewer's decision differed from the suggestion for
n of N records (p%; Cohen's kappa k, 95% CI a to b, Maybe counted as Include).
A second reviewer (YY) independently screened a random 20% sample (n records,
seed s, stratified by AI suggestion); agreement was k2 (95% CI), and the x
disagreements were resolved by discussion. Of the m records sought at full
text, r could not be retrieved."
