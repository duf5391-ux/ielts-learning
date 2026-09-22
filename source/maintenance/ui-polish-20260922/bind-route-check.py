from pathlib import Path
from hashlib import sha256
import json
p=Path(__file__).resolve().parent
raw=(p/'candidate.html').read_bytes().decode('utf8')
new="(old && old.count>0 && (old.lastAt||old.firstAt) ? [{at:old.lastAt || old.firstAt,context:old.context || '',legacy:true}] : [])"
old="(old ? [{at:old.lastAt || old.firstAt || now,context:old.context || '',legacy:true}] : [])"
expected='7b0eff16e66cef3d8c3a4389ae1b1542f1b99e1d62fbd1c15ace8590b504d2aa'
prior=sha256(raw.replace(new,old).encode()).hexdigest()
q=json.loads((p.parent/'product-repair-20260922/qa/ui-polish-20260922-routes.json').read_text(encoding='utf8'))
assert q['pass'] and prior==expected,(prior,expected)
report={'pass':True,'tested':expected,'final':sha256(raw.encode()).hexdigest(),'routes':len(q['routes']),'only_difference':'Lookup legacy-history fallback skips undated studied rows. Route markup, IDs, owners and route controllers unchanged.'}
(p/'route-binding.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(p/'legacy-routes.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report))
