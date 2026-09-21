"""Expand the existing background units without rebuilding other workbook sections."""
from pathlib import Path
from collections import Counter
import json
import re
import shutil
from bs4 import BeautifulSoup
from markdown import markdown

HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN = BOOK / '开始学习.html'
SOURCE = BOOK / 'enrichment-topics.json'
BACKUP = HERE / 'backups' / '开始学习-before-background-expansion.html'
DATA_BACKUP = HERE / 'backups' / 'enrichment-topics-before-expansion.json'
FILES = ['expanded-family.json', 'expanded-food.json', 'expanded-travel.json', 'expanded-media.json']
CSS = '''
.background-expanded>summary strong,.background-expanded>summary small,.background-expanded .enrichment-time{color:#ad2430}
.background-expanded>summary{border-left:4px solid #ad2430}
.background-expanded .background-lesson{line-height:1.9}
.background-expanded .background-lesson h3{margin-top:32px;padding-top:12px;border-top:1px solid #ead2d0}
.background-expanded .background-lesson h3:first-child{margin-top:0;border-top:0;padding-top:0}
.background-expanded .background-lesson table{display:block;max-width:100%;overflow-x:auto;font-size:14px}
.background-expanded .background-lesson th,.background-expanded .background-lesson td{vertical-align:top;white-space:normal;min-width:145px}
.background-expanded .background-lesson td:last-child{min-width:210px}
.background-expanded .background-lesson p{margin:14px 0}
.background-expanded .background-lesson li{margin:10px 0}
@media(max-width:600px){
 .background-expanded .background-lesson{font-size:15px}
 .background-expanded .background-lesson h3{font-size:19px;line-height:1.6}
 .background-expanded .enrichment-time{white-space:normal}
 .background-expanded .background-lesson table,.background-expanded .background-lesson tbody{display:block;width:100%;overflow:visible}
 .background-expanded .background-lesson thead{display:none}
 .background-expanded .background-lesson tr{display:block;margin:0 0 16px;padding:10px 12px;border:1px solid #ead2d0;border-radius:6px}
 .background-expanded .background-lesson td{display:block;min-width:0!important;width:auto;padding:6px 0;border:0;overflow-wrap:break-word}
 .background-expanded .background-lesson td:first-child{font-size:17px;font-weight:700}
 .background-expanded .background-lesson td:nth-child(2)::before{content:'中文：';font-weight:700}
 .background-expanded .background-lesson td:nth-child(3)::before{content:'例句：';font-weight:700}
}
'''


def replace_markdown(node, value):
    fragment = BeautifulSoup(markdown(value, extensions=['tables', 'fenced_code', 'nl2br']), 'html.parser')
    node.clear()
    for child in list(fragment.contents):
        node.append(child.extract())
    if 'resource-added' not in node.get('class', []):
        node['class'] = node.get('class', []) + ['resource-added']


def invariants(soup):
    return {
        'fields': Counter(n['data-save'] for n in soup.select('[data-save]')),
        'panels': [n['id'] for n in soup.select('.panel')],
        'enrichment': [n['data-enrichment'] for n in soup.select('[data-enrichment]')],
        'audio': [str(n) for n in soup.select('audio')],
        'resource_cards': len(soup.select('.res-card')),
    }


