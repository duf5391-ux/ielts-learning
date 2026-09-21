from pathlib import Path
from bs4 import BeautifulSoup
import json,urllib.parse
work=Path('C:/Users/Admin1/Documents/ChatGPT/ielts')
root=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
old=BeautifulSoup((work/'backups/开始学习-before-copy-cleanup.html').read_text(encoding='utf8'),'html.parser')
now=BeautifulSoup((root/'开始学习.html').read_text(encoding='utf8'),'html.parser')
result={}
for label,selector in [('panels','.panel'),('chapters','.chapter.panel'),('new_units','.res-unit'),('added_background','#background > .resource-added'),('enrichment','.enrichment-unit'),('word_cards','.tv-card'),('audio','audio'),('fields','[data-save]')]:
 a=old.select(selector);b=now.select(selector)
 result[label]={'before':len(a),'after':len(b),'preserved':len(a)==len(b)}
result['field_keys_preserved']=sorted(n['data-save'] for n in old.select('[data-save]'))==sorted(n['data-save'] for n in now.select('[data-save]'))
result['audio_sources_preserved']=[(n.get('src'),[s.get('src') for s in n.select('source')]) for n in old.select('audio')]==[(n.get('src'),[s.get('src') for s in n.select('source')]) for n in now.select('audio')]
ids={n['id'] for n in now.select('[id]')}
result['missing_anchors']=sorted({a['href'] for a in now.select('a[href^="#"]') if len(a['href'])>1 and urllib.parse.unquote(a['href'][1:]) not in ids})
result['missing_nav_targets']=sorted({a['data-go'] for a in now.select('[data-go]') if a['data-go'] not in ids})
qa=work/'cleanup-ui-qa';qa.mkdir(exist_ok=True)
(qa/'static-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
