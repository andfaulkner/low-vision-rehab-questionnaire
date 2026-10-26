import csv,sys,re
i=sys.argv[1]
for p in ('A','B'):
    print('== pass',p)
    for r in csv.DictReader(open(f'analysis/extraction/pass{p}/{i}/dta.csv')):
        it=re.findall(r'Q\d+',r['item_text']) or [r['item_text'][:25]]
        print('+'.join(it),'|',r['threshold'][:22],'|',r['ref_threshold_logmar'],'| n',r['n'],'npos',r['n_positive'],'| sens',r['sens'],'spec',r['spec'],'auc',r['auc'],'| pg',r['page'][:18])
