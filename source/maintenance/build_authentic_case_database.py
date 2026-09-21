"""Import reviewed source data into SQLite and compile the offline case banks."""
from pathlib import Path
from reviewed_source_notes import annotate_source_html
from collections import Counter
from bs4 import BeautifulSoup
from html import escape as E
import hashlib, json, re, sqlite3, shutil
import material_reading as material

HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
DB = BOOK / '学习案例.sqlite3'
QA = HERE / 'authentic-case-qa'
CASE_FILES=['authentic-reading-cases.json','authentic-reading-official-cases.json','authentic-reading-cambridge-cases.json','authentic-reading-gap-cases.json','authentic-writing-cases.json']
MODULE_FILES=['reading-remediations.json','reading-official-remediations.json','writing-remediations.json','support-remediations.json']

def dump(x): return json.dumps(x, ensure_ascii=False)
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def items(value): return value if isinstance(value, list) else value.get('cases', [])
def digest(x): return hashlib.sha256(str(x).encode()).hexdigest()[:20]
def types(c):
    value = c.get('questionTypes') or c.get('questionType') or c.get('type') or '综合练习'
    labels={'note-completion':'笔记填空','true-false-not-given':'事实判断 TFNG','yes-no-not-given':'观点判断 YNNG','matching-headings':'标题匹配','matching-information':'段落信息匹配','matching-features':'人物／特征匹配','matching-sentence-endings':'句尾匹配','summary-completion':'摘要填空','sentence-completion':'句子填空','table-completion':'表格填空','flow-chart-completion':'流程图填空','diagram-labelling':'图示标注','short-answer':'短答题','short-answer-questions':'短答题','multiple-choice':'选择题','multiple-choice-multiple':'多项选择'}
    labels.update({'summary-completion-options':'选词摘要填空','diagram-label-completion':'图示标注','multiple-choice-single':'选择题','multiple-choice-multiple-answers':'多项选择'})
    return list(dict.fromkeys(labels.get(x,x) for x in (value if isinstance(value,list) else [value])))
def dom_id(c): return c['id'] if c['id'].startswith(c['skill']+'-') else c['skill']+'-case-'+c['id']
def question_numbers(q):
    raw=str(q.get('number',''));nums=re.findall(r'\d+',raw)
    if len(nums)==2 and re.search(r'[-–—]',raw) and 0<=int(nums[1])-int(nums[0])<20:return [str(n) for n in range(int(nums[0]),int(nums[1])+1)]
    return nums or [raw]
def question_count(c):return sum(len(question_numbers(q)) for q in c.get('questions',[]))
def pnum(page): return page[0] if isinstance(page, list) else page
def source_link(src):
    path = src.get('path') or src.get('local_path') or src.get('localPath') or ''
    if path and Path(path).is_absolute():
        try: path = Path(path).relative_to(BOOK).as_posix()
        except ValueError: path = Path(path).as_posix()
    page = pnum(src.get('page'))
    url = src.get('href') or path or src.get('url', '')
    if page and '.pdf' in url.lower() and '#page=' not in url: url += '#page='+str(page)
    title = src.get('title') or src.get('label') or '查看原题'
    return f'<a href="{E(url,quote=True)}" target="_blank" rel="noopener">{E(title)}</a>' if url else E(title)

def rich(value):
    """Render authored explanatory data as text, never as executable markup."""
    if not value: return ''
    if isinstance(value, str): return '<p>'+E(value)+'</p>'
    if isinstance(value, list): return ''.join(rich(x) for x in value)
    labels={'structure':'篇章结构','phrases':'词语与搭配','sentences':'句子精读','text':'原句','phrase':'表达','meaning':'含义','explanation':'讲解','why':'为什么','quote':'原文','focus':'精读重点','translation':'句意','pitfall':'容易误读之处','paragraph':'对应段落','answer':'答案','evidence':'证据','teachingPoint':'讲解','function':'作用'}
    return ''.join('<div>'+('<h4>'+E(labels.get(k,k))+'</h4>')+rich(v)+'</div>' for k,v in value.items() if v)

