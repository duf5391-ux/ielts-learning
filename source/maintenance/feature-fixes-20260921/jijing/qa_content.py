"""Source-to-release integrity checks; semantic review remains separate."""
import json,hashlib,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.codex-tools/jijing-libs'))
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
text=lambda s:BeautifulSoup(s or '', 'html.parser').get_text(' ',strip=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
units=read(HERE/'new-units.json')['units'];checks=[]
def check(name,fn):fn();checks.append({'name':name,'status':'pass'})
def test_snapshots():
    for m in read(HERE/'snapshot-manifest.json'):assert sha(HERE/m['snapshot'])==m['sha256']
check('Fixed local source snapshot hashes match manifest',test_snapshots)
def test_reading():
    u=units[0];part=read(HERE/u['sourceSnapshot'])['data']['parts'][0]
    pars=[n.get_text(' ',strip=True) for n in BeautifulSoup(part['article'],'html.parser').find_all('div') if re.match(r'^\([A-H]\) ',n.get_text(' ',strip=True))]
    assert u['contextParagraphs']==pars and len(pars)==8
    original={q['qNumber']:q for g in part['groups'] for q in g['questions']}
    covered=[]
    for q in u['questions']:
        n=q['originalNumber'];source=original[n if '-' not in n else n.split('-')[0]]
        assert q['prompt']==text(source['question'])
        group=next(g for g in part['groups'] if source in g['questions'])
        opts=source.get('options') or group['questions'][0]['options']
        assert q['options']==[{'label':o['optionNum'],'text':text(o.get('optionContent') or o['option'])} for o in opts]
        covered+=q['sourceQuestionIds']
    assert set(covered)=={q['id'] for q in original.values()} and len(covered)==14
    assert all(q.get('rightAnswer') is None for q in original.values())
    assert len(u['answers'])==12
    for a,q in zip(u['answers'],u['questions']):
        assert a['id']==q['id']
        letters=re.findall(r'\b[A-H]\b',a['answer']);assert len(letters)==(3 if q['responseType']=='three-letters' else 1)
        assert all(letter in [o['label'] for o in q['options']] for letter in letters)
        assert a['evidenceParagraphs'] and a['explanation']
check('Full reading paragraphs, prompts, shared options and all 14 source identities preserved; multi-answer group explicit',test_reading)
def test_writing():
    for u in units[1:]:
        part=read(HERE/u['sourceSnapshot'])['data']['parts'][0]
        art=json.loads(part['articleJson'])
        assert u['promptParagraphs']==[' '.join(s['text'] for s in seg['sentences']) for seg in art['segments']]
        assert u['instructions']==part['description']
        assert u['supplement']==part['groups'][0]['supplementPrompt2']
        assert len(u['rubric'])==4 and u['closeReadingHtml']
check('Three Task 2 prompts, time/word instructions and supplementary directions match downloaded source',test_writing)
def test_actual_new():
    pub=read(ROOT/'content-pipeline/batches/jijing-20260920/publication.json');page=Path(pub['formal_path']).read_text(encoding='utf-8')
    # May be called after integration; exclude this owned batch before checking.
    page=re.sub(r'<!--JIJING-UPDATE-20260921:[^>]+-->.*?<!--/JIJING-UPDATE-20260921-->','',page,flags=re.S)
    for u in units:
        phrase=u['contextIntroduction'] if u['skill']=='reading' else u['promptParagraphs'][0]
        assert phrase.lower() not in page.lower(), 'Duplicates pre-existing material: '+u['id']
check('All four material bodies are absent from the pre-existing book',test_actual_new)
def test_difficulty():
    d=read(HERE/'difficulty.json');assert len(d['items'])==15
    for u in units:assert u['difficulty']==d['items'][u['id']]
    assert {v['level'] for v in d['items'].values()}=={2,3,4}
    for v in d['items'].values():assert v['reason'] and v['dimensions'] and v['officialBand'] is None and v['learnerMastery'] is None
check('All 15 published/referenced items have individually reasoned editorial difficulty; no official band/mastery score',test_difficulty)
report={'checks':checks,'passed':len(checks),'newUnitSha256':sha(HERE/'new-units.json'),'difficultySha256':sha(HERE/'difficulty.json'),'semanticReview':'Separate independent agent read-through; this script checks source integrity, not correctness by itself.'}
(HERE/'content-integrity-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
