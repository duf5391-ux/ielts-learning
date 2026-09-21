"""Finish the four-entry UI on the preserved candidate, including the live daily module.

No old builder is run. A publication checks the exact live base and a fresh QA report.
"""
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from collections import Counter
from html import escape
import json, hashlib, re, shutil, sys, argparse

ROOT=Path(__file__).resolve().parent
STAGE=Path('D:/IELTS-Work/learning-adjust-20260920')
SOURCE=STAGE/'开始学习-repaired.html'
TARGET=STAGE/'开始学习-ui-final.html'
LIVE=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
REPORT=ROOT/'research/navigation-ui-final-20260920.json'
SOURCE_SHA='e7ba1c456ae3234cf46024e7c31c01ed371188a42e0e2bb53cf30b614c6093c2'
LIVE_SHA='9ea2422ccda6eb3bd063ed716259585f0fcc2a34d6f7a62358d11e35834b9d97'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def add(n,html):
    for c in list(BeautifulSoup(html,'html.parser').contents):n.append(c)

def build():
    raw=SOURCE.read_bytes();live=LIVE.read_bytes()
    assert sha(raw)==SOURCE_SHA,'Reviewed candidate changed'
    assert sha(live)==LIVE_SHA,'Current live book changed; merge it before proceeding'
    s=BeautifulSoup(raw.decode('utf8'),'html.parser');base=BeautifulSoup(live.decode('utf8'),'html.parser')
    ids={n['id']:n for n in s.select('[id]')}
    data=json.loads(ids['learning-adjust-data'].string);data['navigationVersion']=3
    # Keep existing content improvements. This pass edits navigation and its labels.
    for u in data['units']:
        title=u['title'];u['part']=''
        match=re.search(r'Part\s*([1-4])',title,re.I)
        if match:u['part']='Part '+match[1]
        text=title+' '+u['id']
        choices=[('判断|TFNG|judgement|statements','判断题'),('标题|headings','标题匹配'),('匹配|matching|people','匹配题'),('填空|summary|notes|表单|表格|流程图','填空与信息整理'),('单选|多选|选择|choice','选择题'),('短答|short.answer','简答题'),('图表|折线|柱状|饼图|table|chart','图表'),('地图|map','地图'),('流程|process','流程图'),('观点|利弊|议论|argument','观点与论证'),('词汇|vocab','词汇运用')]
        u['category']=next((label for pattern,label in choices if re.search(pattern,text,re.I)), '表达与运用' if u['skill'] in ['phrases','speaking','writing1','writing2'] else '理解与方法')
    evidence=json.loads((ROOT/'research/listening-full-answer-evidence-20260920.json').read_text(encoding='utf8'))
    listening=data['tests']['listening'];old_note=listening['note']
    listening['key']={str(x['question']):x['answer_options_for_existing_text_input'] for x in evidence['items']}
    assert len(listening['key'])==40
    listening['note']='官方机考体验题 · 40题。选择题可填字母，提交后核对参考答案。'
    for t in list(s.find_all(string=True)):
        if t.parent.name in ['script','style']:continue
        if old_note in str(t):t.replace_with(str(t).replace(old_note,listening['note']))
    # Copy the currently published daily feature, rather than rebuilding it from sources.
    for ident in ['daily-study-style','daily-study-state','daily-study-catalog','daily-study-model-script','daily-study-script']:
        n=base.find(id=ident);assert n is not None,ident
        (s.head if n.name=='style' else s.main if ident=='daily-study-state' else s.body).append(n.extract())
    guide=ids['guide'];guide['data-la-owner']='study';guide['data-la-title']='直接开始学习'
    projects=s.new_tag('section',id='learning-projects',attrs={'class':'panel workspace-panel','hidden':'','data-la-owner':'study','data-la-title':'学习项目'})
    add(projects,'<header class="la-heading"><a href="#study">← 返回学习</a><h1>学习项目</h1><p>按建议顺序完成一组内容，也可以直接进入其中一项。</p></header>')
    project_section=guide.select_one('[data-project]').find_parent('section');projects.append(project_section.extract())
    add(projects,'<p><a href="#course-window">打开我的定制课程 →</a></p>');s.main.append(projects)
    study=ids['study'];resume=ids['la-resume'].extract()
    quick=s.new_tag('section',id='la-study-quick',attrs={'class':'la-quick'})
    add(quick,'<div class="la-quick-main"><h2>直接开始学习</h2><p>已有默认安排；也可以选板块和 15／30／60 分钟。</p><a href="#guide">查看安排并开始 →</a></div><div class="la-quick-side"><h2>继续上次</h2><div class="la-resume-slot"></div><div class="la-quick-links"><a href="#learning-projects">学习项目 →</a><a href="#plan">今天选的内容 →</a></div></div>')
    quick.select_one('.la-resume-slot').replace_with(resume);ids['la-study-location'].insert_after(quick)
    # The daily screen contains its own setup, not another parallel homepage/menu.
    hidden=s.new_tag('div',attrs={'class':'la-hidden-legacy'})
    for n in list(guide.contents):hidden.append(n.extract())
    guide.append(hidden);add(guide,'<nav class="la-section-links"><a href="#study">← 返回学习</a></nav>')
    guide.append(base.find(id='daily-study-home').extract())
    # Preserve the daily integrator's exact block boundaries for future updates.
    for ident,mark in [('daily-study-home','home'),('daily-study-style','style'),('daily-study-state','state')]:
        n=s.find(id=ident);n.insert_before(Comment('DAILY-STUDY-V1:'+mark));n.insert_after(Comment('/DAILY-STUDY-V1:'+mark))
    s.find(id='daily-study-catalog').insert_before(Comment('DAILY-STUDY-V1:scripts'))
    s.find(id='daily-study-script').insert_after(Comment('/DAILY-STUDY-V1:scripts'))
    extras=ids['la-study-extras'];extras.clear();extras['class']='la-study-extras'
    add(extras,'<h2>词汇与背景</h2><div class="la-extra-grid"><a href="#study-vocabulary-list"><strong>词汇</strong><span>单词、语境与主动运用 →</span></a><a href="#study-phrases-list"><strong>短语</strong><span>搭配、用法与配套小练 →</span></a><a href="#study-shared-list"><strong>共用背景</strong><span>供不同科目使用的阅读材料 →</span></a></div>')
    for mode in ['study','practice']:
        root=ids[mode]
        for code in ['writing1','writing2']:add(root,f'<span id="{mode}-{code}-list"></span>')
        toolbar=root.select_one('.la-toolbar')
        for code,label in [('part','Part'),('type','题型／内容')]:
            add(toolbar,f'<label>{label}<select id="la-{mode}-{code}"><option value="">全部</option></select></label>')
        toolbar.select_one('label:has(input)').extract();toolbar.append(ids['la-'+mode+'-search'].find_parent('label'))
        ids['la-'+mode+'-search']['placeholder']='搜索本类内容'
    # Keep clear links to every existing workspace function.
    workspace=ids['workspace'];grid=s.new_tag('div',attrs={'class':'la-workspace-grid'})
    for card in list(workspace.select(':scope > .la-card')):grid.append(card.extract())
    for target,title,note in [('vocabulary-review','我的单词表','复习收藏的单词、原句与搭配。'),('sentence-learning','我的句子本','回看收藏的句子、译文和修改。')]:
        add(grid,f'<article class="la-card" data-workspace-shortcut="{target}"><h2>{title}</h2><p>{note}</p><a href="#{target}">打开 →</a></article>')
    workspace.append(grid)
    for card in grid.select('.la-card'):
        if card.find('a').get('href')=='#course-window':
            card.find('h2').string='我的定制课程';card.find('p').string='继续自己导入或定制的课程。'
    for ident,title in [('records','学习记录与备份'),('materials','我的资料'),('library','原始资料'),('writing-workbench','写作工作台'),('plan','今天选的内容'),('course-window','我的定制课程')]:
        p=ids[ident];p['data-la-title']=title
        nav=s.new_tag('nav',attrs={'class':'la-section-links'});add(nav,f'<a href="#{"study" if ident=="course-window" else "workspace"}">← 返回{"学习" if ident=="course-window" else "工作区"}</a>');p.insert(0,nav)
    tests=ids['tests'];tests.select_one(':scope > .la-grid')['class']='la-grid la-test-selection'
    for card in tests.select(':scope > .la-grid > .la-card'):
        card['class']='la-card la-subject-card';card.find('a').string='选择'+card.find('h2').get_text()+'测试 →'
    mock=tests.select_one(':scope > .la-card');mock['class']='la-mock-card';mock.find('h2').string='四科组合测试'
    mock.find('p').string='依次完成听力、阅读、写作和口语。使用公开样题与 Cambridge 21 材料组合，各科分别保存；口语可另行完成。'
    ids['la-start-mock'].string='开始四科组合测试'
    sidebar=s.select_one('.sidebar-goal');sidebar.clear();add(sidebar,'<p>按自己的节奏学习。</p><a href="#guide">直接开始学习 →</a><br><a href="#plan">今天选的内容 →</a>')
    for a in s.select('#workspace-navigation a[href="#guide"]'):
        if not a.find_parent(class_='sidebar-goal'):a['href']='#study'
    # Legacy panels still exist for saved fields and deep links. Root entry defaults to Study.
    for script in [s.find_all('script')[0],s.find_all('script')[2]]:
        script.string=script.string.replace("||'guide'", "||'study'")
    ids['learning-adjust-data'].string=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    ids['learning-adjust-script'].string=(ROOT/'learning-adjust.js').read_text(encoding='utf8')
    style=s.new_tag('style',id='navigation-ui-final-style');style.string=(ROOT/'navigation-ui.css').read_text(encoding='utf8');s.head.append(style)
    # Validate against the live book as well as the candidate.
    live_s=BeautifulSoup(live.decode('utf8'),'html.parser')
    count=lambda tree:Counter(n['data-save'] for n in tree.select('[data-save]'))
    assert not count(live_s)-count(s),'Live saved fields removed'
    assert all(v==1 for v in count(s).values()),'Duplicate saved fields'
    before_ids={n['id'] for n in live_s.select('[id]')};after_ids=Counter(n['id'] for n in s.select('[id]'))
    assert before_ids<=after_ids.keys(),'Live anchor removed'
    assert not [k for k,v in after_ids.items() if v>1],'Duplicate IDs'
    media=lambda tree:Counter((n.name,n.get('src')) for n in tree.select('img,audio,source') if n.get('src'))
    assert not media(live_s)-media(s),'Live media removed'
    for ident in ['daily-study-style','daily-study-state','daily-study-catalog','daily-study-model-script','daily-study-script','daily-study-home']:
        assert str(live_s.find(id=ident))==str(s.find(id=ident)),ident+' changed'
    output=str(s).encode('utf8');TARGET.write_bytes(output)
    report={'source':str(SOURCE),'sourceSHA256':SOURCE_SHA,'liveSourceSHA256':LIVE_SHA,'target':str(TARGET),'sha256':sha(output),'published':False,'liveFields':sum(count(live_s).values()),'candidateFields':sum(count(s).values()),'units':len(data['units']),'dailyModulePreserved':True,'primary':['学习','练习','测试','工作区'],'browserVisualVerified':False,'scope':'Finish classification, entry UI, subject pickers, labels and return routes; preserve existing candidate content fixes and current live daily feature.'}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))