def source_html(source):
    page = source.get('page')
    label = (' · PDF 第 '+(', '.join(map(str,page)) if isinstance(page,list) else str(page))+' 页') if page else ''
    kind=source.get('kind','')
    return '<p class="case-source">'+E(kind)+' · '+source_link(source)+E(label)+'</p>'

def options_html(options):
    if isinstance(options,dict):return '<ul class="case-options">'+''.join('<li><strong>'+E(str(k))+'.</strong> '+E(str(v))+'</li>' for k,v in options.items())+'</ul>'
    if isinstance(options,list):return '<ul class="case-options">'+''.join('<li>'+E(str(x))+'</li>' for x in options)+'</ul>'
    return rich(options)

def render_case(c, source_reuse):
    cid=dom_id(c); skill=c['skill']; base='case-'+c['id']; questions=c.get('questions',[])
    paras=c.get('paragraphs',[]); wc=c.get('wordCount') or sum(len(re.findall(r"\b[\w'-]+\b", p.get('text','') if isinstance(p,dict) else p)) for p in paras)
    rawsrc=c.get('source',{}); search=' '.join([c['title'], *types(c), dump(rawsrc),dump(paras),dump([q.get('prompt','') for q in questions])]).lower()
    length=f'{len(paras)} 段 · {wc} 词 · {question_count(c)} 题' if skill=='reading' else '原题拆段写作 · 参考段落与逐段讲解'
    reused=' · 同篇原文另有裁切' if source_reuse>1 and skill=='reading' else ''
    out=[f'<details class="exam-case" id="{E(cid)}" data-case-id="{E(c["id"])}" data-types="{E(dump(types(c)),quote=True)}" data-search="{E(search,quote=True)}"><summary><strong>{E(c["title"])}</strong><span data-case-state>未作答</span><span class="case-meta">{E(" / ".join(types(c)))} · {E(length+reused)}</span></summary><div class="case-body">',source_html(rawsrc)]
    material_data=material.lessons()
    if skill.startswith('writing'):
        out.append(material.render_writing(c,material_data,material.source_cases()))
    if c.get('instructions'): out.append('<div class="case-task">'+rich(c['instructions'])+'</div>')
    if c.get('contextNote'):out.append('<p class="case-meta">'+E(c['contextNote'])+'</p>')
    if paras:
        out.append('<div class="case-passage" lang="en">')
        for p in paras:
            p={'text':p} if isinstance(p,str) else p
            text=p['text'];label=str(p.get('label',''))
            if re.fullmatch('[A-Z]',label):text=re.sub(r'^'+label+r'\s+','',text)
            out.append('<p><span class="case-paragraph-label">'+E(label)+'</span>'+E(text)+'</p>')
        out.append('</div>')
        if c.get('footnotes'):out.append('<aside class="case-meta">'+rich(c['footnotes'])+'</aside>')
    if c.get('prompt'):out.append('<div class="case-task" lang="en">'+rich(c['prompt'])+'</div>')
    image=c.get('image') or c.get('imagePath')
    if isinstance(image,dict):image=image.get('path') or image.get('src')
    if image:out.append(f'<figure><a href="{E(image,quote=True)}" target="_blank" rel="noopener"><img class="case-figure" src="{E(image,quote=True)}" alt="{E(c["title"])} · 原题图示，点击查看大图" loading="lazy"></a><figcaption class="case-meta">点击图示可查看大图。</figcaption></figure>')
    if c.get('practicePrompt'):out.append('<h4>本次写作任务</h4><div class="case-task">'+rich(c['practicePrompt'])+'</div>')
    if questions:
        option_groups={}
        for q in questions:
            if q.get('options'):option_groups.setdefault(dump(q['options']),[]).append(str(q.get('number','')))
        common_options={k:v for k,v in option_groups.items() if len(v)>1}
        for serialized,nums in common_options.items():out.append('<div class="case-task"><h4>共用选项 · 原题 '+E('、'.join(nums))+'</h4>'+options_html(json.loads(serialized))+'</div>')
        for i,q in enumerate(questions):
            n=q.get('number',i+1); fid=base+'-q'+str(i+1)
            out.append(f'<div class="case-question"><p><strong>{E(str(n))}.</strong> {E(q.get("prompt",q.get("text","")))}</p>')
            if q.get('instructions'):out.append(rich(q['instructions']))
            if q.get('options') and dump(q['options']) not in common_options:out.append('<div lang="en">'+options_html(q['options'])+'</div>')
            out.append(f'<label for="{E(fid)}">第 {E(str(n))} 题作答<input type="text" id="{E(fid)}" data-save="{E(fid)}" data-case-answer autocomplete="off"></label></div>')
    else:
        out.append(f'<label for="{E(base)}-answer">我的段落<textarea id="{E(base)}-answer" data-save="{E(base)}-answer" data-case-answer rows="9"></textarea></label><p class="case-meta" data-case-wordcount>0 词</p>')
    out.append(f'<input type="checkbox" hidden data-save="{E(base)}-done" data-case-done><input type="hidden" data-save="{E(base)}-saved-at" data-case-saved-at><button type="button" data-case-submit>保留作答，打开答案与精读</button><p class="case-status" data-case-status role="status"></p><section class="case-feedback" hidden><h3>对照答案，回到证据</h3>')
    if questions:
        for i,q in enumerate(questions):
            ans=q.get('answer',q.get('answers',''))
            ans='；'.join(map(str,ans)) if isinstance(ans,list) else str(ans)
            out.append('<div class="case-answer-row"><p><strong>第 '+E(str(q.get('number',i+1)))+' 题 · '+E(ans)+'</strong></p>'+rich(q.get('explanation')))
            if q.get('evidence'):out.append('<blockquote>'+rich(q['evidence'])+'</blockquote>')
            out.append('</div>')
        key=rawsrc.get('answerPage') or c.get('answerPage')
        if key:
            keysrc={**rawsrc,'page':key,'title':'核对原答案页'}
            if rawsrc.get('answerPath'):keysrc['path']=rawsrc['answerPath']
            out.append('<p class="case-source">'+source_link(keysrc)+'</p>')
    if c.get('modelAnswer'):
        out.append('<h4>参考写法</h4><p class="case-meta">下列段落为针对原题编写的参考写法，用于对照内容和表达；写作没有唯一标准答案。</p><div class="case-model" lang="en">'+rich(c['modelAnswer'])+'</div>')
    out.append(rich(c.get('explanation')))
    if c.get('intensive') and c['id'] not in material_data:out.append('<h3>答后精读</h3>'+rich(c['intensive']))
    out.append(f'<label for="{E(base)}-revision">我的修订／证据笔记<textarea id="{E(base)}-revision" data-save="{E(base)}-revision" rows="5"></textarea></label></section>')
    if c['id'] in material_data:out.append(material.render_reading(c,material_data[c['id']]))
    out.append('</div></details>')
    return annotate_source_html(''.join(out))

