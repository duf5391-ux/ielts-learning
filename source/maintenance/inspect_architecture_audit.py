from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import json, hashlib

HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
OUT=HERE/'architecture-audit-qa'
OUT.mkdir(exist_ok=True)
page=(BOOK/'开始学习.html').read_text(encoding='utf8')
s=BeautifulSoup(page,'html.parser')
for n in list(s.select('[data-content-audit], [data-architecture-audit]')): n.decompose()
old=json.loads((HERE/'audit-content-20260919.json').read_text(encoding='utf8'))
items=[]
for x in old['items']:
    n=s.select_one(x['target_selector'])
    text=n.get_text(' ',strip=True)
    items.append({'id':x['id'],'title':x['title'],'category':x['category'],'status':x['status'],'selector':x['target_selector'],'text':text,'sha256':hashlib.sha256(str(n).encode()).hexdigest(),'fields':len(n.select('[data-save]')),'headings':[h.get_text(' ',strip=True) for h in n.select('h2,h3,h4,summary')],'checks':x['checks'],'reason':x['reason'],'action':x['next_action']})
(OUT/'live-items.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf8')
for i,n in enumerate(s.select('script')): (OUT/f'live-script-{i}.js').write_text(n.get_text(),encoding='utf8')
for id in ['guide','plan','records','library','prep','materials']:
    n=s.find(id=id)
    if n:(OUT/f'panel-{id}.txt').write_text(n.get_text(' ',strip=True),encoding='utf8')
stats={'bytes':len(page.encode()),'fields':len(s.select('[data-save]')),'field_duplicates':[k for k,v in Counter(n['data-save'] for n in s.select('[data-save]')).items() if v>1],'scripts':[{ 'index':i,'id':n.get('id'),'type':n.get('type'),'chars':len(n.get_text())} for i,n in enumerate(s.select('script'))],'panels':[n['id'] for n in s.select('main>.panel')],'ids':len(s.select('[id]')),'duplicate_ids':[k for k,v in Counter(n['id'] for n in s.select('[id]')).items() if v>1],'categories':dict(Counter(x['category'] for x in items))}
(OUT/'inventory.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(stats,ensure_ascii=False,indent=2))
print('\n'.join(f"{x['id']} | {x['category']} | {x['title']} | {x['status']} | {len(x['text'])} chars" for x in items))
