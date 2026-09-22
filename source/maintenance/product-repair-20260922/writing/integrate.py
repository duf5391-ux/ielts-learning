"""Writing-only incremental composition, based on the actual formal controller."""
from pathlib import Path
from bs4 import BeautifulSoup
from html import escape
import copy,json,re,hashlib
HERE=Path(__file__).resolve().parent
e=lambda v:escape(str(v),quote=True)
frag=lambda html:BeautifulSoup(html,'html.parser')
QUESTIONS=json.loads((HERE/'questions.json').read_text(encoding='utf8'))
MARKER='product-writing-repair-20260922'

def bridge(q,origin):
 return frag(f'<aside class="ww-origin-link" data-ww-source="{e(q["id"])}"><a href="#{e(q["id"])}" data-ww-open="{e(q["id"])}" data-ww-from="{e(origin)}">完整写作 · {e(q["title"])} →</a><span data-ww-source-status="{e(q["id"])}">工作台尚未开始</span><small>工作台保留一份独立首稿与修订；本页已有作答照常保留。</small></aside>').aside

def build_unit(q,template):
 uid=q['id'];unit=copy.deepcopy(template);oldid=unit['id']
 # Reuse only generic controls; new questions get entirely new field identities.
 for node in [unit,*unit.find_all(True)]:
  for attr,val in list(node.attrs.items()):
   if isinstance(val,str):node[attr]=val.replace(oldid,uid)
 unit['data-ww-unit']=uid.removeprefix('ww-');unit['data-ww-minimum']='150' if q['skill']=='writing1' else '250';unit['data-ww-minutes']='20' if q['skill']=='writing1' else '40'
 unit.header.h2.string=q['title'];unit.header.p.string='从自己的首稿开始，按需要检查与修订。'
 unit.header.select_one('.ww-badge').string=('Academic Task 1' if q['skill']=='writing1' else 'Task 2')+' · '+q['type']
 plan=unit.find(id=uid+'-plan')
 # Replace task-specific teaching with optional neutral planning questions.
 for help_ in plan.select('[data-ww-support]'):help_.decompose()
 labels=['题目比较什么？对象、范围和单位是什么？','哪些主要特征应进入概览？','哪些信息适合放在一起比较？','原图中有哪些数据、位置或步骤需要核对？'] if q['skill']=='writing1' else ['题目有哪些问句或判断？','我的回答或立场是什么？','第一个理由：为什么成立，有什么例子？','第二个理由、对照或边界是什么？']
 for i,label in enumerate(labels,1):unit.select_one(f'[data-save="{uid}-plan-{i}"]').parent.span.string=label
 next_=unit.find(id=uid+'-next');next_.h3.string='可选 / 下次再写'
 # Do not clone unrelated question-specific micro exercises into a new task.
 for node in list(next_.children):
  if getattr(node,'name',None) and (node.name=='details' or (node.name=='p' and not node.select('[data-save]'))):node.decompose()
 micro=unit.select_one(f'[data-save="{uid}-micro"]');micro.parent.span.string='可选：以后想检查的句子或片段'
 return unit

