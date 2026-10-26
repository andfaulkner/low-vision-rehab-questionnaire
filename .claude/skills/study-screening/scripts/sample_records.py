#!/usr/bin/env python3
"""Choose a seeded random verification sample for a second reviewer, or list
the Include/Maybe records whose full text has not been retrieved.

Sampling
    python3 -I sample_records.py --fraction 0.2 --seed 7 -o analysis/screening/second_reviewer_sample.csv
    python3 -I sample_records.py --n 30 --seed 7 --stratify "Suggested decision (AI)" -o ...
    python3 -I sample_records.py --fraction 0.2 --seed 7 --pool ft -o ...      # full-text stage: reviewer's Include/Maybe
    python3 -I sample_records.py --fraction 0.2 --seed 7 --exclude-ids-from earlier_sample.csv -o ...

    The sample CSV is a blank decision sheet: ID, Year, Authors, Title, Journal,
    DOI link, Abstract, then empty "Second reviewer decision", "Second reviewer
    reason" and "Second reviewer notes". It carries neither the first
    reviewer's nor the AI's decisions, so the second reviewer is blind. Feed the
    filled sheet to agreement.py with --b-file. The same --seed and pool give
    the same sample, and the IDs are also printed so they can be quoted in the
    Methods. --stratify allocates proportionally within each value of a column
    (largest-remainder rounding, at least one per non-empty stratum), which
    keeps rare AI "Include" rows in the sample.

Retrieval
    python3 -I sample_records.py --retrieval -o analysis/screening/retrieval.csv
    python3 -I sample_records.py --retrieval --decision-col "Independent T/A decision (AI)"

    Lists every record whose decision column (default the reviewer's H) is
    Include or Maybe, with the matching PDF in data/articles/ and .txt in
    data/articles_text/ found by first-author surname + year, the matching
    logic of the screening-workbook skill's included.py (imported when it is
    present, otherwise a copy of it; the output says which). Status is
    "retrieved" (PDF and text), "text-missing" (PDF only; run pdf-to-text) or
    "not-retrieved" (nothing). The not-retrieved count is the PRISMA 2020
    "reports not retrieved" box.

The source is the workbook (default) or a Screening CSV export. Nothing is
ever written to the workbook.
"""

import argparse
import csv
import os
import random
import re
import sys
import unicodedata
from collections import OrderedDict

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screening_common as sc  # noqa: E402

BIB = ["ID", "Year", "Authors", "Title", "Journal", "DOI link", "Abstract"]
BLANK = ["Second reviewer decision", "Second reviewer reason", "Second reviewer notes"]


# ---- matching: import included.py's functions, or the same logic copied here ----
def _load_matcher():
    try:
        if sc.WORKBOOK_SCRIPTS not in sys.path:
            sys.path.insert(0, sc.WORKBOOK_SCRIPTS)
        import included  # noqa: E402
        return included.parse_filename, included.match_file, "screening-workbook/scripts/included.py"
    except Exception:
        return _parse_filename, _match_file, "a copy of included.py's matcher (import failed)"


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def _first_surname(authors):
    a = (authors or "").strip()
    if not a:
        return ""
    head = re.split(r",|;| and | & ", a, maxsplit=1)[0]
    head = re.sub(r"\bet al\.?$", "", head).strip()
    return _norm(head)


def _parse_filename(fn):
    stem = os.path.splitext(fn)[0]
    parts = [p.strip() for p in stem.split(" - ")]
    authors = parts[0] if parts else ""
    year = next((p for p in parts[1:] if re.fullmatch(r"\d{4}", p)), "")
    title = " - ".join(p for p in parts[1:] if p != year)
    a = re.sub(r"\bet al\.?$", "", authors).strip()
    a = re.split(r" and | & |,", a, maxsplit=1)[0]
    return _norm(a), year, _norm(title)


def _match_file(rec, files):
    surname, year, title = _first_surname(rec["Authors"]), (rec["Year"] or "").strip(), _norm(rec["Title"])
    if not surname:
        return ""
    cands = [f for f, (a, y, t) in files.items() if a == surname]
    if year:
        with_year = [f for f in cands if files[f][1] == year]
        cands = with_year or [f for f in cands if not files[f][1]]
    if not cands:
        head = " ".join(title.split()[:6])
        cands = [f for f, (a, y, t) in files.items() if head and t.startswith(head)]
    if len(cands) > 1:
        def overlap(f):
            return len(os.path.commonprefix([files[f][2], title]))
        cands.sort(key=overlap, reverse=True)
    return cands[0] if cands else ""


