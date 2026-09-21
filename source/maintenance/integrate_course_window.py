"""Add or update the staged personal course window without rebuilding the book.

Optional --course imports an authored package into the persistent course catalogue.
Existing course IDs are immutable: publish changed teaching as a new course ID.
Browser attempts are kept separately by course and task ID.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN = BOOK / '开始学习.html'
REGISTRY = HERE / 'course-window-courses.json'
PATTERN = r'<!--COURSE-WINDOW-V1:[^>]+-->.*?<!--/COURSE-WINDOW-V1-->'
STAGES = ['baseline', 'understand', 'guided', 'transfer', 'delayed']


def require(value, message):
    if not value:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 100000


def validate_package(package):
    require(isinstance(package, dict) and package.get('version') == 1, '课程版本必须为 1')
    courses = package.get('courses')
    require(isinstance(courses, list) and len(courses) <= 100, '课程列表无效')
    course_ids = set()
    for course in courses:
        require(isinstance(course, dict), '课程必须为对象')
        for key in ['id', 'title', 'requirement', 'goal']:
            require(nonempty(course.get(key)), f'课程缺少 {key}')
        require(course['id'] not in course_ids, '课程 ID 重复')
        course_ids.add(course['id'])
        require(isinstance(course.get('sourceText'), str), '缺少原始材料文本')
        alignment = course.get('examAlignment')
        require(isinstance(alignment, dict), '课程缺少考试拟合说明')
        for key in ['exam', 'paper', 'taskType', 'scope']:
            require(nonempty(alignment.get(key)), f'考试拟合缺少 {key}')
        sources = alignment.get('sources')
        require(isinstance(sources, list) and sources, '缺少可核查的考试依据')
        require(all(isinstance(s, dict) and all(nonempty(s.get(k)) for k in ['id', 'title', 'url']) and s['url'].startswith('https://') for s in sources), '考试依据链接格式无效')
        source_ids = {s['id'] for s in sources}
        require(len(source_ids) == len(sources), '考试依据 ID 重复')
        criteria = alignment.get('criteria')
        require(isinstance(criteria, list) and criteria, '缺少考试要求映射')
        for criterion in criteria:
            require(isinstance(criterion, dict) and all(nonempty(criterion.get(k)) for k in ['id', 'label', 'requirement']), '考试要求说明无效')
            require(isinstance(criterion.get('sourceIds'), list) and criterion['sourceIds'] and all(s in source_ids for s in criterion['sourceIds']), '考试要求缺少有效依据')
        criterion_ids = {c['id'] for c in criteria}
        require(len(criterion_ids) == len(criteria), '考试要求 ID 重复')
        require(isinstance(alignment.get('gaps'), list) and all(nonempty(g) for g in alignment['gaps']), '考试覆盖缺口格式无效')
        items = course.get('items')
        require(isinstance(items, list) and 1 <= len(items) <= 100, '材料点数量须为 1–100')
        item_ids = set()
        for item in items:
            require(isinstance(item, dict), '材料点必须为对象')
            for key in ['id', 'text', 'explanation', 'boundary']:
                require(nonempty(item.get(key)), f'材料点缺少 {key}')
            require(item['id'] not in item_ids, '材料点 ID 重复')
            item_ids.add(item['id'])
        stages = course.get('stages')
        require(isinstance(stages, list) and [s.get('id') for s in stages] == STAGES,
                '课程须依次包含 baseline / understand / guided / transfer / delayed 五阶段')
        task_ids, covered, exam_covered = set(), set(), set()
        for stage in stages:
            for key in ['title', 'purpose']:
                require(nonempty(stage.get(key)), f'阶段缺少 {key}')
            tasks = stage.get('tasks')
            require(isinstance(tasks, list) and 1 <= len(tasks) <= 100, '阶段须有可作答的练习')
            for task in tasks:
                require(isinstance(task, dict), '练习必须为对象')
                for key in ['id', 'prompt', 'reference', 'explanation']:
                    require(nonempty(task.get(key)), f'练习缺少 {key}')
                require(task['id'] not in task_ids, '练习 ID 重复')
                task_ids.add(task['id'])
                targets = task.get('targets')
                require(isinstance(targets, list) and targets and all(t in item_ids for t in targets),
                        '每个练习必须关联有效材料点')
                covered.update(targets)
                exam_targets = task.get('examTargets')
                require(isinstance(exam_targets, list) and exam_targets and all(t in criterion_ids for t in exam_targets), '练习须关联有效考试要求')
                exam_covered.update(exam_targets)
                require(nonempty(task.get('examUse')), '练习须说明在考试中怎样使用')
                require(task.get('practiceMode') in ['micro', 'exam-task'], '练习须区分微练习与考试任务')
                if 'materialSourceIds' in task:
                    require(isinstance(task['materialSourceIds'], list) and task['materialSourceIds'] and all(s in source_ids for s in task['materialSourceIds']), '练习选材来源引用无效')
                    require(nonempty(task.get('adaptationNote')), '有选材来源的练习须说明原题与改编范围')
                require(isinstance(task.get('rubric'), list) and task['rubric'] and all(nonempty(s) for s in task['rubric']),
                        '练习须有具体核对标准')
                require(task.get('type') in ['choice', 'text'], '仅支持 choice / text')
                if task['type'] == 'choice':
                    options = task.get('options')
                    require(isinstance(options, list) and 2 <= len(options) <= 10, '选择题选项无效')
                    require(all(isinstance(o, dict) and nonempty(o.get('id')) and nonempty(o.get('text')) for o in options), '选择题选项内容无效')
                    ids = [o['id'] for o in options]
                    require(len(ids) == len(set(ids)) and task.get('answer') in ids, '选择题答案或选项 ID 无效')
        require(covered == item_ids, '存在没有对应练习的材料点')
        require(exam_covered == criterion_ids, '已声明的考试要求缺少对应练习；请移到缺口说明或补齐练习')
    return package


class Inventory(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.ids, self.fields, self.media = [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if 'data-save' in a:
            self.fields.append(a['data-save'])
        if tag in ['img', 'audio', 'source']:
            self.media.append((tag, a.get('src')))

    handle_startendtag = handle_starttag


def strip_feature(page):
    return re.sub(PATTERN, '', page, flags=re.S)


def mark(name, content):
    return f'<!--COURSE-WINDOW-V1:{name}-->{content}<!--/COURSE-WINDOW-V1-->'


def build(page, package):
    original = strip_feature(page)
    page = original
    css = (HERE / 'course-window.css').read_text(encoding='utf-8')
    css += '\n.cw-entry{display:flex;align-items:center;justify-content:space-between;gap:24px;margin:0 0 26px;padding:20px 24px;border:1px solid var(--line,#d9ded4);border-left:3px solid var(--green,#204c42);border-radius:8px;background:#f0f4e9}.cw-entry strong{color:var(--green,#204c42)}.cw-entry p{font-size:14px;margin:5px 0 0}.cw-entry a{flex-shrink:0;font-size:14px}@media(max-width:700px){.cw-entry{align-items:flex-start;flex-direction:column;gap:10px;padding:18px}}'
    js = (HERE / 'course-window.js').read_text(encoding='utf-8')
    require('</script' not in js.lower(), 'JS contains an unsafe inline closing script tag')
    payload = json.dumps(package, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    page = page.replace('</head>', mark('style', '<style>' + css + '</style>') + '</head>', 1)
    nav = '<button data-go="course-window"><svg aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8M8 13h5M8 17h3"/></svg><span>定制学习</span></button>'
    pattern = r'(<button\b[^>]*\bdata-go="materials")'
    require(len(re.findall(pattern, page)) >= 1, '找不到工作台导航')
    page = re.sub(pattern, lambda m: mark('nav', nav) + m[1], page, count=1)
    entry = '<aside class="cw-entry"><div><strong>把你的材料，做成贴合考试的课程</strong><p>给出技巧、语料或词汇；选取相关考试材料，配上讲解和分阶段练习。</p></div><a href="#course-window">进入定制学习 →</a></aside>'
    for section in ['guide', 'materials']:
        pattern = r'(<section\b[^>]*\bid="' + section + r'"[^>]*>)'
        require(len(re.findall(pattern, page)) == 1, f'找不到 {section} 入口')
        page = re.sub(pattern, lambda m: m[1] + mark(section, entry), page, count=1)
    section = '<section class="panel workspace-panel" id="course-window" hidden><header class="chapter-head workspace-heading"><p class="ui-kicker">YOUR MATERIALS · EXAM PRACTICE</p><h1>定制学习</h1><p>从你给的内容出发，按考试真正要求的能力来设计课。</p></header><div id="course-window-app"></div><noscript>请启用 JavaScript 以使用定制学习窗口。</noscript></section>'
    require(page.count('</main>') == 1, '主内容边界不唯一')
    page = page.replace('</main>', mark('panel', section) + '</main>', 1)
    data = '<script id="course-window-data" type="application/json">' + payload + '</script>'
    code = '<script id="course-window-script">' + js + '</script>'
    code += '<script id="course-window-nav">(()=>{const sync=()=>{if(!document.getElementById("course-window")?.hidden){const label=document.getElementById("current-page-label");if(label)label.textContent="定制学习";}};window.addEventListener("hashchange",sync);sync();})();</script>'
    page = page.replace('</body>', mark('runtime', data + code) + '</body>', 1)
    require(strip_feature(page) == original, '原学习册发生非预期修改')
    before, after = Inventory(original), Inventory(page)
    require(len(after.ids) == len(set(after.ids)), '生成页面存在重复 ID')
    require(before.fields == after.fields, '原有学习记录字段发生修改')
    require(before.media == after.media, '原有图片/音频发生修改')
    return page, {'preserved_fields': len(before.fields), 'preserved_media': len(before.media), 'preserved_existing_content_exactly': True, 'courses': len(package['courses'])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--course', type=Path, help='已设计且检查过的课程包 JSON')
    parser.add_argument('--check', action='store_true', help='仅验证，不写文件')
    args = parser.parse_args()
    seed = validate_package(json.loads((HERE / 'course-window-seed.json').read_text(encoding='utf-8')))
    registry = validate_package(json.loads(REGISTRY.read_text(encoding='utf-8'))) if REGISTRY.exists() else {'version': 1, 'courses': []}
    if args.course:
        added = validate_package(json.loads(args.course.read_text(encoding='utf-8-sig')))
        by_id = {c['id']: c for c in registry['courses']}
        for course in added['courses']:
            require(course.get('status') != 'sample', '真实课程不能标为 sample')
            require(course['id'] not in by_id or by_id[course['id']] == course,
                    '此课程 ID 已存在不同内容；请为新版使用新的课程 ID，以保留原作答关系')
            by_id[course['id']] = course
        registry = {'version': 1, 'courses': list(by_id.values())}
    package = validate_package({'version': 1, 'courses': seed['courses'] + registry['courses']})
    for _ in range(3):
        raw = MAIN.read_bytes()
        page, report = build(raw.decode('utf-8'), package)
        require(build(page, package)[0] == page, '插入器未通过幂等性校验')
        if args.check:
            print(json.dumps({**report, 'check_only': True, 'idempotent': True}, ensure_ascii=False))
            return
        if MAIN.read_bytes() != raw:
            continue
        if raw != page.encode('utf-8'):
            backup = HERE / 'backups' / ('开始学习-before-course-window-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.html')
            backup.parent.mkdir(exist_ok=True)
            backup.write_bytes(raw)
            temporary = MAIN.with_name('开始学习.course-window.tmp')
            temporary.write_text(page, encoding='utf-8', newline='')
            if MAIN.read_bytes() != raw:
                temporary.unlink()
                continue
            os.replace(temporary, MAIN)
        REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')
        (BOOK / 'course-window-courses.json').write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding='utf-8')
        report.update(idempotent=True, main=str(MAIN), sha256=hashlib.sha256(MAIN.read_bytes()).hexdigest())
        qa = HERE / 'course-window-qa'
        qa.mkdir(exist_ok=True)
        (qa / 'integration.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))
        return
    raise RuntimeError('其他任务正在修改学习册，请稍后重试；本次未覆盖其改动。')


if __name__ == '__main__':
    main()
