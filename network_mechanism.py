"""Separate direct endpoint isolation from disconnection beyond live endpoints."""
from pathlib import Path
import json,sys
import numpy as np
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import hazard_population as h
p=h.p;C=h.C
for fp in sorted((R/'hazard_reference').glob('*.json')):
    out=R/'mechanism_results'/fp.name
    if out.exists():continue
    x=json.loads(fp.read_text());code=fp.stem;pop=dict(np.load(C/'population_support'/f'{code}.npz'));dry=np.load(x['sources']['dry|strategic']['path'])
    w,_=p.weights(dry,pop['endpoint_mass'],15);rows=[];profiles={}
    for scope in ['strategic','expanded']:
        a=dict(np.load(p.DATA/code/f'{scope}_static.npz'));g=dict(np.load(R/'hazard_inputs'/code/f'{scope}.npz'));ix=pop[scope+'_nodes']
        for rp in ['RP10','RP100','RP500']:
            closed=np.maximum.reduceat(g[rp],g['spans'][:,0])>.30
            live=~closed[a['phys']];outdeg=np.bincount(a['au'][live],minlength=len(a['nodes']));indeg=np.bincount(a['av'][live],minlength=len(a['nodes']))
            wet=np.load(x['sources']['|'.join([scope,rp,'exposed','retained'])]['path'],mmap_mode='r');local=remote=0.;profile=[]
            for start in range(0,len(w),64):
                ww=w[start:start+64];miss=~np.isfinite(wet[start:start+64]);adjacent=(outdeg[ix[start:start+64]]==0)[:,None]|(indeg[ix]==0)[None,:]
                local+=float(ww[miss&adjacent].sum());remote+=float(ww[miss&~adjacent].sum())
                den=ww.sum(1);profile.extend(np.divide((ww*miss).sum(1),den,out=np.zeros(len(den)),where=den>0).tolist())
            ref=next(z for z in x['rows'] if z['scope']==scope and z['period']==rp and z['grade']=='exposed' and z['mask_policy']=='retained' and z['model']=='population' and z['theta']==15)
            assert abs(local+remote-ref['U'])<1e-12
            rows.append({'scope':scope,'period':rp,'local_endpoint_isolation_U':local,'remote_disconnection_U':remote,'total_U':local+remote,'remote_fraction_of_U':remote/(local+remote) if local+remote else None})
            profiles[scope+'|'+rp]=profile
    h.write(out,{'code':code,'rows':rows,'origin_disconnection_profiles':profiles,'interpretation':'Remote means a positive-cost live outgoing arc at the origin and live incoming arc at destination still exist, but no directed route joins them. It does not mean both residential cells are unflooded.'})
    print(json.dumps({'code':code,'rows':len(rows)}),flush=True)
