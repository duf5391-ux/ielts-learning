"""Reorganise the verified September 20 checkpoint, preserving every saved field.

Default: stage only. --write publishes after independent QA. A changed live file is
never overwritten unless it is the checkpoint or this integrator's last output.
"""
from pathlib import Path
from bs4 import BeautifulSoup,Tag
from collections import Counter
from html import escape as E
import argparse,hashlib,json,re,shutil,sys
from build_complete_tests import build as build_tests

ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
BACKUP=Path('D:/IELTS-Backups/2026-09-20_133954-before-learning-adjust')
BASE=BACKUP/'original-project/outputs/IELTS-四科学习册/开始学习.html'
OUT=Path('D:/IELTS-Work/learning-adjust-20260920')
REPORT=ROOT/'research/learning-adjust-integration-20260920.json'
MAIN=BOOK/'开始学习.html'
LABELS={'reading':'阅读','listening':'听力','writing1':'写作 · Task 1','writing2':'写作 · Task 2','speaking':'口语','vocabulary':'词汇','phrases':'短语','shared':'共用背景'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def frag(html):return BeautifulSoup(html,'html.parser')
def add(node,html):
    for n in list(frag(html).contents):node.append(n)
def heading(title,note=''):
    return f'<header class="la-heading"><p class="la-kicker">IELTS / MY STUDY</p><h1>{E(title)}</h1><p>{E(note)}</p></header>'
def source_text(n):return n.get_text(' ',strip=True)
def field(key,label,rows=3):return f'<label class="field"><span>{E(label)}</span><textarea data-save="{E(key)}" rows="{rows}"></textarea></label>'
def name(n):
    h=n.find(['summary','h1','h2','h3','h4']);return source_text(h)[:90] if h else n.get('id','学习内容')

def adjust():
    assert json.loads((BACKUP/'backup-status.json').read_text(encoding='utf8'))['status']=='VERIFIED'
    raw=BASE.read_bytes();live=MAIN.read_bytes();allowed={sha(raw)}
    if REPORT.exists():allowed.add(json.loads(REPORT.read_text(encoding='utf8')).get('outputSHA256',''))
    assert sha(live) in allowed,'Live book changed independently; inspect changes before integration.'
    s=BeautifulSoup(raw.decode('utf8'),'html.parser');units=[];seen=set();gates=0
    original_fields=Counter(n['data-save'] for n in s.select('[data-save]'))
    original_ids={n['id'] for n in s.select('[id]')}
    original_media=Counter((n.name,n.get('src')) for n in s.select('img,audio,source') if n.get('src'))
    def panel(ident,title,note,owner=None):
        n=frag(f'<section id="{ident}" class="panel workspace-panel" hidden data-la-owner="{owner or ident}" data-la-title="{E(title)}">{heading(title,note)}</section>').find();s.main.append(n);return n
    study=panel('study','学习','按科目、话题或题型找讲解，做配套的小练习。')
    practice=panel('practice','练习','按实际任务选择：阅读题、听力题、写作或口语。')
    tests=panel('tests','测试','完整套题与单科测试单独作答；学习和练习记录不计入测试进度。')
    workspace=panel('workspace','工作区','继续写作、收集词句、整理资料，或查看和备份记录。')
    phrases=panel('phrases','短语','按意思和使用场景学习搭配；词汇单独列出。','study')
    practice_panels={k:panel('practice-'+k,LABELS[k]+'练习','选择一个题组，先作答，再核对答案。','practice') for k in ['reading','listening','writing1','writing2','speaking','phrases']}
    for ident in ['background','vocabulary','reading','listening','writing1','writing2','speaking','course-window']:
        s.find(id=ident)['data-la-owner']='study';s.find(id=ident)['data-la-title']=LABELS.get(ident,{'background':'共用背景','course-window':'我的学习项目'}.get(ident,ident))
    for ident in ['records','library','materials','writing-workbench','plan']:
        s.find(id=ident)['data-la-owner']='workspace'
    # Keep legacy home IDs used by record summaries, but remove its old journey from the UI.
    guide=s.find(id='guide');legacy=s.new_tag('div',attrs={'class':'la-hidden-legacy','aria-hidden':'true'})
    for n in list(guide.contents):legacy.append(n.extract())
    guide.append(legacy);add(guide,heading('今天想学什么','接着学、按顺序做一组，或者直接挑一项。'))
    add(guide,'<div id="la-resume" class="la-card"></div><div class="la-grid"><article class="la-card"><p class="la-kicker">LEARN</p><h2>学会一个具体用法</h2><p>讲解、例子和配套练习放在一起。</p><a href="#study">选择学习内容 →</a></article><article class="la-card"><p class="la-kicker">PRACTISE</p><h2>直接练一项</h2><p>按科目、话题或题型挑选。</p><a href="#practice">选择练习 →</a></article><article class="la-card"><p class="la-kicker">TEST</p><h2>完整做一套</h2><p>四科组合，或单独完成一科。</p><a href="#tests">进入测试 →</a></article></div><section><h2>今天选的内容</h2><div id="la-today-progress"></div><ul id="la-today-list" class="la-list"></ul></section>')
    plan=s.find(id='plan');oldplan=s.new_tag('div',attrs={'class':'la-hidden-legacy'})
    for n in list(plan.contents):oldplan.append(n.extract())
    plan.append(oldplan);add(plan,heading('今天选的内容','从学习或练习中加入几项，按自己的节奏完成。')+'<ul id="la-plan-list" class="la-list"></ul><a href="#study">去选择内容 →</a>')
    nav=s.select_one('#workspace-navigation nav');nav.clear()
    for ident,title in [('guide','今天'),('study','学习'),('practice','练习'),('tests','测试'),('workspace','工作区')]:add(nav,f'<button data-go="{ident}" type="button"><span>{title}</span></button>')
    goal=s.select_one('.sidebar-goal');goal.clear();add(goal,'<p>随时继续，也可以只练一题。</p><a href="#plan">今天选的内容 →</a>')
    # Move intact banks so their existing controllers and frozen records stay attached.
    for skill in ['reading','listening','writing1','writing2','speaking']:
        old=s.find(id=skill)
        for bank in old.select(':scope > .case-bank, :scope > .pp-practice'):practice_panels[skill].append(bank.extract())
        for n in old.select(':scope > .pp-entry,:scope > .new-library-entry,:scope > .background-note'):n['class']=n.get('class',[])+['la-hidden-legacy']
        old.insert(0,frag(f'<header class="la-skill-title"><a href="#study">← 学习内容</a><h1>{LABELS[skill]}学习</h1><p>可直接选择下面的讲解，或从原题开始学。</p><a href="#practice-{skill}">只想做题？进入{LABELS[skill]}练习 →</a></header>').find())
        review=s.find(id=skill+'-review');summary=review.find('summary',recursive=False)
        if summary:summary.string='可选：换一道题再试'
        for label in old.select('.learn-stage .field'):
            if any(x in source_text(label.find('span') or label) for x in ['作答后记录','诊断','K 以前','下次']):
                label.wrap(frag('<details class="la-optional"><summary>可选记录</summary></details>').find())
    vocab=s.find(id='vocabulary')
    for n in list(vocab.select(':scope > .enrichment-section,:scope > .usage-grid')):phrases.append(n.extract())
    usage=s.find(id='usage-cards');intro=usage.find_next_sibling('p');phrases.insert(1,usage.extract())
    if intro:phrases.insert(2,intro.extract())
    pp=s.find(id='pp-vocabulary');practice_panels['phrases'].append(pp.extract())
    for n in vocab.select(':scope > .pp-entry,:scope > .new-library-entry,:scope > .background-start'):n['class']=n.get('class',[])+['la-hidden-legacy']
    vocab.insert(0,frag('<header class="la-skill-title"><a href="#study">← 学习内容</a><h1>词汇</h1><a href="#phrases">短语与搭配 →</a></header>').find())
    # Topic content follows what the learner actually does, not the source's old folder.
    destinations={'topic-crime':'reading','topic-government':'reading','topic-society':'reading','topic-space':'listening','topic-environment':'reading','topic-health':'reading','topic-culture':'reading','topic-everyday':'reading'}
    topic_ranges={'topic-crime':range(27,41),'topic-government':range(14,27),'topic-society':range(1,14),'topic-space':range(26,31),'topic-environment':range(1,14),'topic-health':range(27,41),'topic-culture':range(1,14)}
    for ident,skill in destinations.items():
        n=s.find(id=ident);practice_panels[skill].append(n.extract());n['data-la-topic-practice']='true'
        if ident=='topic-culture':
            content=n.select_one('.remediated-teaching');content.clear();add(content,'<p>这份收藏主题与“社会责任”使用同一篇文章、同一组题。<a href="#topic-society">进入 The Davies Sisters 完整阅读练习 →</a></p>');del n['data-la-topic-practice'];continue
        answers=s.new_tag('div',attrs={'class':'la-topic-answers'})
        for q in topic_ranges.get(ident,[1]):add(answers,field('practice-'+ident+'-q'+str(q),f'Q{q}' if ident in topic_ranges else '按原题号写出答案',1 if ident in topic_ranges else 5))
        content=n.select_one('.remediated-teaching')
        if content:content.append(answers)
        else:n.append(answers)
        if ident=='topic-space':
            # Complete original audio is available; transcript is feedback, not the task input.
            n.insert(1,frag('<p>听力流程图 · Q26–30。播放官方完整原音，在 Part 3 对应题段作答；文字稿留到完成后查看。</p>').find())
            n.insert(2,frag('<audio controls preload="none" src="原始参考/precise-official-listening-full.mp3" aria-label="完整听力原音，Part 3 行星生命证据"></audio>').find())
            children=list(content.children);start=next(x for x in children if isinstance(x,Tag) and x.name=='h4' and source_text(x)=='原材料');end=next(x for x in children if isinstance(x,Tag) and x.name=='h4' and source_text(x).startswith('原题'))
            transcript=frag('<details class="la-topic-transcript"><summary>作答后查看文字稿</summary></details>').find()
            for c in children[children.index(start):children.index(end)]:transcript.append(c.extract())
            content.append(transcript)
    # Shared passages are linked, not counted again as a new activity under another topic.
    reuse={'supplement-audit-045':'topic-society','supplement-audit-046':'topic-health','supplement-audit-047':'topic-crime','supplement-audit-048':'topic-government','supplement-audit-134':'topic-crime'}
    for ident,target in reuse.items():
        node=s.find(id=ident)
        if node and not node.select('[data-save],img,audio,source'):
            childids=[n['id'] for n in node.select('[id]')]
            node.clear();add(node,f'<p class="la-topic-reference">同话题的独立阅读题：<a href="#{target}">{E(name(s.find(id=target)))} →</a></p>')
            for x in childids:add(node,f'<span id="{x}"></span>')
    for ident,skill in [('topic-education','writing2'),('topic-work','speaking'),('topic-technology','writing2')]:s.find(id=skill).append(s.find(id=ident).extract())
    s.find(id='speaking').append(s.find(id='topic-personal').extract())
    for n in list(s.select('#background [data-enrichment]')):
        skill='writing2' if n['data-enrichment']=='background_family_children' else 'reading';practice_panels[skill].append(n.extract());n['data-optional']='false'
    for n in s.select('#background > .background-start,#background > .topic-nav,#background > .topic-catalog,#background > .new-library-entry,#background > .pp-entry,#background > #topic-use,#background > #topic-coverage'):
        n['class']=n.get('class',[])+['la-hidden-legacy']
    bg=s.find(id='background');bg.select_one(':scope > .chapter-head').insert(0,frag('<h1>共用背景</h1><p>可供多科使用的知识与材料。具体阅读、写作、听力、口语任务分别进入练习。</p>'))
    # Split the mixed fisheries exercise, keeping all three original field names.
    fisheries=s.find(id='pr-background-fisheries');body=fisheries.select_one('.pp-body');questions=body.select(':scope > .pp-question');key=body.select_one(':scope > .pp-key');keytext=key.find('p').get_text(' ',strip=True)
    write=frag('<details class="pp-unit" id="pr-fisheries-writing"><summary>写作 · 海洋资源：执行捕捞上限</summary><div class="pp-body"></div></details>').find();wb=write.select_one('.pp-body')
    wb.append(questions[1].extract());wb.append(body.select_one('.pp-another').extract());add(wb,'<p>共用材料：<a href="#pr-background-fisheries">捕捞速度与鱼群总量 →</a></p>')
    key.find('p').string='C。设定捕捞上限与确保实际遵守是两件事。'
    newkey=frag('<details class="pp-key"><summary>完成后核对写作示例</summary><p></p></details>').find();newkey.find('p').string=keytext.split('2. 示例：',1)[-1];wb.insert(1,newkey)
    fisheries.find('summary').clear();add(fisheries.find('summary'),'阅读 · 海洋资源：捕捞与鱼群恢复');practice_panels['reading'].append(fisheries.extract());practice_panels['writing2'].append(write)
    oldpp=s.find(id='pp-background');add(oldpp,'<p><a href="#pr-background-fisheries">阅读理解 →</a> · <a href="#pr-fisheries-writing">写作练习 →</a></p>')
    # Turn exposed answer sections in topic practice into proper answer disclosures.
    for parent in s.select('[data-la-topic-practice] .remediated-teaching, .enrichment-unit .remediated-teaching'):
        heads=[h for h in parent.find_all(['h3','h4'],recursive=False) if re.match(r'^(答案|原答案|参考作答|参考答案|核对)',source_text(h))]
        for h in heads:
            if h.parent is not parent:continue
            d=frag('<details class="la-topic-key"><summary>完成后核对答案与解释</summary></details>').find();h.insert_before(d)
            following=list(h.next_siblings);d.append(h.extract())
            for n in following:
                if isinstance(n,Tag) and ('la-topic-answers' in n.get('class',[]) or n.name=='details'):break
                d.append(n.extract())
    # Progress models deliberately exclude stars, notes, revision, reflection and optional retries.
    def register(n,mode,skill,steps=None,title=None,topic=None,description=''):
        if not n:return
        ident=n.get('id')
        if not ident:
            ident='learn-'+n.get('data-enrichment',str(len(units)));n['id']=ident
        if ident in seen:return
        seen.add(ident);n['data-learning-unit']=ident
        if steps is None:
            learned=n.select_one('[data-save^="resource-learned-"], [data-save^="topic-read-"]')
            frozen=n.select_one('[data-case-done], [data-save$="-frozen"]')
            if learned and mode=='study':steps=[{'kind':'check','key':learned['data-save']}]
            elif frozen:steps=[{'kind':'check','key':frozen['data-save']}]
            else:
                fs=[x for x in n.select('[data-save]') if x.name in ['textarea','select'] or x.get('type') not in ['checkbox','hidden']]
                fs=[x for x in fs if not x.find_parent(class_='pp-another') and not re.search(r'(?:-revision|-transfer|-diagnosis|-saved-at|-minutes|-review|-note)$',x['data-save'])]
                if 'pp-unit' in n.get('class',[]):fs=[x for x in n.select('.pp-answer [data-save]') if not x.find_parent(class_='pp-another')]
                steps=[{'kind':'answer','key':x['data-save']} for x in fs]
            if not steps:
                k='learning-read-'+ident;add(n,f'<label class="la-unit-tools"><input type="checkbox" data-save="{k}"> 我已看过本单元</label>');steps=[{'kind':'check','key':k}]
        title=title or name(n);title=re.sub(r'\s*(未作答|待开始).*$', '',title)
        if not topic:
            topic=next((v for pattern,v in [('教育|课堂|小学|学校|学习|Davies','教育与学习'),('就业|工作|岗位|收入|Monika','工作与生活'),('AI|人工智能|科技|算法','科技'),('城市|公交|交通|噪声|住房|居住|地图|silence','城市与交通'),('环境|捕捞|海洋|鱼群|saiga|动物','环境与自然'),('食物|食糖|Sugar|消费|健康','健康与消费'),('家庭|儿童|朋友|人物','家庭与关系'),('旅游|旅行|公园|景点','旅行与地方')] if re.search(pattern,title,re.I)), '通用')
        unit={'id':ident,'mode':mode,'skill':skill,'skillLabel':LABELS[skill],'title':title,'topic':topic,'type':title,'description':description,'steps':steps};units.append(unit)
        box=frag(f'<div data-unit-progress="{ident}" class="la-part-progress"></div>').find()
        if n.name=='details':n.insert(1,box)
        else:n.insert(0,box)
    for skill in ['reading','listening','writing1','writing2','speaking']:
        root=s.find(id=skill)
        for n in root.select('.res-unit,[data-enrichment]'):register(n,'study',skill)
        first=s.find(id=skill+'-first');fs=[n for n in first.select('[data-save]') if re.search(r'-q\d+$|-essay$|-record-note$',n['data-save'])]
        register(first,'study',skill,[{'kind':'answer','key':x['data-save']} for x in fs],title=LABELS[skill]+' · 从原题开始学')
        for n in root.select('.topic-reader,.personal-reader'):register(n,'study',skill)
    for skill,root in practice_panels.items():
        for n in root.select('.pp-unit,.exam-case,[data-enrichment],[data-la-topic-practice]'):register(n,'practice',skill)
    for n in s.select('#background > .topic-reader,#background .authentic-background'):register(n,'study','shared',title='阅读材料中的话题背景' if 'authentic-background' in n.get('class',[]) else None)
    for n in s.select('#phrases [data-enrichment],#phrases .usage-card'):register(n,'study','phrases')
    for n in s.select('#vocabulary .word-card'):register(n,'study','vocabulary')
    tv=s.find(id='topical-vocabulary');register(tv,'study','vocabulary',[{'kind':'answer','key':x['data-save']} for x in tv.select('[data-save^="topic-vocab-level-"]')],title='按话题选词汇',description='1000 个词条；进度只表示已标记熟悉度的比例。');units[-1]['progressLabel']='已标记'
    # All answer disclosures get a local answer prerequisite, never a module-wide checklist.
    for d in list(s.select('.pp-key,.prereq-key,.prereq-transcript,.prereq-speaking-source,.la-topic-key,.la-topic-transcript')):
        scope=d.find_parent(class_='pp-another') or d.find_parent(class_='pp-unit') or d.find_parent(class_='prereq-lesson') or d.find_parent(class_='enrichment-unit') or d.find_parent(attrs={'data-la-topic-practice':True}) or d.find_parent(class_='authentic-supplement')
        if not scope:continue
        if 'prereq-lesson' in scope.get('class',[]):
            # Each small task unlocks its own feedback; later tasks are independent.
            prior=d.find_previous(['textarea','input']);fs=[prior] if prior and prior.get('data-save') and prior in scope.descendants else []
        elif scope.get('data-enrichment'):fs=[scope.select_one(f'[data-save="enrich-{scope["data-enrichment"]}-answer"]')]
        else:fs=[x for x in scope.select('textarea[data-save],input[data-save]') if x.get('type') not in ['checkbox','hidden'] and (scope.get('class')==['pp-another'] or not x.find_parent(class_='pp-another')) and not re.search(r'(?:-note|-revision|-saved-at|-another)$',x['data-save'])]
        if 'pp-unit' in scope.get('class',[]):fs=[x for x in scope.select('.pp-answer [data-save]') if not x.find_parent(class_='pp-another')]
        if 'pp-another' in scope.get('class',[]):fs=scope.select('textarea[data-save]')
        fs=[x for x in fs if x]
        if not fs:continue
        gates+=1;d['id']=d.get('id') or 'answer-check-'+str(gates);d['data-answer-gate']=json.dumps([x['data-save'] for x in fs],ensure_ascii=False);d.attrs.pop('open',None)
        wrapper=frag('<div class="la-gate-content" hidden></div>').find()
        for n in list(d.contents):
            if not(isinstance(n,Tag) and n.name=='summary'):wrapper.append(n.extract())
        d.append(wrapper)
    # Explicit "don't know" is valid effort; a blank answer is not.
    keys={k for d in s.select('[data-answer-gate]') for k in json.loads(d['data-answer-gate'])}
    for n in s.select('textarea[data-save],input[data-save]'):
        if n['data-save'] in keys and not n.find_parent(class_='la-gate-content') and not re.search(r'prereq-listening-.*-note',n['data-save']):
            n.insert_after(frag(f'<button type="button" class="la-unknown" data-la-unknown="{E(n["data-save"])}">暂时不会</button>').find())
    # Topic/skill filters index real activities; they do not duplicate any lesson content.
    for mode,root in [('study',study),('practice',practice)]:
        topicnames=sorted({u['topic'] for u in units if u['mode']==mode})
        skilloptions=''.join(f'<option value="{k}">{v}</option>' for k,v in LABELS.items() if any(u['mode']==mode and u['skill']==k for u in units))
        add(root,f'<div id="la-{mode}-progress"></div><div class="la-toolbar"><label>科目<select id="la-{mode}-skill"><option value="">全部</option>{skilloptions}</select></label><label>话题<select id="la-{mode}-topic"><option value="">全部</option>'+''.join(f'<option>{E(t)}</option>' for t in topicnames)+f'</select></label><label>内容或题型<input id="la-{mode}-search" type="search" placeholder="例如：判断题、教育、短语"></label><span id="la-{mode}-count" role="status"></span></div><div id="la-{mode}-cards" class="la-grid"></div>')
    add(study,'<div class="la-links"><a href="#vocabulary">词汇</a><a href="#phrases">短语</a><a href="#background">共用背景</a><a href="#course-window">我的学习项目与资料</a></div>')
    projects=[{'id':'reading-evidence','title':'阅读：把判断的依据找清楚','units':['reading-tech-judgement','pr-reading-davies-statements','reading-first']},{'id':'education-writing','title':'写作：教育话题到理由段','units':['topic-education','pr-writing2-primary']},{'id':'listening-form','title':'听力：表单与选择题','units':['listening-first','pr-listening-p1','pr-listening-p2'] }]
    projects=[{**p,'units':[x for x in p['units'] if x in seen]} for p in projects]
    projectsection=frag('<section><h2>想按顺序学，可以从这一组开始</h2><p>顺序是建议；可以跳到你需要的那一项。</p><div class="la-grid"></div></section>').find()
    for p in projects:
        card=f'<article class="la-card la-project" data-project="{p["id"]}"><h3>{p["title"]}</h3><div data-project-progress></div><ol>'+''.join(f'<li><a href="#{x}">{E(next(u["title"] for u in units if u["id"]==x))}</a></li>' for x in p['units'])+'</ol></article>';add(projectsection.select_one('.la-grid'),card)
    guide.append(projectsection)
    for root in [*practice_panels.values(),*[s.find(id=k) for k in ['reading','listening','writing1','writing2','speaking','vocabulary','phrases','background']]]:
        ids=[u['id'] for u in units if s.find(id=u['id']).find_parent(id=root['id'])]
        root.insert(1,frag(f'<div data-collection-progress="{E(json.dumps(ids))}" class="la-part-progress"></div>').find())
    for target,title,desc in [('writing-workbench','写作工作台','接着写、保存原稿与修改稿。'),('records','记录与备份','作答记录、词句积累和导出恢复。'),('course-window','我的学习项目','继续已有课程，或整理自己的材料。'),('materials','我的资料','加入、查找和阅读课外材料。'),('library','原始资料','查找原题、图表、音频与文件。'),('plan','今天选的内容','只安排你今天想做的几项。')]:
        add(workspace,f'<article class="la-card"><h2>{title}</h2><p>{desc}</p><a href="#{target}">打开 →</a></article>')
    testdata=build_tests();add(s.main,(OUT/'complete-tests.html').read_text(encoding='utf8'))
    add(tests,'<article class="la-card"><h2>四科完整组合练习</h2><p>听力 → 阅读 → 写作，口语可另行完成。组合采用已收集的公开样题与 Cambridge 21 材料；不是同一套官方整卷。听力暂不生成整科分数。</p><div id="la-mock-progress"></div><button type="button" id="la-start-mock" class="la-primary">开始四科组合练习</button></article><div class="la-grid">'+''.join(f'<article class="la-card"><h2>{m["label"]}整科</h2><p>{m["scope"]}</p><p>{m["note"]}</p><a href="#test-{k}">进入 →</a></article>' for k,m in testdata.items())+'</div>')
    # Narrow changes to core code: route by actual DOM ownership and require a real first attempt.
    scripts=s.find_all('script');core=scripts[0].string
    core=core.replace("if(h.startsWith('topic-'))id='background';if(h.startsWith('usage-')||h==='core-words')id='vocabulary';for(const c of ['writing1','writing2','listening','speaking','reading'])if(h.startsWith(c+'-'))id=c;",'')
    core=core.replace('!answerKeys.some(k=>String(fields[k]).trim())','!answerKeys.length||!answerKeys.every(k=>String(fields[k]).trim())').replace('先留下答案或录音文件记录，再保存首次作答。','先完成各题的作答；不会的题可写“暂时不会”，再核对。')
    scripts[0].string=core
    scripts[1].string=scripts[1].string.replace("&&!optional"," ").replace("&&el.dataset.optional!=='true'",'')
    ui=scripts[2].string
    ui=re.sub(r'function backgroundView\(hash\)\{.*?\n \}\n let vocabFilter',"function backgroundView(hash){}\n let vocabFilter",ui,flags=re.S)
    ui=ui.replace("if(hash.startsWith('topic-'))pageId='background';if(hash.startsWith('usage-')||hash==='core-words')pageId='vocabulary';for(const c of chapters)if(hash.startsWith(c+'-'))pageId=c;",'')
    ui=ui.replace("backgroundView(hash);if(pageId", "backgroundView(hash);if(pageId==='phrases'){vocabFilter='usage';$('#vocab-search').value='';filterVocabulary();}if(pageId")
    scripts[2].string=ui
    # Keep imported five-stage packages compatible, but remove stage/time bureaucracy from display.
    cw=s.find(id='course-window-script');text=cw.string
    a=text.index("    const budgetControl =");b=text.index("    const stages =",a)
    text=text[:a]+"    const tasks = c.stages.filter(s => s.id !== 'delayed').flatMap(s => s.tasks); const done = tasks.filter(t => state.attempts.some(a => a.courseId === c.id && a.taskId === t.id)).length;\n    header.append(el('p', Math.round(done/tasks.length*100) + '% · ' + done + ' / ' + tasks.length + ' 项已作答；自评与加练可选。', 'cw-muted')); workspace.append(header);\n"+text[b:]
    text=text.replace("const reveal = button('先看参考（会记录看过答案）', () => { recordExposure(c, t, 'reference'); if (!card.querySelector('.cw-reference')) appendReference(card, t); reveal.disabled = true; }); reveal.dataset.cwReveal = t.id; reveal.disabled = draft.revealed;", "const reveal = el('span','先提交自己的答案，再核对。','cw-muted');")
    text=text.replace("if (draft.revealed) appendReference(card, t);",'')
    text=text.replace("请对照下方参考与标准，给这次表现一个自评。","可对照参考检查；自评可留空。")
    text=text.replace("assessment.append(el('span', '这次表现：'))","assessment.append(el('span', '可选：这次表现'))")
    text=text.replace("'当前阶段 ' + (PHASES.indexOf(stage.id) + 1) + ' / 5 · 设计用时约 ' + stage.minutes + ' 分钟'","'本节约 ' + stage.minutes + ' 分钟'")
    text=text.replace("'学习阶段'","'本课内容'").replace("'下一阶段／先跳过 →'","'下一节 →'").replace("'← 上一阶段'","'← 上一节'")
    text=text.replace("'先保存一批原料，或选择示例体验分阶段学习。'","'选择已有学习项目即可开始；也可以整理自己的材料。'")
    text=text.replace("['先试一次', '理解与辨析', '带支架练习', '独立迁移', '隔日再用']","['先做一题', '理解用法', '练习', '换个情境', '可选加练']")
    cw.string=text
    data={'version':1,'units':units,'projects':projects,'tests':testdata,'skills':LABELS}
    add(s.main,'<input type="hidden" id="learning-adjust-state" data-save="learning-adjust-state"><p id="la-notice" role="status" aria-live="polite" class="la-notice" hidden></p>')
    st=s.new_tag('style',id='learning-adjust-style');st.string=(ROOT/'learning-adjust.css').read_text(encoding='utf8');s.head.append(st)
    j=s.new_tag('script',id='learning-adjust-data',type='application/json');j.string=json.dumps(data,ensure_ascii=False).replace('</','<\\/');s.body.append(j)
    for filename in ['learning-adjust-model.js','learning-adjust.js']:
        j=s.new_tag('script',id=filename.replace('.js','-script'));j.string=(ROOT/filename).read_text(encoding='utf8');s.body.append(j)
    output=str(s).encode('utf8');(OUT/'开始学习-adjusted.html').write_bytes(output)
    fields=Counter(n['data-save'] for n in s.select('[data-save]'));ids=[n['id'] for n in s.select('[id]')]
    missingfields=original_fields-fields;missingids=sorted(original_ids-set(ids));missingmedia=original_media-Counter((n.name,n.get('src')) for n in s.select('img,audio,source') if n.get('src'))
    assert not missingfields,missingfields
    assert not missingids,missingids
    assert not missingmedia,missingmedia
    assert all(v==1 for v in fields.values()),'Duplicate save keys'
    assert len(ids)==len(set(ids)),'Duplicate IDs'
    report={'backup':str(BACKUP),'inputSHA256':sha(raw),'outputSHA256':sha(output),'oldFields':sum(original_fields.values()),'fields':sum(fields.values()),'preservedFields':sum(original_fields.values()),'units':len(units),'answerGates':gates,'missingIds':missingids,'missingMedia':list(missingmedia),'staged':str(OUT/'开始学习-adjusted.html'),'applied':False}
    (OUT/'learning-adjust-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report,live

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    if args.write:
        raise SystemExit('Publication blocked: the 2026-09-20 audit found unresolved answer-gate, progress and save-failure defects. The navigation-v2 candidate is separate and not included in this older builder. Fix and re-review the current candidate before enabling publication.')
    report,live=adjust()
    if args.write:
        # QA is generated from the exact staged bytes; never accept stale verification.
        import qa_learning_adjust
        qa_learning_adjust.run()
        assert MAIN.read_bytes()==live,'Concurrent live edit'
        (BOOK/'learning-assets').mkdir(exist_ok=True)
        for p in (OUT/'learning-assets').iterdir():shutil.copy2(p,BOOK/'learning-assets'/p.name)
        MAIN.write_bytes((OUT/'开始学习-adjusted.html').read_bytes());report['applied']=True
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
