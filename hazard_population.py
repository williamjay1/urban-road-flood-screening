"""Frozen cross-intensity comparison and origin/destination decomposition."""
from pathlib import Path
import sys,json,time,argparse,hashlib
import numpy as np
R=Path(__file__).resolve().parent
P=R;sys.path.insert(0,str(P))
import population_routing as p
C=p.CACHE

def write(path,x):
    path.parent.mkdir(exist_ok=True,parents=True)
    t=path.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2),encoding='utf-8');t.replace(path)

def mixed_weights(base,origin,destination,theta):
    valid=np.isfinite(base)&~np.eye(len(base),dtype=bool)
    q=np.where(valid,1. if theta is None else np.exp(-base/theta),0.)*destination[None,:]
    den=q.sum(1);o=origin*(den>0);o/=o.sum()
    q=np.divide(q,den[:,None],out=np.zeros_like(q),where=den[:,None]>0)*o[:,None]
    assert abs(q.sum()-1)<1e-10
    return q

def hazard(code,scope):
    target=R/'hazard_inputs'/code/f'{scope}.npz'
    if target.exists():return dict(np.load(target))
    import rasterio
    from rasterio.windows import Window
    ref=dict(np.load(p.DATA/code/f'{scope}_hazard.npz'))
    source=C/code/('exact_cell/geometry.npz' if scope=='strategic' else 'expanded_classes/exact_RP100.npz')
    coords=np.load(source)['coords'];ref['RP100']=ref.pop('values')
    manifest=json.loads((C/'raster_manifest.json').read_text())
    for rp in ['RP10','RP500']:
        with rasterio.open(manifest[rp]['path']) as ds:
            rr,cc=rasterio.transform.rowcol(ds.transform,coords[:,0],coords[:,1]);rr=np.asarray(rr);cc=np.asarray(cc)
            r0,r1=int(rr.min()),int(rr.max())+1;c0,c1=int(cc.min()),int(cc.max())+1
            tile=ds.read(1,window=Window(c0,r0,c1-c0,r1-r0),boundless=True,fill_value=ds.nodata or 0)
            v=tile[rr-r0,cc-c0].astype(float)
            valid=np.isfinite(v)&(v!=ds.nodata)&(rr>=0)&(rr<ds.height)&(cc>=0)&(cc<ds.width)
            v[~valid]=0;v=np.maximum(v,0);ref[rp]=v
            # Independent raster.sample subset, deterministic across all cities.
            ii=np.unique(np.linspace(0,len(coords)-1,min(101,len(coords)),dtype=int))
            sampled=np.array([z[0] for z in ds.sample(coords[ii])],float)
            sampled[~np.isfinite(sampled)|(sampled==ds.nodata)]=0;sampled=np.maximum(sampled,0)
            assert np.array_equal(sampled,v[ii])
    target.parent.mkdir(exist_ok=True,parents=True);np.savez_compressed(target,**ref)
    return ref

def run(code):
    target=R/'hazard_results'/f'{code}.json'
    if target.exists():return
    t=time.time();pop=dict(np.load(C/'population_support'/f'{code}.npz'));mass=pop['endpoint_mass'];unit=np.ones(len(mass))
    graphs={s:dict(np.load(p.DATA/code/f'{s}_static.npz')) for s in ['strategic','expanded']}
    dry={};sources={};wet={};quality={}
    for scope,a in graphs.items():
        dry[scope],sources['dry|'+scope]=p.matrix(code,scope,a,a['base'],pop[scope+'_nodes'])
        g=hazard(code,scope)
        quality[scope]={'nonmonotone_fraction':float(np.mean((g['RP10']>g['RP100'])|(g['RP100']>g['RP500']))),'hazard_input_sha256':hashlib.sha256((R/'hazard_inputs'/code/f'{scope}.npz').read_bytes()).hexdigest()}
        for rp in ['RP10','RP100','RP500']:
            for policy in ['retained','spurious_zero_bound']:
                depth=g[rp].copy()
                if policy!='retained':depth[g['spurious_mask']]=0
                f=np.select([depth<=.05,depth<=.10,depth<=.20],[1.,.75,.5],default=.25);f[depth>.30]=0
                factor=np.add.reduceat(np.divide(g['fractions'],f,out=np.full(len(f),np.inf),where=f>0),g['spans'][:,0])
                for grade in ['exposed','bridge_immune']:
                    applied=factor.copy()
                    if grade=='bridge_immune':applied[a['bridge']]=1
                    key='|'.join([scope,rp,grade,policy]);wet[key],sources[key]=p.matrix(code,scope,a,a['base']*applied,pop[scope+'_nodes'])
    rows=[];replay=[]
    prior=json.loads((P/'population_reference'/f'{code}.json').read_text())['scenarios']
    for model,origin,dest in [('unit',unit,unit),('origin',mass,unit),('destination',unit,mass),('population',mass,mass)]:
        for theta in [5,15,30,None]:
            w=mixed_weights(dry['strategic'],origin,dest,theta)
            if model in ['population','unit']:
                oldw,_=p.weights(dry['strategic'],origin,theta);assert np.allclose(oldw,w,rtol=0,atol=1e-14);del oldw
            for key,tt in wet.items():
                scope,rp,grade,policy=key.split('|');metrics=p.metrics(dry[scope],tt,w)
                row={'model':model,'theta':theta,'scope':scope,'period':rp,'grade':grade,'mask_policy':policy,**metrics};rows.append(row)
                if rp=='RP100' and model in ['population','unit']:
                    ref=next(x for x in prior if all(x[k]==row[k] for k in ['model','theta','scope','grade','mask_policy']))
                    replay.extend(abs(metrics[k]-ref[k]) for k in ['D','U','unconditional_finite_delay_minutes'])
            del w
    assert len(rows)==384 and max(replay)<1e-10
    write(target,{'code':code,'status':'COMPLETE','rows':rows,'sources':sources,'quality':quality,'prior_replay_max_error':max(replay),'seconds':time.time()-t})
    print(json.dumps({'code':code,'seconds':time.time()-t,'rows':len(rows)}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--codes',nargs='*');args=ap.parse_args()
    codes=args.codes or [x['code'] for x in json.loads((P/'population_support_audit.json').read_text())['cities']]
    for code in codes:run(code)
