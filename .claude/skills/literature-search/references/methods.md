# Methods behind the scripts, and when they do not apply

## Recall testing against a known set

A search string cannot be validated against the literature it did not
retrieve, so the standard check is recall against a set of records known
to be relevant: the "gold set" or "known-item" test (Sampson & McGowan
2006 on errors in search strategies; Cochrane Handbook ch. 4, Lefebvre et
al. 2023). The logic is the same as a diagnostic test: the key sources are
the "diseased", recall is sensitivity, and the record count stands in for
the false positives. Two caveats the script's output states:

1. **Tuning bias.** A string revised until it finds every key source is
   fitted to those papers. The doc avoided this with a held-out set of 14
   papers chosen before the string was finished and never used to tune
   it (the same idea as a validation sample in prediction modelling).
   Report both; the held-out figure is the one that says the string
   generalises. If a held-out paper is used to fix the string, it has
   joined the tuning set and the held-out count must be reduced.
2. **Precision is a judgement.** There is no correct trade-off between
   records screened and papers found; the reviewer decides how many
   title/abstract decisions a key source is worth. The per-arm table
   gives the price of each arm so the decision is explicit and can be
   reported (PRISMA-S item 7). Published guidance on sensitivity-
   maximising vs precision-maximising searches: Cochrane Handbook 4.4.3.

Known limitations: (a) PubMed counts drift as records are indexed, so
compare runs by `--diff`, not by eye; (b) `esearch` applies PubMed's
Automatic Term Mapping to untagged terms exactly as the web interface
does, so counts agree with the web, but a string pasted with different
quoting may not; (c) records not in PubMed (web pages, some reports)
cannot be tested this way and are listed as "no PubMed summary".

## Citation searching (snowballing)

Checking reference lists (backward) and citing articles (forward) is a
required supplementary method in Cochrane reviews (Handbook 4.3.5) and a
PRISMA-S item. Greenhalgh & Peacock (2005, BMJ 331:1064) found that in a
complex review most included sources came from snowballing and personal
knowledge rather than protocol-driven database searches; Horsley et al.
(2011, Cochrane Methodology Review MR000026) found reference checking
adds 2.5-43% of included studies; Wohlin (2014, EASE) formalised the
iterative start-set / backward / forward procedure; Cooper et al. (2018,
Health Info Libr J 35:265) review the evidence for supplementary search
methods.

How the script applies it:

- **Seeds** are the included studies (reviewer's columns only). Snowball
  once at title/abstract inclusion to find candidates early, and again
  from the final full-text included set, which is the one to report.
- **Sources.** OpenAlex (Priem, Piwowar & Orr 2022, arXiv:2205.01833)
  covers references and citations across publishers and gives abstracts;
  NCBI elink's `pubmed_pubmed_citedin` only sees citations from PubMed
  Central full texts, so it is the fallback. Neither is complete:
  OpenAlex misses references in some older or non-DOI papers, so a
  by-hand look at the reference list of a key paper is still worthwhile.
- **Prioritisation by `times_linked`.** A candidate linked from two or
  more included studies is far likelier to be relevant than one linked
  from one (the bibliographic-coupling / co-citation argument; Kessler
  1963, Small 1973). Screening the 2+ group first is the usual practical
  rule; whether to screen the one-link tail depends on its size and on
  the reviewer's time. Say in the log which groups were screened.
- **Iteration.** If a snowball round adds records that the reviewer
  includes, snowball from them too (Wohlin's iteration) until a round
  adds nothing. Each round is a row in the log.

## De-duplication thresholds

Candidates are matched to the Screening tab by DOI (normalised: lower
case, no `https://doi.org/` prefix, no trailing punctuation), by PMID (the
sheet has no PMID column, so the key-source table in the strategy doc
supplies IDs 5-135 where known), and by title. Title matching uses the
normalised title (NFKD accents stripped, lower case, punctuation to
spaces) compared exactly, then the Jaccard similarity of the word sets.
Bramer et al. (2016, J Med Libr Assoc 104:240) show that DOI plus
title/year matching catches nearly all database duplicates while keeping
false merges rare. The thresholds here: **>= 0.85 is a duplicate** (a
title differing by a subtitle, a trailing period or one word; an
11-word title with 2 words changed scores 0.82, so near-identical
variants pass and distinct papers from the same group, which usually
share fewer than half their words, do not); **0.60-0.85 is flagged** as
a possible duplicate and kept, because series papers ("Part I"/"Part
II", "clinical outcomes and cost-effectiveness" vs "Results of ... trial:
clinical outcomes and cost-effectiveness", which scored 0.83 in the test
run) live there and need a human eye. Both values are CLI options; if
they are changed, say so in the log (item 16).

## PubMed to Scopus translation

Scopus has no MeSH-aware search: `INDEXTERMS` searches the index terms
Scopus holds, which are MeSH for MEDLINE-sourced records and Emtree or
publisher keywords otherwise, with no explosion, no major-topic
restriction and no subheadings. `TITLE-ABS-KEY` is the usual equivalent
of PubMed `[tiab]` plus keywords; `TITLE-ABS` is closer to `[tiab]`
itself. Proximity: PubMed `"a b c"[ti:~N]` finds the words in any order
with up to N other words between them; Scopus `W/N` is pairwise and
order-free, `PRE/N` ordered. Scopus has no publication-type field that
matches PubMed `[pt]` values such as "Practice Guideline"; `DOCTYPE`
codes are broad (ar, re, ed, le, cp, ch, bk). `AND NOT` is applied after
all other operators, so a string with `AND NOT` in the middle does not
mean what it reads as. Scopus also treats `{...}` as exact phrase and
`"..."` as loose phrase (wildcards allowed, punctuation ignored). Because
of all this, the translation is a draft: run it, compare the count with
PubMed's, check the key sources by DOI in the export, and keep both
versions in the log. Scopus syntax reference: Elsevier Scopus Search
Tips (service.elsevier.com, "Scopus Advanced search").

## AI assistance

The strategy was developed and tested with AI assistance, and the scripts
here were written by an AI assistant. That is reportable under PRISMA-S
item 7 and PRISMA 2020 item 7, and the review's Methods must say so (see
the prisma-reporting skill's AI-disclosure template). The reviewer decides
the string, the seeds, the thresholds and which candidates enter the
review; the scripts only make those decisions reproducible.
