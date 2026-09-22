"""Compose isolated mobile-performance and workspace changes on the latest formal book."""
import gzip
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser

import prepare_mobile_media as media


class Structure(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.fields, self.json_blocks = [], [], {}
        self.current = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        if 'data-save' in values:
            self.fields.append(values['data-save'])
        if tag == 'script' and values.get('type') == 'application/json':
            self.current = [values['id'], '']

    def handle_data(self, text):
        if self.current is not None:
            self.current[1] += text

    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.json_blocks[self.current[0]] = self.current[1]
            self.current = None


def prepare():
    from workspace_split import transform as workspace
    from runtime_performance import transform as performance
    media.prepare()
    path = media.STAGE / '开始学习.html'
    media_only = path.read_bytes()
    html = media_only.decode('utf-8')
    before = Structure(html)
    layers = []
    for name, transform in [('workspace_split', workspace), ('runtime_performance', performance)]:
        previous = html.encode('utf-8')
        html = transform(html)
        current = html.encode('utf-8')
        layers.append({'name': name, 'before_sha256': media.sha(previous), 'after_sha256': media.sha(current)})
    after = Structure(html)
    assert before.fields == after.fields and len(after.fields) == 3353
    assert not (Counter(before.ids) - Counter(after.ids))
    assert all(count == 1 for count in Counter(after.ids).values())
    assert before.json_blocks == after.json_blocks
    for marker in ['home', 'style', 'state', 'scripts']:
        pattern = r'<!--DAILY-STUDY-V1:' + marker + r'-->.*?<!--/DAILY-STUDY-V1:' + marker + r'-->'
        original = re.findall(pattern, media_only.decode('utf-8'), re.S)
        actual = re.findall(pattern, html, re.S)
        assert len(original) == 1 and actual == original
    candidate = html.encode('utf-8')
    temporary = path.with_suffix('.tmp')
    temporary.write_bytes(candidate)
    temporary.replace(path)
    report_path = media.STAGE / 'manifest.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    report['media_only_candidate_sha256'] = report['candidate_sha256']
    report['media_stage_non_media_content_identical'] = report.pop('all_non_media_content_identical')
    report.update(status='prepared_combined', candidate_sha256=media.sha(candidate),
                  after_bytes=len(candidate), after_gzip_bytes=len(gzip.compress(candidate, mtime=0)),
                  layers=layers, all_original_ids_preserved=True, all_json_contracts_identical=True,
                  daily_blocks_identical=True, release_ready=False)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ['status', 'candidate_sha256', 'after_bytes', 'after_gzip_bytes', 'save_fields', 'layers']}, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    prepare()
