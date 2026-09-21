"""Check the bytes a fresh Git checkout receives, without touching user records."""
from pathlib import Path
import hashlib
import json
import subprocess
import tarfile

root = Path(__file__).resolve().parents[1]
repo = root / 'github-publication'
manifest = json.loads((repo / 'manifest.json').read_text(encoding='utf-8'))
expected = {'site/' + item['path']: item for item in manifest['files']}
seen = set()
process = subprocess.Popen(['git', '-C', str(repo), 'archive', 'HEAD'], stdout=subprocess.PIPE)
try:
    with tarfile.open(fileobj=process.stdout, mode='r|') as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith('site/'):
                continue
            item = expected[member.name]
            with archive.extractfile(member) as stream:
                checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
            if member.size != item['bytes'] or checksum != item['sha256']:
                raise ValueError('Committed asset bytes changed: ' + member.name)
            seen.add(member.name)
    if process.wait() != 0 or seen != set(expected):
        raise ValueError('Git archive incomplete')
finally:
    process.stdout.close()
    if process.poll() is None:
        process.terminate()
commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
report = {'status': 'passed', 'commit': commit, 'checked_files': len(seen),
          'note': 'All site assets archived from the Git commit match the prepared SHA-256 inventory.'}
(root / 'research/github-committed-assets-20260921.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
