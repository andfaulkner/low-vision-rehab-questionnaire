# PROVISIONAL: lead's resolutions applied after merge.py. Run: python3 -I analysis/extraction/apply_resolutions.py
import csv
R = 'analysis/extraction'
BY = 'AI chain step 5 (advisory)'
log = []


def load(f):
    r = csv.DictReader(open(f'{R}/{f}.csv', encoding='utf-8'))
    return r.fieldnames, list(r)


def save(f, cols, rows):
    w = csv.DictWriter(open(f'{R}/{f}.csv', 'w', newline='', encoding='utf-8'), fieldnames=cols)
    w.writeheader()
    w.writerows(rows)


cols, eff = load('effects')


def fix(sid, estimate, comp_start, n, note):
    for r in eff:
        if r['study_id'] == str(sid) and r['estimate'] == estimate and r['comparator'].startswith(comp_start) and r['n'] == 'NR':
            r['n'] = str(n)
            r['derivation'] = (r['derivation'] + '; n assumed: ' + note).strip('; ')
            log.append((sid, 'effects', f'{r["comparator"][:40]} est {estimate}', 'n', 'NR', str(n), note))
            return
    raise SystemExit(f'not found {sid} {estimate}')


fix(95, '-0.28', 'binocular VA', 405, 'N = 405 rated the 21 driving tasks (p3); pairs not stated, unconfirmed')
fix(95, '0.35', 'binocular log contrast', 405, 'N = 405 rated the 21 driving tasks (p3); pairs not stated, unconfirmed')
fix(95, '-0.69', 'overall driving difficulty', 405, 'N = 405 rated the 21 driving tasks (p3); pairs not stated, unconfirmed')
fix(119, '0.41', 'EQ 5D-5L Self-care', 257, 'only the public-hospital sub-sample (n = 257, p2) completed the EQ 5D-5L (p3); pairs not stated')
fix(119, '0.73', 'EQ 5D-5L Usual activities', 257, 'only the public-hospital sub-sample (n = 257, p2) completed the EQ 5D-5L (p3); pairs not stated')
fix(120, '0.576', 'low-contrast VA', 20, '30 participants (p1) minus 10 who could not read the low-contrast chart (p4); inferred, Table 2 says only that the sample was reduced')
save('effects', cols, eff)

# dta: study 27 reference is a composite, so no pure VA logMAR; pass A had 0.1 on some rows, pass B blank. Pass B (blank) kept.
with open(f'{R}/resolutions.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['study_id', 'file', 'row', 'column', 'value_before', 'resolved_value', 'basis', 'resolved_by'])
    for s, f, row, col, b, a, note in log:
        w.writerow([s, f, row, col, b, a, note, BY])
    # dta numeric checks done by the lead against the text (sens/spec/n identical in pass A and B on every overlapping row)
    w.writerow([92, 'dta', 'Q97 (0.3 logMAR) and Q30 (1.0 logMAR) headline rows', 'sens/spec/auc', 'A=B', 'A=B', 'checked against text p1 (abstract) and p4: Q97 AUC 0.85, sens 0.89, spec 0.81; Q30 AUC 0.80, sens 0.89, spec 0.71', BY])
    w.writerow([119, 'dta', 'cut-off 105 or 106', 'sens/spec', 'A=B', '0.954/0.918', 'checked against text p1, p4 (95.4% / 91.8%)', BY])
    w.writerow([27, 'dta', 'whole file', 'rows', 'A 5 rows, B 20 rows', 'B (20 rows)', 'identical sens/spec/n/positives on all 5 overlapping rows; B adds questions A could not assign from the scrambled Table 1; ref_threshold_logmar left blank (composite reference)', BY])
    w.writerow([38, 'dta', 'reading problems, blurred vision', 'sens/spec', 'A=B', 'Table 4.1 values', 'both passes follow Table 4.1 (0.839/0.747; 0.791/0.867); the text on p15 pairs them differently', BY])
    w.writerow([79, 'dta', 'all 8 rows', 'sens/spec', 'A=B', 'A=B', 'identical on all 8 rows (Table 4 p5); no 2x2 counts reported', BY])
print(len(log), 'n resolutions')
