#!/usr/bin/env python3
"""Evidence map (instrument x reference standard, cell = independent datasets and total n) and a
harvest / effect-direction plot for effects.csv outcomes, for a synthesis without meta-analysis.

    python3 -I evidence_map.py --dta analysis/extraction/dta.csv [--effects analysis/extraction/effects.csv] \
        [--studies analysis/synthesis/studies_with_datasets.csv] [--rob analysis/risk_of_bias/quadas2.csv] \
        [--rows instrument] [--cols reference_standard] [--out-dir analysis/synthesis]

Evidence map (from --dta, rows x cols default instrument x reference_standard; from --effects,
instrument x comparator): each cell counts distinct dataset_id values (dataset_id from
--studies, else study_id) and sums n once per dataset (the largest n that dataset contributes
to the cell). Shaded by number of datasets, text in every cell, so colour is never the only
cue. Written as evidence_map_<source>.svg/.png and .md. Use it to show at a glance where the
evidence is (and the empty cells that a reader would otherwise assume exist).

Harvest plot (from --effects; Ogilvie 2008, Crowther 2011): one panel per outcome group
(instrument x comparator x outcome_type), three columns (negative / null or unclear /
positive direction), one bar per dataset, bar height = effect-size class (1 trivial ...
4 large), bar colour and hatch = risk of bias (QUADAS-2 overall from --rob; grey = not
assessed). Direction uses the sign after the optional `direction = flip` column, relative
to the null (0 for r, md, smd; 0.5 for AUC; 1 for ratios); null when the CI includes the
null or, without a CI, the estimate is in the trivial band. Proportions and single means
have no direction and are listed but not plotted. Written as harvest_plot.svg/.png plus
effect_direction.md (arrow table ▲ ▼ ◄► per Boon & Thomson 2021, with a direction-only
vote count and an exact sign test; significance is never counted).

Exit 0 on success, 1 on bad input. Needs numpy and matplotlib.
"""
from __future__ import annotations

import argparse
import csv
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
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

VERSION = "1.0.0"
NR = {"", "nr", "na", "n/a", "none", "-"}
C_SEQ = "#2a78d6"
C_TEXT, C_MUTED, C_GRID = "#0b0b0b", "#52514e", "#d9d8d4"
ROB_COLOUR = {"Low": "#009E73", "Unclear": "#E69F00", "High": "#D55E00", "": "#bbbbbb"}
ROB_HATCH = {"Low": "", "Unclear": "//", "High": "xx", "": "..."}
NULL = {"correlation": 0.0, "spearman": 0.0, "auc": 0.5, "md": 0.0, "mean_diff": 0.0, "smd": 0.0, "generic": 0.0, "logratio": 1.0}
# effect-size classes: 1 trivial, 2 small, 3 moderate, 4 large
CLASS_LABEL = {1: "trivial", 2: "small", 3: "moderate", 4: "large"}


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


def size_class(outcome, est):
    """Cohen 1988 for r and d; Hosmer & Lemeshow 2013 bands for AUC; Chen 2010 for odds ratios."""
    a = abs(est)
    if outcome in ("correlation", "spearman"):
        cuts = (0.1, 0.3, 0.5)
    elif outcome == "auc":
        a = abs(est - 0.5)
        cuts = (0.2, 0.3, 0.4)
    elif outcome in ("smd", "md", "mean_diff", "generic"):
        cuts = (0.2, 0.5, 0.8)       # md/generic are only classed when the row is on a d-like scale; see md note
    elif outcome == "logratio":
        a = abs(math.log(est)) if est > 0 else 0
        cuts = (math.log(1.5), math.log(2.5), math.log(4))
    else:
        return None
    return 1 + sum(a >= c for c in cuts)


