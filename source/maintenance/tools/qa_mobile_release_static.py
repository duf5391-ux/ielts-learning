"""Cross-file preservation checks for the combined mobile/workbench release."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from prepare_mobile_media import BOOK, STAGE
from prepare_mobile_release import Structure
from qa_mobile_media import verify as verify_media


def verify(path=None):
    path = Path(path) if path else STAGE / '开始学习.html'
    raw = path.read_bytes()
    html = raw.decode('utf-8')
    baseline = (BOOK / '开始学习.html').read_text(encoding='utf-8')
    before, after = Structure(baseline), Structure(html)
    checks = []
    assert before.fields == after.fields and len(after.fields) == 3353
    checks.append('All 3353 ordered saved-field identities preserved')
    assert not (Counter(before.ids) - Counter(after.ids))
    assert all(n == 1 for n in Counter(after.ids).values())
    checks.append('Every original anchor retained exactly once; new IDs unique')
    assert before.json_blocks == after.json_blocks
    data = json.loads(after.json_blocks['learning-adjust-data'])
    assert len(data['units']) == 220
    checks.append('All 220 unit contracts and JSON catalogs byte-identical')
    for label in ['home', 'style', 'state', 'scripts']:
        regex = r'<!--DAILY-STUDY-V1:' + label + r'-->.*?<!--/DAILY-STUDY-V1:' + label + r'-->'
        original = re.findall(regex, baseline, re.S)
        assert len(original) == 1 and re.findall(regex, html, re.S) == original
    checks.append('All daily-study boundaries and module content preserved')
    nav = re.search(r'<aside\b[^>]*\bid="workspace-navigation".*?</aside>', html, re.S).group()
    buttons = re.findall(r'<button\b[^>]*data-go="([^"]+)"[^>]*>.*?</button>', nav, re.S)
    assert buttons == ['study', 'practice', 'tests', 'workspace', 'development'], buttons
    assert '学习工作台' in nav and '开发工作台' in nav
    checks.append('Five separate top-level destinations; original testing route retained')
    workspace = re.search(r'<section\b[^>]*\bid="workspace"[^>]*>.*?</section>', html, re.S).group()
    old_workspace = re.search(r'<section\b[^>]*\bid="workspace"[^>]*>.*?</section>', baseline, re.S).group()
    links = lambda text: re.findall(r'<a\b[^>]*href="([^"]+)"', text)
    assert links(workspace) == links(old_workspace)
    checks.append('All eight prior learning workbench destinations preserved')
    assert 'id="workspace-split-style"' in html and 'id="development"' in html
    checks.append('Independent development page and wider workbench styles present')
    media_report = verify_media(path)
    assert media_report['passed']
    checks.append('24 extracted media files byte-identical; every other media reference retained')
    result = {'candidate': str(path), 'candidate_sha256': hashlib.sha256(raw).hexdigest(),
              'passed': len(checks), 'total': len(checks), 'checks': checks,
              'user_records_read': False, 'requires_interaction_and_progressive_boot_qa': True}
    (STAGE / 'static-qa.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv) > 1 else None)
