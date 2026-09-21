from pathlib import Path
from bs4 import BeautifulSoup
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ui-repair-20260921'
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
raw=BOOK.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85'
(OUT/'source').mkdir(parents=True,exist_ok=True)
backup=OUT/'baseline.html'
if not backup.exists():backup.write_bytes(raw)
assert backup.read_bytes()==raw
s=BeautifulSoup(raw.decode('utf8'),'html.parser')
scripts=[]
for i,n in enumerate(s.find_all('script')):
    name=n.get('id',f'script-{i}')
    code=n.string or ''
    if code and n.get('type')!='application/json':
        (OUT/'source'/f'{name}.js').write_text(code,encoding='utf8')
    scripts.append({'id':name,'src':n.get('src'),'chars':len(code),'type':n.get('type')})
(OUT/'scripts.json').write_text(json.dumps(scripts,ensure_ascii=False,indent=2),encoding='utf8')
for ident in ['study','practice','workspace','records','library','vocabulary-review','sentence-learning','writing-workbench','topical-vocabulary','daily-study-home']:
    n=s.find(id=ident)
    (OUT/'source'/f'{ident}.html').write_text(str(n),encoding='utf8')
    print(ident,[(x.name,x.get('id'),x.get('class'),x.get_text(' ',strip=True)[:75]) for x in n.children if getattr(x,'name',None)])
(OUT/'baseline.json').write_text(json.dumps({'path':str(BOOK),'sha256':hashlib.sha256(raw).hexdigest(),'saved_fields':[n['data-save'] for n in s.select('[data-save]')],'ids':[n['id'] for n in s.select('[id]')],'media':[(n.name,n.get('src')) for n in s.select('img[src],audio[src],source[src]')]},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(scripts,ensure_ascii=False))
