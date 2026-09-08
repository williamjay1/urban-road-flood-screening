"""Exact interval-selection regret via a conventional top-k epigraph MILP.

An adversary sets selected scores to lower endpoints and unselected to upper.
For fixed rho, L*x >= (1-rho)*(k*t + sum(z)), z>=U-(U-L)*x-t.
Binary search gives an explicit gap certificate on the minimum relative regret.
These independent intervals are scenario bounds, not simultaneous probabilities.
"""
import itertools,json
from pathlib import Path
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint

def regret(lo,hi,selected,k):
    v=hi.copy();v[selected]=lo[selected];oracle=np.sort(v)[-k:].sum()
    return max(0,float(1-lo[selected].sum()/oracle))

def feasible(lo,hi,k,rho):
    n=len(lo);size=2*n+1
    # order x, t, z; t>=0 suffices for nonnegative scores.
    equality=np.r_[np.ones(n),np.zeros(n+1)]
    zrows=np.c_[np.diag(hi-lo),np.ones(n),np.eye(n)]
    capture=np.r_[lo,-(1-rho)*k,-(1-rho)*np.ones(n)]
    A=np.vstack([equality,zrows,capture]);lb=np.r_[k,hi,0.];ub=np.r_[k,np.full(n+1,np.inf)]
    result=milp(np.zeros(size),integrality=np.r_[np.ones(n),np.zeros(n+1)],bounds=Bounds(np.zeros(size),np.r_[np.ones(n),hi.max(),np.full(n,hi.max())]),constraints=LinearConstraint(A,lb,ub),options={'time_limit':60,'mip_rel_gap':0})
    if result.status==2:return None
    assert result.success,result.message
    ix=np.flatnonzero(result.x[:n]>.5);assert len(ix)==k
    assert regret(lo,hi,ix,k)<=rho+1e-6
    return ix

def optimize_interval(lo,hi,k,tol=1e-6):
    left=0.;right=1.;selected=np.argsort(-lo)[:k]
    while right-left>tol:
        mid=(left+right)/2;trial=feasible(lo,hi,k,mid)
        if trial is None:left=mid
        else:right=mid;selected=trial
    actual=regret(lo,hi,selected,k)
    assert actual<=right+1e-6
    return selected,{'certified_lower':left,'certified_upper':max(right,actual),'actual_regret':actual,'absolute_gap':max(right,actual)-left}

def tests():
    rng=np.random.default_rng(9026);rows=[]
    for n,k in [(6,2),(7,3),(9,4)]:
        lo=rng.uniform(.01,.6,n);hi=lo+rng.uniform(0,.4,n)
        ix,report=optimize_interval(lo,hi,k)
        exact=min(regret(lo,hi,np.array(j),k) for j in itertools.combinations(range(n),k))
        assert abs(exact-report['actual_regret'])<3e-6
        # Independent endpoint adversary is checked against every interval vertex.
        vertex_max=max(1-np.array(v)[ix].sum()/np.sort(v)[-k:].sum() for v in itertools.product(*zip(lo,hi)))
        assert abs(vertex_max-regret(lo,hi,ix,k))<1e-10
        rows.append({'n':n,'k':k,'oracle_error':abs(exact-report['actual_regret']),'vertex_error':abs(vertex_max-regret(lo,hi,ix,k))})
    return {'status':'PASS','cases':rows}

if __name__=='__main__':
    root=Path(__file__).resolve().parent;obj=json.loads((root/'decision_regret_results.json').read_text());a=np.array(obj['scores']);lo=a.min(axis=0);hi=a.max(axis=0)
    output={'tests':tests(),'interpretation':'Independent city-specific full score ranges; conservative box containing the finite shared settings. Not a probability interval or observed benefit.','capacities':{}}
    for k in [6,9,12,18]:
        ix,certificate=optimize_interval(lo,hi,k)
        base={name:regret(lo,hi,np.array([obj['codes'].index(c) for c in data['selected_codes']]),k) for name,data in obj['capacities'][str(k)]['strategies'].items()}
        output['capacities'][str(k)]={'selected_codes':[obj['codes'][i] for i in ix],'certificate':certificate,'existing_strategy_box_regret':base}
    (root/'interval_regret_results.json').write_text(json.dumps(output,indent=2));print(json.dumps(output),flush=True)
