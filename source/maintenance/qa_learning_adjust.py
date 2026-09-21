from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import unquote,urlparse
import json,hashlib,re,subprocess,sys

ROOT=Path(__file__).resolve().parent
OUT=Path('D:/IELTS-Work/learning-adjust-20260920')
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
BASE=Path('D:/IELTS-Backups/2026-09-20_133954-before-learning-adjust/original-project/outputs/IELTS-四科学习册/开始学习.html')
NODE=Path('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')

def run():
    raw=(OUT/'开始学习-adjusted.html').read_bytes();s=BeautifulSoup(raw.decode('utf8'),'html.parser');old=BeautifulSoup(BASE.read_text(encoding='utf8'),'html.parser')
    checks=[]
    def check(name,condition,detail=None):
        checks.append({'check':name,'pass':bool(condition),'detail':detail});assert condition,(name,detail)
    ids=[x['id'] for x in s.select('[id]')];idmap={x['id']:x for x in s.select('[id]')};fields={x['data-save']:x for x in s.select('[data-save]')}
    check('Unique IDs',len(ids)==len(set(ids)))
    check('Unique saved fields',len(fields)==len(s.select('[data-save]')))
    check('All existing save keys retained',{x['data-save'] for x in old.select('[data-save]')}<=set(fields))
    for selector in ['[data-record]','[data-stop]','[data-upload]','[data-download]','[data-case-done]','.exam-case','.tv-card']:
        check('Preserve '+selector,len(s.select(selector))>=len(old.select(selector)))
    check('Five primary entries',[x['data-go'] for x in s.select('#workspace-navigation [data-go]')]==['guide','study','practice','tests','workspace'])
    data=json.loads(s.find(id='learning-adjust-data').string)
    check('One catalog entry per activity',len(data['units'])==len({u['id'] for u in data['units']}))
    for u in data['units']:
        check('Reachable activity '+u['id'],u['id'] in idmap and idmap[u['id']].find_parent('main') is not None)
        check('Nonempty denominator '+u['id'],len(u['steps'])>0)
        check('Progress keys '+u['id'],all(x['key'] in fields for x in u['steps']))
        check('Progress excludes favorites '+u['id'],not any('star-' in x['key'] or 'bookmark' in x['key'] for x in u['steps']))
    for d in s.select('[data-answer-gate]'):
        keys=json.loads(d['data-answer-gate']);check('Gate prerequisites '+d['id'],len(keys)>0 and all(k in fields for k in keys))
        check('Gate feedback initially concealed '+d['id'],'open' not in d.attrs and d.select_one('.la-gate-content').has_attr('hidden'))
        check('Answers are outside own feedback '+d['id'],all(fields[k] not in d.select('.la-gate-content [data-save]') for k in keys))
    for skill,expected in [('reading',40),('listening',40),('writing',2),('speaking',3)]:
        values=s.select('[data-test-answer="'+skill+'"]');check('Complete '+skill+' answer sheet',len(values)==expected)
        check('Unique question numbers '+skill,len({x['data-question'] for x in values})==expected)
        check('Submission starts hidden '+skill,s.select_one('#test-'+skill+' .la-test-result').has_attr('hidden'))
    check('Reading answer key complete',len(data['tests']['reading']['key'])==40)
    check('Listening partial key clearly labelled',len(data['tests']['listening']['key'])==16 and '24' in data['tests']['listening']['note'])
    check('Fisheries reading separate',idmap['pr-background-fisheries'].find_parent(id='practice-reading') is not None)
    check('Fisheries writing separate',idmap['pr-fisheries-writing'].find_parent(id='practice-writing2') is not None)
    check('Phrase section separate',idmap['usage-cards'].find_parent(id='phrases') is not None)
    for ident,owner in [('topic-education','writing2'),('topic-work','speaking'),('topic-space','practice-listening'),('topic-government','practice-reading')]:check(ident+' belongs to '+owner,idmap[ident].find_parent(id=owner) is not None)
    oldlinks={a['href'] for a in old.select('a[href^="#"]')};broken=[]
    for a in s.select('a[href^="#"]'):
        h=unquote(a['href'][1:]);
        if h and h not in idmap and a['href'] not in oldlinks:broken.append(h)
    check('No new broken internal links',not broken,broken)
    missing=[]
    for n in s.select('img[src],audio[src],source[src]'):
        src=unquote(n['src']);p=urlparse(src)
        if p.scheme or src.startswith('//'):continue
        local=OUT/p.path if p.path.startswith('learning-assets/') else BOOK/p.path
        if not local.is_file():missing.append(src)
    check('Local media available',not missing,missing)
    scriptout=OUT/'checked-scripts';scriptout.mkdir(exist_ok=True)
    for i,n in enumerate(s.find_all('script')):
        if n.get('src') or n.get('type') in ['application/json','application/ld+json']:continue
        file=scriptout/f'{i}.js';file.write_text(n.string or n.get_text(),encoding='utf8')
        result=subprocess.run([str(NODE),'--check',str(file)],capture_output=True,text=True)
        check('JavaScript syntax '+str(i),result.returncode==0,result.stderr.strip())
    report={'sha256':hashlib.sha256(raw).hexdigest(),'checks':len(checks),'passed':sum(x['pass'] for x in checks),'browserEndToEnd':False,'checksDetail':checks}
    (ROOT/'research/learning-adjust-static-qa-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:report[k] for k in ['sha256','checks','passed','browserEndToEnd']}));return report
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');run()
