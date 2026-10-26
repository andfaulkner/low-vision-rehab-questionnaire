"""Count independent datasets per instrument x comparator class for correlation rows in effects.csv.

Used by chain step 7 to decide whether any correlation/AUC outcome has >= 3 independent studies
of one instrument against one comparator (effect-size-meta-analysis threshold). Standard library only.
Run: python3 -I analysis/synthesis/count_effect_groups.py
"""
import collections
import csv

STUDIES = "analysis/synthesis/studies_with_datasets.csv"
EFFECTS = "analysis/extraction/effects.csv"


def cls(c: str):
    c = c.lower()
    if "test-retest" in c or c == "none":
        return None
    if "visual field" in c or "mean deviation" in c or "hfa" in c or "microperimet" in c or "mp1" in c:
        return "visual field / perimetry"
    if "contrast" in c:
        return "contrast sensitivity"
    if "acuity" in c or c.startswith("va") or "bcva" in c or "logmar" in c or "etdrs" in c or "letters" in c:
        return "visual acuity"
    if "reading" in c or "mnread" in c:
        return "reading"
    if "referral" in c:
        return "clinician referral"
    return "questionnaire / other"


def main():
    st = {r["study_id"]: r for r in csv.DictReader(open(STUDIES, encoding="utf-8"))}
    cnt = collections.defaultdict(set)
    for r in csv.DictReader(open(EFFECTS, encoding="utf-8")):
        if r["outcome_type"] not in ("correlation", "spearman", "auc"):
            continue
        k = cls(r["comparator"])
        if k is None:
            continue
        cnt[(r["instrument"], k)].add(st.get(r["study_id"], {}).get("dataset_id", r["study_id"]))
    print("instrument | comparator class | independent datasets")
    for (i, k), d in sorted(cnt.items(), key=lambda t: (-len(t[1]), t[0])):
        print(f"{len(d)} | {i} | {k} | {sorted(d)}")
    print("max independent datasets in any cell =", max(len(d) for d in cnt.values()))


if __name__ == "__main__":
    main()
