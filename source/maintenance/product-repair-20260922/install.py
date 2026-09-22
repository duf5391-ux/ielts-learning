"""Install only the exact accepted candidate, keeping the prior workbook for recovery."""
from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone
from build import FORMAL,EXPECTED

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
candidate=HERE/'candidate.html'
static=read(HERE/'static.json')
accepted=read(HERE/'release-acceptance.json')
assert sha(FORMAL)==EXPECTED, 'Formal changed; stop and reconcile before installing'
assert static['pass'] and accepted['pass']
assert sha(candidate)==static['candidate']==accepted['candidate_sha256']
for check in accepted['evidence']:
    p=HERE/check['path']
    assert p.exists() and sha(p)==check['sha256'], str(p)
backup=HERE/'formal-backup';backup.mkdir(exist_ok=True)
assert not (backup/'recovery.json').exists(), 'Inspect earlier installation before retry'
shutil.copy2(FORMAL,backup/FORMAL.name)
record=dict(formal=str(FORMAL),before=EXPECTED,after=sha(candidate),backup=str(backup/FORMAL.name),installed_at=datetime.now(timezone.utc).isoformat(),assets='Existing linked assets unchanged; this release changes only the main HTML')
(backup/'recovery.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
tmp=FORMAL.with_name(FORMAL.name+'.product-20260922.tmp')
shutil.copy2(candidate,tmp)
assert sha(tmp)==record['after']
tmp.replace(FORMAL)
(HERE/'installation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
