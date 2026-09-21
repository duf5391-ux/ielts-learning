"""Publish a bounded maintenance snapshot, never browser data or credentials."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'source-publication' / 'source'
EXPECTED = '2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85'
manifest = []

def copy(src, relative, role):
    data = src.read_bytes()
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    manifest.append(dict(path=str(relative).replace('\\', '/'), bytes=len(data),
                         sha256=hashlib.sha256(data).hexdigest(), role=role))

baseline = ROOT / 'ui-repair-20260921/baseline.html'
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == EXPECTED
copy(baseline, Path('production/开始学习.html'), 'current-production-source')
for f in (ROOT / 'ui-repair-20260921/source').iterdir():
    if f.is_file():
        copy(f, Path('production/extracted') / f.name, 'current-production-extract')

extensions = {'.py', '.js', '.cjs', '.css', '.json', '.ps1', '.md', '.html'}
for f in ROOT.iterdir():
    if f.is_file() and f.suffix in extensions and f.stat().st_size < 3_000_000:
        copy(f, Path('maintenance') / f.name, 'maintenance-history-not-all-current')

excluded_parts = {'stage', 'site', 'dist', 'backup', 'backups', 'formal-backup',
                  'baseline', 'source-snapshot', '__pycache__', 'node_modules', '.git'}
for directory in ['content-pipeline', 'feature-fixes-20260921']:
    for f in (ROOT / directory).rglob('*'):
        if (f.is_file() and f.suffix in extensions and f.stat().st_size < 3_000_000
                and not excluded_parts.intersection(f.relative_to(ROOT).parts)):
            copy(f, Path('maintenance') / f.relative_to(ROOT), 'maintenance-history-not-all-current')

for name in ['prepare.py', 'package.py', 'dictionary-web-loader.js',
             'extra-resources.json', 'README.md', 'check-dictionary.cjs']:
    copy(ROOT / 'web-publication' / name, Path('maintenance/web-publication') / name, 'build-tool')

for directory in ['interface-map-20260921', 'ui-route-probe-20260921']:
    for f in (ROOT / 'research' / directory).rglob('*'):
        if f.is_file() and 'failure' not in f.name:
            copy(f, Path('maintenance/research') / f.relative_to(ROOT / 'research'), 'probe-evidence')
for f in (ROOT / 'research').iterdir():
    if f.is_file() and (f.suffix in {'.py', '.cjs'} or f.name in {
        'ui-experience-audit-20260921.md', 'ui-structure-probe-20260921.md',
        'work-progress-audit-20260921.md', 'feature-fixes-delivery-20260921.md',
        'github-pages-migration-status.json', 'mobile-workspace-delivery-20260921.md',
        'material-reading-delivery-20260920.md', 'health-interaction-delivery-20260920.md'}):
        copy(f, Path('maintenance/research') / f.name, 'audit-or-probe-tool')

for name in ['lookup-controller.js', 'vocabulary-review-controller.js']:
    copy(ROOT / 'ui-repair-20260921' / name, Path('drafts') / name, 'untested-draft-do-not-deploy')

# Report only file names on a match, never credential contents.
secret_patterns = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{40,}',
                   r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                   r'AKIA[0-9A-Z]{16}']
hits = []
for row in manifest:
    f = DEST / row['path']
    if f.suffix in extensions or f.suffix == '.txt':
        text = f.read_text(encoding='utf-8', errors='replace')
        if any(re.search(p, text) for p in secret_patterns):
            hits.append(row['path'])
assert not hits, 'Possible credential in: ' + ', '.join(hits)
(DEST / 'manifest.json').write_text(json.dumps(dict(
    production_sha256=EXPECTED, base_commit='46bc80bc1d77638f019f58a2c39bfed65a99c19e',
    files=manifest, exclusions=['credentials, browser profiles, personal learning records',
    'downloaded tool repositories, archives, duplicate media, unrelated projects',
    'historical full-page candidates and failed probe selector attempts']),
    ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(manifest), bytes=sum(x['bytes'] for x in manifest),
                     credential_pattern_matches=len(hits)), ensure_ascii=False))
