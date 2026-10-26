#!/usr/bin/env python3
"""Flag probable overlapping cohorts among included studies and group them into
independent datasets, so a synthesis never counts the same participants twice.

    python3 -I independent_datasets.py analysis/extraction/studies.csv \
        [--screening data/LVR_screening_sheet_2_Screening.csv] [--dta analysis/extraction/dta.csv] \
        [--out-dir analysis/synthesis] [--assign [PATH]] [--merge high|probable|possible]

Signals checked for every pair of studies (details in SKILL.md and references/methods.md):
  cross-ref      the `cohort` or `notes` column of one study names the other ("same 385
                 participants as ID 128", "Wu 2024")                                   -> high
  cohort name    both studies name the same cohort/registry in `cohort`                -> high
  authors        surname overlap (Jaccard >= --author-threshold, or >= --min-shared
                 surnames) taken from an `authors` column or the Screening export
  identical n    same analysed n (or same n_enrolled)
  years/site     recruitment years overlap, or same country + setting
Confidence: high = cross-ref or cohort name; probable = authors + (identical n, or
overlapping years, or same site); possible = authors alone, or identical n + same
country. Pairs at or above --merge (default probable) are joined into one dataset_id
(union-find). Every grouping is a suggestion; the reviewer confirms it. A `dataset_id`
column already present and filled in studies.csv is treated as the reviewer's answer
and kept, with any disagreement reported.

Outputs (deterministic): <out-dir>/independent_datasets.csv (one row per study),
overlap_pairs.csv (every flagged pair with reasons), independent_datasets.md (groups
to confirm). --assign writes a copy of studies.csv with dataset_id and
dataset_confidence columns (default <out-dir>/studies_with_datasets.csv).

Exit 0 on success, 1 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

VERSION = "1.0.0"
LEVELS = {"high": 3, "probable": 2, "possible": 1}
NR = {"", "nr", "na", "n/a", "none", "-"}


def is_blank(s):
    return s is None or str(s).strip().lower() in NR


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def to_int(s):
    try:
        return int(float(str(s).strip()))
    except (TypeError, ValueError):
        return None


def read_csv(path, skip_title=False):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    if not lines:
        return [], []
    if skip_title and "," not in lines[0]:
        lines = lines[1:]  # the workbook exports start with a title line holding the sheet name
    reader = csv.DictReader(lines)
    fields = [f.strip() for f in (reader.fieldnames or [])]
    rows = []
    for r in reader:
        rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
    return fields, rows


def surnames(authors):
    """Surnames from 'Wu YH, Yu D, Legge GE' / 'Wu, Y. H.; Yu, D.' / 'Y.H. Wu; D. Yu' strings."""
    if is_blank(authors):
        return set()
    text = authors.replace(" and ", "; ").replace(" & ", "; ")
    parts = re.split(r";|\band\b", text) if ";" in text else None
    out = set()
    if parts is None:
        # comma-separated "Surname Initials" form; a comma after the surname ("Wu, Y. H.") also works
        chunks = [c.strip() for c in text.split(",") if c.strip()]
        i = 0
        while i < len(chunks):
            c = chunks[i]
            words = c.split()
            if len(words) == 1 and i + 1 < len(chunks) and re.fullmatch(r"[A-Z](\.|\s|[A-Z])*\.?", chunks[i + 1].replace(" ", "")):
                out.add(norm(c))          # "Wu" , "Y. H."
                i += 2
                continue
            out.add(norm(words[0]) if not re.fullmatch(r"[A-Z.\-]+", words[0]) or len(words) == 1 else norm(words[-1]))
            i += 1
    else:
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if "," in p:
                out.add(norm(p.split(",")[0]))
            else:
                words = p.split()
                out.add(norm(words[-1]) if re.fullmatch(r"[A-Z.\-]+", words[0]) else norm(words[0]))
    return {s for s in out if s and s not in {"et al", "al"}}


def years_in(text):
    return {int(y) for y in re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", text or "")}


def year_span(text):
    ys = years_in(text)
    return (min(ys), max(ys)) if ys else None


def label_tokens(label):
    m = re.match(r"\s*([A-Za-z'\-]+)\D*(\d{4})?", label or "")
    if not m:
        return None, None
    return norm(m.group(1)), m.group(2)


def cross_reference(a, b):
    """Does study a's cohort/notes text point at study b?"""
    text = " ".join(a.get(c, "") for c in ("cohort", "notes")).lower()
    if not text.strip():
        return None
    sid = b.get("study_id", "")
    if sid and re.search(r"\bid\s*[:#]?\s*%s\b" % re.escape(sid), text):
        return f"{a['label']} cohort/notes cite ID {sid}"
    surname, year = label_tokens(b.get("label", ""))
    if surname and year and re.search(r"\b%s\b[^.;]{0,40}\b%s\b" % (re.escape(surname), year), text):
        return f"{a['label']} cohort/notes cite {b['label']}"
    return None


