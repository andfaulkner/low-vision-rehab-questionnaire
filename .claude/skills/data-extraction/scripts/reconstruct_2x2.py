#!/usr/bin/env python3
"""Reconstruct a diagnostic 2x2 table from whatever a paper reports.

Single case (CLI flags):
    python3 -I reconstruct_2x2.py --n 385 --n-positive 264 --sens 0.89 --spec 0.81
    python3 -I reconstruct_2x2.py --tp 235 --fp 23 --fn 29 --tn 98
    python3 -I reconstruct_2x2.py --n 200 --sens 0.80 --spec 0.90 --ppv 0.667
    python3 -I reconstruct_2x2.py --sens 0.60 --sens-ci 0.51,0.69      # estimates n_positive from the CI

Whole extraction file (fills blank / NR cells, never overwrites a reported value):
    python3 -I reconstruct_2x2.py --csv analysis/extraction/dta.csv --out /tmp/dta_filled.csv
    python3 -I reconstruct_2x2.py --csv analysis/extraction/dta.csv --in-place
    python3 -I reconstruct_2x2.py --csv analysis/extraction/dta.csv --dry-run

Any sufficient subset of n, n_positive, n_negative, prevalence, sens, spec, ppv, npv,
TP, FP, FN, TN is accepted. Proportions may be given as 0.89, 89 or 89%; the number of
decimals you type is taken as the reported precision and drives the rounding check:
integer counts must reproduce every reported value to that precision or the case is
flagged INCONSISTENT. When several integer tables reproduce the reported values, the
one nearest the exact solution is chosen and the alternatives are listed.

Confidence intervals: Wilson score for sens/spec/PPV/NPV/prevalence (Newcombe 1998),
log method for LR+/LR- (Simel 1991) and DOR (Woolf), 0.5 added to every cell when a
cell is zero (Haldane-Anscombe), stated in the output when applied.

Exit status: 0 on success (flags are printed, not fatal), 1 on bad input or I/O error.
"""

import argparse
import csv
import itertools
import json
import math
import os
import re
import statistics
import sys

PROPORTION_FIELDS = ("sens", "spec", "ppv", "npv", "prevalence")
COUNT_FIELDS = ("n", "n_positive", "n_negative", "TP", "FP", "FN", "TN")
ALL_FIELDS = COUNT_FIELDS + PROPORTION_FIELDS
NR_TOKENS = {"", "nr", "not reported", "na", "n/a", "-", "none"}
PERCENT_NOTES = []  # filled by parse_value, drained by solve()


class Val:
    """A reported number with its precision (decimals) kept for the rounding check."""

    def __init__(self, value, decimals, raw):
        self.value = value
        self.decimals = decimals
        self.raw = raw

    def __repr__(self):
        return f"Val({self.raw!r})"


