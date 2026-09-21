from pathlib import Path
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
path = ROOT / 'local-learning-architecture.json'
data = json.loads(path.read_text(encoding='utf-8'))
for item in data['items']:
    item['action'] = item['improvement']
    item['evidence_quotes'] = item['evidence'] if isinstance(item['evidence'][0], str) else item['evidence_quotes']
    item['evidence'] = [{'quote': quote, 'selectors': item['locations'], 'note': '本条证据位于列出的相关范围；多位置为联合评审。'} for quote in item['evidence_quotes']]

data['rubric'] = [
    {'dimension':'用途与目标', 'qualified':'入口明确告诉学习者这项活动要理解或练成什么；短教学材料只承诺窄目标。', 'unqualified':'用途混淆、目标无法观察，或以局部表现代表整科水平。'},
    {'dimension':'理解与示范', 'qualified':'解释、题面、范例及对应关系足以支撑当前目标；可以使用自编短例。', 'unqualified':'事实或答案错误，必要信息缺失，或范例不能说明所教规则。'},
    {'dimension':'独立应用', 'qualified':'需要练习的单元有学习者实际作答，支持条件明确；背景输入允许不做题。', 'unqualified':'只有看答案/重复已讲题，却缺少该技能需要的新应用。'},
    {'dimension':'反馈修订', 'qualified':'能指出具体证据和可改变的一处行为，允许合法替代表达。', 'unqualified':'只有范文比对或笼统判断，学习者不知道怎么修改自己的作答。'},
    {'dimension':'延迟与迁移', 'qualified':'分别记录熟题回忆和新情境使用，材料与任务可执行，避免把难度差异直接解释为进步。', 'unqualified':'只有下次再练的口号，或用熟题记忆充当新能力证据。'},
    {'dimension':'学习管理', 'qualified':'有限时间内可选任务、可降负荷、可据证据决定继续/修复/迁移；手动安排完全可接受。', 'unqualified':'目录膨胀而无选路、待办无优先级、完成量替代掌握证据。'},
    {'dimension':'材料身份（独立轴）', 'qualified':'明确材料身份和核验范围，不冒充官方或预测命中；这不自动证明教学充分。', 'unqualified':'身份误导或来源声称不成立；自编本身不是不合格。'}
]

inventory = [
 ('guide','学习首页','背景优先主入口；下一步卡；五章首答进度；阅读/听力/Task1/Task2/口语卡；教育/工作/科技快捷背景；低负荷提醒','导航卡、简短用途、用时、进度','从首页选背景或核心章节；也可转学习安排。','下一步目前是固定背景建议，未由证据驱动。'),
 ('plan','学习安排','新学与复习并行；首轮试学；阅读日/Task1日/Task2日/听力日/口语日；另日修订与隔日回忆；背景替换时间预算','计划说明、时间表、负荷原则','选一个时段的主任务；后续另日回到修订/迁移。','第一册使用安排，不是完整八周课程清单。'),
 ('background','话题背景','12段原材料摘读；家庭/食物/旅游/媒体4篇扩展读本；犯罪/政府/社会/太空与教育等12主题；六段个人生活；自添话题；主题映射；每日使用说明','中文概念、英文情境、中文理解、搭配表、易混辨析、对话、可选回顾、来源入口','选一段读懂→看2—3组表达→可选回顾/生活联系→隔日换情境。','不同背景类型并列；回顾不强制。'),
 ('vocabulary','词汇与用法','136组新增语境用法索引；12个搭配微课；30话题1000词条检索；精选词义与搭配练习；24个跨话题常见词；20组原文用法卡；自添词汇','词义/词性、搭配、例句、中文解释、词典发音外链、K/R/N自评、收藏、填空/改写/输出','词库查阅/收藏，或微课意义结构→首稿→反馈修订→隔日迁移。','词库查阅与主动学习微课不是同一种完成证据。'),
 ('reading','阅读','7个技巧单元：定位/判断/标题/信息人物匹配/填空/图示/选择复盘；4个主题练习；Miles Davis和Older workers两项补充课；Davies Sisters核心13题','完整文章/短篇、题干、答题框、示范、逐题证据、错误对照、方法步骤、可选练习','核心：20分钟首答→查一处错误→学习与修订→逐题自核→短迁移→另一未见判断材料。','新增技巧在核心章节之前；示范/练习/核心之间需要明确选路。'),
 ('writing1','写作 Task 1','5个技巧：读图/概览/精确数据/流程/地图；地图改造和交通趋势2新课；英国继续教育柱图、制砖流程2补充课；美国就业折线图核心','本地图、数据表、题面、完整范文/示范段、逐句数据证据、改错、草稿与修订','核心：20分钟原稿→中文核图→概述/数量表达局部修复→样本评语→隔日换数字→陌生地图概述。','不同图型迁移检验目标已解释；同通勤图多个微课不能算多个独立测试。'),
 ('writing2','写作 Task 2','环境讨论/社区原因措施2新课；家庭财富观点/旅游利弊2补充课；数字时代剧院影院核心','题面、观点拆解、机制解释、例子、词块、参考段/全文、原书考生样本评语','核心：40分钟原稿→核题目义务→选一个理由展开→修订一段→新工作情境60—90词迁移。','新增单元多是先学后用；与核心未见首答不能混作基线。'),
 ('listening','听力','课堂通知/分工/天气/讲座4新课；运输保险选择和客户来电2补充课；货运报价1—8核心；开放大学27—30迁移','音频播放器、题面/表格、答案、文字稿、声音信息所指表、表达转换','核心：按条件首听留答→只重听一处→必要时查稿→修复与自核→延迟熟片→另一原声题组。','8题与4题的原始正确率不直接表示升降。'),
 ('speaking','口语','16组主题课；Part1自然短答与Part3解释比较2补充课；重要物品Part2核心与原题追问；新追问和后续完整P1—3指引','语境阅读、词块与易错、短示范、P1/P2/P3问题、音频/文字稿、录音/下载、时间点笔记','核心：准备1分钟/说1—2分钟→保存录音→回听一处→短支架或重答→隔日追问→后续完整练习。','主题课与核心录音闭环不完全一致；手机录音也可完成。'),
 ('records','学习记录','已学新单元；加入复习；查词待复习/全部/已复习；补充单元首稿记录；五章作答与实际用时；学习笔记；导出文字/备份/恢复','行为统计、状态列表、首答记录、自由笔记、备份说明','查看已留记录→回到单元→复习/取消复习；录音单独保存。','行为完成与掌握已区分，但缺一张跨单元技能证据/下一步汇总。'),
 ('library','资源目录','14组文字题目全文搜索；当前147块审核摘要；44个话题技巧分类目录；背景读本/打印学习册/参考反馈入口；考试要求表；58份配套文件入口','搜索、科目分类、卡片、审核状态、规则表、PDF/音频/图片/文本链接','找题目/技能/文件→跳到当前章节或原件；可以核对规则与答案。','数量为当前目录显示数；58是入口条目数，存在同文件重复入口，不等同58个独立教学单元。'),
 ('materials','我的资料','粘贴/文件导入；词汇搭配/背景/题目讲解/其他类型；整段或逐行词表；标题/标签/来源；预览；新增资料列表和导出','自填资料、TXT/Markdown/TSV/JSON导入、分类筛选、预览','录入→预览→保存→在词汇/背景/资料入口查阅。','用户材料未核验，不自动计入原材料真实性或教学合格；本次未操作导入。')
]
data['page_inventory'] = [dict(zip(['anchor','title','modules','content_types','observed_learning_flow','boundary'], row)) for row in inventory]
data['inventory_method'] = '依据当前HTML可见文本、导航、控件和对应内容块整理页面功能/内容构成；不是浏览器交互回归，不声称所有控件已实际点击或录音成功。'
source = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
soup = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser')
panels = {p['id']:p for p in soup.select('.panel[id]')}
for page in data['page_inventory']:
    assert page['anchor'] in panels
    page['selector'] = '#' + page['anchor']
