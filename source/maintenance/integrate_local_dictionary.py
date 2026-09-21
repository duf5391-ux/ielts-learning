"""Install the local dictionary into the existing study book without rebuilding it.

First run local-dictionary/build_dictionary.py to build local-dictionary/dist.
This installer never reads or writes the user's browser storage.
"""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse, quote
from datetime import datetime
import hashlib
import json
import re
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'local-dictionary'
DIST = SOURCE / 'dist'
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')


class Inventory(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.fields, self.media = [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'data-save' in d:
            self.fields.append((tag, d['data-save']))
        if tag in ('img', 'audio', 'source', 'video'):
            self.media.append((tag, tuple(attrs)))


def marked(text, name, body, before):
    block = f'<!--LOCAL-DICTIONARY:{name}-->{body}<!--/LOCAL-DICTIONARY:{name}-->'
    pattern = rf'<!--LOCAL-DICTIONARY:{name}-->.*?<!--/LOCAL-DICTIONARY:{name}-->'
    if re.search(pattern, text, re.S):
        return re.sub(pattern, lambda _: block, text, count=1, flags=re.S)
    assert before in text, (name, before)
    return text.replace(before, block + before, 1)


def main_page(text):
    script = (SOURCE / 'main-lookup.js').read_text(encoding='utf8')
    assert '</script' not in script
    body = '<script src="local-dictionary/dictionary-engine.js"></script><script src="local-dictionary/dictionary-ui.js"></script><script id="lookup-controller">' + script + '</script>'
    pattern = r'<!--LOCAL-DICTIONARY:lookup-->.*?<!--/LOCAL-DICTIONARY:lookup-->'
    block = '<!--LOCAL-DICTIONARY:lookup-->' + body + '<!--/LOCAL-DICTIONARY:lookup-->'
    if re.search(pattern, text, re.S):
        text = re.sub(pattern, lambda _: block, text, count=1, flags=re.S)
    else:
        hits = [m for m in re.finditer(r'<script\b[^>]*>(.*?)</script>', text, re.S) if "const field = $('#lookup-history-store')" in m.group(1)]
        assert len(hits) == 1, 'Cannot identify the existing lookup controller'
        m = hits[0]
        text = text[:m.start()] + block + text[m.end():]
    text = marked(text, 'style', '<link rel="stylesheet" href="local-dictionary/dictionary.css">', '</head>')
    banner = '<section class="local-dictionary-entry"><p>本地英汉词典已就绪。点击正文英文词，或输入单词，断网也能查看释义、音标和词形。</p><button type="button" data-open-local-lookup>本地查词</button><a href="本地词典.html" target="_blank" rel="noopener">打开独立词典 →</a></section>'
    if '<!--LOCAL-DICTIONARY:entry-->' in text:
        text = marked(text, 'entry', banner, '</main>')
    else:
        text, n = re.subn(r'(<section\b[^>]*\bid="vocabulary"[^>]*>)', lambda m: m.group(1) + '<!--LOCAL-DICTIONARY:entry-->' + banner + '<!--/LOCAL-DICTIONARY:entry-->', text, count=1)
        assert n == 1
    text = text.replace('查询自动加入待复习。在线查询仅发送所查词语；原句保留在本地。', '查询自动加入待复习。释义与原句保存在本地，查词无需联网。')
    text = text.replace('收藏与熟悉度标记会自动保存；点击词典可查更多义项和发音。', '收藏与熟悉度标记会自动保存；点击本地词典可查更多义项、音标和词形。')
    def link(m):
        attrs, href, inner = m.group(1), unescape(m.group(2)), m.group(3)
        if not href.startswith('https://www.oxfordlearnersdictionaries.com/search/english/?q='):
            return m.group(0)
        term = parse_qs(urlparse(href).query).get('q', [''])[0]
        if not term:
            return m.group(0)
        return '<a' + attrs + 'href="本地词典.html?word=' + escape(quote(term), quote=True) + '" data-local-dictionary="' + escape(term, quote=True) + '"' + inner[:inner.index('>')+1] + '本地词典</a>'
    text = re.sub(r'<a([^>]*?)href="([^"]+)"([^>]*>.*?</a>)', link, text, flags=re.S)
    # Word lookup stays offline; the separate, user-triggered sentence translator may be online.
    assert 'api.mymemory.translated.net' not in script
    return text


def library_page(text):
    old = "https://dictionary.cambridge.org/dictionary/english/'+encodeURIComponent(r.text.trim().replace(/\\s+/g,'-'))+'\">查词典"
    new = "本地词典.html?word='+encodeURIComponent(r.text.trim())+'\">本地词典"
    if old in text:
        assert text.count(old) == 1
        text = text.replace(old, new)
    else:
        assert new in text, 'Cannot identify dictionary links in the vocabulary library'
    return text


def frequency_page(text):
    body = '''<script>(()=>{document.querySelector('#rows').addEventListener('click',e=>{const b=e.target.closest('[data-word]');if(!b)return;const a=document.createElement('a');a.textContent='查本地词典 →';a.href='本地词典.html?word='+encodeURIComponent(b.dataset.word);a.target='_blank';a.rel='noopener';const p=document.createElement('p');p.append(a);document.querySelector('#evidence').append(p);});})();</script>'''
    return marked(text, 'frequency', body, '</body>') if '</body>' in text else marked(text, 'frequency', body, '</html>')


def install():
    manifest = json.loads((DIST / 'dictionary-manifest.json').read_text(encoding='utf8'))
    count = manifest['entryCount']
    target = BOOK / 'local-dictionary'
    target.mkdir(exist_ok=True)
    shutil.copytree(DIST, target, dirs_exist_ok=True)
    for name in ['dictionary-ui.js', 'dictionary.css']:
        shutil.copy2(SOURCE / name, target / name)
    shutil.copy2(SOURCE / 'source' / 'LICENSE', target / 'LICENSE')
    shutil.copy2(SOURCE / 'source' / 'provenance.json', target / 'provenance.json')
    provenance = json.loads((SOURCE / 'source' / 'provenance.json').read_text(encoding='utf8'))
    source_note = '# 本地英汉词典\n\n数据：[ECDICT](https://github.com/skywind3000/ECDICT)，MIT 许可证，下载与构建于 2026-09-19。固定版本、原始文件地址与 SHA-256 见 [provenance.json](provenance.json)。\n\n保留通用英汉释义、已有英文释义、音标、词性与词形数据。浏览器按需读取本机分片，查词无需在线接口。未收录的词不会自动联网。音标字段并非每条都有；词库未包含统一的真人发音录音。原有课程搭配、例句与词典通用义项分别显示。\n\n' + f'已构建词条：{count:,}。词形对应依据词库 exchange 字段。\n\n' + '维护源位于工作区 local-dictionary；安装脚本为 integrate_local_dictionary.py。原始 CSV 保存在工作区 source 中，不需要放进浏览器存储。\n'
    (target / 'SOURCE.md').write_text(source_note, encoding='utf8')
    standalone = (SOURCE / 'dictionary-page.html').read_text(encoding='utf8').replace('__COUNT__', f'{count:,}')
    (BOOK / '本地词典.html').write_text(standalone, encoding='utf8')
    backup = ROOT / 'backups' / ('local-dictionary-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    report = {'files': [], 'backup': str(backup), 'entryCount': count, 'storage': 'No user browser storage accessed'}
    for name, transform in [('开始学习.html', main_page), ('完整词汇来源库.html', library_page), ('词频与原文证据.html', frequency_page)]:
        path = BOOK / name
        before = path.read_text(encoding='utf8')
        after = transform(before)
        assert transform(after) == after, name + ' is not idempotent'
        a, b = Inventory(before), Inventory(after)
        assert a.fields == b.fields, name + ': saved fields changed'
        assert a.media == b.media, name + ': media changed'
        if name == '开始学习.html':
            gloss = r'<script id="lookup-glossary" type="application/json">.*?</script>'
            assert re.search(gloss, before, re.S).group() == re.search(gloss, after, re.S).group()
        if before != after:
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / name)
            assert path.read_text(encoding='utf8') == before, 'Concurrent edit detected; run installer again'
            tmp = path.with_suffix('.local-dictionary.tmp')
            tmp.write_text(after, encoding='utf8')
            tmp.replace(path)
        report['files'].append({'name': name, 'changed': before != after, 'savedFieldsPreserved': len(a.fields), 'mediaPreserved': len(a.media), 'idempotent': True, 'sha256': hashlib.sha256(after.encode('utf8')).hexdigest()})
    (SOURCE / 'integration-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    install()
