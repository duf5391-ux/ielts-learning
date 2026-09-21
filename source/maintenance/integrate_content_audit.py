"""Apply content-review labels and a readable palette without rebuilding lessons."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
from html import escape
import argparse
import hashlib
import json
import re

def select_nodes(soup, selector):
    """Scope frequent chapter selectors before running CSS over the large book."""
    match = re.match(r'^#([\w-]+)(\s+.*)?$', selector)
    if match:
        parent = soup.find(id=match.group(1))
        if parent is None: return []
        rest = (match.group(2) or '').strip()
        if not rest: return [parent]
        return parent.select((':scope ' if rest.startswith('>') else '') + rest)
    match = re.fullmatch(r'\[(data-[\w-]+)=["\']([^"\']+)["\']\]', selector)
    if match: return soup.find_all(attrs={match.group(1): match.group(2)})
    return soup.select(selector)

HERE = Path(__file__).resolve().parent
MAIN = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
QA = HERE / 'content-audit-qa'
CSS = '''
.background-expanded>summary strong,.background-expanded>summary small,.background-expanded .enrichment-time{color:var(--green,#204c42)}
.background-expanded>summary{border-left-color:var(--line,#d9ded4)}
.background-reader.is-updated>h2{color:var(--green,#204c42)!important}
.background-library .topic-tile.is-updated h3{color:var(--ink,#22312e)}
.content-audit-badge{display:inline-block!important;vertical-align:middle;align-self:flex-start;margin:6px 8px 6px 0;padding:3px 9px;border:1px solid;border-radius:5px;font:600 12px/1.7 'Microsoft YaHei',sans-serif!important;letter-spacing:0;white-space:nowrap}
.content-audit-badge[data-audit-status="达标"]{color:#245c3e!important;background:#eaf3ed;border-color:#b6cfbd}
.content-audit-badge[data-audit-status="存疑"]{color:#765000!important;background:#fff6dd;border-color:#ddc688}
.content-audit-badge[data-audit-status="不达标"]{color:#963434!important;background:#faeaea;border-color:#dfb5b5}
.content-audit-badge[data-audit-round="previous"]{color:#606961!important;background:#f0f1ed;border-color:#cdd2cb}
.content-audit-note{margin:12px 0 22px!important;padding:12px 16px!important;background:#f5f6f1!important;border:1px solid #d9ded4!important;border-radius:7px;color:var(--ink,#22312e)!important}
.content-audit-note>summary{font-size:13px!important;font-weight:500!important;color:var(--muted,#65726c)!important}
.content-audit-note p{font:14px/1.8 'Microsoft YaHei',sans-serif!important;margin:10px 0 0!important;color:var(--ink,#22312e)!important;overflow-wrap:anywhere}
.content-audit-summary{margin:18px 0 22px;padding:16px 18px;border:1px solid #d9ded4;border-radius:8px;background:#f6f7f2;color:var(--ink,#22312e)}
.content-audit-summary p{margin:7px 0;font-size:13px;line-height:1.8;color:var(--muted,#65726c)}
.content-audit-summary .content-audit-badge{margin-bottom:3px}
@media(max-width:700px){.content-audit-note,.content-audit-summary{padding:12px!important}.content-audit-badge{font-size:11px!important}}
'''


def normalized_text(soup):
    clone = BeautifulSoup(str(soup.main), 'html.parser')
    for node in clone.select('[data-content-audit]'):
        node.decompose()
    return clone.get_text(' ', strip=True).replace('红色部分可直接开始', '各单元均可直接开始')


def signatures(soup):
    return {
        'fields': sorted(n['data-save'] for n in soup.select('[data-save]')),
        'ids': sorted(n['id'] for n in soup.select('[id]') if not n.get('data-content-audit')),
        'scripts': [hashlib.sha256(n.get_text().encode()).hexdigest() for n in soup.select('script')],
        'audio': [n.get('src') for n in soup.select('audio source,audio[src]')],
        'images': [hashlib.sha256(n.get('src', '').encode()).hexdigest() for n in soup.select('img')],
        'text': normalized_text(soup),
    }


def apply_review(page, data=None):
    s = BeautifulSoup(page, 'html.parser')
    before = signatures(s)
    for node in list(s.select('[data-content-audit]')):
        node.decompose()
    for node in s.select('[data-audit-target]'):
        del node['data-audit-target']
    for node in s.main.find_all(string=lambda value: value and '红色部分可直接开始' in value):
        node.replace_with(str(node).replace('红色部分可直接开始', '各单元均可直接开始'))
    matches = [node for node in s.select('style') if '.res-usage-grid' in node.get_text() and '.res-filters' in node.get_text()]
    assert len(matches) == 1, 'Expected one resource stylesheet'
    matches[0].string = (HERE / 'resource-expansion.css').read_text(encoding='utf8')
    style = s.new_tag('style', id='content-audit-style', attrs={'data-content-audit': 'style'})
    style.string = CSS
    s.head.append(style)
    marked = []

    def badge(item, card=False):
        n = s.new_tag('span', attrs={'class': 'content-audit-badge', 'data-content-audit': 'card' if card else item['id'], 'data-audit-status': item['status']})
        previous = item.get('audit_round') == 'previous'
        n['data-audit-round'] = 'previous' if previous else 'current'
        n.string = ('前轮·' if previous else '') + item['status']
        n['title'] = ('前轮结论，本轮未重新核验：' if previous else '内容审核：') + item['status']
        return n

    def text(value):
        return '；'.join(str(x) for x in value) if isinstance(value, list) else str(value)

    if data:
        assert data['items'], 'Empty audit'
        seen = set()
        targets = []
        cards_by_anchor = {}
        for card in s.select('.res-card, .topic-tile, .qt-results a'):
            cards_by_anchor.setdefault(card.get('href'), []).append(card)
        for index, item in enumerate(data['items'], 1):
            item['status'] = {'可疑': '存疑', '未达标': '不达标'}.get(item['status'], item['status'])
            assert item['status'] in ['达标', '存疑', '不达标'], item
            item.setdefault('id', 'review-' + str(index))
            assert item['id'] not in seen, item['id']
            seen.add(item['id'])
            nodes = select_nodes(s, item['target_selector'])
            assert len(nodes) == 1, (item['title'], item['target_selector'], len(nodes))
            targets.append((item, nodes[0]))
        for item, target in targets:
            assert not target.select(':scope > [data-content-audit]'), 'Overlapping audit targets'
            target['data-audit-target'] = item['id']
            heading = target.find('summary', recursive=False) if target.name == 'details' else target.find(['h1', 'h2', 'h3', 'h4'], recursive=False)
            if heading is None:
                heading = target.select_one(':scope > header h1, :scope > header h2, :scope > .chapter-head h1')
            tag = badge(item)
            if heading:
                heading.append(tag)
            else:
                target.insert(0, tag)
            note = s.new_tag('details', attrs={'class': 'content-audit-note', 'data-content-audit': item['id']})
            summary = s.new_tag('summary')
            summary.string = '前轮审核（本轮未复核）' if item.get('audit_round') == 'previous' else '本轮审核：依据与官方对照'
            note.append(summary)
            for label, key in [('审查范围', 'scope'), ('判定', 'reason'), ('当前证据', 'evidence'), ('材料依据', 'source_basis'), ('拟合检查', 'fit_summary'), ('下一步', 'next_action')]:
                value = item.get(key)
                if value:
                    paragraph = s.new_tag('p')
                    paragraph.string = label + '：' + text(value)
                    note.append(paragraph)
            for source in item.get('benchmark_links', []):
                paragraph = s.new_tag('p')
                link = s.new_tag('a', href=source['url'], target='_blank', rel='noopener')
                link.string = source['title']
                paragraph.append(link)
                if source.get('note'): paragraph.append(' · ' + source['note'])
                note.append(paragraph)
            if target.name == 'details':
                heading.insert_after(note)
            elif heading and heading.parent is target:
                heading.insert_after(note)
            else:
                target.insert(1 if not heading else 0, note)
            anchor = item.get('anchor')
            if anchor:
                for card in cards_by_anchor.get('#' + anchor, []):
                    card.append(badge(item, True))
            marked.append({'id': item['id'], 'selector': item['target_selector'], 'status': item['status']})

        current_items = [x for x in data['items'] if x.get('audit_round') != 'previous']
        counts = Counter(x['status'] for x in current_items)
        box = s.new_tag('aside', attrs={'class': 'content-audit-summary', 'data-content-audit': 'summary'})
        title = s.new_tag('strong')
        title.string = '内容审核 · ' + str(data.get('date', '2026-09-19'))
        box.append(title)
        line = s.new_tag('div')
        for status in ['达标', '存疑', '不达标']:
            b = badge({'id': 'count', 'status': status})
            b.string = status + ' ' + str(counts[status])
            line.append(b)
        box.append(line)
        p = s.new_tag('p')
        p.string = '本轮复核 ' + str(len(current_items)) + ' 个教学块／材料项。按任务、例子、语言和答案证据评价，只针对注明用途，不是学习成绩。' + data.get('review_description', '此轮先标记，教学正文暂未替换。')
        box.append(p)
        library = s.select_one('#library > header.chapter-head')
        assert library
        library.insert_after(box)

    after = signatures(s)
    assert before == after, [key for key in before if before[key] != after[key]]
    return str(s), marked


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--colors-only', action='store_true')
    args = parser.parse_args()
    data = None if args.colors_only else json.loads((HERE / 'audit-content-20260919.json').read_text(encoding='utf8'))
    page, marked = apply_review(MAIN.read_text(encoding='utf8'), data)
    MAIN.write_text(page, encoding='utf8')
    QA.mkdir(exist_ok=True)
    result = {'marked': len(marked), 'items': marked, 'sha256': hashlib.sha256(page.encode()).hexdigest(), 'original_text_fields_scripts_audio_images_preserved': True}
    (QA / 'integration-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'marked': len(marked), 'sha256': result['sha256'], 'preserved': True}))
