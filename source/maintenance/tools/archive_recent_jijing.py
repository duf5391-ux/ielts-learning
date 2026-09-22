"""Archive explicitly public September 2026 Ieltsa study resources for offline use."""
import concurrent.futures as cf
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.codex-tools/jijing-libs'))
from bs4 import BeautifulSoup

OUT = ROOT / 'downloads/jijing-20260920/ieltsa'
BASE = 'https://ieltsactualtests.com'
for folder in ('raw', 'pages', 'assets', 'text'):
    (OUT / folder).mkdir(parents=True, exist_ok=True)

def get(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (personal offline study archive)'})
            with urllib.request.urlopen(req, timeout=55) as resp:
                return resp.read(), resp.headers.get('Content-Type', ''), resp.geturl()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

def file_info(path, **extra):
    b = path.read_bytes()
    return dict(path=path.relative_to(OUT).as_posix(), bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), **extra)

seeds = ['/zh/recalls/2026-09', '/zh/writing']
downloads = {}
urls = []
for seed in seeds:
    url = BASE + seed
    b, mime, final = get(url)
    downloads[url] = (b, mime, final)
    soup = BeautifulSoup(b.decode('utf-8'), 'html.parser')
    if 'recalls' in seed:
        urls.append(url)
    for a in soup.select('a[href]'):
        href = a['href']
        if re.fullmatch(r'/zh/(?:listening|reading)/2026-sep-[\w-]+', href) or re.fullmatch(r'/zh/writing/2026-09-\d+', href):
            urls.append(urllib.parse.urljoin(url, href))
urls = list(dict.fromkeys(urls))
page_paths = {u: 'pages/' + '/'.join(urllib.parse.urlparse(u).path.strip('/').split('/')[1:]).replace('/', '--') + '.html' for u in urls}
errors = []
with cf.ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(get, u): u for u in urls if u not in downloads}
    for f in cf.as_completed(futures):
        u = futures[f]
        try:
            downloads[u] = f.result()
            print('PAGE', u, len(downloads[u][0]), flush=True)
        except Exception as exc:
            errors.append({'url': u, 'error': str(exc)})

assets = {}
soups = {}
for url in urls:
    if url not in downloads:
        continue
    b, mime, final = downloads[url]
    soup = BeautifulSoup(b.decode('utf-8'), 'html.parser')
    soups[url] = soup
    main = soup.find_all('main')[-1] if soup.find('main') else soup.body
    for tag in main.select('img[src],audio[src],source[src]'):
        asset = urllib.parse.urljoin(url, tag['src'])
        if urllib.parse.urlparse(asset).hostname not in ('cdn.ieltsactualtests.com', 'ieltsactualtests.com'):
            continue
        suffix = Path(urllib.parse.urlparse(asset).path).suffix or '.bin'
        name = hashlib.sha256(asset.encode()).hexdigest()[:12] + '-' + Path(urllib.parse.urlparse(asset).path).name
        assets[asset] = 'assets/' + name

asset_records = []
def asset_job(item):
    url, rel = item
    path = OUT / rel
    if not path.exists():
        b, mime, final = get(url)
        if 'text/html' in mime:
            raise ValueError('asset returned HTML')
        path.write_bytes(b)
    return file_info(path, url=url)

with cf.ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(asset_job, item): item for item in assets.items()}
    for f in cf.as_completed(futures):
        u, rel = futures[f]
        try:
            record = f.result()
            asset_records.append(record)
            print('ASSET', rel, record['bytes'], flush=True)
        except Exception as exc:
            errors.append({'url': u, 'error': str(exc)})

