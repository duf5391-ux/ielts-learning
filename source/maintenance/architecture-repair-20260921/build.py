"""Incremental architecture repair from the fingerprinted production page."""
from pathlib import Path
from collections import Counter
import hashlib
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'ui-repair-20260921/baseline.html'
EXPECTED = '2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == EXPECTED
s = BeautifulSoup(BASE.read_text(encoding='utf-8'), 'html.parser')
before = BeautifulSoup(str(s), 'html.parser')
def fragment(html): return BeautifulSoup(html, 'html.parser')
def replace_script(id, change):
    script=s.find(id=id); script.string=change(str(script.string))
def replace_exact(text, old, new):
    assert old in text, old[:100]
    return text.replace(old,new)
def back(panel, target='study', label='学习'):
    nav=panel.find('nav',class_='la-section-links',recursive=False)
    if nav: nav.decompose()
    panel.insert(0,fragment(f'<nav class="la-section-links"><a href="#{target}">← 返回{label}</a></nav>'))

# Existing hashes and fields remain stable; these become genuine main panels.
for id,title in [('vocabulary-review','我的单词表'),('sentence-learning','我的句子本')]:
    panel=s.find(id=id).extract()
    panel['class']=list(dict.fromkeys(panel.get('class',[])+['panel','workspace-panel','learning-tool-panel']))
    panel['data-la-owner']='study';panel['data-la-title']=title;panel['hidden']=''
    s.main.append(panel)
    if id=='sentence-learning':
        back(panel);panel.find('h2').name='h1'
for id in ['writing-workbench','course-window','plan']:
    panel=s.find(id=id);panel['data-la-owner']='study';back(panel)
s.find(id='plan')['data-la-title']='自选清单'
s.select_one('#plan > header p:last-child').string='从学习或练习中加入想做的内容，按自己的节奏选择；清单保留到你手动移除。'

def vocabulary(js):
    js=replace_exact(js,'host.replaceChildren();',"host.replaceChildren();\n  const back=el('nav','','la-section-links'), backLink=el('a','← 返回学习');backLink.href='#study';back.append(backLink);host.append(back);")
    return replace_exact(js,"el('h2','我的单词表')","el('h1','我的单词表')")
replace_script('vocabulary-review-controller',vocabulary)

# Study is the home of learning activities; workspace manages sources and records.
study=s.find(id='la-study-extras')
study.append(fragment('''<section class="learning-tools" id="learning-tools"><h2>我的学习</h2><div class="la-extra-grid">
<a href="#vocabulary-review"><strong>我的单词表</strong><span>收藏词语、直接标记、回忆复习 →</span></a>
<a href="#sentence-learning"><strong>我的句子本</strong><span>重看收藏的句子与译文 →</span></a>
<a href="#writing-workbench"><strong>写作工作台</strong><span>审题、首稿、检查与修订 →</span></a>
<a href="#course-window"><strong>我的定制课程</strong><span>按已有课程继续学习 →</span></a></div></section>'''))
workspace=s.find(id='workspace');workspace['data-la-title']='工作台'
workspace.select_one('h1').string='工作台'
workspace.select_one('.la-heading > p:last-child').string='整理原始资料和个人材料，查看学习记录与备份。'
grid=workspace.select_one('.la-workspace-grid');grid.clear()
grid.append(fragment('''<article class="la-card"><h2>原始资料</h2><p>原题、图表、音频和配套文件。</p><a href="#library">查找资料 →</a></article>
<article class="la-card"><h2>我的资料</h2><p>导入、编辑和整理自己的材料。</p><a href="#materials">管理资料 →</a></article>
<article class="la-card"><h2>记录与备份</h2><p>查看已保留的答案，导出或恢复记录。</p><a href="#records">查看记录 →</a></article>
<article class="la-card"><h2>资料接入与制课</h2><p>查看接入进度，整理需要在本机交给助手的材料与要求。</p><a href="#course-design">整理待设计资料 →</a></article>'''))

