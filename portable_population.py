from pathlib import Path
import argparse,json,hashlib,sys
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import population_routing as p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--codes',nargs='*');ap.add_argument('--response',action='store_true');args=ap.parse_args()
 output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
 assert output!=ROOT,'Use a separate output directory'
 manifest=json.loads((ROOT/'input_manifest.json').read_text());checked=0
 codes=args.codes or sorted(f.stem for f in (ROOT/'population_reference').glob('*.json'))
 for name,expected in manifest.items():
  if any('/'+c+'/' in '/'+name or name.endswith('/'+c+'.npz') for c in codes):
   assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name;checked+=1
 p.ROOT=output;p.CACHE=output;p.DATA=ROOT/'datasets'
 # Only a lightweight copy of population support is required in the output.
 import shutil
 shutil.copytree(ROOT/'population_support',output/'population_support',dirs_exist_ok=True)
 p.toy_tests();reports=[]
 for code in codes:
  p.run(code)
  actual=json.loads((output/'population_results'/f'{code}.json').read_text());reference=json.loads((ROOT/'population_reference'/f'{code}.json').read_text())
  key=lambda r:tuple(r[x] for x in ['model','theta','scope','grade','mask_policy'])
  ref={key(r):r for r in reference['scenarios']};err=[]
  for row in actual['scenarios']:
   for metric in ['D','U','unconditional_finite_delay_minutes']:
    err.append(abs(row[metric]-ref[key(row)][metric]))
  assert len(err)==264 and max(err)<1e-10
  reports.append({'code':code,'comparisons':len(err),'max_error':max(err)})
  if args.response:
   import response_robustness as response
   response.ROOT=output;response.test();response.run(code)
   source=ROOT/'response_results'/f'{code}.json'
   if source.exists():
    actual_response=json.loads((output/'response_results'/f'{code}.json').read_text())
    response_reference=json.loads(source.read_text())
    rkey=lambda r:tuple(r[k] for k in ['variant','scope','grade','mask_policy','theta'])
    lookup={rkey(r):r for r in response_reference['scenarios']};response_errors=[]
    for row in actual_response['scenarios']:
     for metric in ['D','U','unconditional_finite_delay_minutes']:response_errors.append(abs(row[metric]-lookup[rkey(row)][metric]))
    assert len(response_errors)==288 and max(response_errors)<1e-10
    reports[-1]['response_comparisons']=len(response_errors);reports[-1]['response_max_error']=max(response_errors)
 (output/'portable_audit.json').write_text(json.dumps({'status':'PASS','input_files_hashed':checked,'cities':reports},indent=2));print(json.dumps(reports))
if __name__=='__main__':main()
