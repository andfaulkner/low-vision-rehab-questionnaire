#!/usr/bin/env python3
"""Validate extraction CSVs (studies, dta, effects, instruments) and report pooling readiness.

    python3 -I validate_extraction.py analysis/extraction
    python3 -I validate_extraction.py --dta /tmp/dta.csv --studies /tmp/studies.csv
    python3 -I validate_extraction.py analysis/extraction --report analysis/extraction/readiness.md

Checks: exact column sets (references/schema.md is the human-readable copy of the schema
below), allowed values, numeric ranges, impossible values (sens > 1, TP + FN != n_positive,
CI not bracketing the estimate), rounding-consistency of sens/spec against the counts,
duplicate rows, missing page citations, study_ids that do not exist in studies.csv or in
the Screening sheet, instruments never defined in instruments.csv. Then prints how many
studies contribute to each instrument x reference standard x threshold group and whether
that is enough to pool.

Exit status: 0 when there are no errors (warnings allowed), 1 when any error is found or a
file cannot be read.
"""

import argparse
import collections
import csv
import os
import re
import sys

NR = "NR"
NR_TOKENS = {"nr", "not reported", "n/a", "na"}

SCHEMA = {
    "studies": {
        "columns": ["study_id", "label", "year", "country", "setting", "design",
                    "n_enrolled", "n", "age_mean", "age_sd", "age_range",
                    "pct_female", "pct_glaucoma", "diagnosis_mix", "recruitment",
                    "instruments", "n_items", "administration_mode",
                    "time_to_administer_min", "language", "unit_of_analysis", "cohort",
                    "page", "notes"],
        "key": ["study_id"],
        "required": ["study_id", "label", "year", "design", "n", "page"],
        "int": ["study_id", "year", "n_enrolled", "n"],
        "num": ["age_mean", "age_sd", "pct_female", "pct_glaucoma", "time_to_administer_min"],
        "allowed": {
            "design": ["cross-sectional", "cohort", "case-control", "RCT", "pre-post",
                       "validation", "systematic review", "other"],
            "administration_mode": ["self", "interviewer", "telephone", "online", "mixed"],
            "unit_of_analysis": ["person", "eye"],
        },
        "range": {"year": (1900, 2100), "pct_female": (0, 100), "pct_glaucoma": (0, 100),
                  "age_mean": (18, 110), "n": (1, None), "n_enrolled": (1, None),
                  "time_to_administer_min": (0, None)},
    },
    "dta": {
        "columns": ["study_id", "label", "instrument", "item_text", "threshold", "reference_standard",
                    "ref_threshold", "ref_threshold_logmar", "unit", "subgroup", "n",
                    "n_positive", "prevalence", "TP", "FP", "FN", "TN", "sens", "spec",
                    "ppv", "npv", "sens_ci_low", "sens_ci_high", "spec_ci_low",
                    "spec_ci_high", "auc", "auc_ci_low", "auc_ci_high", "ci_level", "page",
                    "derivation", "notes"],
        "key": ["study_id", "instrument", "item_text", "threshold", "reference_standard",
                "ref_threshold", "unit", "subgroup"],
        "required": ["study_id", "instrument", "threshold", "reference_standard",
                     "ref_threshold", "unit", "page"],
        "int": ["study_id", "n", "n_positive", "TP", "FP", "FN", "TN"],
        "num": ["ref_threshold_logmar", "prevalence", "sens", "spec", "ppv", "npv",
                "sens_ci_low", "sens_ci_high", "spec_ci_low", "spec_ci_high", "auc",
                "auc_ci_low", "auc_ci_high", "ci_level"],
        "allowed": {
            "reference_standard": ["visual acuity", "visual field", "contrast sensitivity",
                                   "full questionnaire", "clinician judgement",
                                   "ophthalmic exam", "composite", "other"],
            "unit": ["person", "eye"],
        },
        "range": {"prevalence": (0, 1), "sens": (0, 1), "spec": (0, 1), "ppv": (0, 1),
                  "npv": (0, 1), "sens_ci_low": (0, 1), "sens_ci_high": (0, 1),
                  "spec_ci_low": (0, 1), "spec_ci_high": (0, 1), "auc": (0, 1),
                  "auc_ci_low": (0, 1), "auc_ci_high": (0, 1), "ci_level": (50, 99.9),
                  "ref_threshold_logmar": (-0.3, 3), "n": (1, None)},
    },
    "effects": {
        "columns": ["study_id", "label", "outcome_type", "measure", "instrument", "comparator",
                    "estimate", "ci_low", "ci_high", "se", "sd", "events", "n", "n_pos",
                    "n_neg", "m1", "sd1", "n1", "m2", "sd2", "n2", "unit", "subgroup",
                    "p_value", "page", "derivation", "notes"],
        "key": ["study_id", "outcome_type", "measure", "instrument", "comparator", "unit",
                "subgroup"],
        "required": ["study_id", "label", "outcome_type", "measure", "instrument",
                     "comparator", "estimate", "page"],
        "int": ["study_id", "events", "n", "n_pos", "n_neg", "n1", "n2"],
        "num": ["estimate", "ci_low", "ci_high", "se", "sd", "m1", "sd1", "m2", "sd2", "p_value"],
        "allowed": {
            "outcome_type": ["correlation", "spearman", "auc", "proportion", "mean", "md",
                             "generic", "logratio"],
            "unit": ["person", "eye"],
        },
        "range": {"se": (0, None), "sd": (0, None), "sd1": (0, None), "sd2": (0, None),
                  "p_value": (0, 1), "n": (1, None), "n1": (1, None), "n2": (1, None),
                  "n_pos": (1, None), "n_neg": (1, None)},
    },
    "instruments": {
        "columns": ["instrument", "full_name", "n_items", "domains", "response_scale",
                    "scoring", "validation_method", "languages", "time_to_administer_min",
                    "target_population", "source_refs", "notes"],
        "key": ["instrument"],
        "required": ["instrument", "full_name", "n_items", "source_refs"],
        "int": ["n_items"],
        "num": ["time_to_administer_min"],
        "allowed": {},
        "range": {"n_items": (1, None), "time_to_administer_min": (0, None)},
        "tokens": {"validation_method": ["Rasch", "IRT", "CTT", "factor analysis",
                                         "test-retest", "internal consistency",
                                         "criterion validity", "ROC", "none reported"]},
    },
}
OUTCOME_RANGE = {"correlation": (-1, 1), "spearman": (-1, 1), "auc": (0, 1), "proportion": (0, 1)}


