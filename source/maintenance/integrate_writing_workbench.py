"""Idempotent writing composition; the caller owns backups and publishing."""
from pathlib import Path
import json
import re
from integrate_part_practice import Structure

HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
PATTERN = r'<!--WRITING-WORKBENCH-V1:[^>]+-->.*?<!--/WRITING-WORKBENCH-V1-->'


def mark(name, content):
    return f'<!--WRITING-WORKBENCH-V1:{name}-->{content}<!--/WRITING-WORKBENCH-V1-->'


def apply(page):
    base = re.sub(PATTERN, '', page, flags=re.S)
    before = Structure(base)
    content = (HERE / 'writing-workbench.html').read_text(encoding='utf-8')
    css = (HERE / 'writing-workbench.css').read_text(encoding='utf-8')
    js = (HERE / 'writing-workbench.js').read_text(encoding='utf-8')
    inserts = [
        (base.index('</main>'), mark('panel', content)),
        (base.index('</head>'), mark('style', '<style>' + css + '</style>')),
        (base.rindex('</body>'), mark('script', '<script>' + js + '</script>')),
    ]
    labels = {
        'guide': ('写作工作台', '选题、审题、限时首稿、四维检查与修订，每题单独保存。', '#writing-workbench'),
        'writing1': ('Task 1 写作工作台', '折线图、流程图与平面图，从概览到完整首稿，再检查修订。', '#ww-jobs'),
        'writing2': ('Task 2 写作工作台', '从回应问题到理由与例子，保留首稿、检查证据与多次修订。', '#ww-primary'),
        'records': ('继续我的写作', '回到上次题目，查看首稿和修订。写作输入随本册学习记录一并备份。', '#writing-workbench'),
    }
    for section, (title, summary, href) in labels.items():
        if section not in before.sections:
            continue
        entry = f'<aside class="ww-entry"><div><strong>{title}</strong><p>{summary}</p></div><a href="{href}">进入 →</a></aside>'
        inserts.append((before.sections[section][0], mark(section + '-entry', entry)))
    result = base
    for at, html in sorted(inserts, reverse=True):
        result = result[:at] + html + result[at:]
    after = Structure(result)
    assert re.sub(PATTERN, '', result, flags=re.S) == base, 'Changed content outside writing markers'
    assert len(after.ids) == len(set(after.ids)), 'Duplicate IDs'
    assert len(after.fields) == len(set(after.fields)), 'Duplicate saved fields'
    assert set(before.fields).issubset(after.fields), 'An existing saved field was lost'
    from collections import Counter
    assert not (Counter(before.media) - Counter(after.media)), 'Existing media removed'
    return result, {
        'sourced_tasks': 6,
        'new_save_fields': len(after.fields) - len(before.fields),
        'original_fields_preserved': len(before.fields),
        'original_content_preserved_exactly': True,
        'assets_embedded': ['writing-workbench.css', 'writing-workbench.js'],
    }


if __name__ == '__main__':
    from build_writing_workbench import build
    build()
    raw = (BOOK / '开始学习.html').read_text(encoding='utf-8')
    page, report = apply(raw)
    assert apply(page)[0] == page
    qa = HERE / 'writing-workbench-qa'
    qa.mkdir(exist_ok=True)
    preview = page.replace('<head>', '<head><base href="' + BOOK.as_uri() + '/">', 1)
    (qa / 'preview.html').write_text(preview, encoding='utf-8')
    report['idempotent'] = True
    (qa / 'integration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
