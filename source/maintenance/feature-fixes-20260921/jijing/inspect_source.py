import json, re, sys, shutil, hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
publication=json.loads((ROOT/'content-pipeline/batches/jijing-20260920/publication.json').read_text(encoding='utf-8'))
page=Path(publication['formal_path']).read_text(encoding='utf-8')
data=json.loads(re.search(r'<script[^>]+id="learning-adjust-data"[^>]*>(.*?)</script>',page,re.S)[1])
print(data['skills'])
print(json.dumps([u for u in data['units'] if 'writing' in u['skill']][:2],ensure_ascii=False,indent=2))
print(re.findall(r'<section[^>]+id="([^"]*writing[^"]*)"',page))
raw=ROOT/'downloads/jiufen-jijing-20260921'
files=['materials-index.json','classification-methodology.md','raw/exams/2026548860543401986.json']+[f'raw/writing/{i}.json' for i in ['2083004583069663233','2082721901793837057','2082028220178825218']]
manifest=[]
for rel in files:
    src=raw/rel; dst=HERE/'source-snapshot'/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists(): shutil.copy2(src,dst)
    manifest.append({'source':str(src),'snapshot':str(dst.relative_to(HERE)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
(HERE/'snapshot-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
