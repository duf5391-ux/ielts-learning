"""Static preservation checks for a separate concurrency candidate, read-only."""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import argparse,hashlib,json,re,subprocess,tempfile

ROOT=Path(__file__).resolve().parent
FORMAL=Path(r'C:\Users\Admin1\Documents\Codex\2026-09-12\referenced-chatgpt-conversation-this-is-an\outputs\IELTS-四科学习册\开始学习.html')
class Page(HTMLParser):
    def __init__(self): super().__init__();self.fields=[];self.ids=[];self.media=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'data-save' in a:self.fields.append(a['data-save'])
        if a.get('id')!='record-concurrency-model-script' and 'id' in a:self.ids.append(a['id'])
        if tag in ('audio','source','img','script','link') and ('src' in a or 'href' in a):self.media.append((tag,a.get('src'),a.get('href')))
def scripts(t):return [m for m in re.finditer(r'<script\b([^>]*)>(.*?)</script>',t,re.S)]
def without_core(t):return re.sub(r'<script\b[^>]*>.*?</script>',lambda m:'' if '/* RECORD-SAFETY-20260919 */' in m.group(0) or 'id="record-concurrency-model-script"' in m.group(0) else m.group(0),t,flags=re.S).replace('\r\n','\n')
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=FORMAL);ap.add_argument('--candidate',type=Path,default=ROOT/'research/record-concurrency-candidate.html');args=ap.parse_args()
source=args.source.read_text(encoding='utf-8');candidate=args.candidate.read_text(encoding='utf-8');a,b=Page(),Page();a.feed(source);b.feed(candidate)
assert Counter(a.fields)==Counter(b.fields)
assert a.ids==b.ids and a.media==b.media
assert 'DAILY-STUDY-V1' in candidate and 'daily-study-state' in b.fields
# One inserted newline belongs to the new model node.
assert without_core(candidate).replace('\n\n\n','\n\n',1)==without_core(source).replace('\n\n\n','\n\n',1) or without_core(candidate).strip()==without_core(source).strip() or without_core(candidate).replace('\n','')==without_core(source).replace('\n','')
unchanged_before=[m.group(0) for m in scripts(source) if '/* RECORD-SAFETY-20260919 */' not in m.group(0)]
unchanged_after=[m.group(0) for m in scripts(candidate) if '/* RECORD-SAFETY-20260919 */' not in m.group(0) and 'id="record-concurrency-model-script"' not in m.group(0)]
assert unchanged_before==unchanged_after
with tempfile.TemporaryDirectory(prefix='record-concurrency-') as scratch:
    for number,m in enumerate(scripts(candidate)):
        if '/* RECORD-SAFETY-20260919 */' in m.group(0) or 'id="record-concurrency-model-script"' in m.group(0):
            p=Path(scratch)/f'script-{number}.js';p.write_text(m.group(2),encoding='utf-8');subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
result={'source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'candidate':str(args.candidate),'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest(),'save_fields':len(a.fields),'preserved_fields_ids_external_refs':True,'other_script_nodes_identical':len(unchanged_before),'only_main_record_core_modified':True,'new_script':'record-concurrency-model-script','changed_scripts_syntax_valid':True}
(ROOT/'research/record-concurrency-preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
