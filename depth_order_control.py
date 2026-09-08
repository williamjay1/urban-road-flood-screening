"""Explicit monotone-depth envelope control, never a silent hazard correction."""
from pathlib import Path
import json,sys,argparse
import numpy as np
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import hazard_population as h
p=h.p;C=h.C
parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--shard',type=int,default=0);parser.add_argument('--shards',type=int,default=1);partition,_=parser.parse_known_args()
for position,fp in enumerate(sorted((R/'hazard_results').glob('*.json'))):
    if position%partition.shards!=partition.shard:continue
    out=R/'depth_order_results'/fp.name
    if out.exists():
        previous=json.loads(out.read_text())
        if all('model' in row for row in previous['cost_changed_scenarios']):continue
        h.write(R/'depth_order_legacy'/fp.name,previous)
    print('START '+fp.stem,flush=True)
    x=json.loads(fp.read_text());code=fp.stem;pop=dict(np.load(C/'population_support'/f'{code}.npz'));dry={s:np.load(x['sources']['dry|'+s]['path']) for s in ['strategic','expanded']};changes=[];sources={}
    for scope in ['strategic','expanded']:
        g=dict(np.load(R/'hazard_inputs'/code/f'{scope}.npz'));a=dict(np.load(p.DATA/code/f'{scope}_static.npz'))
        raw=np.array([g[rp] for rp in ['RP10','RP100','RP500']]);cum=np.maximum.accumulate(raw,axis=0)
        for j,rp in enumerate(['RP10','RP100','RP500']):
            if np.array_equal(raw[j],cum[j]):continue
            for policy in ['retained','spurious_zero_bound']:
                factors=[]
                for field in [raw[j],cum[j]]:
                    d=field.copy()
                    if policy!='retained':d[g['spurious_mask']]=0
                    f=np.select([d<=.05,d<=.10,d<=.20],[1.,.75,.5],default=.25);f[d>.30]=0
                    factors.append(np.add.reduceat(np.divide(g['fractions'],f,out=np.full(len(f),np.inf),where=f>0),g['spans'][:,0]))
                for grade in ['exposed','bridge_immune']:
                    aa,bb=[f.copy() for f in factors]
                    if grade=='bridge_immune':aa[a['bridge']]=1;bb[a['bridge']]=1
                    if np.array_equal(aa,bb):continue
                    tt,source=p.matrix(code,scope,a,a['base']*bb,pop[scope+'_nodes']);sources['|'.join([scope,rp,grade,policy])]=source
                    for model,mass in [('population',pop['endpoint_mass']),('unit',np.ones(len(pop['endpoint_mass'])))]:
                        for theta in [5,15,30,None]:
                            w,_=p.weights(dry['strategic'],mass,theta);met=p.metrics(dry[scope],tt,w)
                            ref=next(z for z in x['rows'] if z['model']==model and z['theta']==theta and z['period']==rp and z['scope']==scope and z['grade']==grade and z['mask_policy']==policy)
                            assert met['D']>=ref['D']-1e-10 and met['U']>=ref['U']-1e-10
                            changes.append({'model':model,'period':rp,'scope':scope,'grade':grade,'mask_policy':policy,'theta':theta,'raw_D':ref['D'],'raw_U':ref['U'],'cumulative_D':met['D'],'cumulative_U':met['U'],'delta_D':met['D']-ref['D'],'delta_U':met['U']-ref['U']})
    h.write(out,{'code':code,'status':'COMPLETE','cost_changed_scenarios':changes,'sources':sources,'unchanged_scenarios':'Exact identity of the applied cost array establishes zero change; no redundant routing performed.'})
    print(json.dumps({'code':code,'changed_scenarios':len(changes)}),flush=True)
