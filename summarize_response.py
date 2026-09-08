from pathlib import Path
import json,sys,numpy as np
from scipy.stats import spearmanr
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
from decision_regret import evaluate,optimize,top
from interval_regret import optimize_interval,regret
a=json.loads((R/'population_analysis.json').read_text());codes=a['codes'];settings=[tuple(s) for s in a['settings']];base=np.array(a['population_scores']);report={}
assert json.loads((R/'response_audit_summary.json').read_text())['status']=='PASS'
results={c:json.loads((R/'response_results'/f'{c}.json').read_text()) for c in codes};units={c:json.loads((R/'response_audits'/f'{c}.json').read_text()) for c in codes}
union=[base]
for variant in ['published_curve','step_20cm','step_50cm']:
 def get(objs,rowkey):return np.array([[next(r['D'] for r in objs[c][rowkey] if (r['scope'],r['grade'],r['mask_policy'],r['theta'],r['variant'])==(*s,variant)) for c in codes] for s in settings])
 mat=get(results,'scenarios');unit=get(units,'unit_rows');union.append(mat)
 delta=mat-base;diff=mat-unit
 ix=np.unravel_index(abs(delta).argmax(),delta.shape)
 choices=a['capacities']['9']['strategies'];shared={n:evaluate(mat,np.array([codes.index(c) for c in r['selected_codes']]),9) for n,r in choices.items()}
 report[variant]={'median_abs_change':float(np.median(abs(delta))),'max_abs_change':float(abs(delta).max()),'signed_min':float(delta.min()),'signed_max':float(delta.max()),'max_city':codes[ix[1]],'max_setting':settings[ix[0]],'matched_rank_min':min(float(spearmanr(x,y).statistic) for x,y in zip(mat,base)),'population_minus_unit_median_abs':float(np.median(abs(diff))),'population_minus_unit_max_abs':float(abs(diff).max()),'original_selection_transfer':shared,'scores':mat.tolist(),'unit_scores':unit.tolist()}
mat=np.concatenate(union);ix,certificate=optimize(mat,9);mean=top(mat.mean(0),9)
box,bcert=optimize_interval(mat.min(0),mat.max(0),9)
report['combined_128']={'rows':128,'minimax':evaluate(mat,ix,9),'certificate':certificate,'mean':evaluate(mat,mean,9),'mean_selected':[codes[i] for i in mean],'minimax_selected':[codes[i] for i in ix],'mean_local_interval_regret':regret(mat.min(0),mat.max(0),mean,9),'interval_minimax':bcert,'interval_minimax_selected':[codes[i] for i in box]}
(R/'response_analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps({v:{k:r[k] for k in ['median_abs_change','max_abs_change','max_city','matched_rank_min','population_minus_unit_median_abs']} for v,r in report.items() if v!='combined_128'}))
