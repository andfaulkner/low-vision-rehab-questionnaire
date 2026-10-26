# PROVISIONAL: merges pass A (+ pass B for the dual-extracted papers) into the four master CSVs.
import csv, glob, os
R = 'analysis/extraction'
DUAL = {27, 38, 79, 92, 119, 128}
USE_B_DTA = {27}   # pass B has a strict superset of rows, identical on the overlap


def rd(p):
    return list(csv.DictReader(open(p, encoding='utf-8'))) if os.path.exists(p) else []


def hdr(p):
    return next(csv.reader(open(p, encoding='utf-8')))


ids = sorted(int(os.path.basename(d)) for d in glob.glob(f'{R}/passA/*'))
for f in ('studies', 'dta', 'effects', 'instruments'):
    cols = hdr(f'{R}/passA/{ids[0]}/{f}.csv')
    rows = []
    for i in ids:
        a = rd(f'{R}/passA/{i}/{f}.csv')
        b = rd(f'{R}/passB/{i}/{f}.csv') if i in DUAL else []
        if f == 'dta' and i in USE_B_DTA:
            rows += b
            continue
        rows += a
        if f == 'effects' and b:
            seen = {(r['outcome_type'], r['estimate'], r['n'], r['comparator'][:12]) for r in a}
            for r in b:
                k = (r['outcome_type'], r['estimate'], r['n'], r['comparator'][:12])
                if k not in seen:
                    r['notes'] = (r.get('notes', '') + ' [row from pass B only]').strip()
                    rows.append(r)
        if f == 'instruments':
            names = {r['instrument'].lower() for r in rows}
            rows += [r for r in b if r['instrument'].lower() not in names]
    if f == 'instruments':
        seen = set()
        u = []
        for r in rows:
            k = r['instrument'].lower().strip()
            if k not in seen:
                seen.add(k)
                u.append(r)
        rows = u
    w = csv.DictWriter(open(f'{R}/{f}.csv', 'w', newline='', encoding='utf-8'), fieldnames=cols, extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
    print(f, len(rows))
