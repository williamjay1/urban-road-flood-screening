from pathlib import Path
import sys,json,hashlib,time,argparse,traceback
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from portable_primary_recompute import solve
CACHE=ROOT
DATA=ROOT/'datasets'

def weights(base,mass,theta):
    support=np.isfinite(base)&~np.eye(len(base),dtype=bool)
    attractiveness=np.where(support,1. if theta is None else np.exp(-base/theta),0.)*mass[None,:]
    denominator=attractiveness.sum(axis=1)
    included=(denominator>0)&(mass>0)
    origin=np.where(included,mass,0.);origin/=origin.sum()
    w=np.divide(attractiveness,denominator[:,None],out=np.zeros_like(attractiveness),where=denominator[:,None]>0)*origin[:,None]
    assert abs(w.sum()-1)<1e-10
    assert np.max(abs(w.sum(axis=1)-origin))<1e-10
    return w,{'dry_origin_population_retained':float(mass[included].sum()/mass.sum()),'coincident_endpoint_population_pair_share':float(np.sum((mass/mass.sum())**2))}

def metrics(base,wet,w):
    d=u=delay=0.
    for start in range(0,len(w),64):
        ww=w[start:start+64];bb=base[start:start+64];tt=wet[start:start+64]
        support=ww>0;missing=support&~np.isfinite(tt);finite=support&np.isfinite(tt)
        assert np.all(tt[finite]>=bb[finite]-1e-7)
        delta=np.maximum(0,tt[finite]-bb[finite]);wf=ww[finite]
        lost=float(ww[missing].sum());u+=lost
        d+=lost+float(np.sum(wf*np.clip(delta/bb[finite],0,1)))
        delay+=float(np.sum(wf*delta))
    return {'D':d,'U':u,'unconditional_finite_delay_minutes':delay,'conditional_finite_delay_minutes':delay/(1-u) if u<1 else None}