# Course design needs the local assistant; learning an already designed package
# is a different operation. No remote generation or connection is invented.
s.main.append(fragment('''<section id="course-design" class="panel workspace-panel" data-la-owner="workspace" data-la-title="资料接入与制课" hidden>
<nav class="la-section-links"><a href="#workspace">← 返回工作台</a></nav>
<header class="la-heading"><p class="la-kicker">MATERIALS / COURSE DESIGN</p><h1>资料接入与制课</h1><p>先整理原料与目标，再在本机与助手一起完成设计、核查和接入。</p></header>
<div class="course-design-boundary"><strong>当前网页没有连接本机助手</strong><p>这里可以保存和导出待设计资料，不会自动生成课程。请在本机助手可用时，通过项目对话交接材料；整理完成后再发布或导入课程。已制成的课程可以在网站继续学习。</p><a href="#course-window">查看已有课程 →</a></div>
<p id="cw-design-message" class="cw-message" role="status" aria-live="polite"></p><div id="course-design-app"></div>
<details id="content-intake-status"><summary>资料接入进度 · 2026年9月21日核对</summary>
<p>以下是随网站发布的资料批次进度，不包含只保存在你当前浏览器里的个人资料。</p>
<ul><li><strong>已接入：</strong>38组阅读材料精读，并把适用表达接到相关写作练习。<a href="#reading-case-bank">查看阅读材料</a></li>
<li><strong>已接入的小批机经：</strong>听力10题、阅读13题与9道Task 2参考题干；九分另有《语言起源》14题和3道Task 2。<a href="#pr-jiufen-20260921-origin-language-v1">查看已核查的九分阅读</a></li>
<li><strong>九分整批仍待接入：</strong>资料已归档，阅读切片及部分解析答案候选已整理；标准答案、逐段讲解和正式学习入口仍需核查。不能把这些原料计作已完成课程。</li></ul>
</details></section>'''))
course=s.find(id='course-window');course['data-la-title']='已有定制课程'
course.select_one('header h1').string='已有定制课程'
course.select_one('header > p:last-child').string='学习已经设计好的课程；制课需要另在本机与助手协作。'
for a in s.select('#learning-tools a[href="#course-window"]'):
    a.find('strong').string='已有定制课程';a.find('span').string='学习已导入课程；示例单独标明 →'
for a in s.select('#materials a[href="#course-window"]'):
    a['href']='#course-design'
s.find(id='materials').insert(1,fragment('<p class="material-intake-boundary">导入后先保存为个人资料，可阅读和整理；不会自动变成练习或定制课程。需要加工时，<a href="#course-design">整理需求并交给本机助手 →</a></p>'))

def course_design(js):
    js=replace_exact(js,"message.setAttribute('role', error ? 'alert' : 'status');", "message.setAttribute('role', error ? 'alert' : 'status'); const designMessage=document.getElementById('cw-design-message');designMessage.textContent=text;designMessage.classList.toggle('cw-error',error);designMessage.setAttribute('role',error?'alert':'status');")
    js=replace_exact(js,"mount.replaceChildren(introduction, message, toolbar, intake, listRegion, workspace);", "const designMount=document.getElementById('course-design-app'), draftList=el('div','','cw-list-region'), pendingWorkspace=el('div','','cw-workspace');draftList.id='cw-draft-list';pendingWorkspace.id='cw-pending-workspace';\n  const designToolbar=el('div','','cw-toolbar');designToolbar.append(briefButton);\n  const designLink=el('a','整理新资料或请求制课 →');designLink.href='#course-design';\n  mount.replaceChildren(message, toolbar, designLink, listRegion, workspace);\n  designMount.replaceChildren(designToolbar,intake,draftList,pendingWorkspace);")
    js=replace_exact(js,"safe(() => update(s => { s.selected = selected; })); renderList(); renderWorkspace();", "safe(() => update(s => { s.selected = selected; })); renderList(); renderWorkspace();location.hash=c?'course-window':'course-design';")
    js=replace_exact(js,"listRegion.replaceChildren(); const courses = allCourses()", "listRegion.replaceChildren();draftList.replaceChildren(el('h2','待设计原料'),el('p',state.drafts.length+' 批已保存，尚未制成课程','cw-muted')); const courses = allCourses()")
    js=replace_exact(js,"listRegion.append(el('h2', '我的学习窗口'), el('p', state.drafts.length + ' 批待设计 · ' + userCourses.length + ' 门已设计课程 · 示例单独体验，不计入我的批次。', 'cw-muted'));", "listRegion.append(el('h2', '课程列表'), el('p', userCourses.length + ' 门已设计课程 · 示例仅用于体验，不是已经为你制成的课程。', 'cw-muted'));")
    js=replace_exact(js,"b.dataset.cwCourse = d.id; b.setAttribute('aria-pressed', String(selected === d.id)); choices.append(b);", "b.dataset.cwCourse = d.id; b.setAttribute('aria-pressed', String(selected === d.id)); draftList.append(b);")
    js=replace_exact(js,"workspace.replaceChildren();\n    const d = state.drafts.find", "workspace.replaceChildren();pendingWorkspace.replaceChildren();\n    const d = state.drafts.find")
    js=replace_exact(js,"workspace.append(card); return; }", "pendingWorkspace.append(card);workspace.append(el('p','当前选择的是待设计原料，请从上方选择已有课程或示例。','cw-empty')); return; }")
    js=replace_exact(js,"已保存为待设计。导出需求后，我会基于原料、目标和学习记录设计课程。", "已保存为待设计，尚未生成课程。请导出需求，在本机项目对话中交给助手继续处理。")
    return js
