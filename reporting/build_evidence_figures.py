"""Paired physical contrasts and external observations; no model-generated images."""
from pathlib import Path
import json,hashlib,os
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'final_article/figures';OUT.mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'figure_cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':2.4,'grid.linewidth':2.4,'lines.linewidth':2.4,'pdf.fonttype':42})
blue='#2468A0';orange='#C27A2D';gray='#A6AFB8';dark='#232D38'
plt.rcParams.update({'xtick.major.width':2.4,'ytick.major.width':2.4,'lines.markeredgewidth':2.4,'patch.linewidth':2.4})
def save(fig,name):
    for suffix,dpi in [('.pdf',None),('.png',900),('_preview.png',160)]:fig.savefig(OUT/(name+suffix),dpi=dpi,bbox_inches='tight')
    with Image.open(OUT/(name+'.png')) as im:im.convert('RGB').save(OUT/(name+'.tiff'),compression='tiff_lzw',dpi=(900,900))
    plt.close(fig)
screen=json.loads((ROOT/'screening_analysis.json').read_text())['dense_convergence_results']['counts']['384']
weighted=json.loads((ROOT/'design_weighted_effects.json').read_text())['results']['dense_convergence_results']['384']
factors=['road_scope','bridge','spurious_bound'];names=['Road coverage','Bridge assumption','Flagged depth bound']
fig,axes=plt.subplots(1,2,figsize=(7.4,3.5),layout='constrained');rng=np.random.default_rng(831)
for i,key in enumerate(factors):
    a=np.array(list(screen['paired_effects'][key]['city_mean_abs_change'].values()))
    axes[0].scatter(a,i+rng.uniform(-.16,.16,len(a)),s=13,color=blue,alpha=.62,linewidths=0)
    v=weighted[key];lo,hi=v['approximate_95_interval'];m=v['mean']
    axes[1].errorbar(m,i,xerr=[[m-lo],[hi-m]],fmt='o',color=blue,capsize=3,markersize=5,elinewidth=2.4,capthick=2.4)
axes[0].set(yticks=range(3),yticklabels=names,xlabel='Mean absolute paired change by city',ylim=(2.6,-.6))
axes[1].set(yticks=range(3),yticklabels=[],xlabel='Frame mean absolute paired change',ylim=(2.6,-.6))
axes[1].axvline(0,color=gray,lw=2.4)
for ax,panel in zip(axes,'AB'):ax.grid(axis='x',alpha=.18);ax.text(-.05,1.03,panel,transform=ax.transAxes,fontweight='bold')
save(fig,'physical_contrasts')
external=json.loads((ROOT/'external_correspondence_analysis.json').read_text());agg=external['aggregates']
events=['EMSR517','EMSR664','EMSR773'];eventnames=['Germany','Italy','Spain'];lookup={(r['event'],r['period']):r for r in agg if r['category']=='damage' and r['excluded_product'] is None}
fig,axes=plt.subplots(1,2,figsize=(7.4,3.6),layout='constrained')
for k,(rp,color) in enumerate(zip(['RP10','RP100','RP500'],[gray,blue,orange])):
    axes[0].barh(np.arange(3)+(k-1)*.23,[lookup[e,rp]['wet_fraction'] for e in events],height=.20,label=rp.replace('RP',''),color=color)
for k,(key,label,color) in enumerate([('wet_fraction','Retained',blue),('wet_outside_spurious_fraction','Outside flagged depth',orange),('wet_outside_both_fraction','Outside both masks',gray)]):
    axes[1].barh(np.arange(3)+(k-1)*.23,[lookup[e,'RP100'][key] for e in events],height=.20,label=label,color=color)
for ax,panel in zip(axes,'AB'):
    ax.set(yticks=range(3),yticklabels=eventnames,xlim=(0,.8),ylim=(2.6,-.6),xlabel='Fraction of damaged record length')
    ax.grid(axis='x',alpha=.16);ax.text(-.05,1.03,panel,transform=ax.transAxes,fontweight='bold')
axes[0].legend(title='Return period (years)',frameon=False,fontsize=10,title_fontsize=10,loc='upper center',bbox_to_anchor=(.5,-.20),ncol=3)
axes[1].legend(frameon=False,fontsize=10,loc='upper center',bbox_to_anchor=(.5,-.20),ncol=1)
save(fig,'event_correspondence')
captions={'physical_contrasts':'Physical contrasts. (A) Each point is the average absolute paired disruption change for one city across the four settings of the other two factors, at 384 anchors. (B) Stratified design weighted means for the 721-area eligible frame with approximate 95% sampling intervals. Intervals do not include hazard or demand model uncertainty; three areas were sampled per stratum. The lower interval for the flagged depth contrast is allowed to extend below zero as an unconstrained sampling approximation.',
'event_correspondence':'Event correspondence. Positive modeled depth intersecting damaged or destroyed CEMS road record length. (A) Three return period layers. (B) The 100-year layer with all intersections retained, only intersections outside the spurious depth mask, and only intersections outside both the spurious depth and permanent water masks. Germany, Italy and Spain contribute 169.09, 11.10 and 197.48 km of product record length, respectively. These are spatial correspondences with physical damage, not traffic closure accuracy; overlapping records across products are not deduplicated.'}
(OUT/'evidence_captions.json').write_text(json.dumps(captions,indent=2))
(OUT/'evidence_provenance.json').write_text(json.dumps({'inputs':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['screening_analysis.json','design_weighted_effects.json','external_correspondence_analysis.json']},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'formats':'Vector PDF, 900 dpi PNG and RGB TIFF'},indent=2))
print(str(OUT),flush=True)