def matrix(code,scope,a,cost,ix):
    folder=CACHE/'population_routes'/code/scope;folder.mkdir(parents=True,exist_ok=True)
    h=hashlib.sha256()
    for x in [a['nodes'],a['au'],a['av'],a['phys'],cost,ix]:
        h.update(str((x.shape,str(x.dtype))).encode());h.update(np.ascontiguousarray(x).tobytes())
    path=folder/(h.hexdigest()+'.npy')
    if not path.exists():
        value=solve(a,cost,ix)
        tmp=path.with_suffix('.tmp')
        with tmp.open('wb') as f:np.save(f,value)
        tmp.replace(path)
    value=np.load(path,mmap_mode='r');assert value.shape==(len(ix),len(ix))
    assert np.all(value.diagonal()==0)
    return value,{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def run(code):
    begin=time.time();out=ROOT/'population_results';out.mkdir(exist_ok=True);target=out/f'{code}.json'
    if target.exists() and json.loads(target.read_text()).get('status')=='COMPLETE':return
    p=dict(np.load(CACHE/'population_support'/f'{code}.npz'))
    graphs={s:dict(np.load(DATA/code/f'{s}_static.npz')) for s in ['strategic','expanded']}
    ix={s:p[f'{s}_nodes'] for s in graphs};dry={};matrix_sources={}
    for s,a in graphs.items():dry[s],matrix_sources['dry_'+s]=matrix(code,s,a,a['base'],ix[s])
    # Pre-flood support is frozen on strategic routes for every comparison.
    mass_models={'population':p['endpoint_mass'],'unit':np.ones(len(p['endpoint_mass']))}
    for label,keep in [('snap1km',p['cell_snap_m']<=1000),('snap2km',p['cell_snap_m']<=2000),('interior',p['cell_area_fraction']>=1-1e-12)]:
        mass_models[label]=np.bincount(p['cell_to_endpoint'],weights=p['cell_mass']*keep,minlength=len(p['endpoint_mass']))
    rows=[];support_audit={}
    # Rebuild a weight matrix at a time, avoiding 20 resident N*N matrices in memory.
    wet_sources={};wet_matrices={}
    for scope,a in graphs.items():
        geom=np.load(DATA/code/f'{scope}_hazard.npz')
        for policy in ['retained','spurious_zero_bound']:
            depth=geom['values'].copy()
            if policy!='retained':depth[geom['spurious_mask']]=0
            f=np.select([depth<=.05,depth<=.10,depth<=.20],[1.,.75,.5],default=.25);f[depth>.30]=0
            rates=np.divide(geom['fractions'],f,out=np.full(len(f),np.inf),where=f>0)
            factor=np.add.reduceat(rates,geom['spans'][:,0])
            for grade in ['exposed','bridge_immune']:
                applied=factor.copy()
                if grade=='bridge_immune':applied[a['bridge']]=1
                setting=(scope,grade,policy)
                wet_matrices[setting],wet_sources['|'.join(setting)]=matrix(code,scope,a,a['base']*applied,ix[scope])
    for model,mass in mass_models.items():
        for theta in ([5,15,30,None] if model in ['population','unit'] else [15]):
            w,audit=weights(dry['strategic'],mass,theta)
            audit['population_mass_before_dry_support']=float(mass.sum())
            audit['fraction_of_full_population']=float(mass.sum()/p['endpoint_mass'].sum()) if model!='unit' else None
            support_audit[f'{model}|{theta}']=audit
            for setting,wet in wet_matrices.items():
                scope,grade,policy=setting
                rows.append({'model':model,'theta':theta,'scope':scope,'grade':grade,'mask_policy':policy,**metrics(dry[scope],wet,w)})
    result={'code':code,'status':'COMPLETE','seconds':time.time()-begin,'endpoint_count':len(p['endpoint_mass']),'population_sum':float(p['endpoint_mass'].sum()),'support':support_audit,'scenarios':rows,'dry_matrices':matrix_sources,'wet_matrices':wet_sources,'population_support_sha256':hashlib.sha256((CACHE/'population_support'/f'{code}.npz').read_bytes()).hexdigest()}
    temp=target.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2),encoding='utf-8');temp.replace(target)
    print(json.dumps({'code':code,'seconds':result['seconds'],'endpoints':result['endpoint_count'],'rows':len(rows)}),flush=True)

def toy_tests():
    base=np.array([[0.,1.,2.],[1.,0.,np.inf],[2.,3.,0.]])
    w,a=weights(base,np.array([1.,2.,3.]),None)
    assert np.allclose(w.sum(axis=1),np.array([1,2,3])/6)
    assert w[1,2]==0 and np.all(w.diagonal()==0)
    assert metrics(base,base,w)['D']==0
    wet=base.copy();wet[~np.eye(3,dtype=bool)]=np.inf
    m=metrics(base,wet,w);assert abs(m['D']-1)<1e-12 and abs(m['U']-1)<1e-12
    (ROOT/'population_metric_tests.json').write_text(json.dumps({'status':'PASS','cases':['origin mass conservation','dry unreachable zero weight','diagonal excluded','dry identity zero loss','complete closure unit loss']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--codes',nargs='*');args=parser.parse_args();toy_tests()
    codes=args.codes or [x['code'] for x in json.loads((ROOT/'population_support_audit.json').read_text())['cities']]
    done=[];errors={}
    for code in codes:
        try:run(code);done.append(code)
        except Exception as exc:errors[code]={'error':repr(exc),'traceback':traceback.format_exc()};print(json.dumps(errors[code]),flush=True)
        (ROOT/'population_routing_status.json').write_text(json.dumps({'status':'RUNNING','requested':codes,'done':done,'errors':errors},indent=2))
    (ROOT/'population_routing_status.json').write_text(json.dumps({'status':'COMPLETE' if not errors else 'FAILED','requested':codes,'done':done,'errors':errors},indent=2))
