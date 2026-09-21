from pathlib import Path
from html import escape as E
from collections import Counter
from urllib.parse import quote
import json,re,shutil,hashlib
from markdown import markdown

HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN=BOOK/'开始学习.html'
BACKUP=HERE/'backups'/'开始学习-before-resources-20260916.html'
NAMES={'background':'话题背景','reading':'阅读','listening':'听力','writing1':'写作 Task 1','writing2':'写作 Task 2','speaking':'口语'}
for name in ['current-speaking.json','skills-resources.json','background-additions.json']:
    assert (HERE/name).exists(),f'Waiting for {name}'
speaking=json.loads((HERE/'current-speaking.json').read_text(encoding='utf8'))
skills=json.loads((HERE/'skills-resources.json').read_text(encoding='utf8'))
background=json.loads((HERE/'background-additions.json').read_text(encoding='utf8'))
BACKUP.parent.mkdir(exist_ok=True)
if not BACKUP.exists():shutil.copy2(MAIN,BACKUP)
page=MAIN.read_text(encoding='utf8')
# Re-running replaces only marked additions; the original lookup, notes and answers remain intact.
page=re.sub(r'<!--RESOURCE-20260916:[^>]+-->.*?<!--/RESOURCE-20260916-->', '',page,flags=re.S)
def mark(key,body):return f'<!--RESOURCE-20260916:{key}-->'+body+'<!--/RESOURCE-20260916-->'
def at_section(sid,body):
    global page
    pattern=r'(<section\b[^>]*\bid="'+sid+r'"[^>]*>)'
    assert re.search(pattern,page),sid
    page=re.sub(pattern,lambda m:m[1]+mark(sid,body),page,count=1)
def p(s,cls=''):return '<p'+(' class="'+cls+'"' if cls else '')+'>'+E(str(s))+'</p>'
def ul(items):return '<ul>'+''.join('<li>'+E(str(x))+'</li>' for x in items)+'</ul>'
def link(url,title):return '<a href="'+E(str(url),quote=True)+'">'+E(str(title))+'</a>'
def md(s):return markdown(s,extensions=['tables','fenced_code','nl2br'])
def safe_media_path(source):
    f=Path(source)
    assert f.is_file(),f
    if f.is_relative_to(BOOK):return quote(f.relative_to(BOOK).as_posix(),safe='/')
    target=BOOK/'扩展资料'/'2026-09-16-resource-audio'
    target.mkdir(exist_ok=True)
    dest=target/(hashlib.sha256(str(f).encode()).hexdigest()[:8]+'-'+f.name)
    if not dest.exists():shutil.copy2(f,dest)
    return quote(dest.relative_to(BOOK).as_posix(),safe='/')

catalog=[];unit_html={};vocab=[]
source_map={x['id']:x for x in speaking['sources']}
def sources_for(t):
    out=''
    for sid in t.get('sourceIds',[]):
        s=source_map[sid]
        out+=p(s.get('note',''))+link(s['url'],s['title'])
    return '<details><summary>话题来源与核验说明</summary>'+out+'</details>' if out else p('语境、示范与练习均为工作区原创；基础话题补齐，未标为当季题目。','res-meta')

def controls(uid):
    return f'''<div class="res-track"><label><input type="checkbox" data-save="resource-learned-{uid}"> 我已学习本单元</label><label><input type="checkbox" data-save="resource-review-{uid}"> 加入我的复习</label><p class="res-meta">学习记录与复习记录分开保留；勾选不代表已掌握，不影响继续学新内容。</p></div><label class="field"><span>我的新表达／本次复习记录（可留空）</span><textarea rows="3" data-save="resource-note-{uid}"></textarea></label>'''