replace_script('course-window-script',course_design)

# User 2026-09-21: defer custom courses entirely until local assistant integration.
# Retain the old controller and data for compatibility, expose only a future window.
for a in list(s.select('#learning-tools a[href="#course-window"]')):a.decompose()
course['data-la-owner']='workspace';course['data-la-title']='定制课程 · 待开放'
back(course,'workspace','工作台')
course.select_one('header h1').string='定制课程 · 待开放'
course.select_one('header > p:last-child').string='预留试用窗口。接入本机助手后，再开启资料设计与定制课程功能。'
runtime=s.new_tag('div',id='course-disabled-runtime',hidden='')
runtime.append(s.find(id='course-window-app').extract());course.append(runtime)
course.append(fragment('<p class="course-design-boundary">当前暂不开放制课、课程导入或试学。已有本地课程记录保留；一键学习继续使用已发布内容，不依赖这个窗口。</p>'))
s.find(id='course-design')['data-la-title']='资料接入进度'
s.select_one('#course-design header h1').string='资料接入进度'
s.select_one('#course-design header > p:last-child').string='新资料先拆分、核查，再按用途接入现有学习与题库。'
s.select_one('#course-design .course-design-boundary').clear()
s.select_one('#course-design .course-design-boundary').append(fragment('<strong>定制课程暂不开放</strong><p>目前优先整理新资料。制课窗口留待接入本机助手后试用。</p><a href="#course-window">查看预留窗口 →</a>'))
s.find(id='course-design-app')['hidden']=''
s.find(id='cw-design-message')['hidden']=''
for a in grid.select('a[href="#course-design"]'):
    a.parent.find('h2').string='资料接入进度';a.parent.find('p').string='查看新资料处理情况与定制课程预留窗口。';a.string='查看进度 →'
for a in s.select('#materials a[href="#course-design"]'):a.string='查看资料接入进度 →'

# Keep raw files in the workspace, and move the existing mixed teaching index to
# its already-linked #resource-update route, now a dedicated study panel.
library=s.find(id='library');resources=s.find(id='resource-update').extract()
resources['class']=['panel','workspace-panel','library-catalog'];resources['hidden']=''
resources['data-la-owner']='study';resources['data-la-title']='学习资源索引'
old_h2=resources.find('h2');old_h2.string='话题与学习技巧'
directory=s.find(id='text-question-directory').extract()
cases=library.select_one('.case-library-entry').extract()
wrappers=library.select_one('.pp-practice-nav').extract()
priority=s.find(id='official-fit-priority').extract()
extra=library.select_one('aside.new-library-entry').extract()
resources.insert(0,fragment('<header class="la-heading"><p class="la-kicker">LEARNING INDEX</p><h1>学习资源索引</h1><p>按题目、话题与技巧查找已有学习和练习。</p></header>'))
back(resources)
resources.append(directory);resources.append(cases);resources.append(wrappers);resources.append(priority);resources.append(extra)
s.main.append(resources)
library.select_one('header h1').string='原始资料'
library.select_one('header > p:last-child').string='查找原题、图表、音频与配套文件；学习活动从学习或练习进入。'
library.select_one('header > p:first-child').string='SOURCE MATERIALS'
for a in library.select('.library-jumps a[href="#resource-update"]'): a.extract()
library.append(fragment('<p class="source-study-link">想按题目或技巧学习？<a href="#resource-update">打开学习资源索引 →</a></p>'))
study.append(fragment('<p><a href="#resource-update">按题目与技巧查找学习资源 →</a></p>'))

