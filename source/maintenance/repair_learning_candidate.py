"""Repair the reviewed navigation candidate; preserve the live book and audit inputs."""
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from collections import Counter
import hashlib, json, re, sys

ROOT = Path(__file__).resolve().parent
STAGE = Path('D:/IELTS-Work/learning-adjust-20260920')
SOURCE = STAGE / '开始学习-navigation-v2.html'
TARGET = STAGE / '开始学习-repaired.html'
EXPECTED = '4a6027355f4644bb3145b23a79266a3e7e7a2509a5c45d1d420825631fb77f67'

def run():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    s = BeautifulSoup(raw.decode('utf8'), 'html.parser')
    original_fields = Counter(n['data-save'] for n in s.select('[data-save]'))
    original_ids = {n['id'] for n in s.select('[id]')}
    original_media = Counter((n.name, n.get('src')) for n in s.select('img,audio,source') if n.get('src'))
    data = json.loads(s.find(id='learning-adjust-data').string)
    units = {u['id']: u for u in data['units']}
    changes = []

    def add(node, text):
        for child in list(BeautifulSoup(text, 'html.parser').contents): node.append(child)

    def replace(script, old, new):
        assert script.string.count(old) == 1, old[:120]
        script.string = script.string.replace(old, new)

    scripts = s.find_all('script')
    core = scripts[0]
    # Persist all related fields as one transaction. Failed saves keep drafts editable.
    api = '''
window.IELTSRecordStore={commit(values){
 if(loadBlocked)return false;
 const controls=Object.entries(values).map(([k,v])=>[$(`[data-save="${k}"]`),v]);
 if(controls.some(([n,v])=>!n||!['string','boolean'].includes(typeof v)))return false;
 const previous=state;
 state={...state,fields:{...state.fields,...values}};
 if(!save()){state=previous;return false}
 controls.forEach(([n,v])=>{if(n.type==='checkbox')n.checked=v;else n.value=v});
 document.dispatchEvent(new Event('ielts-record-committed'));return true;
}};
'''
    replace(core, 'function wordCounts()', api + '\nfunction wordCounts()')
    replace(core, "localStorage.setItem(key,JSON.stringify(state));storageOK=true;", "const raw=JSON.stringify(state);localStorage.setItem(key,raw);if(localStorage.getItem(key)!==raw)throw Error('Record write was not retained');storageOK=true;")
    replace(core, 'const note=$(`[data-save="${id}-record-note"]`);', 'const note=$(`[data-save="${id}-record-note"]`)||(id===\'speaking-review\'?$(`[data-save="speaking-review-answer"]`):null);')
    replace(core, 'state.fields[note.dataset.save]=name;save()', "note.dispatchEvent(new Event('input',{bubbles:true}))")
    enrichment = scripts[1]
    old = "const time=field(el,'saved-at');time.value=new Date().toLocaleString();time.dispatchEvent(new Event('input',{bubbles:true}));const frozen=field(el,'frozen');frozen.checked=true;frozen.dispatchEvent(new Event('input',{bubbles:true}));refresh(el);"
    new = "const time=field(el,'saved-at'),frozen=field(el,'frozen');if(!window.IELTSRecordStore.commit({[time.dataset.save]:new Date().toLocaleString(),[frozen.dataset.save]:true})){el.querySelector('[data-enrich-status]').textContent='当前未能保存，首稿仍可编辑。请先导出文字，答案尚未解锁。';return;}refresh(el);"
    replace(enrichment, old, new)
    case = s.find(id='authentic-case-script')
    old = "saveField(unit.querySelector('[data-case-saved-at]'),new Date().toISOString());saveField(unit.querySelector('[data-case-done]'),true);refresh(unit);"
    new = "const time=unit.querySelector('[data-case-saved-at]'),done=unit.querySelector('[data-case-done]');if(!window.IELTSRecordStore.commit({[time.dataset.save]:new Date().toISOString(),[done.dataset.save]:true})){unit.querySelector('[data-case-status]').textContent='当前未能保存，作答仍可编辑。请先导出文字，答案尚未解锁。';return;}refresh(unit);"
    replace(case, old, new)
    changes.append('首稿与案例提交原子保存；失败不冻结、不解锁；口语加练自动记录录音文件名')

    def new_field(parent, key, label, rows=2):
        add(parent, f'<label class="field"><span>{label}</span><textarea data-save="{key}" rows="{rows}"></textarea><button type="button" class="la-unknown" data-la-unknown="{key}">暂时不会</button></label>')
        return key

    def gate(node, keys, ident):
        assert keys
        node['id'] = node.get('id') or ident
        node['data-answer-gate'] = json.dumps(keys, ensure_ascii=False)
        node.attrs.pop('open', None)
        if node.select_one(':scope > .la-gate-content'): return
        wrapper = s.new_tag('div', attrs={'class':'la-gate-content','hidden':''})
        for c in list(node.contents):
            if not (isinstance(c, Tag) and c.name == 'summary'): wrapper.append(c.extract())
        node.append(wrapper)

    # Original optional notes never count as answers or prerequisites.
    def optional(key):
        return key.startswith(('resource-note-', 'resource-review-')) or bool(re.search(r'-(note|revision|transfer|diagnosis|saved-at|minutes|review|familiarity)$', key))
    for u in data['units']:
        u['steps'] = [step for step in u['steps'] if not optional(step['key'])]
    for d in s.select('[data-answer-gate]'):
        keys = [k for k in json.loads(d['data-answer-gate']) if not optional(k)]
        assert keys, d['id']
        d['data-answer-gate'] = json.dumps(keys, ensure_ascii=False)

    # Paired tasks must be completed independently of the background-read checkbox.
    for ident in ['topic-education','topic-technology','topic-work']:
        u = units[ident]
        u['steps'] += [{'kind':'answer','key':n['data-save']} for n in s.find(id=ident).select('textarea[data-save^="prereq-"]')]
    # Technology's paired tasks are reading evidence/meaning; its background is reusable.
    tech = s.find(id='topic-technology')
    s.find(id='reading').append(tech.extract())
    units['topic-technology'].update(skill='reading', skillLabel='阅读')
    for a in tech.select('.reader-toolbar a'): a['href']='#study-reading-list'
    changes.append('可选笔记从进度和解锁条件移除；教育/工作/科技按实际配套任务计算进度')

    # Each general-English lesson now has its own answers. Unrelated IELTS questions
    # move intact into listening practice so one lesson is no longer two topics.
    listening = [
        ('campus-notes',5,'shipping-form','运输表单：姓名、地址、尺寸与总价','表单填空'),
        ('team-roles',6,'insurance','运输保险：选项与最终决定','单项选择'),
        ('weather-table',6,'overseas','海外生活：困难与社区信息','匹配题'),
        ('lecture-outline',5,'distance-learning','远程学习：动机与时间安排','单项选择'),
    ]
    for suffix,count,slug,title,kind in listening:
        ident = 'listening-new-new-listening-'+suffix
        n = s.find(id=ident)
        heading = next(h for h in n.select('.res-body h3') if '应用一下' in h.get_text())
        heading.string = '听后练习'
        old_key = next(d for d in n.select('.res-body details') if d.find('summary').get_text(strip=True)=='查看参考与解释')
        answers = s.new_tag('div', attrs={'class':'la-lesson-answers'})
        keys = []
        for q in range(1,count+1):
            label = '改正最后一句中的代词位置' if suffix=='campus-notes' and q==5 else f'第 {q} 题'
            keys.append(new_field(answers, 'lesson-listening-'+suffix+'-q'+str(q), label))
        old_key.insert_before(answers)
        gate(old_key, keys, 'check-listening-'+suffix)
        units[ident]['steps'] = [{'kind':'answer','key':key} for key in keys]
        units[ident]['progressLabel']='练习已作答'
        track = n.select_one('[data-save^="resource-learned-"]').find_parent('label')
        for text in list(track.find_all(string=True, recursive=False)): text.replace_with(' 我已读过讲解')
        exercise = n.select_one('.prereq-listening')
        new_id = 'practice-listening-'+slug
        exercise['data-learning-unit'] = new_id
        outer = s.new_tag('article', id=new_id)
        outer['data-learning-unit'] = new_id
        del exercise['data-learning-unit']
        add(outer, f'<h2>{title}</h2><div data-unit-progress="{new_id}" class="la-part-progress"></div>')
        outer.append(exercise.extract())
        s.find(id='practice-listening').append(outer)
        steps = [{'kind':'answer','key':x['data-save']} for x in exercise.select('textarea[data-save]') if not optional(x['data-save'])]
        u = {'id':new_id,'mode':'practice','skill':'listening','skillLabel':'听力','title':title,'topic':'工作与生活','type':kind,'description':'听完整题段，作答后核对原稿与答案。','steps':steps}
        data['units'].append(u);units[new_id]=u
    changes.append('四组听力教学补22个对应作答位置；四组不同题材的雅思题独立归入听力练习')

    # Supplementary duplicate source commentary belongs after the actual attempt.
    for ident in ['learn-reading-headings-miles','learn-reading-choice-older-workers','learn-vocab-take-into-account']:
        n = s.find(id=ident)
        extra = n.select_one(':scope > .authentic-supplement')
        d = s.new_tag('details')
        add(d,'<summary>原文与答案详解</summary>')
        d.append(extra.extract())
        n.select_one('.enrichment-feedback').append(d)

    # A phrase lesson should not contain an unrelated 13-question reading paper.
    usage = s.find(id='usage-03');extra=usage.select_one('.authentic-supplement')
    assert not extra.select('[data-save],img,audio,source')
    preserved = [x['id'] for x in extra.select('[id]')]
    extra.clear()
    add(extra, '<h4>标明消息从哪里来</h4><p>according to 后接信息来源，例如一份通知、调查或某个人的说法。引用来源不表示你已证实了其中的结论。</p><p>用 according to 改写这条消息（练习情境）：The notice says that the workshop is on Friday at 10 a.m.</p>')
    for child_id in preserved: add(extra,f'<span id="{child_id}"></span>')
    key = new_field(extra,'usage-03-application','我的改写')
    d=s.new_tag('details');add(d,'<summary>完成后核对</summary><p>According to the notice, the workshop is on Friday at 10 a.m.</p><p>the notice 是信息来源；时间与活动保持原意。according to 后不直接接一个完整的主谓句。</p>');extra.append(d)
    gate(d,[key],'check-usage-03')
    units['usage-03']['steps']=[{'kind':'answer','key':key}]
    changes.append('三处补充答案放回提交后的反馈区；according to 配套练习聚焦表达本身')

    # Use the short semantic title; the full summary also contains description/time.
    for u in data['units']:
        n=s.find(id=u['id'])
        if n.has_attr('data-enrichment'):
            summary=n.find('summary',recursive=False)
            title=summary.select_one('strong') or summary.select_one('.enrichment-title')
            if title:u['title']=title.get_text(' ',strip=True)
            else:
                span=summary.find('span')
                if span:u['title']=span.get_text(' ',strip=True)
        u['title']=re.sub(r'^\d{2}\s+','',u['title'])
        u['title']=re.sub(r'^新增\s*','',u['title'])
        u['type']=u.get('type') or u['title']
    # All progress collections follow current DOM ownership after moving the tasks.
    for root in s.select('main > .panel'):
        collection=root.select_one(':scope > [data-collection-progress]')
        if collection:collection['data-collection-progress']=json.dumps([u['id'] for u in data['units'] if s.find(id=u['id']).find_parent(id=root['id'])],ensure_ascii=False)
    # Reading project uses a different passage after the worked judgement example.
    project=next(p for p in data['projects'] if p['id']=='reading-evidence')
    replacement='topic-health'
    assert replacement in units
    project['units']=['reading-tech-judgement',replacement,'reading-first']
    card=s.select_one('[data-project="reading-evidence"] ol');card.clear()
    for ident in project['units']:add(card,f'<li><a href="#{ident}">{units[ident]["title"]}</a></li>')

    # Obsolete review badges are text nodes left by earlier content assembly.
    for t in list(s.find_all(string=True)):
        if t.parent.name in ['script','style']:continue
        new=str(t).replace('前轮·达标','').replace('前轮 · 达标','')
        if new!=str(t):t.replace_with(new)
    for n in s.select('[data-audit-target]'):del n['data-audit-target']
    # Optional reflection stays available without crowding the task or its progress.
    for n in s.select('[data-enrichment] [data-save]'):
        if re.search(r'-(diagnosis|familiarity|transfer)$',n['data-save']):
            label=n.find_parent('label')
            if label and not label.find_parent(class_='la-optional'):
                d=s.new_tag('details',attrs={'class':'la-optional'});add(d,'<summary>可选：记录或再练一次</summary>');label.wrap(d)

    data['repairVersion']=1
    s.find(id='learning-adjust-data').string=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    s.find(id='learning-adjust-script').string=(ROOT/'learning-adjust.js').read_text(encoding='utf8')
    s.find(id='learning-adjust-model-script').string=(ROOT/'learning-adjust-model.js').read_text(encoding='utf8')
    fields=Counter(n['data-save'] for n in s.select('[data-save]'))
    assert not (original_fields-fields),'Saved fields removed'
    assert all(v==1 for v in fields.values()),'Duplicate saved fields'
    assert original_ids<={n['id'] for n in s.select('[id]')},'Anchor removed'
    media=Counter((n.name,n.get('src')) for n in s.select('img,audio,source') if n.get('src'))
    assert not (original_media-media),'Existing media removed'
    output=str(s).encode('utf8');TARGET.write_bytes(output)
    report={'sourceSHA256':EXPECTED,'outputSHA256':hashlib.sha256(output).hexdigest(),'target':str(TARGET),'published':False,'originalFields':sum(original_fields.values()),'fields':sum(fields.values()),'units':len(data['units']),'changes':changes,'browserEndToEnd':False}
    (ROOT/'research/learning-repair-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');run()
