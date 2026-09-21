"""Minimal public HTTP resource checks. No browser, login, or full media downloads."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote,urljoin
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json,gzip,hashlib,subprocess

ROOT=Path(__file__).resolve().parent.parent
BASE='https://ielts-study-book-0920.harry-oditbap.chatgpt.site/'
DIST=ROOT/'web-publication/dist'
STATUS=ROOT/'research/public-deployment-status.json'
started=datetime.now(timezone.utc).isoformat()
status_before=json.loads(STATUS.read_text(encoding='utf-8'))
v2_commit='f50f9a430671aa940407e4ffc25875795344f156'
v2_html=subprocess.run(['git','show',v2_commit+':dist/index.html'],cwd=ROOT/'web-publication',check=True,capture_output=True).stdout
samples=[('',8192,False,'home'),('index.html',1024,False,'entry'),('原始参考/precise-official-listening-full.mp3',1024,False,'audio'),('原始参考/8ee8170c-Cambridge IELTS 21 - Academic.pdf',1024,False,'pdf'),('local-dictionary/dictionary-manifest.js',16384,True,'dictionary-manifest'),('local-dictionary/shards/nb.json.gz.bin',4096,True,'dictionary-gzip')]
headers_wanted=['Content-Type','Content-Length','Content-Range','Content-Encoding','Accept-Ranges','Cache-Control','ETag','Last-Modified','X-Content-Type-Options']
def selected_headers(response):return {key:response.headers.get(key) for key in headers_wanted if response.headers.get(key) is not None}
def check(item):
    relative,limit,whole,kind=item
    url=urljoin(BASE,quote(relative,safe='/'))
    result={'kind':kind,'path':relative or '/','url':url,'checked_at_utc':datetime.now(timezone.utc).isoformat()}
    try:
        request_headers={'Accept-Encoding':'identity','User-Agent':'IELTS-static-resource-audit/1.0'}
        with urlopen(Request(url,method='HEAD',headers=request_headers),timeout=30) as response:
            result['head']={'status':response.status,'headers':selected_headers(response)}
        if not whole:request_headers['Range']=f'bytes=0-{limit-1}'
        with urlopen(Request(url,headers=request_headers),timeout=30) as response:
            data=response.read(limit+1 if whole else limit)
            result['get']={'status':response.status,'headers':selected_headers(response),'bytes_read':len(data)}
        if kind in ('home','entry'):
            decoder=__import__('codecs').getincrementaldecoder('utf-8')('strict');decoded=decoder.decode(data,final=False)
            length=result['head']['headers'].get('Content-Length')
            result['html']={'utf8_prefix_valid':True,'doctype':decoded[:80].lower().find('<!doctype html')>=0,'charset_utf8':'charset="utf-8"' in decoded.lower() or "charset='utf-8'" in decoded.lower(),'contains_chinese':any('\u3400'<=c<='\u9fff' for c in decoded),'prefix_matches_deployed_v2_commit':data==v2_html[:len(data)],'head_size_matches_v2':int(length)==len(v2_html) if length is not None else None,'v2_entry_bytes':len(v2_html)}
        elif kind=='audio':result['magic_valid']=data.startswith(b'ID3') or (len(data)>1 and data[0]==255 and data[1]&224==224)
        elif kind=='pdf':result['magic_valid']=data.startswith(b'%PDF-')
        elif kind=='dictionary-manifest':
            result['full_body_obtained']=len(data)<=limit and len(data)==int(result['get']['headers'].get('Content-Length',-1))
            result['manifest_registration_present']=b'IELTSLocalDictionary.registerManifest' in data
            result['local_resource_sha256_matches']=hashlib.sha256(data).digest()==hashlib.sha256((DIST/relative).read_bytes()).digest()
        elif kind=='dictionary-gzip':
            result['gzip_magic_valid']=data.startswith(b'\x1f\x8b')
            payload=json.loads(gzip.decompress(data))
            result['decoded_payload']={'format':payload.get('format'),'version':payload.get('version'),'entries':len(payload.get('entries',{})),'aliases':len(payload.get('aliases',{}))}
            result['local_resource_sha256_matches']=hashlib.sha256(data).digest()==hashlib.sha256((DIST/relative).read_bytes()).digest()
            result['manual_gzip_decode_safe']=not result['get']['headers'].get('Content-Encoding') and result['gzip_magic_valid']
        result['prefix_matches_current_dist']=data==(DIST/(relative or 'index.html')).read_bytes()[:len(data)]
    except Exception as error:result['error']=str(error)
    return result
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,samples))
status_after=json.loads(STATUS.read_text(encoding='utf-8'))
evidence={'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'base_url':BASE,'last_succeeded_status_at_start':{key:status_before.get(key) for key in ('version_number','version_id','status','url','updated_at','source_commit','source_html_sha256','published_html_sha256')},'last_succeeded_status_at_end':{key:status_after.get(key) for key in ('version_number','version_id','status','updated_at')},'v2_commit_used_for_prefix_and_size_comparison':v2_commit,'download_boundary':'Home prefix only; audio/PDF first 1024 bytes; complete dictionary manifest and one 3015-byte gzip shard only. No whole HTML, audio, PDF, archive, authentication or user storage downloaded.','checks':results,'total_body_bytes_read':sum(x.get('get',{}).get('bytes_read',0) for x in results)}
(ROOT/'research/health-public-resource-check.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(evidence,ensure_ascii=False,indent=2))