def original_key(c):
    s=c['source'];return s.get('originalUnit') or s.get('passageTitle') or (s.get('path','')+'|'+s.get('test','')+'|'+s.get('title',''))

def compile_banks(cases):
    out={}; stats={}; reuse=Counter(original_key(c) for c in cases)
    for skill,title in [('reading','原题片段 · 答后精读'),('writing1','看图写作 · 段落练习'),('writing2','议论文 · 段落练习')]:
        group=[c for c in cases if c['skill']==skill]
        if not group:continue
        tally=Counter(t for c in group for t in types(c)); originals=len({original_key(c) for c in group})
        description='保留正常考试原文和原题。按题型选取连续多段片段，作答后核对答案、证据与句子。' if skill=='reading' else '用真实题目练习多段写作。先审题并写出自己的段落，再看针对原题的参考写法和修改依据。'
        h=[f'<section class="case-bank" id="{skill}-case-bank" data-case-bank="{skill}"><h2>{title}</h2><p class="case-bank-intro">{description} 共 {len(group)} 组，来自 {originals} '+('篇不同原文' if skill=='reading' else '道不同原题')+'；同源练习已标注。</p><div class="case-toolbar"><label>查找<input type="search" data-case-search placeholder="题型、主题或出处"></label><label>进度<select data-case-filter><option value="all">全部</option><option value="new">未作答</option><option value="done">已作答</option></select></label><button type="button" data-case-next>继续未做的一组</button></div><div class="case-types" aria-label="按题型筛选"><button type="button" data-case-type="全部" aria-pressed="true">全部</button>']
        for t,n in tally.items():h.append(f'<button type="button" data-case-type="{E(t,quote=True)}" aria-pressed="false">{E(t)} · {n}</button>')
        h.append('</div><p class="case-progress" data-case-count aria-live="polite"></p><p data-case-empty hidden>没有符合条件的练习，试试更换关键词或进度。</p>')
        h.extend(render_case(c,reuse[original_key(c)]) for c in group);h.append('</section>');out[skill]=''.join(h)
        unique_questions={(original_key(c),n) for c in group for q in c.get('questions',[]) for n in question_numbers(q)}
        stats[skill]={'cases':len(group),'originals':originals,'questions':sum(question_count(c) for c in group),'uniqueQuestions':len(unique_questions),'answerFields':sum(len(c.get('questions',[])) for c in group),'by_type':dict(tally)}
    return out,stats

