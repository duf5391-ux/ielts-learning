"""Apply a scoped review to the current book; never rebuild from old snapshots."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from bs4 import BeautifulSoup
from html import escape as E
import json,re,hashlib,sqlite3,shutil
from integrate_content_audit import apply_review, signatures, select_nodes

ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN=BOOK/'开始学习.html'
QA=ROOT/'deep-audit-qa'
INPUTS=['background-deep-audit-20260919.json','vocabulary-deep-audit-20260919.json','teaching-official-fit-20260919.json','listening-speaking-fit-20260919.json']
STATUSES=['达标','存疑','不达标']
def read(p):return json.loads(p.read_text(encoding='utf8'))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def plain(v):
    if isinstance(v,dict):return '；'.join(str(k)+'：'+plain(x) for k,x in v.items())
    if isinstance(v,list):return '；'.join(plain(x) for x in v)
    return str(v) if v is not None else ''
def append(n,html):
    for c in list(BeautifulSoup(html,'html.parser').contents):n.append(c)
def replace_in(n,old,new):
    count=0
    for t in list(n.find_all(string=True)):
        if t.parent.name in ['script','style']:continue
        protected=str(t).replace(new,'\x00DEEP_ALREADY_FIXED\x00')
        if old in protected:
            count+=protected.count(old);t.replace_with(protected.replace(old,new).replace('\x00DEEP_ALREADY_FIXED\x00',new))
    return count
def report_url(url):
    if re.match(r'^(?:https?:|file:)',url):return url
    base,sep,frag=url.partition('#')
    p=Path(base)
    return (p if p.is_absolute() else BOOK/p).as_uri()+(sep+frag if sep else '')

CSS='''
.deep-audit-entry{margin:18px 0;padding:16px 20px;border:1px solid #c9d6cd;border-radius:9px;background:#f3f7f2;color:#243d32}
.deep-audit-entry h3{margin:0 0 9px;font-size:18px}.deep-audit-entry p{font-size:14px;line-height:1.8;margin:7px 0}.deep-audit-entry a{overflow-wrap:anywhere}
.deep-audit-entry .deep-links{display:flex;gap:10px;flex-wrap:wrap}.deep-audit-entry .deep-links a{padding:7px 12px;border:1px solid #c9d6cd;background:white;border-radius:5px}
.deep-unit-summary{font-size:13px;line-height:1.8;color:#526355;margin:10px 0 16px}.deep-word-badge{font-size:11px!important;line-height:1.6;margin-left:6px;display:inline-block;padding:1px 5px;border-radius:4px;border:1px solid #cdd2cb;color:#6f590c;background:#fff9e4}
#vocabulary p,#vocabulary .authentic-supplement,#vocabulary .enrichment-body,#vocabulary .usage-card{overflow-wrap:anywhere;min-width:0}
'''

def build_report(data,inputs):
    cards=[]
    for i in data['items']:
        if i.get('audit_round')!='current':continue
        badges='<span class="badge" data-status="'+E(i['status'])+'">'+E(i['status'])+'</span>'
        if i.get('found_status') and i['found_status']!=i['status']:badges+='<small>发现时：'+E(i['found_status'])+' → 已作局部修正</small>'
        lines=''.join('<p><b>'+label+'：</b>'+E(plain(i.get(k)))+'</p>' for label,k in [('范围','scope'),('判定','reason'),('具体证据','evidence'),('官方依据','source_basis'),('拟合','fit_summary'),('已修','resolved_issue'),('待补','next_action')] if i.get(k))
        links=''.join('<p><a target="_blank" rel="noopener" href="'+E(report_url(x['url']),quote=True)+'">'+E(x['title'])+'</a>'+(' · '+E(x.get('note','')) if x.get('note') else '')+'</p>' for x in i.get('benchmark_links',[]))
        cards.append('<article data-status="'+i['status']+'" data-category="'+E(i.get('category','教学'))+'"><div class="top"><h2>'+E(i['title'])+'</h2>'+badges+'</div>'+lines+links+'<a href="'+MAIN.as_uri()+'#'+i['review_anchor']+'">回到这个学习单元 →</a></article>')
    counts=data['summary']['current_by_status']
    row=' · '.join(x+' '+str(counts.get(x,0)) for x in STATUSES)
    limits=''.join('<li>'+E(plain(x))+'</li>' for d in inputs for x in d.get('limitations',[]))
    html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>学习单元与词汇深审</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f6ef;color:#263a32;font:15px/1.85 "Microsoft YaHei",sans-serif}main{max-width:1100px;margin:auto;padding:32px 22px 70px}h1{font-size:30px;line-height:1.4}h2{font-size:18px;margin:0}p{margin:10px 0}a{color:#236c57;overflow-wrap:anywhere}article,.intro{background:white;border:1px solid #d2dcd2;border-radius:10px;padding:22px;margin:15px 0}article p{overflow-wrap:anywhere}.top{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.badge{font-size:12px;padding:2px 9px;border-radius:5px;white-space:nowrap;background:#fff3d0;color:#795609}.badge[data-status="达标"]{background:#e6f2e8;color:#285b3c}.badge[data-status="不达标"]{background:#fbe6e3;color:#8a382e}small{color:#70766b}nav{position:sticky;top:0;background:#f5f6ef;padding:14px 0;display:flex;gap:12px;flex-wrap:wrap}input,select{font:inherit;padding:8px 12px;border:1px solid #b6c7b9;border-radius:5px;background:white;max-width:100%}input{flex:1;min-width:180px}[hidden]{display:none!important}summary{cursor:pointer}@media(max-width:600px){main{padding:20px 12px}article,.intro{padding:16px}}
</style></head><body><main><h1>学习单元、话题背景与词汇深审</h1>'''
    html+='<p>2026-09-19 · '+str(data['summary']['current_total'])+' 项本轮复核 · '+row+'</p><div class="intro"><p>达标：按注明用途，题目、例子、讲解和答案相互支持。存疑：语言或片段可用，但出处映射、练习或证据不足。不达标：发现明确错误，或教学目标与材料、练习不相符。</p><p>优先同题官方样本及考官评语。官方出版物中的考生答案也可能低分；原创参考稿不授予官方分数。只有词频分母、计数和语料范围明确，才能使用相应范围的“高频”。</p><p>本轮已逐项检查全部 22 个“补充学习单元”，并另查 4 个话题背景学习单元。灰色“前轮”结论不计入本轮统计。各词库的全量检查和抽查范围见下方原始报告。</p><div class="sources">'
    for fn in INPUTS:
        report=ROOT/'research'/fn
        md=report.with_suffix('.md')
        html+='<p><a href="'+(md if md.exists() else report).as_uri()+'">'+E(fn.replace('-20260919.json',''))+' 详细报告</a></p>'
    html+='</div><p><a href="'+(BOOK/'词条逐项审核.html').as_uri()+'">1000词条逐项审核与样本词频 →</a></p><details><summary>覆盖限制</summary><ul>'+limits+'</ul></details></div><nav><input id="q" type="search" placeholder="查单元、错误、词语或材料" aria-label="搜索审核"><select id="status" aria-label="筛选状态"><option value="">全部状态</option>'+''.join('<option>'+x+'</option>' for x in STATUSES)+'</select><select id="category" aria-label="筛选内容类别"><option value="">全部类别</option></select></nav><p id="count" role="status"></p><div id="cards">'+''.join(cards)+'''</div><script>
const cards=[...document.querySelectorAll('article')],q=document.querySelector('#q'),status=document.querySelector('#status'),category=document.querySelector('#category');[...new Set(cards.map(x=>x.dataset.category))].forEach(x=>category.add(new Option(x,x)));function filter(){let n=0;for(const c of cards){c.hidden=!!((status.value&&c.dataset.status!==status.value)||(category.value&&c.dataset.category!==category.value)||!c.textContent.toLowerCase().includes(q.value.trim().toLowerCase()));if(!c.hidden)n++}document.querySelector('#count').textContent=`显示 ${n} / ${cards.length} 项`}for(const x of [q,status,category])x.addEventListener('input',filter);filter();</script></main></body></html>'''
    (ROOT/'research'/'学习单元与词汇深审.html').write_text(html,encoding='utf8')
    (BOOK/'学习单元与词汇深审.html').write_text(html,encoding='utf8')

def run():
    QA.mkdir(exist_ok=True)
    raw=MAIN.read_text(encoding='utf8')
    backup=ROOT/'backups'/'开始学习-before-deep-audit-20260919.html'
    if not backup.exists():backup.write_text(raw,encoding='utf8')
    s=BeautifulSoup(raw,'html.parser');before=signatures(s)
    for n in list(s.select('[data-deep-audit-ui]')):n.decompose()
    inputs=[read(ROOT/'research'/fn) for fn in INPUTS]
    data=read(ROOT/'audit-content-remediated-20260919.json')
    for i in data['items']:i['audit_round']='previous';i['status']={'可疑':'存疑','未达标':'不达标'}.get(i['status'],i['status'])
    by_node={id(select_nodes(s,i['target_selector'])[0]):i for i in data['items']}
    external=[];reviewed=[]
    for source,fn in zip(inputs,INPUTS):
        print('Integrating '+fn,flush=True)
        for a in source.get('items',[]):
            sel=a.get('target_selector')
            if sel in ['#vocabulary a[href="词频与原文证据.html"]','#vocabulary a[href="完整词汇来源库.html"]']:
                sel=sel.replace('#vocabulary a[','#vocabulary .tv-links a[')
            nodes=select_nodes(s,sel) if sel else []
            if len(nodes)!=1:
                if a.get('external_page') or a.get('page') or a.get('target_file'):
                    external.append(a);continue
                raise AssertionError((fn,sel,len(nodes)))
            target=nodes[0];i=by_node.get(id(target))
            if target.name=='a':
                wrapper_id='deep-link-'+a['id']
                wrapper=s.find(id=wrapper_id)
                if wrapper is None:
                    wrapper=s.new_tag('div',id=wrapper_id,attrs={'class':'deep-link-review'});target.wrap(wrapper)
                target=wrapper;sel='#'+wrapper_id
            if i and i.get('audit_round')=='current':raise AssertionError(('Duplicate current review',sel))
            if not i:
                i={'id':'deep-'+str(len(data['items'])+1),'target_selector':sel};data['items'].append(i);by_node[id(target)]=i
            existing_id=i['id'];previous=deepcopy(i)
            i.update(a);i['id']=existing_id;i['target_selector']=previous['target_selector'];i['audit_round']='current';i['review_file']=fn;i['previous_review']={k:previous.get(k) for k in ['status','reason','source_basis']}
            unit_title=target.select_one(':scope > summary strong') if target.get('data-enrichment') else None
            if unit_title:i['title']=unit_title.get_text(' ',strip=True)
            i['scope']=plain(i.get('scope') or i.get('scope_note') or '')
            i['evidence']=plain(i.get('evidence',[]))
            i['fit_summary']=plain(i.get('fit_summary') or i.get('official_fit') or '')
            registry=source.get('source_registry',[])
            if isinstance(registry,dict):registry=[dict(v,id=k) for k,v in registry.items()]
            if isinstance(i.get('source_basis'),list):
                mapped=[]
                for ref in i['source_basis']:
                    rec=next((r for r in registry if r.get('id')==ref),None)
                    mapped.append((rec.get('title') or rec.get('name') or ref) if rec else ref)
                    if rec and rec.get('url'):
                        i.setdefault('benchmark_links',[]).append({'title':rec.get('title') or ref,'url':rec['url']})
                i['source_basis']='；'.join(map(str,mapped))
            fit=i.get('official_fit',{})
            if isinstance(fit,dict) and fit.get('local_path'):
                page=(fit.get('physical_pages') or [None])[0]
                href=fit['local_path']+('#page='+str(page) if page else '')
                i.setdefault('benchmark_links',[]).append({'title':'所对照的本地原件','url':href})
            i['review_anchor']=target.get('id') or 'deep-unit-'+i['id']
            if not target.get('id'):
                marker=s.new_tag('span',id=i['review_anchor'],attrs={'data-deep-audit-ui':'anchor'})
                head=target.find('summary',recursive=False)
                if head:head.insert_after(marker)
                else:target.insert(0,marker)
            if target.get('id'):i['anchor']=target['id']
            reviewed.append(i)
    # Focused corrections discovered in this review, applied to visible teaching only.
    corrections=[]
    def fix(sel,old,new):
        nodes=select_nodes(s,sel);assert len(nodes)==1,(sel,len(nodes));n=nodes[0]
        count=replace_in(n,old,new)
        if not count:assert new in n.get_text(' ',strip=True),(sel,old)
        corrections.append({'selector':sel,'old':old,'new':new,'occurrences_changed':count})
    weather='#listening-new-new-listening-weather-table'
    fix(weather,'雨将在周六什么时段抵达 south coast？','雨最迟会在什么时候抵达 south coast？')
    fix(weather,'4＝下午。不要只记 Saturday 而漏掉时段。','4＝最迟周六下午。原文 by Saturday afternoon 给出截止时间；不能据此断定恰好在下午抵达。')
    for i in reviewed:
        if i.get('category')=='口语资源':
            n=s.select_one(i['target_selector'])
            if '真实 Part 3' in n.get_text(' ',strip=True):
                fix(i['target_selector'],'练习：保留题目中的对象、时间和问法，换成自己的真实经历。先口头作答，再对照上面的具体内容逐项检查；不需要逐字背诵参考作答。','练习：回应题目的一般判断或社会现象，提出理由、具体例子及适用条件。个人经历可以作例证，但不要用个人故事代替讨论。先独立口头作答，再检查是否回应问法。')
    fix('#speaking-new-sep26-energy','So the space itself is useful, but looking after it is part of the benefit.','So the space itself is useful, but the time and effort needed to maintain it are part of the trade-off.')
    fix('#listening-new-new-listening-lecture-outline','The task needs no equipment; in other words, you can do it anywhere.','The task needs no equipment; in other words, you do not need any tools or devices to do it.')
    lecture=next(i for i in reviewed if i['id']=='audit-024')
    lecture.update(found_status='不达标',resolved_issue='已修正in other words示范：无需设备不推出任何地点可做；现只做同义改述。')
    # Additional exact edits are reviewed before being placed in this file.
    for p in read(ROOT/'research'/'approved-deep-corrections.json') if (ROOT/'research'/'approved-deep-corrections.json').exists() else []:
        fix(p['selector'],p['old'],p['new'])
    glossary=s.select_one('#lookup-glossary')
    glossary_old=glossary.get_text()
    def update_strings(v):
        if isinstance(v,dict):return {k:update_strings(x) for k,x in v.items()}
        if isinstance(v,list):return [update_strings(x) for x in v]
        if isinstance(v,str):
            for p in corrections:
                v=v.replace(p['new'],'\x00DEEP_ALREADY_FIXED\x00').replace(p['old'],p['new']).replace('\x00DEEP_ALREADY_FIXED\x00',p['new'])
        return v
    glossary.string=json.dumps(update_strings(json.loads(glossary_old)),ensure_ascii=False)
    # Repairable language findings are re-evaluated only within their original language scope.
    correction_nodes={}
    for p in corrections:
        patched=select_nodes(s,p['selector'])[0]
        correction_nodes.setdefault(id(patched),[]).append(p)
        card=patched.find_parent(class_='tv-card')
        if card is not None:correction_nodes.setdefault(id(card),[]).append(p)
    for i in reviewed:
        target=select_nodes(s,i['target_selector'])[0]
        patches=correction_nodes.get(id(target),[])
        if patches and i.get('review_file')=='vocabulary-deep-audit-20260919.json' and ('.res-usage:nth-child(' in i['target_selector'] or '.tv-card[data-tv-id=' in i['target_selector']):
            i['found_status']=i['status'];i['status']='达标'
            i['resolved_issue']='已修订本卡的语言示范：'+'；'.join(p['new'] for p in patches)
            i['reason']='原发现见审查证据；当前用法示范已作局部修订，按注明的原创语言练习用途达标。'
            i['next_action']='保留原创示范身份；若用于官方高分表达学习，仍须补对应原句与考官评语。'
    if any(p['selector'].startswith('#reading-new-new-reading-urban-tfng') for p in corrections):
        i=next(i for i in reviewed if i['id']=='audit-008')
        i.update(found_status='存疑',status='达标',resolved_issue='已删去作答前泄露Q12/13答案的句子，保持先提交后核对的练习流程。',reason='按原题证据定位与学习后应用用途达标；已修复先泄露答案再要求检验的冲突。')
    everyday=next(i for i in reviewed if i['target_selector']=='#topic-everyday')
    everyday.update(found_status='存疑',status='达标',resolved_issue='已明示General Training用途；按生活通知的信息定位用途达标，不作为Academic难度样本。')
    for i in reviewed:
        if 'deep-link-vocab-frequency-link' in i['target_selector']:
            i.update(resolved_issue='独立词频页已补回语料分母、计数核查结果与不能外推考试概率的说明。',reason='词频数值复算达标，范围说明已补回；考试组仍缺从此视图直接回查PDF原件的映射，因此整体入口保留存疑。')
    # Keep historical review anchors and evidence, but remove their competing current verdict.
    for n in s.select('.learning-audit-note'):
        summary=n.find('summary',recursive=False)
        if summary:summary.string='历史教学审查（旧版本记录，当前判断见单元审核）'
        n.attrs.pop('open',None);n['data-verdict']='历史记录'
    for i in reviewed:i['status']={'可疑':'存疑','未达标':'不达标'}.get(i['status'],i['status']);assert i['status'] in STATUSES
    data['summary']={'current_total':len(reviewed),'current_by_status':dict(Counter(i['status'] for i in reviewed)),'previous_not_rechecked':len(data['items'])-len(reviewed),'external_review_items':len(external)}
    data['criteria']={'达标':'在本条注明用途内，题目、例子、讲解、练习与证据一致；不自动认证更大范围或高分。','存疑':'部分内容可用，但语境、来源映射、目标对应或反馈证据待补。','不达标':'存在明确错误或核心教学目标与材料、练习不相符。','原创规则':'原创微型示范和对真题的原创参考答案可按教学用途达标；不授予官方身份或分数。','高频规则':'频次只解释指定语料、清洗与词形单位，不外推IELTS总体概率。'}
    data['scope']={'date':'2026-09-19','current_reviewed_items':len(reviewed),'supplementary_learning_units':22,'background_learning_units':4,'background_readers':18,'word_rows_separate':1000,'method':'当前DOM逐项用途审核、官方原题/原稿/评语拟合、语言首审与统计复算；报告分别说明边界。'}
    data['review_description']='灰色“前轮”标签表示本轮未复核，不计入上方统计。全部22个补充学习单元及4个话题背景学习单元已逐项检查；详见学习单元与词汇深审。'
    data['corrections']=corrections;data['external_reviews']=external
    print('Applying reviewed labels',flush=True)
    page,_=apply_review(str(s),data);s=BeautifulSoup(page,'html.parser')
    style=s.new_tag('style',attrs={'data-deep-audit-ui':'style'});style.string=CSS;s.head.append(style)
    for section in s.select('.enrichment-section'):
        units=section.select('details[data-enrichment]')
        if not units:continue
        ids={u.get('data-audit-target') for u in units}
        subset=[i for i in reviewed if i['id'] in ids]
        counts=Counter(i['status'] for i in subset)
        note=s.new_tag('p',attrs={'class':'deep-unit-summary','data-deep-audit-ui':'units'})
        note.string='学习单元审核：'+str(len(subset))+'/'+str(len(units))+' 已复核 · '+' / '.join(k+' '+str(counts[k]) for k in STATUSES)+'。展开单元标题下的审核说明查看具体原因。'
        heading=section.find(['header','h2']);heading.insert_after(note)
    entry=s.new_tag('section',id='official-fit-priority',attrs={'class':'deep-audit-entry','data-deep-audit-ui':'entry'})
    append(entry,'<h3>学习单元与词汇：本轮深审</h3><p>重点检查例子、讲解、练习、答案是否对得上。官方同题高分样本优先用于对照；词频只按注明语料范围理解。</p><div class="deep-links"><a href="学习单元与词汇深审.html" target="_blank" rel="noopener">查看逐项审核与筛选</a><a href="#vocabulary">词汇学习单元</a><a href="#background">话题背景</a></div>')
    append(entry,'<p><a href="词条逐项审核.html" target="_blank" rel="noopener">1000词条：逐条语言审核与样本词频 →</a></p>')
    s.select_one('#library > header.chapter-head').insert_after(entry)
    word_entry=s.new_tag('aside',attrs={'class':'deep-audit-entry','data-deep-audit-ui':'word-entry'})
    append(word_entry,'<h3>逐词检查：意思、搭配与实际出现</h3><p>1000条词义与短搭配完成首审；完整原句依据仍待补。词频为指定样本内的精确词形统计，不代表考试出现概率。</p><a href="词条逐项审核.html" target="_blank" rel="noopener">筛选词条、查看修订与27篇样本计数 →</a>')
    s.select_one('#topical-vocabulary').insert(0,word_entry)
    benchmarks=read(ROOT/'research'/'approved-official-benchmarks.json') if (ROOT/'research'/'approved-official-benchmarks.json').exists() else []
    for b in benchmarks:
        target=s.select_one(b['selector']);assert target,b
        box=s.new_tag('aside',attrs={'class':'deep-audit-entry','data-deep-audit-ui':'benchmark'})
        append(box,'<h3>'+E(b['title'])+'</h3><p>'+E(b['explanation'])+'</p><div class="deep-links">'+''.join('<a target="_blank" rel="noopener" href="'+E(l['url'],quote=True)+'">'+E(l['title'])+'</a>' for l in b['links'])+'</div><p>'+E(b['task'])+'</p>')
        inner=target.select_one(':scope > .enrichment-body, :scope > .res-body')
        (inner if inner is not None else target).append(box)
    after=signatures(s)
    checks={k:before[k]==after[k] for k in ['fields','audio','images']}
    executable=lambda doc:[hashlib.sha256(n.get_text().encode()).hexdigest() for n in doc.select('script') if n.get('type')!='application/json']
    checks['executable_scripts_preserved']=executable(BeautifulSoup(raw,'html.parser'))==executable(s)
    checks['lookup_glossary_valid']=isinstance(json.loads(s.select_one('#lookup-glossary').get_text()),(dict,list))
    checks['all_original_ids_retained']=not(set(before['ids'])-set(after['ids']))
    ids=[n['id'] for n in s.select('[id]')];checks['no_duplicate_ids']=len(ids)==len(set(ids))
    checks['all_22_supplementary_units_reviewed']=all(n.get('data-audit-target') in {i['id'] for i in reviewed} for n in s.select('details[data-enrichment]') if n.find_parent('section',id='vocabulary') or n.find_parent('section',id='reading') or n.find_parent('section',id='writing1') or n.find_parent('section',id='writing2') or n.find_parent('section',id='listening') or n.find_parent('section',id='speaking'))
    assert all(checks.values()),checks
    MAIN.write_text(str(s),encoding='utf8')
    dump(ROOT/'audit-content-deep-20260919.json',data);dump(BOOK/'content-audit-current.json',data)
    with sqlite3.connect(BOOK/'学习案例.sqlite3') as con:
        con.execute('DELETE FROM current_audit')
        con.executemany('INSERT INTO current_audit VALUES(?,?,?,?)',[(i['id'],i['status'],i['target_selector'],json.dumps(i,ensure_ascii=False)) for i in data['items']])
    build_report(data,inputs)
    dump(QA/'integration.json',{'checks':checks,'summary':data['summary'],'preserved_fields':len(after['fields']),'corrections':corrections,'official_benchmarks':len(benchmarks)})
    print(json.dumps({'checks':checks,'summary':data['summary']},ensure_ascii=False))

if __name__=='__main__':run()