class Report:
    def __init__(self):
        self.items = []  # (level, file, row, message)

    def error(self, f, row, msg):
        self.items.append(("ERROR", f, row, msg))

    def warn(self, f, row, msg):
        self.items.append(("WARN", f, row, msg))

    def info(self, f, row, msg):
        self.items.append(("INFO", f, row, msg))

    def count(self, level):
        return sum(1 for i in self.items if i[0] == level)


def is_nr(v):
    return v is not None and v.strip().lower() in NR_TOKENS


def blank(v):
    return v is None or v.strip() == ""


def num(v):
    """float or None (blank / NR); raises ValueError on garbage."""
    if blank(v) or is_nr(v):
        return None
    s = v.strip().rstrip("%").replace(",", "")
    return float(s)


def decimals_of(v):
    s = v.strip().rstrip("%")
    return len(s.split(".")[1]) if "." in s else 0


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        r = csv.DictReader(fh)
        return r.fieldnames or [], list(r)


def norm_key(values):
    return tuple(re.sub(r"\s+", " ", (v or "").strip().lower()) for v in values)


def check_file(kind, path, rep, ctx):
    spec = SCHEMA[kind]
    try:
        fields, rows = read_csv(path)
    except OSError as e:
        rep.error(kind, 0, f"cannot read {path}: {e}")
        return []
    fields = [f.strip() for f in fields]
    missing = [c for c in spec["columns"] if c not in fields]
    extra = [c for c in fields if c not in spec["columns"]]
    if missing:
        rep.error(kind, 1, "missing columns: " + ", ".join(missing))
    if extra:
        rep.warn(kind, 1, "extra columns (ignored by downstream skills): " + ", ".join(extra))
    seen = {}
    for i, row in enumerate(rows, start=2):
        row = {k.strip(): (v if v is not None else "") for k, v in row.items() if k is not None}
        # required
        for c in spec["required"]:
            if c in fields and blank(row.get(c)):
                rep.error(kind, i, f"{c} is empty (write NR if the paper does not report it)")
        # page citation
        if "page" in fields:
            pg = row.get("page", "")
            if blank(pg) or is_nr(pg) or not re.search(r"\d", pg):
                rep.error(kind, i, "missing page citation (every value must be traceable to a [page N])")
        # numbers
        parsed = {}
        for c in spec["int"] + spec["num"]:
            if c not in fields:
                continue
            v = row.get(c, "")
            try:
                x = num(v)
            except ValueError:
                rep.error(kind, i, f"{c}={v!r} is not a number, blank or NR")
                continue
            parsed[c] = x
            if x is None:
                continue
            if c in spec["int"] and abs(x - round(x)) > 1e-9:
                rep.error(kind, i, f"{c}={v!r} must be an integer")
            lo, hi = spec["range"].get(c, (None, None))
            if (lo is not None and x < lo) or (hi is not None and x > hi):
                rep.error(kind, i, f"{c}={v!r} outside allowed range [{lo}, {hi}]")
        # allowed values
        for c, allowed in spec["allowed"].items():
            v = row.get(c, "")
            if c in fields and not blank(v) and not is_nr(v) and v.strip() not in allowed:
                rep.error(kind, i, f"{c}={v!r} not in allowed values {allowed}")
        for c, allowed in spec.get("tokens", {}).items():
            v = row.get(c, "")
            if c in fields and not blank(v) and not is_nr(v):
                bad = [t.strip() for t in v.split(";") if t.strip() and t.strip() not in allowed]
                if bad:
                    rep.warn(kind, i, f"{c} has tokens outside the recommended list: {bad}")
        # duplicates
        key = norm_key(row.get(c, "") for c in spec["key"])
        if key in seen:
            rep.error(kind, i, f"duplicate of row {seen[key]} on key {spec['key']} (same study x test x threshold x reference standard; use subgroup or merge)")
        else:
            seen[key] = i
        # cross-file references
        sid = parsed.get("study_id")
        if sid is not None and kind != "studies":
            if ctx.get("study_ids") is not None and int(sid) not in ctx["study_ids"]:
                rep.error(kind, i, f"study_id {int(sid)} has no row in studies.csv")
        if sid is not None and ctx.get("screening"):
            scr = ctx["screening"].get(int(sid))
            if scr is None:
                rep.warn(kind, i, f"study_id {int(sid)} is not an ID in the Screening sheet")
            elif kind == "studies":
                surname = re.split(r"[\s,]+", row.get("label", "").strip())[0].lower()
                if surname and surname not in scr.lower():
                    rep.warn(kind, i, f"label {row.get('label')!r} does not match Screening authors {scr[:40]!r} for ID {int(sid)}")
        for c in ("instrument", "instruments"):
            if c in fields and ctx.get("instruments") is not None:
                for name in re.split(r"\s*;\s*", row.get(c, "").strip()):
                    if name and not is_nr(name) and name.lower() not in ctx["instruments"]:
                        rep.warn(kind, i, f"instrument {name!r} is not defined in instruments.csv")
        # kind-specific
        if kind == "dta":
            check_dta_row(row, parsed, rep, i)
        if kind == "effects":
            check_effects_row(row, parsed, rep, i)
        if kind == "studies":
            ne, na = parsed.get("n_enrolled"), parsed.get("n")
            if ne is not None and na is not None and na > ne:
                rep.error(kind, i, f"n {int(na)} > n_enrolled {int(ne)}")
        row["_row"] = i
        rows[i - 2] = row
    return rows


