"""Validate offline references introduced by database-backed teaching and cases."""
from pathlib import Path
from urllib.parse import unquote
import json,re
from bs4 import BeautifulSoup
from build_authentic_case_database import BOOK,QA

def main():
    s=BeautifulSoup((BOOK/'开始学习.html').read_text(encoding='utf8'),'html.parser')
    ids={n['id'] for n in s.select('[id]')}
    checked=set();issues=[]
    for n in s.select('.case-bank a[href],.case-bank img[src],.remediated-teaching a[href],.remediated-teaching img[src],.authentic-supplement a[href],.authentic-supplement img[src],.framework-case-links a[href]'):
        raw=n.get('href') or n.get('src');value=unquote(raw)
        if value in checked:continue
        checked.add(value)
        if value.startswith('#'):
            if value[1:] not in ids:issues.append({'url':raw,'reason':'missing internal target'})
        elif not re.match(r'^(?:https?:|data:|mailto:)',value,re.I):
            file=value.split('#')[0].split('?')[0];p=Path(file)
            if not p.is_absolute():p=BOOK/p
            if not p.is_file():issues.append({'url':raw,'reason':'missing local file'})
    result={'unique_references_checked':len(checked),'issues':issues}
    (QA/'link-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False));assert not issues

if __name__=='__main__':main()
