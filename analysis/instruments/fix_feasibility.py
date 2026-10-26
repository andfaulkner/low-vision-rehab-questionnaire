"""One-off repair of unquoted commas in feasibility.csv (chain step 7). Run: python3 -I analysis/instruments/fix_feasibility.py"""
import csv

p = "analysis/instruments/feasibility.csv"
rows = list(csv.reader(open(p, encoding="utf-8")))
h = rows[0]
out = [h]
fix = {"IVI": (5, 9), "GQL-15": (5, 9), "APEDS-VFQ": (5, 8), "EQ-5D vision bolt-on": (7, 9)}
for r in rows[1:]:
    if r[0] in fix and len(r) != len(h):
        a, b = fix[r[0]]
        r = r[:a] + [", ".join(x.strip() for x in r[a:b])] + r[b:]
    assert len(r) == len(h), (r[0], len(r))
    out.append(r)
csv.writer(open(p, "w", newline="", encoding="utf-8")).writerows(out)
print("ok")