def render_topic(t,section):
    uid=t['id'];anchor=('topic-'+uid if section=='background' else 'speaking-new-'+uid)
    catalog.append({'id':uid,'anchor':anchor,'section':section,'title':t['title'],'status':t['status'],'current':section=='speaking','uses':len(t['language'])})
    body=p('2026-09-16 新增 · '+t['status'],'res-badge')+p(t['intro_zh'])
    if t.get('coverage'):body+=p('可覆盖的练习方向：'+'；'.join(t['coverage']))
    if t.get('concepts'):body+='<h3>先分清概念</h3>'+ul([x['term']+'：'+x['meaning_zh'] for x in t['concepts']])
    body+='<h3>语境阅读</h3>'+p(t['context_en'],'english')+'<details><summary>中文理解</summary>'+p(t['context_zh'])+'</details>'
    body+='<h3>把表达学完整</h3><div class="res-usage-grid">'
    for i,w in enumerate(t['language']):
        vid=f'{uid}-{i}'
        vocab.append({**w,'id':vid,'anchor':anchor,'topic':t['title']})
        body+='<article class="res-usage"><h4>'+E(w['chunk'])+'</h4>'+p(w['meaning_zh'])+p(w['structure'],'res-structure')+p(w['example_en'],'english')+p('易错：'+w['error_zh'])+'</article>'
    body+='</div><h3>示范与拆解</h3>'+p(t['model']['prompt_en'],'english')+p(t['model']['answer_en'],'english')+p(t['model']['explanation_zh'])
    body+='<details><summary>小练习与解析（可随时打开）</summary>'
    for q in t['practice']:
        body+=p(q['prompt'])+'<details><summary>参考答案与原因</summary>'+p(q['answer'])+p(q['explanation_zh'])+'</details>'
    body+='</details>'
    if section=='speaking':
        s=t['speaking'];body+='<details><summary>继续说：Part 1 / Part 2 / Part 3</summary>'
        for key,label in [('part1_en','Part 1 · 简短回答'),('part2_en','Part 2 · 独立长回答'),('part3_en','Part 3 · 展开讨论')]:
            val=s[key];body+='<h3>'+label+'</h3>'+(ul(val) if isinstance(val,list) else p(val,'english'))
        val=s['part3_support_zh'];body+=(ul(val) if isinstance(val,list) else p(val))+p(s['part3_model_en'],'english')+'</details>'
    r=t['optional_review'];body+='<details><summary>复习选项：换个情境再用</summary>'+p(r['prompt_en'],'english')+ul(r['checkpoints_zh'])+'</details>'
    body+=controls(uid)+sources_for(t)
    if section=='background':
        result=f'<article id="{anchor}" class="topic-reader resource-added"><h2>{E(t["title"])}</h2>'+body+f'<label><input type="checkbox" data-save="topic-read-{uid}"> 已读过这篇背景</label><p>{link("#background","返回全部话题")}</p></article>'
    else:result=f'<details id="{anchor}" class="res-unit resource-added"><summary><span class="res-badge">新增</span> {E(t["title"])}</summary><div class="res-body">'+body+'</div></details>'
    unit_html[uid]=result
    return result

bg_html=''.join(render_topic(t,'background') for t in background['topics'])
sp_html=''.join(render_topic(t,'speaking') for t in speaking['topics'])
at_section('speaking','<section class="res-section"><h2 class="resource-added">本季优先话题 · 16 组教学资源</h2>'+p('依据截至 2026-09-16 可核查的公开汇编选题；两份汇编部分相互引用，交叉出现不等于独立考场确认。示范与练习为原创，不是官方题目或背诵答案。','resource-added')+sp_html+'</section>')
at_section('background',bg_html)
new_tiles=''.join(f'<a class="topic-tile resource-added" href="#topic-{t["id"]}"><span class="res-badge">新增背景</span><h3>{E(t["title"].split("：")[0])}</h3><p>{E(t["title"].split("：")[-1])}</p></a>' for t in background['topics'])
page=page.replace('<div class="topic-grid">','<div class="topic-grid">'+mark('topic-tiles',new_tiles),1)
page=page.replace('<div class="catalog-intro">',mark('current-topics', '<div class="res-callout resource-added"><strong>优先学本季话题</strong>'+p('先从 2026 年 9—12 月公开回忆主题进入语境与表达，再按缺口补基础背景。')+link('#resource-update','打开本季题目与新增资源 →')+'</div>')+'<div class="catalog-intro">',1)

