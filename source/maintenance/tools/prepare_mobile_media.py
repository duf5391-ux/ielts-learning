"""Externalize embedded book media without reserializing content or changing saved IDs."""
import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
STAGE = ROOT / 'content-pipeline/mobile-media-20260921'
TYPES = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/webp': 'webp', 'audio/mpeg': 'mp3', 'audio/wav': 'wav', 'audio/ogg': 'ogg', 'audio/mp4': 'm4a'}
sha = lambda data: hashlib.sha256(data).hexdigest()


class MediaTags(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.starts = [0]
        self.starts.extend(m.end() for m in re.finditer('\n', source))
        self.tags = []
        self.fields = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'data-save' in values:
            self.fields.append(values['data-save'])
        if tag in ('img', 'audio', 'source'):
            line, column = self.getpos()
            start = self.starts[line - 1] + column
            self.tags.append((start, self.get_starttag_text(), tag, values))


def replace_attribute(tag, name, value):
    pattern = re.compile(r'(\s' + re.escape(name) + r'\s*=\s*)([\"\'])(.*?)\2', re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(lambda m: m[1] + m[2] + value + m[2], tag, count=1)
    close = '/>' if tag.endswith('/>') else '>'
    return tag[:-len(close)] + ' ' + name + '="' + value + '"' + close


def prepare():
    raw = (BOOK / '开始学习.html').read_bytes()
    source = raw.decode('utf-8')
    media = MediaTags(source)
    replacements, assets = [], {}
    counts = {'embedded_media': 0, 'image_tags': 0, 'audio_tags': 0}
    for start, original, tag, attrs in media.tags:
        updated = original
        uri = attrs.get('src') or ''
        if uri.startswith('data:'):
            match = re.fullmatch(r'data:([^;,]+);base64,(.*)', uri, re.S)
            if not match or match[1] not in TYPES:
                raise ValueError('Unsupported embedded media: ' + uri[:70])
            payload = base64.b64decode(re.sub(r'\s+', '', match[2]), validate=True)
            digest = sha(payload)
            relative = 'assets/deferred-media/' + digest[:24] + '.' + TYPES[match[1]]
            if relative in assets and assets[relative]['sha256'] != digest:
                raise ValueError('Asset name collision')
            target = STAGE / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            assets[relative] = {'path': relative, 'sha256': digest, 'bytes': len(payload), 'mime': match[1]}
            updated = replace_attribute(updated, 'src', relative)
            counts['embedded_media'] += 1
        if tag == 'img':
            updated = replace_attribute(updated, 'loading', 'lazy')
            updated = replace_attribute(updated, 'decoding', 'async')
            counts['image_tags'] += 1
        elif tag == 'audio':
            updated = replace_attribute(updated, 'preload', 'none')
            counts['audio_tags'] += 1
        if updated != original:
            replacements.append((start, original, updated))
    candidate = source
    for start, original, updated in reversed(replacements):
        assert candidate[start:start + len(original)] == original
        candidate = candidate[:start] + updated + candidate[start + len(original):]
    # This exact inverse proves everything outside the selected media tags is unchanged.
    before_tags = MediaTags(source).tags
    after_tags = MediaTags(candidate).tags
    assert len(before_tags) == len(after_tags)
    restored = candidate
    for old, new in reversed(list(zip(before_tags, after_tags))):
        restored = restored[:new[0]] + old[1] + restored[new[0] + len(new[1]):]
    assert restored == source
    fields = MediaTags(candidate).fields
    assert media.fields == fields
    for tag in after_tags:
        assert not (tag[3].get('src') or '').startswith('data:')
    out = candidate.encode('utf-8')
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / '开始学习.html').write_bytes(out)
    report = {
        'status': 'prepared', 'source': str(BOOK / '开始学习.html'),
        'source_sha256': sha(raw), 'candidate_sha256': sha(out),
        'before_bytes': len(raw), 'after_bytes': len(out),
        'before_gzip_bytes': len(gzip.compress(raw, mtime=0)),
        'after_gzip_bytes': len(gzip.compress(out, mtime=0)),
        'save_fields': len(fields), 'media_counts': counts,
        'all_non_media_content_identical': True,
        'assets': list(assets.values()),
    }
    (STAGE / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'assets'}, ensure_ascii=False, indent=2))


def publish():
    report = json.loads((STAGE / 'manifest.json').read_text(encoding='utf-8'))
    assert report.get('release_ready') is True, 'Combined release and its UI/record checks must pass before publication'
    main = BOOK / '开始学习.html'
    candidate = (STAGE / '开始学习.html').read_bytes()
    assert sha(main.read_bytes()) == report['source_sha256'], 'Formal book changed; regenerate candidate'
    assert sha(candidate) == report['candidate_sha256']
    for asset in report['assets']:
        assert sha((STAGE / asset['path']).read_bytes()) == asset['sha256']
        target = BOOK / asset['path']
        if target.exists():
            assert sha(target.read_bytes()) == asset['sha256'], 'Existing asset differs'
    backup = ROOT / 'backups' / ('mobile-media-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(main, backup / main.name)
    for asset in report['assets']:
        target = BOOK / asset['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STAGE / asset['path'], target)
        assert sha(target.read_bytes()) == asset['sha256']
    # Assets first, then replace only a still-matching source entry.
    assert sha(main.read_bytes()) == report['source_sha256'], 'Concurrent update detected'
    temporary = main.with_name('开始学习.mobile-media.tmp')
    temporary.write_bytes(candidate)
    os.replace(temporary, main)
    report.update(status='published_local', backup=str(backup / main.name), published_at=datetime.now().isoformat())
    (STAGE / 'publication.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'sha256': sha(main.read_bytes()), 'backup': report['backup']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    publish() if args.publish else prepare()