def within(reported_str, computed):
    tol = 0.5 * 10 ** (-decimals_of(reported_str)) + 1e-9
    return abs(num(reported_str) - computed) <= tol


def check_dta_row(row, p, rep, i):
    tp, fp, fn, tn = (p.get(k) for k in ("TP", "FP", "FN", "TN"))
    n, npos, prev = p.get("n"), p.get("n_positive"), p.get("prevalence")
    sens, spec = p.get("sens"), p.get("spec")
    if tp is not None and fn is not None and npos is not None and tp + fn != npos:
        rep.error("dta", i, f"TP + FN = {int(tp + fn)} but n_positive = {int(npos)}")
    if None not in (tp, fp, fn, tn):
        if n is not None and tp + fp + fn + tn != n:
            rep.error("dta", i, f"TP+FP+FN+TN = {int(tp + fp + fn + tn)} but n = {int(n)}")
        if blank(row.get("derivation")):
            rep.warn("dta", i, "2x2 counts present but derivation is empty; write 'reported directly (Table N)' or how they were derived")
    if tp is not None and fn is not None and sens is not None and tp + fn > 0:
        if not within(row["sens"], tp / (tp + fn)):
            rep.error("dta", i, f"sens {row['sens']} does not match TP/(TP+FN) = {tp / (tp + fn):.4f}")
    if tn is not None and fp is not None and spec is not None and tn + fp > 0:
        if not within(row["spec"], tn / (tn + fp)):
            rep.error("dta", i, f"spec {row['spec']} does not match TN/(TN+FP) = {tn / (tn + fp):.4f}")
    if prev is not None and npos is not None and n:
        if not within(row["prevalence"], npos / n):
            rep.error("dta", i, f"prevalence {row['prevalence']} does not match n_positive/n = {npos / n:.4f}")
    if npos is not None and n is not None and npos > n:
        rep.error("dta", i, f"n_positive {int(npos)} > n {int(n)}")
    for est, lo, hi in (("sens", "sens_ci_low", "sens_ci_high"), ("spec", "spec_ci_low", "spec_ci_high"),
                        ("auc", "auc_ci_low", "auc_ci_high")):
        e, l, h = p.get(est), p.get(lo), p.get(hi)
        if (l is None) != (h is None):
            rep.error("dta", i, f"{lo}/{hi}: give both limits or neither")
        if e is not None and l is not None and h is not None and not (l - 1e-9 <= e <= h + 1e-9):
            rep.error("dta", i, f"{est} {e} is not inside its CI [{l}, {h}]")
    auc = p.get("auc")
    if auc is not None and sens is not None and spec is not None and abs(auc - (sens + spec) / 2) < 0.006:
        rep.info("dta", i, "auc equals (sens+spec)/2: a single-threshold 'AUC', not a ROC area; note it and do not pool it with true ROC AUCs")
    if blank(row.get("item_text")) and not is_nr(row.get("item_text", "")):
        rep.warn("dta", i, "item_text empty: give the verbatim question for single items, or NR for a total score")
    if blank(row.get("ref_threshold_logmar")) and row.get("reference_standard", "").strip() == "visual acuity":
        rep.warn("dta", i, "ref_threshold_logmar empty for a visual acuity reference standard (see pitfalls.md conversion table)")


