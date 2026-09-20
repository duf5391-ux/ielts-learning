"""Verify only the files that will be uploaded to GitHub Pages (stdlib only)."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate(site, manifest):
    site = site.resolve()
    expected = {}
    for item in manifest['files']:
        name = item['path']
        relative = PurePosixPath(name)
        if (not name or '\\' in name or ':' in name or relative.is_absolute()
                or '..' in relative.parts or name != relative.as_posix()
                or name in expected):
            raise ValueError('Unsafe or duplicate asset path: ' + name)
        expected[name] = item
    if 'index.html' not in expected:
        raise ValueError('Missing homepage')
    actual = {}
    for path in site.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink cannot be published: ' + str(path))
        if path.is_file():
            actual[path.relative_to(site).as_posix()] = path
    if set(actual) != set(expected):
        raise ValueError('Inventory mismatch: missing=%s extra=%s' % (
            sorted(set(expected) - set(actual))[:5],
            sorted(set(actual) - set(expected))[:5]))
    total = 0
    for name, path in actual.items():
        item = expected[name]
        size = path.stat().st_size
        if size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('Asset changed after preparation: ' + name)
        if size >= 100 * 1024 * 1024:
            raise ValueError('Asset exceeds Git file limit: ' + name)
        total += size
    if total != manifest['total_bytes'] or len(actual) != manifest['published_files']:
        raise ValueError('Manifest totals do not match')
    if total >= 1024 * 1024 * 1024:
        raise ValueError('Site exceeds GitHub Pages size limit')
    if digest(site / 'index.html') != manifest['published_html_sha256']:
        raise ValueError('Homepage fingerprint mismatch')
    return {'files': len(actual), 'bytes': total,
            'source_html_sha256': manifest['source_html_sha256'],
            'published_html_sha256': manifest['published_html_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    manifest = json.loads((args.root / 'manifest.json').read_text(encoding='utf-8'))
    print(json.dumps(validate(args.root / 'site', manifest), ensure_ascii=False))
