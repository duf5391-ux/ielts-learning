"""Draw current, observed entry relationships. This is an audit artifact, not site UI."""
from pathlib import Path
from html import escape
from urllib.parse import quote
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/interface-map-20260921'
data=json.loads((OUT/'interface-map.json').read_text(encoding='utf8'))
base=data['site']
def node(title,route='',children=None,issue=''):
    return dict(title=title,route=route,children=children or [],issue=issue)
tree=[
node('学习','#study',[
 node('直接开始：选时长、板块与每日步骤','#guide',[node('学习中：步骤、暂停、休息、收工、笔记'),node('结束：反馈与下次安排')], '① 与“今天选的内容”读取不同安排'),
 node('继续上次：只追踪目录单元',issue='② 词句本、写作工作台、定制课不在此续学范围'),
 node('学习项目：现有材料的组合入口','#learning-projects'),
 node('今天选的内容 → 当前归工作台','#plan',issue='① 加入今天不进入每日安排'),
 node('听力学习 · 7项','#study-listening-list'),
 node('阅读学习 · 15项','#study-reading-list'),
 node('写作学习','#study-writing-list',[node('Task 1 · 10项','#study-writing1-list'),node('Task 2 · 6项','#study-writing2-list')]),
 node('口语学习 · 26项','#study-speaking-list'),
 node('词汇学习 · 25项','#study-vocabulary-list',[node('1000话题词卡：30话题、收藏、熟悉度','#topical-vocabulary',issue='③ 这里的收藏没有进入“我的单词表”'),node('我的词汇资料：来自个人导入','#my-vocabulary-materials')]),
 node('短语学习 · 33项','#study-phrases-list',issue='④ 旅游词汇题外层归练习，具体题却归这里'),
 node('共用背景 · 2项','#study-shared-list',[node('我的话题资料','#my-topic-materials')], '⑤ 每日背景却进入写作 Task 2 的教育话题'),
]),
node('练习','#practice',[
 node('听力 · 10项','#practice-listening-list'),node('阅读 · 56项','#practice-reading-list'),
 node('写作','#practice-writing-list',[node('Task 1 · 11项','#practice-writing1-list'),node('Task 2 · 20项','#practice-writing2-list')]),
 node('口语 · 3项','#practice-speaking-list'),node('题组：作答 → 核对 → 同材料精读'),
]),
node('测试','#tests',[
 node('听力整科 · 40题','#test-listening'),node('阅读整科 · 40题','#test-reading'),node('写作整科 · Task 1＋2','#test-writing'),node('口语整科 · Part 1＋2＋3','#test-speaking'),node('四科组合：依次进入，分别记录'),
]),
node('学习工作台','#workspace',[
 node('写作工作台 · 6题 × 4阶段','#writing-workbench',[node('审题／首稿／检查修订／再练')], '⑥ 学习活动放在工作台；新写作题尚未接入'),
 node('记录与备份','#records',[
   node('资源已学／加入复习列表'),node('我的句子本（内嵌）','#sentence-learning'),node('我的单词表（内嵌）','#vocabulary-review'),node('查词历史（内嵌）','#lookup-history'),node('五章首次记录／笔记／导出恢复')
 ], '⑦ 单词和句子打开后仍是整张记录页'),
 node('我的定制课程 → 当前归学习','#course-window',[node('原料需求／课程导入／独立备份'),node('五阶段：先做 → 理解 → 练习 → 换情境 → 加练')], '⑧ 工作台入口与页面归属不一致'),
 node('我的资料：导入、预览、编辑、导出','#materials'),
 node('原始资料 → 页面叫“资源目录”','#library',[
   node('14组文字题目和练习入口'),node('话题与学习技巧目录 · 44项','#resource-update'),node('原件／打印／反馈／考试要求')
 ], '⑨ 原件管理、教学目录、练习入口混放'),
 node('今天选的内容（重复快捷入口）','#plan'),
 node('我的单词表 → 记录内嵌位置','#vocabulary-review',issue='⑦ 非独立学习页'),
 node('我的句子本 → 记录内嵌位置','#sentence-learning',issue='⑦ 非独立学习页'),
]),
node('开发工作台（侧栏“开发与维护”）','#development',[node('网站文件 → GitHub'),node('发布记录 → GitHub Actions')]),
]
global_nodes=[node('查词浮窗：查词／收藏／原句','#word-lookup'),node('选中文字工具条：查词／收藏／翻译','#selection-toolbar'),node('句子翻译弹窗：译文／修订／收藏','#sentence-popup'),node('健康学习设置：时长／休息／继续／收工','#energy-control'),node('原图弹窗、文件选择、下载、录音权限与错误提示')]
def markup(n):
    title=escape(n['title']);route=n['route']
    if route:title=f'<a href="{base}{quote(route,safe="#")}" target="_blank" rel="noopener">{title}</a>'
    issue=f'<span class="issue">{escape(n["issue"])}</span>' if n['issue'] else ''
    children='<ul>'+''.join(markup(x) for x in n['children'])+'</ul>' if n['children'] else ''
    return f'<li><div class="node">{title}{issue}</div>{children}</li>'
