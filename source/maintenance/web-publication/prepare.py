"""Prepare a standalone copy of the current book; never modify the source book.

Usage: python prepare.py --book PATH --assets PATH [--target sites|github-pages]
Only reachable HTML/CSS resources and the dictionary runtime are published.
Sites (default): each resource <=25 MiB; expanded site <255 MiB.
GitHub Pages: each resource <100 MiB; expanded site <1 GiB.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import argparse, hashlib, json, re, shutil, subprocess, tempfile, gzip, importlib.util, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent
MIB = 1024 * 1024
TARGET_LIMITS = {
    'sites': {'label': 'Sites', 'asset_bytes': 25 * MIB, 'asset_inclusive': True,
              'total_bytes': 255 * MIB, 'asset_description': '<=25 MiB', 'total_description': '<255 MiB'},
    'github-pages': {'label': 'GitHub Pages', 'asset_bytes': 100 * MIB, 'asset_inclusive': False,
                     'total_bytes': 1024 * MIB, 'asset_description': '<100 MiB', 'total_description': '<1 GiB'},
}


def check_asset_size(size, target, name):
    limits = TARGET_LIMITS[target]
    exceeds = size > limits['asset_bytes'] if limits['asset_inclusive'] else size >= limits['asset_bytes']
    if exceeds:
        raise ValueError('%s requires each resource %s; prepare a verified web copy: %s' % (
            limits['label'], limits['asset_description'], name))


def check_total_size(size, target):
    limits = TARGET_LIMITS[target]
    if size >= limits['total_bytes']:
        raise ValueError('%s requires the expanded site %s; prepared size is %s bytes' % (
            limits['label'], limits['total_description'], size))


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--book', required=True, type=Path)
    ap.add_argument('--assets', required=True, type=Path)
    ap.add_argument('--target', choices=tuple(TARGET_LIMITS), default='sites',
                    help='Publication size budget (default: sites); see limits above.')
    ap.add_argument('--progressive', action='store_true',
                    help='Apply the reviewed progressive loader before final validation.')
    return ap.parse_args(argv)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.fields, self.scripts, self.script = [], [], [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'data-save' in a:
            self.fields.append(a['data-save'])
        for key in ('src', 'href', 'poster', 'data', 'action'):
            if a.get(key):
                self.refs.append(a[key])
        if a.get('style'):
            self.refs.extend(css_refs(a['style']))
        if tag == 'script':
            self.script = [a, '']

    def handle_data(self, data):
        if self.script is not None:
            self.script[1] += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(self.script)
            self.script = None

def css_refs(text):
    return re.findall(r'url\(\s*[\"\']?([^\"\')]+)', text)

def resolve_ref(base, value, source):
    if value.startswith(('#', 'data:', 'blob:', 'mailto:', 'javascript:', 'tel:')):
        return None
    u = urlsplit(value)
    if u.scheme or u.netloc:
        if u.scheme.lower() in ('file', 'c', 'd'):
            raise ValueError('Local machine reference: ' + value)
        return None
    if not u.path:
        return None
    target = (base / unquote(u.path)).resolve()
    if not target.is_relative_to(source):
        raise ValueError('Reference escapes book directory: ' + value)
    if target.is_dir():
        target /= 'index.html'
    if not target.is_file():
        raise ValueError('Missing resource: ' + str(target))
    return target

def main():
    args = parse_args()
    source = args.book.resolve()
    entry = source / '开始学习.html'
    entry_hash = digest(entry)
    queue = [entry]
    seen = set()
    source_hashes = {}
    # Dynamic resources require an explicit, reviewed source entry.
    extra_resources = ROOT / 'extra-resources.json'
    if extra_resources.exists():
        for item in json.loads(extra_resources.read_text(encoding='utf-8'))['resources']:
            p = resolve_ref(source, item['path'], source)
            if p is None or digest(p) != item['source_sha256']:
                raise ValueError('Explicit resource no longer matches reviewed source: ' + item['path'])
            queue.append(p)
    # The dictionary creates script tags for a manifest and 702 lazy shards.
    queue.extend(p for p in (source / 'local-dictionary').rglob('*') if p.is_file()
                 and p.suffix.lower() in ('.js', '.css', '.txt', '.md'))
    while queue:
        p = queue.pop()
        if p in seen:
            continue
        if p.is_symlink():
            raise ValueError('Symlink is not a publishable file: ' + str(p))
        seen.add(p)
        source_hashes[p] = digest(p)
        refs = []
        if p.suffix.lower() in ('.html', '.htm'):
            t = p.read_text(encoding='utf-8')
            page = Page(); page.feed(t)
            refs = page.refs
            for style in re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S | re.I):
                refs.extend(css_refs(style))
            # Explicit JS/JSON resource literals, where they resolve to real files.
            for match in re.finditer(r'''["']([^"'\n]{1,180}\.(?:json|js|css|html))["']''', t):
                literal = match.group(1)
                u = urlsplit(literal)
                if not u.scheme and not u.netloc and (p.parent / unquote(u.path)).is_file():
                    refs.append(literal)
        elif p.suffix.lower() == '.css':
            refs = css_refs(p.read_text(encoding='utf-8'))
        for value in refs:
            q = resolve_ref(p.parent, value, source)
            if q is not None and q not in seen:
                queue.append(q)

    assets = args.assets.resolve()
    overrides = {}
    # Hashes are pinned to the reviewed source and verified prepared asset.
    overrides['原始参考/precise-official-listening-full.mp3'] = (
        assets / 'precise-official-listening-full-web.mp3',
        'e80b35b4d18aab72ccac42eca13498909ad532173f532160eaa690c7c4833870',
        'd45e0ea90377ee336783279c8ac8a9edf48e291097f46c3691b4ebb385c9ec07')
    pdf_info = assets / 'pdf-web-preparation.json'
    if pdf_info.exists():
        d = json.loads(pdf_info.read_text(encoding='utf-8'))
        overrides[d['relative_path']] = (assets / 'cambridge-ielts21-web.pdf', d['source_sha256'], d['output_sha256'])
    audio_info = assets / 'audio-web-preparation.json'
    if audio_info.exists():
        for d in json.loads(audio_info.read_text(encoding='utf-8'))['items']:
            overrides[d['relative_path']] = (assets / d['output_file'], d['source_sha256'], d['output_sha256'])
    extra_audio = assets / 'jijing-audio-preparation.json'
    if extra_audio.exists():
        d = json.loads(extra_audio.read_text(encoding='utf-8'))
        overrides[d['relative_path']] = (assets / d['output_file'], d['source_sha256'], d['output_sha256'])

    runtime = ROOT / '.sites-runtime'
    runtime.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='stage-', dir=runtime))
    entries, substitutions = [], []
    try:
        for p in sorted(seen):
            if digest(p) != source_hashes[p]:
                raise ValueError('Source changed during preparation; rerun: ' + str(p))
            rel = p.relative_to(source).as_posix()
            from_path = p
            if rel in overrides:
                replacement, old_sha, new_sha = overrides[rel]
                if digest(p) != old_sha or digest(replacement) != new_sha:
                    raise ValueError('Prepared resource no longer matches reviewed original: ' + rel)
                from_path = replacement
                substitutions.append({'path': rel, 'original_sha256': old_sha, 'published_sha256': new_sha})
            check_asset_size(from_path.stat().st_size, args.target, rel)
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(from_path, dest)
            entries.append({'path': rel, 'bytes': dest.stat().st_size, 'sha256': digest(dest)})

        # Preserve every dictionary row while reducing the expanded deployment size.
        dictionary_original = dictionary_compressed = shard_count = 0
        for p in (stage / 'local-dictionary/shards').glob('*.js'):
            text = p.read_text(encoding='utf-8')
            match = re.fullmatch(r'window\.IELTSLocalDictionary\.registerShard\("([a-z_]{2})",\s*(\{.*\})\);\s*', text, re.S)
            assert match and match[1] == p.stem, 'Unknown dictionary shard format: ' + p.name
            raw = match[2].encode('utf-8')
            data = json.loads(raw)
            assert data['format'] == 1 and data.get('entries') is not None
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            assert gzip.decompress(compressed) == raw
            p.with_suffix('.json.gz.bin').write_bytes(compressed)
            dictionary_original += p.stat().st_size
            dictionary_compressed += len(compressed)
            shard_count += 1
            p.unlink()
        engine = stage / 'local-dictionary/dictionary-engine.js'
        text = engine.read_text(encoding='utf-8')
        marker = '  function loadScript(relativePath, registered) {\n'
        assert text.count(marker) == 1
        text = text.replace(marker, marker + (ROOT / 'dictionary-web-loader.js').read_text(encoding='utf-8'), 1)
        # The small manifest is always needed: avoid an extra dynamic script request.
        manifest_script = (stage / 'local-dictionary/dictionary-manifest.js').read_text(encoding='utf-8')
        text += '\n' + manifest_script
        engine.write_text(text, encoding='utf-8')

        original = entry.read_text(encoding='utf-8')
        before = Page(); before.feed(original)
        # Keep all content, scripts, routes and data-save identities byte-for-byte.
        extra = '\n<link rel="manifest" href="site.webmanifest">\n<meta name="theme-color" content="#356c57">\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-title" content="雅思学习册">\n<link rel="icon" href="app-icon.svg" type="image/svg+xml">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
        published = original.replace('</head>', extra + '</head>', 1)
        published = published.replace('释义与原句保存在本地，查词无需联网。', '收藏与原句保存在当前浏览器，首次查词需要联网加载词库。')
        assert published != original, 'Missing head element'
        after = Page(); after.feed(published)
        assert Counter(before.fields) == Counter(after.fields)
        assert before.scripts == after.scripts
        assert 'DAILY-STUDY-V1' in published and 'daily-study-state' in after.fields
        (stage / 'index.html').write_text(published, encoding='utf-8')
        # Keep old relative links working, with one canonical copy of the book.
        (stage / '开始学习.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>雅思学习册</title><script>location.replace("./index.html"+location.search+location.hash)</script><a href="index.html">打开学习册</a></html>', encoding='utf-8')
        dictionary_page = stage / '本地词典.html'
        dictionary_page.write_text(dictionary_page.read_text(encoding='utf-8').replace(
            '释义、音标与词形保存在本机，断网也能查。770,611 条词目；支持常见词形变化。',
            '站内词库收录 770,611 条词目，支持常见词形变化；首次加载词条需要联网。'), encoding='utf-8')
        (stage / 'site.webmanifest').write_text(json.dumps({
            'name': 'IELTS 四科学习册', 'short_name': '雅思学习册', 'lang': 'zh-CN',
            'id': './', 'start_url': './index.html#study', 'scope': './',
            'display': 'standalone', 'background_color': '#f7f7f2', 'theme_color': '#356c57',
            'icons': [{'src': 'app-icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
                      {'src': 'app-icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
                      {'src': 'app-icon.svg', 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any'}]
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        for name in ('app-icon-192.png', 'app-icon-512.png', 'apple-touch-icon.png'):
            shutil.copyfile(ROOT / 'static-icons' / name, stage / name)
        (stage / 'app-icon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect width="192" height="192" rx="42" fill="#356c57"/><path d="M40 48h43q13 0 13 12q0-12 13-12h43v88h-43q-13 0-13 12q0-12-13-12H40z" fill="#f7f7f2"/><path d="M96 63v65M53 70h27M53 87h27M112 70h27M112 87h27" fill="none" stroke="#356c57" stroke-width="6" stroke-linecap="round"/></svg>', encoding='utf-8')
        (stage / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
        (stage / '_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Robots-Tag: noindex, nofollow\n', encoding='utf-8')

        progressive_report = None
        if args.progressive:
            transform = ROOT.parent / 'tools/progressive_web.py'
            if not transform.is_file():
                raise ValueError('Progressive transform is missing: ' + str(transform))
            spec = importlib.util.spec_from_file_location('ielts_progressive_web', transform)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            progressive_report = module.apply_progressive_loading(stage)
            if not isinstance(progressive_report, dict):
                raise ValueError('Progressive transform must return its verification report')

        # Validate the resulting dependency closure, including companion pages.
        html_count = script_count = 0
        js_files = []
        for p in stage.rglob('*'):
            if not p.is_file(): continue
            check_asset_size(p.stat().st_size, args.target, p.relative_to(stage).as_posix())
            if p.suffix.lower() in ('.html', '.htm'):
                page = Page(); page.feed(p.read_text(encoding='utf-8')); html_count += 1
                for value in page.refs:
                    resolve_ref(p.parent, value, stage)
                for attrs, text in page.scripts:
                    if attrs.get('src') or attrs.get('type', '').lower() not in ('', 'text/javascript', 'application/javascript', 'module'): continue
                    scratch = runtime / ('syntax-check.mjs' if attrs.get('type') == 'module' else 'syntax-check.js')
                    scratch.write_text(text, encoding='utf-8')
                    subprocess.run(['node', '--check', str(scratch)], check=True, capture_output=True)
                    script_count += 1
            elif p.suffix.lower() == '.js':
                js_files.append(p)
                script_count += 1
        def syntax_check(p):
            subprocess.run(['node', '--check', str(p)], check=True, capture_output=True)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(syntax_check, js_files))
        assert digest(entry) == entry_hash, 'Live book changed during packaging; rerun against the new source'
        for p, original_hash in source_hashes.items():
            if digest(p) != original_hash:
                raise ValueError('Source changed during preparation; rerun: ' + str(p))
        total_size = sum(p.stat().st_size for p in stage.rglob('*') if p.is_file())
        check_total_size(total_size, args.target)
        # Replace only generated output after all validations have succeeded.
        dist = ROOT / 'dist'
        assert dist.resolve().parent == ROOT and dist.name == 'dist'
        if dist.exists(): shutil.rmtree(dist)
        stage.rename(dist)
        published_files = [{'path': p.relative_to(dist).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
                           for p in sorted(dist.rglob('*')) if p.is_file()]
        report = {'publication_target': args.target,
                  'progressive_loading': progressive_report,
                  'source_html_sha256': entry_hash, 'published_html_sha256': digest(dist / 'index.html'),
                  'save_fields': len(before.fields), 'source_files': len(entries),
                  'published_files': sum(1 for p in dist.rglob('*') if p.is_file()),
                  'total_bytes': sum(p.stat().st_size for p in dist.rglob('*') if p.is_file()),
                  'html_pages_checked': html_count, 'scripts_syntax_checked': script_count,
                  'dictionary': {'lossless': True, 'shards': shard_count, 'original_bytes': dictionary_original, 'compressed_bytes': dictionary_compressed},
                  'substitutions': substitutions, 'prepared_inputs': entries, 'files': published_files}
        report['source_inputs'] = [{'path': p.relative_to(source).as_posix(), 'sha256': sha}
                                  for p, sha in sorted(source_hashes.items())]
        (ROOT / 'publication-manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','prepared_inputs','source_inputs')}, ensure_ascii=False, indent=2))
    finally:
        if stage.exists():
            assert stage.resolve().parent == runtime.resolve()
            shutil.rmtree(stage)

if __name__ == '__main__':
    main()