def direction(outcome, est, lo, hi, flip):
    null = NULL.get(outcome)
    if null is None or est is None:
        return None
    sign = -1 if flip else 1
    if lo is not None and hi is not None:
        if (lo - null) * sign > 0 and (hi - null) * sign > 0:
            return "positive"
        if (lo - null) * sign < 0 and (hi - null) * sign < 0:
            return "negative"
        return "null"
    cls = size_class(outcome, est)
    if cls is not None and cls <= 1:
        return "null"
    return "positive" if (est - null) * sign > 0 else ("negative" if (est - null) * sign < 0 else "null")


def rob_overall(rob_rows):
    by = defaultdict(dict)
    for r in rob_rows:
        by[r.get("study_id", "")][r.get("domain", "")] = (r.get("rob_judgement") or "").strip().title()
    out = {}
    for sid, doms in by.items():
        js = list(doms.values())
        out[sid] = "High" if "High" in js else ("Unclear" if ("Unclear" in js or len(js) < 4) else "Low")
    return out


def sign_test(pos, neg):
    """Two-sided exact binomial test of pos vs neg (p = 0.5), null rows excluded."""
    n = pos + neg
    if n == 0:
        return None
    k = min(pos, neg)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(1.0, p)


def build_map(rows, rcol, ccol, dataset_of):
    cells = defaultdict(lambda: defaultdict(dict))  # row -> col -> dataset -> max n
    for r in rows:
        rv, cv = r.get(rcol, "") or "NR", r.get(ccol, "") or "NR"
        ds = dataset_of.get(r["study_id"], r["study_id"])
        n = to_int(r.get("n")) or 0
        cells[rv][cv][ds] = max(cells[rv][cv].get(ds, 0), n)
    rows_ = sorted(cells)
    cols_ = sorted({c for r in cells.values() for c in r})
    return cells, rows_, cols_


def draw_map(cells, rows_, cols_, title, outbase):
    kmax = max((len(d) for r in cells.values() for d in r.values()), default=1)
    cmap = LinearSegmentedColormap.from_list("seq", ["#ffffff", C_SEQ])
    fig, ax = plt.subplots(figsize=(max(7.0, 2.4 + 1.6 * len(cols_)), 1.9 + 0.62 * len(rows_)))
    for i, rv in enumerate(rows_):
        for j, cv in enumerate(cols_):
            d = cells.get(rv, {}).get(cv, {})
            k = len(d)
            frac = k / kmax if kmax else 0
            ax.add_patch(plt.Rectangle((j, len(rows_) - 1 - i), 1, 1, facecolor=cmap(0.15 + 0.85 * frac) if k else "#ffffff",
                                       edgecolor="white", linewidth=2))
            if k:
                ax.text(j + 0.5, len(rows_) - 1 - i + 0.5, f"k = {k}\nn = {sum(d.values())}", ha="center", va="center", fontsize=8,
                        color="white" if frac > 0.6 else C_TEXT)
            else:
                ax.text(j + 0.5, len(rows_) - 1 - i + 0.5, "—", ha="center", va="center", fontsize=8, color=C_MUTED)
    ax.set_xlim(0, len(cols_))
    ax.set_ylim(0, len(rows_))
    ax.set_xticks([j + 0.5 for j in range(len(cols_))])
    ax.set_xticklabels([c[:28] for c in cols_], fontsize=8, rotation=20, ha="right")
    ax.set_yticks([len(rows_) - 1 - i + 0.5 for i in range(len(rows_))])
    ax.set_yticklabels([r[:40] for r in rows_], fontsize=8)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.suptitle(title, fontsize=10, x=0.01, ha="left")
    fig.text(0.01, 0.01, "k = independent datasets (papers sharing participants count once); n = participants summed once per dataset.\n"
             "Shade = k. Empty cell (—) = no included study.", fontsize=7, color=C_MUTED, va="bottom")
    fig.subplots_adjust(left=min(0.45, 0.12 + 0.012 * max((len(r) for r in rows_), default=10)), right=0.98, top=0.88,
                        bottom=min(0.45, 0.22 + 0.9 / (1.9 + 0.62 * len(rows_))))
    fig.savefig(outbase + ".svg", metadata={"Date": None})
    fig.savefig(outbase + ".png", dpi=200, metadata={"Software": None})
    plt.close(fig)


