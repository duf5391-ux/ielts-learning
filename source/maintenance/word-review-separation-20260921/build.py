"""Separate word library, review and sentence notebook into primary routes."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
BASE=ROOT/'architecture-repair-20260921/combined.html';EXPECTED='83346245cc01a3c48dcac31ce6c2b8a30744391cf6e4ae99f8db105103e6d166'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==EXPECTED
s=BeautifulSoup(BASE.read_text(encoding='utf8'),'html.parser');before=BeautifulSoup(str(s),'html.parser')
fragment=lambda h:BeautifulSoup(h,'html.parser')
nav=s.select_one('#workspace-navigation nav')
anchor=nav.select_one('[data-go="study"]')
for id,title in [('vocabulary-review','单词'),('word-review','复习'),('sentence-learning','句子')]:
 b=s.new_tag('button',attrs={'data-go':id,'type':'button'});span=s.new_tag('span');span.string=title;b.append(span);anchor.insert_after(b);anchor=b
 if s.find(id=id):s.find(id=id)['data-la-owner']=id
s.main.append(fragment('''<section id="word-review" class="panel workspace-panel learning-tool-panel" data-la-owner="word-review" data-la-title="单词复习" hidden><header class="vr-heading"><div><h1>单词复习</h1><p class="vr-muted">从收藏的单词开始，按到期时间复习，也可以自由加练。</p></div></header><nav class="word-tool-links" aria-label="词句工具"><a href="#vocabulary-review">查看单词表 →</a><a href="#sentence-learning">重看句子 →</a></nav></section>'''))
for a in list(s.select('#learning-tools a[href="#vocabulary-review"],#learning-tools a[href="#sentence-learning"]')):a.decompose()
for a in list(s.select('#sentence-learning > .la-section-links')):a.decompose()
s.find(id='sentence-learning').insert(0,fragment('<nav class="word-tool-links" aria-label="词句工具"><a href="#vocabulary-review">单词表 →</a><a href="#word-review">单词复习 →</a></nav>'))
s.select_one('#sentence-learning .st-kicker').decompose()
# Same store and controller. Move existing review controls instead of creating
# another queue, grading system, history field or duplicate review state.
js=(ROOT/'ui-repair-20260921/vocabulary-review-controller.js').read_text(encoding='utf8')
js=js.replace("if (!lookup || !host) return;","const reviewHost=document.getElementById('word-review');if (!lookup || !host || !reviewHost) return;")
js=js.replace("host.replaceChildren();","host.replaceChildren();const links=el('nav','','word-tool-links');const reviewLink=el('a','开始复习 →');reviewLink.href='#word-review';const sentenceLink=el('a','我的句子 →');sentenceLink.href='#sentence-learning';links.append(reviewLink,sentenceLink);host.append(links);")
for name in ['stats','controls','status','stage','note']:js=js.replace('host.append('+name+')','reviewHost.append('+name+')')
js=js.replace("stage.hidden=false; library.open=false; nextCard();","stage.hidden=false; library.open=true;location.hash='word-review'; nextCard();")
js=js.replace("stage.hidden=true;library.open=true;session=null;refresh();}","stage.hidden=true;library.open=true;session=null;refresh();location.hash='vocabulary-review';}")
# Feedback from list actions remains visible on the word page as well.
js=js.replace("function announce(text) { status.textContent=text; }","function announce(text) { status.textContent=text;const n=document.getElementById('word-list-status');if(n)n.textContent=text; }")
js=js.replace("host.append(heading);","host.append(heading);const listStatus=el('p','','vr-muted');listStatus.id='word-list-status';listStatus.setAttribute('role','status');host.append(listStatus);")
s.find(id='vocabulary-review-controller').string=js
assert str(s.find(id='lookup-controller').string).strip()==(ROOT/'ui-repair-20260921/source/lookup-controller.js').read_text(encoding='utf8').strip()
s.find(id='lookup-controller').string=(ROOT/'ui-repair-20260921/lookup-controller.js').read_text(encoding='utf8')
j=str(s.find(id='learning-adjust-script').string)
j=j.replace("'vocabulary-review':'我的单词表'","'word-review':'单词复习','vocabulary-review':'我的单词表'")
j=j.replace("guide:'今天',study:'学习'","'word-review':'复习','vocabulary-review':'单词','sentence-learning':'句子',guide:'今天',study:'学习'")
s.find(id='learning-adjust-script').string=j
style=s.new_tag('style',id='word-review-separation-style');style.string='''.word-tool-links{display:flex;gap:20px;flex-wrap:wrap;margin:0 0 18px}.word-tool-links a{font-size:14px;color:#376648}#vocabulary-review .vr-heading{margin-top:0}#vocabulary-review .vr-library{border:0;padding:0}#vocabulary-review .vr-library>summary{display:none}#word-review .vr-heading{margin-bottom:12px}#word-review .vr-stats{margin:16px 0}#vocabulary-review .vr-help{display:none}#workspace-navigation nav button{flex-shrink:0}#workspace-navigation nav{overflow-y:auto;min-height:0}@media(max-width:600px){#vocabulary-review .vr-heading h1,#word-review h1{font-size:26px}.word-tool-links{margin-bottom:14px;gap:16px}}''';s.head.append(style)
OUT=HERE/'candidate.html';OUT.write_text(str(s),encoding='utf8')
fields=lambda d:Counter((e['data-save'],e.name,e.get('type',''),e.get('value',''),e.get_text()) for e in d.select('[data-save]'))
assert fields(before)==fields(s)
assert Counter(e['id'] for e in before.select('[id]'))<=Counter(e['id'] for e in s.select('[id]'))
assert len(s.select('[id]'))==len({e['id'] for e in s.select('[id]')})
for id in ['record-concurrency-model-script','health-study-bridge-script','daily-study-script','daily-study-model-script','energy-control-script']:
 assert str(before.find(id=id))==str(s.find(id=id)),id
for id in ['lookup-controller','vocabulary-review-controller','learning-adjust-script']:
 p=HERE/(id+'.js');p.write_text(str(s.find(id=id).string),encoding='utf8');subprocess.run(['node','--check',str(p)],check=True)
manifest={'source_sha256':EXPECTED,'candidate_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'fields':len(s.select('[data-save]')),'units':227,'newRoute':'word-review','oldDataPreserved':True}
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(manifest))
