"""Patch the current classified page; preserve old and new audit evidence."""
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import hashlib,json,sys,shutil

ROOT=Path(__file__).resolve().parent
LIVE=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
TARGET=Path('D:/IELTS-Work/learning-adjust-20260920/开始学习-feature-checked.html')
BASE_SHA='3b4ee9cdce99f45a6819818095b55067e928120448cc66401b3545ae92ae8acf'
raw=LIVE.read_bytes();assert hashlib.sha256(raw).hexdigest()==BASE_SHA,'Live changed; inspect and merge first'
s=BeautifulSoup(raw.decode('utf8'),'html.parser')
old=BeautifulSoup(raw.decode('utf8'),'html.parser')
s.find(id='learning-adjust-script').string=(ROOT/'learning-adjust.js').read_text(encoding='utf8')

# Dedicated panels keep imported material lists outside legacy hidden catalogs.
for ident,panel,title,category in [('vocabulary-additions','my-vocabulary-materials','我的词汇资料','vocabulary'),('topic-additions','my-topic-materials','我的话题资料','shared')]:
    root=s.new_tag('section',id=panel,attrs={'class':'panel workspace-panel','hidden':'','data-la-owner':'study','data-la-title':title})
    nav=BeautifulSoup(f'<nav class="la-section-links"><a href="#study-{category}-list">← 返回{"词汇" if category=="vocabulary" else "共用背景"}</a><a href="#materials">管理我的资料 →</a></nav>','html.parser').nav
    root.append(nav);root.append(s.find(id=ident).extract());s.main.append(root)

material=s.find_all('script')[3]
needle="window.addEventListener('hashchange',()=>{if(location.hash==='#usage-cards')"
replacement="window.addEventListener('hashchange',()=>{if(['#my-vocabulary-materials','#vocabulary-additions'].includes(location.hash)){vocabFilter='all';$('#vocab-search').value='';}if(location.hash==='#usage-cards')"
assert material.string.count(needle)==1
material.string=material.string.replace(needle,replacement)

# Keep practical options available without making them prerequisites to learning.
course=s.find(id='course-window-script')
text=course.string.replace('\r\n','\n')
needle="  function renderWorkspace() {\n    workspace.replaceChildren();"
assert text.count(needle)==1
text=text.replace(needle,"  function renderWorkspace() {\n    const optionsOpen = !!workspace.querySelector('[data-cw-optional]')?.open;\n    workspace.replaceChildren();")
needle="    const stages = el('nav', '', 'cw-stages');"
assert text.count(needle)==1
options="""    const options = el('details', '', 'cw-optional'); options.dataset.cwOptional=''; options.open=optionsOpen;
    options.append(el('summary', '学习量与继续建议（可选）'));
    const budgetControl = el('div', '', 'cw-budget'); budgetControl.append(el('span', '本次可用时间'));
    for (const n of [5, 10, 15]) { const b = button(n + ' 分钟', () => { budget = n; goStage(c, liveStage); }); b.dataset.cwBudget=String(n); b.setAttribute('aria-pressed',String(budget===n)); budgetControl.append(b); }
    const workload = budget===5 ? '建议先做本节 1 道任务。' : budget===10 ? '建议先做本节前 2 道任务。' : '可按需要完成本节任务。';
    options.append(budgetControl,el('p',workload+' 随时可以调整或跳到其他内容，无需先选时间。','cw-muted'));
    const action=nextAction(c), recommendation=el('aside','','cw-next'); recommendation.append(el('strong','根据最近作答继续'),el('p',action.text));
    const nextTask=action.taskId||c.stages.find(s=>s.id===action.stage)?.tasks.find(t=>!action.targets||t.targets.some(v=>action.targets.includes(v)))?.id;
    const nextButton=button('打开建议内容 →',()=>goStage(c,action.stage,nextTask));nextButton.dataset.cwRecommendation=action.stage;recommendation.append(nextButton);
    if(action.offerSource)recommendation.append(button('回看对应原料讲解（计为看过提示）',()=>revealSources(c,taskById(c,state.attempts.filter(a=>a.courseId===c.id).slice(-1)[0].taskId),recommendation)));
    options.append(recommendation);workspace.append(options);
"""
course.string=text.replace(needle,options+needle)

fields=lambda t:Counter(n['data-save'] for n in t.select('[data-save]'))
assert fields(old)==fields(s)
assert Counter(n['id'] for n in old.select('[id]'))<=Counter(n['id'] for n in s.select('[id]'))
assert all(v==1 for v in Counter(n['id'] for n in s.select('[id]')).values())
for ident in ['daily-study-home','daily-study-style','daily-study-state','daily-study-catalog','daily-study-model-script','daily-study-script','learning-adjust-data']:
    assert str(old.find(id=ident))==str(s.find(id=ident)),ident
before=old.find_all('script');after=s.find_all('script');assert len(before)==len(after)
changed=[i for i,(a,b) in enumerate(zip(before,after)) if str(a)!=str(b)];assert changed==[3,14,24],changed
assert [(n.name,n.get('src')) for n in old.select('[src]')]==[(n.name,n.get('src')) for n in s.select('[src]')]
output=str(s).encode('utf8');TARGET.write_bytes(output)
report={'baseSHA256':BASE_SHA,'sha256':hashlib.sha256(output).hexdigest(),'target':str(TARGET),'savedFields':sum(fields(s).values()),'units':218,'changedScripts':changed,'dailyUnchanged':True,'published':False}
(ROOT/'research/feature-completeness-repair-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
sys.stdout.reconfigure(encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))

if '--publish' in sys.argv:
    for name in ['feature-repairs-tests-20260920.json','learning-function-final-fixed-20260920.json']:
        qa=json.loads((ROOT/'research'/name).read_text(encoding='utf8'))
        assert qa['sha256']==report['sha256'] and qa['passed']==qa['total'],name
    qa=json.loads((ROOT/'research/feature-repair-static-20260920.json').read_text(encoding='utf8'))
    assert qa['sha256']==report['sha256'] and not any(qa[k] for k in ['duplicateIds','missingAnchors','missingLocalFiles'])
    assert hashlib.sha256(LIVE.read_bytes()).hexdigest()==BASE_SHA
    backup=Path('D:/IELTS-Backups/2026-09-20-feature-completeness');backup.mkdir(parents=True,exist_ok=True)
    previous=backup/'开始学习-before-feature-check-3b4ee9cdce99.html'
    if not previous.exists():shutil.copy2(LIVE,previous)
    assert hashlib.sha256(previous.read_bytes()).hexdigest()==BASE_SHA
    temp=LIVE.with_name('开始学习-feature-'+report['sha256'][:12]+'.tmp');temp.write_bytes(output)
    assert hashlib.sha256(temp.read_bytes()).hexdigest()==report['sha256']
    assert hashlib.sha256(LIVE.read_bytes()).hexdigest()==BASE_SHA
    temp.replace(LIVE)
    assert hashlib.sha256(LIVE.read_bytes()).hexdigest()==report['sha256']
    report.update(published=True,live=str(LIVE),backup=str(previous))
    (ROOT/'research/feature-completeness-repair-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    (backup/'README-回退说明.md').write_text(f'恢复 `{previous.name}` 到 `{LIVE}` 即可回退本轮功能补漏。原始分类前完整备份仍保留。本次没有访问或修改浏览器实际记录。\n\n旧 SHA256：{BASE_SHA}\n新 SHA256：{report["sha256"]}\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