def map_markdown(cells, rows_, cols_, rlabel, clabel):
    md = [f"| {rlabel} \\ {clabel} | " + " | ".join(cols_) + " |", "|---|" + "---|" * len(cols_)]
    for rv in rows_:
        md.append(f"| {rv} | " + " | ".join(
            (f"k={len(cells[rv][cv])}, n={sum(cells[rv][cv].values())}" if cells.get(rv, {}).get(cv) else "—") for cv in cols_) + " |")
    return md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dta", help="dta.csv from the data-extraction skill")
    ap.add_argument("--effects", help="effects.csv from the data-extraction skill")
    ap.add_argument("--studies", help="studies.csv with dataset_id (the --assign copy from independent_datasets.py)")
    ap.add_argument("--rob", help="QUADAS-2 CSV (study_id, domain, rob_judgement) for bar colour in the harvest plot")
    ap.add_argument("--rows", default="instrument", help="row column of the map (default %(default)s)")
    ap.add_argument("--cols", default=None, help="column of the map (default reference_standard for dta, comparator for effects)")
    ap.add_argument("--out-dir", default="analysis/synthesis")
    ap.add_argument("--no-harvest", action="store_true", help="skip the harvest plot and effect-direction table")
    ap.add_argument("--version", action="version", version=VERSION)
    args = ap.parse_args(argv)
    if not args.dta and not args.effects:
        sys.exit("error: give --dta and/or --effects")

    dataset_of, labels, n_of = {}, {}, {}
    if args.studies:
        _, srows = read_csv(args.studies)
        for s in srows:
            if not is_blank(s.get("dataset_id")):
                dataset_of[s["study_id"]] = s["dataset_id"]
            labels[s["study_id"]] = s.get("label") or s["study_id"]
            n_of[s["study_id"]] = to_int(s.get("n"))
    rob = {}
    if args.rob:
        _, rrows = read_csv(args.rob)
        rob = rob_overall(rrows)
    os.makedirs(args.out_dir, exist_ok=True)
    plt.rcParams.update({"svg.hashsalt": "narrative-synthesis", "font.size": 8.5, "axes.edgecolor": "#888888", "hatch.linewidth": 0.6})
    written = []

    for src, path, default_col in (("dta", args.dta, "reference_standard"), ("effects", args.effects, "comparator")):
        if not path:
            continue
        if not os.path.exists(path):
            sys.exit(f"error: {path} not found")
        fields, rows = read_csv(path)
        ccol = args.cols or default_col
        for c in ("study_id", args.rows, ccol):
            if c not in fields:
                sys.exit(f"error: {path} lacks the '{c}' column")
        for r in rows:
            if is_blank(r.get("n")) and n_of.get(r["study_id"]):
                r["n"] = str(n_of[r["study_id"]])
        cells, rows_, cols_ = build_map(rows, args.rows, ccol, dataset_of)
        base = os.path.join(args.out_dir, f"evidence_map_{src}")
        draw_map(cells, rows_, cols_, f"Evidence map: {args.rows} x {ccol} ({src}.csv)", base)
        md = [f"# Evidence map ({src}.csv): {args.rows} x {ccol}", "",
              "Cell = number of independent datasets (k) and participants summed once per dataset (n). "
              "Papers that share participants count once (dataset_id from studies.csv; study_id when absent). "
              "An empty cell is a gap in the evidence, worth a sentence in the Results.", ""] + map_markdown(cells, rows_, cols_, args.rows, ccol) + [""]
        with open(base + ".md", "w", encoding="utf-8") as fh:
            fh.write("\n".join(md))
        written += [base + ".svg/.png/.md"]
        if src == "effects" and not args.no_harvest:
            written += harvest(rows, dataset_of, labels, rob, args)

    print("wrote: " + ", ".join(written))
    return 0


