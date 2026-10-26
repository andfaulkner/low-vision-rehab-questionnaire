import csv
p = 'analysis/extraction/studies.csv'
r = csv.DictReader(open(p, encoding='utf-8'))
cols = r.fieldnames
rows = list(r)
for x in rows:
    if x['study_id'] == '128':
        x['cohort'] = 'same 385 participants as Wu 2026 (Screening ID 92); stated in Wu 2026, not in this paper; count as ONE independent dataset'
w = csv.DictWriter(open(p, 'w', newline='', encoding='utf-8'), fieldnames=cols)
w.writeheader()
w.writerows(rows)
