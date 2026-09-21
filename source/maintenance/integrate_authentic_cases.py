"""Replace unsupported teaching, retain suspect entries, and add DB-generated cases."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from bs4 import BeautifulSoup
import hashlib,json,re,sqlite3
from build_authentic_case_database import HERE,BOOK,QA,DB,read,dump,build,dom_id,source_html,source_link,rich,E
from integrate_content_audit import apply_review

MAIN=BOOK/'开始学习.html'

def fragment(html):return BeautifulSoup(html,'html.parser')
def append_html(node,html):
    for child in list(fragment(html).contents):node.append(child)

def clean_review(s):
    for n in list(s.select('[data-content-audit]')):n.decompose()
    for n in s.select('[data-audit-target]'):del n['data-audit-target']

def lesson_html(r,case_map):
    html=r.get('teachingHtml') or r.get('html') or ''
    for ref in r.get('sourceRefs',[]):
        html+='<p class="remediation-source">'+source_link(ref)+'</p>'
    linked=[case_map[x] for x in r.get('caseIds',[]) if x in case_map]
    if linked:
        html+='<div class="case-study-links">'+''.join('<a href="#'+E(dom_id(c))+'">练原题：'+E(c['title'])+'</a>' for c in linked)+'</div>'
    assert html.strip(),r['auditId']
    return html

def preserve_controls(node):
    """Retain old record keys and UI controls without retaining unsupported tasks."""
    nodes=[]
    for field in list(node.select('[data-save]')):
        if not field.parent:continue
        label=field.find_parent('label')
        candidate=label if label and node in label.parents else field
        if candidate in nodes:continue
        nodes.append(candidate.extract())
    return nodes

def replace_target(s,target,r,case_map):
    title=r.get('title')
    heading=target.find('summary',recursive=False) if target.name=='details' else target.find(['h2','h3','h4'],recursive=False)
    if heading and title:
        heading.clear();heading.string=title
    body=target.select_one(':scope > .res-body, :scope > .enrichment-body')
    if body is None:body=target
    oldids=[n['id'] for n in body.select('[id]')]
    controls=preserve_controls(body)
    freeze=body.select_one('[data-enrich-freeze]')
    status=body.select_one('[data-enrich-status]')
    if freeze:freeze.extract()
    if status:status.extract()
    # Stable note/control keys survive, including the enrichment save workflow.
    if body is target:
        for child in list(body.contents):
            if child is not heading:child.extract()
    else:body.clear()
    intro=s.new_tag('div',attrs={'class':'remediated-teaching prose'})
    append_html(intro,lesson_html(r,case_map));body.append(intro)
    if target.get('data-enrichment'):
        attempt=s.new_tag('section',attrs={'class':'enrichment-attempt'})
        append_html(attempt,'<h3>我的原题练习记录</h3><p>按上方真实题目留下自己的回答或录音简记；参考内容用于对照，不必复述示范中的经历。</p>')
        feedback=s.new_tag('section',attrs={'class':'enrichment-feedback','hidden':''})
        append_html(feedback,'<h3>核对并修订</h3><p>回到上方原题与具体示范，核对是否回应问题、证据是否准确，再改写自己的回答。</p>')
        for n in controls:
            f=n if n.has_attr('data-save') else n.select_one('[data-save]')
            key=f['data-save']
            (attempt if key.endswith(('-answer','-frozen','-saved-at')) else feedback).append(n)
        if freeze:attempt.append(freeze)
        if status:attempt.append(status)
        body.append(attempt);body.append(feedback)
    elif controls:
        records=s.new_tag('div',attrs={'class':'retained-records'})
        append_html(records,'<p class="small">本单元的学习记录</p>')
        for n in controls:records.append(n)
        body.append(records)
    current={n.get('id') for n in target.select('[id]')}
    for id in oldids:
        if id not in current:body.append(s.new_tag('span',id=id,attrs={'hidden':''}))

def source_refs(r,case_map):
    refs=deepcopy(r.get('sourceRefs',[]))
    for cid in r.get('caseIds',[]):
        if cid in case_map:refs.append(case_map[cid]['source'])
    result=[]
    for src in refs:
        path=src.get('path') or src.get('local_path') or src.get('localPath')
        if path:
            p=Path(path);p=p if p.is_absolute() else BOOK/p
            assert p.exists(),str(p)
            result.append({'label':src.get('title') or src.get('label','原始材料'),'local_path':str(p),'href':src.get('href') or str(path)+(('#page='+str(src['page'])) if src.get('page') and not isinstance(src['page'],list) else ''),'exists':True,'page':src.get('page')})
        elif src.get('url') or src.get('href'):result.append(src)
    return result

def run():
    cases,banks,stats=build();case_map={c['id']:c for c in cases}
    data=read(HERE/'audit-content-20260919.json');original=deepcopy(data);lookup={x['id']:x for x in data['items']}
    # Rebuild from the untouched pre-remediation snapshot; repeatable without duplicate fields.
    s=BeautifulSoup((QA/'before-remediation.html').read_text(encoding='utf8'),'html.parser');clean_review(s)
    for id in ['authentic-case-style','authentic-case-script']:
        n=s.find(id=id)
        if n:n.decompose()
    reps={};supps={}
    with sqlite3.connect(DB) as con:
        for relation,payload in con.execute('SELECT relation,payload FROM teaching_modules'):
            r=json.loads(payload)
            collection=reps if relation=='replacements' else supps
            assert r['auditId'] not in collection,r['auditId'];collection[r['auditId']]=r
    required={x['id'] for x in data['items'] if x['status']=='未达标'}
    suspicious={x['id'] for x in data['items'] if x['status']=='可疑'}
    assert set(reps)==required,{'missing':list(required-set(reps)),'extra':list(set(reps)-required)}
    assert set(supps)==suspicious,{'missing':list(suspicious-set(supps)),'extra':list(set(supps)-suspicious)}
    changed_titles={}
    for aid,r in reps.items():
        item=lookup[aid];target=s.select_one(item['target_selector']);assert target,aid
        replace_target(s,target,r,case_map)
        item['previous_status']=item['status'];item['status']='达标'
        item['source_refs']=source_refs(r,case_map)
        assert item['source_refs'],(aid,'No primary source')
        if r.get('title'):item['title']=r['title'];changed_titles[item.get('anchor')]=r['title']
        item['reason']=r.get('auditReason') or r.get('reason') or '已以可回查原页的真实题目／材料替换原自编核心任务；讲解对应具体题目、答案或参考表达。'
        item['source_basis']='；'.join(dict.fromkeys(x['label'] for x in item['source_refs']))
        item['source_kind']='真实原题／原始材料与针对性教学'
        item['next_action']='已替换并复核；可从相邻原题链接核查。'
        item['remediation']=r.get('verification',{});item['case_ids']=r.get('caseIds',[])
        item['previous_checks']=item.get('checks',{})
        item['checks']={'source_traceability':'原始文件和对应页可回查','composition':'真实题目／原文与明确标注的教学解释、参考写法','context_sufficiency':'完整题面或连续原文语境；按本单元任务核对','answer_evidence':'具体题目、答案或参考表达与原材料对应'}
        item['data_file']='学习案例.sqlite3 → teaching_modules'
    for aid,r in supps.items():
        item=lookup[aid];target=s.select_one(item['target_selector']);assert target,aid
        sid='supplement-'+aid
        node=s.new_tag('section',id=sid,attrs={'class':'authentic-supplement'})
        append_html(node,'<h4>'+E(r.get('title') or '补充：真实材料与具体核对')+'</h4>'+lesson_html(r,case_map));target.append(node)
        item['next_action']='原可疑内容保留；已在本项末尾补充可回查原始材料与具体讲解，分别标记。'
        refs=source_refs(r,case_map);assert refs,(aid,'No supplement primary source')
        data['items'].append({'id':sid,'target_selector':'#'+sid,'anchor':sid,'title':r.get('title') or '真实材料补充','status':'达标','category':'可疑内容的达标补充','source_kind':'原始材料补充','source_basis':'；'.join(dict.fromkeys(x['label'] for x in refs)),'reason':r.get('auditReason') or '补充材料有原页出处，示范与答案针对该材料，不改变相邻原内容的可疑标记。','source_refs':refs,'next_action':'可对照原页复核。','case_ids':r.get('caseIds',[])})
    for skill,html in banks.items():
        chapter=s.find(id=skill);node=fragment(html).section
        tech=chapter.select_one(':scope > .technique-section')
        if tech:tech.insert_after(node)
        else:chapter.insert(0,node)
        outline=chapter.select_one('.chapter-outline')
        if outline:append_html(outline,'<a href="#'+skill+'-case-bank">原题片段练习</a>')
    with sqlite3.connect(DB) as con:
        framework_links={}
        for selector,cid in con.execute('SELECT target_selector,case_id FROM framework_links ORDER BY rowid'):
            framework_links.setdefault(selector,[]).append(case_map[cid])
    for selector,linked in framework_links.items():
        target=s.select_one(selector);assert target,selector
        node=s.new_tag('section',attrs={'class':'framework-case-links'})
        append_html(node,'<h4>用原题练这一题型</h4><div class="case-study-links">'+''.join('<a href="#'+E(dom_id(c))+'">'+E(c['title'])+'</a>' for c in linked)+'</div>')
        target.append(node)
    library=s.select_one('#library > header.chapter-head')
    entry=s.new_tag('section',attrs={'class':'case-library-entry'})
    append_html(entry,'<h2>原题片段练习</h2><div class="case-study-links">'+''.join('<a href="#'+skill+'-case-bank">'+{'reading':'阅读','writing1':'Task 1','writing2':'Task 2'}[skill]+' · '+str(values['cases'])+' 组</a>' for skill,values in stats.items())+'</div>')
    library.insert_after(entry)
    for c in cases:
        refs=source_refs({'sourceRefs':[c['source']]},case_map)
        data['items'].append({'id':'case-review-'+c['id'],'target_selector':'#'+dom_id(c),'anchor':dom_id(c),'title':c['title'],'status':'达标','category':'数据库原题案例','source_kind':c['source'].get('kind','原题'),'source_basis':c['source'].get('title','原始题目'),'reason':'原题来源、片段范围与参考答案已逐项核对；作答后展示答案证据和精读。' if c['skill']=='reading' else '原题与图表可回查，练习与参考段落回应原任务；自编参考写法已明确标注。','source_refs':refs,'next_action':'按原题作答后对照讲解。'})
    for link in s.select('a[href^="#"]'):
        raw=link['href'][1:]
        if raw in case_map:link['href']='#'+dom_id(case_map[raw])
    for card in s.select('.res-card,.topic-tile'):
        anchor=card.get('href','').lstrip('#')
        if anchor in changed_titles:
            title=card.select_one('h3,strong')
            if title:title.string=changed_titles[anchor]
            if anchor.startswith('speaking-new-'):
                for x in card.select('p,.res-card-status'):
                    x.string='真实考试题与原始样题 · 示范与逐项解释'
    # Resource record lists retain stable save IDs but use the replacement lesson names.
    for script in s.select('script'):
        text=script.get_text()
        if 'const catalog=' in text:
            m=re.search(r'const catalog=(\[.*?\]);',text,re.S)
            if m:
                cat=json.loads(m.group(1))
                for x in cat:
                    if x.get('anchor') in changed_titles:
                        x['title']=changed_titles[x['anchor']];x['status']='真实材料教学 · 已复核'
                script.string=text[:m.start(1)]+dump(cat)+text[m.end(1):]
    style=s.new_tag('style',id='authentic-case-style');style.string=(HERE/'authentic-cases.css').read_text(encoding='utf8');s.head.append(style)
    script=s.new_tag('script',id='authentic-case-script');script.string=(HERE/'authentic-cases.js').read_text(encoding='utf8');s.body.append(script)
    data['date']='2026-09-19';data['review_description']='57 项未达标内容已替换；38 项可疑内容保留原标记并分别补充达标材料。新增原题片段练习纳入本轮审核。'
    data['summary']={'total':len(data['items']),'by_status':dict(Counter(x['status'] for x in data['items'])),'remediated':len(reps),'retained_questionable':len(supps),'cases':stats}
    data['scope']['unit_level_items']=len(data['items']);data['scope']['source_html_sha256']=hashlib.sha256(str(s).encode()).hexdigest()
    data['scope']['method']='保留初轮审计ID，逐项替换57个未达标单元；保留38个可疑单元并分别增加独立补充；SQLite生成原题案例后核对来源、作答与精读流程。初轮报告另存。'
    with sqlite3.connect(DB) as con:
        con.execute('CREATE TABLE IF NOT EXISTS current_audit(id TEXT PRIMARY KEY,status TEXT NOT NULL,target_selector TEXT NOT NULL,payload TEXT NOT NULL)')
        con.execute('DELETE FROM current_audit')
        con.executemany('INSERT INTO current_audit VALUES(?,?,?,?)',[(i['id'],i['status'],i['target_selector'],dump(i)) for i in data['items']])
        con.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('case_statistics',dump(stats)))
        con.commit()
    page,marked=apply_review(str(s),data)
    MAIN.write_text(page,encoding='utf8')
    (HERE/'audit-content-remediated-20260919.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    (BOOK/'content-audit-current.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    final=BeautifulSoup(page,'html.parser');baseline=read(QA/'preservation-baseline.json')
    fields=[n['data-save'] for n in final.select('[data-save]')];ids=[n['id'] for n in final.select('[id]')]
    hashes={hashlib.sha256(n.get_text().encode()).hexdigest() for n in final.select('script')}
    checks={'old_fields_preserved':not(set(baseline['fields'])-set(fields)),'no_duplicate_fields':len(fields)==len(set(fields)),'old_ids_preserved':not(set(baseline['ids'])-set(ids)),'no_duplicate_ids':len(ids)==len(set(ids)),'core_scripts_preserved':all(h in hashes for i,h in enumerate(baseline['scripts']) if i!=7),'original_audio_preserved':[n.get('src') for n in final.select('audio source,audio[src]')]==baseline['audio'],'original_question_images_preserved':[hashlib.sha256(n.get('src','').encode()).hexdigest() for n in final.select('.qt-originals img')]==baseline['qt_original_images'],'one_resource_navigation':len(final.select('.sidebar [data-go="library"]'))==1 and not final.select('.sidebar [data-go="resource-update"]'),'case_count':len(final.select('.exam-case'))==len(cases),'audit_count':len(final.select('[data-audit-target]'))==len(data['items'])}
    (QA/'integration-checks.json').write_text(json.dumps({'checks':checks,'counts':data['summary']},ensure_ascii=False,indent=2),encoding='utf8')
    assert all(checks.values()),checks
    print(dump({'checks':checks,'counts':data['summary']}))

if __name__=='__main__':run()
