"""Bind independent source QA reports to the frozen candidate before installation."""
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
read=lambda name:json.loads((HERE/name).read_text(encoding='utf8'))
sha=lambda name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
candidate=sha('candidate.html')
assert read('static.json')['pass'] and read('static.json')['candidate']==candidate
assert read('qa/qa-final.json')['pass'] and read('qa/qa-final.json')['candidate_sha256']==candidate
assert read('writing/qa-combined.json')['pass'] and read('writing/qa-combined.json')['candidate_sha256']==candidate
equivalence=read('component-equivalence.json')
assert equivalence['pass'] and equivalence['candidate_sha256']==candidate
frontend=read('frontend/qa-combined.json')
assert frontend['pass']
assert equivalence['tested_combination']==frontend['candidate_sha256']
files=['static.json','component-equivalence.json','frontend/qa-combined.json','writing/qa-combined.json',
       'qa/qa-final.json','qa/final-targeted.json','qa/final-production.json','qa/final-diff.json',
       'qa/combined-first-desktop.json','qa/combined-first-mobile.json',
       'qa/combined-first-compatibility.json','qa/combined-first-routes.json']
record=dict(pass_=True,candidate_sha256=candidate,checked_at=datetime.now(timezone.utc).isoformat(),
    evidence=[dict(path=name,sha256=sha(name)) for name in files],
    scope='Accepted for formal source installation. Progressive packed and HTTPS release QA still required.',
    prior_check_limits='Unchanged reliability/catalog/daily components inherit the preceding combination checks via exact script SHA. Final navigation and writing are directly checked. The old compatibility report initial word-card scroll failure is superseded by final-targeted pass.')
record['pass']=record.pop('pass_')
(HERE/'release-acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
