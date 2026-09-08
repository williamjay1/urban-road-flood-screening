from pathlib import Path
import fitz,json
R=Path(__file__).resolve().parent
out=[]
for p in sorted((R/'article/figures').glob('*.pdf')):
    q=R/'reproducibility/article/figures'/p.name
    a=fitz.open(p);b=fitz.open(q)
    x=a[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5));y=b[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
    out.append({'figure':p.name,'identical':x.samples==y.samples,'size_equal':(x.width,x.height)==(y.width,y.height)})
report={'status':'PASS' if all(x['identical'] for x in out) else 'FAIL','comparisons':out}
(R/'figure_reproduction_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
