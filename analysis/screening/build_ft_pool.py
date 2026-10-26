"""Build analysis/screening/ft_pool.csv by plan rule 6. Run: python3 -I build_ft_pool.py (from repo root)."""
import csv, sys
sys.dont_write_bytecode = True
sys.path.insert(0, ".claude/skills/screening-workbook/scripts")
import lvrwb
wb = lvrwb.Workbook("data/LVR_screening_sheet_2.xlsx")
hm = {v: k for k, v in wb.header_map().items()}
rows = wb.id_to_row()
def val(r, name):
    return (wb.value("Screening", f"{hm[name]}{r}") or "").strip()
H, N, Q = "Title/abstract decision", "Suggested decision (AI)", "Independent T/A decision (AI)"
# IDs 128-135 are "Not screened" placeholders (all Include) in the strict file: ignore them.
strict = {int(x["ID"]): x["Strict decision (AI)"].strip() for x in csv.DictReader(open("results/LVR_strict_screening.csv")) if int(x["ID"]) <= 127}
inv = {int(x["id"]): x for x in csv.DictReader(open("analysis/screening/text_inventory.csv"))}
ok = lambda d: d in ("Include", "Maybe")
out = []
for i in sorted(rows):
    r = rows[i]
    h, n, q, s = val(r, H), val(r, N), val(r, Q), strict.get(i, "")
    if h:
        basis = "reviewer" if ok(h) else None
    else:
        k = sum(ok(d) for d in (n, q, s))
        basis = "ai-consensus" if k >= 2 else "ai-single" if k == 1 else None
    if basis:
        t = inv.get(i, {})
        out.append(dict(id=i, basis=basis, h=h, n=n, q=q, strict=s, text_file=t.get("txt", ""), text_status=t.get("status", "not-retrieved")))
with open("analysis/screening/ft_pool.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "basis", "h", "n", "q", "strict", "text_file", "text_status"])
    w.writeheader(); w.writerows(out)
import collections
print(len(out), collections.Counter(o["basis"] for o in out), collections.Counter(o["text_status"] for o in out))
print([o["id"] for o in out])
print("sanity", {i: i in {o["id"] for o in out} for i in (92, 128, 133)})
