"""Incremental, checked publication of material reading and writing preparation."""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import argparse, hashlib, json, re, shutil, sqlite3, sys
import material_reading as M

ROOT=M.ROOT
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
LIVE=BOOK/'开始学习.html'
QA=ROOT/'material-reading-qa'
STAGE=QA/'stage'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,indent=2)

class Spans(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,text):
        super().__init__(convert_charrefs=False);self.text=text;self.lines=[0];self.stack=[];self.ids={}
        self.lines.extend(m.end() for m in re.finditer('\n',text));self.feed(text)
    def position(self):
        row,col=self.getpos();return self.lines[row-1]+col
    def handle_starttag(self,tag,attrs):
        if tag not in self.VOID:self.stack.append((tag,dict(attrs).get('id'),self.position()))
    def handle_startendtag(self,tag,attrs):pass
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                _,ident,start=self.stack[i]
                if ident:self.ids[ident]=(start,self.text.index('>',self.position())+1)
                del self.stack[i:];return

def fragment(text):return BeautifulSoup(text,'html.parser')
def append(parent,text):
    for child in list(fragment(text).contents):parent.append(child)

def update_reading(raw,c,lesson):
    soup=fragment(raw);unit=soup.find(id=M.case_id(c));feedback=unit.select_one('.case-feedback')
    assert feedback is not None,c['id']
    for old in unit.select('.material-reading'):old.decompose()
    heading=next((h for h in feedback.find_all('h3',recursive=False) if h.get_text(strip=True)=='答后精读'),None)
    if heading:
        sibling=heading.next_sibling
        while sibling is not None:
            nxt=sibling.next_sibling
            if getattr(sibling,'name',None)=='label' and sibling.select_one('[data-save]'):break
            sibling.extract();sibling=nxt
        heading.decompose()
    append(unit.select_one('.case-body'),M.render_reading(c,lesson))
    button=unit.select_one('[data-case-submit]')
    if button:button.string='保留作答，查看答案'
    return str(unit)

def update_writing(raw,c,data,cases):
    soup=fragment(raw);unit=soup.find(id=M.case_id(c))
    for old in unit.select('.material-writing'):old.decompose()
    content=M.render_writing(c,data,cases)
    if content:
        prep=fragment(content).section
        prompt=unit.select_one('.case-body > .case-task')
        assert prompt,c['id'];prompt.insert_before(prep)
    return str(unit)

def link_alias(raw,ids,cases):
    soup=fragment(raw);unit=soup.find();
    for old in unit.select('[data-material-links]'):old.decompose()
    if ids:
        links='<aside data-material-links=""><h4>这份材料的精读</h4><p>'+ ' · '.join('<a href="#'+M.intensive_id(cid)+'">'+M.E(cases[cid]['title'])+'</a>' for cid in ids)+'</p></aside>'
        append(unit,links)
    return str(unit)

def aliases(cases):
    result={}
    for u in M.read(ROOT/'precise-reading.json')['units']:
        key=u['source'].get('originalUnit')
        linked=[c['id'] for c in cases.values() if c['skill']=='reading' and c['source'].get('originalUnit')==key]
        if not linked:
            title=u.get('title','').lower()
            linked=[c['id'] for c in cases.values() if c['skill']=='reading' and title and title in c['title'].lower()]
        assert linked,u['id'];result[u['id']]=linked
    result['reading-first']=[cid for cid in cases if cid.startswith('rd-c21-davies-')]
    return result

def validate_page(original,html,data,cases):
    before,after=fragment(original),fragment(html)
    counts=lambda soup:Counter(n['data-save'] for n in soup.select('[data-save]'))
    assert counts(before)==counts(after),'Saved controls changed'
    assert all(n==1 for n in counts(after).values()),'Duplicate save fields'
    ids=Counter(n['id'] for n in after.select('[id]'))
    assert not {k:v for k,v in ids.items() if v>1},'Duplicate DOM ids'
    assert not set(n['id'] for n in before.select('[id]'))-set(ids),'Existing anchors lost'
    media=lambda s:Counter((n.name,n.get('src')) for n in s.select('audio,source,img'))
    assert media(before)==media(after),'Media changed'
    for cid,lesson in data.items():
        node=after.find(id=M.intensive_id(cid));assert node and not node.find_parent(class_='case-feedback'),cid
        assert not node.select('[data-save],button,input,textarea'),cid
        assert node.select_one('.mr-paragraph blockquote')
        for link in node.select('a[href^="#"]'):assert after.find(id=link['href'][1:]),link['href']
        source=after.find(id=M.case_id(cases[cid]))
        assert str(source.select_one('.case-passage'))==str(before.find(id=source['id']).select_one('.case-passage')),cid
        assert [str(x) for x in source.select('.case-question')]==[str(x) for x in before.find(id=source['id']).select('.case-question')],cid
    for c in cases.values():
        if c['skill'].startswith('writing') and M.writing_entries(c['id'],data):
            node=after.find(id=M.writing_id(c['id']));assert node
            body=node.parent;children=list(body.children)
            assert children.index(node)<children.index(body.select_one('.case-task')),'Preparation must precede prompt and answer'
    nav=lambda s:str(s.find(id='workspace-navigation'))
    assert nav(before)==nav(after),'Navigation changed'
    changed={'daily-study-catalog','daily-study-model-script','daily-study-script','authentic-case-script','material-reading-script'}
    unchanged=lambda s:[(n.get('id'),n.get_text()) for n in s.select('script') if n.get('id') not in changed]
    assert unchanged(before)==unchanged(after),'Existing support/controller script changed'
    return {'savedFields':sum(counts(after).values()),'allSavedFieldsPreserved':True,'allOriginalMediaPreserved':True,'originalReadingAndQuestionsPreserved':True,'navigationPreserved':True,'pureReadingUnits':len(data),'writingPreparationUnits':len(after.select('.material-writing'))}

