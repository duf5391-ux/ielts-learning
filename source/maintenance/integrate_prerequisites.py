"""Apply content fixes first; verify, then remove audit/production prose from the learner page.

Run after integrate_learning_upgrade.py. Does not rebuild the book or access browser data.
"""
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from collections import Counter
from html import escape as E
from datetime import datetime
import argparse, hashlib, json, re, shutil
import prerequisite_content as content

ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
OUT=Path('D:/IELTS-Work/content-repair-20260920')
MAIN=BOOK/'开始学习.html'

def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode('utf8')).hexdigest()
def fragment(html):return BeautifulSoup(html,'html.parser')
def add(node,html):
    for el in list(fragment(html).contents):node.append(el)

def put_before(node,html):
    for el in list(fragment(html).contents):node.insert_before(el)

def recorder(uid):
    return f'''<div class="recorder" data-recorder="{uid}"><button type="button" data-record="{uid}">开始录音</button><button type="button" data-stop="{uid}" disabled>结束录音</button><a data-download="{uid}" hidden>下载录音</a><audio controls data-preview="{uid}" hidden></audio><label>载入录音 <input type="file" accept="audio/*" data-upload="{uid}"></label><p class="small" data-rec-status="{uid}">两遍录音分别下载保存；文字备份不含音频。</p></div><label class="field"><span>录音文件名</span><input type="text" data-save="{uid}-record-note"></label>'''

LISTENING={
 21:('d88d54dd-recording-1.mp3','Recording 1 · 运输表单 · Q1–8',list(range(1,9))),
 22:('c31e6351-recording-2.mp3','Recording 2 · 运输保险 · Q9–10',[9,10]),
 23:('precise-recording-3.mp3','Recording 3 · 海外学生社交活动 · Q11–16',list(range(11,17))),
 24:('bb61bf2b-recording-4.mp3','Recording 4 · 开放大学 · Q27–30',list(range(27,31)))
}

COURSE_COPY={
 '你给资料，我设计贴合考试的讲解与练习':'用自己的资料安排学习',
 '双向拟合 = 你的材料 ↔ 雅思考试。我会按相关真题、官方样例和有评分依据的作答选材，说明这批资料适合怎样用于目标题型，再从考试任务反查材料和练习是否贴合。重点是来源与设计的考试拟合度，不以一批资料保证覆盖整个考试。':'课程围绕具体学习目标安排讲解、练习与反馈。进入课程后，先了解本次任务和适用范围，再按阶段作答、核对与复习。',
 '可以直接在当前对话发材料，我设计后放回这里。这个窗口按阶段学习；作答记录用于另外调整支架和下一步。下方保存、导出和导入是可选的整理与备份工具。':'这里可以保存材料和学习目标，并导入整理好的课程；保存材料不会自动生成课程。已有课程与作答记录可单独导出备份。',
 '双向拟合表：材料 ↔ 雅思考试（含原料提示）':'本课材料与练习目标'
}

def course_copy(script):
    for old,new in COURSE_COPY.items():script=script.replace(old,new)
    return script

def repair_listening(s):
    for no,(filename,label,questions) in LISTENING.items():
        unit=s.find(id=f'supplement-audit-{no:03}')
        assert unit is not None
        if unit.get('data-prerequisite')=='listening-v1':continue
        assert (BOOK/'原始参考'/filename).is_file(),filename
        children=list(unit.contents)
        headings=[n for n in children if isinstance(n,Tag) and n.name=='h4']
        question=next(n for n in headings if n.get_text(strip=True)=='原题')
        key=next(n for n in headings if n.get_text(strip=True)=='原答案')
        transcript=next(n for n in headings if n.get_text(strip=True).startswith('原材料'))
        a,b,c=(children.index(x) for x in (transcript,question,key))
        assert a<b<c
        title=headings[0].get_text(strip=True)
        unit.clear();unit['data-prerequisite']='listening-v1';unit['class']=list(set(unit.get('class',[])+['prereq-listening']))
        add(unit,f'<h4>{E(title)}</h4><p>本题使用 {E(label)}。先读题并播放下面的原音；原稿与答案可在作答后分别展开。上方课堂音频是另一份材料。</p><audio controls preload="none" src="原始参考/{filename}" aria-label="{E(label)}"></audio>')
        for n in children[b:c]:unit.append(n)
        for q in questions:add(unit,content.field(f'listening-{no}-q{q}',f'Q{q}',1))
        add(unit,content.field(f'listening-{no}-note','听后记录：不确定的题号／已重听或查稿',2))
        tapescript=s.new_tag('details',attrs={'class':'prereq-transcript'});add(tapescript,'<summary>作答后查看文字稿</summary>')
        for n in children[a:b]:tapescript.append(n)
        unit.append(tapescript)
        answers=s.new_tag('details',attrs={'class':'prereq-key'});add(answers,'<summary>核对答案与解释</summary>')
        for n in children[c:]:answers.append(n)
        unit.append(answers)

