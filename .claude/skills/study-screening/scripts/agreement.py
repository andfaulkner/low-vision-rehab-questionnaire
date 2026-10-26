#!/usr/bin/env python3
"""Agreement between two screening decision columns: per-category counts,
percent agreement, Cohen's kappa with a 95% CI, PABAK, a confusion matrix and
the list of disagreements with the reason on each side.

    python3 -I agreement.py                                   # reviewer H vs AI N, title/abstract, xlsx
    python3 -I agreement.py data/LVR_screening_sheet_2_Screening.csv --maybe-as include
    python3 -I agreement.py --a "Title/abstract decision" --b "Independent T/A decision (AI)"
    python3 -I agreement.py --a N --b Q --maybe-as separate   # the two AI passes, 3x3
    python3 -I agreement.py --b-file analysis/screening/second_reviewer.csv \\
        --b "Second reviewer decision" --b-reason "Second reviewer reason"
    python3 -I agreement.py --stage ft --a "Full-text decision" \\
        --b-file analysis/screening/ft_ai_decisions.csv --b decision --b-reason reason
    python3 -I agreement.py -o analysis/screening --name ta_reviewer_vs_ai1

Source: the workbook (default data/LVR_screening_sheet_2.xlsx, read through
the screening-workbook helper, never saved) or a Screening CSV export whose
first line is the sheet name. Columns are chosen by header text or letter.
The reason column of H, J, N and Q is implied (I, K, O, R); give --a-reason /
--b-reason for anything else. --b-file joins a second CSV on its ID column,
for a second human reviewer's sheet or AI full-text decisions kept outside
the workbook.

Only rows where BOTH columns hold a decision are compared; rows with one side
empty are counted and listed as unpaired. Maybe is collapsed as --maybe-as
says (include: Maybe counts as Include, the PRISMA reading, since both go to
full text; exclude; separate: 3x3 kappa). Any decision or reason that is not
spelled exactly as in the Lists tab stops the script with exit status 2,
because the Counts formulas would silently miss it too.

Kappa: Cohen (1960); SE and CI from the large-sample variance of Fleiss,
Cohen and Everitt (1969); PABAK from Byrt, Bishop and Carlin (1993); the
prevalence and bias indexes for the 2x2 case from the same paper. Optional
--bootstrap N gives a percentile CI as a cross-check. See
references/screening-methods.md for interpretation and the known caveats.
"""

import argparse
import csv
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screening_common as sc  # noqa: E402

CATS_TA = ["Include", "Exclude", "Maybe"]


def collapse(value, how):
    if value == "Maybe":
        if how == "include":
            return "Include"
        if how == "exclude":
            return "Exclude"
    return value


def kappa_stats(matrix, cats):
    """matrix[i][j] = count with rater A = cats[i], rater B = cats[j]."""
    n = sum(sum(r) for r in matrix)
    k = len(cats)
    if n == 0:
        raise sc.ScreeningError("no paired decisions to compare")
    p = [[matrix[i][j] / n for j in range(k)] for i in range(k)]
    row = [sum(p[i]) for i in range(k)]
    col = [sum(p[i][j] for i in range(k)) for j in range(k)]
    po = sum(p[i][i] for i in range(k))
    pe = sum(row[i] * col[i] for i in range(k))
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    # Fleiss, Cohen & Everitt (1969) large-sample variance (the form in Fleiss 2003, eq. 18.15).
    if pe < 1:
        a = sum(p[i][i] * ((1 - pe) - (col[i] + row[i]) * (1 - po)) ** 2 for i in range(k))
        b = sum(p[i][j] * (col[i] + row[j]) ** 2 for i in range(k) for j in range(k) if i != j)
        c = (po * pe - 2 * pe + po) ** 2
        var = (a + (1 - po) ** 2 * b - c) / (n * (1 - pe) ** 4)
        se = math.sqrt(max(var, 0.0))
    else:
        se = float("nan")
    lo, hi = max(-1.0, kappa - 1.959964 * se), min(1.0, kappa + 1.959964 * se)
    pabak = (k * po - 1) / (k - 1) if k > 1 else float("nan")
    out = {"n": n, "k": k, "po": po, "pe": pe, "kappa": kappa, "se": se, "ci_low": lo, "ci_high": hi,
           "pabak": pabak, "row_marg": row, "col_marg": col}
    if k == 2:
        # Byrt 1993: prevalence index (a-d)/n, bias index (b-c)/n, with cats[0] the positive class.
        a_, b_, c_, d_ = matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1]
        out["prevalence_index"] = (a_ - d_) / n
        out["bias_index"] = (b_ - c_) / n
        out["b_recall_of_a_pos"] = a_ / (a_ + b_) if a_ + b_ else float("nan")
        out["b_specificity_vs_a"] = d_ / (c_ + d_) if c_ + d_ else float("nan")
    # Specific (per-category) agreement: 2*n_ii / (n_i. + n_.i)
    out["specific"] = {}
    for i, cat in enumerate(cats):
        denom = (row[i] + col[i]) * n
        out["specific"][cat] = (2 * matrix[i][i] / denom) if denom else float("nan")
    return out


