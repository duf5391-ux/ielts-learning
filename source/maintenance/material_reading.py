"""Render authored material reading and source-linked writing preparation."""
from pathlib import Path
from html import escape as E
from functools import lru_cache
import json, re

ROOT = Path(__file__).resolve().parent
PACKS = ['reading-base.json', 'reading-cambridge.json', 'reading-official-gap-ai.json']
READING_FILES = ['authentic-reading-cases.json', 'authentic-reading-official-cases.json', 'authentic-reading-cambridge-cases.json', 'authentic-reading-gap-cases.json']

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

@lru_cache(maxsize=1)
def source_cases():
    return {c['id']: c for name in READING_FILES + ['authentic-writing-cases.json'] for c in read(ROOT/name)['cases']}

@lru_cache(maxsize=2)
def lessons(required=False):
    result = {}
    for name in PACKS:
        path = ROOT/'content-pipeline'/'intensive'/name
        if not path.exists():
            if required: raise ValueError('Missing content package: '+name)
            continue
        for c in read(path)['cases']:
            assert c['id'] not in result, c['id']
            result[c['id']] = c
    return result

def norm(text):
    return re.sub(r'\s+', ' ', text).strip()

def validate(data, cases):
    expected = {c['id'] for c in cases.values() if c['skill'] == 'reading'}
    assert set(data) == expected, {'missing': sorted(expected-set(data)), 'extra': sorted(set(data)-expected)}
    errors = []
    forbidden = re.compile(r'Q\s*\d+|第\s*\d+\s*题|干扰项|读选项|正确选项|解题步骤|解题技巧|定位答案|答案是[ABCD]')
    for cid, lesson in data.items():
        source = cases[cid]
        paragraphs = source['paragraphs']
        original = norm(' '.join(p['text'] if isinstance(p, dict) else p for p in paragraphs))
        if [p['label'] for p in lesson['paragraphs']] != [p.get('label', '') if isinstance(p, dict) else '' for p in paragraphs]:
            errors.append((cid, 'paragraph coverage/order'))
        if len(lesson['phrases']) < 3 or len(lesson['sentences']) < 2:
            errors.append((cid, 'insufficient authored language content'))
        for entry in lesson['phrases'] + lesson['sentences']:
            if norm(entry['text']) not in original: errors.append((cid, 'quote not in source', entry['text']))
        if forbidden.search(json.dumps(lesson, ensure_ascii=False)):
            errors.append((cid, 'exam-answer explanation in material reading'))
        for phrase in lesson.get('writing', []):
            if norm(phrase['phrase']) not in original: errors.append((cid, 'writing phrase not in source', phrase['phrase']))
            for match in phrase['matches']:
                target = cases.get(match['caseId'])
                if not target or target['skill'] not in ['writing1', 'writing2']:
                    errors.append((cid, 'invalid writing target', match['caseId']))
                if not match['example'].strip() or not match['fit'].strip(): errors.append((cid, 'empty writing preparation'))
        if not any(p.get('matches') for p in lesson.get('writing', [])) and not lesson.get('noWritingMatchReason'):
            errors.append((cid, 'missing explanation for no writing match'))
    assert not errors, errors
    return {'readingUnits': len(data), 'paragraphs': sum(len(x['paragraphs']) for x in data.values()), 'phrases': sum(len(x['phrases']) for x in data.values()), 'sentences': sum(len(x['sentences']) for x in data.values()), 'writingMatches': sum(len(p['matches']) for x in data.values() for p in x.get('writing', []))}

def intensive_id(cid): return 'material-reading-'+cid
def writing_id(cid): return 'writing-prep-'+cid
def case_id(c): return c['skill']+'-case-'+c['id']
def p(text, cls=''): return '<p'+(' class="'+cls+'"' if cls else '')+'>'+E(text)+'</p>'

