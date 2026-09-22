"""Compose reviewed patches against the exact published workbook; never install here."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json, subprocess
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FORMAL = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
EXPECTED = '83346245cc01a3c48dcac31ce6c2b8a30744391cf6e4ae99f8db105103e6d166'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def apply_module(name, page):
    path = HERE / name / 'integrate.py'
    spec = importlib.util.spec_from_file_location('product_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply(page)

def main():
    assert sha(FORMAL) == EXPECTED, 'Formal changed. Inspect the other task before composing.'
    baseline = FORMAL.read_text(encoding='utf8')
    page = baseline
    for name in ['frontend', 'writing', 'navigation']:
        page = apply_module(name, page)
    before = BeautifulSoup(baseline, 'html.parser')
    after = BeautifulSoup(page, 'html.parser')
    fields = lambda s: Counter((n['data-save'], n.name, n.get('type',''), n.get('value',''), n.get_text() if n.name!='select' else '') for n in s.select('[data-save]'))
    assert fields(before) <= fields(after), 'An original answer field or default was altered'
    for node in before.select('select[data-save]'):
        target=after.select_one('select[data-save="'+node['data-save']+'"]')
        options=lambda n: Counter((o.get('value'),o.get_text(),o.has_attr('selected')) for o in n.find_all('option'))
        assert target and options(node) <= options(target), node['data-save']
    assert Counter(n['id'] for n in before.select('[id]')) <= Counter(n['id'] for n in after.select('[id]'))
    assert len(after.select('[id]')) == len({n['id'] for n in after.select('[id]')}), 'Duplicate ID'
    for tag in ['audio', 'source', 'img']:
        assert Counter(n.get('src') for n in before.find_all(tag)) <= Counter(n.get('src') for n in after.find_all(tag)), tag
    for key in ['record-concurrency-model-script', 'health-study-bridge-script', 'health-study-ui-script', 'energy-control-script', 'daily-study-script', 'daily-study-model-script']:
        if before.find(id=key):
            assert str(before.find(id=key)) == str(after.find(id=key)), key
    ids={n['id'] for n in after.select('[id]')}
    for link in after.select('a[href^="#"]'):
        target = link['href'][1:]
        if target:
            assert target in ids, 'Missing link: ' + target
    folder = HERE / 'syntax'
    folder.mkdir(exist_ok=True)
    count = 0
    for i, node in enumerate(after.find_all('script')):
        if node.get('type', '') in ['', 'text/javascript'] and node.string:
            path = folder / (str(i) + '.js')
            path.write_text(str(node.string), encoding='utf8')
            subprocess.run(['node', '--check', str(path)], check=True, capture_output=True)
            count += 1
    out = HERE / 'candidate.html'
    out.write_text(page, encoding='utf8')
    report = dict(pass_=True, baseline=EXPECTED, candidate=sha(out), fields=len(after.select('[data-save]')), oldFields=len(before.select('[data-save]')), scripts=count)
    report['pass'] = report.pop('pass_')
    (HERE / 'static.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
