"""Read back the published release and its two critical audio prefixes."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.parse
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=read(ROOT/'web-publication/publication-manifest.json')
deployment=read(HERE/'deployment.json')
assert deployment['status']=='completed' and deployment['conclusion']=='success'
assert deployment['headSha']==read(HERE/'publication-build.json')['commit']
base='https://duf5391-ux.github.io/ielts-learning/'
report=dict(deployment=deployment,source_html_sha256=manifest['source_html_sha256'],checks=[],
            network_scope='Local HTTP requests using the existing process proxy; mainland direct access measured separately.')
for name,rel,wanted in [('homepage','',manifest['published_html_sha256']),
    ('progressive_manifest',manifest['progressive_loading']['manifest']['path'],manifest['progressive_loading']['manifest']['sha256'])]:
    url=base+urllib.parse.quote(rel,safe='/')
    with urllib.request.urlopen(url,timeout=60) as response:
        content=response.read();status=response.status
    assert status==200 and sha(content)==wanted,(name,status,sha(content),wanted)
    report['checks'].append(dict(name=name,status=status,sha256=sha(content),bytes=len(content)))
for name,rel in [('official_audio','原始参考/precise-official-listening-full.mp3'),
                 ('jijing_audio','机经资料/jijing-20260920/ieltsa/assets/494b5ff8b614-2026-sep-hf-1.mp3')]:
    req=urllib.request.Request(base+urllib.parse.quote(rel,safe='/'),headers={'Range':'bytes=0-1023'})
    with urllib.request.urlopen(req,timeout=60) as response:
        content=response.read(1024);status=response.status
        mime=response.headers.get('Content-Type');ran=response.headers.get('Content-Range')
    assert status in (200,206) and mime.split(';')[0] in ('audio/mpeg','audio/mp3','audio/x-mpeg','audio/mpeg3') and content[:3]==b'ID3',(name,status,mime)
    assert status!=206 or (ran or '').startswith('bytes 0-1023/'),(name,ran)
    report['checks'].append(dict(name=name,status=status,content_type=mime,content_range=ran,prefix='ID3',scope='First 1024 bytes; not full playback'))
report.update({'pass':True,'checked_at':datetime.now(timezone.utc).isoformat()})
(HERE/'release-live.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