for u in skills['units']:
    uid=u['id'];section=u['section'];assert section in NAMES
    if uid=='new-writing1-transport-trends':u['title']='趋势图：增长幅度、主次关系与百分点'
    anchor=section+'-new-'+uid
    catalog.append({'id':uid,'anchor':anchor,'section':section,'title':u['title'],'status':u['source_note'],'current':False,'uses':len(u['vocabulary'])})
    body=p('2026-09-16 新增 · '+u['intro'],'res-badge')+p(u['source_note'],'res-meta')+md(u['lesson_md'])
    figures={'new-writing1-library-map':('library-maps.svg','2010与2025图书馆布局对比；原创教学地图'),'new-writing1-transport-trends':('commuting-trends.svg','2010至2025主要通勤方式占比；原创虚构数据')}
    if uid in figures:
        file,label=figures[uid];url=safe_media_path(HERE/'resource-figures'/file)
        body='<figure><img class="res-figure" src="'+E(url,quote=True)+'" alt="'+E(label)+'"><figcaption>'+E(label)+'</figcaption></figure>'+body
    for media in u.get('media',[]):
        if media['type']=='audio':
            src=media.get('path') or media.get('url');url=safe_media_path(src) if not src.startswith('http') else src
            body+='<div class="audio-box">'+p(media.get('label','配套原音'))+f'<audio controls preload="none" src="{E(url,quote=True)}"></audio></div>'
        elif media['type']=='image':
            url=safe_media_path(media['path']);body+='<img class="res-figure" src="'+E(url,quote=True)+'" alt="'+E(media.get('label','教学题面'))+'">'
    body+='<h3>用法与易错</h3><div class="res-usage-grid">'
    for i,w in enumerate(u['vocabulary']):
        word={'id':f'{uid}-{i}','chunk':w['phrase'],'meaning_zh':w['meaning'],'structure':w.get('structure',w['phrase']),'example_en':w['example'],'error_zh':w['pitfall'],'anchor':anchor,'topic':u['title']}
        vocab.append(word)
        body+='<article class="res-usage"><h4>'+E(w['phrase'])+'</h4>'+p(w['meaning'])+p(w['example'],'english')+p('易错：'+w['pitfall'])+'</article>'
    body+='</div><h3>应用一下（可选）</h3>'+md(u['task_prompt'])+'<details><summary>查看参考与解释</summary>'+md(u['feedback_md'])+'</details><details><summary>复习选项：简短再用</summary>'+md(u['transfer_prompt'])+'</details>'+controls(uid)
    body+='<details><summary>资源出处与原件</summary>'
    for s in u['sources']:
        if s.get('url'):body+=link(s['url'],s['title'])+p(s.get('note',''))
        if s.get('local_path'):
            src=s['local_path'];url=safe_media_path(src) if Path(src).is_absolute() else src
            body+=link(url,s['title']+' · 本地文件')
    body+='</details>'
    unit_html[uid]=f'<details id="{anchor}" class="res-unit resource-added"><summary><span class="res-badge">新增</span> {E(u["title"])}</summary><div class="res-body">'+body+'</div></details>'
for section in ['reading','listening','writing1','writing2']:
    arr=[u for u in skills['units'] if u['section']==section]
    if arr:at_section(section,'<section class="res-section"><h2 class="resource-added">新增可学资源 · '+str(len(arr))+' 单元</h2>'+p('语境、教学和参考均可直接打开。听力使用配套原音；自编题与官方材料分别注明。','resource-added')+''.join(unit_html[u['id']] for u in arr)+'</section>')

# A searchable resource catalogue keeps current speaking first without relabelling foundation material.
cards=''
for c in sorted(catalog,key=lambda item:not item['current']):
    cards+=f'<a class="res-card resource-added" href="#{c["anchor"]}" data-res-section="{c["section"]}" data-res-current="{str(c["current"]).lower()}"><span class="res-badge">'+('本季口语 · 回忆选题' if c['current'] else '新增 · '+NAMES[c['section']])+'</span><h3>'+E(c['title'])+'</h3>'+p(str(c['uses'])+' 组表达 · 语境 / 示范 / 解析')+'</a>'
