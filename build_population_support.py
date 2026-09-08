"""Conserve areally allocated GEOSTAT population within each fixed FUA."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,rasterio
from rasterio.windows import from_bounds,Window
from shapely.geometry import shape,box,mapping
from shapely.ops import transform
from shapely.prepared import prep
from pyproj import Transformer
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--codes',nargs='*');args=parser.parse_args()
OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
frame=json.loads((ROOT/'source_manifest.json').read_text());source=ROOT/'sources'/'boundaries.geojson';raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()==frame['boundary_source_sha256']
features={f['properties']['URAU_CODE']:f for f in json.loads(raw)['features']}
codes=args.codes or [x['code'] for x in json.loads((ROOT/'sampling_frame_audit.json').read_text(encoding='utf-8'))['selected']]
tf=Transformer.from_crs(4326,3035,always_xy=True).transform
pop=ROOT/'sources'/'JRC_1K_POP_2018.tif'
assert hashlib.sha256(pop.read_bytes()).hexdigest()=='4372a58f2e4a0b0bd784ef72761717e524bbf4007afe5691b1f16bfb3b187c31'
rows=[]
with rasterio.open(pop) as r:
    for code in codes:
        geom=transform(tf,shape(features[code]['geometry']));prepared=prep(geom)
        w=from_bounds(*geom.bounds,transform=r.transform)
        startrow=int(np.floor(w.row_off));startcol=int(np.floor(w.col_off))
        w=Window(startcol,startrow,int(np.ceil(w.col_off+w.width))-startcol,int(np.ceil(w.row_off+w.height))-startrow)
        a=r.read(1,window=w,masked=True);coords=[];mass=[];rawpop=[];fraction=[];grid=[];interior=[]
        for iy,ix in zip(*np.where(a.filled(0)>0)):
            x,y=r.xy(iy+startrow,ix+startcol);cell=box(x-500,y-500,x+500,y+500)
            if not prepared.intersects(cell):continue
            if prepared.covers(cell):f=1.;point=cell.centroid
            else:
                part=cell.intersection(geom);f=part.area/1e6
                if f<=1e-12:continue
                point=part.centroid
                if not part.covers(point):point=part.representative_point()
            coords.append((point.x,point.y));p=float(a[iy,ix]);mass.append(p*f);rawpop.append(p);fraction.append(f);grid.append((iy+startrow,ix+startcol));interior.append(f==1.)
        coords=np.array(coords);mass=np.array(mass)
        assert len(mass)>0 and np.all(mass>0)
        g=np.load(ROOT/'datasets'/code/'strategic_static.npz')
        distance,node=cKDTree(g['nodes']).query(coords)
        unique,inverse=np.unique(node,return_inverse=True);node_mass=np.bincount(inverse,weights=mass,minlength=len(unique))
        assert abs(node_mass.sum()-mass.sum())<1e-6
        # All endpoint identities are fixed before hazard evaluation.
        expanded=np.load(ROOT/'datasets'/code/'expanded_static.npz')
        lookup={tuple(x):i for i,x in enumerate(expanded['nodes'])}
        expanded_node=np.array([lookup[tuple(p)] for p in g['nodes'][unique]])
        np.savez_compressed(OUT/f'{code}.npz',cell_xy=coords,cell_mass=mass,cell_raw_population=np.array(rawpop),cell_area_fraction=np.array(fraction),grid_indices=np.array(grid),cell_to_endpoint=inverse,cell_snap_m=distance,strategic_nodes=unique,expanded_nodes=expanded_node,endpoint_xy=g['nodes'][unique],endpoint_mass=node_mass)
        def quantile(q):
            order=np.argsort(distance);return float(distance[order][np.searchsorted(np.cumsum(mass[order]),q*mass.sum())])
        rows.append({'code':code,'positive_intersecting_cells':len(mass),'distinct_endpoints':len(unique),'population_2018_areal_estimate':float(mass.sum()),'boundary_cell_population_share':float(mass[np.array(fraction)<1].sum()/mass.sum()),'within_endpoint_pair_mass_fraction':float(np.sum((node_mass/node_mass.sum())**2)),'snap_median_m':quantile(.5),'snap_p95_m':quantile(.95),'snap_max_m':float(distance.max()),'population_snap_over_1km_share':float(mass[distance>1000].sum()/mass.sum()),'population_snap_over_2km_share':float(mass[distance>2000].sum()/mass.sum()),'mass_balance_error':float(node_mass.sum()-mass.sum())})
        print(json.dumps(rows[-1]),flush=True)
(OUT/'population_support_audit.json').write_text(json.dumps({'status':'COMPLETE_REQUESTED','source_grid_sha256':hashlib.sha256(pop.read_bytes()).hexdigest(),'boundary_source_sha256':frame['boundary_source_sha256'],'allocation':'Uniform areal apportionment for intersected boundary cells; centroid of retained geometry (interior representative point if necessary), nearest strategic graph node; no post-flood resnapping. Population is a modeled 2018 grid, not observed trips or current population.','cities':rows},indent=2),encoding='utf-8')
