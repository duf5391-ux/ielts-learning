"""Incremental candidate for the current formal book; never rebuild from an old page."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib, importlib.util, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')

def replace_script(text, name, code):
    pattern = r'(<script\b[^>]*\bid="'+re.escape(name)+r'"[^>]*>).*?(</script>)'
    assert len(re.findall(pattern,text,re.S)) == 1, name
    assert '</script' not in code
    return re.sub(pattern,lambda m:m[1]+code+m[2],text,count=1,flags=re.S)

def apply_vocabulary(text):
    for name, path in [('lookup-controller', ROOT/'local-dictionary/main-lookup.js'), ('vocabulary-review-controller', ROOT/'local-dictionary/vocabulary-review.js')]:
        text=replace_script(text,name,path.read_text(encoding='utf8'))
    block='<!--FEATURE-FIXES-V1:vocabulary--><style id="vocabulary-quick-marks-style">'+(HERE/'vocabulary-quick-marks.css').read_text(encoding='utf8')+'</style><script id="vocabulary-quick-marks-script">'+(HERE/'vocabulary-quick-marks.js').read_text(encoding='utf8')+'</script><!--/FEATURE-FIXES-V1:vocabulary-->'
    pattern=r'<!--FEATURE-FIXES-V1:vocabulary-->.*?<!--/FEATURE-FIXES-V1:vocabulary-->'
    return re.sub(pattern,lambda _:block,text,flags=re.S) if re.search(pattern,text,re.S) else text.replace('</body>',block+'</body>',1)

class Fields(HTMLParser):
    def __init__(self,text):
        super().__init__();self.fields=[];self.ids=[];self.units=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'data-save' in a:self.fields.append(a['data-save'])
        if 'id' in a:self.ids.append(a['id'])
        if 'data-learning-unit' in a:self.units.append(a['data-learning-unit'])

def main():
    source=(BOOK/'开始学习.html').read_bytes(); text=source.decode('utf8')
    candidate=apply_vocabulary(text)
    modules={}
    for name in ['writing-speaking','jijing']:
        spec=importlib.util.spec_from_file_location(name,HERE/name/'integrate.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); modules[name]=module
    candidate=modules['writing-speaking'].apply(candidate)
    candidate,jijing=modules['jijing'].apply(candidate)
    assets=modules['jijing'].assets()
    before,after=Fields(text),Fields(candidate)
    assert set(before.fields)<=set(after.fields),'Saved fields removed'
    assert set(before.units)<=set(after.units),'Learning units removed'
    assert len(after.fields)==len(set(after.fields)),'Duplicate saved fields'
    assert len(after.ids)==len(set(after.ids)),'Duplicate IDs'
    assert len(set(after.fields)-set(before.fields)) in (0,15),'Unexpected added fields'
    assert set(before.ids)<=set(after.ids),'Existing IDs removed'
    for marker in ['DAILY-STUDY-V1','daily-study-state','record-concurrency-model-script','RUNTIME-PERFORMANCE-V1','health-study-ui-script','learning-adjust-script']:
        assert marker in candidate,marker
    (HERE/'candidate.html').write_text(candidate,encoding='utf8',newline='')
    assert modules['jijing'].apply(modules['writing-speaking'].apply(apply_vocabulary(candidate)))[0]==candidate,'Composition not idempotent'
    result={'source_sha256':hashlib.sha256(source).hexdigest(),'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'save_fields':len(after.fields),'units':len(after.units),'ids_preserved':True,'jijing':jijing,'assets':assets}
    (HERE/'candidate-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))

if __name__=='__main__':main()
