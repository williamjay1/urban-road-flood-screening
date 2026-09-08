from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
files=sorted((R/'depth_order_reference').glob('*.json'));assert len(files)==36
z=np.load(R/'hazard_analysis_arrays.npz');codes=z['codes'].tolist();settings=[tuple(json.loads(s)) for s in z['settings']];population=z['population'].copy();unit=z['unit'].copy();changes=[]
for file in files:
    j=codes.index(file.stem)
    for row in json.loads(file.read_text())['cost_changed_scenarios']:
        i=settings.index(tuple(row[k] for k in ['period','theta','scope','grade','mask_policy']))
        (population if row['model']=='population' else unit)[i,j]=row['cumulative_D']
        if row['delta_D']>1e-10 or row['delta_U']>1e-10:changes.append({'code':file.stem,**row})
a=json.loads((R/'hazard_analysis.json').read_text());summary={}
for rp in ['RP10','RP100','RP500']:
    ii=np.array([s[0]==rp for s in settings]);mat=population[ii];optimum=np.sort(mat,axis=1)[:,-9:].sum(1)
    reg={}
    for name,selected in a['lists'].items():
        jj=[codes.index(c) for c in selected];reg[name]=float(np.max(1-mat[:,jj].sum(1)/optimum))
    summary[rp]={'median_abs_population_unit':float(np.median(abs(population[ii]-unit[ii]))),'original_list_transfer_regret':reg}
mechanism=[json.loads(f.read_text()) for f in sorted((R/'mechanism_results').glob('*.json'))];assert len(mechanism)==36
ms={}
for scope in ['strategic','expanded']:
    for rp in ['RP10','RP100','RP500']:
        rows=[next(q for q in x['rows'] if q['period']==rp and q['scope']==scope) for x in mechanism]
        remote=np.array([q['remote_disconnection_U'] for q in rows]);local=np.array([q['local_endpoint_isolation_U'] for q in rows]);positive=remote+local>1e-10
        ms[scope+'|'+rp]={'median_remote_U':float(np.median(remote)),'median_local_U':float(np.median(local)),'remote_larger_than_local_cities':int(np.sum(remote>local+1e-10)),'positive_U_cities':int(positive.sum()),'median_remote_fraction_among_positive':float(np.median(remote[positive]/(remote+local)[positive])),'max_remote_U':float(max(remote))}
out={'status':'COMPLETE','cumulative_changed_cities':sorted(set(x['code'] for x in changes)),'cumulative_changed_population_cities':sorted(set(x['code'] for x in changes if x['model']=='population')),'max_cumulative_population_D_change':max([x['delta_D'] for x in changes if x['model']=='population'] or [0]),'cumulative_by_period':summary,'cumulative_changes':changes,'mechanism_summary':ms}
(R/'controls_analysis.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='cumulative_changes'},indent=2))
