from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import unquote
from collections import Counter
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent
STAGE=Path('D:/IELTS-Work/learning-adjust-20260920')
LIVE=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
p=STAGE/'开始学习-ui-final.html';raw=p.read_bytes();s=BeautifulSoup(raw.decode('utf8'),'html.parser');old=BeautifulSoup(LIVE.read_text(encoding='utf8'),'html.parser')
ids={n['id'] for n in s.select('[id]')};checks=[]
def check(name,passed,detail=None):checks.append(dict(name=name,passed=bool(passed),detail=detail))
missing=sorted({a['href'] for a in s.select('a[href]') if a['href'].startswith('#') and len(a['href'])>1 and unquote(a['href'][1:]) not in ids})
check('All local anchor links resolve',not missing,missing)
fields=lambda tree:Counter(n['data-save'] for n in tree.select('[data-save]'))
check('All current live fields retained once',not(fields(old)-fields(s)) and all(v==1 for v in fields(s).values()),{'live':sum(fields(old).values()),'new':sum(fields(s).values())})
missing_media=[]
for n in s.select('img[src],audio[src],source[src]'):
    src=n['src']
    if src.startswith(('data:','http:','https:','blob:')):continue
    local=unquote(src.split('#')[0].split('?')[0])
    if not (LIVE.parent/local).exists() and not (STAGE/local).exists():missing_media.append(src)
check('Every local image/audio source is present',not missing_media,sorted(set(missing_media)))
for mark in ['home','style','state','scripts']:
    check('Daily module markers preserved: '+mark,raw.count(('<!--DAILY-STUDY-V1:'+mark+'-->').encode())==1 and raw.count(('<!--/DAILY-STUDY-V1:'+mark+'-->').encode())==1)
data=json.loads(s.find(id='learning-adjust-data').string);bad=[];saved_fields=fields(s)
for u in data['units']:
    for step in u['steps']:
        if step['kind']!='checked' and step['key'] not in saved_fields:bad.append([u['id'],step['key']])
check('All progress steps refer to a saved control',not bad,bad)
check('Workspace includes writing, records, courses, materials, sources, selection, words and sentences',len(s.select('#workspace .la-workspace-grid>.la-card'))==8)
check('Responsive breakpoints and hidden navigation controls are defined',all(x in s.find(id='navigation-ui-final-style').string for x in ['max-width:600px','max-width:1000px','label[hidden]','[data-la-focus-hidden]']))
out={'source':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'passed':sum(c['passed'] for c in checks),'total':len(checks),'visualBrowserCheck':False}
(ROOT/'research/navigation-ui-static-20260920.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
sys.stdout.reconfigure(encoding='utf8');print(json.dumps(out,ensure_ascii=False,indent=2));sys.exit(0 if out['passed']==out['total'] else 1)
