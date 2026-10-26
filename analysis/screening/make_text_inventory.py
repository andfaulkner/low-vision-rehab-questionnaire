#!/usr/bin/env python3
"""Match every Screening record to data/articles/*.pdf and data/articles_text/*.txt.
Run from the repo root: python3 -I analysis/screening/make_text_inventory.py"""
import csv, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, ".claude/skills/screening-workbook/scripts")
import lvrwb, included  # noqa: E402

SUSPECT = {48, 69}  # wrong paper / supplementary tables only (plan doc)
wb = lvrwb.Workbook(lvrwb.DEFAULT_XLSX)
cells = wb.cells(lvrwb.SCREENING)
last = wb.extent(lvrwb.SCREENING)[0]


def listing(d, ext):
    return {f: included.parse_filename(f) for f in sorted(os.listdir(d)) if f.lower().endswith(ext)}


pdfs, txts = listing("data/articles", ".pdf"), listing("data/articles_text", ".txt")


def val(col, row):
    c = cells.get("%s%d" % (col, row))
    return (c.value or "") if c else ""


rows = []
for r in range(2, last + 1):
    rec = {"ID": val("A", r), "Year": str(val("B", r)), "Authors": val("C", r), "Title": val("D", r)}
    if not rec["ID"]:
        continue
    pdf, txt = included.match_file(rec, pdfs), included.match_file(rec, txts)
    i = int(float(rec["ID"]))
    status = "suspect" if i in SUSPECT else "retrieved" if txt else "text-missing" if pdf else "not-retrieved"
    rows.append({"id": i, "year": rec["Year"], "first_author": included.first_surname(rec["Authors"]),
                 "pdf": pdf, "txt": txt, "status": status})
with open("analysis/screening/text_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "year", "first_author", "pdf", "txt", "status"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(len(rows), dict(Counter(x["status"] for x in rows)))
for x in rows:
    if x["status"] != "retrieved":
        print(x["id"], x["first_author"], x["year"], x["status"], "| pdf:", x["pdf"][:40], "| txt:", x["txt"][:40])
