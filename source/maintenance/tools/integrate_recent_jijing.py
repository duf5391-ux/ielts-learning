"""Add this material batch to the current book without regenerating existing content."""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.codex-tools/jijing-libs'))
sys.path.insert(0, str(ROOT))
from bs4 import BeautifulSoup
from integrate_part_practice import Structure

BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN = BOOK / '开始学习.html'
BATCH = ROOT / 'content-pipeline/batches/jijing-20260920'
DOWNLOAD = ROOT / 'downloads/jijing-20260920'
APPROVED = BATCH / 'approved'
STAGE = BATCH / 'stage'
ASSETREL = '机经资料/jijing-20260920'
PROJECT = 'jijing-202609-v1'
MARKER = r'<!--JIJING-20260920:[^>]+-->.*?<!--/JIJING-20260920-->'
DATARE = r'(<script\b[^>]*id="learning-adjust-data"[^>]*>)(.*?)(</script>)'
e = lambda x: html.escape(str(x), quote=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
def mark(name, body):
    return '<!--JIJING-20260920:'+name+'-->'+body+'<!--/JIJING-20260920-->'

def write_archive_index(units, references):
    APPROVED.mkdir(parents=True,exist_ok=True)
    body='<h1>近期机经 · 已清洗内容</h1><p>来源网站标为2026年9月的回忆整理。具体考场未独立确认；以下内容按语言练习使用，保留原件并单独标明教学改编。</p>'
    for u in units:
        body+='<section><h2>'+e(u['title'])+'</h2><p>'+str(len(u['questions']))+'题 · 作答保存、参考答案与同材料答后精读。</p><a href="../../开始学习.html#'+u['id']+'">进入项目练习 →</a></section>'
    if references:
        body+='<section><h2>Task 2 写作题干参考</h2><p>'+str(len(references))+'道已去除导流、拆开整理的题干，无范文；可用于选题与审题。</p><a href="writing-task2.html">查看题干 →</a></section>'
    body+='<p>本页仅列本次通过内容核查并已接入的部分。</p>'
    css='body{font:17px/1.8 system-ui,sans-serif;background:#f6f5ee;color:#233d34;max-width:950px;margin:auto;padding:30px}h1,h2{line-height:1.4}a{color:#166651}section{background:white;border:1px solid #d8dfd2;border-radius:14px;padding:22px;margin:20px 0}'
    (APPROVED / 'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>近期机经已清洗内容</title><style>'+css+'</style>'+body+'</html>',encoding='utf-8')
    if references:
        body='<a href="index.html">← 本批已清洗内容</a><h1>Task 2 写作题干参考</h1><p>来源网站标为2026年9月回忆，具体考场未独立确认。这里只保留题干，不含范文和自动评分。</p>'
        for i,item in enumerate(references,1):
            body+='<section><h2>题目 '+str(i)+'</h2><p lang="en">'+e(item['prompt'])+'</p>'
            if item.get('originalPrompt'):
                body+='<p>本题已整理英文语法与搭配，保留原问题含义。</p>'
            body+='<a href="'+e(item['sourceUrl'])+'" target="_blank" rel="noopener">原始来源</a></section>'
        (APPROVED/'writing-task2.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task 2 写作题干参考</title><style>'+css+'</style>'+body+'</html>',encoding='utf-8')

def unit_html(u):
    uid=u['id']; fields=[uid+'-'+q['id'] for q in u['questions']]; gate=uid+'-check'
    text='<article class="jj-unit" id="'+uid+'" data-learning-unit="'+uid+'"><h2>'+e(u['title'])+'</h2>'
    text+='<p class="small">'+e(u['sourceNature'])+' · 预计'+str(u['minutes'])+'分钟（含答后精读）</p><div data-unit-progress="'+uid+'"></div>'
    text+='<p>'+e(u['instructions']).replace('\n','<br>')+'</p>'
    if u.get('audio'):
        text+='<audio controls preload="metadata" src="'+e(ASSETREL+'/'+u['audio'])+'"></audio>'
    text+='<div class="jj-context">'+''.join('<p>'+e(p)+'</p>' for p in u['contextParagraphs'])+'</div>'
    for i,q in enumerate(u['questions'],1):
        key=fields[i-1]
        text+='<div class="jj-question"><p><strong>'+str(i)+'.</strong> '+e(q['prompt'])+'</p>'
        if q.get('options'):
            text+='<p class="small">'+e(' / '.join(q['options']))+'</p>'
        text+='<label class="pp-answer"><span>第'+str(i)+'题作答</span><textarea rows="2" data-save="'+key+'"></textarea></label><button type="button" data-la-unknown="'+key+'">暂时不会</button></div>'
    text+='<details class="pp-key" id="'+gate+'" data-answer-gate="'+e(json.dumps(fields))+'"><summary>核对答案与答后精读</summary><div class="la-gate-content" hidden><h3>参考答案</h3><ol>'
    for a in u['answers']:
        text+='<li><strong>'+e(a['answer'])+'</strong><p>'+e(a['explanation'])+'</p></li>'
    text+='</ol>'+u['closeReadingHtml']
    if u.get('transcript'):
        text+='<details><summary>回读同段听力原文</summary><div class="jj-transcript">'+e(u['transcript']).replace('\n','<br>')+'</div></details>'
    text+='</div></details><p class="small">来源：<a target="_blank" rel="noopener" href="'+e(u['sourceUrl'])+'">Ieltsa 回忆整理</a> · <a target="_blank" rel="noopener" href="'+e(ASSETREL+'/index.html')+'">本批完整资料目录</a></p></article>'
    return text,dict(id=uid,mode='practice',skill=u['skill'],skillLabel={'listening':'听力','reading':'阅读'}[u['skill']],title=u['title'],topic='机经 · 2026年9月',type='回忆整理题组',description=str(len(fields))+'题；作答后核对，并回到同一材料精读。',steps=[dict(kind='answer',key=k) for k in fields]+[dict(kind='checked',key=gate)],part=u['part'],category='机经',progressLabel='作答与核对')

def build(page, units):
    base=re.sub(MARKER,'',page,flags=re.S)
    match=re.search(DATARE,base,re.S); assert match
    data=json.loads(match[2])
    data['units']=[u for u in data['units'] if not u['id'].startswith('pr-jijing-202609-')]
    data['projects']=[p for p in data['projects'] if p['id']!=PROJECT]
    additions=[]
    structure=Structure(base)
    for u in units:
        content,meta=unit_html(u)
        data['units'].append(meta)
        end=structure.sections['practice-'+u['skill']][1]
        additions.append((end,mark(u['skill'],content)))
    ids=[u['id'] for u in units]
    data['projects'].append(dict(id=PROJECT,title='近期机经 · 2026年9月',units=ids))
    # Locate the exact grid and source list start without reserializing the old page.
    def tag_start_offset(parent_id, class_name):
        parent=re.search(r'<section\b[^>]*\bid="'+parent_id+r'"[^>]*>',base)
        assert parent, parent_id
        tag=re.search(r'<div\b[^>]*class="[^"]*\b'+class_name+r'\b[^"]*"[^>]*>',base[parent.end():])
        assert tag, class_name
        return parent.end()+tag.end()
    card='<article class="la-card la-project" data-project="'+PROJECT+'"><p class="la-kicker">2026年9月 · 回忆整理</p><h3>近期机经 · 已清洗题组</h3><p>空乘岗位咨询与罐头食品简史：先完成题组，再核对答案、回到同一材料精读。另附9道Task 2题干参考。</p><div data-project-progress></div><ol>'+''.join('<li><a href="#'+u['id']+'">'+e(u['title'])+'</a></li>' for u in units)+'</ol><a href="'+ASSETREL+'/index.html" target="_blank" rel="noopener">查看本批已接入内容 →</a><p class="small">进度表示两组练习的作答与核对，不代表掌握度。</p></article>'
    additions.append((tag_start_offset('learning-projects','la-grid'),mark('project',card)))
    source='<a class="source-file" data-library-kind="机经资料" href="'+ASSETREL+'/index.html" target="_blank" rel="noopener"><span class="file-ext">机经</span><div><h3>近期机经 · 已清洗内容</h3><p>听力Part 1与独立阅读题组 · 含参考答案和材料精读</p></div></a>'
    additions.append((tag_start_offset('library','source-list'),mark('library',source)))
    css='.jj-unit{max-width:1000px;margin:24px auto;padding:20px;border:1px solid var(--line);border-radius:12px;background:#fff}.jj-unit audio{width:100%;margin:16px 0}.jj-context{padding:18px 22px;background:#f5f6ee;border-left:3px solid #9eaf9a;line-height:1.85}.jj-context p{margin:0 0 15px}.jj-question{margin:24px 0;padding-bottom:18px;border-bottom:1px solid var(--line)}.jj-unit .pp-key{margin:26px 0;padding:18px}.jj-transcript{font-size:15px;line-height:1.8}.jj-unit h3{margin-top:26px}.jj-unit textarea{width:100%;box-sizing:border-box}.jj-unit .la-gate-content[hidden]{display:none!important}@media(max-width:640px){.jj-unit{padding:14px}.jj-context{padding:14px}}'
    additions.append((base.index('</head>'),mark('css','<style>'+css+'</style>')))
    additions.append((match.start(2),None))
    result=base
    # Change only the data payload and this batch's owned inserts.
    edits=[(pos,pos,content) for pos,content in additions if content is not None]
    edits.append((match.start(2),match.end(2),json.dumps(data,ensure_ascii=False).replace('</',r'<\/')))
    for start,end,content in sorted(edits,reverse=True):
        result=result[:start]+content+result[end:]
    old=Structure(page); new=Structure(result)
    assert len(new.ids)==len(set(new.ids))
    assert len(new.fields)==len(set(new.fields))
    assert set(old.fields).issubset(new.fields)
    # Everything outside the single catalog payload and owned inserts is byte-identical.
    normalize=lambda s:re.sub(DATARE,lambda m:m[1]+'CATALOG'+m[3],re.sub(MARKER,'',s,flags=re.S),flags=re.S)
    assert normalize(result)==normalize(page)
    return result, dict(original_save_fields=len(old.fields),new_save_fields=len(new.fields)-len(old.fields),total_save_fields=len(new.fields),units=len(units),catalog_units=len(data['units']),preserved_outside_owned_blocks=True)

def asset_files():
    for path in APPROVED.rglob('*'):
        if not path.is_file(): continue
        rel=path.relative_to(APPROVED)
        yield path,Path(ASSETREL)/rel

def stage():
    units=[json.loads((BATCH/name).read_text(encoding='utf-8')) for name in ('listening-unit.json','reading-unit.json')]
    # A separate content decision must approve every unit before staging/publishing.
    decision=json.loads((BATCH/'content-review/release-decision.json').read_text(encoding='utf-8'))
    assert all(u['id'] in decision['approved_unit_ids'] for u in units)
    for u in units:
        assert decision['unit_sha256'][u['id']]==sha((BATCH/('listening-unit.json' if u['skill']=='listening' else 'reading-unit.json')).read_bytes())
    writing_file=BATCH/'content-review/writing-clean.json'
    assert sha(writing_file.read_bytes())==decision['writing_clean_sha256']
    references=[r for r in json.loads(writing_file.read_text(encoding='utf-8'))['items'] if r['id'] in decision['approved_reference_ids']]
    assert len(references)==len(decision['approved_reference_ids'])==9
    assert all(r['status']=='qualified_reference' for r in references)
    write_archive_index(units,references)
    for u in units:
        if u.get('audio'):
            dst=APPROVED/u['audio'];dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(DOWNLOAD/u['audio'],dst)
    page=MAIN.read_bytes(); decoded=page.decode('utf-8')
    candidate,check=build(decoded,units)
    assert build(candidate,units)[0]==candidate,'Not idempotent'
    STAGE.mkdir(parents=True,exist_ok=True)
    (STAGE/'baseline.html').write_bytes(page)
    (STAGE/'candidate.html').write_text(candidate,encoding='utf-8',newline='')
    assets=[]
    for source,rel in asset_files():
        target=STAGE/rel; target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            assert target.resolve().is_relative_to(STAGE.resolve())
            target.unlink()
        shutil.copy2(source,target)
        assert sha(source.read_bytes())==sha(target.read_bytes())
        assets.append(dict(source=str(source),path=rel.as_posix(),sha256=sha(target.read_bytes()),bytes=target.stat().st_size))
    manifest=dict(batch_id='jijing-20260920',project_id=PROJECT,status='staged',created_at=datetime.now().isoformat(),formal_path=str(MAIN),baseline_sha256=sha(page),candidate_sha256=sha(candidate.encode('utf-8')),checks=check,assets=assets,units=[u['id'] for u in units],content_decision_sha256=sha((BATCH/'content-review/release-decision.json').read_bytes()),source_kind='reviewed recall-derived exercises; not official examination material')
    (BATCH/'publication.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({**check,'stage':str(STAGE),'assets':len(assets),'candidate_sha256':manifest['candidate_sha256']},ensure_ascii=False))

def publish():
    record=json.loads((BATCH/'publication.json').read_text(encoding='utf-8'))
    report=json.loads((BATCH/'qa.json').read_text(encoding='utf-8-sig'))
    browser_report=json.loads((BATCH/'browser-qa.json').read_text(encoding='utf-8'))
    candidate=(STAGE/'candidate.html').read_bytes()
    assert report['passed']==report['total'] and report['sha256']==sha(candidate)
    assert browser_report['candidate_sha256']==sha(candidate)
    assert not browser_report['errors'] and browser_report['checks']
    assert all(check['status']=='pass' for check in browser_report['checks'])
    assert sha(candidate)==record['candidate_sha256']
    assert sha((BATCH/'content-review/release-decision.json').read_bytes())==record['content_decision_sha256']
    assert sha(MAIN.read_bytes())==record['baseline_sha256'],'Book changed after staging'
    backup=ROOT/'backups'/('jijing-20260920-'+datetime.now().strftime('%H%M%S'))
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copy2(MAIN,backup/'开始学习.html')
    new_assets=[]
    # Preflight all asset conflicts before writing anything.
    for item in record['assets']:
        dst=BOOK/item['path']
        if dst.exists(): assert sha(dst.read_bytes())==item['sha256'],'Asset conflict '+str(dst)
    for item in record['assets']:
        src=STAGE/item['path']; dst=BOOK/item['path']
        assert sha(src.read_bytes())==item['sha256']
        if not dst.exists():
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            new_assets.append(str(dst))
    record.update(backup=str(backup/'开始学习.html'),new_assets=new_assets,status='assets-copied')
    (BATCH/'publication.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp=MAIN.with_suffix('.jijing.tmp')
    tmp.write_bytes(candidate)
    assert sha(MAIN.read_bytes())==record['baseline_sha256'],'Book changed during publish'
    os.replace(tmp,MAIN)
    assert sha(MAIN.read_bytes())==record['candidate_sha256']
    record.update(status='published',published_at=datetime.now().isoformat())
    (BATCH/'publication.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    (backup/'恢复说明.md').write_text('本批只改变开始学习.html及新增机经资料/jijing-20260920目录。恢复前校验当前主册SHA为 '+record['candidate_sha256']+'；若不匹配应停止，避免覆盖后续修改。将本目录开始学习.html恢复至正式位置，新增资料可保留以免破坏外部引用。完整新资产清单见 '+str(BATCH/'publication.json')+'。此流程不是跨文件事务。',encoding='utf-8')
    print(json.dumps({'status':'published','main':str(MAIN),'backup':record['backup'],'sha256':record['candidate_sha256'],'assets':len(record['assets'])},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(); parser.add_argument('--publish',action='store_true'); args=parser.parse_args()
    publish() if args.publish else stage()
