#!/usr/bin/env python3
"""Per-study accuracy tables and figures WITHOUT pooling (SWiM / Cochrane Handbook ch. 12).

    python3 -I accuracy_table.py analysis/extraction/dta.csv \
        [--effects analysis/extraction/effects.csv] [--studies analysis/synthesis/studies_with_datasets.csv] \
        [--rob analysis/risk_of_bias/quadas2.csv] [--group-by instrument,reference_standard] \
        [--filter unit=person] [--filter subgroup=] [--out-dir analysis/synthesis]

Reads the data-extraction dta.csv (one row per index test x threshold x reference standard),
groups rows by instrument x reference standard (or --group-by), and writes:
  accuracy_table.md / .csv   sens, spec, AUC with 95% CIs, n, prevalence, threshold, reference
                             threshold, dataset_id, QUADAS-2 overall judgement; one row per
                             study-threshold; a verdict per group (describe / hand to pooling)
  forest_nopool.svg/.png     paired sensitivity and specificity with CIs, grouped, no pooled
                             diamond, labelled "no pooled estimate"
  roc_space.svg/.png         sensitivity vs 1 - specificity, one point per study-threshold,
                             marker shape + colour by instrument, size by n
Missing CIs are computed from the 2x2 cells with the Wilson score interval (Newcombe 1998),
imported from data-extraction's reconstruct_2x2.py (formula repeated here as a fallback).
When only sens and n_positive are known the counts are back-calculated and the CI is marked
approximate. AUC rows from effects.csv (outcome_type = auc) are joined on study_id +
instrument when dta.csv has no AUC for that row. An "AUC" equal to (sens + spec) / 2 at a
single threshold is flagged, not treated as a ROC area.

Exit 0 on success, 1 on bad input. Needs numpy and matplotlib.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import os
import sys
from collections import OrderedDict, defaultdict

try:
    import numpy as np
    import matplotlib
except ImportError:  # python3 -I hides the user site; re-add that one trusted dir
    import site
    sys.path.append(site.getusersitepackages())
    try:
        import numpy as np
        import matplotlib
    except ImportError:
        sys.exit("numpy and matplotlib are required: python3 -m pip install --user --break-system-packages numpy matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

VERSION = "1.0.0"
HERE = os.path.dirname(os.path.abspath(__file__))
RECONSTRUCT = os.path.normpath(os.path.join(HERE, "..", "..", "data-extraction", "scripts", "reconstruct_2x2.py"))
NR = {"", "nr", "na", "n/a", "none", "-"}
MIN_K_BIVARIATE = 4

# Same palette as dta-meta-analysis / dataviz reference palette; Okabe-Ito for RoB as in risk-of-bias.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
C_TEXT, C_MUTED, C_GRID, C_BAND = "#0b0b0b", "#52514e", "#d9d8d4", "#f1f1f1"
ROB_COLOUR = {"Low": "#009E73", "Unclear": "#E69F00", "High": "#D55E00"}


def load_wilson():
    if os.path.exists(RECONSTRUCT):
        try:
            spec = importlib.util.spec_from_file_location("reconstruct_2x2", RECONSTRUCT)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.wilson, "reconstruct_2x2.py"
        except Exception as exc:  # pragma: no cover
            print(f"note: could not import {RECONSTRUCT} ({exc}); using the local Wilson formula", file=sys.stderr)

    def wilson(x, n, level=95):
        """Wilson score interval (Newcombe 1998, method 3): same formula as reconstruct_2x2.py."""
        if n <= 0:
            return (float("nan"), float("nan"))
        z = {90: 1.6448536269514722, 95: 1.959963984540054, 99: 2.5758293035489004}[int(level)]
        p = x / n
        denom = 1 + z * z / n
        centre = (p + z * z / (2 * n)) / denom
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
        return (max(0.0, centre - half), min(1.0, centre + half))
    return wilson, "local"


def is_blank(s):
    return s is None or str(s).strip().lower() in NR


def num(s):
    if is_blank(s):
        return None
    try:
        return float(str(s).strip().rstrip("%"))
    except ValueError:
        return None


def to_int(s):
    v = num(s)
    return None if v is None else int(round(v))


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields = [f.strip() for f in (reader.fieldnames or [])]
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
    return fields, rows


def parse_filters(items):
    out = []
    for it in items or []:
        if "=" not in it:
            sys.exit(f"error: --filter expects COL=VALUE, got '{it}'")
        col, val = it.split("=", 1)
        out.append((col.strip(), val.strip()))
    return out


def keep(row, filters):
    for col, val in filters:
        have = row.get(col, "")
        if val == "":
            if not is_blank(have):
                return False
        elif have.lower() != val.lower():
            return False
    return True


def rob_overall(rob_rows):
    """QUADAS-2 overall per study: High if any domain High, else Unclear if any Unclear, else Low
    (same rule as risk-of-bias/rob_plots.py). Returns {study_id: (overall, 'D1 L / D2 H / ...')}."""
    order = ["Patient selection", "Index test", "Reference standard", "Flow and timing"]
    by = defaultdict(dict)
    for r in rob_rows:
        by[r.get("study_id", "")][r.get("domain", "")] = (r.get("rob_judgement") or "").strip().title()
    out = {}
    for sid, doms in by.items():
        js = [doms.get(d, "") for d in order]
        overall = "High" if "High" in js else ("Unclear" if ("Unclear" in js or "" in js) else "Low")
        short = " / ".join(f"D{i + 1} {j[:1] or '?'}" for i, j in enumerate(js))
        out[sid] = (overall, short)
    return out


def fmt(x, d=2):
    return "NR" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def fmt_ci(est, lo, hi, flag=""):
    if est is None:
        return "NR"
    if lo is None or hi is None:
        return f"{fmt(est)}{flag}"
    return f"{fmt(est)} ({fmt(lo)}-{fmt(hi)}){flag}"


def derive(row, wilson, level):
    """Fill sens/spec/CIs from whatever the row has. Returns a dict with the values and a source note."""
    tp, fp, fn, tn = (to_int(row.get(c)) for c in ("TP", "FP", "FN", "TN"))
    n = to_int(row.get("n"))
    npos = to_int(row.get("n_positive"))
    if npos is None and tp is not None and fn is not None:
        npos = tp + fn
    if n is None and None not in (tp, fp, fn, tn):
        n = tp + fp + fn + tn
    nneg = None if (n is None or npos is None) else n - npos
    prev = num(row.get("prevalence"))
    if prev is None and n and npos is not None:
        prev = npos / n
    out = {"n": n, "n_positive": npos, "prevalence": prev, "flags": []}
    for name, x, denom, lo_col, hi_col in (("sens", tp, (tp + fn) if None not in (tp, fn) else None, "sens_ci_low", "sens_ci_high"),
                                            ("spec", tn, (tn + fp) if None not in (tn, fp) else None, "spec_ci_low", "spec_ci_high")):
        est = num(row.get(name))
        lo, hi = num(row.get(lo_col)), num(row.get(hi_col))
        src = "reported"
        if est is None and x is not None and denom:
            est = x / denom
            src = "from 2x2"
        if (lo is None or hi is None) and est is not None:
            if x is not None and denom:
                lo, hi = wilson(x, denom, level)
                src = "Wilson from 2x2"
            else:
                d = (tp + fn) if (name == "sens" and None not in (tp, fn)) else (npos if name == "sens" else nneg)
                if d:
                    lo, hi = wilson(int(round(est * d)), d, level)
                    src = "Wilson, counts back-calculated"
                    out["flags"].append("approx")
        out[name], out[name + "_lo"], out[name + "_hi"], out[name + "_src"] = est, lo, hi, src
    out["auc"], out["auc_lo"], out["auc_hi"] = num(row.get("auc")), num(row.get("auc_ci_low")), num(row.get("auc_ci_high"))
    text = (row.get("notes", "") + " " + row.get("derivation", "")).lower()
    if out["auc"] is not None and out["sens"] is not None and out["spec"] is not None:
        if "(sens+spec)/2" in text.replace(" ", "") or (out["auc_lo"] is None and abs(out["auc"] - (out["sens"] + out["spec"]) / 2) < 0.006):
            out["flags"].append("auc_single")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dta", help="dta.csv from the data-extraction skill")
    ap.add_argument("--effects", help="effects.csv; its outcome_type=auc rows supply AUCs missing from dta.csv")
    ap.add_argument("--studies", help="studies.csv (ideally the --assign copy from independent_datasets.py with dataset_id)")
    ap.add_argument("--rob", help="QUADAS-2 CSV from the risk-of-bias skill (study_id, domain, rob_judgement)")
    ap.add_argument("--group-by", default="instrument,reference_standard", help="comma-separated dta.csv columns (default %(default)s)")
    ap.add_argument("--filter", action="append", metavar="COL=VALUE", help="keep rows where COL equals VALUE (empty VALUE keeps blank cells); repeatable")
    ap.add_argument("--out-dir", default="analysis/synthesis")
    ap.add_argument("--level", type=int, default=95, choices=(90, 95, 99))
    ap.add_argument("--min-k", type=int, default=MIN_K_BIVARIATE, help="independent datasets needed before a group is handed to dta-meta-analysis (default %(default)s)")
    ap.add_argument("--title", default="Accuracy of self-report items and questionnaires, per study (no pooled estimate)")
    ap.add_argument("--version", action="version", version=VERSION)
    args = ap.parse_args(argv)

    wilson, wilson_src = load_wilson()
    if not os.path.exists(args.dta):
        sys.exit(f"error: {args.dta} not found")
    fields, rows = read_csv(args.dta)
    for col in ("study_id", "instrument", "threshold", "reference_standard"):
        if col not in fields:
            sys.exit(f"error: dta.csv lacks the '{col}' column")
    group_cols = [c.strip() for c in args.group_by.split(",") if c.strip()]
    for c in group_cols:
        if c not in fields:
            sys.exit(f"error: --group-by column '{c}' not in dta.csv")
    filters = parse_filters(args.filter)
    rows = [r for r in rows if keep(r, filters)]
    if not rows:
        sys.exit("error: no rows left after --filter")

    labels, dataset, n_study = {}, {}, {}
    if args.studies:
        _, srows = read_csv(args.studies)
        for s in srows:
            labels[s["study_id"]] = s.get("label") or s["study_id"]
            if not is_blank(s.get("dataset_id")):
                dataset[s["study_id"]] = s["dataset_id"]
            n_study[s["study_id"]] = to_int(s.get("n"))
    rob = {}
    if args.rob:
        _, rrows = read_csv(args.rob)
        rob = rob_overall(rrows)
    effects_auc = defaultdict(list)
    if args.effects:
        _, erows = read_csv(args.effects)
        for e in erows:
            if (e.get("outcome_type") or "").lower() == "auc":
                effects_auc[(e["study_id"], e.get("instrument", ""))].append(e)

    table = []
    for r in rows:
        sid = r["study_id"]
        d = derive(r, wilson, args.level)
        if d["auc"] is None:
            cands = effects_auc.get((sid, r.get("instrument", "")), [])
            cands = [e for e in cands if (e.get("subgroup", "") == r.get("subgroup", "")) and (is_blank(e.get("unit")) or e.get("unit") == r.get("unit"))]
            if cands:
                e = cands[0]
                d["auc"], d["auc_lo"], d["auc_hi"] = num(e.get("estimate")), num(e.get("ci_low")), num(e.get("ci_high"))
                d["flags"].append("auc_effects")
        label = r.get("label") or labels.get(sid) or sid
        table.append({
            "group": tuple(r.get(c, "") for c in group_cols),
            "study_id": sid, "label": label,
            "dataset_id": dataset.get(sid, sid),
            "threshold": r.get("threshold", ""), "ref_threshold": r.get("ref_threshold", ""),
            "subgroup": r.get("subgroup", ""), "unit": r.get("unit", ""),
            "item_text": r.get("item_text", ""),
            "n": d["n"] if d["n"] is not None else n_study.get(sid),
            "n_positive": d["n_positive"], "prevalence": d["prevalence"],
            "sens": d["sens"], "sens_lo": d["sens_lo"], "sens_hi": d["sens_hi"], "sens_src": d["sens_src"],
            "spec": d["spec"], "spec_lo": d["spec_lo"], "spec_hi": d["spec_hi"], "spec_src": d["spec_src"],
            "auc": d["auc"], "auc_lo": d["auc_lo"], "auc_hi": d["auc_hi"],
            "rob_overall": rob.get(sid, ("", ""))[0], "rob_domains": rob.get(sid, ("", ""))[1],
            "flags": d["flags"], "page": r.get("page", ""),
        })

    groups = OrderedDict()
    for t in sorted(table, key=lambda t: (t["group"], t["label"], t["threshold"])):
        groups.setdefault(t["group"], []).append(t)

    os.makedirs(args.out_dir, exist_ok=True)
    md = [f"# {args.title}", "",
          f"One row per study x threshold. CIs are {args.level}% Wilson score intervals from the 2x2 cells when the paper "
          f"gave none (`{wilson_src}`); 'approx' marks CIs from counts back-calculated from a reported proportion. "
          "No pooled estimate is given: rows sharing a dataset_id come from the same participants and count once. "
          "AI-drafted table; the reviewer checks every number against the cited page.", ""]
    verdicts = []
    for g, items in groups.items():
        head = " x ".join(f"{c} = {v or 'NR'}" for c, v in zip(group_cols, g))
        k_studies = len({t["study_id"] for t in items})
        k_ind = len({t["dataset_id"] for t in items})
        by_thr = defaultdict(set)
        for t in items:
            by_thr[(t["threshold"], t["ref_threshold"])].add(t["dataset_id"])
        thresholds = dict(by_thr)
        best_thr, best_k = max(by_thr.items(), key=lambda kv: (len(kv[1]), kv[0]))[0], max(len(v) for v in by_thr.values())
        if k_ind >= args.min_k and len(thresholds) == 1:
            verdict = f"{k_ind} independent datasets at one threshold: candidate for pooling; run `dta_pool.py validate` (dta-meta-analysis) before deciding"
        elif best_k >= args.min_k:
            verdict = (f"{k_ind} independent datasets over {len(thresholds)} threshold/reference definitions; the largest comparable subset "
                       f"({best_k} datasets at '{best_thr[0]}' vs '{best_thr[1]}') is a candidate for pooling in dta-meta-analysis; describe the rest")
        elif k_ind >= args.min_k:
            verdict = (f"{k_ind} independent datasets but {len(thresholds)} threshold/reference definitions (largest comparable subset {best_k}): "
                       "pool only with a pre-specified one-per-study threshold rule (dta-meta-analysis), otherwise describe")
        elif k_ind == 1:
            verdict = "1 independent dataset: present as-is with CIs; no pooling, no between-study heterogeneity"
        else:
            verdict = f"{k_ind} independent datasets (< {args.min_k}): describe per study with CIs and the range; a bivariate model cannot be fitted"
        verdicts.append((head, k_studies, k_ind, verdict))
        md += [f"## {head}", "", f"{k_studies} study/ies, {k_ind} independent dataset(s). **Verdict:** {verdict}.", "",
               "| Study | Dataset | n | Prevalence | Test threshold | Reference threshold | Sensitivity (95% CI) | Specificity (95% CI) | AUC (95% CI) | QUADAS-2 overall |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for t in items:
            fl_s = "†" if "approx" in t["flags"] else ""
            fl_a = "§" if "auc_single" in t["flags"] else ("‡" if "auc_effects" in t["flags"] else "")
            sub = f" ({t['subgroup']})" if t["subgroup"] else ""
            md.append("| " + " | ".join([
                t["label"] + sub, t["dataset_id"], str(t["n"]) if t["n"] is not None else "NR", fmt(t["prevalence"]),
                t["threshold"] or "NR", t["ref_threshold"] or "NR",
                fmt_ci(t["sens"], t["sens_lo"], t["sens_hi"], fl_s), fmt_ci(t["spec"], t["spec_lo"], t["spec_hi"], fl_s),
                fmt_ci(t["auc"], t["auc_lo"], t["auc_hi"], fl_a),
                (t["rob_overall"] + (f" ({t['rob_domains']})" if t["rob_domains"] else "")) or "not assessed",
            ]) + " |")
        md.append("")
    md += ["† CI from counts back-calculated from the reported proportion and group size (approximate). "
           "§ Not a ROC area: (sens + spec) / 2 at a single threshold, as the paper computed it. "
           "‡ AUC taken from effects.csv (ROC area reported separately from the 2x2).", ""]
    md += ["## Group summary", "", "| Group | studies | independent datasets | verdict |", "|---|---|---|---|"]
    for head, ks, ki, v in verdicts:
        md.append(f"| {head} | {ks} | {ki} | {v} |")
    md.append("")
    with open(os.path.join(args.out_dir, "accuracy_table.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    csv_cols = ["group", "study_id", "label", "dataset_id", "subgroup", "unit", "n", "n_positive", "prevalence", "threshold", "ref_threshold",
                "sens", "sens_lo", "sens_hi", "sens_src", "spec", "spec_lo", "spec_hi", "spec_src", "auc", "auc_lo", "auc_hi",
                "rob_overall", "rob_domains", "flags", "page"]
    with open(os.path.join(args.out_dir, "accuracy_table.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(csv_cols)
        for t in table:
            w.writerow([(" x ".join(t["group"]) if c == "group" else ";".join(t["flags"]) if c == "flags"
                         else ("" if t[c] is None else (f"{t[c]:.4f}" if isinstance(t[c], float) else t[c]))) for c in csv_cols])

    plt.rcParams.update({"svg.hashsalt": "narrative-synthesis", "font.size": 8.5, "axes.edgecolor": "#888888",
                         "text.color": C_TEXT, "axes.labelcolor": C_TEXT, "xtick.color": C_MUTED, "ytick.color": C_TEXT})
    forest(groups, group_cols, args, os.path.join(args.out_dir, "forest_nopool"))
    roc_space(table, args, os.path.join(args.out_dir, "roc_space"))

    print(f"{len(table)} study-threshold rows in {len(groups)} group(s); outputs in {args.out_dir}/ "
          "(accuracy_table.md/.csv, forest_nopool.svg/.png, roc_space.svg/.png)")
    for head, ks, ki, v in verdicts:
        print(f"  {head}: {ks} studies, {ki} independent -> {v}")
    return 0


def forest(groups, group_cols, args, outbase):
    rows = []  # (kind, text, item)
    for g, items in groups.items():
        rows.append(("head", " x ".join(v or "NR" for v in g), None))
        shared = {d for d in [t["dataset_id"] for t in items] if [t["dataset_id"] for t in items].count(d) > 1}
        for t in items:
            lab = t["label"] + (f" ({t['subgroup']})" if t["subgroup"] else "")
            thr = t["threshold"] if len(t["threshold"]) <= 38 else t["threshold"][:36] + "..."
            mark = (" ‡" if t["dataset_id"] in shared else "") + (" †" if "approx" in t["flags"] else "")
            rows.append(("item", f"{lab}{mark} · {thr} · n={t['n'] if t['n'] is not None else 'NR'}", t))
    n_rows = len(rows)
    height = max(2.8, 0.34 * n_rows + 1.6)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, height), sharey=True)
    ys = list(range(n_rows))[::-1]
    for ax, key, name in ((axes[0], "sens", "Sensitivity"), (axes[1], "spec", "Specificity")):
        for y, (kind, text, t) in zip(ys, rows):
            if kind == "head":
                ax.axhspan(y - 0.5, y + 0.5, color=C_BAND, zorder=0, linewidth=0)
                continue
            est, lo, hi = t[key], t[key + "_lo"], t[key + "_hi"]
            if est is None:
                ax.text(0.5, y, "NR", ha="center", va="center", color=C_MUTED, fontsize=7.5)
                continue
            size = 4 + 3.5 * math.sqrt((t["n"] or 25) / 100)
            if lo is not None and hi is not None:
                ax.plot([lo, hi], [y, y], color=PALETTE[0], linewidth=1.4, solid_capstyle="butt", zorder=2)
            ax.plot(est, y, marker="s", markersize=size, color=PALETTE[0], markeredgecolor="white", markeredgewidth=0.8, zorder=3)
            ax.text(1.03, y, f"{est:.2f}" + ("" if lo is None else f" ({lo:.2f}-{hi:.2f})"), va="center", ha="left", fontsize=7.5, color=C_TEXT, clip_on=False)
        ax.set_xlim(0, 1)
        ax.tick_params(axis="y", length=0)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xlabel(f"{name} ({args.level}% CI)")
        ax.grid(axis="x", color=C_GRID, linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_ylim(-0.6, n_rows - 0.4)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([t if k == "item" else t for k, t, _ in rows], fontsize=8)
    for lab, (kind, _, _) in zip(axes[0].get_yticklabels(), rows):
        if kind == "head":
            lab.set_fontweight("bold")
    axes[0].tick_params(axis="y", length=0)
    fig.suptitle(args.title, fontsize=10, x=0.01, ha="left")
    fig.text(0.01, 0.005, "No pooled estimate: studies are shown individually (synthesis without meta-analysis, SWiM). "
             "Squares scale with n. ‡ same participants as another row (one dataset). † approximate CI.",
             fontsize=7.5, color=C_MUTED, ha="left", va="bottom")
    fig.subplots_adjust(left=0.38, right=0.9, top=0.9, bottom=max(0.08, 0.5 / height), wspace=0.48)
    fig.savefig(outbase + ".svg", metadata={"Date": None})
    fig.savefig(outbase + ".png", dpi=200, metadata={"Software": None})
    plt.close(fig)


def roc_space(table, args, outbase):
    pts = [t for t in table if t["sens"] is not None and t["spec"] is not None]
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.plot([0, 1], [0, 1], color=C_GRID, linewidth=1, linestyle="--", zorder=1)
    ax.text(0.97, 0.94, "chance", color=C_MUTED, fontsize=7.5, ha="right", rotation=0)
    instruments = sorted({t["group"][0] if t["group"] else "" for t in pts})
    handles = []
    placed = []  # label boxes (x0, y0, x1, y1) in points, to keep labels off each other and off the markers
    candidates = [((7, 3), "left"), ((7, -9), "left"), ((-7, 3), "right"), ((-7, -9), "right"), ((0, 11), "center"), ((0, -15), "center"),
                  ((16, 10), "left"), ((16, -16), "left"), ((-16, 10), "right"), ((-16, -16), "right"), ((0, 22), "center"), ((0, -26), "center")]
    all_pts = sorted(pts, key=lambda t: (-t["sens"], t["spec"]))
    for t in all_pts:
        r = math.sqrt(20 + 0.6 * (t["n"] or 25)) / 2 * 1.1
        c = ax.transData.transform((1 - t["spec"], t["sens"])) * 72 / fig.dpi
        placed.append((c[0] - r, c[1] - r, c[0] + r, c[1] + r))  # marker footprints are obstacles too

    def overlap(a, b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

    for i, inst in enumerate(instruments):
        col, mk = PALETTE[i % len(PALETTE)], MARKERS[i % len(MARKERS)]
        sub = [t for t in all_pts if (t["group"][0] if t["group"] else "") == inst]
        for t in sub:
            n = t["n"] or 25
            ax.scatter(1 - t["spec"], t["sens"], s=20 + 0.6 * n, color=col, marker=mk, alpha=0.75, edgecolors="white", linewidths=0.8, zorder=3)
            text = t["label"] + (f" ({t['subgroup']})" if t["subgroup"] else "")
            w, h = 3.9 * len(text), 8.0
            base = ax.transData.transform((1 - t["spec"], t["sens"])) * 72 / fig.dpi
            best = None
            for off, ha in candidates:
                x0 = base[0] + off[0] - (w if ha == "right" else w / 2 if ha == "center" else 0)
                box = (x0, base[1] + off[1] - 1, x0 + w, base[1] + off[1] + h)
                clashes = sum(overlap(box, p) for p in placed)
                if best is None or clashes < best[0]:
                    best = (clashes, off, ha, box)
                if clashes == 0:
                    break
            placed.append(best[3])
            ax.annotate(text, (1 - t["spec"], t["sens"]), xytext=best[1], textcoords="offset points", ha=best[2],
                        fontsize=7, color=C_TEXT, zorder=4)
        handles.append(Line2D([0], [0], marker=mk, color="none", markerfacecolor=col, markersize=7, label=inst[:40] or "NR"))
    for n_ref in (50, 200, 500):
        handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="#bbbbbb", markersize=math.sqrt(20 + 0.6 * n_ref) * 0.95, label=f"n = {n_ref}"))
    ax.legend(handles=handles, loc="lower right", fontsize=7.5, frameon=False, title="instrument / size", title_fontsize=7.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("1 - specificity (false positive rate)")
    ax.set_ylabel("Sensitivity")
    ax.set_title("Study results in ROC space (no summary curve)", fontsize=10, loc="left")
    ax.grid(color=C_GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.text(0.01, 0.005, "One point per study-threshold; point area scales with n. No SROC curve is fitted (too few independent datasets).",
             fontsize=7.5, color=C_MUTED)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.94, bottom=0.11)
    fig.savefig(outbase + ".svg", metadata={"Date": None})
    fig.savefig(outbase + ".png", dpi=200, metadata={"Software": None})
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