def repair_speaking(s):
    for uid,data in content.SPEAKING.items():
        unit=s.select_one(f'[data-enrichment="{uid}"]');assert unit is not None
        if unit.get('data-prerequisite')=='speaking-v1':continue
        body=unit.select_one('.enrichment-body');source=body.select_one('.remediated-teaching')
        attempt=body.select_one('.enrichment-attempt');feedback=body.select_one('.enrichment-feedback')
        put_before(source,content.block(uid,data['title'],f'<p>{E(data["task"])}</p><p class="english">{E(data["prompt"])}</p><h4>第一遍：用自己的内容回答</h4>'+recorder('prereq-'+uid+'-first')))
        source.wrap(fragment('<details class="prereq-speaking-source"></details>').find())
        source.parent.insert(0,fragment('<summary>说完后查看正式题页与考生转写</summary>').find())
        attempt.find('h3').string='保留第一遍的观察'
        attempt.find('p').string='先回听自己的录音，记下文件名和一处需要修改的时间点。下载第一遍声音，再保留下面的文字记录。'
        attempt.select_one('.field span').string='第一遍录音文件名／时间点／我听到的问题'
        feedback.find('h3').string='只修一处，再录一遍'
        feedback.find('p').string=data['check']
        for n in fragment('<p>'+E(data['example'])+'</p><h4>第二遍：同一问，改进一处</h4>'+recorder('prereq-'+uid+'-retry')).contents[:]:feedback.find('label').insert_before(n)
        revision=feedback.select_one(f'[data-save="enrich-{uid}-revision"]')
        revision.find_parent('label').find('span').string='两遍相比：这一处是否更清楚？'
        transfer=feedback.select_one(f'[data-save="enrich-{uid}-transfer"]')
        transfer.find_parent('label').insert_before(fragment('<p>'+E(data['next'])+'</p>').find())
        unit['data-prerequisite']='speaking-v1'

def repair_background(s):
    for key,html in [('education',content.EDUCATION),('work',content.WORK),('technology',content.TECHNOLOGY)]:
        node=s.find(id='topic-'+key);assert node is not None
        prior=node.find(id='prereq-'+key)
        if prior:prior.replace_with(fragment(html).find());continue
        supplement=node.select_one('.authentic-supplement');put_before(supplement,html)
        # Keep the original full source/answers available as a separately named extension.
        if key in ['education','work']:
            wrapper=fragment('<details class="prereq-extension"></details>').find();supplement.wrap(wrapper)
            title={'education':'延伸阅读：Davies 姐妹的教育与收藏','work':'延伸阅读：制糖业中的历史劳工'}[key]
            wrapper.insert(0,fragment('<summary>'+title+'</summary>').find())
            first=supplement.find('p',recursive=False)
            if first:first.string={'education':'这份阅读练习讨论人物教育与收藏经历，可另行学习；前面的课堂任务练习教育机会、技能与学习支持。','work':'这份阅读练习讨论制糖业的历史与劳工。现代岗位安排的理解练习见上方。'}[key]
        if key=='education':
            for old in node.select('.deep-audit-entry'):
                if '课程与学习方式' in old.get_text():old.decompose()
    for target,html,anchor in [('usage-05',content.AS_RESULT,'prereq-as-result'),('topical-vocabulary',content.VOCABULARY,'prereq-vocabulary-usage')]:
        node=s.find(id=target);assert node is not None
        prior=node.find(id=anchor)
        if prior:prior.replace_with(fragment(html).find());continue
        before=node.select_one('.authentic-supplement') if target=='usage-05' else node.select_one('.tv-controls')
        put_before(before,html)
    vocabulary=s.find(id='topical-vocabulary')
    vocabulary.select_one('.tv-scope').string='本表按主题词典、词汇课和公开词表整理。中文义项与短搭配为教学编写；词形在原文中出现，不代表本表每个义项和搭配都出现在同一来源。需要语境时，可从“词频与原文”回查；实际用词练习见下方。'
    for card in vocabulary.select('.tv-card'):
        if card.select_one('[data-prereq-word]'):continue
        term=card.select_one('[data-local-dictionary]')['data-local-dictionary']
        meaning=card.select_one('.tv-meaning').get_text(' ',strip=True)
        add(card.find('footer'),f'<a href="#prereq-vocabulary-usage" data-prereq-word="{E(term,quote=True)}" data-prereq-meaning="{E(meaning,quote=True)}">用这个词造句</a>')
    add(s.find(id='prereq-vocabulary-usage'),'<p id="prereq-vocab-status" role="status" aria-live="polite"></p>')
    for ident in ['reading-case-rd-official-miles-1','reading-case-rd-c21-dreams-2']:
        node=s.find(id=ident)
        if node and not node.select_one('.prereq-exposure'):
            body=node.select_one('.case-body') or node
            p=s.new_tag('p',attrs={'class':'prereq-exposure small'})
            p.string='本材料也用于本册教学。已看过原文、示范或答案时，这次作答用于练习与复习，不作为未见题测试。'
            body.insert(0,p)

