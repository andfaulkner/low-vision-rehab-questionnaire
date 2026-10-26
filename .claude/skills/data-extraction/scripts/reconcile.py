#!/usr/bin/env python3
"""Compare two extraction passes of the same CSV (pass A vs pass B) cell by cell.

    python3 -I reconcile.py analysis/extraction/passA/dta.csv analysis/extraction/passB/dta.csv
    python3 -I reconcile.py A/studies.csv B/studies.csv --out /tmp/studies_disagreements.csv
    python3 -I reconcile.py A.csv B.csv --kind dta --ignore notes,derivation --tol 0.005

Rows are matched on the schema key for the file kind (detected from the file name, or
given with --kind / --key). Keys are compared after lower-casing and collapsing
whitespace; rows still unmatched are paired by similarity within the same study_id
(--fuzzy, default 0.85) so that a reworded item_text does not hide a real match.
Numbers agree when within --tol (default 0, i.e. exact after normalisation); NR, blank
and 'not reported' are treated as the same value. The reviewer decides every
disagreement by going back to the cited page; this script only lists them.

Exit status: 0 identical, 2 disagreements or unmatched rows found, 1 error.
"""

import argparse
import csv
import difflib
import os
import re
import sys

KEYS = {
    "studies": ["study_id"],
    "dta": ["study_id", "instrument", "item_text", "threshold", "reference_standard",
            "ref_threshold", "unit", "subgroup"],
    "effects": ["study_id", "outcome_type", "measure", "instrument", "comparator", "unit",
                "subgroup"],
    "instruments": ["instrument"],
}
NR_TOKENS = {"", "nr", "not reported", "n/a", "na"}


def norm(v):
    s = re.sub(r"\s+", " ", (v or "").strip())
    return "NR" if s.lower() in NR_TOKENS else s


def norm_key(v):
    s = norm(v).lower()
    return re.sub(r"[^\w\s./<>=%-]", "", s)


def to_num(s):
    try:
        return float(s.rstrip("%").replace(",", ""))
    except (ValueError, AttributeError):
        return None


def same(a, b, tol):
    a, b = norm(a), norm(b)
    if a == b:
        return True
    x, y = to_num(a), to_num(b)
    if x is not None and y is not None:
        return abs(x - y) <= tol + 1e-12
    return a.lower() == b.lower()


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        r = csv.DictReader(fh)
        return [f.strip() for f in (r.fieldnames or [])], [{(k or "").strip(): (v or "") for k, v in row.items()} for row in r]


