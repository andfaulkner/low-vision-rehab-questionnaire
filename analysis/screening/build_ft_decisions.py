"""Parse raw subagent lines into analysis/screening/ft_ai_decisions.csv and verify each quote against the text.
Usage: python3 -I build_ft_decisions.py RAW_LINES.csv  (run from repo root)"""
import csv, re, sys
raw = open(sys.argv[1], encoding="utf-8").read().splitlines()
pool = {int(r["id"]): r for r in csv.DictReader(open("analysis/screening/ft_pool.csv"))}
rows = {}
pat = re.compile(r'^(\d+),(Include|Exclude),([^,"]*),"((?:[^"]|"")*)",(.*)$')
for ln in raw:
    m = pat.match(ln)
    if not m:
        sys.exit("unparsed: " + ln[:80])
    i = int(m[1]); q = m[5].strip()
    if q.startswith('""') and q.endswith(']'):  # doubled-quote variant
        q = q.replace('""', '"')
    rows[i] = dict(id=i, decision=m[2], reason=m[3], rationale=m[4].replace('""', '"'), quote=q)
for i, p in pool.items():
    if p["text_status"] != "retrieved":
        rows[i] = dict(id=i, decision="Exclude", reason="Full text not available",
                       rationale="No usable full text in data/articles_text/; not screened.", quote="NOT RETRIEVED")
missing = [i for i in pool if i not in rows]
extra = [i for i in rows if i not in pool]
print("missing", missing, "extra", extra, "n", len(rows))
def norm(s): return re.sub(r"\s+", " ", s.replace("ﬁ", "fi").replace("ﬂ", "fl")).strip().lower()
bad = []
for i, r in sorted(rows.items()):
    if r["quote"] == "NOT RETRIEVED": continue
    m = re.match(r'^"?(.*?)"?\s*\[page (\d+)\]"?\s*$', r["quote"].strip(), re.S)
    if not m: bad.append((i, "no page marker")); continue
    txt = open("data/articles_text/" + pool[i]["text_file"], encoding="utf-8", errors="replace").read()
    sentence = norm(m[1]).strip('" ')
    # strip leading/trailing ellipsis and bracketed citations for comparison
    s2 = sentence.rstrip(".")
    if s2 not in norm(txt):
        bad.append((i, "quote not found verbatim"))
        continue
    page = re.search(r"\[page %s\]" % m[2], txt)
    pos = norm(txt).find(s2)
    # find page marker preceding the quote
    t = norm(txt); marks = [(mm.start(), int(mm.group(1))) for mm in re.finditer(r"\[page (\d+)\]", t)]
    pg = max([n for s, n in marks if s <= pos], default=None)
    if pg != int(m[2]): bad.append((i, f"page marker says {m[2]}, text has quote on page {pg}"))
print("quote problems:", bad)
with open("analysis/screening/ft_ai_decisions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "decision", "reason", "rationale", "quote"])
    w.writeheader()
    for i in sorted(rows): w.writerow(rows[i])
import collections
print(collections.Counter(r["decision"] for r in rows.values()))
