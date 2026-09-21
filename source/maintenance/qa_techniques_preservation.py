"""Compare the techniques update with the captured workbook baseline."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import unquote
import hashlib
import json

HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
QA = HERE / 'techniques-qa'
baseline = json.loads((QA / 'baseline.json').read_text(encoding='utf8'))
page = BeautifulSoup((BOOK / '开始学习.html').read_text(encoding='utf8'), 'html.parser')
ids = [n['id'] for n in page.select('[id]')]
fields = [n['data-save'] for n in page.select('[data-save]')]
audio = [[n.get('src'), [x.get('src') for x in n.select('source')]] for n in page.select('audio')]
background_changes = []
background_units = page.select('#background .topic-reader, #background .enrichment-unit')
for before in baseline['background']:
    current = page.find(id=before['id']) if before['id'] else (background_units[before['index']] if before['index'] < len(background_units) else None)
    if current is None or hashlib.sha256(current.get_text().encode()).hexdigest() != before['text_hash']:
        background_changes.append(before['id'])
checks = {
    'missing_original_fields': sorted(set(baseline['fields']) - set(fields)),
    'missing_original_ids': sorted(set(baseline['ids']) - set(ids)),
    'duplicate_ids': [key for key, count in Counter(ids).items() if count > 1],
    'duplicate_field_keys': [key for key, count in Counter(fields).items() if count > 1],
    'changed_background_units': background_changes,
    'audio_changed': audio != baseline['audio'],
    'broken_anchors': sorted({a['href'] for a in page.select('a[href^="#"]') if len(a['href']) > 1 and unquote(a['href'][1:]) not in ids}),
    'broken_nav_targets': sorted({a['data-go'] for a in page.select('[data-go]') if a['data-go'] not in ids}),
}
result = {'pass': not any(checks.values()), 'checks': checks,
          'new_fields': sorted(set(fields) - set(baseline['fields'])),
          'new_ids': sorted(set(ids) - set(baseline['ids']))}
(QA / 'preservation-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['pass'] else 1)
