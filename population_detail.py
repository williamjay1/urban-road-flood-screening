from pathlib import Path
import json,numpy as np
from scipy.stats import spearmanr
R=Path(__file__).resolve().parent;a=json.loads((R/'population_analysis.json').read_text());codes=a['codes'];settings=a['settings'];P=np.array(a['population_scores']);U=np.array(a['unit_scores'])
means=(P-U).mean(0);report={'largest_mean_target_differences':[{'code':codes[i],'mean_difference':float(means[i])} for i in np.argsort(-abs(means))[:6]],'physical':{}}
for name,column in [('road',0),('bridge',1),('mask',2)]:
 dif=[]
 for j,s in enumerate(settings):
  if s[3]!=15:continue
  for k,t in enumerate(settings[j+1:],start=j+1):
   if t[3]==15 and all(s[x]==t[x] for x in range(4) if x!=column) and s[column]!=t[column]:dif.append(P[j]-P[k])
 arr=np.array(dif)
 report['physical'][name]={'median_abs':float(np.median(abs(arr))),'max_abs':float(abs(arr).max()),'mean_abs_by_city':dict(zip(codes,abs(arr).mean(0).tolist()))}
report['population_min_pairwise_rank']=min(float(spearmanr(p,q).statistic) for i,p in enumerate(P) for q in P[i+1:])
report['extreme_target_examples']=[]
for i in np.argsort(-abs(means))[:3]:
 rows=json.loads((R/'population_reference'/f'{codes[i]}.json').read_text())['scenarios']
 report['extreme_target_examples'].append({'code':codes[i],'rows':[r for r in rows if r['model'] in ['unit','population'] and r['theta']==15 and r['scope']=='strategic' and r['mask_policy']=='retained']})
(R/'population_detail.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
