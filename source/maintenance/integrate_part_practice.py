"""Add source-matched exercises to existing parts, retaining the original book exactly."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
from datetime import datetime
import hashlib
import json
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN = BOOK / '开始学习.html'
FILES = ['precise-reading.json', 'precise-listening-speaking.json', 'precise-writing-language.json']
SECTIONS = ['reading', 'listening', 'writing1', 'writing2', 'speaking', 'vocabulary', 'background']
PATTERN = r'<!--PART-PRACTICE-V1:[^>]+-->.*?<!--/PART-PRACTICE-V1-->'
QA = HERE / 'part-practice-qa'


def e(value):
    return escape(str(value), quote=True)


def paragraphs(value, cls=''):
    if isinstance(value, list):
        return ''.join(paragraphs(v, cls) for v in value)
    return '<p' + (f' class="{cls}"' if cls else '') + '>' + e(value).replace('\n', '<br/>') + '</p>'


def mark(name, body):
    return f'<!--PART-PRACTICE-V1:{name}-->{body}<!--/PART-PRACTICE-V1-->'


def stripped(page):
    return re.sub(PATTERN, '', page, flags=re.S)


class Structure(HTMLParser):
    def __init__(self, page):
        super().__init__(convert_charrefs=False)
        self.offsets = [0]
        for m in re.finditer('\n', page):
            self.offsets.append(m.end())
        self.stack, self.sections, self.ids, self.fields, self.media = [], {}, [], [], []
        self.feed(page)

    def position(self):
        line, col = self.getpos()
        return self.offsets[line - 1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if 'data-save' in attrs:
            self.fields.append(attrs['data-save'])
        if tag in ['img', 'audio', 'source']:
            self.media.append((tag, attrs.get('src')))
        if tag == 'section':
            self.stack.append((attrs.get('id'), self.position() + len(self.get_starttag_text())))

    def handle_endtag(self, tag):
        if tag == 'section' and self.stack:
            ident, start = self.stack.pop()
            if ident:
                self.sections[ident] = (start, self.position())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == 'section':
            self.handle_endtag(tag)


def field(key, label='作答', rows=3):
    return f'<label class="pp-answer"><span>{e(label)}</span><textarea data-save="{e(key)}" rows="{rows}"></textarea></label>'


def source_link(source):
    href = source.get('path') or source.get('url')
    if not href:
        raise ValueError('Missing actual source link: ' + source['title'])
    if source.get('path'):
        assert (BOOK / source['path']).exists(), source['path']
    page = source.get('page')
    if isinstance(page, list):
        page = page[0] if page else None
    if page and '#' not in href:
        href += '#page=' + str(page)
    rendered = '<a href="' + e(href) + '" target="_blank" rel="noopener">' + e(source['title']) + '</a>'
    if source.get('url') and source.get('path'):
        rendered += ' · <a href="' + e(source['url']) + '" target="_blank" rel="noopener">在线来源</a>'
    return rendered


def recorder(uid):
    return f'''<div class="recorder pp-recorder" data-recorder="{e(uid)}"><button data-record="{e(uid)}" type="button">开始录音</button><button data-stop="{e(uid)}" disabled type="button">结束录音</button><a data-download="{e(uid)}" hidden>下载录音</a><audio controls data-preview="{e(uid)}" hidden></audio><label class="audio-import">载入录音 <input type="file" accept="audio/*" data-upload="{e(uid)}"/></label><p class="small" data-rec-status="{e(uid)}">录音需单独下载保存。</p></div>''' + field(uid + '-record-note', '录音文件名 / 要点', 2)


def unit_html(unit):
    uid = unit['id']
    body = paragraphs(unit.get('instructions', ''), 'pp-instructions')
    if unit.get('audio'):
        audio = unit['audio']
        src = audio['src']
        if not src.startswith(('https://', 'http://')):
            assert (BOOK / src).exists(), src
        if audio.get('start') is not None:
            src += '#t=' + str(audio['start']) + (',' + str(audio['end']) if audio.get('end') is not None else '')
        body += '<audio class="pp-audio" controls preload="none" src="' + e(src) + '"></audio>'
    image = unit.get('image')
    if image:
        assert (BOOK / image['src']).exists(), image['src']
        body += '<figure class="pp-figure original"><img loading="lazy" src="' + e(image['src']) + '" alt="' + e(image['alt']) + '"/></figure>'
    if unit['section'] == 'speaking':
        body += paragraphs(unit.get('prompt', ''))
    if unit.get('context'):
        body += '<div class="pp-context">' + paragraphs(unit['context']) + '</div>'
    if unit['section'] != 'speaking':
        body += paragraphs(unit.get('prompt', ''))
    for index, question in enumerate(unit['questions'], 1):
        body += '<div class="pp-question">' + paragraphs(question['prompt'])
        if question.get('options'):
            opts = question['options']
            if isinstance(opts, dict):
                opts = [{'id': k, 'text': v} for k, v in opts.items()]
            body += '<ul class="pp-options">' + ''.join('<li><b>' + e(o['id']) + '</b> ' + e(o['text']) + '</li>' for o in opts) + '</ul>'
        if unit['section'] != 'speaking':
            body += field(uid + '-' + question['id'], '作答 ' + str(index), 3 if unit['section'].startswith('writing') else 2)
        body += '</div>'
    if unit['section'] == 'speaking':
        body += recorder(uid)
    else:
        body += '<details class="pp-key"><summary>答案</summary>' + paragraphs(unit['reference']) + '</details>'
    transfer = unit.get('transfer')
    if transfer and transfer.get('prompt'):
        body += '<details class="pp-another"><summary>再练一次</summary>' + paragraphs(transfer['prompt'])
        body += field(uid + '-another', '作答', 3)
        body += '<details class="pp-key"><summary>答案</summary>' + paragraphs(transfer['reference']) + '</details></details>'
    body += '<p class="pp-source">选材来源 · ' + source_link(unit['source']) + '</p>'
    # Reasoning, difficulty, pitfall and design metadata intentionally stay out of the learner page.
    return '<details class="pp-unit" id="' + e(uid) + '"><summary><span class="pp-part">' + e(unit['part']) + '</span> ' + e(unit['title']) + '</summary><div class="pp-body">' + body + '</div></details>'


CSS = '''.pp-entry{display:block;width:fit-content;margin:16px 0;padding:8px 14px;border:1px solid var(--line,#d9ded4);border-radius:7px;font-size:14px;text-decoration:none}.pp-practice{margin:42px 0;padding-top:24px;border-top:2px solid var(--green,#204c42)}.pp-practice h2{font-size:25px}.pp-unit{background:#fff}.pp-part{display:inline-block;font-size:12px;font-weight:400;margin-right:12px;color:var(--muted,#65726c)}.pp-body{padding-bottom:20px;overflow-wrap:anywhere}.pp-body p{white-space:normal;line-height:1.8}.pp-instructions{color:var(--muted,#65726c);font-size:14px}.pp-context{background:#f5f6ee;border-left:3px solid #a9b9a6;padding:18px 22px;margin:18px 0}.pp-context p:last-child{margin-bottom:0}.pp-answer{display:block;margin:16px 0}.pp-answer>span{display:block;font-size:13px;margin-bottom:7px}.pp-answer textarea{display:block;width:100%;min-width:0;padding:10px 12px;border:1px solid #bdcabc;border-radius:5px;resize:vertical;font:inherit;line-height:1.7;background:#fff}.pp-options{list-style:none;padding:0;margin:12px 0}.pp-options li{margin:8px 0}.pp-options b{display:inline-block;min-width:24px}.pp-question{margin-top:20px}.pp-key{background:#f0f4e9}.pp-key summary,.pp-another summary{font-size:14px}.pp-source{font-size:12px;color:var(--muted,#65726c);margin:22px 0 0}.pp-figure{max-width:850px}.pp-figure img{width:100%;height:auto}.pp-audio{width:100%;margin:18px 0}.pp-recorder{margin:18px 0}.pp-practice-nav{display:flex;flex-wrap:wrap;gap:8px 16px;margin:12px 0 24px}.pp-practice-nav a{font-size:13px}@media(max-width:640px){.pp-context{padding:14px}.pp-unit{padding:0 14px}.pp-part{display:block}.pp-body{font-size:16px}.pp-recorder button{margin:5px}}@media print{.pp-entry,.pp-recorder button,.pp-recorder input{display:none}.pp-unit{break-inside:auto}.pp-key{display:none}.pp-answer textarea{min-height:24mm}}'''


def load():
    units = []
    for file in FILES:
        payload = json.loads((HERE / file).read_text(encoding='utf-8'))
        if isinstance(payload, dict):
            for asset in payload.get('assetCopies', []):
                source = Path(asset['source']).resolve()
                destination = (BOOK / asset['destination']).resolve()
                assert destination.is_relative_to(BOOK.resolve()), 'Asset destination must remain inside the book'
                assert source.is_file(), source
                if destination.exists():
                    assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(destination.read_bytes()).digest(), 'Existing asset differs: ' + str(destination)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        os.link(source, destination)
                    except OSError:
                        shutil.copy2(source, destination)
        units.extend(payload if isinstance(payload, list) else payload['units'])
    assert len({u['id'] for u in units}) == len(units)
    assert set(u['section'] for u in units) == set(SECTIONS)
    for unit in units:
        assert re.fullmatch(r'pr-[a-z0-9-]+', unit['id']), unit['id']
        assert unit['questions'] and unit['reference'] and unit['source']
        assert not re.search('高难|难度|挑战|陷阱', unit['title'] + unit['part'])
        assert len(set(q['id'] for q in unit['questions'])) == len(unit['questions'])
        assert all(q['prompt'] for q in unit['questions'])
    return units


def apply(page, units):
    base = stripped(page)
    before = Structure(base)
    insertions = []
    for section in SECTIONS:
        selected = [u for u in units if u['section'] == section]
        start, end = before.sections[section]
        entry = '<a class="pp-entry" href="#pp-' + section + '">练习 →</a>'
        content = '<section class="pp-practice" id="pp-' + section + '"><h2>练习</h2><nav class="pp-practice-nav" aria-label="练习题组">' + ''.join('<a href="#' + e(u['id']) + '">' + e(u['part']) + '</a>' for u in selected) + '</nav>' + ''.join(unit_html(u) for u in selected) + '</section>'
        insertions.extend([(start, mark(section + '-entry', entry)), (end, mark(section, content))])
    insertions.append((base.index('</head>'), mark('style', '<style>' + CSS + '</style>')))
    # Add to the existing resource directory, with existing hash routing.
    library_start = before.sections['library'][0]
    links = '<div class="pp-practice-nav">' + ''.join('<a href="#pp-' + sec + '">' + label + '练习</a>' for sec, label in [('reading', '阅读'), ('listening', '听力'), ('writing1', 'Task 1 '), ('writing2', 'Task 2 '), ('speaking', '口语'), ('vocabulary', '词汇'), ('background', '话题')]) + '</div>'
    insertions.append((library_start, mark('directory', links)))
    result = base
    for position, html in sorted(insertions, reverse=True):
        result = result[:position] + html + result[position:]
    assert stripped(result) == base
    after = Structure(result)
    assert len(after.ids) == len(set(after.ids)), 'Duplicate IDs'
    assert len(after.fields) == len(set(after.fields)), 'Duplicate save fields'
    assert set(before.fields).issubset(after.fields)
    assert [f for f in after.fields if not f.startswith('pr-')] == before.fields
    assert before.ids == [v for v in after.ids if not v.startswith(('pr-', 'pp-'))]
    return result, {'units': len(units), 'questions': sum(len(u['questions']) for u in units), 'sections': {s: sum(u['section'] == s for u in units) for s in SECTIONS}, 'original_fields_preserved': len(before.fields), 'new_fields': len(after.fields) - len(before.fields), 'original_content_preserved_exactly': True, 'extra_teaching_rendered': False, 'difficulty_labels': False}


def main():
    units = load()
    for _ in range(3):
        raw = MAIN.read_bytes()
        result, report = apply(raw.decode('utf-8'), units)
        assert apply(result, units)[0] == result
        if MAIN.read_bytes() != raw:
            continue
        if raw != result.encode('utf-8'):
            backup_dir = HERE / 'backups'
            backup_dir.mkdir(exist_ok=True)
            if not list(backup_dir.glob('开始学习-before-part-practice-*.html')):
                backup = backup_dir / ('开始学习-before-part-practice-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.html')
                backup.write_bytes(raw)
            temp = MAIN.with_name('开始学习.part-practice.tmp')
            temp.write_text(result, encoding='utf-8', newline='')
            if MAIN.read_bytes() != raw:
                temp.unlink()
                continue
            os.replace(temp, MAIN)
        QA.mkdir(exist_ok=True)
        report.update(idempotent=True, sha256=hashlib.sha256(MAIN.read_bytes()).hexdigest())
        (QA / 'integration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (HERE / 'part-practice-bank.json').write_text(json.dumps({'version': 1, 'units': units}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))
        return
    raise RuntimeError('学习册正在被其他任务修改，本次未覆盖其内容。')


if __name__ == '__main__':
    main()