# Give record management a proper heading before its actual data, with compact
# shortcuts to learning tools instead of embedding those tools inside records.
records=s.find(id='records');head=records.select_one('header.chapter-head').extract()
head.find('h1').string='学习记录与备份';records.insert(1,head)
aside=records.select_one('.ww-entry')
if aside: aside.decompose()
records.insert(2,fragment('<nav class="record-learning-links" aria-label="相关学习"><a href="#vocabulary-review">我的单词表</a><a href="#sentence-learning">我的句子本</a><a href="#writing-workbench">写作工作台</a></nav>'))

# Labels describe the actual persistent selection list. No forced conversion to
# daily sessions and no alteration to old learning-adjust-state.today records.
for text in list(s.find_all(string=True)):
    if text.parent.name in ['script','style']: continue
    revised=str(text).replace('今天选的内容','自选清单').replace('返回学习工作台','返回工作台')
    if str(text).strip()=='学习工作台': revised=str(text).replace('学习工作台','工作台')
    if revised!=str(text): text.replace_with(revised)
for node in s.select('[data-la-title="今天选的内容"]'):node['data-la-title']='自选清单'

catalog=json.loads(s.find(id='learning-adjust-data').string)
for u in catalog['units']:
    if u['id']=='topic-education': u.update(skill='shared',skillLabel='共用背景')
    if u['id']=='pr-vocabulary-tourism': u.update(mode='practice',skill='vocabulary',skillLabel='词汇',category='改写与填空')
s.find(id='learning-adjust-data').string=json.dumps(catalog,ensure_ascii=False)
education=s.find(id='topic-education').extract();s.find(id='background').append(education)
for a in education.select('.reader-toolbar a'):a['href']='#study-shared-list'
tourism=s.find(id='pp-vocabulary');tourism['data-la-context']='practice-vocabulary-list'
practice=s.find(id='practice')
practice.append(fragment('<div id="architecture-practice-extras" class="la-study-extras"><h2>表达练习</h2><a href="#practice-vocabulary-list">词汇 · 语境改写与填空 →</a></div>'))

def navigation(js):
    js=replace_exact(js,"const scope = {study:'',practice:''};", "const scope = {study:'',practice:''};\n  const learningTools = {'vocabulary-review':'我的单词表','sentence-learning':'我的句子本','writing-workbench':'写作工作台'};")
    js=replace_exact(js,"const resume=$('#la-resume'),last=units.get(state.last);", "const resume=$('#la-resume'),last=units.get(state.last)||(learningTools[state.last]?{id:state.last,title:learningTools[state.last],isTool:true}:null);")
    js=replace_exact(js,"if(last)resume.append(bar(unitProgress(last),last.progressLabel||'完成'));", "if(last&&!last.isTool)resume.append(bar(unitProgress(last),last.progressLabel||'完成'));")
    js=replace_exact(js,"writing1:'study-writing-list',writing2:'study-writing-list'", "writing1:'study-writing1-list',writing2:'study-writing2-list'")
    js=replace_exact(js,"'practice-writing1':'practice-writing-list','practice-writing2':'practice-writing-list'", "'practice-writing1':'practice-writing1-list','practice-writing2':'practice-writing2-list'")
    js=replace_exact(js,"if(u&&state.last!==u.id)save({...state,last:u.id});", "const resumeId=u?.id||(learningTools[panel.id]?panel.id:'');\n    if(resumeId&&state.last!==resumeId)save({...state,last:resumeId});")
    js=replace_exact(js,"const quick=$('#la-'+mode+'-quick');if(quick)quick.hidden=!!group;", "const quick=$('#la-'+mode+'-quick');if(quick)quick.hidden=!!group;\n        if(mode==='practice')$('#architecture-practice-extras').hidden=!!group;")
    # Focus wrapper routes as collections. They do not become fake catalog units.
    js=replace_exact(js,"focusActivity(panel,u);renderCards();", "const collectionRoutes={'pp-reading':['reading','阅读练习'],'pp-listening':['listening','听力练习'],'pp-writing1':['writing1','Task 1 练习'],'pp-writing2':['writing2','Task 2 练习'],'pp-speaking':['speaking','口语练习'],'pp-vocabulary':['vocabulary','词汇练习'],'reading-case-bank':['reading','阅读原题片段'],'writing1-case-bank':['writing1','Task 1 原题片段'],'writing2-case-bank':['writing2','Task 2 原题片段']};\n      const collection=collectionRoutes[h];\n      if(collection&&!u){const focus={id:h,mode:'practice',skill:collection[0],skillLabel:labelOf(collection[0]),title:collection[1]};focusActivity(panel,focus);panel.dataset.laCollectionTitle=focus.title;}else{delete panel.dataset.laCollectionTitle;focusActivity(panel,u);}\n      renderCards();")
    js=replace_exact(js,"const owner=data.navigationVersion&&u?u.mode:panel.dataset.laOwner||panel.id;", "const owner=panel.dataset.laCollectionTitle?'practice':data.navigationVersion&&u?u.mode:panel.dataset.laOwner||panel.id;")
    js=replace_exact(js,"panel.dataset.laTitle||sectionName", "panel.dataset.laCollectionTitle||panel.dataset.laTitle||sectionName")
    js=js.replace("workspace:'学习工作台'","workspace:'工作台'")
    for old,new in [('今天选的内容','自选清单'),('移出今天','移出自选'),('加入今天','加入自选'),('到学习工作台','到工作台')]:js=js.replace(old,new)
    return js
