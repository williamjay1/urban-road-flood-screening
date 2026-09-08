"""Run all city recomputations, with package verification before calculation."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--codes',nargs='+');args=ap.parse_args()
    subprocess.run([sys.executable,str(ROOT/'verify_inputs.py')],check=True)
    codes=args.codes or json.loads((ROOT/'input_manifest.json').read_text(encoding='utf-8'))['codes']
    subprocess.run([sys.executable,str(ROOT/'recompute.py'),'--data',str(ROOT/'datasets'),'--reference',str(ROOT/'results'),'--output',str(args.output.resolve()),'--codes',*codes],check=True)
