"""One explicit recheck of failed CN city/ASN pairs; retain the first result."""
from pathlib import Path
import sys,json
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
import probe_github_publication as probe
first=ROOT/'research/github-publication-probes-20260921T085742.957014Z/summary.json'
previous=json.loads(first.read_text(encoding='utf8'))
plan=probe.request_plan(previous['base_url']); original={x['key']:x for x in previous['resources']}
retry=[]
for resource in plan:
    resource['request']['locations']=[{'country':'CN','city':n['city'],'asn':n['asn'],'limit':1} for n in original[resource['key']]['nodes'] if n['country']=='CN' and not n['response_checks_passed']]
    if resource['request']['locations']:retry.append(resource)
out=ROOT/'research'/('github-publication-retry-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir()
with ThreadPoolExecutor(max_workers=3) as pool: saved=list(pool.map(lambda r:probe.measure(r,out,2,90),retry))
summary={'base_url':previous['base_url'],'created_at':datetime.now(timezone.utc).isoformat(),'first_result':str(first),'scope':'One retry of failed city/ASN pairs; not necessarily the same physical probes. First failures remain valid evidence.','resources':[probe.summarize(x) for x in saved]}
probe.write_json(out/'summary.json',summary)
(out/'report.md').write_text(probe.reader_report(summary),encoding='utf8')
print(json.dumps({'output':str(out),'resources':[{'key':x['key'],'passed':sum(n['response_checks_passed'] for n in x['nodes']),'nodes':len(x['nodes'])} for x in summary['resources']]}))
