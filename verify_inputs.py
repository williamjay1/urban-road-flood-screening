"""Verify immutable packaged derived inputs before reproduction."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'input_manifest.json').read_text(encoding='utf-8'))
for item in manifest['files']:
    p=(ROOT/item['path']).resolve()
    if not p.is_relative_to(ROOT.resolve()):raise ValueError('Input outside package')
    if p.stat().st_size!=item['bytes']:raise ValueError('Size mismatch: '+item['path'])
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    if h.hexdigest()!=item['sha256']:raise ValueError('Hash mismatch: '+item['path'])
print(json.dumps({'status':'PASS','files':len(manifest['files']),'bytes':manifest['bytes']}))
