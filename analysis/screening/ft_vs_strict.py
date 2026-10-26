"""Overlap of the FT AI Include set with the earlier strict pass (IDs 1-127). python3 -I ft_vs_strict.py from repo root."""
import csv
strict = {int(r["ID"]): r for r in csv.DictReader(open("results/LVR_strict_screening.csv", encoding="utf-8")) if int(r["ID"]) <= 127}
ft = {int(r["id"]): r for r in csv.DictReader(open("analysis/screening/ft_ai_decisions.csv", encoding="utf-8"))}
pool = {int(r["id"]): r for r in csv.DictReader(open("analysis/screening/ft_pool.csv"))}
S = {i for i, r in strict.items() if r["Strict decision (AI)"] == "Include"}
F = {i for i, r in ft.items() if r["decision"] == "Include" and i <= 127}
F_all = {i for i, r in ft.items() if r["decision"] == "Include"}
both = S & F; only_s = S - F; only_f = F - S
notin = sorted(i for i in S if i not in pool)
trim = lambda s: s.strip().replace("\n", " ")
L = []
L.append("# FT AI pass vs earlier strict pass\n")
L.append("Advisory only: both are AI decisions. The reviewer has made no full-text decisions (J/K empty).\n")
L.append(f"- Strict pass Includes (IDs 1-127): **{len(S)}**; this step's full-text Includes among IDs 1-127: **{len(F)}** (all IDs incl. 128-135: {len(F_all)}).")
L.append(f"- Both Include: **{len(both)}**; strict only: **{len(only_s)}**; full-text pass only: **{len(only_f)}**.")
agree = len(both) + (len(set(strict) & set(pool)) - len(S | F)) if False else None
L.append(f"- Strict Includes not in the full-text pool: {notin if notin else 'none'}.")
L.append(f"- Jaccard overlap {len(both)/len(S|F):.2f}; share of strict Includes also Included now {len(both)/len(S):.2f}.\n")
def block(title, ids, a, b):
    L.append(f"## {title} ({len(ids)})\n")
    for i in sorted(ids):
        s = strict[i]; f = ft.get(i)
        L.append(f"### ID {i} - {trim(s['Authors'])[:40]} {s['Year']}, {trim(s['Title'])[:110]}")
        L.append(f"- Pool basis: {pool[i]['basis'] if i in pool else 'not in pool'}; text: {pool[i]['text_status'] if i in pool else 'n/a'}")
        L.append(f"- Strict ({s['Strict decision (AI)']}): {trim(s['Strict rationale (AI)'])[:600]}")
        if f:
            L.append(f"- This pass ({f['decision']}{', ' + f['reason'] if f['reason'] else ''}): {trim(f['rationale'])}")
            L.append(f"- Quote: {trim(f['quote'])}")
        L.append("")
block("Strict Include, full-text pass Exclude", only_s, "strict", "ft")
block("Strict Exclude (or absent), full-text pass Include", only_f, "ft", "strict")
open("analysis/screening/ft_vs_strict.md", "w", encoding="utf-8").write("\n".join(L))
print(len(S), len(F), len(both), sorted(only_s), sorted(only_f), notin)
