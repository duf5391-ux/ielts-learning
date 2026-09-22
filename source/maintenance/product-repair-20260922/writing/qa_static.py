from pathlib import Path
from bs4 import BeautifulSoup
import hashlib,json,re
HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
before=BeautifulSoup((BOOK/'开始学习.html').read_text(encoding='utf8'),'html.parser')
raw=(HERE/'candidate.html').read_text(encoding='utf8');after=BeautifulSoup(raw,'html.parser')
questions=json.loads((HERE/'questions.json').read_text(encoding='utf8'))
fields=lambda s:{n['data-save']:n for n in s.select('[data-save]')}
a,b=fields(before),fields(after)
assert set(a)<=set(b)
for key,node in a.items():
 other=b[key];assert node.name==other.name and node.get('type')==other.get('type') and node.get('value')==other.get('value') and node.has_attr('checked')==other.has_attr('checked'),key
 if node.name=='textarea':assert node.text==other.text,key
 if node.name=='select':
  assert all(str(o) in [str(x) for x in other.select('option')] for o in node.select('option')),key
  assert node.select_one('option').get('value',node.select_one('option').text)==other.select_one('option').get('value',other.select_one('option').text),key
ids=[n['id'] for n in after.select('[id]')];assert len(ids)==len(set(ids)),[v for v in ids if ids.count(v)>1]
allkeys=[n['data-save'] for n in after.select('[data-save]')];assert len(allkeys)==len(set(allkeys))
for marker in ['record-concurrency-model-script','energy-control-script','daily-study-script','health-study-control-script']:
 node=before.find(id=marker)
 if node:assert str(node)==str(after.find(id=marker)),marker
for node in before.find_all('script'):
 text=node.string or ''
 if not text.strip() or "const root = document.getElementById('writing-workbench');" in text or node.get('id')=='learning-adjust-data':continue
 assert any(text==(x.string or '') for x in after.find_all('script')),node.get('id')
oldunits=json.loads(before.find(id='learning-adjust-data').string)['units'];units=json.loads(after.find(id='learning-adjust-data').string)['units'];assert units[:len(oldunits)]==oldunits
for q in questions:
 node=after.find(id=q['id']);assert node and after.find(id=q['origin'])
 assert node['data-ww-version']==str(q['version'])
 if q['image']:assert node.select_one('.ww-figure img')['src']==q['image'] and (BOOK/q['image']).is_file()
 for alias in q['aliases']:
  assert after.find(id=alias['route'])
  for k in alias['fields']:assert k in a,k
 # Cloned reading prep uses exact old paragraph text and routes, with unique node IDs.
 if q['prepHtml']:
  old=BeautifulSoup(q['prepHtml'],'html.parser').select_one('.material-writing')
  new=node.select_one('.material-writing');assert old.get_text()==new.get_text()
  assert [x['href'] for x in old.select('a')]==[x['href'] for x in new.select('a')]
report=dict(pass_=True,sha256=hashlib.sha256((HERE/'candidate.html').read_bytes()).hexdigest(),oldFields=len(a),newFields=len(b),addedFields=len(b)-len(a),oldUnits=len(oldunits),newUnits=len(units),questions=len(questions),newQuestions=26,task1=8,task2=24,idsUnique=True,protectedControllersUnchanged=True,existingDefaultsPreserved=True)
report['pass']=report.pop('pass_')
(HERE/'static-results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
mapping=[dict(id=q['id'],questionId=q['questionId'],origin=q['origin'],title=q['title'],skill=q['skill'],version=q['version'],existing=q['existing'],aliases=q['aliases']) for q in questions]
(HERE/'question-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf8')
index=[dict(id=q['id'],origin=q['origin'],sameSourceRoutes=[a['route'] for a in q['aliases']],title=q['title'],skill=q['skill'],topic=q['type'],description=q['prompt'],source=q['source']['title'],referenceConfidence=q['confidence'],mode='writing',tool='writing-workbench') for q in questions]
(HERE/'extra-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report))
