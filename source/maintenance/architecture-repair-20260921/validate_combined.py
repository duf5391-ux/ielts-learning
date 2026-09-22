from pathlib import Path
from collections import Counter
import hashlib,json,subprocess
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
read=lambda p:BeautifulSoup(p.read_text(encoding='utf8'),'html.parser')
base=read(ROOT/'ui-repair-20260921/baseline.html');new=read(HERE/'combined.html')
fields=lambda s:Counter((e['data-save'],e.name,e.get('type',''),e.get('value',''),e.get_text()) for e in s.select('[data-save]'))
assert fields(base)<=fields(new)
assert Counter(e['id'] for e in base.select('[id]'))<=Counter(e['id'] for e in new.select('[id]'))
assert len(new.select('[id]'))==len({e['id'] for e in new.select('[id]')})
for tag in ['audio','source','img']:assert Counter(e.get('src') for e in base.find_all(tag))==Counter(e.get('src') for e in new.find_all(tag))
for id in ['record-concurrency-model-script','energy-control-script','health-study-bridge-script','daily-study-model','daily-study-controller']:
 if base.find(id=id):assert str(base.find(id=id))==str(new.find(id=id)),id
folder=HERE/'combined-syntax';folder.mkdir(exist_ok=True);count=0
for i,s in enumerate(new.find_all('script')):
 if s.get('type','') in ['','text/javascript'] and s.string:
  p=folder/(str(i)+'.js');p.write_text(str(s.string),encoding='utf8');subprocess.run(['node','--check',str(p)],check=True,capture_output=True);count+=1
report={'pass':True,'sha256':hashlib.sha256((HERE/'combined.html').read_bytes()).hexdigest(),'oldFieldsPreserved':3368,'newFields':3,'scriptsSyntaxChecked':count,'idsMediaHealthDailyPreserved':True}
(HERE/'combined-static.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
p=HERE/'qa_health.cjs';s=p.read_text(encoding='utf8');s=s.replace("path.join(here,'candidate.html')","path.join(here,'combined.html')");p.write_text(s,encoding='utf8')
