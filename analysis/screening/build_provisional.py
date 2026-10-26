"""Write analysis/screening/provisional_included.csv (pool records whose full-text AI decision is Include). Run from repo root with python3 -I."""
import csv, sys
sys.dont_write_bytecode = True
sys.path.insert(0, ".claude/skills/screening-workbook/scripts")
import lvrwb
wb = lvrwb.Workbook("data/LVR_screening_sheet_2.xlsx")
col = {v: k for k, v in wb.header_map().items()}
rowof = wb.id_to_row()
links = wb.hyperlinks("Screening")
def cell(i, name):
    return (wb.value("Screening", f"{col[name]}{rowof[i]}") or "").strip()
pool = {int(r["id"]): r for r in csv.DictReader(open("analysis/screening/ft_pool.csv"))}
ft = {int(r["id"]): r for r in csv.DictReader(open("analysis/screening/ft_ai_decisions.csv", encoding="utf-8"))}
fields = ["ID", "Year", "Authors", "Title", "Journal", "DOI", "Zotero key", "TA decision", "TA reason", "FT decision", "FT reason", "Notes",
          "text_file", "basis", "ft_ai_decision", "ft_ai_reason", "ft_ai_quote", "provisional_notes"]
OVERLAP = {92: "Overlapping cohort: same Legge-group 385-adult survey sample as ID 128 (Wu 2024 TVST); count as ONE independent dataset in synthesis (SWiM).",
           128: "Overlapping cohort with ID 92 (Wu 2026 IOVS); one independent dataset."}
out = []
for i in sorted(pool):
    if ft[i]["decision"] != "Include": continue
    p = pool[i]
    r = rowof[i]
    out.append({"ID": i, "Year": cell(i, "Year"), "Authors": cell(i, "Authors"), "Title": cell(i, "Title"), "Journal": cell(i, "Journal"),
                "DOI": links.get(f"{col['DOI link']}{r}", ""), "Zotero key": cell(i, "Zotero key"),
                "TA decision": cell(i, "Title/abstract decision"), "TA reason": cell(i, "Exclusion reason (T/A)"),
                "FT decision": cell(i, "Full-text decision"), "FT reason": cell(i, "Exclusion reason (FT)"), "Notes": cell(i, "Notes"),
                "text_file": p["text_file"], "basis": p["basis"], "ft_ai_decision": "Include", "ft_ai_reason": ft[i]["reason"],
                "ft_ai_quote": ft[i]["quote"], "provisional_notes": OVERLAP.get(i, "")})
with open("analysis/screening/provisional_included.csv", "w", newline="", encoding="utf-8") as f:
    f.write("# PROVISIONAL: reviewer has decided 40/135 at T/A and 0 at FT; see plan doc rule 6\n")
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)
import collections
print(len(out), collections.Counter(o["basis"] for o in out)); print([o["ID"] for o in out])
print("no text:", [i for i in pool if pool[i]["text_status"] != "retrieved"], "| 128 FT:", ft[128]["decision"], ft[128]["reason"])
