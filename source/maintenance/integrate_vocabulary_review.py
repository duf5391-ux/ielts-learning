"""Pure incremental vocabulary upgrade; the caller owns backups and publishing."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'local-dictionary'


def replace_block(text, name, body, before):
    block = f'<!--VOCABULARY-REVIEW:{name}-->{body}<!--/VOCABULARY-REVIEW:{name}-->'
    pattern = rf'<!--VOCABULARY-REVIEW:{name}-->.*?<!--/VOCABULARY-REVIEW:{name}-->'
    if re.search(pattern, text, re.S):
        return re.sub(pattern, lambda _: block, text, count=1, flags=re.S)
    assert before in text, (name, before)
    return text.replace(before, block + before, 1)


def apply(text):
    lookup = (SOURCE / 'main-lookup.js').read_text(encoding='utf8')
    review = (SOURCE / 'vocabulary-review.js').read_text(encoding='utf8')
    assert '</script' not in lookup + review
    pattern = r'(<script\b[^>]*\bid="lookup-controller"[^>]*>).*?(</script>)'
    assert len(re.findall(pattern, text, re.S)) == 1, 'lookup controller not uniquely identified'
    text = re.sub(pattern, lambda m: m.group(1) + lookup + m.group(2), text, count=1, flags=re.S)
    text = replace_block(text, 'style', '<link rel="stylesheet" href="vocabulary-review.css">', '</head>')
    fragment = '<section aria-label="我的单词表与间隔复习" id="vocabulary-review"></section>'
    if '<!--VOCABULARY-REVIEW:entry-->' in text:
        text = replace_block(text, 'entry', fragment, '</body>')
    else:
        marker = '<section id="lookup-learning">'
        assert marker in text
        text = text.replace(marker, marker + '<!--VOCABULARY-REVIEW:entry-->' + fragment + '<!--/VOCABULARY-REVIEW:entry-->', 1)
    script = '<script id="vocabulary-review-controller">' + review + '</script>'
    text = replace_block(text, 'script', script, '<!--/LOCAL-DICTIONARY:lookup-->')
    text = text.replace('<h2>生词复习区</h2>', '<h2>查词历史</h2>')
    text = text.replace('查询过的词和原句自动留在这里。复习时先试着回忆意思，再检查能否用于新句子。', '每次查询都会留下词语和原句。点击收藏后进入上方单词表，再按间隔复习。')
    text = text.replace('“已复习”记录复习动作，不代表已掌握。记录同时包含在本页原有的学习备份中。', '旧版待复习／已复习标记继续保留。所有查询、收藏、拼写与复习记录包含在本页学习备份中。')
    text = text.replace('查询自动加入待复习。释义与原句保存在本地，查词无需联网。', '查询自动留在历史中；点击收藏可加入单词表。释义与原句保存在本地，查词无需联网。')
    return text, {'vocabularyReview': True, 'lookupControllerUpdated': True, 'savedField': 'lookup-history-v1', 'newSavedFields': 0, 'storageMigration': 'none; extend existing rows only on user action'}
