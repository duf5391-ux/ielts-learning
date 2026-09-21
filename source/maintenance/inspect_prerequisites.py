from pathlib import Path
from bs4 import BeautifulSoup
import json, sys
sys.stdout.reconfigure(encoding='utf8')
ROOT = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
OUT = Path('D:/IELTS-Work/content-repair-20260920')
OUT.mkdir(parents=True, exist_ok=True)
s = BeautifulSoup((BOOK/'开始学习.html').read_text(encoding='utf8'),'html.parser')
selectors = ['#topic-education','#topic-work','#topic-technology','#usage-05','#topical-vocabulary'] + [f'[data-audit-target="audit-{n:03}"]' for n in (21,22,23,24,67,69,70,83,84)]
for i, sel in enumerate(selectors):
    n = s.select_one(sel)
    if not n: print('Missing',sel);continue
    clone=BeautifulSoup(str(n),'html.parser')
    for a in clone.select('[data-content-audit],[data-learning-review]'): a.decompose()
    (OUT/f'node-{i}.html').write_text(str(clone),encoding='utf8')
    (OUT/f'node-{i}.txt').write_text(clone.get_text('\n',strip=True),encoding='utf8')
    print(i,sel,'chars',len(n.get_text()),'fields',[x['data-save'] for x in n.select('[data-save]')][:10])
for i, script in enumerate(s.select('script')):
    (OUT/f'script-{i}.js').write_text(script.get_text(),encoding='utf8')
    print('SCRIPT',i,script.get('id'),script.get('src'),len(script.get_text()))
print('head and sidebar')
print(str(s.select_one('aside'))[:5000])
