"""Probe the published IELTS entry and two audio URLs with Globalping.

Run after publication (this creates at most 42 public probe tests):
  python research/probe_github_publication.py --base-url https://duf5391-ux.github.io/ielts-learning/
Offline request preview (no network or output files):
  python research/probe_github_publication.py --dry-run

Only the Python standard library is required. Requests/results, summary.json,
and report.md are written to a new timestamped directory beside this script.
Exit 0: every returned node meets the stated response checks; 1: node issues;
2: API/client failure or incomplete measurement. None means nationwide access
or complete audio playback has been verified. Binary-prefix uncertainty and
unallocated probes remain explicit warnings even when the exit status is 0.

Contract: research/globalping-api-spec.yaml, MeasurementHttpOptions permits
request.headers (Host/User-Agent are reserved). FinishedHttpTestResult.rawBody
is a string/null containing only the first 10 kb, not a lossless byte field.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.globalping.io'
LOCATIONS = [
    {'country': 'CN', 'city': 'Beijing', 'asn': 9808, 'limit': 1},
    {'country': 'CN', 'city': 'Shanghai', 'asn': 9808, 'limit': 1},
    {'country': 'CN', 'city': 'Guangzhou', 'asn': 4134, 'limit': 1},
    {'country': 'CN', 'city': 'Tianjin', 'asn': 4837, 'limit': 1},
    {'country': 'CN', 'city': 'Shanghai', 'asn': 17621, 'limit': 1},
    {'country': 'CN', 'city': 'Wuhan', 'asn': 151185, 'limit': 1},
    {'country': 'CN', 'city': 'Guilin', 'asn': 4134, 'limit': 1},
    {'country': 'CN', 'city': 'Nanning', 'asn': 4837, 'limit': 1},
    {'country': 'CN', 'city': 'Beijing', 'asn': 45090, 'limit': 1},
    {'country': 'CN', 'city': 'Shenzhen', 'asn': 37963, 'limit': 1},
    {'country': 'US', 'limit': 2},
    {'country': 'SG', 'limit': 2},
]
RESOURCES = [
    ('homepage', '首页', '', False),
    ('official_audio', '完整听力音频', '原始参考/precise-official-listening-full.mp3', True),
    ('jijing_audio', '最新机经音频', '机经资料/jijing-20260920/ieltsa/assets/494b5ff8b614-2026-sep-hf-1.mp3', True),
]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def request_plan(base_url):
    base = urllib.parse.urlsplit(base_url)
    if (base.scheme != 'https' or not base.hostname or base.username or base.password
            or base.query or base.fragment or base.port not in (None, 443)):
        raise ValueError('base-url must be an HTTPS URL on port 443 without credentials, query, or fragment')
    prefix = urllib.parse.quote(urllib.parse.unquote(base.path).rstrip('/') + '/', safe='/')
    plan = []
    for key, label, relative, audio in RESOURCES:
        path = prefix + urllib.parse.quote(relative, safe='/')
        request = {'method': 'GET', 'path': path}
        if audio:
            request['headers'] = {'Range': 'bytes=0-1023'}
        plan.append({'key': key, 'label': label, 'audio': audio,
                     'url': f'https://{base.hostname}{path}',
                     'request': {'type': 'http', 'target': base.hostname,
                                 'locations': LOCATIONS, 'inProgressUpdates': True,
                                 'measurementOptions': {'protocol': 'HTTPS', 'port': 443,
                                                        'request': request}}})
    return plan


def api_json(url, payload=None, etag=None, timeout=30):
    headers = {'Accept': 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if etag:
        headers['If-None-Match'] = etag
    request = urllib.request.Request(url,
        data=json.dumps(payload).encode('utf-8') if payload is not None else None,
        headers=headers, method='POST' if payload is not None else 'GET')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response), dict(response.headers)
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return None, dict(error.headers)
        body = error.read(3000).decode('utf-8', errors='replace')
        retry = error.headers.get('Retry-After')
        raise RuntimeError(f'API HTTP {error.code}; Retry-After={retry}; {body}') from error


def measure(resource, output, poll_interval, max_wait):
    """No automatic POST retry; preserve IDs when a response/poll fails."""
    saved = {'resource': resource, 'creation': None, 'measurement': None, 'client_error': None}
    path = output / (resource['key'] + '.json')
    write_json(path, saved)
    try:
        created, headers = api_json(API + '/v1/measurements', resource['request'])
        saved['creation'] = created
        write_json(path, saved)
        location = headers.get('Location') or headers.get('location')
        if not location:
            location = API + '/v1/measurements/' + urllib.parse.quote(created['id'], safe='')
        parsed = urllib.parse.urlsplit(location)
        if parsed.scheme != 'https' or parsed.netloc != 'api.globalping.io' or not parsed.path.startswith('/v1/measurements/'):
            raise ValueError('Unexpected API measurement location')
        etag = None
        deadline = time.monotonic() + max_wait
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Client wait limit reached; saved measurement ID may be queried later')
            result, headers = api_json(location, etag=etag, timeout=min(30, remaining))
            etag = headers.get('ETag') or headers.get('Etag') or headers.get('etag') or etag
            if result is not None:
                saved['measurement'] = result
                write_json(path, saved)
                if result.get('status') != 'in-progress':
                    break
            # API maximum is two reads/second/measurement; sleep after each reply.
            time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))
    except Exception as error:
        saved['client_error'] = str(error)
    write_json(path, saved)
    return saved


def header_value(headers, name):
    value = next((v for k, v in headers.items() if k.lower() == name.lower()), None)
    return ', '.join(value) if isinstance(value, list) else value


def body_prefix(raw, audio):
    if not isinstance(raw, str) or not raw:
        return {'check': 'unavailable', 'note': 'API未返回正文，不能核验前缀'}
    sample = raw[:160]
    if re.match(r'\s*(?:<!doctype\s+html|<html\b)', sample, re.I):
        return {'check': 'html', 'text': sample, 'note': '正文是HTML页面'}
    if not audio:
        return {'check': 'text_sample', 'text': sample}
    if raw.startswith('ID3'):
        return {'check': 'id3_signature', 'text': 'ID3', 'note': '可见MP3常用ID3标签；未解码或完整播放'}
    return {'check': 'binary_unknown', 'text': sample,
            'note': 'API未定义无损二进制编码；不能从JSON字符串可靠重建MP3帧字节，未见ID3不等于音频损坏'}


def summarize(saved):
    resource = saved['resource']
    measurement = saved.get('measurement') or {}
    nodes = []
    for item in measurement.get('results', []):
        probe, result = item['probe'], item.get('result') or {}
        headers, tls = result.get('headers') or {}, result.get('tls') or {}
        content_type = header_value(headers, 'content-type')
        content_range = header_value(headers, 'content-range')
        status = result.get('statusCode')
        prefix = body_prefix(result.get('rawBody'), resource['audio'])
        title = re.search(r'<title[^>]*>(.*?)</title>', result.get('rawBody') or '', re.S | re.I)
        issues = []
        if result.get('status') != 'finished':
            issues.append('探针请求未完成')
        if tls.get('authorized') is not True:
            issues.append('TLS未证实可信')
        if status not in ((200, 206) if resource['audio'] else (200,)):
            issues.append('HTTP状态不符合预期')
        if resource['audio']:
            mime = (content_type or '').split(';')[0].strip().lower()
            if mime not in ('audio/mpeg', 'audio/mp3', 'audio/x-mpeg', 'audio/mpeg3'):
                issues.append('未返回明确MP3 Content-Type')
            if prefix['check'] == 'html':
                issues.append('音频地址返回HTML')
            if status == 206 and not re.fullmatch(r'bytes 0-1023/\d+', content_range or ''):
                issues.append('206的Content-Range未证实所请求的前1024字节')
        elif not title or not re.search(r'IELTS|雅思', html.unescape(title.group(1)), re.I):
            issues.append('返回正文未证实雅思首页标题')
        nodes.append({'country': probe.get('country'), 'city': probe.get('city'),
                      'asn': probe.get('asn'), 'network': probe.get('network'),
                      'network_tags': [x for x in probe.get('tags', []) if x.endswith('-network')],
                      'probe_status': result.get('status'), 'http_status': status,
                      'tls_authorized': tls.get('authorized'), 'tls_protocol': tls.get('protocol'),
                      'tls_error': tls.get('error'), 'resolved_address': result.get('resolvedAddress'),
                      'timings_ms': result.get('timings'), 'content_type': content_type,
                      'content_range': content_range, 'content_length': header_value(headers, 'content-length'),
                      'range_honored': status == 206 if resource['audio'] else None,
                      'api_body_truncated': result.get('truncated'), 'prefix': prefix,
                      'title': html.unescape(title.group(1)) if title else None,
                      'error': result.get('error') or (result.get('rawOutput') if result.get('status') == 'failed' else None),
                      'failure_source': result.get('failureSource'), 'response_checks_passed': not issues,
                      'issues': issues})
    requested = sum(x.get('limit', 1) for x in LOCATIONS)
    actual = measurement.get('probesCount', (saved.get('creation') or {}).get('probesCount', 0))
    return {'key': resource['key'], 'label': resource['label'], 'url': resource['url'],
            'measurement_id': measurement.get('id') or (saved.get('creation') or {}).get('id'),
            'measurement_status': measurement.get('status'), 'created_at': measurement.get('createdAt'),
            'requested_probes': requested, 'actual_probes': actual,
            'unallocated_probe_count': max(0, requested - actual),
            'returned_nodes': len(nodes), 'client_error': saved.get('client_error'), 'nodes': nodes}


def reader_report(summary):
    lines = ['# 雅思GitHub公网验收探测', '', f"目标：{summary['base_url']}",
             f"记录时间（UTC）：{summary['created_at']}", '',
             '首页为普通HTTPS GET；两条音频为GET加Range: bytes=0-1023。未更换UA、解析器或代理。',
             'Globalping仅返回最多前10 kb正文，二进制并非保证无损；ID3只核验可见前缀。',
             '200/206和可信TLS只证明该节点当时的响应；部分下载不代表完整播放。'
             '正文未知保留为未知，不据此保证音频正确。不同请求同城市/ASN不保证同一物理探针。', '']
    def cell(value):
        return str(value if value is not None else '未知').replace('|', '\\|').replace('\n', ' ')[:240]
    for resource in summary['resources']:
        nodes = resource['nodes']
        passed = sum(x['response_checks_passed'] for x in nodes)
        cn = [x for x in nodes if x['country'] == 'CN']
        lines += [f"## {resource['label']}", '', resource['url'], '',
                  f"返回节点{len(nodes)}，响应检查通过{passed}；大陆{len(cn)}个中通过{sum(x['response_checks_passed'] for x in cn)}。"
                  f"请求{resource['requested_probes']}个，分配{resource['actual_probes']}个；未分配不计作成功或失败。",
                  f"测量ID：{resource['measurement_id']}；状态：{resource['measurement_status']}。", '']
        if resource['client_error']:
            lines += ['API/客户端错误：' + resource['client_error'], '']
        lines += ['| 节点/网络 | TLS | HTTP | 总耗时ms | Content-Type | Content-Range | 前缀 | 问题 |',
                  '|---|---|---|---|---|---|---|---|']
        for n in nodes:
            values = [f"{n['country']}/{n['city']} AS{n['asn']} {n['network']}", n['tls_authorized'],
                      n['http_status'], (n['timings_ms'] or {}).get('total'), n['content_type'],
                      n['content_range'], n['prefix']['check'], '; '.join(n['issues']) or '响应检查通过']
            lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
            if n['error']:
                lines.append(f"\n该节点错误：{cell(n['error'])}\n")
        lines.append('')
    lines += ['## 结论边界', '', '本次未验证音频全程解码、跳转播放、词典、录音或学习记录。'
              '缺站404不能通过首页验收。即使全部节点通过，也不能承诺中国大陆或全球长期稳定。', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base-url', default='https://duf5391-ux.github.io/ielts-learning/')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--poll-interval', type=float, default=2.0)
    parser.add_argument('--max-wait', type=float, default=90.0, help='Per-measurement polling deadline in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Print exact requests without network or file writes')
    args = parser.parse_args()
    if args.poll_interval < 0.5 or args.max_wait < 40:
        parser.error('poll-interval must be >=0.5s and max-wait >=40s')
    plan = request_plan(args.base_url)
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output = args.output_dir or Path(__file__).resolve().parent / ('github-publication-probes-' + stamp)
    output.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=3) as pool:
        saved = list(pool.map(lambda resource: measure(resource, output, args.poll_interval, args.max_wait), plan))
    summary = {'base_url': args.base_url, 'created_at': datetime.now(timezone.utc).isoformat(),
               'scope': 'HTTPS response and optional visible prefix only; not complete playback or nationwide reliability',
               'resources': [summarize(x) for x in saved]}
    write_json(output / 'summary.json', summary)
    (output / 'report.md').write_text(reader_report(summary), encoding='utf-8')
    print(json.dumps({'summary': str((output / 'summary.json').resolve()),
                      'report': str((output / 'report.md').resolve()),
                      'measurements': [{'key': x['key'], 'id': x['measurement_id'],
                                        'actual_probes': x['actual_probes'], 'client_error': x['client_error']}
                                       for x in summary['resources']]}, ensure_ascii=False, indent=2))
    if any(x['client_error'] or x['measurement_status'] == 'in-progress' or not x['nodes'] for x in summary['resources']):
        return 2
    return int(any(not n['response_checks_passed'] for x in summary['resources'] for n in x['nodes']))


if __name__ == '__main__':
    sys.exit(main())
