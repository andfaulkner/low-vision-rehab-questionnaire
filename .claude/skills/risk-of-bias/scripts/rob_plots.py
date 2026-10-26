#!/usr/bin/env python3
"""Make QUADAS-2 risk-of-bias figures and tables from a per-study-by-domain CSV.

Input: a CSV in the layout of assets/quadas2_template.csv (one row per study x
domain, with signalling-question answers, judgements, quote and page).

Output (in --out-dir, default analysis/risk_of_bias/):
  quadas2_traffic_light.svg/.png  studies x domains, risk of bias and applicability
  quadas2_summary.svg/.png        stacked % Low / Unclear / High per domain
  quadas2_table.md                per-study judgement table + summary counts
  quadas2_summary.csv             the summary counts behind the bar plot

The CSV is validated first (allowed judgement strings, every study has all four
domains exactly once, signalling answers Y/N/U/NA). Problems print to stderr and
the script exits 1. Missing quotes/pages and judgements that disagree with the
signalling-question algorithm are warnings unless --strict.

Run with `python3 -I` because the CSV is data, not code.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import OrderedDict

DOMAINS = ["Patient selection", "Index test", "Reference standard", "Flow and timing"]
APPLIC_DOMAINS = DOMAINS[:3]          # QUADAS-2 has no applicability judgement for flow and timing
SHORT = {"Patient selection": "D1", "Index test": "D2", "Reference standard": "D3", "Flow and timing": "D4"}
ASHORT = {"Patient selection": "A1", "Index test": "A2", "Reference standard": "A3"}
JUDGEMENTS = ["Low", "Unclear", "High"]  # drawing/stacking order
SIGNAL_COLS = ["signalling_q1", "signalling_q2", "signalling_q3", "signalling_q4"]
REQUIRED = ["study_id", "domain"] + SIGNAL_COLS + ["support_quote", "page", "rob_judgement", "applicability_judgement"]
# Okabe-Ito colours: pass the colour-blind checks (see references/validation.md).
# Colour is never the only cue: every mark also carries a symbol and the legend names it.
COLOURS = {"Low": "#009E73", "Unclear": "#E69F00", "High": "#D55E00"}
SYMBOLS = {"Low": "+", "Unclear": "?", "High": "−"}
TEXT_ON = {"Low": "white", "Unclear": "#0b0b0b", "High": "white"}

_DOMAIN_ALIASES = {}
for _d in DOMAINS:
    _DOMAIN_ALIASES[_d.casefold()] = _d
    _DOMAIN_ALIASES[SHORT[_d].casefold()] = _d
    _DOMAIN_ALIASES[(SHORT[_d] + " " + _d).casefold()] = _d
_DOMAIN_ALIASES.update({"flow & timing": "Flow and timing", "flow/timing": "Flow and timing"})


class Problems:
    def __init__(self, strict: bool):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.strict = strict

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        (self.errors if self.strict else self.warnings).append(msg)

    def report(self) -> None:
        for w in self.warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        for e in self.errors:
            print(f"ERROR: {e}", file=sys.stderr)


def norm_domain(raw: str):
    key = " ".join(raw.strip().split()).casefold()
    key = key.replace("–", "-").replace(":", " ").replace("  ", " ")
    return _DOMAIN_ALIASES.get(key)


def norm_judgement(raw: str, allow_na: bool):
    key = raw.strip().casefold()
    if key in ("", "na", "n/a", "not applicable", "-"):
        return "NA" if allow_na else None
    for j in JUDGEMENTS:
        if key == j.casefold():
            return j
    return None


def norm_signal(raw: str):
    key = raw.strip().upper()
    if key in ("", "NA", "N/A"):
        return "NA" if key else ""
    if key in ("Y", "YES"):
        return "Y"
    if key in ("N", "NO"):
        return "N"
    if key in ("U", "UNCLEAR", "?"):
        return "U"
    return None


def expected_judgement(signals: list[str]):
    """QUADAS-2 rule: any 'no' -> consider High; all 'yes' -> Low; otherwise Unclear.
    NA answers are ignored. Returns None when no question was answered."""
    answered = [s for s in signals if s in ("Y", "N", "U")]
    if not answered:
        return None
    if "N" in answered:
        return "High"
    if all(s == "Y" for s in answered):
        return "Low"
    return "Unclear"


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise SystemExit(f"ERROR: {path} is empty")
        fields = [f.strip() for f in reader.fieldnames]
        rows = []
        for raw in reader:
            rows.append({k.strip(): (v or "").strip() for k, v in raw.items() if k is not None})
        return fields, rows


N_COLS = ("n", "n_analysed", "n_analyzed", "n_enrolled")       # first present column wins
LABEL_COLS = ("label", "citation", "study")


def load_studies(path: str | None, n_col: str | None = None, label_col: str | None = None) -> dict:
    """Optional study table keyed by study_id, e.g. analysis/extraction/studies.csv from the
    data-extraction skill. Sample size comes from --n-col or the first of N_COLS present;
    the display name from --label-col or the first of LABEL_COLS present."""
    if not path:
        return {}
    fields, rows = read_csv(path)
    if "study_id" not in fields:
        raise SystemExit(f"ERROR: {path} needs a study_id column")
    for name, want in (("--n-col", n_col), ("--label-col", label_col)):
        if want and want not in fields:
            raise SystemExit(f"ERROR: {path} has no column '{want}' ({name})")
    n_col = n_col or next((c for c in N_COLS if c in fields), None)
    label_col = label_col or next((c for c in LABEL_COLS if c in fields), None)
    out = {}
    for r in rows:
        out[r["study_id"]] = {"n": r.get(n_col, "") if n_col else "",
                              "label": r.get(label_col, "") if label_col else ""}
    return out


def validate(fields, rows, studies_meta, want_weight, prob: Problems):
    missing = [c for c in REQUIRED if c not in fields]
    if missing:
        prob.error("missing required column(s): " + ", ".join(missing))
        return OrderedDict()
    has_n = "n" in fields

    data: OrderedDict[str, dict] = OrderedDict()   # study_id -> {domain: rowinfo}
    for i, r in enumerate(rows, start=2):           # line numbers for humans (header is line 1)
        sid = r["study_id"]
        if not sid:
            prob.error(f"line {i}: empty study_id")
            continue
        dom = norm_domain(r["domain"])
        if dom is None:
            prob.error(f"line {i} ({sid}): unknown domain '{r['domain']}'; allowed: {', '.join(DOMAINS)}")
            continue
        entry = data.setdefault(sid, {})
        if dom in entry:
            prob.error(f"line {i} ({sid}): domain '{dom}' appears more than once")
            continue

        signals = []
        for c in SIGNAL_COLS:
            s = norm_signal(r[c])
            if s is None:
                prob.error(f"line {i} ({sid}/{dom}): {c}='{r[c]}' is not Y, N, U or NA")
                s = ""
            signals.append(s)
        if all(s in ("", "NA") for s in signals):
            prob.warn(f"line {i} ({sid}/{dom}): no signalling questions answered")

        rob = norm_judgement(r["rob_judgement"], allow_na=False)
        if rob is None:
            prob.error(f"line {i} ({sid}/{dom}): rob_judgement='{r['rob_judgement']}' is not Low, High or Unclear")
        app_allowed_na = dom == "Flow and timing"
        app = norm_judgement(r["applicability_judgement"], allow_na=app_allowed_na)
        if app is None:
            if app_allowed_na:
                prob.error(f"line {i} ({sid}/{dom}): applicability_judgement='{r['applicability_judgement']}' invalid")
            else:
                prob.error(f"line {i} ({sid}/{dom}): applicability_judgement='{r['applicability_judgement']}' is not Low, High or Unclear")
        elif app != "NA" and app_allowed_na:
            prob.warn(f"line {i} ({sid}/{dom}): QUADAS-2 has no applicability judgement for flow and timing; value ignored")
            app = "NA"

        exp = expected_judgement(signals)
        if rob and exp and exp != rob:
            answered = ", ".join(f"q{k + 1}={s}" for k, s in enumerate(signals) if s)
            prob.warn(f"line {i} ({sid}/{dom}): rob_judgement={rob} but the signalling answers ({answered}) imply {exp}; "
                      "explain the override in notes or fix the judgement")
        if not r["support_quote"]:
            prob.warn(f"line {i} ({sid}/{dom}): support_quote is empty; every judgement needs a quoted sentence")
        if not r["page"]:
            prob.warn(f"line {i} ({sid}/{dom}): page is empty")

        entry[dom] = {"signals": signals, "rob": rob, "app": app, "n": r.get("n", "") if has_n else "", "line": i}

    for sid, entry in data.items():
        absent = [d for d in DOMAINS if d not in entry]
        if absent:
            prob.error(f"{sid}: missing domain(s): {', '.join(absent)}")

    # sample sizes
    for sid, entry in data.items():
        n_vals = {e["n"] for e in entry.values() if e["n"]}
        meta_n = studies_meta.get(sid, {}).get("n", "")
        if meta_n:
            n_vals.add(meta_n)
        n = None
        if len(n_vals) > 1:
            prob.error(f"{sid}: conflicting sample sizes {sorted(n_vals)}")
        elif n_vals:
            raw = n_vals.pop()
            try:
                n = float(raw)
                if n <= 0:
                    raise ValueError
            except ValueError:
                prob.error(f"{sid}: n='{raw}' is not a positive number")
        if want_weight and n is None:
            prob.error(f"{sid}: --weight needs a sample size (n column in the CSV or --studies file)")
        entry["_n"] = n
        entry["_label"] = studies_meta.get(sid, {}).get("label", "") or sid
    return data


def overall_rob(entry):
    js = [entry[d]["rob"] for d in DOMAINS]
    if "High" in js:
        return "High"
    if "Unclear" in js:
        return "Unclear"
    return "Low"


def summarise(data, weighted):
    """Returns list of (block, domain, {judgement: (count, pct)})."""
    out = []
    for block, doms, key in (("Risk of bias", DOMAINS, "rob"), ("Applicability", APPLIC_DOMAINS, "app")):
        for d in doms:
            counts = {j: 0.0 for j in JUDGEMENTS}
            raw = {j: 0 for j in JUDGEMENTS}
            for sid, entry in data.items():
                j = entry[d][key]
                if j not in counts:
                    continue
                raw[j] += 1
                counts[j] += entry["_n"] if weighted else 1.0
            total = sum(counts.values())
            pct = {j: (100.0 * counts[j] / total if total else 0.0) for j in JUDGEMENTS}
            out.append((block, d, raw, pct))
    return out


def write_markdown(path, data, summary, weighted, source):
    lines = []
    lines.append(f"# QUADAS-2 assessments ({len(data)} studies)")
    lines.append("")
    lines.append(f"Source CSV: `{source}`. Judgements are the reviewer's (AI-drafted judgements must be confirmed before use; disclose AI assistance in Methods).")
    lines.append("")
    head = ["Study", "n"] + [f"{SHORT[d]} {d}" for d in DOMAINS] + [f"{ASHORT[d]} {d}" for d in APPLIC_DOMAINS] + ["Overall RoB"]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("|" + "|".join(["---"] * len(head)) + "|")
    for sid, entry in data.items():
        n = entry["_n"]
        n_txt = f"{int(n)}" if n is not None and float(n).is_integer() else (f"{n:g}" if n is not None else "")
        cells = [entry["_label"], n_txt]
        cells += [f"{SYMBOLS[entry[d]['rob']]} {entry[d]['rob']}" for d in DOMAINS]
        cells += [f"{SYMBOLS[entry[d]['app']]} {entry[d]['app']}" for d in APPLIC_DOMAINS]
        cells.append(overall_rob(entry))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("D1-D4: risk of bias; A1-A3: applicability concerns. + Low, ? Unclear, − High. "
                 "Overall RoB is High if any domain is High, else Unclear if any domain is Unclear, else Low.")
    lines.append("")
    lines.append("## Summary" + (" (weighted by sample size)" if weighted else ""))
    lines.append("")
    lines.append("| Block | Domain | Low n (%) | Unclear n (%) | High n (%) |")
    lines.append("|---|---|---|---|---|")
    for block, d, raw, pct in summary:
        cells = [block, d] + [f"{raw[j]} ({pct[j]:.0f}%)" for j in JUDGEMENTS]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_summary_csv(path, summary, weighted):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["block", "domain", "judgement", "count", "pct", "weighted"])
        for block, d, raw, pct in summary:
            for j in JUDGEMENTS:
                w.writerow([block, d, j, raw[j], f"{pct[j]:.2f}", "yes" if weighted else "no"])


def _setup_matplotlib():
    try:
        import matplotlib
    except ImportError:  # python3 -I hides the user site; re-add that one trusted dir
        import site
        sys.path.append(site.getusersitepackages())
        try:
            import matplotlib
        except ImportError:
            raise SystemExit("ERROR: matplotlib could not be imported. "
                             "install with: python3 -m pip install --user --break-system-packages matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "svg.hashsalt": "quadas2",      # deterministic SVG ids
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": "#888888",
        "savefig.dpi": 200,
    })
    return plt


def _save(fig, base, formats):
    for fmt in formats:
        meta = {"Date": None} if fmt == "svg" else None
        fig.savefig(f"{base}.{fmt}", format=fmt, bbox_inches="tight", metadata=meta)


def plot_traffic_light(plt, data, base, formats, title):
    from matplotlib.lines import Line2D
    sids = list(data.keys())
    n_st = len(sids)
    cols = [(SHORT[d], d, "rob") for d in DOMAINS]
    gap = 0.8
    xs = list(range(len(DOMAINS))) + [len(DOMAINS) + gap + k for k in range(len(APPLIC_DOMAINS))]
    cols += [(ASHORT[d], d, "app") for d in APPLIC_DOMAINS]
    fig_h = 0.42 * n_st + 2.2
    fig_w = 3.2 + 0.55 * len(xs)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    for yi, sid in enumerate(sids):
        y = n_st - 1 - yi
        entry = data[sid]
        for x, (short, d, key) in zip(xs, cols):
            j = entry[d][key]
            if j == "NA" or j is None:
                continue
            ax.scatter([x], [y], s=260, color=COLOURS[j], edgecolor="white", linewidth=1.2, zorder=3)
            ax.text(x, y, SYMBOLS[j], ha="center", va="center", color=TEXT_ON[j],
                    fontsize=10, fontweight="bold", zorder=4)
        if yi % 2 == 0:
            ax.axhspan(y - 0.5, y + 0.5, color="#f1f1f1", zorder=0, linewidth=0)
    labels = []
    for sid in sids:
        e = data[sid]
        n = e["_n"]
        labels.append(e["_label"] + (f" (n={int(n) if float(n).is_integer() else n:g})" if n is not None else ""))
    ax.set_yticks(range(n_st))
    ax.set_yticklabels(labels[::-1])
    ax.set_xticks(xs)
    ax.set_xticklabels([c[0] for c in cols])
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False, length=0)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.6, xs[-1] + 0.6)
    ax.set_ylim(-0.6, n_st - 0.4)
    for s in ("top", "right", "bottom", "left"):
        ax.spines[s].set_visible(False)
    ax.axvline((xs[3] + xs[4]) / 2, color="#bbbbbb", linewidth=0.8, zorder=1)
    # Block headers sit a fixed 26 points above the column labels, whatever the number of studies.
    for xc, txt in (((xs[0] + xs[3]) / 2, "Risk of bias"), ((xs[4] + xs[6]) / 2, "Applicability")):
        ax.annotate(txt, xy=(xc, 1), xycoords=("data", "axes fraction"), xytext=(0, 26),
                    textcoords="offset points", ha="center", va="bottom", fontsize=9.5)
    if title:
        ax.set_title(title, pad=46, fontsize=11)   # above the block headers
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOURS[j], markersize=11,
                      label=f"{SYMBOLS[j]} {j}") for j in JUDGEMENTS]
    leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02 - 0.3 / fig_h),
                    ncol=3, frameon=False, handletextpad=0.4, columnspacing=1.2)
    foot = ("D1 patient selection, D2 index test, D3 reference standard, D4 flow and timing; "
            "A1-A3 applicability concerns for D1-D3.")
    ax.annotate(foot, xy=(0.5, -0.06 - 0.6 / fig_h), xycoords="axes fraction", ha="center", va="top",
                fontsize=7.5, color="#444444", wrap=True)
    _save(fig, base, formats)
    plt.close(fig)


def plot_summary(plt, summary, base, formats, weighted, n_studies, title):
    rows = summary                      # already ordered: RoB D1-D4 then applicability A1-A3
    fig_h = 0.42 * len(rows) + 1.6
    fig, ax = plt.subplots(figsize=(7.2, fig_h))
    ylabels = []
    for yi, (block, d, raw, pct) in enumerate(rows):
        y = len(rows) - 1 - yi
        short = SHORT[d] if block == "Risk of bias" else ASHORT[d]
        ylabels.append(f"{short} {d}" + ("" if block == "Risk of bias" else " (applicability)"))
        left = 0.0
        for j in JUDGEMENTS:
            w = pct[j]
            if w <= 0:
                continue
            ax.barh(y, w, left=left, color=COLOURS[j], edgecolor="white", linewidth=1.5, height=0.72, zorder=3)
            if w >= 8:
                ax.text(left + w / 2, y, f"{SYMBOLS[j]} {w:.0f}%", ha="center", va="center",
                        color=TEXT_ON[j], fontsize=8, fontweight="bold", zorder=4)
            left += w
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(ylabels[::-1])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of studies" + (" (weighted by sample size)" if weighted else ""))
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#dddddd", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.axhline(len(rows) - len(DOMAINS) - 0.5, color="#bbbbbb", linewidth=0.8)
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=COLOURS[j], label=f"{SYMBOLS[j]} {j}") for j in JUDGEMENTS]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.18 - 0.2 / fig_h), ncol=3, frameon=False)
    ax.set_title(title or f"QUADAS-2 summary ({n_studies} studies)", fontsize=11)
    _save(fig, base, formats)
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="QUADAS-2 CSV (layout of assets/quadas2_template.csv)")
    p.add_argument("--out-dir", default="analysis/risk_of_bias", help="output directory (default: analysis/risk_of_bias)")
    p.add_argument("--studies", help="optional CSV keyed by study_id giving sample sizes and display names, e.g. "
                   "analysis/extraction/studies.csv (uses n/n_analysed/n_enrolled and label/citation)")
    p.add_argument("--n-col", help="column of --studies holding the sample size (default: first of n, n_analysed, n_enrolled)")
    p.add_argument("--label-col", help="column of --studies holding the display name (default: first of label, citation, study)")
    p.add_argument("--weight", action="store_true", help="weight the summary bars by sample size n")
    p.add_argument("--formats", default="svg,png", help="comma-separated figure formats (default: svg,png)")
    p.add_argument("--prefix", default="quadas2", help="output file name prefix (default: quadas2)")
    p.add_argument("--title", default="", help="title for the traffic-light plot (default: none)")
    p.add_argument("--strict", action="store_true", help="treat warnings (empty quotes, algorithm disagreements) as errors")
    p.add_argument("--check", action="store_true", help="validate only; write nothing")
    args = p.parse_args(argv)

    if not os.path.isfile(args.csv):
        print(f"ERROR: no such file: {args.csv}", file=sys.stderr)
        return 2
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    bad = [f for f in formats if f not in ("svg", "png", "pdf")]
    if bad:
        print(f"ERROR: unsupported format(s): {', '.join(bad)}", file=sys.stderr)
        return 2

    prob = Problems(args.strict)
    fields, rows = read_csv(args.csv)
    studies_meta = load_studies(args.studies, args.n_col, args.label_col)
    data = validate(fields, rows, studies_meta, args.weight, prob)
    if not data and not prob.errors:
        prob.error("no study rows found")
    prob.report()
    if prob.errors:
        print(f"{len(prob.errors)} error(s); nothing written.", file=sys.stderr)
        return 1
    print(f"Validated {len(data)} studies x {len(DOMAINS)} domains ({len(prob.warnings)} warning(s)).")
    if args.check:
        return 0

    plt = _setup_matplotlib()          # fail before writing anything if matplotlib is missing
    os.makedirs(args.out_dir, exist_ok=True)
    summary = summarise(data, args.weight)
    base = os.path.join(args.out_dir, args.prefix)
    write_markdown(base + "_table.md", data, summary, args.weight, args.csv)
    write_summary_csv(base + "_summary.csv", summary, args.weight)
    plot_traffic_light(plt, data, base + "_traffic_light", formats, args.title)
    plot_summary(plt, summary, base + "_summary", formats, args.weight, len(data), "")
    written = [base + "_table.md", base + "_summary.csv"]
    written += [f"{base}_traffic_light.{f}" for f in formats] + [f"{base}_summary.{f}" for f in formats]
    for w in written:
        print("wrote", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
