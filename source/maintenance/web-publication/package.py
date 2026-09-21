"""Portable static archive packager for Windows without the optional Bash helper.

The Sites helper was read earlier in this task; this uses its exact static archive
contract: dist assets plus dist/.openai/hosting.json with static.directory=dist.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, tarfile


def require_committed_inputs(root, relative_files):
    """Ignore Git-ignored scratch files, but reject unpublished source changes."""
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], check=True,
                              capture_output=True, text=True, encoding='utf-8').stdout

    repository = Path(git('rev-parse', '--show-toplevel').strip()).resolve()
    if repository != root.resolve():
        raise ValueError('Publish directory must be its own Git repository')
    commit = git('rev-parse', '--verify', 'HEAD').strip()
    if git('status', '--porcelain=v1', '--untracked-files=all').strip():
        raise ValueError('Commit and push all publication changes before packaging')
    tracked = set(git('ls-files', '-z').split('\0'))
    required = {'.openai/hosting.json', 'publication-manifest.json', *relative_files}
    missing = sorted(required - tracked)
    if missing:
        raise ValueError('Publication inputs are not committed: ' + ', '.join(missing[:10]))
    return commit


def validate_manifest(root):
    """Match every generated asset to the exact prepared inventory."""
    dist = root / 'dist'
    manifest = json.loads((root / 'publication-manifest.json').read_text(encoding='utf-8'))
    expected = {}
    for item in manifest['files']:
        name = item['path']
        if not isinstance(name, str) or name in expected:
            raise ValueError('Invalid or duplicate manifest path: ' + str(name))
        expected[name] = item
    actual = {}
    for path in dist.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink is not a publishable asset: ' + str(path))
        if path.is_file():
            actual[path.relative_to(dist).as_posix()] = path
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ValueError(f'Publish inventory mismatch: missing={missing[:10]}, extra={extra[:10]}')
    for name, path in actual.items():
        item = expected[name]
        if path.stat().st_size != item['bytes']:
            raise ValueError('Publish asset length mismatch: ' + name)
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        if checksum != item['sha256']:
            raise ValueError('Publish asset SHA-256 mismatch: ' + name)
    return sorted('dist/' + name for name in actual)

root = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('archive', type=Path)
args = ap.parse_args()
output = args.archive.resolve()
assert output.parent != (root / 'dist').resolve()
assert not output.is_relative_to(root / 'dist')
config = json.loads((root / '.openai/hosting.json').read_text(encoding='utf-8'))
assert config.get('project_id') and config.get('static', {}).get('directory') == 'dist'
assert (root / 'dist/index.html').is_file()
assert sum(p.stat().st_size for p in (root / 'dist').rglob('*') if p.is_file()) < 256 * 1024 * 1024 - 1024 * 1024
assert not any(config.get(k) for k in ('d1', 'r2', 'capabilities'))
published_files = validate_manifest(root)
source_commit = require_committed_inputs(root, published_files)
meta = root / '.sites-runtime/package-hosting.json'
meta.parent.mkdir(exist_ok=True)
meta.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
output.parent.mkdir(parents=True, exist_ok=True)
with tarfile.open(output, 'w:gz', compresslevel=6) as archive:
    for path in sorted((root / 'dist').rglob('*')):
        assert not path.is_symlink(), path
        if path.is_file():
            assert path.stat().st_size <= 25 * 1024 * 1024, path
            archive.add(path, arcname=path.relative_to(root).as_posix(), recursive=False)
    archive.add(meta, arcname='dist/.openai/hosting.json')
with tarfile.open(output) as archive:
    names = archive.getnames()
    assert 'dist/index.html' in names and 'dist/.openai/hosting.json' in names
    assert all(n.startswith('dist/') and '..' not in Path(n).parts for n in names)
    assert all(n not in names for n in ('dist/prepare.py', 'dist/.git/config'))
print(json.dumps({'archive':str(output),'bytes':output.stat().st_size,'files':len(names),
                  'source_commit':source_commit}))
