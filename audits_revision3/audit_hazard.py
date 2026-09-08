from pathlib import Path
import json,sys,hashlib,heapq
import numpy as np
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
import hazard_population as h
p=h.p;C=h.C
files=sorted((R/'hazard_results').glob('*.json'));assert len(files)==36
replay=[];source_checks=[];seen=set();hash_count=0
for fp in files:
    x=json.loads(fp.read_text());assert x['status']=='COMPLETE' and len(x['rows'])==384
    for row in x['rows']:assert -1e-12<=row['U']<=row['D']+1e-12<=1+2e-12
    g=dict(np.load(R/'hazard_inputs'/fp.stem/'strategic.npz'))
    for rp in ['RP10','RP100','RP500']:
        original=np.load(C/fp.stem/'exact_cell'/f'{rp}.npz')['values']
        assert np.array_equal(g[rp],original);source_checks.append((fp.stem,rp))
    for q in x['sources'].values():
        if q['path'] in seen:continue
        path=Path(q['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==q['sha256'];seen.add(q['path']);hash_count+=1
    replay.append(x['prior_replay_max_error'])

# Independent heap-based shortest paths and scalar metric sums; no call to production solve/metrics/weights.
code='ES059L1';x=json.loads((R/'hazard_results'/f'{code}.json').read_text());pop=dict(np.load(C/'population_support'/f'{code}.npz'));mass=pop['endpoint_mass']
def heap_routes(a,cost,ix):
    adj=[[] for _ in a['nodes']]
    for u,v,k in zip(a['au'],a['av'],a['phys']):
        if np.isfinite(cost[k]):adj[int(u)].append((int(v),float(cost[k])))
    output=[]
    for start in ix:
        dist=np.full(len(adj),np.inf);dist[start]=0.;queue=[(0.,int(start))]
        while queue:
            d,u=heapq.heappop(queue)
            if d>dist[u]:continue
            for v,c in adj[u]:
                candidate=d+c
                if candidate<dist[v]:dist[v]=candidate;heapq.heappush(queue,(candidate,v))
        output.append(dist[ix])
    return np.array(output)
baseline={};route_error=[];metric_error=[]
for scope in ['strategic','expanded']:
    a=dict(np.load(p.DATA/code/f'{scope}_static.npz'));ix=pop[scope+'_nodes'];baseline[scope]=heap_routes(a,a['base'],ix)
    ref=np.load(x['sources']['dry|'+scope]['path']);assert np.array_equal(np.isfinite(ref),np.isfinite(baseline[scope]));route_error.append(float(np.max(abs(ref[np.isfinite(ref)]-baseline[scope][np.isfinite(ref)]))))
for scope in ['strategic','expanded']:
    a=dict(np.load(p.DATA/code/f'{scope}_static.npz'));ix=pop[scope+'_nodes'];g=dict(np.load(R/'hazard_inputs'/code/f'{scope}.npz'))
    for rp in ['RP10','RP100','RP500']:
        cost=[]
        for base,(lo,hi) in zip(a['base'],g['spans']):
            total=0.
            for depth,fraction in zip(g[rp][lo:hi],g['fractions'][lo:hi]):
                speed=1 if depth<=.05 else .75 if depth<=.10 else .5 if depth<=.20 else .25 if depth<=.30 else 0
                total+=fraction/speed if speed else float('inf')
            cost.append(base*total)
        wet=heap_routes(a,np.array(cost),ix);ref=np.load(x['sources']['|'.join([scope,rp,'exposed','retained'])]['path'])
        assert np.array_equal(np.isfinite(wet),np.isfinite(ref));route_error.append(float(np.max(abs(wet[np.isfinite(wet)]-ref[np.isfinite(ref)]))))
        for model in ['unit','origin','destination','population']:
            oo=mass if model in ['origin','population'] else np.ones(len(mass));dd=mass if model in ['destination','population'] else np.ones(len(mass))
            for theta in [5,15,30,None]:
                origins=[i for i in range(len(mass)) if any(i!=j and np.isfinite(baseline['strategic'][i,j]) for j in range(len(mass)))];D=U=delay=0.
                for i in origins:
                    dest=[j for j in range(len(mass)) if i!=j and np.isfinite(baseline['strategic'][i,j])]
                    prop=[dd[j]*(1 if theta is None else np.exp(-baseline['strategic'][i,j]/theta)) for j in dest];den=sum(prop)
                    for j,v in zip(dest,prop):
                        w=oo[i]/oo[origins].sum()*v/den
                        if not np.isfinite(wet[i,j]):D+=w;U+=w
                        else:
                            delta=max(0.,wet[i,j]-baseline[scope][i,j]);D+=w*min(1.,delta/baseline[scope][i,j]);delay+=w*delta
                row=next(z for z in x['rows'] if z['period']==rp and z['scope']==scope and z['grade']=='exposed' and z['mask_policy']=='retained' and z['model']==model and z['theta']==theta)
                metric_error.extend([abs(D-row['D']),abs(U-row['U']),abs(delay-row['unconditional_finite_delay_minutes'])])
assert max(route_error)<1e-8 and max(metric_error)<1e-10
out={'status':'PASS','complete_cities':36,'scenario_rows':13824,'independent_source_array_comparisons':len(source_checks),'unique_matrix_hash_checks':hash_count,'RP100_replay_max_error':max(replay),'independent_heap_matrix_checks':len(route_error),'independent_heap_max_error_minutes':max(route_error),'independent_scalar_metric_comparisons':len(metric_error),'independent_scalar_max_error':max(metric_error),'scalar_scope':'All occupied endpoints in Zamora, both scopes, three return periods, four weighting models, four impedances, exposed bridges and retained depths'}
(R/'hazard_audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
