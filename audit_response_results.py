from pathlib import Path
import json,sys,hashlib
import numpy as np
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
import population_routing as p
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def city(code):
 target=R/'response_audits'/f'{code}.json';target.parent.mkdir(exist_ok=True)
 source=R/'response_results'/f'{code}.json';identity=sha(source)
 if target.exists() and json.loads(target.read_text()).get('result_sha256')==identity:return
 obj=json.loads(source.read_text());assert obj['status']=='COMPLETE' and len(obj['scenarios'])==96
 ref=json.loads((R/'population_results'/f'{code}.json').read_text());support=dict(np.load(p.CACHE/'population_support'/f'{code}.npz'))
 bases={s:np.load(ref['dry_matrices']['dry_'+s]['path'],mmap_mode='r') for s in ['strategic','expanded']}
 errs=[];unit=[];hashed=0
 for name,info in obj['matrix_sources'].items():
  path=Path(info['path']);assert sha(path)==info['sha256'];hashed+=1
  variant,scope,grade,mask=name.split('|');wet=np.load(path,mmap_mode='r')
  for theta in [5,15,30,None]:
   row=next(r for r in obj['scenarios'] if (r['variant'],r['scope'],r['grade'],r['mask_policy'],r['theta'])==(variant,scope,grade,mask,theta))
   w,_=p.weights(bases['strategic'],support['endpoint_mass'],theta);actual=p.metrics(bases[scope],wet,w)
   for key in ['D','U','unconditional_finite_delay_minutes']:errs.append(abs(row[key]-actual[key]))
   w,_=p.weights(bases['strategic'],np.ones(len(support['endpoint_mass'])),theta);um=p.metrics(bases[scope],wet,w)
   unit.append({'variant':variant,'scope':scope,'grade':grade,'mask_policy':mask,'theta':theta,**um})
 assert len(errs)==288 and max(errs)<1e-10
 target.write_text(json.dumps({'status':'PASS','code':code,'result_sha256':identity,'comparisons':len(errs),'maximum_error':max(errs),'matrices_hashed':hashed,'unit_rows':unit},indent=2))
 print(json.dumps({'city':code,'response_audit':'PASS'}),flush=True)
def main():
 codes=[r['code'] for r in json.loads((R/'population_support_audit.json').read_text())['cities']]
 for c in codes:
  if (R/'response_results'/f'{c}.json').exists():city(c)
 complete=[json.loads((R/'response_audits'/f'{c}.json').read_text()) for c in codes if (R/'response_audits'/f'{c}.json').exists()]
 (R/'response_audit_summary.json').write_text(json.dumps({'status':'PASS' if len(complete)==36 else 'PARTIAL','cities':len(complete),'comparisons':sum(r['comparisons'] for r in complete),'matrix_references_hashed':sum(r['matrices_hashed'] for r in complete),'maximum_error':max(r['maximum_error'] for r in complete)},indent=2))
if __name__=='__main__':main()