def integrate_energy(s):
    # Static record field precedes the original core restore() call.
    host=s.find(id='energy-control')
    if host:host.replace_with(fragment((ROOT/'energy-control.html').read_text(encoding='utf8')).find())
    else:s.main.insert(0,fragment((ROOT/'energy-control.html').read_text(encoding='utf8')).find())
    style=s.find(id='energy-control-style')
    if not style:style=s.new_tag('style',id='energy-control-style');s.head.append(style)
    style.string=(ROOT/'energy-control.css').read_text(encoding='utf8')
    for name in ['energy-control-model','energy-control','prerequisite-interactions']:
        el=s.find(id=name+'-script')
        if not el:el=s.new_tag('script',id=name+'-script');s.body.append(el)
        el.string=(ROOT/(name+'.js')).read_text(encoding='utf8')

AUDIT='[data-content-audit], [data-learning-audit], [data-deep-audit-ui], .learning-audit-note, .learning-audit-summary, .deep-audit-summary, .deep-audit-entry'
def clean(s):
    removed=[]
    for n in list(s.select(AUDIT)):
        if n.parent is None:continue
        # Some old audit entries contain useful official task links: retain them as source notes.
        if 'deep-audit-entry' in n.get('class',[]) and n.find('a',href=re.compile(r'原始参考/|https://ielts.org')):
            n['class']=['source-note']
            n.attrs.pop('data-deep-audit-ui',None)
            for p in n.find_all('p'):
                if '原单元错位结论' in p.get_text():p.string=p.get_text().split('此对照入口')[0]
            continue
        assert not n.select('[data-save]'), 'Audit wrapper unexpectedly contains learning records'
        removed.append(n.get_text(' ',strip=True)[:180])
        # Retain old anchors, so existing bookmarks keep resolving without displaying audit prose.
        for a in n.find_all(id=True):
            if not s.find(id=a['id']) is a:continue
            n.insert_before(s.new_tag('span',id=a['id']))
        if n.get('id'):n.replace_with(s.new_tag('span',id=n['id']))
        else:n.decompose()
    for a in list(s.select('a[href]')):
        if any(x in a['href'] for x in ['学习架构审查台','内容审核','词条逐项审核','教学审查','审核证据']):
            a.decompose()
    # Remove producer-only instructions, without deleting actual tasks, examples or source notes.
    replacements={
      '此对照入口用于后续重建，原单元错位结论仍保留。':'',
      '本补充保留已有复习记录及原可疑示范':'本次补充可以配合原有复习记录使用',
      '保留原摘读的待核标记；补充下面两页完整真题文章语境与具体导读答案':'下面提供完整阅读语境与导读答案',
      '教师编写，非原考试题号':'导读问题',
      '教师编写的理解检查，不冒充原考试题号':'导读问题',
      '以下原文与题号构成独立补充，原导读保留其待核状态。':'下面可以对照完整原文和对应题目学习。',
    }
    for text in list(s.main.find_all(string=True)):
        if text.parent.name in ['script','style']:continue
        value=str(text)
        for old,new in replacements.items():value=value.replace(old,new)
        if value!=str(text):text.replace_with(value)
    # Replace an obsolete production instruction with the actual completed task.
    for p in s.main.find_all('p'):
        if '优先接IELTS官方Monika' in p.get_text():p.string='工作与休闲的具体讨论见本单元的 Monika 样本任务。'
    for script in s.select('script'):
        old=script.get_text();new=course_copy(old)
        if new!=old:script.string=new
    return removed

def inventory(s):
    return {'fields':[n['data-save'] for n in s.select('[data-save]')],
      'ids':[n['id'] for n in s.select('[id]')],
      'media':Counter((n.name,n.get('src',''),n.get('data-preview','')) for n in s.select('img,audio,source,video')),
      'core':next(n.get_text() for n in s.select('script') if 'RECORD-SAFETY-20260919' in n.get_text()),
      'scripts':{n.get('id') or 'original-'+str(i):n.get_text() for i,n in enumerate(s.select('script'))}}