columns=[tree[:1],tree[1:3],tree[3:]]
columns_html=''.join('<section class="tree-column">'+''.join('<div class="tree-group"><ul class="tree">'+markup(t)+'</ul></div>' for t in column)+'</section>' for column in columns)
routes=''.join(f'<tr><td>{r["number"]}</td><td><a target="_blank" rel="noopener" href="{base}#{quote(r["requested"])}">{escape(r["requested"])}</a></td><td>{escape(r["title"] or "")}</td><td>{escape(r["actual"])}</td><td>{escape(" / ".join(r["from"]))}</td></tr>' for r in data['ledger'])
functions=''.join(f'<tr><td>{escape(f["group"])}</td><td>{escape(f["name"])}</td><td>{escape(f["actions"])}</td><td>{escape(f["records"])}</td></tr>' for f in data['functions'])
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>当前网站入口树 · 探针事实图</title><style>
*{box-sizing:border-box}body{margin:0;background:#f8f8f4;color:#203c32;font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1900px;margin:auto;padding:30px}h1{font-size:30px;letter-spacing:-.5px;margin:0 0 8px}h2{font-size:21px}p{margin:6px 0 15px}.meta{color:#52675f;font-size:14px}.legend{background:#edf3eb;padding:12px 18px;border-left:4px solid #456b54}.overview{display:grid;grid-template-columns:1.05fr .78fr 1.17fr;gap:20px;margin:22px 0}.tree-group{background:#fff;border:1px solid #d6dfd3;border-radius:10px;padding:14px 13px;margin-bottom:16px}.tree{padding-left:0!important}.tree>li:before{display:none}.tree>li>.node{font-size:20px;font-weight:700;border-bottom:1px solid #dbe2d9;padding-bottom:8px;margin-bottom:8px}.tree ul{padding-left:22px;margin:5px 0}.tree li{list-style:none;position:relative;margin:5px 0}.tree li:before{content:"";position:absolute;left:-14px;top:-5px;height:20px;width:10px;border-left:1px solid #adbfb0;border-bottom:1px solid #adbfb0}.tree ul>li:not(:last-child):after{content:"";position:absolute;left:-14px;top:15px;bottom:-10px;border-left:1px solid #adbfb0}.node{padding:2px 0}.node a{color:inherit;text-decoration:none}.node a:hover{text-decoration:underline}.issue{display:block;color:#8e4029;font-size:12px;font-weight:500;line-height:1.45;margin-top:2px}.global{background:#fff;border:1px solid #d6dfd3;border-radius:10px;padding:10px 20px;display:flex;flex-wrap:wrap;gap:8px 25px}.global span{font-size:14px}.global strong{width:100%}details{background:#fff;border:1px solid #d6dfd3;border-radius:8px;padding:14px;margin-top:16px}summary{font-size:18px;font-weight:650;cursor:pointer}input{padding:10px;border:1px solid #abc0af;border-radius:5px;font:inherit;width:min(650px,100%);margin:15px 0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid #dbe2d9;text-align:left;padding:10px;vertical-align:top}th{background:#edf3eb}td a{color:#245e45}small{color:#67776f}@media(max-width:1000px){.overview{grid-template-columns:1fr}main{padding:18px}}@media print{details{display:none}main{padding:0}.overview{gap:12px}body{font-size:12px}}
</style><main><h1>当前网站入口树</h1><p class="meta">正式版 2f870d2c… · 2026-09-21 · 429个站内目标逐条读取＋9个独立网页＋24个动态界面状态</p><div class="legend">这是<strong>现状</strong>，不是新排布。树枝表示当前可见入口；“→”说明跳转归属。橙色标注只列已有探针证据的断点。重复链接不自动等于缺陷。</div>'''+columns_html.join(['<div class="overview">','</div>'])+'<div class="global"><strong>跨页面工具（不是上述内容分类的子页面）</strong>'+''.join('<span>'+escape(n['title'])+'</span>' for n in global_nodes)+'''</div><details><summary>42项功能与保存关系</summary><table><thead><tr><th>范围</th><th>界面</th><th>功能</th><th>记录去向</th></tr></thead><tbody>'''+functions+'''</tbody></table></details><details><summary>429个站内目标逐条清单</summary><input id="search" placeholder="搜索入口、标题或实际落点"><p id="count">429 / 429</p><table id="routes"><thead><tr><th>序号</th><th>入口</th><th>探针显示标题</th><th>实际落点</th><th>入口来源</th></tr></thead><tbody>'''+routes+'''</tbody></table></details><p class="meta">已打开和读取不等于全部功能验收；保存、录音、导入等按操作证据另记。正式页未因本图修改。逐页全文及控件证据：ui-route-probe-20260921/full-content/。</p></main><script>const q=document.getElementById('search'),rows=[...document.querySelectorAll('#routes tbody tr')];q.addEventListener('input',()=>{let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(q.value.trim().toLowerCase());if(!r.hidden)n++;}document.getElementById('count').textContent=n+' / '+rows.length;});</script></html>'''
(OUT/'现状入口树.html').write_text(html,encoding='utf8')
lines=['# 当前网站入口树','', '按实际入口画树，不是新设计。括号标注已证实的问题；重复链接不自动等于错误。','', '```text','网站']
def plain(nodes,prefix=''):
    for i,n in enumerate(nodes):
        last=i==len(nodes)-1;lines.append(prefix+('└─ ' if last else '├─ ')+n['title']+(' 【'+n['issue']+'】' if n['issue'] else ''))
        plain(n['children'],prefix+('   ' if last else '│  '))
plain(tree);lines+=['```','','## 从树上复核出的结构问题','',
'1. 同级入口混合了科目、活动、资料管理、记录与开发维护，不是一个稳定的分类维度。',
'2. 工作台里的词句入口实际落在记录页内部；写作也是学习活动，却列在工作台。',
'3. 入口来源、侧栏归属、页头与返回路径有时不同，例如定制课程、旅游词汇、每日共用背景。',
'4. “今天”“继续”在不同位置读取不同状态，用户无法仅凭名称判断接下来会做什么。',
'5. 原始资料目录混入教学与练习；原件和学习内容缺少清晰边界。',
'6. 同一材料的不同活动与答案需要分别保留，但现在缺少跨入口关系提示；不能用合并旧答解决。',
'','这些问题有路径与记录证据支持；树图用于检查功能边界，下一步排布必须据此处理，而不是只换标签。','', '[打开可搜索的现状树](现状入口树.html) · [全部入口](全量入口表.md) · [功能总览](功能总览.md)']
(OUT/'现状入口树.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print('Created current tree with observed links, 42 functions, 429 target rows.')
