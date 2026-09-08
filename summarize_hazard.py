from pathlib import Path
import json,sys,itertools
import numpy as np
from scipy.stats import spearmanr,t
R=Path(__file__).resolve().parent;P=R;sys.path.insert(0,str(P))
import decision_regret as dr
files=sorted((R/'hazard_reference').glob('*.json'));assert len(files)==36,len(files)
codes=[f.stem for f in files];data=[json.loads(f.read_text()) for f in files]
frame=json.loads((R/'sampling_frame_audit.json').read_text())
meta={x['code']:x for x in frame['selected']}
def frame_estimate(array):
    mean=0.;variance=[]
    for key,s in frame['strata'].items():
        a=np.array([array[j] for j,c in enumerate(codes) if meta[c]['stratum']==key]);assert len(a)==3
        W=s['N']/721;mean+=W*a.mean();variance.append(W*W*(1-3/s['N'])*a.var(ddof=1)/3)
    v=sum(variance);df=v*v/sum(z*z/2 for z in variance) if v else 1;half=t.ppf(.975,df)*np.sqrt(v)
    return {'mean':float(mean),'approximate_95_interval':[float(mean-half),float(mean+half)],'df':float(df)}
def key(x):return tuple(x[k] for k in ['period','theta','scope','grade','mask_policy'])
settings=[key(x) for x in data[0]['rows'] if x['model']=='population']
values={m:np.array([[next(x['D'] for x in c['rows'] if x['model']==m and key(x)==s) for c in data] for s in settings]) for m in ['unit','origin','destination','population']}
orig=.5*((values['origin']-values['unit'])+(values['population']-values['destination']))
dest=.5*((values['destination']-values['unit'])+(values['population']-values['origin']))
diff=values['population']-values['unit'];assert np.max(abs(orig+dest-diff))<1e-12
interaction=values['population']-values['origin']-values['destination']+values['unit']
def rankselect(v,k=9):return np.argsort(-v,kind='stable')[:k]
def regrets(mat,sel):
    optimum=np.sort(mat,axis=1)[:,-len(sel):].sum(1)
    return np.divide(optimum-mat[:,sel].sum(1),optimum,out=np.zeros_like(optimum),where=optimum>0)
is100=np.array([s[0]=='RP100' for s in settings]);lists={'RP100_population_mean':rankselect(values['population'][is100].mean(0)),'RP100_unit_mean':rankselect(values['unit'][is100].mean(0)),'all_period_population_mean':rankselect(values['population'].mean(0))}
summary={};means={}
for rp in ['RP10','RP100','RP500']:
    ix=np.array([s[0]==rp for s in settings]);delta=diff[ix];pm=values['population'][ix];means[rp]=delta.mean(0)
    summary[rp]={'median_abs_population_unit':float(np.median(abs(delta))),'max_abs_population_unit':float(np.max(abs(delta))),'rank_population_unit_min':min(float(spearmanr(a,b).statistic) for a,b in zip(pm,values['unit'][ix])),'mean_origin_abs':float(np.mean(abs(orig[ix]))),'median_origin_abs':float(np.median(abs(orig[ix]))),'median_destination_abs':float(np.median(abs(dest[ix]))),'median_interaction_abs':float(np.median(abs(interaction[ix]))),'population_D_median':float(np.median(pm)),'transfer_regret':{name:float(regrets(pm,sel).max()) for name,sel in lists.items()}}
    summary[rp]['frame_abs_weighting_difference']=frame_estimate(abs(delta).mean(0))
    summary[rp]['origin_larger_abs_than_destination_city_count']=int(np.sum(abs(orig[ix]).mean(0)>abs(dest[ix]).mean(0)))
cityrows=[]
for j,code in enumerate(codes):
    cityrows.append({'code':code,'mean_difference':float(diff[:,j].mean()),'mean_origin':float(orig[:,j].mean()),'mean_destination':float(dest[:,j].mean()),'mean_interaction':float(interaction[:,j].mean()),'by_period':{rp:float(means[rp][j]) for rp in means}})
matched=[]
for s in settings:
    if s[0]!='RP100':continue
    idx=[settings.index((rp,*s[1:])) for rp in ['RP10','RP100','RP500']]
    arr=values['population'][idx];matched.extend(np.ptp(arr,axis=0).tolist())
nonmono=[]
for i,s in enumerate(settings):
    if s[0]!='RP100':continue
    x0=values['population'][settings.index(('RP10',*s[1:]))];x1=values['population'][i];x2=values['population'][settings.index(('RP500',*s[1:]))]
    for j in np.flatnonzero((x0>x1+1e-10)|(x1>x2+1e-10)):nonmono.append({'code':codes[j],'setting':s,'scores':[float(x0[j]),float(x1[j]),float(x2[j])]})
out={'status':'COMPLETE','cities':36,'rows':sum(len(x['rows']) for x in data),'settings_per_model':len(settings),'period_summary':summary,'city_decomposition':cityrows,'additivity_max_error':float(np.max(abs(orig+dest-diff))),'prior_replay_max_error':max(x['prior_replay_max_error'] for x in data),'lists':{k:[codes[i] for i in v] for k,v in lists.items()},'median_hazard_range':float(np.median(matched)),'max_hazard_range':float(max(matched)),'mean_difference_same_sign_all_period_cities':int(np.sum((means['RP10']*means['RP100']>0)&(means['RP100']*means['RP500']>0))),'nonmonotone_scores':nonmono,'max_raw_nonmonotone_cell_fraction':max(z['nonmonotone_fraction'] for c in data for z in c['quality'].values())}
(R/'hazard_analysis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
np.savez_compressed(R/'hazard_analysis_arrays.npz',codes=np.array(codes),settings=np.array([json.dumps(s) for s in settings]),origin_component=orig,destination_component=dest,interaction=interaction,**values)
print(json.dumps({k:v for k,v in out.items() if k not in ['city_decomposition','nonmonotone_scores']},indent=2))
