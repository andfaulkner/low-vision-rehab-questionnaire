"""Align instrument names across feasibility.csv, property_results.csv and a copy of cosmin_ratings.csv
to the spellings used in analysis/extraction/instruments.csv, so instrument_table.py merges them
into one row per instrument (chain step 7). Run: python3 -I analysis/instruments/align_names.py
"""
import csv

FEAS = "analysis/instruments/feasibility.csv"
PROP = "analysis/instruments/property_results.csv"
ROB_IN = "analysis/risk_of_bias/cosmin_ratings.csv"
ROB_OUT = "analysis/instruments/cosmin_ratings_aligned.csv"

REN_FEAS = {
    "VIRFQ (visual impairment risk-for-falls questions)": "VIRFQ",
    "Self-reported mobility questionnaire (Bibby 2007)": "self-reported mobility questionnaire",
}
REN_RATINGS = {
    "SLVQOL (Spanish LVQOL)": "SLVQOL",
    "Sumi visual disability questionnaire": "Sumi revised visual disability questionnaire",
    "VA LV VFQ-48 (Italian version)": "VA LV VFQ-48",
}


def main():
    rows = list(csv.reader(open(FEAS, encoding="utf-8")))
    for r in rows[1:]:
        r[0] = REN_FEAS.get(r[0], r[0])
    csv.writer(open(FEAS, "w", newline="", encoding="utf-8")).writerows(rows)

    rr = list(csv.DictReader(open(ROB_IN, encoding="utf-8")))
    with open(ROB_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0].keys()))
        w.writeheader()
        for r in rr:
            r["instrument"] = REN_RATINGS.get(r["instrument"], r["instrument"])
            w.writerow(r)

    pr = list(csv.reader(open(PROP, encoding="utf-8")))
    hdr = pr[0]
    ci, ni = hdr.index("instrument"), hdr.index("notes")
    for r in pr[1:]:
        if r[ci] == "VA LV VFQ-48 (Italian version)" and not r[ni].startswith("Italian version"):
            r[ni] = "Italian version. " + r[ni]
        r[ci] = REN_RATINGS.get(r[ci], r[ci])
    csv.writer(open(PROP, "w", newline="", encoding="utf-8")).writerows(pr)
    print("aligned")


if __name__ == "__main__":
    main()
