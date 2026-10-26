# PROVISIONAL: extends instruments.csv with the instrument_catalogue.csv columns. Catalogue facts (page-cited in
# instrument_notes.md) are copied for instruments that have a catalogue row; every row keeps verified = no.
import csv
R = 'analysis/extraction'
CAT = '.claude/skills/instrument-synthesis/assets/instrument_catalogue.csv'
cat_rows = list(csv.DictReader(open(CAT, encoding='utf-8')))
cat_cols = list(cat_rows[0].keys())
cat = {r['instrument']: r for r in cat_rows}
ALIAS = {
    'Visual Impairment as a Risk for Falls Questionnaire (VIRFQ)': 'VIRFQ',
    'EQ 5D-5L': 'EQ-5D-5L',
    'HALS two-question visual disability screen': 'Statistics Canada HALS vision questions',
    'Independent Mobility questionnaire': 'self-reported mobility questionnaire',
    'EQ-5D': 'EQ-5D vision bolt-on',
    'Vision bolt-on EQ-5D-3L': 'EQ-5D vision bolt-on',
    'Vision bolt-on EQ-5D-5L': 'EQ-5D vision bolt-on',
}
r = csv.DictReader(open(f'{R}/instruments.csv', encoding='utf-8'))
base_cols = r.fieldnames
rows = list(r)
# rename aliases in the other files too, so instrument names match exactly
REN = {k: v for k, v in ALIAS.items() if k in ('Visual Impairment as a Risk for Falls Questionnaire (VIRFQ)', 'EQ 5D-5L', 'HALS two-question visual disability screen', 'Independent Mobility questionnaire')}
for f in ('dta', 'effects', 'studies'):
    rr = csv.DictReader(open(f'{R}/{f}.csv', encoding='utf-8'))
    cols = rr.fieldnames
    data = list(rr)
    for x in data:
        for c in ('instrument', 'instruments'):
            if c in x:
                v = x[c]
                for k, n in REN.items():
                    v = v.replace(k, n)
                x[c] = v
    w = csv.DictWriter(open(f'{R}/{f}.csv', 'w', newline='', encoding='utf-8'), fieldnames=cols)
    w.writeheader()
    w.writerows(data)
out = []
seen = set()
for x in rows:
    name = REN.get(x['instrument'], x['instrument'])
    if name in seen:
        continue
    seen.add(name)
    x['instrument'] = name
    row = {c: 'NR' for c in cat_cols}
    row['instrument'] = name
    c =cat.get(name) or cat.get(ALIAS.get(name, ''))
    src = 'catalogue row' if c else 'extraction only'
    if c:
        row.update({k: v for k, v in c.items()})
        row['instrument'] = name
    # fill what pass A found where the catalogue row is silent
    for k in ('full_name', 'n_items', 'domains', 'response_scale', 'scoring', 'validation_method', 'languages', 'time_to_administer_min', 'target_population'):
        if row.get(k) in ('NR', '', None) and x.get(k) not in ('NR', '', None):
            row[k] = x[k]
    row['source_refs'] = '; '.join(filter(None, [row.get('source_refs', '') if row.get('source_refs') != 'NR' else '', x.get('source_refs', '')]))
    row['verified'] = 'no'
    row['notes'] = (row.get('notes', '') + f' [catalogued by AI chain step 5 from {src}; PROVISIONAL, unverified]').strip()
    out.append(row)
import re
dedup = {}
for row in out:
    k = row['instrument'].lower().strip()
    if k in dedup:
        continue
    dedup[k] = row
out = list(dedup.values())
for row in out:
    for c in ('n_items', 'time_to_administer_min'):
        v = row[c].strip()
        if v in ('NR', '') or re.fullmatch(r'\d+(\.\d+)?', v):
            continue
        m = re.fullmatch(r'(\d+(\.\d+)?)\b.*', v) if c == 'n_items' and re.match(r'\d+ ?(items)?$', v) else None
        row['notes'] += f' [{c} as written in source: "{v}"; numeric column set to NR]'
        row[c] = 'NR'
w = csv.DictWriter(open(f'{R}/instruments.csv', 'w', newline='', encoding='utf-8'), fieldnames=cat_cols)
w.writeheader()
w.writerows(out)
print(len(out), 'instruments;', sum(1 for r in out if 'catalogue row' in r['notes']), 'with a catalogue row')