def check_effects_row(row, p, rep, i):
    ot = row.get("outcome_type", "").strip()
    e, l, h = p.get("estimate"), p.get("ci_low"), p.get("ci_high")
    rng = OUTCOME_RANGE.get(ot)
    if rng and e is not None and not (rng[0] <= e <= rng[1]):
        rep.error("effects", i, f"estimate {e} outside the range {rng} for outcome_type {ot}")
    if (l is None) != (h is None):
        rep.error("effects", i, "ci_low/ci_high: give both limits or neither")
    if e is not None and l is not None and h is not None and not (l - 1e-9 <= e <= h + 1e-9):
        rep.error("effects", i, f"estimate {e} is not inside its CI [{l}, {h}]")
    if ot == "proportion" and p.get("events") is not None and p.get("n") and e is not None:
        if not within(row["estimate"], p["events"] / p["n"]):
            rep.error("effects", i, f"estimate {row['estimate']} does not match events/n = {p['events'] / p['n']:.4f}")
    if ot in ("correlation", "spearman") and p.get("n") is None and p.get("se") is None and l is None:
        rep.error("effects", i, f"{ot} needs n (pairs) or se or a CI to be poolable")
    if ot == "auc" and p.get("se") is None and l is None and (p.get("n_pos") is None or p.get("n_neg") is None):
        rep.warn("effects", i, "auc has no se, CI or n_pos/n_neg: not poolable (Hanley-McNeil needs group sizes)")
    if ot == "proportion" and p.get("events") is None and p.get("n") is None:
        rep.error("effects", i, "proportion needs events and n")
    if ot == "md" and p.get("se") is None and l is None and any(p.get(c) is None for c in ("m1", "sd1", "n1", "m2", "sd2", "n2")):
        rep.warn("effects", i, "md has neither se/CI nor m1 sd1 n1 m2 sd2 n2: not poolable")


