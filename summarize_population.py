from pathlib import Path
import sys,json,itertools
import numpy as np
from scipy.stats import spearmanr,rankdata
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from decision_regret import top,optimize,evaluate
from interval_regret import optimize_interval,regret
OLD=ROOT

def describe(a):return {'median_abs':float(np.median(abs(a))),'max_abs':float(abs(a).max()),'min':float(a.min()),'max':float(a.max())}

def main():
    obj=json.loads((ROOT/'decision_regret_results.json').read_text());codes=obj['codes'];settings=[tuple(s) for s in obj['settings']];old=np.array(obj['scores'])
    results={c:json.loads((ROOT/'population_reference'/f'{c}.json').read_text()) for c in codes}
    assert all(r['status']=='COMPLETE' for r in results.values())
    def get(model,theta_override=False):
        return np.array([[next(r['D'] for r in results[c]['scenarios'] if (r['scope'],r['grade'],r['mask_policy'],r['theta'],r['model'])==(*s[:3],15 if theta_override else s[3],model)) for c in codes] for s in settings])
    pop=get('population');unit=get('unit');res=json.loads((ROOT/'population_anchor_resolution.json').read_text())
    idx={(r['code'],r['anchors'],r['model'],r['scope'],r['grade'],r['mask_policy'],r['theta']):r for r in res['rows']}
    approx={n:np.array([[idx[(c,n,'population',*s)]['D'] for c in codes] for s in settings]) for n in [96,192,384]}
    geo_unit=np.array([[idx[(c,384,'unit',*s)]['D'] for c in codes] for s in settings])
    report={'status':'COMPLETE_36','codes':codes,'settings':settings,'population_scores':pop.tolist(),'unit_scores':unit.tolist(),
        'population_vs_unit':describe(pop-unit),'population_vs_original_geometry':describe(pop-old),
        'population_vs_unit_spearman':[float(spearmanr(a,b).statistic) for a,b in zip(pop,unit)],
        'population_vs_original_spearman':[float(spearmanr(a,b).statistic) for a,b in zip(pop,old)],
        'population_geometric_approximation':{str(n):{'error':describe(a-pop),'spearman':[float(spearmanr(x,y).statistic) for x,y in zip(a,pop)]} for n,a in approx.items()},
        'normalization_change_original384_vs_unit384':describe(geo_unit-old),
        'support_checks':{},'capacities':{},'allocation_summary':{},'support_summary':{}}
    for model in ['snap1km','snap2km','interior']:
        a=get(model,True);target=np.array([pop[i] for i,s in enumerate(settings) if s[3]==15]);reduced=np.array([a[i] for i,s in enumerate(settings) if s[3]==15])
        report['support_checks'][model]={'contrasts':describe(reduced-target),'rank_correlations':[float(spearmanr(x,y).statistic) for x,y in zip(reduced,target)],'retained_population':{c:results[c]['support'][f'{model}|15']['fraction_of_full_population'] for c in codes}}
    allocation=json.loads((ROOT/'population_support_audit.json').read_text())['cities']
    report['allocation_summary']={'population_total':sum(r['population_2018_areal_estimate'] for r in allocation),'positive_cells':sum(r['positive_intersecting_cells'] for r in allocation),'endpoints':sum(r['distinct_endpoints'] for r in allocation),'endpoint_min':min(r['distinct_endpoints'] for r in allocation),'endpoint_max':max(r['distinct_endpoints'] for r in allocation),'max_population_snap_over_1km':max(r['population_snap_over_1km_share'] for r in allocation),'max_boundary_population_share':max(r['boundary_cell_population_share'] for r in allocation)}
    report['support_summary']={'minimum_retained_dry_origin_population':min(r['support']['population|15']['dry_origin_population_retained'] for r in results.values()),'maximum_coincident_pair_mass':max(r['support']['population|15']['coincident_endpoint_population_pair_share'] for r in results.values())}
    base=settings.index(('strategic','exposed','retained',15));lo=pop.min(axis=0);hi=pop.max(axis=0)
    for k in [6,9,12,18]:
        mm,cert=optimize(pop,k);box,boxcert=optimize_interval(lo,hi,k)
        strategies={'original_baseline':top(old[base],k),'original_mean':top(old.mean(axis=0),k),'unit_baseline':top(unit[base],k),'unit_mean':top(unit.mean(axis=0),k),'population_baseline':top(pop[base],k),'population_mean':top(pop.mean(axis=0),k),'population_mean_rank':top(-np.mean([rankdata(-x) for x in pop],axis=0),k),'population_minimax':mm,'population_interval_minimax':box}
        best=np.array([[1+np.sum(row>x+1e-10) for x in row] for row in pop]);worst=np.array([[np.sum(row>=x-1e-10) for x in row] for row in pop])
        entry={'minimax_certificate':cert,'interval_certificate':boxcert,'persistent':[c for i,c in enumerate(codes) if worst[:,i].max()<=k],'possible':[c for i,c in enumerate(codes) if best[:,i].min()<=k],
            'strategies':{name:{'selected_codes':[codes[i] for i in ix],**evaluate(pop,ix,k),'independent_interval_regret':regret(lo,hi,ix,k)} for name,ix in strategies.items()},'excluded_family_checks':[]}
        primary_mask=np.array([s[3]==15 for s in settings]);physical={}
        for target_name,target_matrix in [('original',old[primary_mask]),('population',pop[primary_mask])]:
            fit,fitcert=optimize(target_matrix,k);low=target_matrix.min(axis=0);high=target_matrix.max(axis=0);bfit,bcert=optimize_interval(low,high,k)
            choices={'baseline':top((old if target_name=='original' else pop)[base],k),'mean':top(target_matrix.mean(axis=0),k),'minimax':fit,'interval_minimax':bfit}
            physical[target_name]={'shared_certificate':fitcert,'interval_certificate':bcert,'strategies':{name:{'selected_codes':[codes[i] for i in ix],**evaluate(target_matrix,ix,k),'independent_interval_regret':regret(low,high,ix,k)} for name,ix in choices.items()}}
        entry['physical_only']=physical
        for factor,groups in [('demand',list(dict.fromkeys(s[3] for s in settings))),('physical',list(dict.fromkeys(s[:3] for s in settings)))]:
            for group in groups:
                mask=np.array([(s[3] if factor=='demand' else s[:3])==group for s in settings]);train=pop[~mask];test=pop[mask];fit,detail=optimize(train,k)
                selections={'original_baseline':strategies['original_baseline'],'population_mean':top(train.mean(axis=0),k),'population_minimax':fit}
                entry['excluded_family_checks'].append({'factor':factor,'excluded':group,'strategies':{name:evaluate(test,ix,k) for name,ix in selections.items()},'solver':detail})
        report['capacities'][str(k)]=entry
    (ROOT/'population_analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['allocation_summary','support_summary','population_vs_unit','population_vs_original_geometry']}))
    print(json.dumps({k:{n:round(r['worst_normalized_regret'],5) for n,r in v['strategies'].items()} for k,v in report['capacities'].items()}))

if __name__=='__main__':main()
