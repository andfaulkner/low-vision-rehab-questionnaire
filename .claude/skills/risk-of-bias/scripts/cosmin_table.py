#!/usr/bin/env python3
"""Validate a COSMIN risk-of-bias CSV and apply the worst-score-counts rule.

Input: a CSV in the layout of assets/cosmin_template.csv (one row per study x
instrument x measurement property x standard, rated Very good / Adequate /
Doubtful / Inadequate, or NA when a standard does not apply).

Output (in --out-dir, default analysis/risk_of_bias/):
  cosmin_ratings.csv   one row per study x instrument x property with the overall
                       (worst-score-counts) rating and the standard that drove it
  cosmin_table.md      the same as a Markdown grid for the manuscript

Exits 1 on invalid ratings, unknown measurement properties, or a property with
no rated standard. Empty quotes/pages are warnings unless --strict.

Run with `python3 -I` because the CSV is data, not code.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import OrderedDict

RATINGS = ["Very good", "Adequate", "Doubtful", "Inadequate"]   # best to worst
RANK = {r: i for i, r in enumerate(RATINGS)}
PROPERTIES = [
    "PROM development", "Content validity", "Structural validity", "Internal consistency",
    "Cross-cultural validity", "Reliability", "Measurement error", "Criterion validity",
    "Hypotheses testing", "Responsiveness",
]
PROP_KEY = {p.casefold(): p for p in PROPERTIES}
PROP_KEY.update({
    "hypotheses testing for construct validity": "Hypotheses testing",
    "construct validity": "Hypotheses testing",
    "cross-cultural validity / measurement invariance": "Cross-cultural validity",
    "measurement invariance": "Cross-cultural validity",
})
REQUIRED = ["study_id", "instrument", "measurement_property", "standard_id", "rating", "support_quote", "page"]


def norm_rating(raw: str):
    key = raw.strip().casefold()
    if key in ("", "na", "n/a", "not applicable", "-"):
        return "NA"
    for r in RATINGS:
        if key == r.casefold():
            return r
    return None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="COSMIN CSV (layout of assets/cosmin_template.csv)")
    p.add_argument("--out-dir", default="analysis/risk_of_bias")
    p.add_argument("--prefix", default="cosmin")
    p.add_argument("--strict", action="store_true", help="treat empty quotes/pages as errors")
    p.add_argument("--check", action="store_true", help="validate only; write nothing")
    args = p.parse_args(argv)

    if not os.path.isfile(args.csv):
        print(f"ERROR: no such file: {args.csv}", file=sys.stderr)
        return 2
    errors, warnings = [], []
    with open(args.csv, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields = [f.strip() for f in (reader.fieldnames or [])]
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
    missing = [c for c in REQUIRED if c not in fields]
    if missing:
        print("ERROR: missing required column(s): " + ", ".join(missing), file=sys.stderr)
        return 1

    groups: OrderedDict[tuple, list] = OrderedDict()
    for i, r in enumerate(rows, start=2):
        sid, inst, prop_raw = r["study_id"], r["instrument"], r["measurement_property"]
        if not sid:
            errors.append(f"line {i}: empty study_id"); continue
        prop = PROP_KEY.get(" ".join(prop_raw.split()).casefold())
        if prop is None:
            errors.append(f"line {i} ({sid}): unknown measurement_property '{prop_raw}'; allowed: {', '.join(PROPERTIES)}")
            continue
        rating = norm_rating(r["rating"])
        if rating is None:
            errors.append(f"line {i} ({sid}/{prop} {r['standard_id']}): rating '{r['rating']}' is not one of "
                          + ", ".join(RATINGS) + " or NA")
            continue
        if rating != "NA":
            if not r["support_quote"]:
                (errors if args.strict else warnings).append(f"line {i} ({sid}/{prop} {r['standard_id']}): support_quote is empty")
            if not r["page"]:
                (errors if args.strict else warnings).append(f"line {i} ({sid}/{prop} {r['standard_id']}): page is empty")
        groups.setdefault((sid, inst, prop), []).append((r["standard_id"], rating))

    results = []
    for (sid, inst, prop), items in groups.items():
        rated = [(s, rt) for s, rt in items if rt != "NA"]
        if not rated:
            errors.append(f"{sid} / {inst} / {prop}: no standard was rated (all NA or blank)")
            continue
        worst = max(rated, key=lambda t: RANK[t[1]])
        driving = [s for s, rt in rated if rt == worst[1]]
        results.append({"study_id": sid, "instrument": inst, "measurement_property": prop,
                        "n_standards_rated": len(rated), "overall_rating": worst[1],
                        "worst_standards": "; ".join(driving)})

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} error(s); nothing written.", file=sys.stderr)
        return 1
    print(f"Validated {len(results)} study x instrument x property ratings ({len(warnings)} warning(s)).")
    if args.check:
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    base = os.path.join(args.out_dir, args.prefix)
    with open(base + "_ratings.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)

    # Markdown grid: rows = study/instrument, columns = properties that occur
    props = [p for p in PROPERTIES if any(r["measurement_property"] == p for r in results)]
    grid: OrderedDict[tuple, dict] = OrderedDict()
    for r in results:
        grid.setdefault((r["study_id"], r["instrument"]), {})[r["measurement_property"]] = r["overall_rating"]
    lines = ["# COSMIN risk-of-bias ratings (worst score counts per property)", "",
             f"Source CSV: `{args.csv}`. A property's rating is the worst rating among its standards "
             "(Mokkink et al. 2018). AI-drafted ratings are advisory until the reviewer confirms them; "
             "disclose AI assistance in Methods.", "",
             "| Study | Instrument | " + " | ".join(props) + " |",
             "|---|---|" + "|".join(["---"] * len(props)) + "|"]
    for (sid, inst), cells in grid.items():
        lines.append(f"| {sid} | {inst} | " + " | ".join(cells.get(p, "not assessed") for p in props) + " |")
    lines += ["", "## Driving standards", "", "| Study | Instrument | Property | Overall | Standards at that rating |", "|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['study_id']} | {r['instrument']} | {r['measurement_property']} | {r['overall_rating']} | {r['worst_standards']} |")
    with open(base + "_table.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", base + "_ratings.csv")
    print("wrote", base + "_table.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
