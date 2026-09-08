"""Independent array aggregation of every cross-intensity output from hashed routes.
Does not call production weight or metric functions. Routing independence is tested separately.
"""
from pathlib import Path
import json
import numpy as np
R=Path(__file__).resolve().parent;C=R.parent/'datasets';errors=[];comparisons=0;cities=[]
for fp in sorted((R/'hazard_results').glob('*.json')):
    data=json.loads(fp.read_text());mass=np.load(C/'population_support'/f'{fp.stem}.npz')['endpoint_mass'];n=len(mass)
    dry={s:np.load(data['sources']['dry|'+s]['path'],mmap_mode='r') for s in ['strategic','expanded']}
    valid=np.isfinite(dry['strategic'])&~np.eye(n,dtype=bool)
    lookup={tuple(x[k] for k in ['model','theta','scope','period','grade','mask_policy']):x for x in data['rows']};maximum=np.zeros(3)
    for theta in [5,15,30,None]:
        attractiveness=np.where(valid,1 if theta is None else np.exp(-dry['strategic']/theta),0)
        for model in ['unit','origin','destination','population']:
            origins=mass if model in ['origin','population'] else np.ones(n);destinations=mass if model in ['destination','population'] else np.ones(n)
            q=attractiveness*destinations[None,:];den=q.sum(1);o=origins*(den>0);o/=o.sum();w=np.divide(q,den[:,None],out=np.zeros_like(q),where=den[:,None]>0)*o[:,None]
            assert abs(w.sum()-1)<1e-10
            for key,source in data['sources'].items():
                if key.startswith('dry|'):continue
                scope,rp,grade,policy=key.split('|');wet=np.load(source['path'],mmap_mode='r');finite=valid&np.isfinite(wet);missing=valid&~np.isfinite(wet)
                delta=np.maximum(0,wet[finite]-dry[scope][finite]);wf=w[finite];U=float(w[missing].sum());D=U+float(np.sum(wf*np.minimum(1,delta/dry[scope][finite])));delay=float(np.sum(wf*delta))
                ref=lookup[(model,theta,scope,rp,grade,policy)];err=np.abs(np.array([D,U,delay])-np.array([ref[k] for k in ['D','U','unconditional_finite_delay_minutes']]))
                maximum=np.maximum(maximum,err);comparisons+=3
    assert max(maximum[:2])<1e-10 and maximum[2]<1e-8,(fp.stem,maximum)
    errors.append(maximum);cities.append({'code':fp.stem,'max_errors':maximum.tolist()});print(fp.stem,flush=True)
assert len(cities)==36 and comparisons==41472,(len(cities),comparisons)
out={'status':'PASS','cities':36,'metric_comparisons':comparisons,'max_errors_D_U_delay':np.max(errors,axis=0).tolist(),'scope':'Independent array weight/metric aggregation from documented route matrices; independent routing is in hazard_audit.json.','city_checks':cities}
(R/'factorial_aggregation_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='city_checks'}))