STYLE = '''body{font:17px/1.75 system-ui,sans-serif;color:#233632;background:#f7f6ef;margin:0}main{max-width:1000px;margin:auto;padding:28px}h1,h2,h3{line-height:1.3;color:#174f44}h2{margin-top:2.2em}img{max-width:100%;height:auto}audio{width:100%;margin:12px 0}a{color:#176759}table{border-collapse:collapse;width:100%;overflow:auto}td,th{border:1px solid #ccd8d1;padding:8px}details{border:1px solid #ccd8d1;background:white;border-radius:8px;padding:14px;margin:16px 0}summary{cursor:pointer;font-weight:bold}li{margin:7px 0}.archive-note{background:#e7eee5;border-radius:12px;padding:18px;margin-bottom:24px}input,select,textarea{font:inherit;max-width:100%}nav{margin-bottom:24px}pre{white-space:pre-wrap}.content>div{margin:14px 0}'''
records = []
for url, soup in soups.items():
    rel = page_paths[url]
    raw_path = OUT / 'raw' / Path(rel).name
    raw_path.write_bytes(downloads[url][0])
    main = soup.find_all('main')[-1] if soup.find('main') else soup.body
    title = main.h1.get_text(' ', strip=True) if main.h1 else soup.title.get_text(' ', strip=True)
    for node in main.select('script,style,link,iframe,button,form,nav'):
        node.decompose()
    for node in main.find_all(True):
        for attr in list(node.attrs):
            if attr.startswith('on') or attr in ('class', 'style', 'srcset'):
                del node[attr]
        if node.name in ('input','select','textarea'):
            node['disabled'] = ''
        if node.name in ('img','source','audio') and node.get('src'):
            asset_url = urllib.parse.urljoin(url, node['src'])
            if asset_url in assets and (OUT / assets[asset_url]).exists():
                node['src'] = '../' + assets[asset_url]
        if node.name == 'a' and node.get('href'):
            target = urllib.parse.urljoin(url, node['href'])
            node['href'] = Path(page_paths[target]).name if target in page_paths else target
        if node.name == 'details':
            node.attrs.pop('open', None)
    content = str(main)
    note = '考生回忆重建资料；站方标注为2026年9月，具体考场来源未独立核实。听力使用重录音频。此离线版用于阅读、听音和核对答案，原网站的自动判分与云端功能不在此运行。'
    document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(title) + '</title><style>' + STYLE + '</style><body><main><nav><a href="../index.html">← 9月机经资料目录</a></nav><div class="archive-note">' + note + '<br>来源：<a href="' + html.escape(url) + '">Ieltsa 原页面</a></div>' + content + '</main></body></html>'
    path = OUT / rel
    path.write_text(document, encoding='utf-8')
    text_path = OUT / 'text' / (Path(rel).stem + '.txt')
    text_path.write_text(title + '\n' + url + '\n\n' + main.get_text('\n', strip=True), encoding='utf-8')
    kind = urllib.parse.urlparse(url).path.split('/')[2]
    records.append(dict(id='ieltsa-'+kind+'-'+Path(rel).stem, title=title, kind=kind, url=url, source_month='2026-09', nature='reconstructed_test' if kind != 'recalls' else 'reported_recall_collection', offline=file_info(path), raw=file_info(raw_path), text=file_info(text_path), local_audio=len(main.select('source[src^="../assets/"]')), local_images=len(main.select('img[src^="../assets/"]'))))

manifest = dict(batch_id='jijing-20260920', retrieved_date='2026-09-20', source=BASE, source_verification='Month and recollection provenance are site claims, not independently verified.', pages=records, assets=asset_records, errors=errors)
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
groups = [('listening','听力：题目、重录音频、原文及答案'),('reading','阅读：文章、题目及答案'),('writing','写作：Task 1 / Task 2题目与图表'),('recalls','口语及其他考后回忆')]
body = '<h1>2026年9月机经资料</h1><p>来源：Ieltsa。回忆重建，非官方试卷；部分阅读不足40题，不能都按完整模考计分。</p><p>离线浏览版：可听音、读题、展开答案；不自动保存或判分。项目中的练习入口另行保存作答。</p>'
for key, label in groups:
    body += '<h2>' + label + '</h2><ol>'
    for rec in records:
        if rec['kind'] == key:
            body += '<li><a href="' + rec['offline']['path'] + '">' + html.escape(rec['title']) + '</a></li>'
    body += '</ol>'
(OUT / 'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>9月机经离线目录</title><style>'+STYLE+'</style><main>'+body+'</main></html>', encoding='utf-8')
print(json.dumps({'pages':len(records),'assets':len(asset_records),'bytes':sum(r['bytes'] for r in asset_records),'errors':errors},ensure_ascii=False), flush=True)
