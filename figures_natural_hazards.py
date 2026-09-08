from pathlib import Path
import os,json
R=Path(__file__).resolve().parent;P=R;O=R/'article'/'figures';O.mkdir(exist_ok=True,parents=True)
assert json.loads((R/'hazard_audit.json').read_text())['status']=='PASS'
os.environ['MPLCONFIGDIR']=str(R/'mplcache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
from shapely.geometry import shape,box
from shapely.ops import transform
from pyproj import Transformer

# Rebuild the supplied earlier figure definitions from local summary inputs.
old=R
s=(R/'revision_figures.py').read_text().replace("'A  ","'a  ").replace("'B  ","'b  ")
exec(compile(s,str(R/'revision_figures.py'),'exec'),{'__file__':str(R/'revision_figures.py')})
s=(R/'build_evidence_figures.py').read_text().replace("OUT=ROOT/'final_article/figures'","OUT=ROOT/'article/figures'").replace("zip(axes,'AB')","zip(axes,'ab')").replace('(A)','(a)').replace('(B)','(b)')
exec(compile(s,str(R/'build_evidence_figures.py'),'exec'),{'__file__':str(R/'build_evidence_figures.py')})

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'axes.titlesize':10,'axes.linewidth':.7,'grid.linewidth':.6,'lines.linewidth':1.6,'lines.markeredgewidth':1.0,'lines.markeredgewidth':1.0,'xtick.major.width':.7,'ytick.major.width':.7,'patch.linewidth':.7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
def save(fig,name):
    fig.savefig(O/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(O/(name+'_preview.png'),dpi=150,bbox_inches='tight')
    temp=O/(name+'_raster.png');fig.savefig(temp,dpi=1200,bbox_inches='tight')
    with Image.open(temp) as im:im.convert('RGB').save(O/(name+'.tiff'),compression='tiff_lzw',dpi=(1200,1200))
    temp.unlink();plt.close(fig)

frame=json.loads((old/'sampling_frame_audit.json').read_text(encoding='utf-8'))
countries=json.loads((R/'context_inputs/CNTR_RG_10M_2024_4326.geojson').read_text(encoding='utf-8'))
boundary=json.loads((R/'sources/boundaries.geojson').read_text(encoding='utf-8'))
bycode={f['properties']['URAU_CODE']:shape(f['geometry']) for f in boundary['features']}
project=Transformer.from_crs(4326,3035,always_xy=True).transform
clip=box(-13,34,33,64)
fig,ax=plt.subplots(figsize=(6.5,5.1));fig.subplots_adjust(bottom=.16,top=.98,left=.02,right=.98)
for f in countries['features']:
    g=shape(f['geometry']).intersection(clip)
    if g.is_empty:continue
    g=transform(project,g)
    for part in getattr(g,'geoms',[g]):
        if part.geom_type=='Polygon':ax.add_patch(Polygon(np.array(part.exterior.coords)/1000,fc='#F0F0ED',ec='#B9C0C4',lw=.45))
styles={'north':('#176A85','o','North'),'west':('#C57531','s','West'),'central_east':('#786495','^','Central/east'),'south':('#3D8660','D','South')}
for region,(color,marker,label) in styles.items():
    points=[]
    for city in frame['selected']:
        if city['macroregion']!=region:continue
        g=bycode[city['code']];assert clip.intersects(g),city['code'];pt=transform(project,g).centroid;points.append([pt.x/1000,pt.y/1000])
    points=np.array(points);ax.scatter(points[:,0],points[:,1],s=45,color=color,marker=marker,edgecolors='white',linewidths=.6,label=f'{label} ({len(points)})',zorder=3)
ax.autoscale();ax.set_aspect('equal');ax.axis('off');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.02),ncol=4,frameon=False,columnspacing=1,handletextpad=.3)
save(fig,'study_areas')

a=json.loads((R/'hazard_analysis.json').read_text());z=np.load(R/'hazard_analysis_arrays.npz');settings=[json.loads(s) for s in z['settings']];codes=z['codes'].tolist()
colors=['#527F91','#C57531','#786495'];rps=['RP10','RP100','RP500'];fig,axes=plt.subplots(2,2,figsize=(6.8,6.0));fig.subplots_adjust(left=.12,right=.97,top=.93,bottom=.13,wspace=.38,hspace=.55)
ax=axes[0,0]
for i,(rp,color) in enumerate(zip(rps,colors)):
    ii=np.array([s[0]==rp for s in settings]);v=np.abs(z['population'][ii]-z['unit'][ii]).mean(0)
    ax.scatter(i+np.linspace(-.17,.17,len(v)),v,s=12,alpha=.55,color=color,lw=0)
    estimate=a['period_summary'][rp]['frame_abs_weighting_difference'];lo,hi=estimate['approximate_95_interval'];m=estimate['mean'];ax.errorbar(i,m,yerr=[[m-lo],[hi-m]],fmt='D',color='black',ms=4,capsize=3,lw=1.4,zorder=4)
ax.set(xticks=range(3),xticklabels=['10','100','500'],xlabel='Return period (years)',ylabel='Mean absolute weighting contrast');ax.set_title('a  Population and unit weights',loc='left')
ax=axes[0,1]
for rp,color in zip(rps,colors):
    ii=np.array([s[0]==rp for s in settings]);ax.scatter(z['origin_component'][ii].mean(0),z['destination_component'][ii].mean(0),s=13,alpha=.6,color=color,label=rp[2:])
ax.axhline(0,color='.7',lw=.6);ax.axvline(0,color='.7',lw=.6);ax.set(xlabel='Origin contribution',ylabel='Destination contribution');ax.set_title('b  Weighting decomposition',loc='left')
fig.legend(*ax.get_legend_handles_labels(),title='Return period (years)',frameon=False,fontsize=8,title_fontsize=8,loc='upper center',bbox_to_anchor=(.75,1.06),ncol=3)
ax=axes[1,0];rulelabels={'RP100_population_mean':'100-year resident mean','RP100_unit_mean':'100-year unit mean','all_period_population_mean':'Three-period resident mean'}
for (name,label),marker,color in zip(rulelabels.items(),['o','s','^'],['#176A85','#C57531','#786495']):
    ax.plot(range(3),[100*a['period_summary'][rp]['transfer_regret'][name] for rp in rps],marker=marker,ms=4,color=color,label=label)
ax.set(xticks=range(3),xticklabels=['10','100','500'],xlabel='Evaluation return period (years)',ylabel='Worst shortlist regret (%)');ax.set_title('c  Transfer between flood intensities',loc='left');ax.set_ylim(bottom=0)
fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,-.005),ncol=3,fontsize=8,frameon=False,columnspacing=.8,handletextpad=.4)
ax=axes[1,1]
mechanism=[json.loads(f.read_text()) for f in sorted((R/'mechanism_results').glob('*.json'))];assert len(mechanism)==36
for i,(rp,color) in enumerate(zip(rps,colors)):
    v=[next(q for q in x['rows'] if q['scope']=='strategic' and q['period']==rp) for x in mechanism]
    ax.scatter([q['local_endpoint_isolation_U'] for q in v],[q['remote_disconnection_U'] for q in v],s=13,color=color,alpha=.55)
ax.set(xlabel='Endpoint isolation',ylabel='Remote disconnection');ax.set_title('d  Disconnection components',loc='left');ax.set_xlim(left=0);ax.set_ylim(bottom=0)
for ax in axes.flat:ax.grid(alpha=.15)
save(fig,'hazard_population')
print(json.dumps({'figures':6,'new_tiff_dpi':1200,'directory':str(O)}))