def expand():
    units = [json.loads((HERE / name).read_text(encoding='utf8')) for name in FILES]
    assert len({u['id'] for u in units}) == 4
    source = json.loads(SOURCE.read_text(encoding='utf8'))
    source_by_id = {u['id']: u for u in source}
    page = MAIN.read_text(encoding='utf8')
    soup = BeautifulSoup(page, 'html.parser')
    before = invariants(soup)
    glossary_node = soup.select_one('#lookup-glossary')
    glossary = json.loads(glossary_node.string)
    stats = []

    for u in units:
        uid = u['id']
        node = soup.select_one(f'#background [data-enrichment="{uid}"]')
        assert node is not None, uid
        assert node.get('data-optional') == 'true', uid
        assert len(u['glossary']) >= 16, uid
        assert all(key in u for key in ('title', 'intro', 'lesson_md', 'task_prompt', 'feedback_md', 'transfer_prompt', 'minutes'))
        assert not re.search(r'官方|核验|自编|非真题|四科|听说读写', u['lesson_md']), uid
        node['class'] = list(dict.fromkeys(node.get('class', []) + ['background-expanded']))
        summary = node.find('summary', recursive=False)
        summary.select_one('strong').string = u['title']
        summary.select_one('small').string = u['intro']
        summary.select_one('.enrichment-time').string = f"约 {u['minutes']} 分钟 · 可分次"
        body = node.select_one('.enrichment-body')
        lesson = body.find('div', class_='prose', recursive=False)
        replace_markdown(lesson, u['lesson_md'])
        lesson['class'] = list(dict.fromkeys(lesson.get('class', []) + ['background-lesson']))
        attempt = node.select_one('.enrichment-attempt')
        attempt.select_one('h3').string = '回顾一下（可选）'
        attempt.select_one('p.small').string = '可以默想，也可以记下想留下的表达；每次只选一个小问题即可。'
        attempt.select_one('label.field > span').string = '我的理解／想记住的表达（可留空）'
        replace_markdown(attempt.select_one('.prose'), u['task_prompt'])
        feedback = node.select_one('.enrichment-feedback')
        feedback.find('h3').string = '参考理解与表达'
        prose_nodes = feedback.select(':scope > .prose')
        assert len(prose_nodes) == 2
        replace_markdown(prose_nodes[0], u['feedback_md'])
        replace_markdown(prose_nodes[1], u['transfer_prompt'])
        feedback.select('h3')[1].string = '联系自己的生活（可选）'
        feedback.select('label.field > span')[0].string = '补充理解／新学到的表达'
        feedback.select('label.field > span')[1].string = '我的例子／下次回顾记录'

        for word in u['glossary']:
            term = re.sub(r'\s+', ' ', word['term'].strip().lower())
            entry = {k: word[k] for k in ('meaning', 'pos', 'chunk', 'example')}
            entry['source'] = '话题背景 · ' + u['title'].split('：')[0]
            old = glossary.get(term, [])
            old = [item for item in old if any(item.get(k) != entry[k] for k in ('meaning', 'pos', 'chunk', 'example'))]
            glossary[term] = [entry] + old
        for key in ('title', 'intro', 'lesson_md', 'task_prompt', 'feedback_md', 'transfer_prompt', 'minutes', 'glossary'):
            source_by_id[uid][key] = u[key]
        headings = [h.get_text(' ', strip=True) for h in lesson.select('h3')]
        stats.append({'id': uid, 'title': u['title'], 'glossary_entries': len(u['glossary']), 'lesson_characters': len(u['lesson_md']), 'headings': headings})

    section = soup.select_one('#background .background-expanded').parent
    section.select_one('.section-heading h2').string = '话题背景学习单元'
    section.select_one('.section-heading p.small').string = '先认识话题中的基本概念，再读生活情境、积累词语和表达。每次可以只学一个情境，新增内容已标红。'
    section.select_one('.ui-kicker').string = 'TOPIC BACKGROUND'
    glossary_node.string = json.dumps(glossary, ensure_ascii=False).replace('</', r'<\/')
    style = soup.select_one('#background-expansion-style')
    if style is None:
        style = soup.new_tag('style', id='background-expansion-style')
        soup.head.append(style)
    style.string = CSS
    result = str(soup)
    after = invariants(soup)
    assert before == after, 'Workbook fields or unrelated content changed'
    assert len(soup.select('#background .background-expanded')) == 4
    assert len({n['id'] for n in soup.select('[id]')}) == len(soup.select('[id]')), 'Duplicate IDs'
    BACKUP.parent.mkdir(exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(MAIN, BACKUP)
    if not DATA_BACKUP.exists():
        shutil.copy2(SOURCE, DATA_BACKUP)
    SOURCE.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    MAIN.write_text(result, encoding='utf8')
    report = {'units': stats, 'saved_fields': sum(after['fields'].values()), 'panels': len(after['panels']), 'audio_controls': len(after['audio']), 'resource_cards': after['resource_cards'], 'preserved_existing_fields': True}
    (HERE / 'background-expansion-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    expand()