def stage_file(path,payload,manifest,snapshots):
    path=Path(path);name=str(len(manifest))+'-'+path.name;target=STAGE/name
    raw=payload if isinstance(payload,bytes) else payload.encode('utf8');target.write_bytes(raw)
    before=snapshots[path]
    expected=sha(before) if before is not None else None
    assert (sha(path.read_bytes()) if path.exists() else None)==expected,'Input changed during build: '+str(path)
    manifest.append({'path':str(path),'before':expected,'staged':str(target),'after':sha(raw)})

def build():
    STAGE.mkdir(parents=True,exist_ok=True)
    data=M.lessons(True)
    paths=[LIVE,ROOT/'daily-study-catalog.json',*(ROOT/n for n in M.READING_FILES),ROOT/'authentic-writing-cases.json',BOOK/'authentic-cases.json',BOOK/'material-reading.json',BOOK/'学习案例.sqlite3']
    snapshots={p:p.read_bytes() if p.exists() else None for p in paths}
    def document(path):return json.loads(snapshots[Path(path)].decode('utf-8-sig'))
    cases={c['id']:c for name in M.READING_FILES+['authentic-writing-cases.json'] for c in document(ROOT/name)['cases']}
    stats=M.validate(data,cases)
    original=snapshots[LIVE].decode('utf8');spans=Spans(original).ids;replacements={}
    for cid,c in cases.items():
        ident=M.case_id(c)
        if c['skill']=='reading' or M.writing_entries(cid,data):
            assert ident in spans,ident
            a,b=spans[ident];raw=original[a:b]
            replacements[ident]=update_reading(raw,c,data[cid]) if c['skill']=='reading' else update_writing(raw,c,data,cases)
    for ident,ids in aliases(cases).items():
        assert ident in spans,ident
        a,b=spans[ident];replacements[ident]=link_alias(original[a:b],ids,cases)
    for ident,filename in [('daily-study-model-script','daily-study-model.js'),('daily-study-script','daily-study.js')]:
        replacements[ident]='<script id="'+ident+'">\n'+(ROOT/filename).read_text(encoding='utf8')+'\n</script>'
    catalog=document(ROOT/'daily-study-catalog.json')
    reading=next(x for x in catalog if x['skill']=='reading')
    reading['variants']=M.daily_variants(data,cases)
    reading['stages']=reading['variants'][0]['stages']
    replacements['daily-study-catalog']='<script id="daily-study-catalog" type="application/json">'+json.dumps(catalog,ensure_ascii=False).replace('</','<\\/')+'</script>'
    # Keep the current, repaired case controller; change only its submit label.
    a,b=spans['authentic-case-script'];replacements['authentic-case-script']=original[a:b].replace('保留作答，打开答案与精读','保留作答，查看答案')
    patches=sorted([(spans[k][0],spans[k][1],v) for k,v in replacements.items()],reverse=True)
    for (a,b,_),(next_a,next_b,_) in zip(patches,patches[1:]):assert next_b<=a,'Overlapping replacements'
    html=original
    for a,b,new in patches:html=html[:a]+new+html[b:]
    html=re.sub(r'<!--MATERIAL-READING-V1:assets-->.*?<!--/MATERIAL-READING-V1:assets-->','',html,flags=re.S)
    style=(ROOT/'material-reading.css').read_text(encoding='utf8');script=(ROOT/'material-reading.js').read_text(encoding='utf8')
    html=html.replace('</body>','<!--MATERIAL-READING-V1:assets--><style id="material-reading-style">'+style+'</style><script id="material-reading-script">'+script+'</script><!--/MATERIAL-READING-V1:assets--></body>',1)
    checks=validate_page(original,html,data,cases)
    manifest=[]
    stage_file(LIVE,html,manifest,snapshots)
    (QA/'candidate.html').write_bytes(html.encode('utf8'))
    stage_file(ROOT/'daily-study-catalog.json',dump(catalog),manifest,snapshots)
    for filename in M.READING_FILES:
        doc=document(ROOT/filename)
        for c in doc['cases']:
            c['intensive']=M.simple_intensive(data[c['id']]);c['materialReadingRef']=c['id']
        stage_file(ROOT/filename,dump(doc),manifest,snapshots)
    writing=document(ROOT/'authentic-writing-cases.json')
    for c in writing['cases']:
        refs=[{'readingCaseId':source,'phrase':phrase['phrase']} for source,phrase,match in M.writing_entries(c['id'],data)]
        if refs:c['readingExpressionRefs']=refs
        else:c.pop('readingExpressionRefs',None)
    stage_file(ROOT/'authentic-writing-cases.json',dump(writing),manifest,snapshots)
    exported=document(BOOK/'authentic-cases.json')
    for c in exported['cases']:
        if c['id'] in data:c['intensive']=M.simple_intensive(data[c['id']]);c['materialReadingRef']=c['id']
        elif c['skill'].startswith('writing'):
            refs=[{'readingCaseId':source,'phrase':phrase['phrase']} for source,phrase,match in M.writing_entries(c['id'],data)]
            if refs:c['readingExpressionRefs']=refs
            else:c.pop('readingExpressionRefs',None)
    stage_file(BOOK/'authentic-cases.json',dump(exported),manifest,snapshots)
    stage_file(BOOK/'material-reading.json',dump({'version':1,'cases':list(data.values())}),manifest,snapshots)
    db=BOOK/'学习案例.sqlite3';dbcopy=STAGE/'updated.sqlite3';dbcopy.write_bytes(snapshots[db])
    with sqlite3.connect(dbcopy) as con:
        for c in exported['cases']:
            row=con.execute('SELECT payload FROM cases WHERE id=?',(c['id'],)).fetchone();assert row,c['id']
            payload=json.loads(row[0])
            for key in ['intensive','materialReadingRef','readingExpressionRefs']:
                if key in c:payload[key]=c[key]
                elif key=='readingExpressionRefs':payload.pop(key,None)
            con.execute('UPDATE cases SET payload=? WHERE id=?',(json.dumps(payload,ensure_ascii=False),c['id']))
        con.commit();assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    stage_file(db,dbcopy.read_bytes(),manifest,snapshots)
    report={'sourceSHA256':sha(original.encode('utf8')),'candidateSHA256':sha(html.encode('utf8')),'stats':stats,'checks':checks,'manifest':manifest,'published':False,'browserVisualVerified':False}
    (QA/'integration.json').write_text(dump(report),encoding='utf8')
    print(dump({k:v for k,v in report.items() if k!='manifest'}))

