"""Recompute the complete cross-intensity factorial from portable inputs."""
from pathlib import Path
import argparse,json,hashlib,sys,shutil
import numpy as np
PACKAGE=Path(__file__).resolve().parent
sys.path.insert(0,str(PACKAGE))
import hazard_population as h

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--codes',nargs='+',required=True);ap.add_argument('--cumulative',action='store_true');args=ap.parse_args()
    out=Path(args.output).resolve();assert out!=PACKAGE and PACKAGE not in out.parents,'Use a separate output directory'
    out.mkdir(exist_ok=True,parents=True)
    manifest=json.loads((PACKAGE/'hazard_input_manifest.json').read_text())
    for record in manifest['files']:
        if record.get('code') not in args.codes:continue
        path=PACKAGE/record['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],record['path']
    h.P=PACKAGE;h.R=out;h.C=PACKAGE;h.p.DATA=PACKAGE/'datasets';h.p.CACHE=out
    audit=[]
    for code in args.codes:
        target=out/'hazard_inputs'/code;target.mkdir(exist_ok=True,parents=True)
        for scope in ['strategic','expanded']:shutil.copyfile(PACKAGE/'hazard_inputs'/code/f'{scope}.npz',target/f'{scope}.npz')
        h.run(code)
        result=json.loads((out/'hazard_results'/f'{code}.json').read_text());reference=json.loads((PACKAGE/'hazard_reference'/f'{code}.json').read_text())
        keys=['period','model','theta','scope','grade','mask_policy'];lookup={tuple(x[k] for k in keys):x for x in reference['rows']};errors=[]
        for row in result['rows']:
            ref=lookup[tuple(row[k] for k in keys)]
            errors.extend(abs(row[k]-ref[k]) for k in ['D','U','unconditional_finite_delay_minutes'])
        assert max(errors)<1e-10
        audit.append({'code':code,'metric_comparisons':len(errors),'max_absolute_error':max(errors)})
    cumulative_audit=[]
    if args.cumulative:
        script=(PACKAGE/'depth_order_control.py').read_text(encoding='utf-8')
        exec(compile(script,str(PACKAGE/'depth_order_control.py'),'exec'),{'__file__':str(out/'depth_order_control.py')})
        for code in args.codes:
            result=json.loads((out/'depth_order_results'/f'{code}.json').read_text())
            reference=json.loads((PACKAGE/'depth_order_reference'/f'{code}.json').read_text())
            keys=['period','model','theta','scope','grade','mask_policy'];lookup={tuple(x[k] for k in keys):x for x in reference['cost_changed_scenarios']};errors=[]
            assert len(result['cost_changed_scenarios'])==len(lookup)
            for row in result['cost_changed_scenarios']:
                ref=lookup[tuple(row[k] for k in keys)];errors.extend(abs(row[k]-ref[k]) for k in ['cumulative_D','cumulative_U'])
            assert max(errors or [0])<1e-10;cumulative_audit.append({'code':code,'metric_comparisons':len(errors),'max_error':max(errors or [0])})
    (out/'portable_hazard_audit.json').write_text(json.dumps({'status':'PASS','cities':audit,'cumulative':cumulative_audit},indent=2));print(json.dumps(audit))

if __name__=='__main__':main()
