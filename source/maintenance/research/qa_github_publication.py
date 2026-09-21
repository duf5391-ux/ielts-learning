"""Exercise refusal of corrupt/incomplete publication inputs on isolated fixtures."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', root / 'github-publication/validate.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
results = []
with tempfile.TemporaryDirectory(prefix='ielts-pages-validation-') as directory:
    site = Path(directory)
    content = b'<html>isolated fixture</html>'
    checksum = hashlib.sha256(content).hexdigest()
    manifest = {'source_html_sha256': checksum, 'published_html_sha256': checksum,
                'published_files': 1, 'total_bytes': len(content),
                'files': [{'path': 'index.html', 'bytes': len(content), 'sha256': checksum}]}
    (site / 'index.html').write_bytes(content)
    validator.validate(site, manifest)
    results.append('valid isolated site accepted')

    def rejects(label, altered=None):
        try:
            validator.validate(site, altered or manifest)
        except ValueError:
            results.append(label)
        else:
            raise AssertionError('Did not reject: ' + label)

    (site / 'index.html').write_bytes(b'X' * len(content))
    rejects('same-size asset corruption rejected')
    (site / 'index.html').write_bytes(content)
    (site / 'secret.env').write_text('dummy fixture, not a credential')
    rejects('unlisted extra file rejected')
    (site / 'secret.env').unlink()
    (site / 'index.html').unlink()
    rejects('missing homepage rejected')
    (site / 'index.html').write_bytes(content)
    for name in ('../outside', '/absolute', 'C:/local', 'folder\\asset', './index.html'):
        changed = copy.deepcopy(manifest)
        changed['files'][0]['path'] = name
        rejects('unsafe path rejected: ' + name, changed)
    changed = copy.deepcopy(manifest)
    changed['files'].append(changed['files'][0].copy())
    rejects('duplicate path rejected', changed)
    changed = copy.deepcopy(manifest)
    changed['total_bytes'] += 1
    rejects('incorrect total rejected', changed)
report = {'status': 'passed', 'checks': len(results), 'results': results,
          'scope': 'Isolated validation fixtures; no user browser records.'}
(root / 'research/github-publication-validation-tests-20260921.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report))
