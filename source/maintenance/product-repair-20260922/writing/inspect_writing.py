from pathlib import Path
from bs4 import BeautifulSoup
import json
HERE=Path(__file__).resolve().parent
FORMAL=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
soup=BeautifulSoup(FORMAL.read_text(encoding='utf8'),'html.parser')
root=soup.find(id='writing-workbench')
(HERE/'original-workbench.html').write_text(str(root),encoding='utf8')
rows=[]
for el in soup.select('section[id],article[id]'):
 id=el['id']
 if ('writing' in id or 'essay' in id or 'jijing' in id) and not el.find_parent(id='writing-workbench'):
  rows.append(dict(id=id,tag=el.name,classes=el.get('class'),text=el.get_text(' ',strip=True),fields=[x.get('data-save') for x in el.select('[data-save]')],html=str(el)))
(HERE/'inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([dict(id=r['id'],chars=len(r['text']),fields=r['fields']) for r in rows],ensure_ascii=False))
content=[]
for el in soup.select('[id]'):
 id=el['id']
 if id.startswith(('wc-','jijing-202609','pr-jiufen','new-writing','writing1-first','writing2-first','test-writing')):
  content.append(dict(id=id,tag=el.name,text=el.get_text(' ',strip=True),html=str(el)))
(HERE/'question-detail.json').write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([dict(id=r['id'],text=r['text'][:200]) for r in content],ensure_ascii=False))