def package_sources():
    # Package exact copies of existing library originals; never create substitute sources.
    source_map=read(BOOK/'source-map.json')
    for name in CASE_FILES+MODULE_FILES:
        if not (HERE/name).exists():continue
        document=read(HERE/name)
        if not isinstance(document,dict):continue
        for asset in document.get('assetsToCopy',[]):
            origin=Path(asset['source']);target=(BOOK/asset['target']).resolve()
            assert target.is_relative_to(BOOK.resolve()),str(target)
            sha=hashlib.sha256(origin.read_bytes()).hexdigest()
            assert sha==asset['sha256'],str(origin)
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=sha:shutil.copy2(origin,target)
            row={'source':origin.as_posix(),'packaged':target.relative_to(BOOK).as_posix()}
            if not any(x.get('packaged')==row['packaged'] for x in source_map):source_map.append(row)
    (BOOK/'source-map.json').write_text(json.dumps(source_map,ensure_ascii=False,indent=2),encoding='utf8')

def build():
    package_sources()
    cases=[]
    for name in CASE_FILES:
        if not (HERE/name).exists():continue
        cases.extend(items(read(HERE/name)))
    assert len({c['id'] for c in cases})==len(cases),'duplicate case ids'
    con=sqlite3.connect(DB);con.execute('PRAGMA foreign_keys=ON')
    con.executescript('''CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,path TEXT NOT NULL,title TEXT,page TEXT,payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY,skill TEXT NOT NULL,title TEXT NOT NULL,source_id TEXT REFERENCES sources(id),original_unit TEXT,payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS case_types(case_id TEXT REFERENCES cases(id),question_type TEXT,PRIMARY KEY(case_id,question_type));
    CREATE TABLE IF NOT EXISTS paragraphs(case_id TEXT REFERENCES cases(id),sequence INTEGER,label TEXT,text TEXT,PRIMARY KEY(case_id,sequence));
    CREATE TABLE IF NOT EXISTS questions(case_id TEXT REFERENCES cases(id),sequence INTEGER,original_number TEXT,prompt TEXT,answer TEXT,evidence TEXT,explanation TEXT,payload TEXT,PRIMARY KEY(case_id,sequence));
    CREATE TABLE IF NOT EXISTS review_links(audit_id TEXT,case_id TEXT REFERENCES cases(id),relation TEXT,PRIMARY KEY(audit_id,case_id,relation));
    CREATE TABLE IF NOT EXISTS framework_links(target_selector TEXT,case_id TEXT REFERENCES cases(id),PRIMARY KEY(target_selector,case_id));
    CREATE TABLE IF NOT EXISTS teaching_modules(audit_id TEXT,relation TEXT,payload TEXT NOT NULL,PRIMARY KEY(audit_id,relation));
    CREATE TABLE IF NOT EXISTS support_materials(id TEXT PRIMARY KEY,payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);''')
    for t in ['framework_links','review_links','questions','paragraphs','case_types','cases','sources','teaching_modules','support_materials']:con.execute('DELETE FROM '+t)
    errors=[]
    for c in cases:
        assert c['skill'] in ['reading','writing1','writing2'],c['id']
        src=c['source'];path=src.get('path','');assert path,c['id']
        local=BOOK/path
        if not local.exists():errors.append({'case':c['id'],'missingSource':str(local)})
        srcid=src.get('id') or digest(dump(src));srcid=str(srcid)+'-'+digest(dump(src))[:8]
        con.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?,?,?)',(srcid,path,src.get('title',''),dump(src.get('page')),dump(src)))
        con.execute('INSERT INTO cases VALUES(?,?,?,?,?,?)',(c['id'],c['skill'],c['title'],srcid,original_key(c),dump(c)))
        for t in types(c):con.execute('INSERT INTO case_types VALUES(?,?)',(c['id'],t))
        for i,p in enumerate(c.get('paragraphs',[])):
            p={'text':p} if isinstance(p,str) else p
            con.execute('INSERT INTO paragraphs VALUES(?,?,?,?)',(c['id'],i,str(p.get('label','')),p['text']))
        for i,q in enumerate(c.get('questions',[])):
            assert q.get('answer') is not None,(c['id'],i,'missing answer')
            con.execute('INSERT INTO questions VALUES(?,?,?,?,?,?,?,?)',(c['id'],i,str(q.get('number',i+1)),q.get('prompt',q.get('text','')),dump(q['answer']),dump(q.get('evidence')),dump(q.get('explanation')),dump(q)))
    assert not errors,errors
    for name in MODULE_FILES:
        if not (HERE/name).exists():continue
        data=read(HERE/name)
        for c in data.get('cases',[]):
            con.execute('INSERT OR REPLACE INTO support_materials VALUES(?,?)',(c['id'],dump(c)))
        for relation in ['replacements','supplements']:
            for r in data.get(relation,[]):
                if (r.get('cross_module') or r.get('verification',{}).get('crossModule')) and not (r.get('teachingHtml') or r.get('html')):continue
                con.execute('INSERT INTO teaching_modules VALUES(?,?,?)',(r['auditId'],relation,dump(r)))
                for cid in r.get('caseIds',[]):
                    if any(c['id']==cid for c in cases):con.execute('INSERT OR IGNORE INTO review_links VALUES(?,?,?)',(r['auditId'],cid,relation))
    mappings=HERE/'case-framework-links.json'
    if mappings.exists():
        for row in read(mappings):
            for cid in row['caseIds']:
                assert any(c['id']==cid for c in cases),(row['targetSelector'],cid)
                con.execute('INSERT INTO framework_links VALUES(?,?)',(row['targetSelector'],cid))
    con.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('version','2026-09-19-authentic-1'));con.commit()
    exported=[json.loads(row[0]) for row in con.execute('SELECT payload FROM cases ORDER BY rowid')]
    con.close()
    banks,stats=compile_banks(exported)
    (BOOK/'authentic-cases.json').write_text(dump({'version':1,'cases':exported,'stats':stats}),encoding='utf8')
    QA.mkdir(exist_ok=True)
    for skill,html in banks.items():(QA/(skill+'-bank.html')).write_text(html,encoding='utf8')
    (QA/'case-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    print(dump(stats))
    return exported,banks,stats

if __name__=='__main__':build()