def render_reading(c, lesson):
    out = ['<details class="material-reading" id="'+intensive_id(c['id'])+'" data-material-source="'+E(c['id'])+'"><summary>材料精读 · 内容与词句</summary><div class="mr-body">', p(lesson['overview'], 'mr-overview')]
    for i, (source, annotation) in enumerate(zip(c['paragraphs'], lesson['paragraphs'])):
        out += ['<section class="mr-paragraph"><h4>'+E(annotation['label'] or '第'+str(i+1)+'段')+'</h4><blockquote lang="en">'+E(source['text'])+'</blockquote>', p(annotation['explanation']), '</section>']
    out.append('<section class="mr-phrases"><h4>词语与搭配</h4>')
    for entry in lesson['phrases']:
        out += ['<div class="mr-phrase"><strong lang="en">'+E(entry['text'])+'</strong>', p(entry['meaning']), p(entry['usage']), '</div>']
    out.append('</section><section class="mr-sentences"><h4>句子精读</h4>')
    for entry in lesson['sentences']:
        out += ['<div class="mr-sentence"><blockquote lang="en">'+E(entry['text'])+'</blockquote>', p(entry['translation']), p(entry['explanation']), '</div>']
    out.append('</section>')
    useful = [x for x in lesson.get('writing', []) if x.get('matches')]
    if useful:
        out.append('<section class="mr-writing-links"><h4>这篇材料里可用于写作的表达</h4>')
        for entry in useful:
            out += ['<div class="mr-phrase"><strong lang="en">'+E(entry['phrase'])+'</strong>', p(entry['meaning']), p(entry['usage'])]
            out.append('<p>'+ ' · '.join('<a href="#'+writing_id(m['caseId'])+'-from-'+E(c['id'])+'">用于写作：'+E(m['fit'])+'</a>' for m in entry['matches'])+'</p></div>')
        out.append('</section>')
    out += [p('读完讲解，可以把原文连起来再读一次；想保留的词句可使用已有收藏功能。'), '</div></details>']
    return ''.join(out)

def writing_entries(cid, data):
    return [(source, phrase, match) for source, lesson in data.items() for phrase in lesson.get('writing', []) for match in phrase['matches'] if match['caseId'] == cid]

def render_writing(c, data, cases):
    entries = writing_entries(c['id'], data)
    if not entries: return ''
    groups = {}
    for source, phrase, match in entries: groups.setdefault(source, []).append((phrase, match))
    out = ['<section class="material-writing" id="'+writing_id(c['id'])+'" data-writing-case="'+E(c['id'])+'"><h3>写作前置 · 文中表达</h3>', p('下面的表达来自阅读材料，例句按本题语境编写。选择确实需要的表达即可。', 'mr-prep-note')]
    for source, values in groups.items():
        out.append('<details class="mr-source-group" id="'+writing_id(c['id'])+'-from-'+E(source)+'" data-reading-source="'+E(source)+'"><summary>'+E(cases[source]['title'])+'</summary>')
        for phrase, match in values:
            out += ['<article class="mr-phrase"><h4 lang="en">'+E(phrase['phrase'])+'</h4>', p(phrase['meaning']), p(phrase['usage']), '<p class="mr-example-label">本题例句 · 编写示范</p><blockquote lang="en">'+E(match['example'])+'</blockquote>', p(match['fit']), '</article>']
        out.append('<p><a href="#'+intensive_id(source)+'">回到这份材料的精读</a></p></details>')
    out.append('</section>')
    return ''.join(out)

def simple_intensive(lesson):
    return {'structure': [lesson['overview']]+[p['label']+'：'+p['explanation'] for p in lesson['paragraphs']], 'phrases': [{'phrase': p['text'], 'meaning': p['meaning'], 'explanation': p['usage']} for p in lesson['phrases']], 'sentences': [{'text': s['text'], 'translation': s['translation'], 'explanation': s['explanation']} for s in lesson['sentences']]}

def daily_variants(data, cases):
    variants = []
    for cid, lesson in data.items():
        c = cases[cid]
        words = sum(len(p['text'].split()) for p in c['paragraphs'])
        targets = list(dict.fromkeys(m['caseId'] for p in lesson.get('writing', []) for m in p['matches']))
        variants.append({'id': cid, 'title': c['title'], 'minMinutes': 30 if words > 600 else 15, 'stages': [
            {'title': '阅读 · '+c['title'], 'target': case_id(c), 'instruction': '阅读本单元原文并完成题目，按自己的节奏作答。', 'weight': 0.55},
            {'title': '材料精读 · 内容与词句', 'target': intensive_id(cid), 'instruction': '回到刚读过的原文，看逐段内容、词块和长句讲解，再连起来读。', 'weight': 0.45}
        ], 'writingTargets': [{'id': wid, 'skill': cases[wid]['skill'], 'title': cases[wid]['title'], 'target': case_id(cases[wid]), 'primerTarget': writing_id(wid)} for wid in targets]})
    return variants
