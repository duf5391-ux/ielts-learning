"""Read current delivery and compare it with the existing teaching snapshot.

Writes only this review's evidence file; does not change lessons or old reviews.
"""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import sys

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from review_snapshot_utils import item_fingerprints

MAIN = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
raw = MAIN.read_bytes()
soup = BeautifulSoup(raw.decode('utf-8'), 'html.parser')
snapshot = BeautifulSoup((ROOT / 'architecture-audit-qa/delivery-content-snapshot.html').read_text(encoding='utf-8'), 'html.parser')
review = json.loads((ROOT / 'research/teaching-current-review.json').read_text(encoding='utf-8'))
comparisons = []
for item in review['items']:
    before, after = item_fingerprints(snapshot, item), item_fingerprints(soup, item)
    changes = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    comparisons.append({'id': item['id'], 'changedSelectors': changes, 'matches': not changes})

selectors = ['#guide', '#records', '#listening-new-new-listening-campus-notes',
             '#listening-new-new-listening-team-roles', '#listening-new-new-listening-weather-table',
             '#listening-new-new-listening-lecture-outline', '#pp-listening',
             '.enrichment-unit[data-enrichment="speaking_part1_natural_answers"]',
             '.enrichment-unit[data-enrichment="speaking_part3_explain_compare"]',
             '#topic-education', '#topic-work']
nodes = []
for selector in selectors:
    original = soup.select_one(selector)
    if original is None:
        nodes.append({'selector': selector, 'missing': True})
        continue
    node = BeautifulSoup(str(original), 'html.parser')
    for overlay in list(node.select('[data-learning-audit],[data-content-audit],script,style')):
        overlay.decompose()
    nodes.append({'selector': selector, 'audio': len(node.select('audio')),
                  'recorders': len(node.select('[data-recorder]')),
                  'headings': [h.get_text(' ', strip=True) for h in node.select('h2,h3,h4,summary')],
                  'text': node.get_text(' ', strip=True)[:1400],
                  'audioSources': [a.get('src', '')[:200] for a in node.select('audio[src],audio source')]})

embedded = soup.select_one('#course-window-data')
course_data = json.loads(embedded.get_text()) if embedded else None
scripts = [n.get('src') for n in soup.select('script[src]')]
script_match = {}
for name in ['course-window.js', 'authentic-cases.js']:
    deployed = MAIN.parent / name
    local = (ROOT / name).read_text(encoding='utf-8').strip()
    script_match[name] = {
        'inlineExactMatch': any(local == n.get_text().strip() for n in soup.select('script:not([src])')),
        'externalExactMatch': deployed.exists() and deployed.read_bytes() == (ROOT / name).read_bytes(),
    }
evidence = {
    'checkedAt': datetime.now().astimezone().isoformat(timespec='seconds'),
    'scope': 'Static source and delivery review, not full content certification or a browser user-record inspection',
    'main': str(MAIN), 'mainSha256': hashlib.sha256(raw).hexdigest(), 'mainBytes': len(raw),
    'teachingComparison': {'matched': sum(x['matches'] for x in comparisons),
                           'changed': sum(not x['matches'] for x in comparisons), 'items': comparisons},
    'counts': {sel: len(soup.select(sel)) for sel in ['.exam-case', '.pp-unit', '[data-save]', '[data-recorder]', '#course-window-app']},
    'scripts': scripts, 'deployedScriptMatchesWorkspace': script_match,
    'embeddedCourses': [{'id': c.get('id'), 'status': c.get('status'), 'title': c.get('title')}
                        for c in (course_data or {}).get('courses', [])],
    'publishedCourseCount': len(json.loads((ROOT / 'course-window-courses.json').read_text(encoding='utf-8'))['courses']),
    'nodes': nodes, 'mainUnchangedDuringRead': raw == MAIN.read_bytes(),
}
output = ROOT / 'research/recheck-direction-evidence-20260920.json'
output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({k:v for k,v in evidence.items() if k not in ['nodes', 'teachingComparison']},ensure_ascii=False))
print(json.dumps(evidence['teachingComparison'],ensure_ascii=False))
for node in nodes:
    node['text'] = node.get('text', '')[:450]
    print(json.dumps(node,ensure_ascii=False))