def compare(a, b, args):
    reasons, level = [], 0

    xr = cross_reference(a, b) or cross_reference(b, a)
    if xr:
        reasons.append("cross-ref: " + xr)
        level = max(level, 3)

    ca, cb = norm(a.get("cohort")), norm(b.get("cohort"))
    if ca and cb and not is_blank(a.get("cohort")) and not is_blank(b.get("cohort")):
        if ca == cb or (len(ca) >= 10 and ca in cb) or (len(cb) >= 10 and cb in ca):
            reasons.append(f"same cohort name: '{a.get('cohort')}'")
            level = max(level, 3)

    sa, sb = a["_surnames"], b["_surnames"]
    shared = sa & sb
    jacc = len(shared) / len(sa | sb) if (sa | sb) else 0.0
    author_hit = bool(sa and sb) and (jacc >= args.author_threshold or len(shared) >= args.min_shared)
    if author_hit:
        reasons.append(f"authors: {len(shared)} shared surname(s) ({', '.join(sorted(shared))}); Jaccard {jacc:.2f}")

    na, nb = to_int(a.get("n")), to_int(b.get("n"))
    ea, eb = to_int(a.get("n_enrolled")), to_int(b.get("n_enrolled"))
    same_n = (na is not None and na == nb and na > 0) or (ea is not None and ea == eb and ea > 0)
    if same_n:
        reasons.append(f"identical n: {na if na is not None and na == nb else ea}")

    ya, yb = year_span(a.get("recruitment")), year_span(b.get("recruitment"))
    years_overlap = bool(ya and yb and ya[0] <= yb[1] and yb[0] <= ya[1])
    if years_overlap:
        reasons.append(f"recruitment years overlap: {ya[0]}-{ya[1]} vs {yb[0]}-{yb[1]}")

    same_country = norm(a.get("country")) and norm(a.get("country")) == norm(b.get("country"))
    same_site = bool(same_country and norm(a.get("setting")) and norm(a.get("setting")) == norm(b.get("setting")))
    if same_site:
        reasons.append(f"same country and setting: {a.get('country')}, {a.get('setting')}")

    if author_hit and (same_n or years_overlap or same_site):
        level = max(level, 2)
    elif author_hit or (same_n and same_country):
        level = max(level, 1)

    if args.dta_n and same_n is False:
        # identical per-analysis n in dta.csv for the same instrument x reference standard
        common = set(args.dta_n.get(a["study_id"], {})) & set(args.dta_n.get(b["study_id"], {}))
        for key in sorted(common):
            if args.dta_n[a["study_id"]][key] & args.dta_n[b["study_id"]][key]:
                n_eq = sorted(args.dta_n[a["study_id"]][key] & args.dta_n[b["study_id"]][key])[0]
                reasons.append(f"identical 2x2 n ({n_eq}) for {key[0]} vs {key[1]} in dta.csv")
                level = max(level, 2 if author_hit else 1)
                break
    return level, reasons


class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if (ra, rb) > (rb, ra):
                ra, rb = rb, ra
            self.parent[rb] = ra


