"""Incremental health/navigation/storage fixes against the current formal book.

Builds a reviewed candidate; publication checks the exact base and browser QA hash.
Never restores a previous full-page build.
"""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
import argparse, hashlib, importlib.util, json, re, shutil, subprocess

ROOT=Path(__file__).resolve().parent
LIVE=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
QA=ROOT/'health-interaction-qa'
TARGET=QA/'candidate.html'
REPORT=QA/'integration.json'
SOURCE_FILES=['energy-control.js','health-study-bridge.js','health-study-ui.js','health-study-ui.css','record-concurrency-model.js','record-concurrency-patch.py']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def replace_script(html,ident,code):
    pattern=r'(<script\b[^>]*\bid=["\']'+re.escape(ident)+r'["\'][^>]*>).*?(</script>)'
    result,count=re.subn(pattern,lambda m:m[1]+'\n'+code.rstrip()+'\n'+m[2],html,flags=re.S)
    assert count==1,(ident,count)
    return result
def validate(original,html):
    a,b=BeautifulSoup(original,'html.parser'),BeautifulSoup(html,'html.parser')
    fields=lambda s:Counter(n['data-save'] for n in s.select('[data-save]'))
    assert fields(a)==fields(b),'Saved controls changed'
    assert all(v==1 for v in fields(b).values()),'Duplicate saved controls'
    ids=lambda s:Counter(n['id'] for n in s.select('[id]'))
    assert ids(a)<=ids(b),'Existing route removed'
    assert all(v==1 for v in ids(b).values()),'Duplicate IDs'
    media=lambda s:Counter((n.name,n.get('src'),n.get('href')) for n in s.select('audio,source,img,link[href]'))
    assert media(a)==media(b),'Media changed'
    unchanged=['workspace-navigation','daily-study-home','daily-study-style','daily-study-state','daily-study-catalog','daily-study-model-script','daily-study-script','learning-adjust-data','learning-adjust-script']
    for ident in unchanged:assert str(a.find(id=ident))==str(b.find(id=ident)),ident
    for marker in ['home','style','state','scripts']:
        assert original.count('DAILY-STUDY-V1:'+marker)==html.count('DAILY-STUDY-V1:'+marker)==2,marker
    checked=0
    scripts_dir=QA/'syntax';scripts_dir.mkdir(parents=True,exist_ok=True)
    for i,s in enumerate(b.find_all('script')):
        if s.get('src') or s.get('type') in ['application/json','application/ld+json']:continue
        file=scripts_dir/f'{i}.js';file.write_text(s.get_text(),encoding='utf8')
        subprocess.run(['node','--check',str(file)],check=True,capture_output=True)
        checked+=1
    return {'savedFields':sum(fields(b).values()),'allOriginalFieldsPreserved':True,'allOriginalIdsPreserved':True,'mediaPreserved':True,'dailyModulePreserved':True,'executableScriptsChecked':checked}
def build(source):
    QA.mkdir(parents=True,exist_ok=True)
    raw=source.read_bytes();html=original=raw.decode('utf8')
    installed='health-study-ui-script' in html
    spec=importlib.util.spec_from_file_location('record_concurrency_patch',ROOT/'record-concurrency-patch.py')
    patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    if 'record-concurrency-model-script' not in html:html=patch.patch_html(html)
    html=replace_script(html,'energy-control-script',(ROOT/'energy-control.js').read_text(encoding='utf8'))
    style='<style id="health-study-ui-style">\n'+(ROOT/'health-study-ui.css').read_text(encoding='utf8')+'\n</style>'
    if installed:
        html,count=re.subn(r'<style\b[^>]*\bid=["\']health-study-ui-style["\'][^>]*>.*?</style>',lambda m:style,html,flags=re.S)
        assert count==1,'Expected one installed health style'
    else:html=html.replace('</head>',style+'\n</head>',1)
    scripts='\n'.join('<script id="'+ident+'">\n'+(ROOT/file).read_text(encoding='utf8')+'\n</script>' for ident,file in [('health-study-bridge-script','health-study-bridge.js'),('health-study-ui-script','health-study-ui.js')])
    assert html.count('</body>')==1
    if installed:
        for ident,file in [('health-study-bridge-script','health-study-bridge.js'),('health-study-ui-script','health-study-ui.js')]:
            html=replace_script(html,ident,(ROOT/file).read_text(encoding='utf8'))
    else:html=html.replace('</body>',scripts+'\n</body>',1)
    checks=validate(original,html)
    output=html.encode('utf8');TARGET.write_bytes(output)
    assert sha(source.read_bytes())==sha(raw),'Source changed during build'
    report={'source':str(source),'baseSHA256':sha(raw),'candidate':str(TARGET),'sha256':sha(output),'sources':{f:sha((ROOT/f).read_bytes()) for f in SOURCE_FILES},'checks':checks,'published':False}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
def publish():
    r=json.loads(REPORT.read_text(encoding='utf8'))
    qa=json.loads((QA/'browser-results.json').read_text(encoding='utf8'))
    assert qa['sha256']==r['sha256'] and qa['passed'] and not qa.get('failures'),'Candidate browser QA missing or failed'
    assert Path(r['source']).resolve()==LIVE.resolve(),'Only a candidate based on the latest formal book can be published'
    assert sha(TARGET.read_bytes())==r['sha256']
    assert sha(LIVE.read_bytes())==r['baseSHA256'],'Formal book changed; rebuild and retest the incremental candidate'
    for f,h in r['sources'].items():assert sha((ROOT/f).read_bytes())==h,'Source changed: '+f
    backup=Path('D:/IELTS-Backups/2026-09-20-health-interactions');backup.mkdir(parents=True,exist_ok=True)
    previous=backup/('开始学习-before-health-'+r['baseSHA256'][:12]+'.html')
    if not previous.exists():shutil.copy2(LIVE,previous)
    assert sha(previous.read_bytes())==r['baseSHA256']
    temporary=LIVE.with_name('开始学习-health-'+r['sha256'][:12]+'.tmp')
    temporary.write_bytes(TARGET.read_bytes());assert sha(temporary.read_bytes())==r['sha256']
    assert sha(LIVE.read_bytes())==r['baseSHA256'];temporary.replace(LIVE)
    assert sha(LIVE.read_bytes())==r['sha256']
    r.update(published=True,backup=str(previous),live=str(LIVE))
    REPORT.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    return r
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=LIVE);ap.add_argument('--publish',action='store_true');args=ap.parse_args()
    print(json.dumps(publish() if args.publish else build(args.source),ensure_ascii=False,indent=2))
