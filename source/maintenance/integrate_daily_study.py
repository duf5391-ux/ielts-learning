"""Add the daily entry without rebuilding either the live book or frozen navigation v2."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
import argparse, hashlib, json, re, shutil, sys

ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
LIVE=BOOK/'开始学习.html'
NAV=Path('D:/IELTS-Work/learning-adjust-20260920/开始学习-navigation-v2.html')
QA=ROOT/'daily-study-qa'
MARK='DAILY-STUDY-V1'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def block(name,text):return f'<!--{MARK}:{name}-->\n{text}\n<!--/{MARK}:{name}-->'
def clean(html):return re.sub(r'<!--DAILY-STUDY-V1:([\w-]+)-->.*?<!--/DAILY-STUDY-V1:\1-->','',html,flags=re.S)

def build(source,target):
    raw=source.read_bytes();original=raw.decode('utf8');html=clean(original)
    before=BeautifulSoup(html,'html.parser')
    assert before.find(id='guide') and before.select('main > .panel')
    catalog=json.loads((ROOT/'daily-study-catalog.json').read_text(encoding='utf8'))
    missing=[]
    for item in catalog:
        for stage in item['stages']:
            for ident in ([stage['target']] if isinstance(stage['target'],str) else stage['target'].values()):
                if not before.find(id=ident):missing.append(ident)
    assert not missing,f'Missing material targets: {missing}'
    home=block('home',(ROOT/'daily-study.html').read_text(encoding='utf8'))
    html,n=re.subn(r'(<section\b[^>]*\bid=[\"\']guide[\"\'][^>]*>)',lambda m:m[1]+home,html,count=1)
    assert n==1
    html=html.replace('</head>',block('style','<style id="daily-study-style">'+(ROOT/'daily-study.css').read_text(encoding='utf8')+'</style>')+'</head>',1)
    html=html.replace('</main>',block('state','<input type="hidden" id="daily-study-state" data-save="daily-study-state">')+'</main>',1)
    data=json.dumps(catalog,ensure_ascii=False).replace('</','<\\/')
    scripts='<script id="daily-study-catalog" type="application/json">'+data+'</script>'
    for filename in ['daily-study-model.js','daily-study.js']:
        text=(ROOT/filename).read_text(encoding='utf8');assert '</script' not in text.lower()
        scripts+=f'<script id="{filename[:-3]}-script">\n{text}\n</script>'
    html=html.replace('</body>',block('scripts',scripts)+'</body>',1)
    after=BeautifulSoup(html,'html.parser')
    counts=lambda s:Counter(n['data-save'] for n in s.select('[data-save]'))
    old_fields,new_fields=counts(before),counts(after)
    assert not old_fields-new_fields
    assert new_fields-old_fields==Counter({'daily-study-state':1})
    old_media=Counter((n.name,n.get('src')) for n in before.select('img,audio,source') if n.get('src'))
    new_media=Counter((n.name,n.get('src')) for n in after.select('img,audio,source') if n.get('src'))
    assert old_media==new_media
    assert [str(n) for n in before.select('script')]==[str(n) for n in after.select('script:not([id^="daily-study-"])')]
    # Stripping our marked insertions reproduces the base source byte-for-byte.
    assert clean(html)==clean(original)
    ids=Counter(n['id'] for n in after.select('[id]'))
    assert all(count==1 for ident,count in ids.items() if ident.startswith(('ds-','daily-study-')))
    output=html.encode('utf8');target.write_bytes(output)
    return {'source':str(source),'target':str(target),'sourceSHA256':sha(raw),'sha256':sha(output),'originalFields':sum(old_fields.values()),'addedFields':['daily-study-state'],'allOriginalBytesPreserved':True,'allOriginalScriptsPreserved':True,'allOriginalMediaPreserved':True,'materialTargetsVerified':True}

def run(publish=False):
    QA.mkdir(exist_ok=True)
    if publish:
        report=json.loads((QA/'integration.json').read_text(encoding='utf8'))
        item=report['live'];staged=Path(item['target'])
        assert sha(staged.read_bytes())==item['sha256'],'Staged file changed; validate before publishing'
        assert sha(LIVE.read_bytes())==item['sourceSHA256'],'Live book changed; rebuild without overwriting concurrent work'
        checked=json.loads((QA/'browser-results.json').read_text(encoding='utf8'))
        assert checked['sourceSHA256']==item['sha256'] and checked['passed']==checked['total'] and checked['total']>=10,'Browser checks must pass for this exact candidate'
        backup=QA/('开始学习-before-daily-'+item['sourceSHA256'][:12]+'.html')
        if not backup.exists():shutil.copy2(LIVE,backup)
        assert sha(backup.read_bytes())==item['sourceSHA256']
        LIVE.write_bytes(staged.read_bytes());report['published']=True;report['backup']=str(backup)
        (QA/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps({'published':str(LIVE),'sha256':sha(LIVE.read_bytes()),'backup':str(backup)},ensure_ascii=False));return
    live=build(LIVE,QA/'开始学习-daily.html')
    nav=build(NAV,NAV.with_name('开始学习-navigation-v3-daily.html'))
    report={'live':live,'navigation':nav,'published':False,'candidateContentAuditStillRequired':True}
    (QA/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');run(p.parse_args().publish)