def sort_key(sid):
    return (0, int(sid)) if sid.isdigit() else (1, sid)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("studies", help="studies.csv from the data-extraction skill")
    ap.add_argument("--screening", default="data/LVR_screening_sheet_2_Screening.csv",
                    help="Screening export supplying Authors per study_id ('' to skip; default %(default)s)")
    ap.add_argument("--dta", help="dta.csv; identical per-table n for the same instrument x reference standard is an extra signal")
    ap.add_argument("--out-dir", default="analysis/synthesis")
    ap.add_argument("--assign", nargs="?", const="__default__", metavar="PATH",
                    help="write a copy of studies.csv with dataset_id / dataset_confidence columns (default <out-dir>/studies_with_datasets.csv)")
    ap.add_argument("--merge", choices=list(LEVELS), default="probable", help="lowest confidence that joins two studies into one dataset (default %(default)s)")
    ap.add_argument("--author-threshold", type=float, default=0.5, help="Jaccard overlap of surname sets that counts as the same group (default %(default)s)")
    ap.add_argument("--min-shared", type=int, default=3, help="or at least this many shared surnames (default %(default)s)")
    ap.add_argument("--version", action="version", version=VERSION)
    args = ap.parse_args(argv)

    if not os.path.exists(args.studies):
        sys.exit(f"error: {args.studies} not found")
    fields, rows = read_csv(args.studies)
    for col in ("study_id", "label"):
        if col not in fields:
            sys.exit(f"error: studies.csv lacks the '{col}' column")
    if not rows:
        sys.exit("error: studies.csv has no rows")
    ids = [r["study_id"] for r in rows]
    if len(set(ids)) != len(ids):
        sys.exit("error: duplicate study_id in studies.csv")

    authors_by_id = {}
    if args.screening and os.path.exists(args.screening):
        _, srows = read_csv(args.screening, skip_title=True)
        authors_by_id = {r.get("ID", ""): r.get("Authors", "") for r in srows}
    elif args.screening:
        print(f"note: {args.screening} not found; author overlap uses the 'authors' column only", file=sys.stderr)

    for r in rows:
        r["_surnames"] = surnames(r.get("authors") or authors_by_id.get(r["study_id"], ""))
        if not r["_surnames"]:
            fa, _ = label_tokens(r["label"])
            r["_surnames"] = {fa} if fa else set()
    no_authors = [r["label"] for r in rows if len(r["_surnames"]) <= 1]
    if no_authors:
        print(f"note: author lists not found for {len(no_authors)} study/ies (first author from label only): {', '.join(no_authors)}", file=sys.stderr)

    args.dta_n = None
    if args.dta:
        _, drows = read_csv(args.dta)
        args.dta_n = defaultdict(lambda: defaultdict(set))
        for d in drows:
            n = to_int(d.get("n"))
            if n:
                args.dta_n[d.get("study_id", "")][(d.get("instrument", ""), d.get("reference_standard", ""))].add(n)

    rows.sort(key=lambda r: sort_key(r["study_id"]))
    pairs = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            level, reasons = compare(rows[i], rows[j], args)
            if level:
                pairs.append((rows[i], rows[j], level, reasons))

    uf = UnionFind(ids)
    existing = "dataset_id" in fields and any(not is_blank(r.get("dataset_id")) for r in rows)
    conflicts = []
    if existing:
        by_ds = defaultdict(list)
        for r in rows:
            if not is_blank(r.get("dataset_id")):
                by_ds[r["dataset_id"]].append(r["study_id"])
        for members in by_ds.values():
            for m in members[1:]:
                uf.union(members[0], m)
        for a, b, level, _ in pairs:
            if level >= LEVELS[args.merge] and uf.find(a["study_id"]) != uf.find(b["study_id"]) \
                    and not is_blank(a.get("dataset_id")) and not is_blank(b.get("dataset_id")):
                conflicts.append((a, b, level))
    else:
        for a, b, level, _ in pairs:
            if level >= LEVELS[args.merge]:
                uf.union(a["study_id"], b["study_id"])

    groups = defaultdict(list)
    for r in rows:
        groups[uf.find(r["study_id"])].append(r)
    ordered = sorted(groups.values(), key=lambda g: sort_key(min((m["study_id"] for m in g), key=sort_key)))
    ds_of = {}
    for k, g in enumerate(ordered, 1):
        name = None
        if existing:
            names = {m.get("dataset_id") for m in g if not is_blank(m.get("dataset_id"))}
            name = sorted(names)[0] if names else None
        name = name or f"D{k:02d}"
        for m in g:
            ds_of[m["study_id"]] = name

    pair_level = defaultdict(dict)
    pair_reasons = defaultdict(list)
    for a, b, level, reasons in pairs:
        for x, y in ((a, b), (b, a)):
            pair_level[x["study_id"]][y["study_id"]] = level
            pair_reasons[x["study_id"]].append(f"{y['label']} ({[k for k, v in LEVELS.items() if v == level][0]}): " + "; ".join(reasons))

    os.makedirs(args.out_dir, exist_ok=True)
    inv = {v: k for k, v in LEVELS.items()}
    per_study = []
    for r in rows:
        members = [m for m in groups[uf.find(r["study_id"])] if m is not r]
        if existing and not is_blank(r.get("dataset_id")):
            conf = "reviewer"
        elif members:
            conf = inv[min(pair_level[r["study_id"]].get(m["study_id"], LEVELS[args.merge]) for m in members)]
        else:
            conf = "independent"
        per_study.append({
            "study_id": r["study_id"], "label": r["label"], "dataset_id": ds_of[r["study_id"]],
            "dataset_confidence": conf,
            "grouped_with": "; ".join(m["label"] for m in members),
            "flagged_pairs": " | ".join(pair_reasons[r["study_id"]]),
            "n": r.get("n", ""), "reviewer_confirmed": "yes" if conf == "reviewer" else "",
        })
    with open(os.path.join(args.out_dir, "independent_datasets.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_study[0].keys()))
        w.writeheader()
        w.writerows(per_study)
    with open(os.path.join(args.out_dir, "overlap_pairs.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["study_id_a", "label_a", "study_id_b", "label_b", "confidence", "merged", "reasons"])
        for a, b, level, reasons in sorted(pairs, key=lambda p: (-p[2], sort_key(p[0]["study_id"]), sort_key(p[1]["study_id"]))):
            w.writerow([a["study_id"], a["label"], b["study_id"], b["label"], inv[level],
                        "yes" if ds_of[a["study_id"]] == ds_of[b["study_id"]] else "no", " | ".join(reasons)])

    n_multi = sum(1 for g in ordered if len(g) > 1)
    md = [f"# Independent datasets ({len(ordered)} from {len(rows)} studies)", "",
          f"Grouping rule: pairs at confidence >= **{args.merge}** share a dataset_id. "
          "These are suggestions from surname, cohort, n, year and site matching; the reviewer confirms "
          "each grouping against the papers and records the decision in the `dataset_id` column of "
          "studies.csv (the `--assign` copy is the place to do it). Confirmed groupings are reported in "
          "the Methods as the unit of counting for the synthesis.", "",
          "| dataset_id | studies | confidence | why |", "|---|---|---|---|"]
    for g in ordered:
        name = ds_of[g[0]["study_id"]]
        labels = ", ".join(f"{m['label']} (ID {m['study_id']}, n={m.get('n') or 'NR'})" for m in g)
        confs = {p["dataset_confidence"] for p in per_study if p["dataset_id"] == name}
        why = ""
        if len(g) > 1:
            inner = [(a, b, l, rs) for a, b, l, rs in pairs if ds_of[a["study_id"]] == name and ds_of[b["study_id"]] == name]
            why = "<br>".join(f"{a['label']} / {b['label']}: " + "; ".join(rs) for a, b, l, rs in inner) or "reviewer-assigned"
        md.append(f"| {name} | {labels} | {', '.join(sorted(confs))} | {why} |")
    unmerged = [(a, b, l, rs) for a, b, l, rs in pairs if ds_of[a["study_id"]] != ds_of[b["study_id"]]]
    md += ["", f"**{n_multi}** dataset(s) contain more than one study and need confirmation."]
    if unmerged:
        md += ["", f"## Flagged but not merged (below --merge {args.merge})", ""]
        for a, b, l, rs in unmerged:
            md.append(f"- {a['label']} / {b['label']} ({inv[l]}): " + "; ".join(rs))
        md.append("")
        md.append("Check these against the papers too; re-run with `--merge possible` to join them, or set `dataset_id` by hand.")
    if conflicts:
        md += ["", "## Conflicts with the reviewer's dataset_id column", ""]
        for a, b, l in conflicts:
            md.append(f"- {a['label']} ({a.get('dataset_id')}) and {b['label']} ({b.get('dataset_id')}) look {inv[l]} overlapping but are assigned different datasets; the reviewer's assignment was kept.")
    md += ["", "Rule for synthesis: when two papers share a dataset, count it once; take the larger or more "
           "complete report for the main table and present the other beside it, never as a second data point "
           "(SWiM item 1; Cochrane Handbook ch. 12 on the unit of analysis).", ""]
    with open(os.path.join(args.out_dir, "independent_datasets.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    if args.assign:
        path = os.path.join(args.out_dir, "studies_with_datasets.csv") if args.assign == "__default__" else args.assign
        if os.path.abspath(path) == os.path.abspath(args.studies):
            sys.exit("error: --assign must not overwrite the input studies.csv; give another path")
        out_fields = [f for f in fields if f not in ("dataset_id", "dataset_confidence")] + ["dataset_id", "dataset_confidence"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=out_fields, extrasaction="ignore")
            w.writeheader()
            ps = {p["study_id"]: p for p in per_study}
            for r in rows:
                row = {k: v for k, v in r.items() if not k.startswith("_")}
                row["dataset_id"] = ds_of[r["study_id"]]
                row["dataset_confidence"] = ps[r["study_id"]]["dataset_confidence"]
                w.writerow(row)
        print(f"wrote {path}")

    print(f"{len(rows)} studies -> {len(ordered)} independent datasets; {n_multi} grouping(s) to confirm; "
          f"{len(unmerged)} flagged pair(s) left unmerged; outputs in {args.out_dir}/ "
          "(independent_datasets.csv, overlap_pairs.csv, independent_datasets.md)")
    if conflicts:
        print(f"WARNING: {len(conflicts)} pair(s) conflict with the existing dataset_id column; see the .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
