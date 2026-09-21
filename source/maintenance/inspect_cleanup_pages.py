from pathlib import Path
from bs4 import BeautifulSoup
import json,re
root=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
out={}
for name in ['开始学习.html','完整词汇来源库.html','词频与原文证据.html','扩展资料目录.html']:
 soup=BeautifulSoup((root/name).read_text(encoding='utf-8'),'html.parser')
 found=[]
 for t in soup.find_all(string=re.compile('官方|来源|核验|出处|注明|原创|版权|回忆汇编')):
  if t.parent.name in ('style','script'): continue
  p=t.parent
  a=[]
  for parent in [p,*list(p.parents)[:3]]:
   a.append(parent.name+('#'+parent['id'] if parent.get('id') else '')+(''.join('.'+c for c in parent.get('class',[]))))
  found.append({'path':' < '.join(a),'text':str(t).strip()})
 out[name]={'matches':found,'scripts':[s.get_text()[:10000] if len(s.get_text())<30000 else {'id':s.get('id'),'length':len(s.get_text()),'start':s.get_text()[:200]} for s in soup.find_all('script')]}
Path('C:/Users/Admin1/Documents/ChatGPT/ielts/cleanup-pages-inspection.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in out.items():
 print(k,len(v['matches']))
 print(json.dumps(v['matches'][:20],ensure_ascii=False,indent=2))