count=len(catalog);uses=len(vocab)
catalog_intro=f'''<header class="chapter-head resource-added"><p class="res-badge">新增资源 · 2026-09-16</p><h1>本季话题与教学资源</h1><p>{count} 个教学单元 · {uses} 组用法。红色为本轮新增或补齐；可以先读教学，练习和复习均不设解锁关卡。</p></header>'''
catalog_intro+='<div class="res-dual resource-added"><a href="#resource-update" data-res-scroll-new><strong>学习新内容</strong><p>按本季话题和实际缺口选择；先看语境与示范。</p></a><a href="#records"><strong>复习旧内容</strong><p>从自己加入复习的用法开始，简短回忆后核对。随时回到新内容。</p></a></div>'
catalog_intro+='<p class="res-meta resource-added">参考'+link('https://apps.apple.com/cn/app/id698570469','“不背单词”的语境与搭配学习思路')+'：新学与复习并行，可把需要巩固的单元加入复习。</p>'
catalog_intro+='<details class="resource-added"><summary>来源说明：本季口语回忆＋官方资源＋原创教学</summary>'+p(speaking.get('note','口语采用本季公开回忆汇编，非官方完整题库。'))+p(skills['scope_note'])+'</details>'
filters='<label class="field"><span>查话题或技能</span><input id="res-search" type="search" placeholder="例如：回收、地图、信息匹配"></label><div class="res-filters">'+''.join(f'<button type="button" data-res-filter="{k}" aria-pressed="{str(k=="all").lower()}">{v}</button>' for k,v in [('all','全部'),('current','本季口语'),('background','补齐背景'),('reading','阅读'),('listening','听力'),('writing1','Task 1'),('writing2','Task 2')])+'</div><p id="res-count" role="status"></p>'
audit='<details class="resource-added"><summary>本轮逐板块检查与修复结果</summary><table><thead><tr><th>板块</th><th>核查与处理</th></tr></thead><tbody>'
for a,b in [
('话题背景','已有14篇基础语境及4个补充单元；本轮补齐犯罪、政府、社会、太空4篇读本。原基础分类不冒充当季题库。'),
('口语','补16组本季回忆主题的完整教学；每组含语境、4条表达、示范、Part 1/2/3练习与可选复习。'),
('阅读','补4种题型的材料和证据解析；修正已见原文仍列作未见基线的说明。'),
('听力','将4份已有原音储备转成可学单元，带原音、教学、练习与解析。'),
('写作 Task 1 / Task 2','补4单元，题面、思路、示范、语言与错误解释均齐；近期回忆仅用作选题参考。'),
('词汇与表达','原30话题1000词条属于词库；本轮新增用法可从例句返回完整语境，无需逐词闯关。'),
('学习首页 / 安排 / 记录','增加新学与复习并列入口，记录已学和待复习；更新数量。复习不阻挡新内容。'),
('材料与规则 / 新增资料','保留现有导入及原件入口；新增来源登记与本地音频。本轮以网页为准，旧PDF未同步扩写。')]:audit+='<tr><td>'+E(a)+'</td><td>'+E(b)+'</td></tr>'
audit+='</tbody></table><p>原有五章与26个补充单元已有教学与固定反馈，不能算空白。个性化作文／录音批改和自动排课仍未实现；本轮资源扩展不将其计作已完成。</p></details>'
cat='<section class="panel" id="resource-update" hidden>'+catalog_intro+audit+'<section id="resource-new-list">'+filters+'<div class="res-grid">'+cards+'</div><p id="res-empty" hidden>没有匹配项，试试其他关键词或分类。</p></section><details class="resource-added"><summary>核查来源登记</summary>'
for s in speaking['sources']:cat+=p(s['title'])+link(s['url'],'打开来源')+p(s.get('note',''))
for s in skills.get('resource_catalog',[]):cat+=p(s['title'])+link(s['url'],'打开来源')+p(s.get('note',''))
cat+='</details></section>'
page=page.replace('</main>',mark('catalog',cat)+'</main>',1)
page=re.sub(r'(<nav\b[^>]*aria-label="主导航"[^>]*>)',lambda m:m[1]+mark('nav','<button data-go="resource-update" class="resource-added"><span>本季题目与新增资源</span></button>'),page,count=1)
notice=f'<div class="res-callout resource-added"><strong>本轮新增 {count} 个教学单元 · {uses} 组用法</strong>'+p('本季口语优先，四科资源扩充；新学和复习并行，红色部分可直接开始。')+link('#resource-update','查看全部新增与补齐内容 →')+'</div>'
at_section('guide',notice)
at_section('plan','<div class="res-callout resource-added"><h2>新学与复习一起安排</h2>'+p('每天从一组新语境开始，也给已学表达留一次短回忆。示例：15分钟新内容＋5分钟复习；有余力再做专项练习。比例按实际负担调整，不必先清空复习才能学新内容。')+link('#resource-update','选新内容')+' · '+link('#records','回看待复习内容')+'</div>')
at_section('records','<section class="res-callout resource-added"><h2>新增资源：我的学习与复习</h2><p id="res-progress"></p><div class="res-dual"><div><h3>已学过</h3><ul id="res-learned-list"></ul></div><div><h3>我加入的复习</h3><ul id="res-review-list"></ul></div></div><p>勾选和笔记随原“学习记录 JSON”一并导出。复习完成后可取消加入；这不代表已掌握。查词记录仍在下方生词复习区。</p></section>')
at_section('library',notice+p('本轮新增资源与旧版PDF分开标明；本季题目、原创教学和官方原件各有出处。','resource-added'))
at_section('materials','<div class="res-callout resource-added">'+p('已核查的本轮扩展资源已接入各科，无需再次导入。此页继续用于你自行补充的资料。')+link('#resource-update','打开新增资源目录')+'</div>')
vbody='<details class="resource-added"><summary>本轮新增 '+str(uses)+' 组语境用法（点击返回完整教学）</summary><p>这些是按语境选取的用法单位，可能含跨主题复现，不等同新增了同等数量的不同单词。</p><div class="res-usage-grid">'
for w in vocab:vbody+='<article class="res-usage"><h4>'+E(w['chunk'])+'</h4>'+p(w['meaning_zh'])+p(w['example_en'],'english')+p('结构：'+w['structure'])+p('易错：'+w['error_zh'])+link('#'+w['anchor'],w['topic']+' →')+'</article>'
vbody+='</div></details>'
at_section('vocabulary',vbody)

