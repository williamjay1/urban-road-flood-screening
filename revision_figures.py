from pathlib import Path
import os,json
R=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(R/'mplcache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
a=json.loads((R/'population_analysis.json').read_text());old=json.loads((R/'decision_regret_results.json').read_text())
O=R
names={r['code']:r['name'].removeprefix('FUA of ').strip() for r in json.loads((O/'sampling_frame_audit.json').read_text(encoding='utf-8'))['selected']}
plt.rcParams.update({'font.size':10,'axes.labelsize':10,'axes.titlesize':11,'lines.linewidth':2.4,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
out=R/'article'/'figures';out.mkdir(exist_ok=True)
def save(fig,name):
 fig.savefig(out/(name+'.pdf'))
 fig.savefig(out/(name+'.png'),dpi=900)
 with Image.open(out/(name+'.png')) as im:im.convert('RGB').save(out/(name+'.tiff'),compression='tiff_lzw',dpi=(900,900))
 (out/(name+'.png')).unlink();plt.close(fig)
p=np.array(a['population_scores']);g=np.array(old['scores']);order=np.argsort(-p.mean(0));y=np.arange(len(order))
fig,axes=plt.subplots(1,2,figsize=(7.2,9),sharey=True,gridspec_kw={'width_ratios':[1,1]})
fig.subplots_adjust(left=.24,right=.98,bottom=.12,top=.94,wspace=.18)
ax=axes[0]
for j,i in enumerate(order):ax.plot([g[:,i].mean(),p[:,i].mean()],[j,j],color='.72',lw=2.4)
ax.scatter(g.mean(0)[order],y,s=24,color='#A05D2C',label='Geometric reference',zorder=3)
ax.scatter(p.mean(0)[order],y,s=24,color='#126A82',label='Resident model',zorder=3)
ax.set_yticks(y,[names[a['codes'][i]] for i in order]);ax.invert_yaxis();ax.set_xlim(0,1);ax.set_xlabel('Mean disruption');ax.set_title('A  Evaluation target',loc='left')
ax=axes[1]
ax.hlines(y,p.min(0)[order],p.max(0)[order],color='#126A82',lw=2.4)
ax.scatter(p.mean(0)[order],y,s=18,color='#126A82');ax.set_xlim(0,1);ax.set_xlabel('Disruption range');ax.set_title('B  Resident scenarios',loc='left')
for ax in axes:ax.grid(axis='x',alpha=.18);ax.tick_params(axis='y',length=0)
fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.57,.015))
save(fig,'population_screening')
fig,axes=plt.subplots(1,2,figsize=(7.2,4.1));fig.subplots_adjust(left=.10,right=.98,top=.89,bottom=.30,wspace=.35)
styles=[('original_baseline','Geometric baseline','#A05D2C','o'),('population_baseline','Resident baseline','#888888','s'),('population_mean','Resident mean','#126A82','^'),('population_minimax','Shared minimax','#743B85','D')]
ks=[6,9,12,18]
for n,label,color,marker in styles:
 for ax,key in zip(axes,['worst_normalized_regret','independent_interval_regret']):
  ax.plot(ks,[100*a['capacities'][str(k)]['strategies'][n][key] for k in ks],color=color,marker=marker,ms=5,label=label)
for ax,title in zip(axes,['A  Shared settings','B  Independent local bounds']):
 ax.set_title(title,loc='left');ax.set_xticks(ks);ax.set_xlabel('Areas selected');ax.set_ylabel('Worst regret (%)');ax.grid(alpha=.18);ax.set_ylim(bottom=0)
fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.5,.01))
save(fig,'decision_loss')
print('Two new vector and 900 dpi RGB TIFF figures complete')
