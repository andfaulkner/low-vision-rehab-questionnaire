import sys, re, xml.etree.ElementTree as ET
src, dst = sys.argv[1:3]
raw = open(src, encoding='utf-8').read()
raw = re.sub(r'<!DOCTYPE[^>]*>', '', raw, count=1)
root = ET.fromstring(raw)
def txt(e):
    return re.sub(r'\s+', ' ', ''.join(e.itertext())).strip()
out = ['[page 1]', 'NOTE: reconstructed from the Europe PMC JATS XML of PMC11412607 (open access); the PDF could not be fetched. The XML has no page breaks, so cite section / table / figure labels instead of page numbers.', '']
t = root.find('.//article-title'); out.append('TITLE: ' + txt(t))
for ab in root.findall('.//abstract'):
    out.append('ABSTRACT: ' + txt(ab))
def walk(sec, depth=0):
    ti = sec.find('title')
    out.append('\n' + '#' * (depth + 1) + ' ' + (txt(ti) if ti is not None else ''))
    for ch in sec:
        if ch.tag == 'p': out.append(txt(ch))
        elif ch.tag == 'sec': walk(ch, depth + 1)
        elif ch.tag == 'table-wrap': table(ch)
        elif ch.tag == 'fig': out.append('FIGURE ' + txt(ch))
def table(tw):
    lab = tw.find('label'); cap = tw.find('caption')
    out.append('\nTABLE ' + (txt(lab) if lab is not None else '') + ': ' + (txt(cap) if cap is not None else ''))
    for tr in tw.iter('tr'):
        out.append(' | '.join(txt(c) for c in tr if c.tag in ('td', 'th')))
    for fn in tw.iter('fn'): out.append('TABLE NOTE: ' + txt(fn))
body = root.find('.//body')
for sec in body:
    if sec.tag == 'sec': walk(sec)
    elif sec.tag == 'p': out.append(txt(sec))
    elif sec.tag == 'table-wrap': table(sec)
# any table-wrap not inside a body sec already printed? print leftovers by label check
printed = '\n'.join(out)
for tw in root.iter('table-wrap'):
    lab = tw.find('label')
    if lab is not None and ('TABLE ' + txt(lab) + ':') not in printed: table(tw)
out.append('\nREFERENCES'); 
for r in root.findall('.//ref-list/ref'): out.append(txt(r))
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
