#!/usr/bin/env python3
"""List the records the reviewer has let through screening, as CSV, with the
matching full-text file under data/articles_text/ when one can be found.

    python3 -I included.py                  # T/A Include or Maybe, or FT Include (default --stage any)
    python3 -I included.py --stage ft       # only Full-text decision = Include
    python3 -I included.py --stage ta       # only Title/abstract Include or Maybe
    python3 -I included.py -o analysis/included.csv

Reads the xlsx (the source of truth), not the CSV exports, so it cannot be
fooled by a stale export. Only the reviewer's columns H-L decide inclusion;
the AI suggestion columns are ignored. Records that are Include/Maybe at
title/abstract but Exclude at full text are dropped (they are listed with
--stage ta).

Text-file matching: first author's surname (Authors is "Surname, Given et
al.") plus Year against the "Surname et al. - YEAR - Title.txt" file names,
compared after stripping accents, case and punctuation; ties are broken by
title overlap. A record with no match has an empty text_file column, and the
summary on stderr says how many were unmatched, so the data-extraction step
knows which full texts still need converting (see the pdf-to-text skill).
"""

import argparse
import csv
import os
import re
import sys
import unicodedata

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lvrwb  # noqa: E402

COLS = [("ID", "A"), ("Year", "B"), ("Authors", "C"), ("Title", "D"), ("Journal", "E"), ("DOI", "F"),
        ("Zotero key", "M"), ("TA decision", "H"), ("TA reason", "I"), ("FT decision", "J"),
        ("FT reason", "K"), ("Notes", "L")]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def first_surname(authors):
    a = (authors or "").strip()
    if not a:
        return ""
    head = re.split(r",|;| and | & ", a, maxsplit=1)[0]
    head = re.sub(r"\bet al\.?$", "", head).strip()
    return norm(head)


def parse_filename(fn):
    stem = os.path.splitext(fn)[0]
    parts = [p.strip() for p in stem.split(" - ")]
    authors = parts[0] if parts else ""
    year = next((p for p in parts[1:] if re.fullmatch(r"\d{4}", p)), "")
    title = " - ".join(p for p in parts[1:] if p != year)
    a = re.sub(r"\bet al\.?$", "", authors).strip()
    a = re.split(r" and | & |,", a, maxsplit=1)[0]
    return norm(a), year, norm(title)


def match_file(rec, files):
    surname, year, title = first_surname(rec["Authors"]), (rec["Year"] or "").strip(), norm(rec["Title"])
    if not surname:
        return ""
    cands = [f for f, (a, y, t) in files.items() if a == surname]
    if year:
        with_year = [f for f in cands if files[f][1] == year]
        cands = with_year or [f for f in cands if not files[f][1]]
    if not cands:
        # fall back on the title alone (e.g. the Authors cell is empty or formatted oddly)
        head = " ".join(title.split()[:6])
        cands = [f for f, (a, y, t) in files.items() if head and t.startswith(head)]
    if len(cands) > 1:
        def overlap(f):
            t = files[f][2]
            return len(os.path.commonprefix([t, title]))
        cands.sort(key=overlap, reverse=True)
        if overlap(cands[0]) == overlap(cands[1]):
            print("warning: ID %s matches several files equally: %s" % (rec["ID"], "; ".join(cands[:3])), file=sys.stderr)
    return cands[0] if cands else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=lvrwb.DEFAULT_XLSX, help="workbook (default: data/LVR_screening_sheet_2.xlsx)")
    ap.add_argument("--text-dir", default=lvrwb.DEFAULT_TEXT_DIR, help="folder of full-text .txt files (default: data/articles_text)")
    ap.add_argument("--stage", choices=["any", "ta", "ft"], default="any",
                    help="any: T/A Include/Maybe not excluded at FT, or FT Include; ta: T/A Include/Maybe; ft: FT Include")
    ap.add_argument("-o", "--out", help="write CSV here instead of stdout (e.g. analysis/included.csv)")
    args = ap.parse_args()

    if not os.path.isfile(args.xlsx):
        lvrwb.die("workbook not found: %s" % args.xlsx)
    wb = lvrwb.Workbook(args.xlsx)
    cells = wb.cells(lvrwb.SCREENING)
    links = wb.hyperlinks(lvrwb.SCREENING)
    last = wb.extent(lvrwb.SCREENING)[0]
    headers = wb.header_map()
    expect = {"H": "Title/abstract decision", "J": "Full-text decision"}
    for col, name in expect.items():
        if headers.get(col) != name:
            lvrwb.die("column %s is %r, expected %r: the layout changed, update COLS" % (col, headers.get(col), name))

    files = {}
    if os.path.isdir(args.text_dir):
        for fn in sorted(os.listdir(args.text_dir)):
            if fn.lower().endswith(".txt"):
                files[fn] = parse_filename(fn)

    out_rows, unmatched = [], 0
    for row in range(2, last + 1):
        rec = {}
        for name, col in COLS:
            ref = "%s%d" % (col, row)
            c = cells.get(ref)
            rec[name] = links.get(ref) if ref in links else ((c.value or "") if c else "")
        if not rec["ID"]:
            continue
        ta, ft = rec["TA decision"], rec["FT decision"]
        ta_in = ta in ("Include", "Maybe")
        if args.stage == "ta":
            keep = ta_in
        elif args.stage == "ft":
            keep = ft == "Include"
        else:
            keep = (ta_in and ft != "Exclude") or ft == "Include"
        if not keep:
            continue
        rec["text_file"] = match_file(rec, files)
        if not rec["text_file"]:
            unmatched += 1
        out_rows.append(rec)

    fieldnames = [n for n, _ in COLS] + ["text_file"]
    dest = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.DictWriter(dest, fieldnames=fieldnames, lineterminator="\n")
    w.writeheader()
    w.writerows(out_rows)
    if args.out:
        dest.close()
    print("%d record(s) at stage %s; %d without a text file in %s" %
          (len(out_rows), args.stage, unmatched, os.path.relpath(args.text_dir)), file=sys.stderr)


if __name__ == "__main__":
    main()