def parse_value(raw, field):
    """Parse '0.89', '89', '89%', '235', '12.5 %' into a Val. Returns None for NR / blank."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s.lower() in NR_TOKENS:
        return None
    pct = s.endswith("%")
    s = s.rstrip("%").strip().replace(",", "")
    try:
        v = float(s)
    except ValueError:
        raise ValueError(f"{field}: cannot parse {raw!r} as a number")
    decimals = len(s.split(".")[1]) if "." in s else 0
    if field in PROPORTION_FIELDS:
        if pct or v > 1.0:
            if not pct:
                PERCENT_NOTES.append(f"{field}={raw} read as {v}% (write 0.{int(v):02d}-style proportions or add % to be explicit)")
            v = v / 100.0
            decimals += 2
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"{field}: {raw!r} is not a proportion in [0, 1]")
    else:
        if v < 0 or abs(v - round(v)) > 1e-9:
            raise ValueError(f"{field}: {raw!r} is not a non-negative integer")
        v = int(round(v))
    return Val(v, decimals, str(raw).strip())


def matches(computed, val):
    """True if `computed` rounds to the reported value at the reported precision."""
    if val is None:
        return True
    tol = 0.5 * 10 ** (-val.decimals) + 1e-9
    return abs(computed - val.value) <= tol


# ---------------------------------------------------------------- statistics


def zscore(level):
    return statistics.NormalDist().inv_cdf(0.5 + level / 200.0)


def wilson(x, n, level=95):
    """Wilson score interval (Newcombe 1998, method 3) for x successes in n."""
    if n <= 0:
        return (float("nan"), float("nan"))
    z = zscore(level)
    p = x / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def log_ci(est, se, level=95):
    z = zscore(level)
    return (est * math.exp(-z * se), est * math.exp(z * se))


def summary_stats(tp, fp, fn, tn, level=95):
    """All the accuracy statistics for an integer 2x2 table."""
    n_pos, n_neg = tp + fn, fp + tn
    n = n_pos + n_neg
    out = {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "n": n, "n_positive": n_pos,
           "n_negative": n_neg, "ci_level": level, "notes": []}
    if n == 0:
        out["notes"].append("empty table")
        return out
    out["prevalence"] = n_pos / n
    out["prevalence_ci"] = wilson(n_pos, n, level)
    if n_pos:
        out["sens"] = tp / n_pos
        out["sens_ci"] = wilson(tp, n_pos, level)
    if n_neg:
        out["spec"] = tn / n_neg
        out["spec_ci"] = wilson(tn, n_neg, level)
    if tp + fp:
        out["ppv"] = tp / (tp + fp)
        out["ppv_ci"] = wilson(tp, tp + fp, level)
    if tn + fn:
        out["npv"] = tn / (tn + fn)
        out["npv_ci"] = wilson(tn, tn + fn, level)
    if "sens" in out and "spec" in out:
        out["youden"] = out["sens"] + out["spec"] - 1
        out["auc_single_point"] = (out["sens"] + out["spec"]) / 2
    # LR / DOR with Haldane-Anscombe correction when any cell is zero
    a, b, c, d = tp, fp, fn, tn
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        out["notes"].append("0.5 added to every cell for LR/DOR (zero cell)")
    se_, sp_ = a / (a + c), d / (b + d)
    if 0 < sp_ < 1 and se_ > 0:
        lrp = se_ / (1 - sp_)
        se_lrp = math.sqrt((1 - se_) / a + sp_ / b)
        out["lr_pos"], out["lr_pos_ci"] = lrp, log_ci(lrp, se_lrp, level)
    if sp_ > 0 and se_ < 1:
        lrn = (1 - se_) / sp_
        se_lrn = math.sqrt(se_ / c + (1 - sp_) / d)
        out["lr_neg"], out["lr_neg_ci"] = lrn, log_ci(lrn, se_lrn, level)
    dor = (a * d) / (b * c)
    se_dor = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    out["dor"], out["dor_ci"] = dor, log_ci(dor, se_dor, level)
    return out


def n_from_ci(p, lo, hi, level=95):
    """Approximate denominator behind a reported proportion and its CI.

    Uses the Wald width (hi - lo = 2 z sqrt(p(1-p)/n)); exact only if the authors used
    Wald, so the answer is an estimate and is labelled as such.
    """
    z = zscore(level)
    width = hi - lo
    if width <= 0 or not 0 < p < 1:
        return None
    return p * (1 - p) / ((width / (2 * z)) ** 2)


# ---------------------------------------------------------------- solver


class Insufficient(Exception):
    pass


def exact_solution(r):
    """Float (TP, FP, FN, TN) from reported values r (dict field -> Val or None).

    Returns (tp, fp, fn, tn, steps) where steps is a list of derivation strings.
    """
    g = {k: (v.value if v is not None else None) for k, v in r.items()}
    steps = []

    def have(*ks):
        return all(g.get(k) is not None for k in ks)

    # 1. totals of the reference standard
    n_pos = n_neg = None
    if have("TP", "FN"):
        n_pos = g["TP"] + g["FN"]
        steps.append("n_positive = TP + FN")
    elif have("n_positive"):
        n_pos = g["n_positive"]
    if have("FP", "TN"):
        n_neg = g["FP"] + g["TN"]
        steps.append("n_negative = FP + TN")
    elif have("n_negative"):
        n_neg = g["n_negative"]
    n = g.get("n")
    if n is None and n_pos is not None and n_neg is not None:
        n = n_pos + n_neg
        steps.append("n = n_positive + n_negative")
    prev = g.get("prevalence")
    if prev is None and have("sens", "spec", "ppv"):
        se, sp, ppv = g["sens"], g["spec"], g["ppv"]
        den = se * (1 - ppv) + ppv * (1 - sp)
        if den > 0:
            prev = ppv * (1 - sp) / den
            steps.append("prevalence from sens, spec, PPV (Bayes)")
    if prev is None and have("sens", "spec", "npv"):
        se, sp, npv = g["sens"], g["spec"], g["npv"]
        den = sp * (1 - npv) + npv * (1 - se)
        if den > 0:
            prev = 1 - npv * (1 - se) / den
            steps.append("prevalence from sens, spec, NPV (Bayes)")
    if n_pos is None and n is not None and prev is not None:
        n_pos = n * prev
        steps.append("n_positive = n x prevalence")
    if n_pos is None and have("TP", "sens") and g["sens"] > 0:
        n_pos = g["TP"] / g["sens"]
        steps.append("n_positive = TP / sens")
    if n_pos is None and have("FN", "sens") and g["sens"] < 1:
        n_pos = g["FN"] / (1 - g["sens"])
        steps.append("n_positive = FN / (1 - sens)")
    if n_neg is None and n is not None and n_pos is not None:
        n_neg = n - n_pos
        steps.append("n_negative = n - n_positive")
    if n_neg is None and have("TN", "spec") and g["spec"] > 0:
        n_neg = g["TN"] / g["spec"]
        steps.append("n_negative = TN / spec")
    if n_neg is None and have("FP", "spec") and g["spec"] < 1:
        n_neg = g["FP"] / (1 - g["spec"])
        steps.append("n_negative = FP / (1 - spec)")
    if n_pos is None and n is not None and n_neg is not None:
        n_pos = n - n_neg
        steps.append("n_positive = n - n_negative")
    if n is None and n_pos is not None and n_neg is not None:
        n = n_pos + n_neg

    # 2. the cells
    tp = g.get("TP")
    if tp is None and n_pos is not None and have("sens"):
        tp = n_pos * g["sens"]
        steps.append("TP = n_positive x sens")
    if tp is None and n_pos is not None and have("FN"):
        tp = n_pos - g["FN"]
        steps.append("TP = n_positive - FN")
    tn = g.get("TN")
    if tn is None and n_neg is not None and have("spec"):
        tn = n_neg * g["spec"]
        steps.append("TN = n_negative x spec")
    if tn is None and n_neg is not None and have("FP"):
        tn = n_neg - g["FP"]
        steps.append("TN = n_negative - FP")
    # PPV / NPV routes when a margin is still unknown
    if tp is not None and tn is None and have("ppv") and 0 < g["ppv"] < 1 and n_neg is not None:
        fp_ = tp * (1 - g["ppv"]) / g["ppv"]
        tn = n_neg - fp_
        steps.append("FP = TP x (1 - PPV) / PPV; TN = n_negative - FP")
    if tn is not None and tp is None and have("npv") and 0 < g["npv"] < 1 and n_pos is not None:
        fn_ = tn * (1 - g["npv"]) / g["npv"]
        tp = n_pos - fn_
        steps.append("FN = TN x (1 - NPV) / NPV; TP = n_positive - FN")
    if tp is None or tn is None or n_pos is None or n_neg is None:
        missing = [k for k, v in (("TP", tp), ("TN", tn), ("n_positive", n_pos),
                                   ("n_negative", n_neg)) if v is None]
        raise Insufficient("cannot determine " + ", ".join(missing)
                           + ". Typical sufficient sets: {TP,FP,FN,TN}; {n, prevalence or "
                           "n_positive, sens, spec}; {n, sens, spec, PPV or NPV}.")
    fn = n_pos - tp
    fp = n_neg - tn
    return tp, fp, fn, tn, steps


def consistent_tables(r, exact, radius=3):
    """All integer tables within `radius` of the exact float solution that reproduce
    every reported value at its precision. Reported counts are held fixed."""
    tp0, fp0, fn0, tn0 = exact
    fixed = {k: r[k].value for k in ("TP", "FP", "FN", "TN") if r.get(k) is not None}

    def rng(name, x):
        if name in fixed:
            return [fixed[name]]
        c = int(round(x))
        return [v for v in range(c - radius, c + radius + 1) if v >= 0]

    found = []
    for tp, fp, fn, tn in itertools.product(rng("TP", tp0), rng("FP", fp0),
                                            rng("FN", fn0), rng("TN", tn0)):
        n_pos, n_neg, n = tp + fn, fp + tn, tp + fp + fn + tn
        if n == 0:
            continue
        checks = [
            ("n", n), ("n_positive", n_pos), ("n_negative", n_neg),
            ("prevalence", n_pos / n),
            ("sens", tp / n_pos if n_pos else float("nan")),
            ("spec", tn / n_neg if n_neg else float("nan")),
            ("ppv", tp / (tp + fp) if tp + fp else float("nan")),
            ("npv", tn / (tn + fn) if tn + fn else float("nan")),
        ]
        if all(matches(v, r.get(k)) for k, v in checks):
            dist = (tp - tp0) ** 2 + (fp - fp0) ** 2 + (fn - fn0) ** 2 + (tn - tn0) ** 2
            found.append((dist, (tp, fp, fn, tn)))
    found.sort()
    return [t for _, t in found]


def solve(reported, level=95, radius=3):
    """reported: dict field -> Val|None. Returns a result dict (see keys below)."""
    r = {k: reported.get(k) for k in ALL_FIELDS}
    given = {k: v.raw for k, v in r.items() if v is not None}
    res = {"given": given, "status": None, "flags": list(PERCENT_NOTES), "derivation": "", "alternatives": []}
    PERCENT_NOTES.clear()
    if all(r[k] is not None for k in ("TP", "FP", "FN", "TN")):
        tp, fp, fn, tn = (r[k].value for k in ("TP", "FP", "FN", "TN"))
        steps = ["2x2 counts as reported, verified against the other reported values"]
        exact = (tp, fp, fn, tn)
    else:
        try:
            tp, fp, fn, tn, steps = exact_solution(r)
        except Insufficient as e:
            res["status"] = "insufficient"
            res["flags"].append(str(e))
            return res
        exact = (tp, fp, fn, tn)
    tables = consistent_tables(r, exact, radius)
    if not tables:
        res["status"] = "inconsistent"
        tp_i, fp_i, fn_i, tn_i = (max(0, int(round(x))) for x in exact)
        res["flags"].append(
            "no integer table within +/-%d of the exact solution reproduces every reported "
            "value at its precision; check per-eye vs per-person counts, exclusions, or a "
            "misread threshold" % radius)
        stats = summary_stats(tp_i, fp_i, fn_i, tn_i, level)
        for k in PROPORTION_FIELDS:
            if r[k] is not None and k in stats and not matches(stats[k], r[k]):
                res["flags"].append(f"reported {k}={r[k].raw} but nearest table gives {stats[k]:.4f}")
        for k in ("n", "n_positive", "n_negative"):
            if r[k] is not None and stats[k] != r[k].value:
                res["flags"].append(f"reported {k}={r[k].raw} but nearest table gives {stats[k]}")
        res["nearest"] = stats
        res["derivation"] = "; ".join(steps)
        return res
    tp_i, fp_i, fn_i, tn_i = tables[0]
    res["status"] = "ok"
    res["stats"] = summary_stats(tp_i, fp_i, fn_i, tn_i, level)
    res["stats"]["notes"] = list(res["stats"]["notes"])
    if len(tables) > 1:
        res["alternatives"] = tables[1:]
        rngs = []
        for i, name in enumerate(("TP", "FP", "FN", "TN")):
            vals = sorted({t[i] for t in tables})
            if len(vals) > 1:
                rngs.append(f"{name} {vals[0]}-{vals[-1]}")
        res["flags"].append(
            f"{len(tables)} integer tables reproduce the reported values ({', '.join(rngs)}); "
            "nearest to the exact solution chosen")
    exact_txt = "exact TP=%.2f FP=%.2f FN=%.2f TN=%.2f" % exact
    res["derivation"] = "; ".join(steps) + f" ({exact_txt}; rounded to {tp_i}/{fp_i}/{fn_i}/{tn_i})"
    return res


# ---------------------------------------------------------------- CSV mode

FILLABLE = ("n", "n_positive", "prevalence", "TP", "FP", "FN", "TN", "sens", "spec",
            "ppv", "npv", "sens_ci_low", "sens_ci_high", "spec_ci_low", "spec_ci_high")


def is_blank(s):
    return s is None or str(s).strip().lower() in NR_TOKENS


def fmt(x, decimals=4):
    return f"{x:.{decimals}f}".rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def process_csv(path, out_path, dry_run, level, radius):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        rows = list(reader)
    needed = {"study_id", "TP", "FP", "FN", "TN", "sens", "spec", "derivation"}
    missing = needed - set(fields)
    if missing:
        sys.exit(f"error: {path} lacks required columns: {', '.join(sorted(missing))}")
    report = {"rows": len(rows), "filled": 0, "verified": 0, "flagged": 0,
              "insufficient": 0, "skipped": 0, "messages": []}
    for i, row in enumerate(rows, start=2):
        label = f"row {i} (study {row.get('study_id', '?')}, {row.get('instrument', '')!s:.30})"
        reported = {}
        try:
            for k in ALL_FIELDS:
                if k in fields:
                    reported[k] = parse_value(row.get(k), k)
        except ValueError as e:
            report["flagged"] += 1
            report["messages"].append(f"{label}: {e}")
            continue
        if all(reported.get(k) is None for k in ALL_FIELDS):
            report["skipped"] += 1
            continue
        res = solve(reported, level, radius)
        if res["status"] == "insufficient":
            report["insufficient"] += 1
            report["messages"].append(f"{label}: insufficient data ({res['flags'][0]})")
            continue
        if res["status"] == "inconsistent":
            report["flagged"] += 1
            report["messages"].append(f"{label}: INCONSISTENT: " + " | ".join(res["flags"]))
            continue
        st = res["stats"]
        filled = []
        values = {"n": st["n"], "n_positive": st["n_positive"], "prevalence": st["prevalence"],
                  "TP": st["TP"], "FP": st["FP"], "FN": st["FN"], "TN": st["TN"],
                  "sens": st.get("sens"), "spec": st.get("spec"),
                  "ppv": st.get("ppv"), "npv": st.get("npv")}
        if "sens_ci" in st:
            values["sens_ci_low"], values["sens_ci_high"] = st["sens_ci"]
        if "spec_ci" in st:
            values["spec_ci_low"], values["spec_ci_high"] = st["spec_ci"]
        for k in FILLABLE:
            if k in fields and is_blank(row.get(k)) and values.get(k) is not None:
                row[k] = fmt(values[k])
                filled.append(k)
        if filled:
            report["filled"] += 1
            note = ("reconstruct_2x2 filled " + ",".join(filled) + " from "
                    + ", ".join(f"{k}={v}" for k, v in res["given"].items())
                    + ": " + res["derivation"])
            if any(k.endswith("_ci_low") or k.endswith("_ci_high") for k in filled):
                note += f"; CIs are Wilson {level}%"
            if res["flags"]:
                note += "; " + "; ".join(res["flags"])
            row["derivation"] = (row.get("derivation", "") + " | " if not is_blank(row.get("derivation")) else "") + note
            report["messages"].append(f"{label}: filled {', '.join(filled)}"
                                      + (f" [{'; '.join(res['flags'])}]" if res["flags"] else ""))
        else:
            report["verified"] += 1
            if res["flags"]:
                report["messages"].append(f"{label}: consistent; {'; '.join(res['flags'])}")
    if not dry_run:
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    return report


# ---------------------------------------------------------------- CLI


def print_result(res, as_json):
    if as_json:
        print(json.dumps(res, indent=2, default=str))
        return
    print("given:      " + ", ".join(f"{k}={v}" for k, v in res["given"].items()))
    print("derivation: " + res["derivation"])
    print("status:     " + res["status"].upper())
    for f in res["flags"]:
        print("flag:       " + f)
    st = res.get("stats") or res.get("nearest")
    if not st:
        return
    print(f"\n            ref+    ref-\n  test+   {st['TP']:5d}   {st['FP']:5d}\n  test-   {st['FN']:5d}   {st['TN']:5d}"
          f"\n  n={st['n']}  n_positive={st['n_positive']}  n_negative={st['n_negative']}\n")

    def line(name, key):
        if key in st:
            ci = st.get(key + "_ci")
            print(f"  {name:<11} {st[key]:.4f}" + (f"  ({ci[0]:.4f} to {ci[1]:.4f})" if ci else ""))
    for name, key in (("prevalence", "prevalence"), ("sens", "sens"), ("spec", "spec"),
                      ("PPV", "ppv"), ("NPV", "npv"), ("LR+", "lr_pos"), ("LR-", "lr_neg"),
                      ("DOR", "dor")):
        line(name, key)
    if "youden" in st:
        print(f"  {'Youden J':<11} {st['youden']:.4f}")
        print(f"  {'(sens+spec)/2':<11} {st['auc_single_point']:.4f}   <- single-point 'AUC', not a ROC area")
    print(f"  CI level {st['ci_level']}% (Wilson for proportions; log method for LR/DOR)")
    for n in st["notes"]:
        print("  note: " + n)
    if res.get("alternatives"):
        print("  alternatives: " + "; ".join("/".join(map(str, t)) for t in res["alternatives"][:8])
              + (" ..." if len(res["alternatives"]) > 8 else ""))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in COUNT_FIELDS:
        p.add_argument("--" + k.lower().replace("_", "-"), dest=k, metavar="INT")
    for k in PROPORTION_FIELDS:
        p.add_argument("--" + k, dest=k, metavar="PROP", help=f"{k} as 0.89, 89 or 89%%")
    p.add_argument("--sens-ci", metavar="LO,HI", help="reported CI of sens; used only to estimate n_positive when nothing else gives it")
    p.add_argument("--spec-ci", metavar="LO,HI", help="reported CI of spec; used only to estimate n_negative")
    p.add_argument("--ci-level", type=float, default=95, help="CI level in %% (default 95)")
    p.add_argument("--radius", type=int, default=3, help="integer search radius around the exact solution (default 3)")
    p.add_argument("--json", action="store_true", help="print the single-case result as JSON")
    p.add_argument("--csv", metavar="DTA_CSV", help="fill blank cells in a dta.csv instead of a single case")
    p.add_argument("--out", metavar="PATH", help="where to write the filled CSV (with --csv)")
    p.add_argument("--in-place", action="store_true", help="write the filled CSV over the input (with --csv)")
    p.add_argument("--dry-run", action="store_true", help="with --csv: report what would be filled, write nothing")
    a = p.parse_args(argv)

    if a.csv:
        if not a.dry_run and not (a.out or a.in_place):
            p.error("--csv needs --out PATH, --in-place or --dry-run")
        out = a.csv if a.in_place else a.out
        rep = process_csv(a.csv, out, a.dry_run, a.ci_level, a.radius)
        for m in rep["messages"]:
            print(m)
        print(f"\n{rep['rows']} rows: {rep['filled']} filled, {rep['verified']} verified as consistent, "
              f"{rep['flagged']} flagged, {rep['insufficient']} insufficient, {rep['skipped']} with no 2x2 data"
              + ("" if a.dry_run else f"\nwritten: {out}"))
        return 0

    try:
        reported = {k: parse_value(getattr(a, k), k) for k in ALL_FIELDS}
    except ValueError as e:
        p.error(str(e))
    if all(v is None for v in reported.values()):
        p.error("give at least one of " + ", ".join("--" + k.lower().replace("_", "-") for k in ALL_FIELDS) + ", or --csv")
    # CI-based estimation of the margins, only as a last resort
    est_notes = []
    for prop, ci, margin in (("sens", a.sens_ci, "n_positive"), ("spec", a.spec_ci, "n_negative")):
        if ci and reported[prop] is not None and reported[margin] is None:
            try:
                lo, hi = (float(x) for x in ci.split(","))
            except ValueError:
                p.error(f"--{prop}-ci must be LO,HI")
            if lo > 1 or hi > 1:
                lo, hi = lo / 100, hi / 100
            est = n_from_ci(reported[prop].value, lo, hi, a.ci_level)
            if est:
                reported[margin] = Val(int(round(est)), 0, f"~{int(round(est))}")
                est_notes.append(f"{margin} ~ {est:.1f} estimated from {prop} CI {lo}-{hi} assuming a Wald interval "
                                 "(APPROXIMATE: confirm with the paper; precision check relaxed for this margin)")
                # the margin is an estimate, so do not let the exact-match check pin it
                reported[margin].decimals = -2  # tolerance of +/- 50 on the margin
    res = solve(reported, a.ci_level, a.radius)
    res["flags"] = est_notes + res["flags"]
    print_result(res, a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
