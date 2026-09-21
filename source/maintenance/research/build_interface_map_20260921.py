"""Describe the current UI only; do not modify the workbook or propose a new layout."""
from pathlib import Path
from collections import Counter
from urllib.parse import quote
from bs4 import BeautifulSoup
import json,hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/interface-map-20260921'
PROBE=ROOT/'research/ui-route-probe-20260921'
OUT.mkdir(exist_ok=True)
raw=(ROOT/'ui-repair-20260921/baseline.html').read_bytes()
s=BeautifulSoup(raw.decode('utf8'),'html.parser')
catalog=json.loads(s.find(id='learning-adjust-data').string)
ledger=json.loads((PROBE/'full-content/ledger.json').read_text(encoding='utf8'))
assert ledger['visited']==ledger['expected']
units={u['id']:u for u in catalog['units']}
panels={n['id']:n for n in s.select('main > .panel')}
rows={r['requested']:r for r in ledger['ledger']}
categories=[r for r in rows if ('分类页' in rows[r]['from'])]
external=json.loads((PROBE/'interface-inventory.json').read_text(encoding='utf8'))
base='https://duf5391-ux.github.io/ielts-learning/'
def clean(x):return str(x or '').replace('|','／').replace('\n',' ').strip()
def link(route,title=None):return f'[{clean(title or route)}]({base}#{quote(route)})'
def label(ident):
    if ident in units:return units[ident]['title']
    if ident in panels:return panels[ident].get('data-la-title',ident)
    n=s.find(id=ident)
    heading=n.find(['h1','h2','h3','summary']) if n else None
    if heading:return heading.get_text(' ',strip=True)[:120]
    return rows[ident]['title'] or ident