def detect_kind(path):
    base = os.path.basename(path).lower()
    for k in KEYS:
        if k in base:
            return k
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", help="pass A CSV")
    ap.add_argument("b", help="pass B CSV")
    ap.add_argument("--kind", choices=KEYS, help="file kind (default: detected from the file name)")
    ap.add_argument("--key", help="comma-separated key columns (overrides --kind)")
    ap.add_argument("--ignore", default="", help="comma-separated columns to skip (e.g. notes,derivation)")
    ap.add_argument("--tol", type=float, default=0.0, help="numeric tolerance (default 0)")
    ap.add_argument("--fuzzy", type=float, default=0.85, help="similarity (0-1) to pair unmatched rows within a study; 0 disables")
    ap.add_argument("--out", metavar="CSV", help="write the disagreement list as CSV")
    a = ap.parse_args(argv)

    kind = a.kind or detect_kind(a.a) or detect_kind(a.b)
    if a.key:
        key = [c.strip() for c in a.key.split(",")]
    elif kind:
        key = KEYS[kind]
    else:
        ap.error("cannot detect the file kind from the names; give --kind or --key")
    ignore = {c.strip() for c in a.ignore.split(",") if c.strip()}
    try:
        fa, ra = read(a.a)
        fb, rb = read(a.b)
    except OSError as e:
        sys.exit(f"error: {e}")
    for c in key:
        if c not in fa or c not in fb:
            sys.exit(f"error: key column {c!r} missing from one of the files")
    cols = [c for c in fa if c in fb and c not in ignore and c not in key]
    only_a_cols = [c for c in fa if c not in fb]
    only_b_cols = [c for c in fb if c not in fa]

    def k(row):
        return tuple(norm_key(row.get(c, "")) for c in key)

    ia = {}
    for i, r in enumerate(ra):
        ia.setdefault(k(r), []).append(i)
    ib = {}
    for i, r in enumerate(rb):
        ib.setdefault(k(r), []).append(i)
    pairs, used_a, used_b = [], set(), set()
    for kk, ais in ia.items():
        bis = ib.get(kk, [])
        for x, y in zip(ais, bis):
            pairs.append((x, y, "exact"))
            used_a.add(x)
            used_b.add(y)
    # fuzzy pairing of leftovers within the same study_id (or globally when no study_id)
    if a.fuzzy > 0:
        left_a = [i for i in range(len(ra)) if i not in used_a]
        left_b = [i for i in range(len(rb)) if i not in used_b]
        cands = []
        for x in left_a:
            for y in left_b:
                if "study_id" in key and norm_key(ra[x].get("study_id")) != norm_key(rb[y].get("study_id")):
                    continue
                s = difflib.SequenceMatcher(None, " | ".join(k(ra[x])), " | ".join(k(rb[y]))).ratio()
                if s >= a.fuzzy:
                    cands.append((s, x, y))
        for s, x, y in sorted(cands, reverse=True):
            if x in used_a or y in used_b:
                continue
            pairs.append((x, y, f"fuzzy {s:.2f}"))
            used_a.add(x)
            used_b.add(y)
    only_a = [i for i in range(len(ra)) if i not in used_a]
    only_b = [i for i in range(len(rb)) if i not in used_b]

    disagreements = []  # (key text, column, A, B, match type)
    per_col = {c: [0, 0] for c in cols}  # agree, disagree
    for x, y, how in pairs:
        ktxt = " | ".join(norm(ra[x].get(c, "")) for c in key)
        if how != "exact":
            disagreements.append((ktxt, "<key>", " | ".join(ra[x].get(c, "") for c in key),
                                  " | ".join(rb[y].get(c, "") for c in key), how))
        for c in cols:
            if same(ra[x].get(c, ""), rb[y].get(c, ""), a.tol):
                per_col[c][0] += 1
            else:
                per_col[c][1] += 1
                disagreements.append((ktxt, c, ra[x].get(c, ""), rb[y].get(c, ""), how))

    print(f"A: {a.a} ({len(ra)} rows)\nB: {a.b} ({len(rb)} rows)\nkey: {', '.join(key)}"
          + (f"\ncolumns ignored: {', '.join(sorted(ignore))}" if ignore else "")
          + (f"\ncolumns only in A: {', '.join(only_a_cols)}" if only_a_cols else "")
          + (f"\ncolumns only in B: {', '.join(only_b_cols)}" if only_b_cols else ""))
    print(f"matched rows: {len(pairs)} ({sum(1 for p in pairs if p[2] != 'exact')} by fuzzy key)")
    if only_a:
        print(f"\nrows only in A ({len(only_a)}):")
        for i in only_a:
            print("  A row " + str(i + 2) + ": " + " | ".join(ra[i].get(c, "") for c in key))
    if only_b:
        print(f"\nrows only in B ({len(only_b)}):")
        for i in only_b:
            print("  B row " + str(i + 2) + ": " + " | ".join(rb[i].get(c, "") for c in key))
    if disagreements:
        print(f"\ncell disagreements ({len(disagreements)}):")
        w = max(len(d[1]) for d in disagreements)
        for ktxt, c, va, vb, how in disagreements:
            print(f"  [{ktxt}]\n    {c:<{w}}  A: {va!r}\n    {' ' * w}  B: {vb!r}" + (f"   ({how} match)" if how != "exact" else ""))
    print("\nagreement by column:")
    for c in cols:
        ag, dis = per_col[c]
        tot = ag + dis
        if tot:
            print(f"  {c:<24} {ag}/{tot} agree" + (f"  <- {dis} to resolve" if dis else ""))
    total_cells = sum(sum(v) for v in per_col.values())
    agree_cells = sum(v[0] for v in per_col.values())
    if total_cells:
        print(f"\noverall: {agree_cells}/{total_cells} cells agree ({100 * agree_cells / total_cells:.1f}%)")
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["key", "column", "A", "B", "match", "resolved_value", "resolved_by"])
            for d in disagreements:
                wr.writerow(list(d) + ["", ""])
            for i in only_a:
                wr.writerow([" | ".join(ra[i].get(c, "") for c in key), "<row>", "present", "absent", "unmatched", "", ""])
            for i in only_b:
                wr.writerow([" | ".join(rb[i].get(c, "") for c in key), "<row>", "absent", "present", "unmatched", "", ""])
        print(f"disagreement list written to {a.out} (fill resolved_value / resolved_by, then apply to the master CSV)")
    return 2 if (disagreements or only_a or only_b) else 0


if __name__ == "__main__":
    sys.exit(main())
