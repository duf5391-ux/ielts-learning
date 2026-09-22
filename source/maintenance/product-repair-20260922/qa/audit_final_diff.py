from pathlib import Path
import hashlib,json,re
h=Path(__file__).parent
old=h/'combined-first-candidate.html';final=h/'final-candidate.html'
hash_text=lambda x:hashlib.sha256(x.encode()).hexdigest()
def scripts(p):
 out={}
 for i,(attrs,body) in enumerate(re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>',p.read_text(encoding='utf8'),re.I)):
  props=dict(re.findall(r'([\w-]+)="([^"]*)"',attrs))
  out[props.get('id',f'unnamed-{i}')]={'type':props.get('type',''),'sha256':hash_text(body),'src':props.get('src')}
 return out
a,b=scripts(old),scripts(final)
changed=[k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)]
required=['learning-adjust-script','daily-study-script','daily-study-model-script','record-concurrency-model-script','health-study-bridge-script','health-study-ui-script']
result={'base_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'changed_scripts':changed,'unchanged_scripts':[k for k in a if a.get(k)==b.get(k)],'required_unchanged':{k:a.get(k)==b.get(k) and k in a for k in required}}
(h/'final-diff.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(result,indent=2,ensure_ascii=False))