def readiness(dta_rows, eff_rows, studies_rows, min_k):
    out = ["# Pooling readiness", ""]
    if studies_rows is not None:
        out.append(f"studies.csv: {len(studies_rows)} studies")
    if dta_rows is not None:
        out += ["", "## Diagnostic accuracy (dta.csv)", "",
                "| instrument | reference standard | ref threshold | unit | studies | rows | complete 2x2 | verdict |",
                "|---|---|---|---|---|---|---|---|"]
        groups = collections.OrderedDict()
        for r in dta_rows:
            g = (r.get("instrument", ""), r.get("reference_standard", ""), r.get("ref_threshold", ""), r.get("unit", ""))
            groups.setdefault(g, []).append(r)
        for g, rows in sorted(groups.items()):
            studies = {r["study_id"] for r in rows}
            full = sum(1 for r in rows if all(not blank(r.get(c)) and not is_nr(r.get(c)) for c in ("TP", "FP", "FN", "TN")))
            k = len(studies)
            if k >= min_k and full >= min_k:
                verdict = f"bivariate model possible (k={k} >= {min_k}); check thresholds are comparable"
            elif k >= 2:
                verdict = f"too few for bivariate (k={k}); report study-level estimates, no pooled point estimate" + ("" if full == len(rows) else f"; {len(rows) - full} rows lack a full 2x2")
            else:
                verdict = "single study: narrative only"
            out.append(f"| {g[0]} | {g[1]} | {g[2]} | {g[3]} | {k} | {len(rows)} | {full} | {verdict} |")
        multi = collections.Counter((r["study_id"], r.get("instrument", ""), r.get("reference_standard", "")) for r in dta_rows)
        dup = [k for k, v in multi.items() if v > 1]
        if dup:
            out += ["", f"{len(dup)} study x instrument x reference-standard combinations contribute more than one row "
                        "(several thresholds, items or subgroups). Pool one row per study per group, or use a multiple-threshold model; see dta-meta-analysis."]
    if eff_rows is not None:
        out += ["", "## Other effect sizes (effects.csv)", "",
                "| outcome | instrument | comparator | studies | rows | verdict |", "|---|---|---|---|---|---|"]
        groups = collections.OrderedDict()
        for r in eff_rows:
            g = (r.get("outcome_type", ""), r.get("instrument", ""), r.get("comparator", ""))
            groups.setdefault(g, []).append(r)
        for g, rows in sorted(groups.items()):
            k = len({r["study_id"] for r in rows})
            with_var = sum(1 for r in rows if any(not blank(r.get(c)) and not is_nr(r.get(c)) for c in ("se", "ci_low", "n")))
            if k >= 3 and with_var == len(rows):
                verdict = f"random-effects pooling possible with caution (k={k})"
            elif k >= 2:
                verdict = f"k={k}: describe, do not pool" + ("" if with_var == len(rows) else f"; {len(rows) - with_var} rows lack n/se/CI")
            else:
                verdict = "single study: narrative only"
            out.append(f"| {g[0]} | {g[1]} | {g[2]} | {k} | {len(rows)} | {verdict} |")
    out += ["", f"Bivariate verdicts use k >= {min_k} studies with a complete 2x2 (Takwoingi et al. 2017 recommend at least 4 for a stable bivariate fit; even then, heterogeneous thresholds argue against a pooled point estimate)."]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", nargs="?", default="analysis/extraction", help="folder holding studies.csv, dta.csv, effects.csv, instruments.csv (default analysis/extraction)")
    for k in SCHEMA:
        ap.add_argument(f"--{k}", metavar="CSV", help=f"explicit path to {k}.csv")
    ap.add_argument("--screening", metavar="CSV", default="data/LVR_screening_sheet_2_Screening.csv", help="Screening export used to check study_ids (default data/LVR_screening_sheet_2_Screening.csv; '' to skip)")
    ap.add_argument("--report", metavar="MD", help="also write the readiness report to this markdown file")
    ap.add_argument("--min-studies", type=int, default=4, help="studies needed before a bivariate fit is called possible (default 4)")
    ap.add_argument("--quiet-info", action="store_true", help="hide INFO lines")
    a = ap.parse_args(argv)

    paths = {k: getattr(a, k) or os.path.join(a.dir, f"{k}.csv") for k in SCHEMA}
    present = {k: p for k, p in paths.items() if os.path.exists(p)}
    if not present:
        sys.exit(f"error: no extraction CSVs found (looked for {', '.join(paths.values())})")
    rep = Report()
    for k, p in paths.items():
        if k not in present:
            rep.warn(k, 0, f"{p} not found; skipped")
    ctx = {}
    if a.screening and os.path.exists(a.screening):
        try:
            with open(a.screening, newline="", encoding="utf-8-sig") as fh:
                lines = fh.read().splitlines(True)
            if lines and "," not in lines[0]:
                lines = lines[1:]  # the exports start with a title line holding the sheet name
            srows = list(csv.DictReader(lines))
            ctx["screening"] = {int(r["ID"]): r.get("Authors", "") for r in srows if (r.get("ID") or "").strip().isdigit()}
        except (OSError, KeyError) as e:
            rep.warn("screening", 0, f"could not read {a.screening}: {e}")
    elif a.screening:
        rep.warn("screening", 0, f"{a.screening} not found; study_ids not checked against the Screening sheet")

    data = {}
    order = ["instruments", "studies", "dta", "effects"]  # references resolve left to right
    for k in order:
        if k not in present:
            continue
        rows = check_file(k, present[k], rep, ctx)
        data[k] = rows
        if k == "instruments":
            ctx["instruments"] = {r.get("instrument", "").strip().lower() for r in rows}
        if k == "studies":
            ids = set()
            for r in rows:
                try:
                    ids.add(int(float(r.get("study_id", ""))))
                except ValueError:
                    pass
            ctx["study_ids"] = ids

    for level, f, row, msg in rep.items:
        if level == "INFO" and a.quiet_info:
            continue
        print(f"{level:5} {f}.csv row {row}: {msg}" if row else f"{level:5} {f}: {msg}")
    print(f"\n{rep.count('ERROR')} errors, {rep.count('WARN')} warnings, {rep.count('INFO')} notes\n")
    md = readiness(data.get("dta"), data.get("effects"), data.get("studies"), a.min_studies)
    print(md)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
        print(f"\nreadiness report written to {a.report}")
    return 1 if rep.count("ERROR") else 0


if __name__ == "__main__":
    sys.exit(main())
