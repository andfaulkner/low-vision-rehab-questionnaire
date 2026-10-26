#!/usr/bin/env python3
"""Build the manuscript's instrument comparison table and feasibility table.

Merges, in this order of precedence (later wins when the cell is non-empty and not NR):
  1. the skill's assets/instrument_catalogue.csv (AI-compiled facts, verified = no by default)
  2. --instruments  analysis/extraction/instruments.csv from the data-extraction skill
                    (facts extracted from the included studies, with page cites)
  3. --feasibility  a filled copy of assets/feasibility_template.csv (feasibility table only)
and joins
  --studies  analysis/extraction/studies.csv  -> k included studies and their labels per instrument
  --ratings  analysis/instruments/summary_of_findings.csv from rate_properties.py
             -> one compact "measurement properties" cell per instrument

Outputs (in --out-dir, default paper/tables/): comparison_table.md/.csv and
feasibility_table.md/.csv. Instruments whose catalogue row is not `verified: yes`
are marked with a dagger in the table and listed in a footnote, so unverified
AI-compiled facts never pass silently into the manuscript.

`--for glaucoma` adds the field/contrast coverage and glaucoma-specific columns to
both tables: field and contrast loss coexist with preserved acuity in glaucoma, so an
acuity-only screen can miss the patients the clinic most wants to find.

Run with `python3 -I`. Standard library only.

Examples
  python3 -I instrument_table.py --studies analysis/extraction/studies.csv \\
      --instruments analysis/extraction/instruments.csv \\
      --ratings analysis/instruments/summary_of_findings.csv --for glaucoma
  python3 -I instrument_table.py --columns instrument,n_items,time_to_administer_min,licence --included-only
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CATALOGUE = os.path.join(HERE, "..", "assets", "instrument_catalogue.csv")

LABELS = {
    "instrument": "Instrument", "full_name": "Full name", "n_items": "Items", "domains": "Domains",
    "response_scale": "Response scale", "scoring": "Scoring", "validation_method": "Validation",
    "languages": "Languages", "time_to_administer_min": "Minutes", "administration_mode": "Mode",
    "reading_level": "Reading level", "target_population": "Target population",
    "development_citation": "Development paper", "development_doi": "DOI", "development_pmid": "PMID",
    "rasch_validated": "Rasch/IRT", "licence": "Licence", "scoring_burden": "Scoring burden",
    "field_contrast_coverage": "Field/contrast coverage", "glaucoma_specific": "Glaucoma-specific",
    "short_forms": "Short forms", "k_studies": "Included studies (k)", "study_labels": "Studies",
    "properties": "Measurement properties (COSMIN; certainty)", "equipment": "Equipment",
    "technician_ready": "Technician-ready", "notes": "Notes", "source_refs": "Sources", "verified": "Verified",
}
DEFAULT_COMPARISON = ["instrument", "n_items", "domains", "scoring", "administration_mode",
                      "time_to_administer_min", "languages", "rasch_validated", "licence",
                      "k_studies", "properties"]
DEFAULT_FEASIBILITY = ["instrument", "n_items", "time_to_administer_min", "administration_mode",
                       "reading_level", "languages", "licence", "scoring_burden", "equipment",
                       "technician_ready"]
GLAUCOMA_COLS = ["field_contrast_coverage", "glaucoma_specific"]
PROP_ABBR = {"Structural validity": "SV", "Internal consistency": "IC", "Cross-cultural validity": "CCV",
             "Reliability": "Rel", "Measurement error": "ME", "Criterion validity": "CV",
             "Hypotheses testing": "HT", "Responsiveness": "Resp"}
CERT_ABBR = {"High": "high", "Moderate": "mod", "Low": "low", "Very low": "very low"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").casefold())


def read_csv(path: str) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh, restkey="_extra")
        fields = [f.strip() for f in (rd.fieldnames or [])]
        rows = []
        for i, r in enumerate(rd, start=2):
            if r.get("_extra"):
                sys.exit(f"ERROR: {path} line {i} has {len(fields) + len(r['_extra'])} fields but the header has {len(fields)} (unquoted comma?)")
            rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items() if k != "_extra"})
    return fields, rows


def is_blank(v: str) -> bool:
    return (v or "").strip() == "" or (v or "").strip().upper() in ("NR", "NA", "N/A")


def md(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def write_md(path: str, title: str, cols: list[str], rows: list[dict], notes: list[str]) -> None:
    lines = [f"# {title}", ""]
    lines.append("| " + " | ".join(LABELS.get(c, c) for c in cols) + " |")
    lines.append("|" + "---|" * len(cols))
    for r in rows:
        lines.append("| " + " | ".join(md(r.get(c, "")) for c in cols) + " |")
    if notes:
        lines += [""] + notes
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_csv(path: str, cols: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--catalogue", default=DEFAULT_CATALOGUE, help="instrument catalogue CSV (default: the skill's assets/instrument_catalogue.csv)")
    p.add_argument("--instruments", help="data-extraction instruments.csv (overrides catalogue cells)")
    p.add_argument("--studies", help="data-extraction studies.csv (counts included studies per instrument)")
    p.add_argument("--ratings", help="summary_of_findings.csv from rate_properties.py")
    p.add_argument("--feasibility", help="filled feasibility CSV (layout of assets/feasibility_template.csv)")
    p.add_argument("--columns", help="comma-separated columns for the comparison table (default: " + ",".join(DEFAULT_COMPARISON) + ")")
    p.add_argument("--feasibility-columns", help="comma-separated columns for the feasibility table (default: " + ",".join(DEFAULT_FEASIBILITY) + ")")
    p.add_argument("--for", dest="for_", choices=["glaucoma"], help="'glaucoma' adds field/contrast coverage and glaucoma-specific columns")
    p.add_argument("--only", action="append", default=[], metavar="INSTRUMENT", help="restrict to these instruments (repeatable)")
    p.add_argument("--included-only", action="store_true", help="keep only instruments that appear in --studies or --instruments")
    p.add_argument("--out-dir", default="paper/tables")
    p.add_argument("--prefix", default="", help="filename prefix, e.g. 'glaucoma_'")
    p.add_argument("--check", action="store_true", help="validate inputs and print the merged rows; write nothing")
    args = p.parse_args(argv)

    for path in [args.catalogue, args.instruments, args.studies, args.ratings, args.feasibility]:
        if path and not os.path.isfile(path):
            print(f"ERROR: no such file: {path}", file=sys.stderr)
            return 2

    cfields, crows = read_csv(args.catalogue)
    if "instrument" not in cfields:
        print("ERROR: catalogue lacks an 'instrument' column", file=sys.stderr)
        return 1
    merged: "OrderedDict[str, dict]" = OrderedDict()
    for r in crows:
        if not r["instrument"]:
            continue
        key = norm(r["instrument"])
        if key in merged:
            print(f"ERROR: duplicate catalogue instrument '{r['instrument']}'", file=sys.stderr)
            return 1
        r.setdefault("verified", "no")
        r["_source"] = "catalogue"
        merged[key] = dict(r)

    overridden = []
    if args.instruments:
        ifields, irows = read_csv(args.instruments)
        if "instrument" not in ifields:
            print("ERROR: --instruments lacks an 'instrument' column", file=sys.stderr)
            return 1
        for r in irows:
            key = norm(r["instrument"])
            if key not in merged:
                merged[key] = {"instrument": r["instrument"], "verified": "extracted (not in catalogue)", "_source": "instruments.csv"}
            tgt = merged[key]
            for c, v in r.items():
                if c == "instrument" or is_blank(v):
                    continue
                if not is_blank(tgt.get(c, "")) and tgt.get(c) != v:
                    overridden.append((r["instrument"], c, tgt.get(c), v))
                tgt[c] = v
            if tgt.get("verified", "no").casefold() == "no":
                tgt["verified"] = "partial (extracted cells from included studies; rest unverified)"

    if args.feasibility:
        ffields, frows = read_csv(args.feasibility)
        for r in frows:
            key = norm(r["instrument"])
            if key not in merged:
                merged[key] = {"instrument": r["instrument"], "verified": r.get("verified", "no"), "_source": "feasibility.csv"}
            for c, v in r.items():
                if c in ("instrument",) or is_blank(v):
                    continue
                if c == "verified":
                    merged[key]["verified"] = v
                    continue
                merged[key][c] = v

    # studies per instrument
    for m in merged.values():
        m["k_studies"] = "0"
        m["study_labels"] = ""
    if args.studies:
        sfields, srows = read_csv(args.studies)
        if "instruments" not in sfields:
            print("ERROR: --studies lacks an 'instruments' column", file=sys.stderr)
            return 1
        unknown = set()
        per: dict[str, list[str]] = {}
        for s in srows:
            for name in [x.strip() for x in re.split(r";", s.get("instruments", "")) if x.strip()]:
                key = norm(name)
                if key not in merged:
                    unknown.add(name)
                    continue
                per.setdefault(key, []).append(s.get("label") or s.get("study_id", ""))
        for key, labels in per.items():
            merged[key]["k_studies"] = str(len(labels))
            merged[key]["study_labels"] = "; ".join(labels)
        if unknown:
            print("WARNING: instruments named in --studies but absent from the catalogue and --instruments: " + "; ".join(sorted(unknown)), file=sys.stderr)

    # ratings per instrument
    for m in merged.values():
        m["properties"] = ""
    if args.ratings:
        rfields, rrows = read_csv(args.ratings)
        need = ["instrument", "property", "summary_rating", "quality_of_evidence"]
        miss = [c for c in need if c not in rfields]
        if miss:
            print("ERROR: --ratings lacks column(s): " + ", ".join(miss), file=sys.stderr)
            return 1
        cells: dict[str, list[str]] = {}
        for r in rrows:
            key = norm(r["instrument"])
            if key not in merged:
                print(f"WARNING: rated instrument '{r['instrument']}' is not in the catalogue or --instruments; adding a bare row", file=sys.stderr)
                merged[key] = {"instrument": r["instrument"], "verified": "no", "_source": "ratings", "k_studies": "", "study_labels": "", "properties": ""}
            abbr = PROP_ABBR.get(r["property"], r["property"])
            cert = r["quality_of_evidence"]
            cert_s = next((v for k, v in CERT_ABBR.items() if cert.startswith(k)), "n/g")
            if "RoB not applied" in cert:
                cert_s += ", no RoB"
            kk = f", k={r['k']}" if r.get("k") else ""
            cells.setdefault(key, []).append(f"{abbr} {r['summary_rating']} ({cert_s}{kk})")
        for key, parts in cells.items():
            merged[key]["properties"] = "; ".join(parts)

    rows = list(merged.values())
    if args.only:
        wanted = {norm(x) for x in args.only}
        rows = [r for r in rows if norm(r["instrument"]) in wanted]
        missing = wanted - {norm(r["instrument"]) for r in rows}
        if missing:
            print("WARNING: --only names not found: " + ", ".join(sorted(missing)), file=sys.stderr)
    if args.included_only:
        rows = [r for r in rows if r.get("k_studies") not in ("", "0") or r.get("_source") == "instruments.csv"]

    comp_cols = [c.strip() for c in (args.columns.split(",") if args.columns else DEFAULT_COMPARISON) if c.strip()]
    feas_cols = [c.strip() for c in (args.feasibility_columns.split(",") if args.feasibility_columns else DEFAULT_FEASIBILITY) if c.strip()]
    if args.for_ == "glaucoma":
        for c in GLAUCOMA_COLS:
            if c not in comp_cols:
                comp_cols.append(c)
            if c not in feas_cols:
                feas_cols.insert(min(len(feas_cols), 9), c)

    # dagger for unverified rows
    daggered = []
    out_rows = []
    for r in rows:
        rr = dict(r)
        v = (rr.get("verified") or "no").casefold()
        if not v.startswith("yes"):
            rr["instrument"] = rr["instrument"] + " \u2020"
            daggered.append(f"{r['instrument']} ({rr.get('verified') or 'no'}" + (f"; uncertain: {r['uncertain_fields']}" if r.get("uncertain_fields") else "") + ")")
        for c in comp_cols + feas_cols:
            rr.setdefault(c, "")
            if rr[c] == "":
                rr[c] = "NR"
        out_rows.append(rr)

    if args.check:
        for r in out_rows:
            print(" | ".join(f"{c}={r.get(c, '')}" for c in comp_cols))
        print(f"OK: {len(out_rows)} instruments; {len(daggered)} unverified; {len(overridden)} catalogue cells overridden by --instruments")
        return 0

    notes = []
    if daggered:
        notes.append("\u2020 Catalogue facts for this instrument are not yet verified against the development paper (AI-compiled; `verified` column): " + "; ".join(daggered) + ".")
    if args.ratings:
        notes.append("Measurement properties: COSMIN summary rating per property (+ sufficient, - insufficient, ? indeterminate, +- inconsistent) with the modified-GRADE certainty in brackets (high/mod/low/very low; n/g = not graded because indeterminate) and k = number of contributing studies. SV structural validity, IC internal consistency, CCV cross-cultural validity, Rel reliability, ME measurement error, CV criterion validity, HT hypotheses testing, Resp responsiveness.")
    if args.for_ == "glaucoma":
        notes.append("Field/contrast coverage: whether the instrument has items that respond to visual-field or contrast-sensitivity loss. In glaucoma these losses coexist with preserved acuity, so an acuity-only screen can miss the patients most in need of rehabilitation.")
    notes.append("Facts extracted from included studies carry page cites in analysis/extraction/instruments.csv; AI assistance in compiling this table must be disclosed in Methods and every cell confirmed by the reviewer before publication.")

    os.makedirs(args.out_dir, exist_ok=True)
    pre = args.prefix
    paths = [os.path.join(args.out_dir, pre + "comparison_table.md"), os.path.join(args.out_dir, pre + "comparison_table.csv"),
             os.path.join(args.out_dir, pre + "feasibility_table.md"), os.path.join(args.out_dir, pre + "feasibility_table.csv")]
    write_md(paths[0], "Instrument comparison", comp_cols, out_rows, notes)
    write_csv(paths[1], comp_cols, out_rows)
    feas_notes = [n for n in notes if not n.startswith("Measurement properties")]
    write_md(paths[2], "Feasibility for a technician work-up", feas_cols, out_rows, feas_notes)
    write_csv(paths[3], feas_cols, out_rows)
    print(f"{len(out_rows)} instruments; {len(daggered)} marked unverified; {len(overridden)} catalogue cells overridden by extracted values")
    for inst, c, old, new in overridden:
        print(f"  override {inst}.{c}: catalogue '{old[:40]}' -> extracted '{new[:40]}'")
    print("Wrote: " + ", ".join(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