def harvest(rows, dataset_of, labels, rob, args):
    groups = OrderedDict()
    skipped = []
    for r in sorted(rows, key=lambda r: (r.get("instrument", ""), r.get("comparator", ""), r.get("outcome_type", ""), r.get("label", ""), r["study_id"])):
        ot = (r.get("outcome_type") or "").lower()
        if ot == "mean_diff":
            ot = "md"
        if ot == "correlation" and "spearman" in (r.get("measure") or "").lower():
            ot = "spearman"
        est, lo, hi = num(r.get("estimate")), num(r.get("ci_low")), num(r.get("ci_high"))
        if ot not in NULL or est is None:
            skipped.append((r.get("label") or labels.get(r["study_id"], r["study_id"]), ot or "NR", r.get("measure", "")))
            continue
        key = (r.get("instrument", "") or "NR", r.get("comparator", "") or "NR", ot)
        flip = (r.get("direction") or "").lower() == "flip"
        cls = size_class(ot, est)
        if ot in ("md", "generic") and not (r.get("measure") or "").lower().startswith(("d", "hedges", "cohen", "smd")):
            cls = None  # raw mean differences have no universal size class
        groups.setdefault(key, []).append({
            "study_id": r["study_id"], "label": r.get("label") or labels.get(r["study_id"], r["study_id"]),
            "dataset_id": dataset_of.get(r["study_id"], r["study_id"]), "n": to_int(r.get("n")),
            "estimate": est, "lo": lo, "hi": hi, "measure": r.get("measure", ""),
            "direction": direction(ot, est, lo, hi, flip), "class": cls, "rob": rob.get(r["study_id"], ""), "flip": flip,
        })
    if not groups:
        print("note: no effects rows with a defined null (correlation, auc, md, smd, generic, logratio); harvest plot skipped", file=sys.stderr)
        return []

    # effect-direction table + vote count
    arrow = {"positive": "▲", "negative": "▼", "null": "◄►", None: "?"}
    md = ["# Effect direction by outcome (effects.csv)", "",
          "▲ effect in the expected direction (CI excludes the null, or no CI and effect beyond the trivial band); "
          "▼ opposite direction; ◄► null, unclear or CI includes the null (Boon & Thomson 2021). "
          "Size class: Cohen 1988 for r and d; AUC 0.5-0.7 trivial, 0.7-0.8 small, 0.8-0.9 moderate, >= 0.9 large (Hosmer & Lemeshow); "
          "OR 1.5 / 2.5 / 4 (Chen 2010). Vote counting is on direction only and is a last resort "
          "(Cochrane Handbook ch. 12): it ignores size and precision and must never count p < 0.05.", ""]
    for key, items in groups.items():
        inst, comp, ot = key
        md += [f"## {inst} vs {comp} ({ot})", "",
               "| Study | Dataset | n | Estimate (95% CI) | Direction | Size class | QUADAS-2 overall |", "|---|---|---|---|---|---|---|"]
        votes = defaultdict(set)
        for it in items:
            ci = "" if it["lo"] is None else f" ({it['lo']:.2f} to {it['hi']:.2f})"
            md.append(f"| {it['label']} | {it['dataset_id']} | {it['n'] or 'NR'} | {it['estimate']:.2f}{ci}{' (flipped)' if it['flip'] else ''} | "
                      f"{arrow[it['direction']]} {it['direction'] or 'undetermined'} | {CLASS_LABEL.get(it['class'], 'n/a')} | {it['rob'] or 'not assessed'} |")
            votes[it["direction"]].add(it["dataset_id"])
        pos, neg, nul = len(votes["positive"]), len(votes["negative"]), len(votes["null"])
        p = sign_test(pos, neg)
        k = len({it["dataset_id"] for it in items})
        md += ["", f"Direction count over {k} independent dataset(s): {pos} positive, {neg} negative, {nul} null/unclear"
               + (f"; exact sign test (positive vs negative) p = {p:.3f}" if p is not None and (pos + neg) >= 2 else "; sign test not computed (fewer than 2 directional results)")
               + ". Report this only if neither a pooled estimate nor a structured summary of effect sizes is possible, and say so.", ""]
    if skipped:
        md += ["## Not plotted (no defined null)", ""] + [f"- {l}: {ot} ({m})" for l, ot, m in skipped] + [""]
    with open(os.path.join(args.out_dir, "effect_direction.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    # harvest plot
    n_g = len(groups)
    fig, axes = plt.subplots(n_g, 1, figsize=(8.5, 1.1 + 1.9 * n_g), squeeze=False)
    cols = [("negative", "Opposite direction"), ("null", "Null / unclear"), ("positive", "Expected direction")]
    for ax, (key, items) in zip(axes[:, 0], groups.items()):
        inst, comp, ot = key
        x = 0
        xticks, xlabels = [], []
        for ci, (dname, dlabel) in enumerate(cols):
            start = x
            sub = [it for it in items if it["direction"] == dname]
            for it in sub:
                h = it["class"] or 1
                ax.bar(x, h, width=0.8, color=ROB_COLOUR.get(it["rob"], "#bbbbbb"), hatch=ROB_HATCH.get(it["rob"], "..."),
                       edgecolor="white", linewidth=0.8, zorder=3)
                ax.text(x, h + 0.08, f"{it['estimate']:.2f}", ha="center", va="bottom", fontsize=6.5, color=C_TEXT)
                xticks.append(x)
                xlabels.append(it["label"][:18] + (f"\n(n={it['n']})" if it["n"] else ""))
                x += 1
            width = max(len(sub), 1)
            ax.axvspan(start - 0.5, start - 0.5 + width, color="#f1f1f1" if ci % 2 == 0 else "#ffffff", zorder=0, linewidth=0)
            ax.text(start - 0.5 + width / 2, 4.55, dlabel, ha="center", va="bottom", fontsize=7.5, color=C_MUTED)
            x = start + width + 0.6
        ax.set_xlim(-0.6, x - 0.6)
        ax.set_ylim(0, 4.9)
        ax.set_yticks([1, 2, 3, 4])
        ax.set_yticklabels(["trivial", "small", "moderate", "large"], fontsize=7)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels, fontsize=7)
        ax.tick_params(length=0)
        ax.set_ylabel("effect size class", fontsize=7.5)
        ax.set_title(f"{inst} vs {comp} ({ot})", fontsize=9, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.grid(axis="y", color=C_GRID, linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)
    handles = [Patch(facecolor=ROB_COLOUR[k], hatch=ROB_HATCH[k], edgecolor="white", label=k or "not assessed") for k in ("Low", "Unclear", "High", "")]
    fig.legend(handles=handles, loc="upper right", fontsize=7.5, frameon=False, title="QUADAS-2 overall", title_fontsize=7.5, ncol=4, bbox_to_anchor=(0.99, 1.0))
    fig.suptitle("Harvest plot: direction and size of effect per study, by risk of bias (no pooling)", fontsize=10, x=0.01, ha="left")
    fig.text(0.01, 0.005, "Bar height = effect-size class; colour and hatch = QUADAS-2 overall judgement. Direction only; significance is not counted.",
             fontsize=7, color=C_MUTED)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.86 if n_g > 1 else 0.78, bottom=0.18 / n_g + 0.05, hspace=0.75)
    base = os.path.join(args.out_dir, "harvest_plot")
    fig.savefig(base + ".svg", metadata={"Date": None})
    fig.savefig(base + ".png", dpi=200, metadata={"Software": None})
    plt.close(fig)
    return [base + ".svg/.png", os.path.join(args.out_dir, "effect_direction.md")]


if __name__ == "__main__":
    sys.exit(main())
