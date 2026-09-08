"""Recompute primary flood screening from frozen graph and cell-intersection data.

Usage: python portable_primary_recompute.py --data datasets --reference results
       --output recomputed --codes BE004L2 [more codes]
Requires Python 3.10+, NumPy and SciPy. All supplied directories are explicit;
there are no dependencies on the originating workstation's path layout.
"""
from pathlib import Path
import argparse,json,hashlib,time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

def solve(a,physical_cost,anchors):
    n=len(a['nodes']);cost=physical_cost[a['phys']];keep=np.isfinite(cost)
    keys=a['au'][keep].astype(np.int64)*n+a['av'][keep];values=cost[keep]
    order=np.argsort(keys,kind='stable');keys=keys[order];values=values[order]
    starts=np.r_[0,np.flatnonzero(np.diff(keys))+1] if len(keys) else np.array([],dtype=int)
    pair=keys[starts];best=np.minimum.reduceat(values,starts) if len(starts) else values
    graph=csr_matrix((best,(pair//n,pair%n)),shape=(n,n))
    result=np.empty((len(anchors),len(anchors)))
    for first in range(0,len(anchors),24):
        result[first:first+24]=dijkstra(graph,directed=True,indices=anchors[first:first+24])[:,anchors]
    return result

def anchors(a,count):
    chosen=list(map(int,a['anchors']));xy=a['nodes'].astype(float);closest=np.full(len(xy),np.inf)
    for i in chosen:closest=np.minimum(closest,np.sum((xy-xy[i])**2,axis=1))
    closest[chosen]=-1
    while len(chosen)<count:
        i=int(np.argmax(closest));chosen.append(i);closest=np.minimum(closest,np.sum((xy-xy[i])**2,axis=1));closest[i]=-1
    return np.array(chosen)

def metric(base,stressed,strategic,theta):
    support=np.isfinite(strategic)&~np.eye(len(base),dtype=bool)
    w=np.zeros_like(base);w[support]=1. if theta is None else np.exp(-strategic[support]/theta);w/=w.sum()
    assert np.all(np.isfinite(base[support]))
    missing=support&~np.isfinite(stressed);finite=support&np.isfinite(stressed)
    loss=np.zeros_like(base);fixed=np.zeros_like(base);loss[missing]=fixed[missing]=1
    loss[finite]=np.clip((stressed[finite]-base[finite])/base[finite],0,1)
    fixed[finite]=np.clip((stressed[finite]-base[finite])/strategic[finite],0,1)
    return {'D':float(np.sum(w*loss)),'U':float(np.sum(w[missing])),'fixed_denominator_loss':float(np.sum(w*fixed))}

def run(code,data,reference,output):
    start=time.time();folder=data/code;graphs={s:dict(np.load(folder/f'{s}_static.npz')) for s in ['strategic','expanded']}
    ix=anchors(graphs['strategic'],384);coords=graphs['strategic']['nodes'][ix];nodes={}
    for scope,a in graphs.items():
        lookup={tuple(p):i for i,p in enumerate(a['nodes'])};nodes[scope]=np.array([lookup[tuple(p)] for p in coords])
    dry={s:solve(a,a['base'],nodes[s]) for s,a in graphs.items()};rows=[]
    for scope,a in graphs.items():
        geom=np.load(folder/f'{scope}_hazard.npz');fractions=geom['fractions'];spans=geom['spans'];values=geom['values'];mask=geom['spurious_mask']
        for policy in ['retained','spurious_zero_bound']:
            depth=values.copy()
            if policy!='retained':depth[mask]=0
            f=np.select([depth<=.05,depth<=.10,depth<=.20],[1.,.75,.5],default=.25);f[depth>.30]=0
            rates=np.divide(fractions,f,out=np.full(len(f),np.inf),where=f>0);factor=np.add.reduceat(rates,spans[:,0])
            for grade in ['exposed','bridge_immune']:
                applied=factor.copy()
                if grade=='bridge_immune':applied[a['bridge']]=1
                wet=solve(a,a['base']*applied,nodes[scope])
                for n in [48,96,192,384]:
                    for theta in ([5,15,30,None] if n==384 else [15]):
                        rows.append({'scope':scope,'mask_policy':policy,'grade':grade,'anchors':n,'theta':theta,**metric(dry[scope][:n,:n],wet[:n,:n],dry['strategic'][:n,:n],theta)})
    ref=json.loads((reference/f'{code}.json').read_text(encoding='utf-8'));expected={(r['scope'],r['mask_policy'],r['grade'],r['anchors']):r for r in ref['scenarios']}
    errors=[]
    for row in rows:
        key=tuple(row[k] for k in ['scope','mask_policy','grade','anchors'])
        if row['theta']==15 and key in expected:
            for metric_name in ['D','U','fixed_denominator_loss']:errors.append(abs(row[metric_name]-expected[key][metric_name]))
    assert len(errors)==72 and max(errors)<1e-10,(code,max(errors),len(errors))
    result={'code':code,'status':'PASS','comparison_count':len(errors),'max_absolute_reference_error':max(errors),'seconds':time.time()-start,'scenarios':rows,'anchor_coordinates':coords.tolist(),'scope':'Fresh shortest paths from frozen derived graph and hazard intersections; not an independent hazard or traffic validation.'}
    output.mkdir(parents=True,exist_ok=True);target=output/f'{code}.json';temporary=target.with_suffix('.tmp');temporary.write_text(json.dumps(result,indent=2),encoding='utf-8');temporary.replace(target)
    print(json.dumps({k:result[k] for k in ['code','status','comparison_count','max_absolute_reference_error','seconds']}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--codes',nargs='+',required=True);args=ap.parse_args()
    for code in args.codes:
        target=args.output/f'{code}.json'
        if target.exists():
            prior=json.loads(target.read_text(encoding='utf-8'))
            if prior.get('status')=='PASS':continue
        run(code,args.data,args.reference,args.output)
