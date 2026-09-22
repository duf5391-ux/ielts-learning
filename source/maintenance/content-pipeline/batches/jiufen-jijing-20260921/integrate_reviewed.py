"""Integrate reviewed content only; proposed tensor uses never publish themselves."""
from pathlib import Path
from collections import Counter
import hashlib,html,json
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
BASE=ROOT/'architecture-repair-20260921/candidate.html';OUT=ROOT/'architecture-repair-20260921/combined.html'
ASSETS=HERE/'reviewed-assets';ASSETS.mkdir(exist_ok=True)
package=json.loads((HERE/'cleaned-luna-20260921/reviewed-package.json').read_text(encoding='utf-8'))
slices=json.loads((ROOT/'downloads/jiufen-jijing-20260921/reading-slices-index.json').read_text(encoding='utf-8'))
source_rows={x['id']:x for x in json.loads((ROOT/'downloads/jiufen-jijing-20260921/materials-index.json').read_text(encoding='utf-8'))['items']}
s=BeautifulSoup(BASE.read_text(encoding='utf-8'),'html.parser');before=BeautifulSoup(str(s),'html.parser')
catalog=json.loads(s.find(id='learning-adjust-data').string)
E=lambda x:html.escape(str(x),quote=True)
fragment=lambda h:BeautifulSoup(h,'html.parser')
assets=[]
for u in package['units']:
    assert hashlib.sha256((ROOT/u['sourceLocalPath']).read_bytes()).hexdigest()==u['sourceSha256']
    full=[p for f in slices['fragments'] if f['sourceUnitId']==u['sourceId'] for p in f['paragraphs']]
    rel='机经资料/jiufen-topic-20260921/'+u['sourceId']+'.html';file=ASSETS/rel;file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(u['sourceTitle'])+'</title><style>body{font:18px/1.85 system-ui;background:#faf9f3;color:#243d30;max-width:850px;margin:auto;padding:24px}p{margin:1.4em 0}a{color:#286648}h1{font-size:28px}</style><a href="../../index.html#'+E(u['id'])+'">← 返回材料精读</a><h1>'+E(u['sourceTitle'])+'</h1><p>来源：九分学长资料 · 原文存档，不将文中观点作为已独立证实的事实。</p>'+''.join('<p>'+E(p)+'</p>' for p in full)+'</html>',encoding='utf-8')
    # Formal local entry has a Chinese filename, rewritten for published pages.
    file.write_text(file.read_text(encoding='utf-8').replace('../../index.html#','../../开始学习.html#'),encoding='utf-8')
    assets.append(dict(path=rel,source=str(file),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    key=u['id']+'-read'
    body='<article class="topic-reader jiufen-close-unit" id="'+E(u['id'])+'" data-learning-unit="'+E(u['id'])+'"><h2>'+E(u['title'])+'</h2>'
    body+='<div class="reading-passage">'+''.join('<p>'+E(p)+'</p>' for p in u['originalParagraphs'])+'</div>'
    body+='<details><summary>这段的前后文</summary><h3>前一段</h3><p>'+E(u['precedingContext'])+'</p><h3>后一段</h3><p>'+E(u['followingContext'])+'</p><a href="'+E(rel)+'" target="_blank" rel="noopener">打开同一材料完整原文 →</a></details>'
    body+='<section class="material-close-reading"><h3>读懂这一段</h3><p>'+E(u['explanation'])+'</p><h3>原文词块</h3>'
    for v in u['vocabulary']:body+='<article><h4>'+E(v['term'])+'</h4><blockquote>'+E(v['quote'])+'</blockquote><p>'+E(v['meaning'])+'</p><p>'+E(v['usage'])+'</p></article>'
    body+='<h3>长句与关系</h3>'
    for q in u['sentences']:body+='<article><blockquote>'+E(q['quote'])+'</blockquote><p>'+E(q['meaning'])+'</p><p>'+E(q['structure'])+'</p></article>'
    body+='</section><label class="read-toggle"><input type="checkbox" data-save="'+E(key)+'"> 我读过这段（可选）</label></article>'
    s.find(id='reading').append(fragment(body))
    catalog['units'].append(dict(id=u['id'],mode='study',skill='reading',relatedSkills=['shared'],skillLabel='阅读',title=u['title'],topic=u['topic'],
       type='材料精读',category='材料精读',description='原文、相邻语境、内容理解、词块和长句关系。',steps=[dict(kind='check',key=key)],
       progressLabel='读过',part='',difficulty=u['difficulty'],referenceConfidence='低',source='九分学长',sourceId=u['sourceId'],sourceVersion=source_rows[u['sourceId']]['rawSha256'],derivedSourceVersion=u['sourceSha256'],
       contentVersion='sha256:'+hashlib.sha256(json.dumps(u,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),exposureFamily='jiufen:'+u['sourceId']))

# Entrance metadata for existing jijing units; keep all previous questions,
# saved keys and manually reviewed difficulty levels.
for u in catalog['units']:
    if 'jijing' in u['id'] or 'jiufen' in u['id']:
        subject='writing' if u['skill'].startswith('writing') else u['skill']
        u['referenceConfidence']={'reading':'低','listening':'高','speaking':'高','writing':'中'}.get(subject,'待核查')
        u.setdefault('source','九分学长' if 'jiufen' in u['id'] else '机经资料来源见题面')
newids=[u['id'] for u in package['units']]
projectId='jiufen-topic-close-20260921'
catalog['projects'].append(dict(id=projectId,title='新资料 · 话题与词句精读',units=newids))
project=s.new_tag('article',attrs={'class':'la-card la-project','data-project':projectId})
project.append(fragment('<h3>新资料 · 话题与词句精读</h3><p>同一段原文可从阅读学习或共用背景进入，收藏的词句继续进已有词句本。</p><div data-project-progress></div><ul>'+''.join('<li><a href="#'+E(u['id'])+'">'+E(u['title'])+'</a><small> · 难度 '+str(u['difficulty']['level'])+'/5 · 参考置信度低 · 九分学长</small></li>' for u in package['units'])+'</ul>'))
s.select_one('#learning-projects .la-grid').insert(0,project)
s.find(id='learning-adjust-data').string=json.dumps(catalog,ensure_ascii=False)
script=s.find(id='learning-adjust-script');js=str(script.string)
old="const scopeMatches = (u, group) => !group || u.skill===group || groupOf(u.skill)===group;"
assert old in js;js=js.replace(old,"const scopeMatches = (u, group) => !group || u.skill===group || groupOf(u.skill)===group || (u.relatedSkills||[]).includes(group);")
needle="const actions=el('div','','la-card-actions');actions.append(link(u.id"
assert needle in js
js=js.replace(needle,"if(u.referenceConfidence){const metadata=el('p','','content-entry-metadata');metadata.textContent='难度 '+(u.difficulty?.level?u.difficulty.level+'/5':'待评估')+' · 参考置信度'+u.referenceConfidence+' · '+u.source;metadata.title=(u.difficulty?.reason||u.difficulty?.rationale||'')+'；参考置信度是资料使用策略，不是命中率。';n.append(metadata);}\n    const actions=el('div','','la-card-actions');actions.append(link(u.id")
# Remember the current category only for compatible multi-use study entries.
js=js.replace("const scope = {study:'',practice:''};", "const scope = {study:'',practice:''};let lastCategory=null;")
js=js.replace("if(category){scope[category[1]]=category[2];", "if(category){lastCategory={mode:category[1],skill:category[2]};scope[category[1]]=category[2];")
old="nav.append(link(u.mode+'-'+(data.navigationVersion>=3?u.skill:groupOf(u.skill))+'-list','← '+(u.mode==='study'?'学习':'练习')+' / '+u.skillLabel),el('span',u.title));"
assert old in js
new="const returnSkill=lastCategory?.mode===u.mode&&(u.relatedSkills||[]).includes(lastCategory.skill)?lastCategory.skill:u.skill;nav.append(link(u.mode+'-'+(data.navigationVersion>=3?returnSkill:groupOf(returnSkill))+'-list','← '+(u.mode==='study'?'学习':'练习')+' / '+(returnSkill===u.skill?u.skillLabel:labelOf(returnSkill))),el('span',u.title));"
js=js.replace(old,new);script.string=js
css=s.new_tag('style',id='content-entry-metadata-style');css.string='.content-entry-metadata{font-size:12px;color:#526e5c;line-height:1.6}.jiufen-close-unit .reading-passage{font-size:18px;line-height:1.9}.jiufen-close-unit .material-close-reading article{margin:22px 0}.jiufen-close-unit blockquote{margin:12px 0;padding:10px 16px;border-left:3px solid #86a68c}.jiufen-close-unit details{margin:20px 0}'
s.head.append(css)
OUT.write_text(str(s),encoding='utf-8')
assert Counter(x['data-save'] for x in before.select('[data-save]'))<=Counter(x['data-save'] for x in s.select('[data-save]'))
assert len([x['id'] for x in s.select('[id]')])==len(set(x['id'] for x in s.select('[id]')))
report=dict(formalBaseline='2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85',architectureBaseSha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
 candidateSha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),fields=len(s.select('[data-save]')),units=len(catalog['units']),newUnits=newids,assets=assets,status='candidate-unpublished')
(HERE/'reviewed-integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='assets'},ensure_ascii=False))
