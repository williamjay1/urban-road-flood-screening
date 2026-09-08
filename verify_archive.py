from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent
m=json.loads((p/'archive_manifest.json').read_text())
for r in m['files']:
 with (p/r['path']).open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
 assert actual==r['sha256'],r['path']
print('PASS:',len(m['files']),'archived file identities')