def index_dir(path, ext, parse):
    files = {}
    if os.path.isdir(path):
        for fn in sorted(os.listdir(path)):
            if fn.lower().endswith(ext):
                files[fn] = parse(fn)
    return files


def retrieval(args, t):
    parse, match, how = _load_matcher()
    pdfs = index_dir(args.pdf_dir, ".pdf", parse)
    txts = index_dir(args.text_dir, ".txt", parse)
    dec_idx = t.col_index(args.decision_col)
    # The DOI column holds the URL in both the CSV export and the lvrwb grid.
    rows_out, counts = [], {"retrieved": 0, "text-missing": 0, "not-retrieved": 0}
    for rid, row in t.records():
        dec = (row[dec_idx] if dec_idx < len(row) else "").strip()
        if dec not in ("Include", "Maybe"):
            continue
        rec = {"ID": rid, "Authors": t.get(row, "Authors"), "Year": t.get(row, "Year"), "Title": t.get(row, "Title")}
        pdf = match(rec, pdfs) if pdfs else ""
        txt = match(rec, txts) if txts else ""
        status = "retrieved" if (pdf and txt) else ("text-missing" if pdf else ("retrieved" if txt else "not-retrieved"))
        counts[status] += 1
        rows_out.append([rid, rec["Year"], rec["Authors"], rec["Title"], t.get(row, "DOI link"), dec, pdf, txt, status])
    header = ["ID", "Year", "Authors", "Title", "DOI link", "decision", "pdf_file", "text_file", "status"]
    dest = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.writer(dest, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows_out)
    if args.out:
        dest.close()
    missing = [str(r[0]) for r in rows_out if r[8] == "not-retrieved"]
    no_text = [str(r[0]) for r in rows_out if r[8] == "text-missing"]
    print("%d record(s) Include/Maybe in %r: %d retrieved, %d PDF without text, %d not retrieved (matching by %s)" %
          (len(rows_out), t.header[dec_idx], counts["retrieved"], counts["text-missing"], counts["not-retrieved"], how), file=sys.stderr)
    if no_text:
        print("PDF but no .txt (run pdf-to-text): IDs %s" % ", ".join(no_text), file=sys.stderr)
    if missing:
        print("not retrieved (PRISMA 'reports not retrieved' = %d): IDs %s" % (len(missing), ", ".join(missing)), file=sys.stderr)
    if args.out:
        print("wrote %s" % args.out, file=sys.stderr)


def largest_remainder(weights, total):
    """Integer allocation of `total` across strata proportional to weights, at least 1 each where weight > 0."""
    keys = [k for k, w in weights.items() if w > 0]
    if not keys or total <= 0:
        return {k: 0 for k in weights}
    s = sum(weights[k] for k in keys)
    raw = {k: total * weights[k] / s for k in keys}
    alloc = {k: int(raw[k]) for k in keys}
    for k in keys:
        if alloc[k] == 0:
            alloc[k] = 1
    rem = total - sum(alloc.values())
    order = sorted(keys, key=lambda k: (raw[k] - int(raw[k]), -weights[k], k), reverse=True)
    i = 0
    while rem > 0 and order:
        k = order[i % len(order)]
        if alloc[k] < weights[k]:
            alloc[k] += 1
            rem -= 1
        i += 1
        if i > 10 * len(order) + total:
            break
    while rem < 0:
        k = max(keys, key=lambda k: (alloc[k], raw[k]))
        if alloc[k] <= 1:
            break
        alloc[k] -= 1
        rem += 1
    return {k: min(alloc.get(k, 0), weights[k]) for k in weights}


