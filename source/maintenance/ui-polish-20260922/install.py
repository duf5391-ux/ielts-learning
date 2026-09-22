from pathlib import Path
from hashlib import sha256
import json, shutil, os
from datetime import datetime,timezone
P=Path(__file__).resolve().parent
formal=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
b=json.loads((P/'build.json').read_text(encoding='utf8'));q=json.loads((P/'verification.json').read_text(encoding='utf8'))
assert q['pass'] and q['source_sha256']==b['candidate']
assert sha256(formal.read_bytes()).hexdigest()==b['baseline'],'Formal changed: reconcile before installation'
assert sha256((P/'candidate.html').read_bytes()).hexdigest()==b['candidate']
backup=P/'formal-backup';backup.mkdir(exist_ok=True)
shutil.copy2(formal,backup/'开始学习.html')
staged=formal.with_name('开始学习.ui-polish-staged.html');shutil.copy2(P/'candidate.html',staged)
assert sha256(formal.read_bytes()).hexdigest()==b['baseline']
os.replace(staged,formal)
record={**b,'formalPath':str(formal),'backup':str(backup/'开始学习.html'),'installedAt':datetime.now(timezone.utc).isoformat(),'verification':'verification.json'}
(P/'installation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