def publish():
    report=json.loads(REPORT.read_text(encoding='utf8'));qa=json.loads((ROOT/'research/navigation-ui-final-tests-20260920.json').read_text(encoding='utf8'))
    static=json.loads((ROOT/'research/navigation-ui-static-20260920.json').read_text(encoding='utf8'))
    assert sha(LIVE.read_bytes())==report['liveSourceSHA256'],'Live changed; rebase before publication'
    assert sha(TARGET.read_bytes())==report['sha256']==qa['sha256']
    assert qa['passed']==qa['total'] and qa['total']>=10,'Navigation regressions must pass'
    assert static['sha256']==report['sha256'] and static['passed']==static['total'],'Static preservation checks must pass'
    backup=Path('D:/IELTS-Backups/2026-09-20-ui-classification');backup.mkdir(exist_ok=True)
    dest=backup/('开始学习-before-ui-'+LIVE_SHA[:12]+'.html')
    if not dest.exists():shutil.copy2(LIVE,dest)
    assert sha(dest.read_bytes())==LIVE_SHA
    added=[]
    for f in (STAGE/'learning-assets').iterdir():
        dst=LIVE.parent/'learning-assets'/f.name;dst.parent.mkdir(exist_ok=True)
        if dst.exists():assert sha(dst.read_bytes())==sha(f.read_bytes()),'Conflicting asset '+f.name
        else:shutil.copy2(f,dst);added.append(str(dst))
    assert sha(LIVE.read_bytes())==report['liveSourceSHA256'],'Live changed while copying assets'
    temp=LIVE.with_name('开始学习-navigation-'+report['sha256'][:12]+'.tmp')
    temp.write_bytes(TARGET.read_bytes());assert sha(temp.read_bytes())==report['sha256'];temp.replace(LIVE)
    assert sha(LIVE.read_bytes())==report['sha256']
    report.update(published=True,live=str(LIVE),backup=str(dest),addedAssets=added);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    (backup/'README-回退说明.md').write_text(f'# 分类入口 UI 回退\n\n正式页面：{LIVE}\n\n恢复本目录 `{dest.name}` 到原正式页面即可；原版含直接开始学习。浏览器用户记录未被读取或改写。新增加的 learning-assets 文件可留在原位，旧版不引用它们。\n\n旧版 SHA256：{LIVE_SHA}\n新版 SHA256：{report["sha256"]}\n',encoding='utf8')
    print(json.dumps({'published':True,'live':str(LIVE),'sha256':report['sha256'],'backup':str(dest)},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');args=p.parse_args();publish() if args.publish else build()
