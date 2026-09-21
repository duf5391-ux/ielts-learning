"""Check staged lesson content, preserved records and exact source mappings without a browser."""
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
from urllib.parse import unquote, urlsplit
import json,re,hashlib,subprocess
from integrate_prerequisites import BOOK,ROOT,OUT,LISTENING,sha

def run():
    path=OUT/'开始学习-reviewed.html'
    text=path.read_text(encoding='utf8');s=BeautifulSoup(text,'html.parser')
    checks=[]
    def check(name,value):
        assert value,name
        checks.append({'check':name,'result':'pass'})
    original=BeautifulSoup((BOOK/'开始学习.html').read_text(encoding='utf8'),'html.parser')
    check('Sidebar and workspace navigation unchanged',str(s.find(id='workspace-navigation'))==str(original.find(id='workspace-navigation')))
    check('All 1000 vocabulary cards lead to active use',len(s.select('.tv-card [data-prereq-word]'))==1000)
    by_field={n['data-save']:n for n in s.select('[data-save]')}
    for old in original.select('[data-save]'):
        new=by_field.get(old['data-save'])
        check('Record '+old['data-save'],new is not None and new.name==old.name and new.get('type')==old.get('type') and new.get('value')==old.get('value'))
    pdf=PdfReader(BOOK/'原始参考/8ee8170c-Cambridge IELTS 21 - Academic.pdf')
    for page,phrase in [(96,'primary schools'),(139,'Band 7'),(140,'mechanical'),(50,'framework')]:
        check(f'C21 page {page} matches new teaching citation',phrase.lower() in pdf.pages[page-1].extract_text().lower())
    for no,(name,label,qs) in LISTENING.items():
        unit=s.find(id=f'supplement-audit-{no:03}')
        check(label+' has original question boundaries',all(str(q) in unit.get_text() for q in qs))
        check(label+' has transcript in a closed disclosure',len(unit.select_one('.prereq-transcript').get_text())>300 and not unit.select_one('.prereq-transcript').has_attr('open'))
        audio=BOOK/'原始参考'/name
        check(label+' local MPEG audio is populated',audio.stat().st_size>10000 and (audio.read_bytes()[:3]==b'ID3' or audio.read_bytes()[0]==255))
    for node in s.select('.prereq-lesson,.prereq-listening'):
        for a in node.select('[href],audio[src]'):
            url=a.get('href',a.get('src',''))
            if url.startswith('#'):check('Internal link '+url,s.find(id=url[1:]) is not None)
            elif not urlsplit(url).scheme:check('Local source '+url,(BOOK/unquote(url.split('#')[0])).exists())
    for n in s.select('script'):
        if n.get('type')=='application/json' or n.get('src'):continue
        js=n.get_text()
        target=OUT/('syntax-'+sha(js)[:10]+'.js');target.write_text(js,encoding='utf8')
        result=subprocess.run(['C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe','--check',str(target)],capture_output=True,text=True)
        check('JS syntax '+str(n.get('id') or 'original script'),result.returncode==0)
    visible=' '.join(n for n in s.main.strings if n.parent.name not in ['script','style'])
    for phrase in ['本轮审核：依据','学习审查（09-19','原单元错位结论','原导读保留其待核状态','此对照入口用于后续重建','查看完整证据、版本与教学抽查']:
        check('Removed producer prose '+phrase,phrase not in visible)
    check('No visible audit badges or labels',not s.select('[data-content-audit], [data-learning-audit]'))
    check('Existing correction annotations preserved',len(s.select('.source-copy-note'))==len(original.select('.source-copy-note')))
    report={'sha256':sha(text),'result':'pass','checks':len(checks),'savedFieldChecks':len(original.select('[data-save]')),'details':checks,'limits':['Static content and script checks, not a complete browser run.','No microphone, live media playback or browser user record access.','1000 vocabulary rows are not individually certified as authentic source examples.']}
    (ROOT/'research/prerequisite-static-qa-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf8');run()
