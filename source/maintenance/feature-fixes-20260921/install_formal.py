"""Install only the reviewed incremental candidate, retaining a cross-file backup."""
from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((HERE/'candidate-manifest.json').read_text())
formal=BOOK/'开始学习.html'; candidate=HERE/'candidate.html'
assert sha(formal)==manifest['source_sha256'],'Formal source changed; regenerate and revalidate before installation'
assert sha(candidate)==manifest['candidate_sha256'],'Candidate changed after review'
backup=HERE/'formal-backup';backup.mkdir(exist_ok=True)
entries=[]
for asset in manifest['assets']+[{'source':str(candidate),'path':'开始学习.html','sha256':manifest['candidate_sha256']}]:
    source=Path(asset['source']); target=BOOK/asset['path'];old=backup/asset['path']
    assert target.resolve().is_relative_to(BOOK.resolve()) and old.resolve().is_relative_to(backup.resolve())
    assert sha(source)==asset['sha256']
    if target.exists():
        assert not old.exists(),'Backup already exists: inspect prior installation'
        old.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,old)
    entries.append({'path':asset['path'],'before':sha(target) if target.exists() else None,'after':asset['sha256']})
(backup/'recovery.json').write_text(json.dumps({'book':str(BOOK),'files':entries},ensure_ascii=False,indent=2),encoding='utf8')
# Assets first and HTML last; one-file replaces are not a cross-file transaction.
for asset in manifest['assets']+[{'source':str(candidate),'path':'开始学习.html','sha256':manifest['candidate_sha256']}]:
    target=BOOK/asset['path'];target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.feature-fix.tmp');shutil.copy2(asset['source'],temp);assert sha(temp)==asset['sha256'];temp.replace(target)
result={**manifest,'installed_at':datetime.now(timezone.utc).isoformat(),'formal_path':str(formal),'backup':str(backup),'installed_sha256':sha(formal)}
(HERE/'installation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'installed':str(formal),'sha256':sha(formal),'save_fields':manifest['save_fields'],'units':manifest['units']}))