functions=[
('总入口','学习首页','#study','查看四科学习分类、词汇/短语/背景、继续上次、每日安排和学习项目。','整册记录中的最近内容'),
('总入口','练习首页','#practice','按听读写说选择练习，继续选话题、题型、Part；写作再分 Task 1/2。','整册作答与完成记录'),
('总入口','测试首页','#tests','选择四科整科测试，或按四科组合顺序测试。','整册中的独立测试状态'),
('总入口','学习工作台','#workspace','现有八个快捷入口：写作、记录、定制课、我的资料、原始资料、今天清单、单词表、句子本。','入口自身不另存答案'),
('总入口','开发工作台','#development','打开网站文件仓库和发布运行记录。','没有学习记录'),
('安排','直接开始／今天的安排','#guide','选15/30/60分钟、板块、Task类型；阅读可选材料；可选阅读后写作；开始或恢复会话。','daily-study-state'),
('安排','今天选的内容','#plan','接收卡片的“加入今天”，打开所选内容、查看进度、移出。当前清单无日期。','learning-adjust-state.today，与每日会话分开'),
('安排','学习中工具栏','daily-study-dock','显示当前步骤、建议时间；暂停/继续、完成步骤、说明、笔记、休息、收工、查看安排。','每日会话及健康提醒状态'),
('安排','随手记弹窗','ds-note','填写、保存可选会话笔记，关闭弹窗。','每日会话笔记'),
('安排','学习结束反馈','ds-completed','显示完成步数和用时；选比较顺利、还想再练、暂时跳过；查看笔记。','每日会话与历史'),
('学习内容','四科学习分类','#study-*-list','听力7、阅读15、Task 1为10、Task 2为6、口语26；进入讲解/题目/精读等具体单元。','按原单元字段保存'),
('学习内容','词汇／短语／共用背景分类','#study-vocabulary-list / #study-phrases-list / #study-shared-list','词汇25、短语33、背景2个目录单元；这些不是“我的收藏”。','按原单元字段保存'),
('学习内容','学习项目','#learning-projects','按现有材料组织建议顺序，含近期机经、新九分机经、阅读、写作和听力项目。','引用原单元进度，不另复制答案'),
('学习内容','原五章首次作答与教学','#reading-first 等','首次作答、保存原稿、展开学习/修订、核对、可选再试；对应五章是听力、阅读、Task 1、Task 2、口语。','五章首次快照及对应字段'),
('练习内容','四科分类与题组','#practice-*-list','听力10、阅读56、Task 1为11、Task 2为20、口语3；作答、保存、答案门控、核对及题后材料回读。','各题自己的作答与核对状态'),
('练习内容','阅读精读与写作前置','material-reading-* / writing-prep-*','同材料理解、词块、长句解释；高拟合写作表达在匹配写作前出现；也由每日安排直接进入。','复用材料/单元身份与每日步骤'),
('测试','听力整科','#test-listening','开始计时、40题作答、提交、参考答案核对、重做、历史。','独立于学习/练习答案'),
('测试','阅读整科','#test-reading','开始计时、40题作答、提交、参考答案核对、重做、历史。','独立测试答案与历史'),
('测试','写作整科','#test-writing','Task 1/2原稿、计时、提交、参考标准、重做、历史。','独立测试原稿'),
('测试','口语整科','#test-speaking','开始后显示Part 1/2/3、各自录音/载入、下载、文件记录、提交与历史。','文字记录进整册；声音单独下载'),
('测试','四科组合','la-start-mock','依次进入四科，分别计时、保存、提交，继续下一科。','组合进度与各科独立测试记录'),
('单词','1000话题词卡','#topical-vocabulary','30话题；搜索/状态筛选/分页、收藏、N/R/K熟悉度、查词、用词造句、查看来源。','topic-vocab-* 字段'),
('单词','我的单词表','#vocabulary-review','收藏列表、搜索/筛选、直接标不会/模糊/会、释义/原句、补充释义和例句、取消收藏。','lookup-history-v1；与1000词卡收藏尚未接通'),
('单词','单词复习与拼写','vr-stage','到期复习、全部加练、单词加练；英文回忆/中文拼写；提示、判定、暂停及复习时间。','查词记录内的独立复习数据'),
('单词','查词浮窗','#word-lookup','点击正文英文或手动输入；词典释义、搭配、原句、收藏、去单词表。','lookup-history-v1'),
('单词','查词历史','#lookup-history','搜索、按状态筛选、再次查词、收藏/取消、旧复习标记、导出查词JSON。','lookup-history-v1，当前嵌在记录页'),
('单词','我的词汇资料','#my-vocabulary-materials','阅读自己导入的词表/词汇资料，回资料管理添加或编辑。','独立“我的新增资料”数据'),
('句子','选中文字工具条','#selection-toolbar','查词、收藏词组、翻译选中句子、关闭；正文与自己写的内容均可选取。','操作分别进入词库或句子本'),
('句子','翻译与编辑弹窗','#sentence-popup','原句、英中方向、在线翻译/本册配套译文、编辑译文、收藏、打开必应。','sentence-collection-v1；在线只发送所选原句'),
('句子','我的句子本','#sentence-learning','搜索收藏的原句/译文，查看修改、取消收藏；当前没有单独的间隔复习队列。','整册内句子收藏，当前嵌在记录页'),
('写作','写作工作台','#writing-workbench','选六道现成题；审题提纲→首稿计时/保留→四维检查与修订→再练；保留修订版本、导出反馈请求。','ww-* 字段；与同题其他入口原稿分开'),
('定制课程','课程窗口','#course-window','添加原料/能力要求、导出设计需求；导入已设计课程；选课程、五阶段、选择/文本作答、提示条件、提交反馈、自评、历史。','ielts-course-window-v1，独立备份'),
('资料','我的资料管理','#materials','粘贴、TXT/MD/TSV/JSON导入、预览、去重保存；四种资料类型；搜索、阅读器、编辑、删除、导出。','ielts-user-materials-v1，独立于整册记录'),
('资料','我的话题资料','#my-topic-materials','阅读自己导入的背景文章/话题笔记，回资料管理。','复用我的新增资料'),
('资料','原始资料／资源目录','#library','现混合文字题目、题组入口、教学目录、打印/反馈文件、考试要求和原始文件搜索。','目录本身不存新答案'),
('资料','话题与学习技巧目录','#resource-update','44个教学单元的筛选、搜索和直达；原文件入口另列。','原单元已学/复习勾选'),
('资料','文字题目与案例组入口','*-text-* / *-case-bank / pp-*','文字化题面、原图、阅读/写作案例银行和Part题组；最终使用各自原单元字段。','复用原题组记录'),
('记录','记录与备份','#records','原五章首次答题状态、教学已学/加入复习、笔记、单词/句子记录；导出文字、整册JSON备份和恢复。','ielts-finished-book-v1，3368个字段及首次快照'),
('全局交互','健康学习提醒','#energy-control','学习时段与休息设置、开始、休息、继续、收工；与每日计时联动。','整册 energy-control-state'),
('全局交互','原页大图弹窗','运行时 dialog','从“查看原图”放大题面图片、关闭。','不保存学习成绩'),
('全局交互','手机导航抽屉','#mobile-menu','展开/关闭导航，切换入口、返回；键盘焦点与遮罩。','无独立答案'),
('全局交互','文件/声音/保存提示','文件选择器、下载、权限与错误提示','资料/课程/记录各自导入导出；麦克风授权、录音与载入、下载；保存失败/冲突提示。','随所属模块保存，录音不属于文字备份'),
]
summary=['# 当前全站接口与功能清单','', '这是当前实现的事实清单，不是新的导航或排布方案。用户要求先逐个探针核查、列清功能；候选修改已暂停，正式网站未因本轮清单发生修改。','',
f'基线正式册 SHA-256：`{hashlib.sha256(raw).hexdigest()}`。逐条实际浏览器读取 **{ledger["visited"]} 个站内目标**，以及 **9 个独立网页**。站内目标包含主面板、分类、具体单元和内层位置，不等于429个独立页面。全部正文和控件状态保存在 `../ui-route-probe-20260921/full-content/`。','',
'“已打开并读取”只表示有实际探针证据；保存、导入、录音等操作是否通过必须另看具体流程记录，不把静态存在或打开成功当成功能验收。','',
'## 功能总表','', '|范围|当前接口|能够做什么|记录/关系|','|---|---|---|---|']
for group,name,route,action,record in functions:
    summary.append(f'|{group}|{name}<br>`{route}`|{clean(action)}|{clean(record)}|')