def review(s):
    checks=[]
    def ok(label,value):
        assert value,label
        checks.append({'check':label,'result':'pass'})
    for no,(_,label,qs) in LISTENING.items():
        u=s.find(id=f'supplement-audit-{no:03}')
        ok(label+'：本地同源音频',len(u.select('audio[src]'))==1 and (BOOK/u.select_one('audio')['src']).exists())
        ok(label+'：独立答题记录',len(u.select('textarea'))==len(qs)+1)
        for cls in ['prereq-transcript','prereq-key']:
            detail=u.select_one('details.'+cls);ok(label+'：'+cls+'默认折叠',detail is not None and not detail.has_attr('open'))
        ok(label+'：稿件与题目分开',not u.select_one('.prereq-transcript').select('textarea'))
    for uid in content.SPEAKING:
        u=s.select_one(f'[data-enrichment="{uid}"]')
        ok(uid+'：两遍录音分别保存',len(u.select('[data-record]'))==2 and len({n['data-record'] for n in u.select('[data-record]')})==2)
        ok(uid+'：原记录保留',all(u.select_one(f'[data-save="enrich-{uid}-{key}"]') for key in ['answer','frozen','saved-at','revision','transfer','diagnosis']))
        ok(uid+'：考生转写默认折叠',not u.select_one('.prereq-speaking-source').has_attr('open'))
    for key in ['education','work','technology','as-result','vocabulary-usage']:
        u=s.find(id='prereq-'+key)
        ok(key+'：具体任务、作答与反馈齐全',u is not None and bool(u.select('textarea')) and bool(u.select('details')))
    ok('写作工作台保留',s.find(id='writing-workbench') is not None)
    ok('单词本与句子本保留',s.find(id='vocabulary-review') is not None and s.find(id='sentence-learning') is not None)
    ok('休息记录在核心恢复前',str(s).index('data-save="energy-control-state"')<str(s).index('RECORD-SAFETY-20260919'))
    return checks

def apply(page,cleanup=True):
    s=fragment(page)
    repair_listening(s);repair_speaking(s);repair_background(s);integrate_energy(s)
    checks=review(s)  # Content validation MUST precede cleanup.
    removed=clean(s) if cleanup else []
    return str(s),checks,removed

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    before=MAIN.read_text(encoding='utf8');a=inventory(fragment(before))
    after,checks,removed=apply(before);b=inventory(fragment(after))
    assert set(a['fields'])<=set(b['fields']),'Existing record removed'
    assert len(b['fields'])==len(set(b['fields'])),'Duplicate saved field'
    assert len(b['ids'])==len(set(b['ids'])),'Duplicate id'
    assert not a['media']-b['media'],'Existing media removed'
    assert a['core']==b['core'],'Core changed'
    # All existing inline code is kept byte-for-byte (original recording, restore, dictionary, writing).
    for key,value in a['scripts'].items():
        if key in ['energy-control-script','energy-control-model-script']:continue
        assert course_copy(value) in b['scripts'].values(),f'Script logic changed: {key}'
    again,_,_=apply(after)
    assert again==after,'Not idempotent'
    (OUT/'开始学习-reviewed.html').write_text(after,encoding='utf8')
    report={'date':datetime.now().isoformat(),'phase':'written' if args.write else 'staged','beforeSHA256':sha(before),'afterSHA256':sha(after),'savedFieldsBefore':len(a['fields']),'savedFieldsAfter':len(b['fields']),'existingMediaPreserved':sum(a['media'].values()),'coreScriptPreserved':True,'otherScriptChanges':'Four display strings only in course window; existing logic preserved','idempotent':True,'checks':checks,'removedAuditBlocks':len(removed),'uiScope':'Existing workspace and navigation preserved; no test-entry redesign','browserVerification':'Not performed: local learner page blocked by browser policy','backup':'D:/IELTS-Backups/2026-09-20_010406-before-content-repair'}
    if args.write and before!=after:
        backup=OUT/('pre-write-'+datetime.now().strftime('%H%M%S')+'.html');backup.write_text(before,encoding='utf8')
        temp=MAIN.with_suffix('.prereq.tmp');temp.write_text(after,encoding='utf8')
        assert temp.read_text(encoding='utf8')==after
        assert MAIN.read_text(encoding='utf8')==before,'Concurrent edit detected'
        temp.replace(MAIN)
    (ROOT/'research/prerequisite-repair-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'removed-audit-prose.json').write_text(json.dumps(removed,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf8');main()
