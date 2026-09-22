"""Read the same existing measurements; never create another probe request."""
import json,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import probe_github_publication as probe
ROOT=Path(__file__).resolve().parent
folder=ROOT/'github-publication-probes-20260921T141958.277540Z'
# Existing system proxy verified by the root task; affects API retrieval only.
# The remote mainland nodes themselves still make direct site requests.
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({'http':'http://127.0.0.1:10808','https':'http://127.0.0.1:10808'})))
def recover(key):
 p=folder/(key+'.json');saved=json.loads(p.read_text(encoding='utf8'))
 result,_=probe.api_json(probe.API+'/v1/measurements/'+saved['creation']['id'])
 saved['originalClientError']=saved['client_error'];saved['measurement']=result;saved['client_error']=None
 probe.write_json(folder/(key+'-recovered.json'),saved);return saved
with ThreadPoolExecutor(max_workers=3) as pool:saved=list(pool.map(recover,['homepage','official_audio','jijing_audio']))
summary={'base_url':'https://duf5391-ux.github.io/ielts-learning/','created_at':datetime.now(timezone.utc).isoformat(),'scope':'Same measurements recovered after API TLS error; node access spans publication and is not version fingerprint evidence','resources':[probe.summarize(x) for x in saved]}
probe.write_json(folder/'summary-recovered.json',summary);(folder/'report-recovered.md').write_text(probe.reader_report(summary),encoding='utf8')
print(json.dumps([{'resource':r['key'],'status':r['measurement_status'],'CNnodes':len([n for n in r['nodes'] if n['country']=='CN']),'CNpassed':sum(n['response_checks_passed'] for n in r['nodes'] if n['country']=='CN'),'errors':[{'city':n['city'],'error':n['error']} for n in r['nodes'] if n['country']=='CN' and not n['response_checks_passed']]} for r in summary['resources']],ensure_ascii=False))