def bootstrap_ci(pairs, cats, reps, seed):
    rng = random.Random(seed)
    idx = {c: i for i, c in enumerate(cats)}
    ks = []
    n = len(pairs)
    for _ in range(reps):
        m = [[0] * len(cats) for _ in cats]
        for _ in range(n):
            a, b = pairs[rng.randrange(n)]
            m[idx[a]][idx[b]] += 1
        try:
            ks.append(kappa_stats(m, cats)["kappa"])
        except (ZeroDivisionError, sc.ScreeningError):
            continue
    ks = [x for x in ks if not math.isnan(x)]
    if len(ks) < 10:
        return float("nan"), float("nan")
    ks.sort()
    return ks[int(0.025 * len(ks))], ks[min(len(ks) - 1, int(0.975 * len(ks)))]


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "NA"
    return ("%%.%df" % nd) % x


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default=None, help="xlsx or Screening CSV (default: data/LVR_screening_sheet_2.xlsx)")
    ap.add_argument("--stage", choices=["ta", "ft"], default="ta", help="which stage's allowed values apply (default ta)")
    ap.add_argument("--a", help="first decision column, header text or letter (default H at ta, J at ft)")
    ap.add_argument("--b", help="second decision column (default N at ta; required at ft)")
    ap.add_argument("--a-reason", help="reason column for --a (implied for H/J/N/Q)")
    ap.add_argument("--b-reason", help="reason column for --b (implied for H/J/N/Q; name it for --b-file)")
    ap.add_argument("--b-file", help="CSV holding --b (and --b-reason) keyed by an ID column, joined to the source")
    ap.add_argument("--a-label", help="label for rater A in the report (default: the column header)")
    ap.add_argument("--b-label", help="label for rater B in the report")
    ap.add_argument("--maybe-as", choices=["include", "exclude", "separate"], default="include",
                    help="how to treat Maybe before computing agreement (default include)")
    ap.add_argument("--lists", help="Lists CSV to validate against when the source is a CSV")
    ap.add_argument("--bootstrap", type=int, default=0, metavar="N", help="also give a percentile bootstrap CI from N resamples")
    ap.add_argument("--seed", type=int, default=20261004, help="bootstrap seed (default 20261004)")
    ap.add_argument("-o", "--out-dir", help="write <name>.md, <name>_summary.csv, <name>_confusion.csv and <name>_disagreements.csv here (else Markdown to stdout)")
    ap.add_argument("--name", help="base name of the output files (default from stage and columns)")
    args = ap.parse_args()

    try:
        t = sc.load_table(args.source, args.lists)
    except (sc.ScreeningError, Exception) as e:
        sc.die(str(e))
    a_name = args.a or ("Title/abstract decision" if args.stage == "ta" else "Full-text decision")
    if args.b is None and not args.b_file:
        if args.stage == "ft":
            sc.die("at the full-text stage give --b (or --b-file with --b): the workbook has no AI full-text columns")
        args.b = "Suggested decision (AI)"
    decisions_ok, reasons_ok = sc.allowed_values(t.lists, args.stage)
    if args.stage == "ft" and args.maybe_as == "separate":
        args.maybe_as = "include"  # no Maybe at FT; keep the 2x2

    try:
        a_idx = t.col_index(a_name)
        a_letter = sc.col_letter(a_idx)
        a_reason = args.a_reason or sc.REASON_FOR_DECISION.get(a_letter)
        a_reason_idx = t.col_index(a_reason) if a_reason else None
    except sc.ScreeningError as e:
        sc.die(str(e))

    # Rater B: a column of the source, or a column of --b-file joined on ID.
    b_values, b_reasons = {}, {}
    if args.b_file:
        if not args.b:
            sc.die("--b-file needs --b naming the decision column in that file")
        try:
            fields, rows = sc.read_decisions_csv(args.b_file)
        except (sc.ScreeningError, OSError) as e:
            sc.die(str(e))
        key_b = args.b.strip().casefold()
        key_r = (args.b_reason or "").strip().casefold()
        if key_b not in fields:
            sc.die("%s has no column %r; columns: %s" % (args.b_file, args.b, ", ".join(fields.values())))
        if key_r and key_r not in fields:
            sc.die("%s has no column %r" % (args.b_file, args.b_reason))
        if "id" not in fields:
            sc.die("%s needs an ID column to join on" % args.b_file)
        for r in rows:
            rid = r.get("id", "").strip()
            if not rid.isdigit():
                continue
            rid = int(rid)
            if rid in b_values:
                sc.die("%s lists ID %d twice" % (args.b_file, rid))
            b_values[rid] = r.get(key_b, "").strip()
            b_reasons[rid] = r.get(key_r, "").strip() if key_r else ""
        b_label = args.b_label or "%s (%s)" % (fields[key_b], os.path.basename(args.b_file))
        b_letter = None
    else:
        try:
            b_idx = t.col_index(args.b)
            b_letter = sc.col_letter(b_idx)
            b_reason = args.b_reason or sc.REASON_FOR_DECISION.get(b_letter)
            b_reason_idx = t.col_index(b_reason) if b_reason else None
        except sc.ScreeningError as e:
            sc.die(str(e))
        for rid, row in t.records():
            b_values[rid] = (row[b_idx] if b_idx < len(row) else "").strip()
            b_reasons[rid] = (row[b_reason_idx] if b_reason_idx is not None and b_reason_idx < len(row) else "").strip()
        b_label = args.b_label or t.header[b_idx]
    a_label = args.a_label or t.header[a_idx]

    # Collect, validate.
    bad, pairs, unpaired_a, unpaired_b, raw = [], [], [], [], []
    title_idx = t.col_index("Title") if "Title" in t.header else None
    for rid, row in t.records():
        av = (row[a_idx] if a_idx < len(row) else "").strip()
        ar = (row[a_reason_idx] if a_reason_idx is not None and a_reason_idx < len(row) else "").strip()
        bv = b_values.get(rid, "")
        br = b_reasons.get(rid, "")
        for who, v in (("A", av), ("B", bv)):
            if v and v not in decisions_ok:
                hint = sc.nearest(v, decisions_ok)
                bad.append("ID %d, rater %s: decision %r is not in Lists%s" % (rid, who, v, (" (did you mean %r?)" % hint) if hint else ""))
        for who, v in (("A", ar), ("B", br)):
            if v and v not in reasons_ok:
                hint = sc.nearest(v, reasons_ok)
                bad.append("ID %d, rater %s: reason %r is not in Lists%s" % (rid, who, v, (" (did you mean %r?)" % hint) if hint else ""))
        if av and bv:
            title = (row[title_idx] if title_idx is not None and title_idx < len(row) else "").strip()
            raw.append((rid, av, ar, bv, br, title))
        elif av:
            unpaired_a.append(rid)
        elif bv:
            unpaired_b.append(rid)
    if bad:
        for b in bad:
            print("malformed: %s" % b, file=sys.stderr)
        print("error: %d malformed value(s); allowed decisions: %s; reasons from %s" %
              (len(bad), " | ".join(decisions_ok), t.lists_source), file=sys.stderr)
        sys.exit(2)
    if not raw:
        sc.die("no record has a decision in both %r and %r" % (a_label, b_label))

    cats = [c for c in CATS_TA if c in decisions_ok]
    if args.maybe_as != "separate":
        cats = [c for c in cats if c != "Maybe"]
    idx = {c: i for i, c in enumerate(cats)}
    matrix = [[0] * len(cats) for _ in cats]
    pairs = []
    for rid, av, ar, bv, br, title in raw:
        ca, cb = collapse(av, args.maybe_as), collapse(bv, args.maybe_as)
        matrix[idx[ca]][idx[cb]] += 1
        pairs.append((ca, cb))
    try:
        st = kappa_stats(matrix, cats)
    except sc.ScreeningError as e:
        sc.die(str(e))
    boot = bootstrap_ci(pairs, cats, args.bootstrap, args.seed) if args.bootstrap else None

    disagreements = [(rid, av, ar, bv, br, title) for rid, av, ar, bv, br, title in raw
                     if collapse(av, args.maybe_as) != collapse(bv, args.maybe_as)]
    raw_diff = sum(1 for rid, av, ar, bv, br, _ in raw if av != bv)
    both_ex = [(ar, br) for rid, av, ar, bv, br, _ in raw if av == "Exclude" and bv == "Exclude"]
    same_reason = sum(1 for ar, br in both_ex if ar and ar == br)
    counts_a = {c: sum(1 for r in raw if r[1] == c) for c in decisions_ok}
    counts_b = {c: sum(1 for r in raw if r[3] == c) for c in decisions_ok}

    # ---- Markdown ----
    L = []
    stage_name = "title/abstract" if args.stage == "ta" else "full text"
    L.append("# Screening agreement: %s vs %s (%s)" % (a_label, b_label, stage_name))
    L.append("")
    L.append("Source: `%s`; Lists from %s; Maybe treated as **%s**." % (sc.nice_path(t.source), t.lists_source, args.maybe_as))
    L.append("Records with a decision on both sides: **%d** (A only: %d, B only: %d, neither: %d)." %
             (len(raw), len(unpaired_a), len(unpaired_b), len(t.records()) - len(raw) - len(unpaired_a) - len(unpaired_b)))
    L.append("")
    L.append("## Per-category counts (paired records, before collapsing)")
    L.append("")
    L.append("| Decision | %s | %s |" % (a_label, b_label))
    L.append("|---|---:|---:|")
    for c in decisions_ok:
        L.append("| %s | %d | %d |" % (c, counts_a[c], counts_b[c]))
    L.append("")
    L.append("## Confusion matrix (rows: %s; columns: %s)" % (a_label, b_label))
    L.append("")
    L.append("| | " + " | ".join(cats) + " | Total |")
    L.append("|---|" + "---:|" * (len(cats) + 1))
    for i, c in enumerate(cats):
        L.append("| **%s** | " % c + " | ".join(str(x) for x in matrix[i]) + " | %d |" % sum(matrix[i]))
    L.append("| **Total** | " + " | ".join(str(sum(matrix[i][j] for i in range(len(cats)))) for j in range(len(cats))) + " | %d |" % st["n"])
    L.append("")
    L.append("## Agreement")
    L.append("")
    L.append("| Statistic | Value |")
    L.append("|---|---:|")
    L.append("| Observed agreement | %s (%d/%d) |" % (fmt(st["po"]), sum(matrix[i][i] for i in range(len(cats))), st["n"]))
    L.append("| Expected by chance | %s |" % fmt(st["pe"]))
    L.append("| Cohen's kappa | %s |" % fmt(st["kappa"]))
    L.append("| SE (Fleiss-Cohen-Everitt) | %s |" % fmt(st["se"]))
    L.append("| 95%% CI | %s to %s |" % (fmt(st["ci_low"]), fmt(st["ci_high"])))
    if boot:
        L.append("| 95%% bootstrap CI (%d resamples, seed %d) | %s to %s |" % (args.bootstrap, args.seed, fmt(boot[0]), fmt(boot[1])))
    L.append("| PABAK | %s |" % fmt(st["pabak"]))
    if "prevalence_index" in st:
        L.append("| Prevalence index (%s) | %s |" % (cats[0], fmt(st["prevalence_index"])))
        L.append("| Bias index | %s |" % fmt(st["bias_index"]))
        L.append("| %s recall of %s's %s | %s |" % (b_label, a_label, cats[0], fmt(st["b_recall_of_a_pos"])))
        L.append("| %s agreement on %s's %s | %s |" % (b_label, a_label, cats[1], fmt(st["b_specificity_vs_a"])))
    for c in cats:
        L.append("| Specific agreement, %s | %s |" % (c, fmt(st["specific"][c])))
    if both_ex:
        L.append("| Same exclusion reason when both Exclude | %d/%d (%s) |" % (same_reason, len(both_ex), fmt(same_reason / len(both_ex))))
    if args.maybe_as != "separate" and raw_diff != len(disagreements):
        L.append("| Raw decision differences hidden by collapsing Maybe | %d |" % (raw_diff - len(disagreements)))
    L.append("")
    L.append("Kappa bands are rough (Landis and Koch 1977; McHugh 2012) and kappa falls when one category dominates, "
             "so read it next to PABAK and the per-category figures; see references/screening-methods.md.")
    L.append("")
    L.append("## Disagreements (%d)" % len(disagreements))
    L.append("")
    if disagreements:
        L.append("| ID | %s | reason | %s | reason | Title |" % (a_label, b_label))
        L.append("|---:|---|---|---|---|---|")
        for rid, av, ar, bv, br, title in disagreements:
            tt = (title[:70] + "...") if len(title) > 73 else title
            L.append("| %d | %s | %s | %s | %s | %s |" % (rid, av, ar or "", bv, br or "", tt.replace("|", "/")))
    else:
        L.append("None.")
    if unpaired_a or unpaired_b:
        L.append("")
        L.append("## Unpaired")
        L.append("")
        if unpaired_a:
            L.append("- Only %s decided: IDs %s" % (a_label, ", ".join(str(x) for x in unpaired_a)))
        if unpaired_b:
            L.append("- Only %s decided: IDs %s" % (b_label, ", ".join(str(x) for x in unpaired_b)))
    L.append("")
    L.append("AI decisions are advisory; the reviewer's columns are the decisions of record, and the Methods must say AI assistance was used.")
    md = "\n".join(L) + "\n"

    if not args.out_dir:
        sys.stdout.write(md)
        return
    os.makedirs(args.out_dir, exist_ok=True)
    name = args.name or "%s_%s_vs_%s" % (args.stage, a_letter, b_letter or "file")
    name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    base = os.path.join(args.out_dir, name)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(md)
    with open(base + "_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["statistic", "value"])
        w.writerow(["stage", args.stage]); w.writerow(["rater_a", a_label]); w.writerow(["rater_b", b_label])
        w.writerow(["maybe_as", args.maybe_as]); w.writerow(["n_paired", st["n"]])
        w.writerow(["n_unpaired_a", len(unpaired_a)]); w.writerow(["n_unpaired_b", len(unpaired_b)])
        for c in decisions_ok:
            w.writerow(["count_a_%s" % c, counts_a[c]]); w.writerow(["count_b_%s" % c, counts_b[c]])
        for key in ("po", "pe", "kappa", "se", "ci_low", "ci_high", "pabak", "prevalence_index", "bias_index",
                    "b_recall_of_a_pos", "b_specificity_vs_a"):
            if key in st:
                w.writerow([key, fmt(st[key], 4)])
        if boot:
            w.writerow(["boot_ci_low", fmt(boot[0], 4)]); w.writerow(["boot_ci_high", fmt(boot[1], 4)])
        for c in cats:
            w.writerow(["specific_agreement_%s" % c, fmt(st["specific"][c], 4)])
        w.writerow(["n_disagreements", len(disagreements)])
        if both_ex:
            w.writerow(["same_reason_when_both_exclude", "%d/%d" % (same_reason, len(both_ex))])
    with open(base + "_confusion.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["%s \\ %s" % (a_label, b_label)] + cats)
        for i, c in enumerate(cats):
            w.writerow([c] + matrix[i])
    with open(base + "_disagreements.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ID", "a_decision", "a_reason", "b_decision", "b_reason", "title"])
        for rid, av, ar, bv, br, title in disagreements:
            w.writerow([rid, av, ar, bv, br, title])
    print("n=%d  agreement=%s  kappa=%s (95%% CI %s to %s)  PABAK=%s  disagreements=%d" %
          (st["n"], fmt(st["po"]), fmt(st["kappa"]), fmt(st["ci_low"]), fmt(st["ci_high"]), fmt(st["pabak"]), len(disagreements)))
    print("wrote %s.md, _summary.csv, _confusion.csv, _disagreements.csv" % sc.nice_path(base))


if __name__ == "__main__":
    main()