data['content_catalog'] = [{k: x[k] for k in ['id','title','category','selector']} for x in json.loads((ROOT.parent/'architecture-audit-qa/live-items.json').read_text(encoding='utf-8'))]
data['flow_baseline'] = {
 'core':'首页/导航→选章节→真实首答→保存条件→定位一个实际问题→输入/示范→有支持修复→反馈自核→隔日提取→陌生材料窄迁移→手动选择下一任务',
 'supplement':'目录/科目页→技巧或主题→输入与示范→练习（部分重复示范）→参考解释→已学/加入复习→自行寻找下一材料',
 'background':'话题入口→一段概念/语境→中文理解→少量表达→可选回顾→可选个人联系→隔日抽取表达',
 'vocabulary':'查词/话题词库→释义搭配→收藏/KRN→记录页复习；12个搭配微课另有首稿/反馈/迁移',
 'breakpoints':['起点和目标到首个任务的决策','补充单元到独立新题的衔接','跨单元证据到下一步与复习优先级']
}
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

mdpath = ROOT/'local-learning-architecture.md'
md = mdpath.read_text(encoding='utf-8').split('\n## 页面与内容构成基线')[0]
md += '\n## 页面与内容构成基线\n\n' + data['inventory_method'] + '\n\n'
md += '当前有12个主面板；JSON同时附147项内容块标题与定位的完整目录。下表展示用户使用的页面、子模块、内容形态及流程。\n\n'
md += '| 页面 | 子模块 | 内容形态 | 使用流程 | 范围备注 |\n|---|---|---|---|---|\n'
for page in data['page_inventory']:
    md += '| ' + ' | '.join([f"{page['title']} `{page['selector']}`",page['modules'],page['content_types'],page['observed_learning_flow'],page['boundary']]) + ' |\n'
md += '''
### 当前学习流程（页面关系，不是软件技术架构）

```mermaid
flowchart TD
  H[学习首页与导航] --> B[背景：选一段理解]
  H --> C[五章核心任务]
  H --> L[资源目录 / 科目专项]
  B --> E[少量表达与可选回顾]
  E --> D[隔日换情境]
  C --> A[首答与实际条件]
  A --> P[选一处实际问题]
  P --> I[输入 / 示范 / 支架]
  I --> F[反馈核对与自己修订]
  F --> R[延迟回忆]
  R --> N[未见材料窄迁移]
  L --> S[技巧 / 主题补充课]
  S --> X[学习与练习]
  X --> Y[参考解释 / 已学 / 加入复习]
  Y -. 部分缺具体材料 .-> N
  V[词库 / 查词] --> K[收藏 / KRN自评]
  K --> M[学习记录与复习]
  N --> M
  Y --> M
  M -. 需学习者自行作决定 .-> H
```

核心路径已经成形。结构性缺口位于入口选路、补充课独立新题，以及记录返回下一任务的决策；并非全册都缺输入、示范、反馈或迁移。

### 教学合格的复核标准

下列标准按活动用途应用，不要求背景阅读也做完整测试。真实性单独记录，不能替代教学质量。

| 维度 | 合格条件 | 不合格条件 |
|---|---|---|
'''
for r in data['rubric']:
    md += f"| {r['dimension']} | {r['qualified']} | {r['unqualified']} |\n"
mdpath.write_text(md,encoding='utf-8')
print(json.dumps({'items':len(data['items']),'pages':len(data['page_inventory']),'catalog':len(data['content_catalog']),'counts':data['counts']},ensure_ascii=False))
