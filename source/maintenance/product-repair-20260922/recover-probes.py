"""Retrieve the existing measurements after a local API TLS timeout; never POST."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import sys,json
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'research'))
import probe_github_publication as p
directory=ROOT/'research/github-publication-probes-20260922T001012.167979Z'
def recover(key):
    saved=json.loads((directory/(key+'.json')).read_text(encoding='utf8'))
    saved['original_client_error']=saved['client_error']
    mid=saved['creation']['id']
    result,_=p.api_json(p.API+'/v1/measurements/'+mid,timeout=20)
    saved['measurement']=result
    saved['client_error']=None
    saved['recovered_at']=datetime.now(timezone.utc).isoformat()
    p.write_json(directory/(key+'-recovered.json'),saved)
    return p.summarize(saved)
with ThreadPoolExecutor(max_workers=3) as pool:
    resources=list(pool.map(recover,['homepage','official_audio','jijing_audio']))
summary=dict(base_url='https://duf5391-ux.github.io/ielts-learning/',created_at=datetime.now(timezone.utc).isoformat(),
             scope='Same measurement IDs retrieved after original API TLS timeouts; no new probes created.',resources=resources)
p.write_json(directory/'summary-recovered.json',summary)
(directory/'report-recovered.md').write_text(p.reader_report(summary),encoding='utf8')
for r in resources:
    print(json.dumps({'key':r['key'],'status':r['measurement_status'],'CN':[dict(city=n['city'],network=n['network'],pass_=n['response_checks_passed'],issues=n['issues']) for n in r['nodes'] if n['country']=='CN']},ensure_ascii=False))