summary+=['','## 目录内容数量（具体224项见全量表）','','|内容|学习|练习|','|---|---:|---:|']
counts=Counter((u['mode'],u['skill']) for u in units.values())
for key,title in [('listening','听力'),('reading','阅读'),('writing1','写作 Task 1'),('writing2','写作 Task 2'),('speaking','口语'),('vocabulary','词汇'),('phrases','短语'),('shared','共用背景')]:summary.append(f'|{title}|{counts["study",key]}|{counts["practice",key]}|')
summary+=['','这里的“目录单元”不包括工作台六题、定制课程五阶段、词卡内1000条、词句收藏和独立资料网页。不能用224个内容路由代表全部界面。',
'','## 目前实际关系与已经确认的断点','',
'- 四科分类／学习项目／每日安排会引用同一批已有内容；不同任务的作答仍各自保留。',
'- 1000词卡收藏与查词收藏是两套状态；前者当前没有进入“我的单词表”。',
'- “我的单词表”和“我的句子本”是学习功能，但现在嵌在记录页；写作工作台列在工作台。',
'- “原始资料”已经在工作台，但内部又混有教学和练习目录。',
'- “加入今天”写自选列表；“直接开始”按时长/板块生成每日步骤，没有读取该列表。',
'- “继续上次”只认目录单元；每日会话、词句本、写作工作台、定制课各有状态，续学入口没有统一说明。',
'- 我的资料、定制课程、整册学习记录是三个保存体系；录音声音另行下载。保存资料不会自动生成定制课。',
'- 同一材料可以出现在学习、练习、写作工作台和测试；这些不应当被误认为同一份草稿或一次新题测试。',
'','[查看全部429个站内目标及9个独立网页](全量入口表.md) · [读取每个页面的全文与控件探针](../ui-route-probe-20260921/full-content/ledger.json) · [已确认问题清单](../ui-experience-audit-20260921.md)']
(OUT/'功能总览.md').write_text('\n'.join(summary)+'\n',encoding='utf8')