def decorate(q,unit,soup):
 uid=q['id'];plan=unit.find(id=uid+'-plan')
 unit['data-ww-question-id']=q['questionId'];unit['data-ww-version']=str(q['version'])
 unit['data-ww-origin']=q['origin']
 for field,suffix,value in [('stage','stage',''),('origin','return-route','')]:
  unit.append(frag(f'<input type="hidden" data-save="{uid}-{suffix}" value="{value}">').input)
 # Keep old prompts/IDs semantically same; attach the verified full question wording.
 oldprompt=plan.select_one('.ww-prompt');oldprompt.clear();oldprompt.append(q['prompt'])
 for image in plan.select('.ww-figure'):image.decompose()
 oldsource=plan.select_one('.ww-backlinks').previous_sibling
 if getattr(oldsource,'name',None) is None:oldsource=plan.select_one('.ww-backlinks').find_previous_sibling()
 if oldsource and oldsource!=oldprompt:oldsource.decompose()
 links=plan.select_one('.ww-backlinks');links.clear()
 links.append(frag(f'<a href="#{q["origin"]}" data-ww-return="{uid}">回到原题入口</a>').a)
 topic=frag('<details class="ww-topic"><summary>查看题面'+('与图表' if q['image'] else '')+' · 来源</summary></details>').details
 topic.append(oldprompt.extract())
 topic.append(frag(f'<p class="ww-rule" lang="en">{e(q["instruction"])}</p>').p)
 if q['image']:topic.append(frag(f'<figure class="ww-figure"><a href="{e(q["image"])}" target="_blank" rel="noopener"><img src="{e(q["image"])}" alt="{e(q["title"])} · 已核对的原题图表" loading="lazy" decoding="async"></a></figure>').figure)
 source=frag(f'<div class="ww-source-detail">{q["sourceHtml"]}<p class="ww-muted">参考置信度：{e(q["confidence"])}</p>{q.get("difficultyHtml","")}</div>').div
 topic.append(source);topic.append(links.extract())
 unit.header.insert_after(topic)
 unit.header.append(frag(f'<p class="ww-related" data-ww-related="{uid}"></p>').p)
 unit.header.append(frag(f'<a class="ww-back-origin" href="#{q["origin"]}" data-ww-return="{uid}">回到原题入口</a>').a)
 # Reading-to-writing expressions retain their exact material relationships.
 if q['prepHtml']:
  prep=frag(q['prepHtml']).section
  for node in [prep,*prep.find_all(True)]:
   if node.get('id'):node['id']=uid+'-'+node['id']
  prep['data-ww-writing-case']=q['questionId']
  if prep.has_attr('data-writing-case'):del prep['data-writing-case']
  wrapper=frag('<details class="ww-reading-prep"><summary>阅读后写作 · 本题可用表达</summary></details>').details
  wrapper.append(prep);topic.insert_after(wrapper)
 for step in unit.select('.ww-step'):
  step['data-ww-step']=step['id'].removeprefix(uid+'-')
  if step['data-ww-step']!='draft':step['hidden']=''
  if step['data-ww-step']=='next':step.h3.string='可选 / 下次再写'
  elif step['data-ww-step']=='draft':step.h3.string='首稿 · '+q['title']
 unit.select_one(f'[data-save="{uid}-first"]').parent.span.string='首稿 · 保留后锁定，在「检查与修订」中修改'
 for link in unit.select('.ww-progress a'):
  if link['href'].endswith('-next'):link.string='可选 · 再写'
  if link['href'].endswith('-plan'):link.string='提纲'
  if link['href'].endswith('-draft'):link.string='首稿'
  if link['href'].endswith('-review'):link.string='检查与修订'
 unit.select_one('.ww-progress').append(frag('<button type="button" data-ww-prompt-toggle>题面</button>').button)
 unit.select_one('.ww-progress').append(frag('<button type="button" data-ww-catalogue>换题</button>').button)
 for check in unit.select('.ww-check'):
  check.name='details';heading=check.h4;heading.name='summary'
 return unit