# Extend the existing local phrase lookup without replacing prior meanings or history.
gmatch=re.search(r'(<script\b[^>]*\bid="lookup-glossary"[^>]*>)(.*?)(</script>)',page,re.S)
if gmatch:
    glossary=json.loads(gmatch[2])
    for w in vocab:
        term=' '.join(w['chunk'].lower().replace('’',"'").split())
        entry={'meaning':w['meaning_zh'],'pos':'用法','chunk':w['structure'],'example':w['example_en'],'source':'工作区新增教学 · '+w['topic']}
        entries=glossary.setdefault(term,[])
        if entry not in entries:entries.append(entry)
    payload=json.dumps(glossary,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')
    page=page[:gmatch.start()]+gmatch[1]+payload+gmatch[3]+page[gmatch.end():]

page=page.replace('太空尚无独立读本，不能直接套环保观点。','<span class="resource-added">已补独立读本：<a href="#topic-space">太空与科研</a>；不能直接套环保观点。</span>')
page=page.replace('<td>后续独立背景</td><td>可先区分预防、回应与责任主体；当前没有对应完整背景章。</td>','<td class="resource-added"><a href="#topic-crime">犯罪与惩罚</a> · <a href="#topic-government">政府公共支出</a> · <a href="#topic-society">社会与代际</a></td><td class="resource-added">已补齐语境、概念、用法、示范与解释；均为原创基础教学。</td>')
page=page.replace('Cambridge 21 Test 2 现优先留作完整基线候选；若已经做过基线，其 Passage 1 只能复盘，不能再次记录为陌生迁移。Test 3 暂留下一轮完整检查，Test 4 继续严格保留。','<span class="resource-added">基线材料状态已修正：背景读本已展示 Cambridge 21 Test 2 Passage 3 和 Test 3 Passage 1/2 的原文片段。若你看过，相关材料应标“部分见过／学习后应用”，不能把整套表现当作完全未见基线。Test 2 Passage 1 若已做过，只用于复盘。Test 4 使用前仍需确认未看过题目、原文和答案；此前见过则另选。</span>')
page=page.replace('8 个主题 · 6 段日常语境','<span class="resource-added">12 个主题 · 6 段日常语境</span>')
page=page.replace("'/ 14 段'","'/ 18 段'")
page=page.replace('已增加 26 个补充学习单元，包含背景、搭配与四科专项；进入各页顶部展开学习。','已有 26 个补充学习单元；本轮另增 '+str(count)+' 个主题与专项教学单元，红色标记，可从各页顶部展开。')
page=page.replace('</head>',mark('style','<style>'+(HERE/'resource-expansion.css').read_text(encoding='utf8')+'</style>')+'</head>',1)
js=(HERE/'resource-expansion.js').read_text(encoding='utf8').replace('__CATALOG__',json.dumps(catalog,ensure_ascii=False).replace('</',r'<\/'))
page=page.replace('</body>',mark('script','<script>'+js+'</script>')+'</body>',1)
from clean_learning_page import clean_html
page,_cleanup_stats=clean_html(page)
MAIN.write_text(page,encoding='utf8')
for name in ['current-speaking.json','skills-resources.json','background-additions.json']:
    shutil.copy2(HERE/name,BOOK/name)
report={'date':'2026-09-16','units':count,'usage_units':uses,'by_section':dict(Counter(x['section'] for x in catalog)), 'catalog':catalog, 'source_integrity':'reported prompts, official resources and original teaching labelled separately','pdf_updated':False,'main_sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest()}
(BOOK/'resource-expansion-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(HERE/'resource-expansion-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
readme=BOOK/'使用说明.txt';text=readme.read_text(encoding='utf8');text=text.split('\n2026-09-16 资源完整性扩充')[0]
readme.write_text(text+f'\n2026-09-16 资源完整性扩充\n新增{count}个教学单元、{uses}组语境用法。首页与左侧“本季题目与新增资源”进入，新增及补齐内容标红。包含16组本季口语回忆主题、4篇此前缺失的背景读本、12个听读写专项。内容可直接学习，复习不作为解锁条件。已学、加入复习与笔记保存在原学习记录JSON。核查来源见页面登记；公开回忆不是官方题库，原创材料明确标识。旧PDF本轮未更新，新增资源以网页为准。\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='catalog'},ensure_ascii=False))
