from pathlib import Path
import json,sys,numpy as np
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
import decision_regret as d
from interval_regret import regret
a=json.loads((R/'population_analysis.json').read_text());scores=np.array(a['population_scores']);codes=a['codes'];errors=[]
for k,row in a['capacities'].items():
 for name,s in row['strategies'].items():
  ix=np.array([codes.index(c) for c in s['selected_codes']]);v=d.evaluate(scores,ix,int(k))
  errors.append(abs(v['worst_normalized_regret']-s['worst_normalized_regret']))
  errors.append(abs(regret(scores.min(0),scores.max(0),ix,int(k))-s['independent_interval_regret']))
 assert abs(row['minimax_certificate']['objective']-row['strategies']['population_minimax']['worst_normalized_regret'])<1e-10
 assert row['interval_certificate']['absolute_gap']<2e-6
assert max(errors)<1e-10
out={'status':'PASS','evaluation_comparisons':len(errors),'max_error':max(errors),'scaled_constraint_exhaustive_toys':d.toy()}
(R/'decision_revision_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='scaled_constraint_exhaustive_toys'}))