def publish():
    report=M.read(QA/'integration.json');checks=M.read(QA/'interaction-results.json')
    assert checks['sha256']==report['candidateSHA256'] and checks['passed']==checks['total'] and checks['total']>=5
    files=report['manifest'];backup=QA/('backup-'+report['sourceSHA256'][:12]);backup.mkdir(exist_ok=True)
    for entry in files:
        path=Path(entry['path']);assert (sha(path.read_bytes()) if path.exists() else None)==entry['before'],'Changed since staging: '+str(path)
        assert sha(Path(entry['staged']).read_bytes())==entry['after']
    for i,entry in enumerate(files):
        path=Path(entry['path'])
        if path.exists():
            dest=backup/(str(i)+'-'+path.name);shutil.copy2(path,dest);assert sha(dest.read_bytes())==entry['before'];entry['backup']=str(dest)
    report['publishState']='prepared';(QA/'integration.json').write_text(dump(report),encoding='utf8')
    # Publish content dependencies first; the checked HTML is the final visible switch.
    for entry in files[1:]+files[:1]:
        path=Path(entry['path']);assert (sha(path.read_bytes()) if path.exists() else None)==entry['before'],'Concurrent update: '+str(path)
        temp=path.with_name(path.name+'.material-'+entry['after'][:12]+'.tmp');temp.write_bytes(Path(entry['staged']).read_bytes());temp.replace(path)
        assert sha(path.read_bytes())==entry['after'];entry['published']=True
        (QA/'integration.json').write_text(dump(report),encoding='utf8')
    report.update(published=True,publishState='complete');(QA/'integration.json').write_text(dump(report),encoding='utf8')
    print(dump({'published':str(LIVE),'sha256':report['candidateSHA256'],'backup':str(backup),'stats':report['stats']}))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args();publish() if args.publish else build()
