"""Publication figures from complete, storage-replayed 36-city results."""
from pathlib import Path
import json,hashlib,os
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'figure_cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'final_article/figures';OUT.mkdir(parents=True,exist_ok=True)
audit=json.loads((ROOT/'storage_replay_audit.json').read_text());assert audit['status']=='PASS' and len(audit['cities'])==36
screen=json.loads((ROOT/'screening_analysis.json').read_text());demand=json.loads((ROOT/'dense_demand_analysis.json').read_text())
labels={r['code']:r['name'].removeprefix('FUA of ').strip() for r in json.loads((ROOT/'sampling_frame_audit.json').read_text(encoding='utf-8'))['selected']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':2.4,'grid.linewidth':2.4,'lines.linewidth':2.4,'pdf.fonttype':42,'savefig.facecolor':'white'})
blue='#2468A0';gray='#ABB2BA';dark='#232D38'
plt.rcParams.update({'xtick.major.width':2.4,'ytick.major.width':2.4,'lines.markeredgewidth':2.4,'patch.linewidth':2.4})
def save(fig,name):
    fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight')
    fig.savefig(OUT/f'{name}.png',dpi=900,bbox_inches='tight')
    with Image.open(OUT/f'{name}.png') as im:im.convert('RGB').save(OUT/f'{name}.tiff',compression='tiff_lzw',dpi=(900,900))
    fig.savefig(OUT/f'{name}_preview.png',dpi=160,bbox_inches='tight');plt.close(fig)
old=screen['dense_od_results'];new=screen['dense_convergence_results']
arrays=[np.array(old['counts']['48']['scores']),*[np.array(new['counts'][str(n)]['scores']) for n in [96,192,384]]]
changes=[abs(b-a).ravel() for a,b in zip(arrays[:-1],arrays[1:])]
corr=[old['density_changes'][0]['rank_correlations_by_setting'],*[r['rank_correlations_by_setting'] for r in new['density_changes']]]
fig,axes=plt.subplots(1,2,figsize=(7.4,3.3),layout='constrained');rng=np.random.default_rng(831)
axes[0].boxplot(changes,positions=[1,2,3],widths=.36,showfliers=False,patch_artist=True,boxprops={'facecolor':'#DCE9F4','edgecolor':blue,'linewidth':2.4},medianprops={'color':dark,'linewidth':2.4},whiskerprops={'linewidth':2.4},capprops={'linewidth':2.4})
for i,values in enumerate(changes,1):axes[0].scatter(i+rng.uniform(-.15,.15,len(values)),values,s=3,color=blue,alpha=.22,linewidths=0)
axes[0].set(ylabel='Absolute change in disruption index',xticks=[1,2,3],xticklabels=['48 → 96','96 → 192','192 → 384'],xlabel='Number of anchors',ylim=(-.003,.10))
c=np.array(corr)
for row in c.T:axes[1].plot([1,2,3],row,'o-',color=blue,alpha=.4,linewidth=2.4,markersize=3)
axes[1].plot([1,2,3],np.median(c,axis=1),'o-',color=dark,linewidth=2.5,markersize=4)
axes[1].set(ylabel='Spearman rank correlation',xticks=[1,2,3],xticklabels=['48 → 96','96 → 192','192 → 384'],xlabel='Number of anchors',ylim=(.96,1.003))
for ax,panel in zip(axes,'AB'):ax.text(-.13,1.03,panel,transform=ax.transAxes,fontweight='bold');ax.grid(axis='y',alpha=.18)
axes[1].legend([Line2D([],[],color=blue,alpha=.5),Line2D([],[],color=dark)],['Each setting','Median'],loc='lower right',frameon=False,fontsize=10)
save(fig,'anchor_density')
primary=new['counts']['384'];codes=primary['codes'];lookup={c:i for i,c in enumerate(codes)}
order=sorted(codes,key=lambda c:np.mean(np.array(primary['scores'])[:,lookup[c]]),reverse=True)
fig,axes=plt.subplots(1,2,figsize=(7.4,9.0),sharey=True,gridspec_kw={'width_ratios':[1.35,1]},layout='constrained')
for y,code in enumerate(order):
    i=lookup[code];extra=demand['city_ranges'][code]
    axes[0].plot([extra['D_min'],extra['D_max']],[y,y],color=gray,lw=4,solid_capstyle='round')
    axes[0].plot([primary['score_interval_min'][i],primary['score_interval_max'][i]],[y,y],color=blue,lw=2.4,solid_capstyle='round')
    axes[1].plot([extra['rank_best'],extra['rank_worst']],[y,y],color=gray,lw=4,solid_capstyle='round')
    axes[1].plot([primary['shared_rank_best'][i],primary['shared_rank_worst'][i]],[y,y],color=blue,lw=2.4,solid_capstyle='round')
    if primary['score_interval_min'][i]==primary['score_interval_max'][i]:axes[0].scatter(primary['score_interval_min'][i],y,s=9,color=blue,zorder=4)
    if primary['shared_rank_best'][i]==primary['shared_rank_worst'][i]:axes[1].scatter(primary['shared_rank_best'][i],y,s=9,color=blue,zorder=4)
axes[0].set(yticks=range(36),yticklabels=[labels[c] for c in order],xlabel='Disruption index',xlim=(-.02,1.02),ylim=(35.8,-.8))
axes[1].set(xlabel='Rank',xlim=(0,37),xticks=[1,9,18,27,36])
for ax,panel in zip(axes,'AB'):
    ax.text(-.08,1.02,panel,transform=ax.transAxes,fontweight='bold');ax.grid(axis='x',alpha=.18);ax.tick_params(axis='y',length=0)
fig.legend([Line2D([],[],color=blue,lw=2.4),Line2D([],[],color=gray,lw=4)],['Physical settings (8)','Physical + demand (32)'],loc='outside lower center',ncol=2,frameon=False,fontsize=10)
save(fig,'city_screening_ranges')
(OUT/'captions.txt').write_text('Figure 1. Anchor density. (A) Absolute score changes across 36 cities and eight physical settings. Points are paired deterministic scenario differences, not independent uncertainty draws. (B) Rank correlations across cities for each setting; the dark line is their median. All anchors are nested and use the same spatial selection rule.\n\nFigure 2. Screening ranges. (A) Minimum and maximum disruption scores at 384 anchors. (B) Best and worst ranks under shared settings. Blue ranges use eight road-scope, bridge and hazard-mask settings at the primary 15-minute impedance weight; gray ranges additionally include 5-minute, 30-minute and uniform weights, yielding 32 settings. Cities are ordered by their mean score across the eight primary settings. Ranges are finite scenario envelopes, not confidence intervals. Passenger-car access checks are reported separately.\n',encoding='utf-8')
inputs=['storage_replay_audit.json','screening_analysis.json','dense_demand_analysis.json','sampling_frame_audit.json']
(OUT/'provenance.json').write_text(json.dumps({'inputs':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in inputs},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'format':'vector PDF, 900 dpi PNG and RGB TIFF; separate low-resolution previews'},indent=2))
print(str(OUT),flush=True)