full=['# 全量入口表：逐个实际探针读取','',f'共 {len(rows)} 个站内目标，按主面板、分类、内容、内层目标拆列；另附9个独立网页。每行对应一份完整正文/控件探针。','', '## 33个主面板地址','', '|入口|现在名称|当前归属|探针实际落点|','|---|---|---|---|']
for ident,n in panels.items():full.append(f'|{link(ident)}|{clean(n.get("data-la-title"))}|{n.get("data-la-owner")}|`{rows[ident]["actual"]}`|')
full+=['','## 18个分类地址','','|入口|名称|当前单元数|','|---|---|---:|']
for ident in categories:
    mode=ident.split('-')[0];skill=ident[len(mode)+1:-5]
    count=sum(u['mode']==mode and (u['skill']==skill or skill=='writing' and u['skill'] in ['writing1','writing2']) for u in units.values())
    full.append(f'|{link(ident)}|{clean(rows[ident]["title"])}|{count}|')
full+=['','练习下词汇、短语、共用背景三个保留分类地址目前各为0个目录单元；不是当前练习首页显示的三个入口。写作总分类的数量是Task 1与Task 2之和，不重复计入224。','', '## 224个具体内容单元','']
for mode,mode_name in [('study','学习'),('practice','练习')]:
 for skill in ['listening','reading','writing1','writing2','speaking','vocabulary','phrases','shared']:
    selected=[u for u in units.values() if u['mode']==mode and u['skill']==skill]
    if not selected:continue
    full += [f'### {mode_name}／{selected[0]["skillLabel"]}（{len(selected)}项）','', '|内容|入口|当前内容内控件数|完整探针|','|---|---|---:|---|']
    for u in selected:
        r=rows[u['id']];full.append(f'|{clean(u["title"])}|{link(u["id"])}|{r["controls"]}|[正文与控件](../ui-route-probe-20260921/full-content/{r["file"]})|')
    full.append('')
others=[r for ident,r in rows.items() if ident not in units and ident not in panels and ident not in categories]
full += [f'## {len(others)}个其他内部位置','', '包括词句本、写作阶段、资料子区、题面、精读与写作前置。许多是同一页面内部位置，并非另一个独立页面。','', '|位置名称|入口|所在实际面板|入口来源|完整探针|','|---|---|---|---|---|']
for r in others:full.append(f'|{clean(label(r["requested"]))}|{link(r["requested"])}|{r["panel"]}|{clean("、".join(r["from"]))}|[正文与控件](../ui-route-probe-20260921/full-content/{r["file"]})|')
full += ['','## 9个独立网页','', '|网页|当前功能|实际打开|','|---|---|---|']
descriptions=['完整来源词表，搜索、来源/类型筛选、分页、词典与源数据下载','扩展PDF目录，按科目/用途搜索筛选','独立词典查询、释义和说明','限定语料内的词频、排序、分页、原文例句','鸟类起源阅读原文（只读）','听力Part 4题面参考（只读）','近期机经内容目录、难度依据、题组链接','九道Task 2题干参考、难度依据、作答入口','新增语言起源与三道Task 2目录、难度依据、作答入口']
for x,desc in zip(external['results'],descriptions):full.append(f'|[{clean(x["title"])}]({base}{quote(x["requested"])})|{desc}|HTTP {x["httpStatus"]}，已读取页面|')
full+=['','## 动态界面','', '查词与翻译弹窗、手机导航、每日工具栏与笔记/结束反馈、健康设置、定制课程五阶段、资料预览/阅读/编辑、测试开始后的题面不全由独立URL区分。逐次点击状态保存在 `../ui-route-probe-20260921/dynamic-interfaces.json`；该文件只在探针运行完成时生成。','', '候选修改未接回正式页。完整功能与保存关系见[功能总览](功能总览.md)。']
(OUT/'全量入口表.md').write_text('\n'.join(full)+'\n',encoding='utf8')
(OUT/'interface-map.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(raw).hexdigest(),'site':base,'siteTargets':len(rows),'mainPanels':len(panels),'categoryRoutes':len(categories),'catalogUnits':len(units),'otherTargets':len(others),'standalonePages':len(external['results']),'functions':[dict(zip(['group','name','entry','actions','records'],f)) for f in functions],'ledger':list(rows.values())},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'siteTargets':len(rows),'panels':len(panels),'categories':len(categories),'units':len(units),'otherTargets':len(others),'standalone':len(external['results']),'functionAreas':len(functions)},ensure_ascii=False))
