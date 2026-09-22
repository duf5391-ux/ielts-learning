"""Bind completed QA evidence to this exact candidate before local publication."""
import json
from pathlib import Path
import prepare_mobile_media as media

stage = media.STAGE
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
manifest = read(stage / 'manifest.json')
digest = media.sha((stage / '开始学习.html').read_bytes())
assert digest == manifest['candidate_sha256']
assert media.sha((media.BOOK / '开始学习.html').read_bytes()) == manifest['source_sha256']
evidence = []
for filename, hash_key, count in [('static-qa.json', 'candidate_sha256', 8), ('workspace-qa.json', 'sha256', 7), ('runtime-qa.json', 'sha256', 11)]:
    path = stage / filename
    report = read(path)
    assert report.get(hash_key) == digest, (filename, 'candidate mismatch', report.keys())
    assert report['passed'] == count and report['total'] == count, filename
    evidence.append({'path': str(path.relative_to(media.ROOT)), 'sha256': media.sha(path.read_bytes())})
browser = read(stage / 'browser-qa.json')
assert browser['passed'] and browser['candidate_sha256'] == digest
progressive_root = media.ROOT / 'content-pipeline/progressive-boot-20260921'
build = read(progressive_root / 'site/progressive-build.json')
assert build['source_html_sha256'] == digest and build['exact_reassembly']
assert build['entry_sha256'] == browser['progressive_entry_sha256']
assert media.sha((progressive_root / 'site/index.html').read_bytes()) == build['entry_sha256']
for asset in build['generated_assets']:
    data = (progressive_root / 'site' / asset['path']).read_bytes()
    assert media.sha(data) == asset['sha256'] and len(data) == asset['bytes']
qa = read(progressive_root / 'qa.json')
assert qa['sourceSha256'] == digest and qa['entrySha256'] == build['entry_sha256']
assert qa['status'] == 'pass' and len(qa['checks']) == 6 and all(c['status'] == 'pass' for c in qa['checks'])
for path in [stage / 'browser-qa.json', progressive_root / 'qa.json', progressive_root / 'site/progressive-build.json']:
    evidence.append({'path': str(path.relative_to(media.ROOT)), 'sha256': media.sha(path.read_bytes())})
manifest.update(release_ready=True, release_evidence=evidence)
(stage / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'release_ready': True, 'candidate_sha256': digest, 'evidence_files': len(evidence)}))
