"""Pure incremental transform + staged assets for the root task to integrate.

CLI only writes inside this directory; it does not publish or replace the book.
"""
import argparse, hashlib, html, json, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from integrate_part_practice import Structure
e=lambda s:html.escape(str(s),quote=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
MARKER=r'<!--JIJING-UPDATE-20260921:[^>]+-->.*?<!--/JIJING-UPDATE-20260921-->'
DATARE=r'(<script\b[^>]*id="learning-adjust-data"[^>]*>)(.*?)(</script>)'
PROJECT='jiufen-reviewed-20260921-v1'
ASSETREL='机经资料/jiufen-reviewed-20260921'
LEGACYREL='机经资料/jijing-20260920'
DATE='2026-09-21'
def read(name): return json.loads((HERE/name).read_text(encoding='utf-8'))
def marker(name,body): return '<!--JIJING-UPDATE-20260921:'+name+'-->'+body+'<!--/JIJING-UPDATE-20260921-->'
CSS='''.jj-update-badge{display:inline-block;padding:3px 10px;border:1px solid #c8d8c9;border-radius:999px;background:#edf4e9;color:#234d3b;font-size:14px;font-weight:650;margin:2px 6px 2px 0}.jj-update-meta{margin:12px 0;color:#415547}.jj-difficulty{margin:12px 0;padding:12px 16px;background:#f6f6ef;border-radius:10px}.jj-difficulty summary{cursor:pointer;color:#254d39;line-height:1.6}.jj-difficulty p{margin:8px 0}.jj-question-options{line-height:1.65;margin:10px 0;padding-left:24px}.jj-question-options li{padding:3px 0}.jj-unit .jj-update-essay{min-height:300px;width:100%;line-height:1.8}.jj-prompt{font-size:18px;line-height:1.8}.jj-new-project a{overflow-wrap:anywhere}.jj-update-actions{display:flex;flex-wrap:wrap;gap:10px}.jj-unit h3.jj-group-title{margin-top:32px;padding-top:16px;border-top:1px solid #d9e2d4}@media(max-width:640px){.jj-difficulty{padding:10px}.jj-prompt{font-size:17px}.jj-question-options{padding-left:20px}}'''

def level_text(d): return f"难度系数 {d['level']}/5 · {d['label']}"
def badge(d,new=False):
    return ('<span class="jj-update-badge">新内容 · '+DATE+'</span>' if new else '')+'<span class="jj-update-badge">'+e(level_text(d))+'</span>'
def difficulty_html(d,new=False):
    dims='；'.join(k+' '+str(v)+'/5' for k,v in d['dimensions'].items())
    return '<div class="jj-update-meta">'+badge(d,new)+'</div><details class="jj-difficulty"><summary>难度依据</summary><p>'+e(d['reason'])+'</p><p class="small">'+e(dims)+'</p><p class="small">1–5为同科材料的编辑评估，数值越大任务负荷越高；不是官方Band或你的掌握度。</p></details>'
def options(opts): return '<ol type="A" class="jj-question-options">'+''.join('<li>'+e(o['text'])+'</li>' for o in opts)+'</ol>'

def unit_html(u):
    uid=u['id']; gate=uid+'-check'
    body='<article class="jj-unit" id="'+uid+'" data-learning-unit="'+uid+'"><h2>'+e(u['title'])+'</h2>'+difficulty_html(u['difficulty'],True)
    body+='<p class="small">'+e(u['sourceNature'])+' · 预计'+str(u['minutes'])+'分钟（含核对与材料回读）</p><div data-unit-progress="'+uid+'"></div>'
    if u['skill']=='reading':
        fields=[uid+'-'+q['id'] for q in u['questions']]
        body+='<p>'+e(u['instructions'])+'</p><div class="jj-context"><p><em>'+e(u['contextIntroduction'])+'</em></p>'+''.join('<p>'+e(p)+'</p>' for p in u['contextParagraphs'])+'</div>'
        by_id={q['id']:q for q in u['questions']}
        for group in u['groups']:
            body+='<h3 class="jj-group-title">'+e(group['title'])+'</h3><p>'+e(group['instructions'])+'</p>'
            common=len(group['questionIds'])>1 and all(by_id[q]['options']==by_id[group['questionIds'][0]]['options'] for q in group['questionIds'])
            if common: body+=options(by_id[group['questionIds'][0]]['options'])
            for qid in group['questionIds']:
                q=by_id[qid];key=uid+'-'+qid
                body+='<div class="jj-question"><p><strong>'+e(q['originalNumber'])+'.</strong> '+e(q['prompt'])+'</p>'
                if not common:body+=options(q['options'])
                desc='填写三个不同字母，顺序不限' if q['responseType']=='three-letters' else '填写一个选项字母'
                body+='<label class="pp-answer"><span>第'+e(q['originalNumber'])+'题 · '+desc+'</span><textarea rows="2" data-save="'+key+'"></textarea></label><button type="button" data-la-unknown="'+key+'">暂时不会</button></div>'
        feedback='<h3>参考答案</h3><p class="small">以下答案由本项目依据文章整理，不是下载到的官方答案键。</p><ol start="27">'
        for a in u['answers']:
            feedback+='<li><strong>'+e(a['answer'])+'</strong><p>'+e(a['explanation'])+'</p></li>'
        feedback+='</ol>'+u['closeReadingHtml']
        desc='14题（12个作答框）；作答、核对、回到同篇材料精读。'
    else:
        fields=[uid+'-essay']
        body+='<p>'+e(u['instructions'])+'</p><div class="jj-context jj-prompt" lang="en">'+''.join('<p>'+e(p)+'</p>' for p in u['promptParagraphs'])+'<p>'+e(u['supplement'])+'</p></div>'
        body+='<p class="small">可以先完成一段再暂停，回来继续原稿。40分钟和至少250词是完整Task 2练习条件；只写提纲或短段时作为阶段练习记录。</p><label class="pp-answer"><span>你的作文</span><textarea class="jj-update-essay" rows="14" data-save="'+fields[0]+'" placeholder="在这里开始写作；原稿会随学习册保存。"></textarea></label><button type="button" data-la-unknown="'+fields[0]+'">暂时不会</button>'
        feedback='<h3>对照自己的作答</h3><p>这些要点用于核对题意与展开，不是唯一范文或自动评分。不同观点均可，只要论证成立。</p><ul>'+''.join('<li>'+e(r)+'</li>' for r in u['rubric'])+'</ul><p>再看语言：段落推进是否清楚，词语是否贴合表达对象，句子是否准确。可保留自己的观点并修改表达，不必套用固定结论。</p>'+u['closeReadingHtml']
        desc='新Task 2题目；写作保存、题意核对与题干词句回读。'
    body+='<details class="pp-key" id="'+gate+'" data-answer-gate="'+e(json.dumps(fields))+'"><summary>核对'+('答案与材料精读' if u['skill']=='reading' else '作答与题干词句')+'</summary><div class="la-gate-content" hidden>'+feedback+'</div></details><p class="small">来源：<a href="'+e(u['sourceUrl'])+'" target="_blank" rel="noopener">九分学长</a> · 资料ID '+e(u['sourceId'])+' · <a href="'+ASSETREL+'/index.html" target="_blank" rel="noopener">本次新内容目录</a></p></article>'
    meta={'id':uid,'mode':'practice','skill':u['skill'],'skillLabel':'阅读' if u['skill']=='reading' else '写作 · Task 2','title':u['title'],'topic':'机经 · 9月21日新增','type':'回忆整理题组' if u['skill']=='reading' else 'Task 2题目','description':'新内容 · '+DATE+' · '+level_text(u['difficulty'])+'。'+desc,'steps':[{'kind':'answer','key':f} for f in fields]+[{'kind':'checked','key':gate}],'part':u['part'],'category':'机经','progressLabel':'作答与核对','addedAt':DATE,'difficulty':u['difficulty']}
    return body,meta

def apply(page):
    """Returns (candidate_html, check_summary), preserving unrelated bytes."""
    base=re.sub(MARKER,'',page,flags=re.S)
    original=Structure(base)
    match=re.search(DATARE,base,re.S); assert match
    data=json.loads(match[2]); units=read('new-units.json')['units']; diff=read('difficulty.json')['items']
    new_ids={u['id'] for u in units}
    data['units']=[u for u in data['units'] if u['id'] not in new_ids]
    data['projects']=[p for p in data['projects'] if p['id']!=PROJECT]
    edits=[]
    # Legacy unit answers, original question meaning and existing save keys stay intact.
    for u in data['units']:
        if u['id'] in diff:
            u['difficulty']=diff[u['id']]
            u['description']=re.sub(r' · 难度系数 [1-5]/5 · [^。]+。?$','',u.get('description',''))
            u['description']=u['description'].rstrip('。')+' · '+level_text(diff[u['id']])+'。'
            pattern=r'(<article\b[^>]*id="'+re.escape(u['id'])+r'"[^>]*>\s*<h2>.*?</h2>)'
            found=re.search(pattern,base,re.S); assert found,u['id']
            edits.append((found.end(),found.end(),marker('legacy-'+u['id'],difficulty_html(diff[u['id']]))))
    grouped={}
    for u in units:
        body,meta=unit_html(u); data['units'].append(meta)
        grouped.setdefault(u['skill'],[]).append(body)
    for skill,bodies in grouped.items():
        end=original.sections['practice-'+skill][1]
        edits.append((end,end,marker('new-'+skill,''.join(bodies))))
    data['projects'].insert(0,{'id':PROJECT,'title':'新内容 · 九分机经 · 9月21日','units':[u['id'] for u in units]})
    def inner_start(section,class_name):
        sec=re.search(r'<section\b[^>]*id="'+re.escape(section)+r'"[^>]*>',base);assert sec
        div=re.search(r'<div\b[^>]*class="[^"]*\b'+re.escape(class_name)+r'\b[^"]*"[^>]*>',base[sec.end():]);assert div
        return sec.end()+div.end()
    card='<article class="la-card la-project jj-new-project" data-project="'+PROJECT+'"><p class="la-kicker">新内容 · '+DATE+'</p><h3>九分机经 · 本次新增</h3><p>1组阅读14题、3道Task 2：可作答、保存、核对，并回到对应材料与词句。</p><div data-project-progress></div><ol>'+''.join('<li><a href="#'+u['id']+'">'+e(u['title'])+'</a> · '+str(u['difficulty']['level'])+'/5</li>' for u in units)+'</ol><p class="small">难度为1–5编辑评估。进度只表示本批作答与核对。</p><a href="'+ASSETREL+'/index.html" target="_blank" rel="noopener">查看本次新内容 →</a></article>'
    pos=inner_start('learning-projects','la-grid');edits.append((pos,pos,marker('project',card)))
    source='<a class="source-file" data-library-kind="机经资料" href="'+ASSETREL+'/index.html" target="_blank" rel="noopener"><span class="file-ext">新增</span><div><h3>9月21日新内容 · 九分机经</h3><p>语言起源阅读14题＋3道Task 2 · 每项标注难度</p></div></a>'
    pos=inner_start('library','source-list');edits.append((pos,pos,marker('library',source)))
    pos=base.index('</head>');edits.append((pos,pos,marker('css','<style id="jijing-update-style">'+CSS+'</style>')))
    edits.append((match.start(2),match.end(2),json.dumps(data,ensure_ascii=False).replace('</',r'<\/')))
    result=base
    for start,end,content in sorted(edits,reverse=True):result=result[:start]+content+result[end:]
    updated=Structure(result)
    assert len(updated.ids)==len(set(updated.ids)),'Duplicate HTML IDs'
    assert len(updated.fields)==len(set(updated.fields)),'Duplicate save keys'
    assert set(Structure(page).fields).issubset(set(updated.fields)),'Lost save fields'
    normalize=lambda s:re.sub(DATARE,lambda m:m[1]+'CATALOG'+m[3],re.sub(MARKER,'',s,flags=re.S),flags=re.S)
    assert normalize(result)==normalize(page),'Changed unrelated bytes'
    return result,{'originalSaveFields':len(Structure(page).fields),'saveFields':len(updated.fields),'newSaveFields':len(updated.fields)-len(Structure(page).fields),'newUnits':len(units),'newReadingQuestions':14,'newWritingTasks':3,'difficultyItems':len(diff),'catalogUnits':len(data['units']),'preservedOutsideOwnedBlocks':True}

def doc(title,body):
    css='body{font:17px/1.8 system-ui,sans-serif;background:#f6f5ee;color:#233d34;max-width:950px;margin:auto;padding:24px;overflow-wrap:anywhere}h1,h2{line-height:1.4}a{color:#166651}section{background:white;border:1px solid #d8dfd2;border-radius:14px;padding:22px;margin:20px 0}a:focus-visible,summary:focus-visible{outline:3px solid #246952;outline-offset:3px}@media(max-width:640px){body{padding:14px}section{padding:16px}}'
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title><style>'+css+CSS+'</style></head><body>'+body+'</body></html>'

def assets():
    out=HERE/'assets'; units=read('new-units.json')['units']; diffs=read('difficulty.json')['items'];files={}
    body='<a href="../../开始学习.html#learning-projects">← 学习项目</a><h1>新内容 · 九分机经</h1><p>2026年9月21日新增：1组阅读14题、3道Task 2写作题目。均可从学习册作答与保存。</p>'
    for u in units:
        body+='<section><h2>'+e(u['title'])+'</h2>'+difficulty_html(u['difficulty'],True)+'<p>'+('14题 · 预计30分钟，含核对和同篇精读。' if u['skill']=='reading' else '完整Task 2练习约40分钟，另留8分钟核对与题干回读。')+'</p><a href="../../开始学习.html#'+u['id']+'">进入练习 →</a></section>'
    body+='<p>资料来自九分学长下载批次，具体考场与日期未核实。阅读答案由本项目依据文章整理；写作提供针对题意的核对要点，允许不同成立观点。</p><p><a href="../jijing-20260920/index.html">之前已接入的听读题组与9道写作参考题干 →</a></p><details><summary>难度系数怎样理解</summary><p>'+e(read('difficulty.json')['scale'])+'</p><p>'+e(read('difficulty.json')['method'])+'</p><p>'+e(read('difficulty.json')['limits'])+'</p></details>'
    files[ASSETREL+'/index.html']=doc('9月21日新内容 · 九分机经',body)
    refs=read('legacy-reference-display.json')['items']
    body='<a href="index.html">← 本批已清洗内容</a><h1>Task 2 写作题干参考</h1><p>来源网站标为2026年9月回忆，具体考场未独立确认。这里只保留题干，不含范文和自动评分。难度已于2026年9月21日补充。</p>'
    for i,r in enumerate(refs,1):
        body+='<section id="'+e(r['id'])+'"><h2>题目 '+str(i)+' · '+e(r['displayTitle'])+'</h2>'+difficulty_html(r['difficulty'])+'<p lang="en">'+e(r['prompt'])+'</p>'
        if r.get('originalPrompt'):body+='<p>本题已整理英文语法与搭配，保留原问题含义。</p>'
        body+='<a href="'+e(r['sourceUrl'])+'" target="_blank" rel="noopener">原始来源</a></section>'
    files[LEGACYREL+'/writing-task2.html']=doc('Task 2 写作题干参考',body)
    old_root=ROOT/'content-pipeline/batches/jijing-20260920'
    old_units=[json.loads((old_root/name).read_text(encoding='utf-8')) for name in ['listening-unit.json','reading-unit.json']]
    body='<a href="../jiufen-reviewed-20260921/index.html">查看9月21日新增内容 →</a><h1>近期机经 · 已清洗内容</h1><p>以下是此前已接入的2026年9月回忆整理；难度信息已于9月21日补充，题目和旧记录继续保留。</p>'
    for u in old_units:
        body+='<section><h2>'+e(u['title'])+'</h2>'+difficulty_html(diffs[u['id']])+'<p>'+str(len(u['questions']))+'题 · 作答保存、参考答案与同材料答后精读。</p><a href="../../开始学习.html#'+u['id']+'">进入项目练习 →</a></section>'
    body+='<section><h2>Task 2 写作题干参考</h2><p>9道参考题干，已逐题标注难度与依据；没有新增作答或范文。</p><a href="writing-task2.html">查看题干 →</a></section><p>具体考场未独立确认；按语言练习使用，不作为已核验同场套卷。</p>'
    files[LEGACYREL+'/index.html']=doc('近期机经已清洗内容',body)
    manifest=[]
    for rel,contents in files.items():
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(contents,encoding='utf-8',newline='')
        manifest.append({'source':str(path),'path':rel,'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size})
    (HERE/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--output',type=Path,default=HERE/'candidate.html');a=p.parse_args()
    if a.source is None:a.source=Path(json.loads((ROOT/'content-pipeline/batches/jijing-20260920/publication.json').read_text(encoding='utf-8'))['formal_path'])
    assert a.output.resolve().is_relative_to(HERE.resolve()),'CLI only writes staging output inside its own directory'
    source=a.source.read_bytes();candidate,checks=apply(source.decode('utf-8'))
    assert apply(candidate)[0]==candidate,'Not idempotent'
    a.output.write_text(candidate,encoding='utf-8',newline='')
    manifest=assets()
    result={'source':str(a.source),'sourceSha256':sha(source),'candidate':str(a.output),'candidateSha256':sha(candidate.encode('utf-8')),'checks':checks,'assets':manifest,'idempotent':True,'formalWritten':False}
    (HERE/'stage-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
