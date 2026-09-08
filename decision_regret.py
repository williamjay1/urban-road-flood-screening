"""Decision-loss diagnostic, conventional minimax optimization, no outcome validation."""
from pathlib import Path
import itertools,json,hashlib
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.stats import rankdata

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT

def top(v,k):
    return np.argsort(-np.asarray(v),kind='stable')[:k]

def optimize(scores,k):
    m,n=scores.shape
    oracle=np.sort(scores,axis=1)[:,-k:].sum(axis=1)
    assert np.all(oracle>0)
    normalized=scores/oracle[:,None]
    # sum(selected normalized scores) + worst regret >= 1 in each setting.
    matrix=np.vstack([np.r_[np.ones(n),0],np.c_[normalized,np.ones(m)]])
    lb=np.r_[k,np.ones(m)];ub=np.r_[k,np.full(m,np.inf)]
    result=milp(np.r_[np.zeros(n),1],integrality=np.r_[np.ones(n),0],
                bounds=Bounds(np.zeros(n+1),np.ones(n+1)),
                constraints=LinearConstraint(matrix*10000,lb*10000,ub*10000),
                options={'mip_rel_gap':1e-10,'time_limit':120})
    assert result.success,result.message
    selected=np.flatnonzero(result.x[:-1]>.5)
    assert len(selected)==k
    actual=float((1-normalized[:,selected].sum(axis=1)).max())
    assert abs(actual-result.fun)<1e-8,(actual,result.fun)
    return selected,{'objective':actual,'dual_bound':float(result.mip_dual_bound),'gap':float(result.mip_gap)}

def evaluate(scores,selected,k):
    oracle=np.sort(scores,axis=1)[:,-k:].sum(axis=1)
    captured=scores[:,selected].sum(axis=1)
    regret=np.maximum(0,(oracle-captured)/oracle)
    overlap=[len(set(selected)&set(top(row,k))) for row in scores]
    return {'worst_normalized_regret':float(regret.max()),'median_normalized_regret':float(np.median(regret)),
            'minimum_oracle_members_retained':min(overlap),'regret_by_setting':regret.tolist(),
            'captured_score_by_setting':captured.tolist(),'oracle_score_by_setting':oracle.tolist()}

def toy():
    rng=np.random.default_rng(20260908);checks=[]
    for n,k,m in [(6,2,4),(8,3,7),(10,4,5)]:
        for repeat in range(4):
            a=rng.uniform(.01,1,(m,n));selected,report=optimize(a,k)
            exact=min(evaluate(a,np.array(ix),k)['worst_normalized_regret'] for ix in itertools.combinations(range(n),k))
            assert abs(exact-report['objective'])<1e-8
            checks.append({'n':n,'k':k,'m':m,'absolute_error':abs(exact-report['objective'])})
    # Identical scores are genuinely interchangeable, not an optimization improvement.
    tied=np.ones((3,6));_,report=optimize(tied,2);assert report['objective']<1e-10
    return {'status':'PASS','exhaustive_cases':checks,'tie_case':'PASS'}

def main():
    folders=list((SOURCE/'geometric_reference').glob('*.json'))
    if not folders:
        folders=list((SOURCE/'portable_recomputation').glob('*.json'))
    if not folders:
        # Audited dense-demand results have exactly the primary scenario fields.
        folders=list((SOURCE/'dense_demand_results').glob('*.json'))
    assert len(folders)==36,[(str(p),p.name) for p in folders]
    objs={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in sorted(folders)}
    codes=list(objs)
    def key(r):return (r['scope'],r['grade'],r['mask_policy'],r.get('theta'))
    rows={c:{key(r):r for r in obj['scenarios'] if r.get('anchors',384)==384} for c,obj in objs.items()}
    settings=list(rows[codes[0]])
    assert len(settings)==32
    assert all(set(rows[c])==set(settings) for c in codes)
    a=np.array([[rows[c][s]['D'] for c in codes] for s in settings])
    assert np.all(np.isfinite(a)) and np.all((a>=0)&(a<=1))
    base=settings.index(('strategic','exposed','retained',15))
    report={'status':'COMPLETE','estimand':'equal-cost capture of modeled city disruption indices, not observed benefits',
            'codes':codes,'settings':settings,'scores':a.tolist(),'tests':toy(),'source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in folders},'capacities':{}}
    for k in [6,9,12,18]:
        mm,solver=optimize(a,k)
        chosen={'baseline':top(a[base],k),'mean_score':top(a.mean(axis=0),k),
                'mean_rank':top(-np.mean([rankdata(-x) for x in a],axis=0),k),'minimax':mm}
        item={'solver':solver,'strategies':{name:{'selected_codes':[codes[i] for i in ix],**evaluate(a,ix,k)} for name,ix in chosen.items()},'excluded_family_checks':[]}
        for factor,groups in [('demand',list(dict.fromkeys(s[3] for s in settings))),('physical',list(dict.fromkeys(s[:3] for s in settings)))]:
            for group in groups:
                mask=np.array([(s[3] if factor=='demand' else s[:3])==group for s in settings]);train=a[~mask];test=a[mask]
                selected,detail=optimize(train,k)
                choices={'baseline':chosen['baseline'],'mean_score':top(train.mean(axis=0),k),'mean_rank':top(-np.mean([rankdata(-x) for x in train],axis=0),k),'minimax':selected}
                item['excluded_family_checks'].append({'factor':factor,'excluded':group,'solver':detail,'strategies':{name:{'selected_codes':[codes[i] for i in ix],**evaluate(test,ix,k)} for name,ix in choices.items()}})
        report['capacities'][str(k)]=item
    target=ROOT/'decision_regret_results.json';target.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:{n:round(v['worst_normalized_regret'],6) for n,v in x['strategies'].items()} for k,x in report['capacities'].items()}),flush=True)

if __name__=='__main__':main()