def apply(page:str)->str:
 if f'id="{MARKER}"' in page:return page
 soup=BeautifulSoup(page,'html.parser');root=soup.find(id='writing-workbench');assert root
 before={x['data-save']:str(x) for x in soup.select('[data-save]')}
 templates={s:copy.deepcopy(root.find(id='ww-jobs' if s=='writing1' else 'ww-primary')) for s in ['writing1','writing2']}
 picker=root.find(id='ww-task-picker')
 picker.parent.contents[0].replace_with('选题 / 继续上次')
 root.select_one('.ww-heading').clear();root.select_one('.ww-heading').append(frag('<h1>写作工作台</h1>').h1)
 root.select_one('.ww-switcher').find('a').extract()
 root.select_one('.ww-switcher')['hidden']=''
 directory=frag('<section class="ww-directory" aria-label="写作题目目录"><h2>找一道题开始写</h2><div class="ww-directory-tools"><label>搜索题目<input id="ww-directory-search" type="search" placeholder="题目、主题或来源"></label><label>Task<select id="ww-directory-task"><option value="">全部</option><option value="writing1">Task 1</option><option value="writing2">Task 2</option></select></label></div><p class="ww-directory-count" role="status"></p><div class="ww-directory-list"></div></section>').section
 for q in QUESTIONS:
  diff=frag(q.get('difficultyHtml','')).select_one('.jj-update-badge')
  difficulty=diff.get_text(' ',strip=True) if diff else '难度未评估'
  if diff and '难度' not in difficulty:
   diff=next((n for n in frag(q.get('difficultyHtml','')).select('.jj-update-badge') if '难度' in n.text),None);difficulty=diff.get_text(' ',strip=True) if diff else '难度未评估'
  confidence=q['confidence'].split('（')[0]
  task='Task 1' if q['skill']=='writing1' else 'Task 2'
  row=frag(f'<a class="ww-directory-row" href="#{q["id"]}" data-ww-pick="{q["id"]}" data-ww-skill="{q["skill"]}" data-ww-search="{e(q["title"]+" "+q["prompt"]+" "+q["source"]["title"])}"><strong>{e(q["title"])}</strong><span>{task} · {e(difficulty)} · 参考置信度：{e(confidence)} · {e(q["source"]["title"])}</span><small data-ww-row-status="{q["id"]}">开始首稿 →</small></a>').a
  directory.select_one('.ww-directory-list').append(row)
 root.select_one('.ww-switcher').insert_after(directory)
 root.find(id='ww-resume').insert_after(frag('<p class="ww-compact-note">题面、首稿与修订在同一处。写过的内容会自动保留。</p>').p)
 for q in QUESTIONS:
  unit=root.find(id=q['id']) if q['existing'] else build_unit(q,templates[q['skill']])
  if not q['existing']:
   root.select_one('.ww-footer').insert_before(unit)
   group=picker.find('optgroup',label='Academic Task 1' if q['skill']=='writing1' else 'Task 2')
   group.append(frag(f'<option value="{q["id"]}">{"Task 1" if q["skill"]=="writing1" else "Task 2"} · {e(q["title"])}</option>').option)
  decorate(q,unit,soup)
  if q.get('newOrigin'):
   origin=frag(f'<article id="{q["origin"]}" class="ww-published-question" data-learning-unit="{q["origin"]}"><h2>{e(q["title"])} · Task 2</h2>{q.get("difficultyHtml","")}<p class="ww-muted">参考置信度：{e(q["confidence"])}</p><div class="ww-origin-prompt" lang="en">{e(q["prompt"])}</div><p lang="en">{e(q["instruction"])}</p>{q["sourceHtml"]}</article>').article
   soup.find(id='practice-writing2').append(origin)
  for a in q['aliases']:
   origin=soup.find(id=a['route']);assert origin,a['route']
   # One clear local entry: an enclosing same-question learning unit already supplies it.
   if any(origin.find_parent(id=other['route']) for other in q['aliases'] if other['route']!=a['route']):continue
   b=bridge(q,a['route'])
   if origin.get('id')=='test-writing':
    field=soup.select_one(f'[data-save="{a["fields"][0]}"]');field.parent.insert_before(b)
   elif origin.select_one('.case-body'):
    origin.select_one('.case-task[lang="en"]').insert_after(b)
   elif origin.name=='details':origin.summary.insert_after(b)
   elif origin.select_one('.jj-prompt'):origin.select_one('.jj-prompt').insert_after(b)
   elif origin.find(['h2','h3']):origin.find(['h2','h3']).insert_after(b)
   else:origin.append(b)
 # New reference questions have direct, indexed entry points; completion uses actual writing actions.
 data_node=soup.find(id='learning-adjust-data');data=json.loads(data_node.string)
 for q in QUESTIONS:
  if not q.get('newOrigin'):continue
  data['units'].append(dict(id=q['origin'],mode='practice',skill='writing2',skillLabel='写作 · Task 2',title=q['title']+' · Task 2',topic='机经 · 2026年9月',type='Task 2完整写作',description=q['confidence']+'。首稿、四维检查和修订在写作工作台。',steps=[dict(kind='answer',key=q['id']+'-first'),dict(kind='answer',key=q['id']+'-first-at'),dict(kind='answer',key=q['id']+'-versions')],part='Task 2',category='机经',progressLabel='首稿、保留与修订版本',source=q['source']['title'],referenceConfidence='中'))
 data_node.string=json.dumps(data,ensure_ascii=False,separators=(',',':'))
 script=next(s for s in soup.find_all('script') if "const root = document.getElementById('writing-workbench');" in s.get_text())
 script.string=patched_controller(script.get_text())
 style=soup.new_tag('style',id=MARKER);style.string=(HERE/'writing.css').read_text(encoding='utf8');soup.head.append(style)
 mapping=soup.new_tag('script',id='writing-question-map',type='application/json');mapping.string=json.dumps([{k:q[k] for k in ['id','questionId','version','title','origin','aliases']} for q in QUESTIONS],ensure_ascii=False).replace('</','<\\/');script.insert_before(mapping)
 enhancement=soup.new_tag('script',id='writing-entry-controller');enhancement.string=(HERE/'entry.js').read_text(encoding='utf8');script.insert_after(enhancement)
 # Existing controls must keep their names, form types, defaults and options.
 after_fields={x['data-save']:x for x in soup.select('[data-save]')}
 for key,raw in before.items():
  after=after_fields.get(key);assert after is not None,key
  old=frag(raw).find(attrs={'data-save':key})
  assert old.name==after.name and old.get('type')==after.get('type'),key
  assert old.get('value')==after.get('value') and old.has_attr('checked')==after.has_attr('checked'),key
  if old.name=='textarea':assert old.text==after.text,key
  if old.name=='select':
   oldopts=[str(x) for x in old.find_all('option')]
   assert all(x in [str(v) for v in after.find_all('option')] for x in oldopts) if key=='ww-active-task' else str(old)==str(after),key
 return str(soup)

