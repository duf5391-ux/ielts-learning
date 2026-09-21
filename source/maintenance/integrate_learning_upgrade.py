"""Incrementally integrate vocabulary review, sentence tools and writing workbench.

Never rebuild the book or touch browser records. Static fields precede restore().
"""
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')


def marked(text, name, body, before):
    block = f'<!--LEARNING-UPGRADE:{name}-->{body}<!--/LEARNING-UPGRADE:{name}-->'
    pattern = rf'<!--LEARNING-UPGRADE:{name}-->.*?<!--/LEARNING-UPGRADE:{name}-->'
    if re.search(pattern, text, re.S):
        return re.sub(pattern, lambda m: block, text, count=1, flags=re.S)
    assert before in text, (name, before)
    return text.replace(before, block + before, 1)


class Inventory(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.fields, self.media, self.ids = [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'data-save' in d:
            self.fields.append(d['data-save'])
        if 'id' in d:
            self.ids.append(d['id'])
        if tag in ('img', 'audio', 'source', 'video'):
            self.media.append((tag, tuple(attrs)))


def sentence_tools(text):
    text = marked(text, 'sentence-records', (ROOT / 'selection-tools.html').read_text(encoding='utf8'), '<section id="lookup-learning">')
    # The popup must precede scripts: useful for keyboard access and future saved fields.
    text = marked(text, 'sentence-popup', (ROOT / 'selection-tools-popup.html').read_text(encoding='utf8'), '<div class="toast"')
    text = marked(text, 'sentence-style', '<link rel="stylesheet" href="selection-tools.css">', '</head>')
    entry = '<div class="st-entry"><div><strong>把遇到的词句，变成自己的积累。</strong><p>选中英文可查词、收藏；选中一句话可翻译并保存译文。</p></div><div class="st-actions"><a href="#vocabulary-review">我的单词表 · 开始复习 →</a><a href="#sentence-learning">我的句子本 →</a></div></div>'
    if '<!--LEARNING-UPGRADE:word-sentence-entry-->' in text:
        text = marked(text, 'word-sentence-entry', entry, '</main>')
    else:
        match = re.search(r'<section\b[^>]*\bid="vocabulary"[^>]*>',text)
        assert match
        point = match.end()
        text = text[:point] + '<!--LEARNING-UPGRADE:word-sentence-entry-->' + entry + '<!--/LEARNING-UPGRADE:word-sentence-entry-->' + text[point:]
    pairs = []
    for filename, en_key, zh_key in [('background-core-words.json','example_en','example_zh'),('background-vocabulary.json','self_example_en','self_example_zh')]:
        for row in json.loads((BOOK / filename).read_text(encoding='utf8')):
            if row.get(en_key) and row.get(zh_key):
                pairs.append({'en':row[en_key],'zh':row[zh_key]})
    data = '<script id="sentence-local-pairs" type="application/json">' + json.dumps(pairs,ensure_ascii=False).replace('<','\\u003c') + '</script>'
    script = (ROOT / 'selection-tools.js').read_text(encoding='utf8')
    assert '</script' not in script
    text = marked(text, 'sentence-script', data + '<script id="selection-tools-script">' + script + '</script>', '</body>')
    return text


def apply(text):
    from integrate_writing_workbench import apply as apply_writing
    from integrate_vocabulary_review import apply as apply_vocabulary
    text, vocab_report = apply_vocabulary(text)
    text = sentence_tools(text)
    text, writing_report = apply_writing(text)
    return text, {'vocabulary': vocab_report, 'writing': writing_report}


def main():
    path = BOOK / '开始学习.html'
    before = path.read_text(encoding='utf8')
    after, report = apply(before)
    assert apply(after)[0] == after, 'Integration is not idempotent'
    a, b = Inventory(before), Inventory(after)
    assert set(a.fields).issubset(b.fields), 'An existing saved field was removed'
    assert len(b.fields) == len(set(b.fields)), 'Duplicate data-save fields'
    assert len(b.ids) == len(set(b.ids)), 'Duplicate IDs'
    for media in a.media:
        assert media in b.media, f'Media removed: {media}'
    # Preserve original core record-safety controller byte for byte.
    scripts = lambda s: re.findall(r'<script\b[^>]*>(.*?)</script>', s, re.S)
    core = next(s for s in scripts(before) if 'RECORD-SAFETY-20260919' in s)
    assert core in scripts(after), 'Core record controller changed'
    report.update({'savedFieldsBefore':len(a.fields),'savedFieldsAfter':len(b.fields),'existingMediaPreserved':len(a.media),'idempotent':True,'sha256':hashlib.sha256(after.encode('utf8')).hexdigest()})
    if before != after:
        originals = sorted(p for p in (ROOT / 'backups').glob('learning-upgrade-*/开始学习.html') if p.stat().st_size > 1000000)
        reuse = '<!--LEARNING-UPGRADE:sentence-records-->' in before and bool(originals)
        required = len(after.encode('utf8')) * (1 if reuse else 2) + 2000000
        assert shutil.disk_usage(BOOK).free > required, 'Not enough free space to stage safely; main book unchanged'
        if reuse:
            backup = originals[0].parent
            report['backupPolicy'] = 'Preserve the original pre-upgrade backup across incremental updates'
        else:
            backup = ROOT / 'backups' / ('learning-upgrade-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / path.name)
        # Stage all assets before changing the main page.
        for name in ['selection-tools.css','writing-workbench.css','vocabulary-review.css']:
            source = ROOT / name
            if source.exists():
                target = BOOK / name
                temp = target.with_suffix(target.suffix + '.upgrade.tmp')
                shutil.copy2(source, temp)
                assert temp.read_bytes() == source.read_bytes()
                temp.replace(target)
        temp = path.with_suffix('.upgrade.tmp')
        temp.write_text(after, encoding='utf8')
        assert temp.read_text(encoding='utf8') == after
        assert path.read_text(encoding='utf8') == before, 'Concurrent edit detected'
        temp.replace(path)
        report['backup'] = str(backup)
    out = ROOT / 'learning-upgrade-qa'
    out.mkdir(exist_ok=True)
    (out / 'integration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf8')
    main()
