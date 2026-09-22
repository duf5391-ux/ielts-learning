"""Guarded incremental installation; assets first, main HTML last."""
from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
m=read(ROOT/'content-pipeline/batches/jiufen-jijing-20260921/reviewed-integration.json');candidate=HERE/'combined.html';formal=BOOK/'开始学习.html'
assert sha(formal)==m['formalBaseline'],'Formal changed; stop instead of overwriting another task'
assert sha(candidate)==m['candidateSha256']
for file in ['qa-combined.json','combined-static.json','release-candidate.json']:assert read(HERE/file)['pass']
assert read(HERE/'combined-static.json')['sha256']==m['candidateSha256']
assert read(HERE/'release-candidate.json')['checks'][0]['detail']['sha256']==m['candidateSha256']
assets=m['assets']+[dict(path='开始学习.html',source=str(candidate),sha256=m['candidateSha256'])]
backup=HERE/'formal-backup';backup.mkdir(exist_ok=True);entries=[]
assert not (backup/'recovery.json').exists(),'Inspect existing installation before retry'
for a in assets:
 target=BOOK/a['path'];old=backup/a['path'];assert target.resolve().is_relative_to(BOOK.resolve()) and old.resolve().is_relative_to(backup.resolve())
 assert sha(Path(a['source']))==a['sha256']
 if target.exists():old.parent.mkdir(parents=True,exist_ok=True);assert not old.exists();shutil.copy2(target,old)
 entries.append(dict(path=a['path'],before=sha(target) if target.exists() else None,after=a['sha256']))
(backup/'recovery.json').write_text(json.dumps(dict(book=str(BOOK),files=entries),ensure_ascii=False,indent=2),encoding='utf8')
for a in assets:
 target=BOOK/a['path'];target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_name(target.name+'.architecture.tmp')
 shutil.copy2(a['source'],temp);assert sha(temp)==a['sha256'];temp.replace(target)
report={**m,'status':'installed-local-awaiting-publication','installedAt':datetime.now(timezone.utc).isoformat(),'formalPath':str(formal),'recovery':str(backup/'recovery.json')}
(HERE/'installation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'installed':str(formal),'sha256':sha(formal),'fields':m['fields'],'units':m['units']},ensure_ascii=False))