def sample(args, t):
    recs = t.records()
    if args.pool == "ft":
        hidx = t.col_index("Title/abstract decision")
        recs = [(rid, r) for rid, r in recs if (r[hidx] if hidx < len(r) else "").strip() in ("Include", "Maybe")]
    elif args.pool == "ta-undecided":
        hidx = t.col_index("Title/abstract decision")
        recs = [(rid, r) for rid, r in recs if not (r[hidx] if hidx < len(r) else "").strip()]
    skip = set()
    if args.exclude_ids_from:
        with open(args.exclude_ids_from, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                v = (row.get("ID") or row.get("id") or "").strip()
                if v.isdigit():
                    skip.add(int(v))
        recs = [(rid, r) for rid, r in recs if rid not in skip]
    if not recs:
        sc.die("the pool is empty")
    if args.n is not None:
        total = args.n
    else:
        total = int(round(args.fraction * len(recs)))
    total = max(0, min(total, len(recs)))
    rng = random.Random(args.seed)
    chosen = []
    strata_report = []
    if args.stratify:
        sidx = t.col_index(args.stratify)
        groups = OrderedDict()
        for rid, r in recs:
            key = (r[sidx] if sidx < len(r) else "").strip() or "(blank)"
            groups.setdefault(key, []).append((rid, r))
        alloc = largest_remainder({k: len(v) for k, v in groups.items()}, total)
        for key in sorted(groups):
            members = sorted(groups[key], key=lambda x: x[0])
            take = alloc.get(key, 0)
            pick = rng.sample(members, take) if take else []
            chosen.extend(pick)
            strata_report.append((key, len(members), take))
    else:
        chosen = rng.sample(sorted(recs, key=lambda x: x[0]), total)
    chosen.sort(key=lambda x: x[0])

    header = BIB + BLANK
    dest = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.writer(dest, lineterminator="\n")
    w.writerow(header)
    for rid, r in chosen:
        w.writerow([t.get(r, name) if name in t.header else "" for name in BIB] + ["", "", ""])
    if args.out:
        dest.close()
    ids = ", ".join(str(rid) for rid, _ in chosen)
    print("sample: %d of %d records (pool=%s, seed=%d%s)" %
          (len(chosen), len(recs), args.pool, args.seed, ", stratified by %r" % args.stratify if args.stratify else ""), file=sys.stderr)
    for key, size, take in strata_report:
        print("  %-40s %4d in pool, %3d sampled" % (key, size, take), file=sys.stderr)
    print("IDs: %s" % ids, file=sys.stderr)
    if args.out:
        print("wrote %s (blank decision sheet; the second reviewer fills the last three columns)" % args.out, file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default=None, help="xlsx or Screening CSV (default: data/LVR_screening_sheet_2.xlsx)")
    ap.add_argument("--fraction", type=float, default=0.2, help="share of the pool to sample (default 0.2)")
    ap.add_argument("--n", type=int, help="sample this many records instead of a fraction")
    ap.add_argument("--seed", type=int, default=20261004, help="random seed; quote it in the Methods (default 20261004)")
    ap.add_argument("--stratify", help="column (header or letter) whose values define strata, e.g. \"Suggested decision (AI)\"")
    ap.add_argument("--pool", choices=["all", "ta-undecided", "ft"], default="all",
                    help="all records; records with no reviewer T/A decision; or the full-text pool (reviewer Include/Maybe)")
    ap.add_argument("--exclude-ids-from", help="CSV with an ID column whose records are left out (an earlier sample)")
    ap.add_argument("--retrieval", action="store_true", help="list Include/Maybe records and whether their PDF/.txt exist")
    ap.add_argument("--decision-col", default="Title/abstract decision", help="decision column for --retrieval (default H)")
    ap.add_argument("--pdf-dir", default=sc.DEFAULT_PDF_DIR, help="folder of PDFs (default data/articles)")
    ap.add_argument("--text-dir", default=sc.DEFAULT_TEXT_DIR, help="folder of .txt full texts (default data/articles_text)")
    ap.add_argument("--lists", help="Lists CSV when the source is a CSV")
    ap.add_argument("-o", "--out", help="write the CSV here instead of stdout")
    args = ap.parse_args()
    if args.fraction <= 0 or args.fraction > 1:
        sc.die("--fraction must be in (0, 1]")
    try:
        t = sc.load_table(args.source, args.lists)
        if args.retrieval:
            retrieval(args, t)
        else:
            sample(args, t)
    except sc.ScreeningError as e:
        sc.die(str(e))


if __name__ == "__main__":
    main()