def patched_controller(js):
 def replace(a,b):
  nonlocal js
  assert js.count(a)==1,a[:100]
  js=js.replace(a,b,1)
 replace("const field = (unit, suffix) => byKey(`${unit.id}-${suffix}`);", "const field = (unit, suffix) => byKey(`${unit.id}-${suffix}`);\n"+(HERE/'stages.js').read_text(encoding='utf8'))
 replace("resumeStatus(selected);\n    return selected;", "setStage(selected, field(selected,'stage').value || (field(selected,'first-at').value ? 'review' : 'draft'));\n    resumeStatus(selected);\n    return selected;")
 replace("requestAnimationFrame(() => target.scrollIntoView({block:'start'}));", "const step = target.closest('[data-ww-step]');\n      setStage(unit, step?.dataset.wwStep || field(unit,'stage').value || unit.dataset.wwCurrentStage || 'draft', !!step);\n      requestAnimationFrame(() => unit.querySelector('[data-ww-step]:not([hidden])').scrollIntoView({block:'start'}));")
 replace("} else if (hash === 'writing-workbench') selectUnit(picker.value);", "} else if (hash === 'writing-workbench') {\n      const selected=selectUnit(picker.value);\n      if (field(selected,'first').value.trim() || field(selected,'first-at').value) requestAnimationFrame(()=>selected.querySelector('[data-ww-step]:not([hidden])').scrollIntoView({block:'start'}));\n    }")
 replace("unit.querySelector(`#${unit.id}-review`).scrollIntoView({behavior: 'smooth', block: 'start'});", "setStage(unit,'review',true);\n    location.hash=unit.id+'-review';\n    unit.querySelector(`#${unit.id}-review`).scrollIntoView({behavior:'smooth',block:'start'});")
 replace("unit.querySelector('.ww-backlinks').previousElementSibling.textContent", "unit.querySelector('.ww-source-detail').textContent")
 replace('再安排一个局部练习。','如确有需要，再建议一个可选的局部练习。')
 replace('首稿已保留；下方修订稿可继续修改，首稿保持原样。','首稿已保留；在「检查与修订」中继续修改，首稿保持原样。')
 return js

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
 source=Path(args.input);target=Path(args.output);assert source.resolve()!=target.resolve()
 result=apply(source.read_text(encoding='utf8'));assert apply(result)==result
 target.write_text(result,encoding='utf8',newline='');print(hashlib.sha256(target.read_bytes()).hexdigest())
