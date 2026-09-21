"""Read-only publication consistency check. Writes evidence only under research/."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import hashlib, json, re

ROOT = Path(__file__).resolve().parent.parent
BOOK = Path(r'C:\Users\Admin1\Documents\Codex\2026-09-12\referenced-chatgpt-conversation-this-is-an\outputs\IELTS-四科学习册')
DIST = ROOT / 'web-publication/dist'
OUT = ROOT / 'research/health-ui-web-evidence-20260920'
OUT.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.fields=[]; self.scripts=[]; self.styles=[]; self.refs=[]; self.ids=[]; self.active=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if 'data-save' in a: self.fields.append(a['data-save'])
        for k in ('href','src','poster','data','action'):
            if a.get(k): self.refs.append((tag,k,a[k]))
        if a.get('style'):
            self.refs.extend((tag,'style',v) for v in re.findall(r'url\(\s*[\"\']?([^\"\')]+)',a['style']))
        if tag in ('script','style'): self.active=[tag,a,'']
    def handle_data(self,s):
        if self.active: self.active[2]+=s
    def handle_endtag(self,tag):
        if self.active and self.active[0]==tag:
            (self.scripts if tag=='script' else self.styles).append(self.active); self.active=None
def parse(t):
    p=Page(); p.feed(t); return p

local=(BOOK/'开始学习.html').read_text(encoding='utf-8')
web=(DIST/'index.html').read_text(encoding='utf-8')
lp,wp=parse(local),parse(web)
manifest=json.loads((ROOT/'web-publication/publication-manifest.json').read_text(encoding='utf-8'))
extra='\n<link rel="manifest" href="site.webmanifest">\n<meta name="theme-color" content="#356c57">\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-title" content="雅思学习册">\n<link rel="icon" href="app-icon.svg" type="image/svg+xml">\n'
mismatches=[]; replacements={x['path']:x for x in manifest['substitutions']}
for item in manifest['files']:
    rel=item['path']; source=BOOK/rel; dest=DIST/rel
    if rel=='开始学习.html': continue # Intentional index redirect.
    expected=item['sha256']
    if not dest.is_file() or sha(dest)!=expected: mismatches.append({'path':rel,'kind':'published-manifest'})
    expected_source=replacements.get(rel,{}).get('original_sha256',expected)
    if not source.is_file() or sha(source)!=expected_source: mismatches.append({'path':rel,'kind':'source-manifest'})
missing=[]; unsafe=[]; external=set(); linked_media=[]
for p in DIST.rglob('*'):
    if p.suffix.lower() not in ('.html','.htm','.css'): continue
    t=p.read_text(encoding='utf-8')
    parsed=parse(t) if p.suffix.lower()!='.css' else None
    refs=[v for _,_,v in parsed.refs] if parsed else []
    css='\n'.join(s[2] for s in parsed.styles) if parsed else t
    refs += re.findall(r'url\(\s*[\"\']?([^\"\')]+)',css)
    for value in refs:
        if value.startswith(('#','data:','blob:','mailto:','javascript:','tel:')): continue
        u=urlsplit(value)
        if u.scheme or u.netloc:
            if u.scheme.lower() in ('file','c','d','http'): unsafe.append({'page':p.relative_to(DIST).as_posix(),'value':value})
            else: external.add(u.netloc)
            continue
        if not u.path: continue
        target=(p.parent/unquote(u.path)).resolve()
        if not target.is_relative_to(DIST.resolve()): unsafe.append({'page':p.relative_to(DIST).as_posix(),'value':value})
        elif not target.is_file(): missing.append({'page':p.relative_to(DIST).as_posix(),'value':value})
        elif target.suffix.lower() in ('.mp3','.wav','.mp4','.webm'): linked_media.append(target.relative_to(DIST).as_posix())

for n,(_,attrs,code) in enumerate(wp.scripts):
    if attrs.get('src') or attrs.get('type','') not in ('','text/javascript','application/javascript'): continue
    name=attrs.get('id') or 'script-'+str(n)
    if name=='script-0' or 'energy' in name or 'daily' in name:
        (OUT/(name+'.js')).write_text(code,encoding='utf-8')

result={
 'formal_source':str(BOOK/'开始学习.html'),
 'formal_source_sha256':sha(BOOK/'开始学习.html'),
 'dist_index_sha256':sha(DIST/'index.html'),
 'manifest_source_matches':sha(BOOK/'开始学习.html')==manifest['source_html_sha256'],
 'manifest_dist_matches':sha(DIST/'index.html')==manifest['published_html_sha256'],
 'only_manifest_metadata_added':web==local.replace('</head>',extra+'</head>',1),
 'script_count':len(lp.scripts),'scripts_identical':lp.scripts==wp.scripts,
 'style_count':len(lp.styles),'styles_identical':lp.styles==wp.styles,
 'save_fields_count':len(lp.fields),'save_fields_identical':Counter(lp.fields)==Counter(wp.fields),
 'ids_identical':lp.ids==wp.ids,
 'all_manifest_resource_hash_mismatches':mismatches,
 'missing_local_dependencies':missing,
 'unsafe_or_http_html_css_refs':unsafe,
 'external_domains_in_html_css':sorted(external),
 'unique_linked_media':sorted(set(linked_media)),
 'dictionary_shard_files':len(list((DIST/'local-dictionary/shards').glob('*.js'))),
 'source_media_replacements':manifest['substitutions'],
 'deployment_status_file_exists':(ROOT/'research/public-deployment-status.json').is_file(),
 'boundaries':'Static copied-bundle validation only; no hosted response, microphone, translation service, or real-browser check.'
}
(OUT/'consistency.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
