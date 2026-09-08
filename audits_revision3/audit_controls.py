from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parent;C=R.parent/'datasets';files=sorted((R/'depth_order_results').glob('*.json'));assert len(files)==36
seen=set();errors=[];count=0;identity_cities=0;mechanism_errors=[]
for f in files:
    q=json.loads(f.read_text());raw=json.loads((R/'hazard_results'/f.name).read_text());dry={s:np.load(raw['sources']['dry|'+s]['path'],mmap_mode='r') for s in ['strategic','expanded']}
    mass=np.load(C/'population_support'/f'{f.stem}.npz')['endpoint_mass'];n=len(mass)
    for source in q['sources'].values():
        if source['path'] not in seen:
            assert hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256'];seen.add(source['path'])
    if not q['cost_changed_scenarios']:identity_cities+=1
    for row in q['cost_changed_scenarios']:
        source=q['sources']['|'.join(row[k] for k in ['scope','period','grade','mask_policy'])];wet=np.load(source['path'],mmap_mode='r');m=mass if row['model']=='population' else np.ones(n)
        support=np.isfinite(dry['strategic'])&~np.eye(n,dtype=bool)
        propensity=np.where(support,1 if row['theta'] is None else np.exp(-dry['strategic']/row['theta']),0)*m[None,:]
        den=propensity.sum(1);included=den>0;origin=m*included;origin=origin/origin.sum();D=U=0.
        for i in range(n):
            if not included[i]:continue
            w=origin[i]*propensity[i]/den[i];unreachable=~np.isfinite(wet[i]);U+=w[unreachable].sum()
            good=support[i]&~unreachable
            D+=w[unreachable].sum()+np.sum(w[good]*np.clip((wet[i,good]-dry[row['scope']][i,good])/dry[row['scope']][i,good],0,1))
        errors.extend([abs(D-row['cumulative_D']),abs(U-row['cumulative_U'])]);count+=2
        assert row['delta_D']>=-1e-10 and row['delta_U']>=-1e-10
    mech=json.loads((R/'mechanism_results'/f.name).read_text())
    for row in mech['rows']:
        ref=next(x for x in raw['rows'] if x['model']=='population' and x['theta']==15 and x['scope']==row['scope'] and x['period']==row['period'] and x['grade']=='exposed' and x['mask_policy']=='retained')
        mechanism_errors.append(abs(row['local_endpoint_isolation_U']+row['remote_disconnection_U']-ref['U']))
assert max(errors or [0])<1e-10 and max(mechanism_errors)<1e-10
out={'status':'PASS','cities':36,'cumulative_metric_recalculations':count,'unique_cumulative_matrix_hashes':len(seen),'max_absolute_error':max(errors or [0]),'unchanged_cost_cities':identity_cities,'mechanism_component_checks':len(mechanism_errors),'max_mechanism_additivity_error':max(mechanism_errors)}
(R/'controls_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
