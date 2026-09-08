from pathlib import Path
import sys,json,time
import numpy as np
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import population_routing as p

def response_factor(a,geom,depth,variant):
    if variant=='published_curve':
        # length is km, baseline cost is minutes.
        speed=a['length']/a['base']*60
        parent=np.repeat(np.arange(len(a['base'])),geom['spans'][:,1]-geom['spans'][:,0])
        assert len(parent)==len(depth)
        mm=depth*1000;limit=.0009*mm**2-.5529*mm+86.9448
        multiplier=np.where(depth<=0,1.,np.minimum(1.,limit/speed[parent]));multiplier[depth>.30]=0
    else:
        threshold={'step_20cm':.20,'step_50cm':.50}[variant]
        multiplier=np.select([depth<=.05,depth<=.10,depth<=.20],[1.,.75,.5],default=.25);multiplier[depth>threshold]=0
    assert np.all((multiplier>=0)&(multiplier<=1))
    rates=np.divide(geom['fractions'],multiplier,out=np.full(len(multiplier),np.inf),where=multiplier>0)
    return np.add.reduceat(rates,geom['spans'][:,0])

def test():
    a={'length':np.array([1.,1.,1.,1.]),'base':np.full(4,1.2)}
    geom={'spans':np.array([[0,1],[1,2],[2,3],[3,4]]),'fractions':np.ones(4)}
    d=np.array([0.,.1,.3,.300001]);f=response_factor(a,geom,d,'published_curve')
    assert f[0]==1 and abs(f[1]-50/40.6548)<1e-10 and abs(f[2]-50/2.0748)<1e-8 and np.isinf(f[3])
    (ROOT/'response_formula_tests.json').write_text(json.dumps({'status':'PASS','depth_mm':[0,100,300,300.001],'road_speed_kmh':50,'cost_factors':[float(x) if np.isfinite(x) else 'closed' for x in f]},indent=2))

def run(code):
    begin=time.time();out=ROOT/'response_results';out.mkdir(exist_ok=True);target=out/f'{code}.json'
    if target.exists() and json.loads(target.read_text()).get('status')=='COMPLETE':return
    original=json.loads((ROOT/'population_results'/f'{code}.json').read_text());pop=np.load(p.CACHE/'population_support'/f'{code}.npz')
    graphs={s:dict(np.load(p.DATA/code/f'{s}_static.npz')) for s in ['strategic','expanded']}
    bases={s:np.load(original['dry_matrices']['dry_'+s]['path'],mmap_mode='r') for s in graphs}
    rows=[];sources={}
    for scope,a in graphs.items():
        geom=dict(np.load(p.DATA/code/f'{scope}_hazard.npz'))
        for policy in ['retained','spurious_zero_bound']:
            depth=geom['values'].copy()
            if policy!='retained':depth[geom['spurious_mask']]=0
            for variant in ['published_curve','step_20cm','step_50cm']:
                factor=response_factor(a,geom,depth,variant)
                for grade in ['exposed','bridge_immune']:
                    applied=factor.copy()
                    if grade=='bridge_immune':applied[a['bridge']]=1
                    wet,source=p.matrix(code,scope,a,a['base']*applied,pop[f'{scope}_nodes'])
                    sources['|'.join([variant,scope,grade,policy])]=source
                    original_setting=next(x for x in original['scenarios'] if (x['model'],x['theta'],x['scope'],x['grade'],x['mask_policy'])==('population',15,scope,grade,policy))
                    for theta in [5,15,30,None]:
                        w,audit=p.weights(bases['strategic'],pop['endpoint_mass'],theta)
                        met=p.metrics(bases[scope],wet,w)
                        ref=next(x for x in original['scenarios'] if (x['model'],x['theta'],x['scope'],x['grade'],x['mask_policy'])==('population',theta,scope,grade,policy))
                        if variant=='published_curve':assert abs(met['U']-ref['U'])<1e-10
                        if variant=='step_20cm':assert met['D']>=ref['D']-1e-10 and met['U']>=ref['U']-1e-10
                        if variant=='step_50cm':assert met['D']<=ref['D']+1e-10 and met['U']<=ref['U']+1e-10
                        rows.append({'variant':variant,'scope':scope,'grade':grade,'mask_policy':policy,'theta':theta,**met})
    result={'code':code,'status':'COMPLETE','seconds':time.time()-begin,'scenarios':rows,'matrix_sources':sources,'checks':'curve same reachability and threshold monotonicity passed for all rows'}
    temp=target.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2));temp.replace(target)
    print(json.dumps({'code':code,'response':'COMPLETE','seconds':result['seconds'],'rows':len(rows)}),flush=True)

if __name__=='__main__':test();run(sys.argv[1])