replace_script('learning-adjust-script',navigation)

css=s.new_tag('style',id='architecture-layout-style')
css.string='''/* Architecture: reuse routes and records, change page boundaries. */
#vocabulary-review[hidden],#sentence-learning[hidden],#resource-update[hidden],#materials [hidden]{display:none!important}
#course-disabled-runtime[hidden],#course-design-app[hidden],#cw-design-message[hidden]{display:none!important}
.learning-tool-panel{margin:0!important;padding:24px!important;border:0!important;background:var(--paper,#fffdf7)!important}
.learning-tool-panel h1{font-size:clamp(25px,3vw,34px);line-height:1.25;margin:4px 0 10px}
.learning-tools{margin-top:30px}.record-learning-links{display:flex;gap:18px;flex-wrap:wrap;margin:16px 0 24px}
.course-design-boundary{padding:16px 20px;background:#edf3ed;border-radius:8px;margin-bottom:24px}#content-intake-status{margin-top:28px;border-top:1px solid #d8dfd8;padding-top:16px}#content-intake-status li{margin:12px 0}#cw-draft-list>button{display:block;margin:8px 0}.material-intake-boundary{padding:12px 16px;background:#edf3ed}
#resource-update{max-width:none}#resource-update>.la-heading{margin-bottom:24px}
#library>header{margin-bottom:24px}#library>.source-study-link{margin-top:28px}
#vocabulary-review .vr-heading{margin-top:12px}#sentence-learning .st-heading{margin-top:12px}
@media(max-width:600px){.learning-tool-panel{padding:16px!important}.learning-tools{margin-top:24px}.record-learning-links{gap:12px}.vr-stats{gap:8px}.vr-stats>div{padding:10px}.vr-help{margin-top:20px}}
'''
s.head.append(css)
candidate=HERE/'candidate.html';candidate.write_text(str(s),encoding='utf-8')
# Preservation evidence checks identities and values, not only counts.
def fields(doc):return Counter((e['data-save'],e.name,e.get('type',''),e.get('value',''),e.get_text()) for e in doc.select('[data-save]'))
assert fields(before)==fields(s),'Saved field identity/default changed'
assert Counter(e['id'] for e in before.select('[id]')) <= Counter(e['id'] for e in s.select('[id]')),'Lost IDs'
assert not [k for k,v in Counter(e['id'] for e in s.select('[id]')).items() if v>1], 'Duplicate IDs'
for tag,attr in [('audio','src'),('source','src'),('img','src')]:
    assert Counter(e.get(attr) for e in before.find_all(tag))==Counter(e.get(attr) for e in s.find_all(tag))
for id in ['record-concurrency-model-script','energy-control-script','health-study-bridge-script','daily-study-model','daily-study-controller']:
    if before.find(id=id):assert str(before.find(id=id))==str(s.find(id=id)),id
report=dict(source_sha256=EXPECTED,candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
            fields=len(s.select('[data-save]')),units=len(catalog['units']),panels=len(s.select('main > .panel')),
            preserved_fields=True,preserved_ids=True,preserved_media=True)
(HERE/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for script in s.find_all('script'):
    if script.get('type','') in ['','text/javascript'] and script.string:
        folder=HERE/'syntax';folder.mkdir(exist_ok=True)
        (folder/((script.get('id') or 'script-'+str(list(s.find_all('script')).index(script)))+'.js')).write_text(str(script.string),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
