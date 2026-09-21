# IELTS 正式册信息架构只读探针 · 2026-09-21

本报告只读 HTML、嵌入脚本及工作区维护脚本；未读取浏览器个人记录，未修改运行文件，未发布，未进行设计修复。浏览器实际打开与截图由主任务另行记录，以下不冒充界面实测。

正式文件：`C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html`。README 顶部与 `feature-fixes-20260921/installation.json` 指向同一文件；原始字节 SHA-256 为 `2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85`。下文“L”均指该正式 HTML 的真实文本行号；一些 HTML 块压在同一长行，须结合 route 定位。

## 能直接证实的主要结论

1. **用户明确指出的分类问题确实存在。** `#writing-workbench` 的 owner 是 workspace（L6581），`#vocabulary-review` 和 `#sentence-learning` 都嵌在 workspace 所属的 `#records` 中（L5551、5559），主入口又列在“学习工作台”的八张卡片内（L6734）。按本轮用户定义，这三者属于学习。只是改三个标签仍不能处理下列其余结构问题。
2. **“原始资料”已有工作台归属，但内容不是一个纯资料目录。** `#library` 的 owner=workspace、路由标题=原始资料，页面大标题仍是“资源目录”，里面同时放着14组文字题目、38/8/12组阅读/写作片段练习、44个教学单元、考试要求和原始文件（L5564）。`#resource-update` 仍是它的“话题与学习技巧”子区。现阶段不能把“原始资料属于工作台”错误理解为需要再搬一次整个资料目录；需要先辨清其中的教学/练习入口。
3. **“今天选的内容”和“今天的安排”是两个独立机制。** 学习/练习卡片的“加入今天”写入 `learning-adjust-state.today`（L9124），`#plan` 由这个数组渲染（L9162–9165）；`#guide` 的每日安排读取独立的 `daily-study-state` 与 `daily-study-catalog`（L9533–9535），用 `M.plan(state.preferences,catalog,state.history,...)` 生成（L9640）。没有读取前者的 selected/today 队列。两个入口都在全局侧栏，学习首页又同时提供它们（L460、6734），但前者属于学习工作台、后者属于学习。不能承诺“加入今天”后“直接开始”就会执行这些内容。另一个确定差异是today只有持久ID数组、没有日期字段，read直接恢复该数组（L9033–9051）；加入/移出也不按日期处理（L9124）。因此“今天选的内容”实为持续保留到手动移除的清单，不会因为新一天自动更新。
4. **“继续上次”也有两种含义。** 学习首页的 `#la-resume` 取 `learning-adjust-state.last`，只在 catalog 单元进入时更新（L9166、9212）；每日安排的“继续这次学习”恢复 `daily-study-state.session`（L9541–9544、9641–9647）。写作工作台、词句本、定制课程不在224单元 catalog 内，不能靠前一种“继续上次”承接；它们另有自己的页面与状态。这里证实的是机制不同，不推断用户记录已经丢失。
5. **同一词汇练习的外层与单元归属冲突。** `#pp-vocabulary` 在 `#practice-phrases` 内，按 panel owner 显示练习；其唯一题目 `#pr-vocabulary-tourism` 在 catalog 中却是 mode=study、skill=phrases（L6897、9025）。单元标题是“词汇 · 旅游语境 在语境中选择措辞”，实际是40–55词改写、介词填空及再写，而 catalog category 是“选择题”。进入具体题目后 owner 改由 unit.mode 决定（L9208），返回学习/短语。外层和具体题目路径应由浏览器探针对照。
6. **“共用背景”跨入口指向不同分类。** 新学习目录的 `#study-shared-list` 只有 `#learn-155`、`#topic-cities` 两项；但每日“共用背景”四步固定去 `#topic-education`（daily catalog，L9283），后者登记为学习/写作·Task 2（总 catalog，L9025），因此页头与返回路会落到写作。其他旧话题也分散在阅读练习、听力练习、口语学习等分类；“共用背景”不等于所有原话题面板内容。
7. **旧 route 改写损失了具体写作类别。** `#writing1` 和 `#writing2` 都重定向到 `#study-writing-list`；`#practice-writing1`、`#practice-writing2` 都去 `#practice-writing-list`（L9200）。因此旧“回到本科学习”、记录中的“进入章节”可能只回到 Task 选择页，不能按文字假定已经直达原Task或原稿。它们不是404死链接，是落点精度退化。
8. **学习工作台混放不同职能，返回语义不统一。** 八项分别是写作工作台、记录与备份、我的定制课程、我的资料、原始资料、今天选的内容、我的单词表、我的句子本（L6734）。`#course-window` 的 owner=study，返回“学习”（L6581），但主要快捷入口在工作台；另外 `#my-vocabulary-materials`、`#my-topic-materials` 在学习内，管理又去工作台的 `#materials`（L7214）。这表明“学习工作台”当前同时承担学习活动、资料管理、记录备份和计划收藏，并没有按对象或动作形成稳定边界。

## 学习、练习、测试的实际定义

总 catalog 共224单元：学习124、练习100。所有带 `data-learning-unit` 的正式单元均有 catalog 登记，不存在本次探针发现的漏登记单元。

- 学习入口按四科和词汇/短语/共用背景分类，默认描述是“讲解与配套练习”；它本身允许先独立作答，如 `#reading-first`、`#writing1-first`、`#speaking-first`，因此“学习=只看讲解”不成立。
- 练习入口并非只有题面。阅读38组带同材料精读；写作案例包含参考段落与逐段讲解，例如 `#writing1-case-wc-c21-t1-jobs`（L6897）。这是已实现的内容体验，不能仅依据“练习”名称断言里面应删掉精读。
- 测试有独立的四科题面、计时、提交状态和历史，入口文案也明确学习/练习记录不冒充测试进度（L6734、9215–9262）。整科听力是官方体验题，阅读/写作是Cambridge21 Test1，口语是公开样题组合，页面已写明各自来源，不能误报为一套来源混同的“真卷”。
- 测试计时到点仅显示“建议时间已到”，不会自动中断输入（L9262）；这是当前实现的自测行为，不宜把它描述成完整仿真考试环境。

**跨路径同源材料会重复出现，并且答案字段不同。** 例如“四行业就业”同时有学习 `#writing1-first`（`writing1-essay`）、片段练习 `#writing1-case-wc-c21-t1-jobs`（`case-wc-c21-t1-jobs-answer`）、小练 `#pr-writing1-jobs`（`pr-writing1-jobs-q1/q2`）、工作台 `#ww-jobs`（`ww-jobs-first/revision`）、测试 `#test-writing`（`full-test-writing-task1`）。学习和工作台提供熟题/提示条件记录；测试仅有自己的作答字段，没有这些条件控件（L5877、6583、6897、7149）。

这不是“字段不同=错误”：不同任务需要分别留答。但当前入口和测试界面不能自动代表“没见过这份材料”，也没有统一的同材料身份/答案跨路径衔接。本轮只记录这个可核对事实，不要求覆盖或合并旧答。

## 顶层入口、次级入口与遗留导航

全局侧栏（L460）有五个主按钮：`#study` 学习、`#practice` 练习、`#tests` 测试、`#workspace` 学习工作台、`#development` 开发工作台。另有“直接开始学习”`#guide`、“今天选的内容”`#plan`。开发工作台只有GitHub仓库和Actions两个外链（L6735）；本次未联网检验其可达性。

学习/练习目录各预埋九个分类锚点：listening、reading、writing、writing1、writing2、speaking、vocabulary、phrases、shared，形式为 `#study-<分类>-list` / `#practice-<分类>-list`（L6734）。根层先生成听读写说四科，写作再分Task1/Task2；学习另显词汇、短语、共用背景。practice-vocabulary/phrases/shared三个锚点存在，但目前没有对应mode=practice单元，主入口也未提供这三张卡；它们是潜在空分类，不是已经证实的可见死链接。

新路由有两层：
1. 基础 `route()/show()` 按目标最近的 main panel 显示，找不到面板时退到guide（L7358–7360）。
2. `panelRoute()` 再处理旧route重定向、分类过滤、单元聚焦、owner、标题和“继续上次”（L9196–9213）。具体单元只保留自身；原五章first单元额外保留learn/feedback/review三段（L9188–9194）。

“有内容目标”不总是“单元聚焦目标”：资源目录仍能进入 `#pp-reading`、`#pp-listening`、`#pp-writing1`、`#pp-writing2`、`#pp-speaking` 以及38/8/12组case-bank外层，这些wrapper不等于catalog单元，`focusActivity` 得不到u便不聚焦。与分类卡直入单元的视图粒度不同（L5564、6865、6896–6897、9188–9194）。

旧 `#pp-background` 留在background面板内，现为“话题·海洋资源”链接外壳；真实 `#pr-background-fisheries` 已归入practice-reading，且已登记为阅读练习（L473、6865、9025）。不能把空壳与题目混为一谈，不能误报为题目没有登记。

**隐藏旧内容需与当前可见UI区分。** `#guide` 的旧“先从背景开始”首页、旧四科卡、旧今天列表；`#plan` 的旧8周安排，都在 `.la-hidden-legacy` 中（L5524、5550），CSS永久 `display:none!important`（L327、400）。这说明实现有历史叠加，但不能把这些旧文案全部报成用户现在看得到的重复页面。当前guide可见内容是daily-study-home与返回学习。

## 链接与完整性核验

- 检查正式HTML内1725个静态 `href=#...`：目标ID全部存在；没有重复ID。
- 检查1607个本地相对文件链接（去query/hash并解码路径）：文件均存在。此结论只限正式册本地资源，不代表公网全可用。
- 每日catalog中的 target/primerTarget 全部有真实ID。
- 没有发现“可见静态链接指到永久la-hidden-legacy内部”的情况。
- 有路由分类/上下文退化及潜在空分类，详见上文；不能把它们笼统记成404或缺文件。
- 工作区 `learning-adjust.js` 与正式内嵌脚本并不逐字一致：正式版本额外包含可见性判断、进度缓存/分批绘制、workspace/development宽版与改名等最新增量。审计结论以正式HTML内嵌脚本为准；不应用旧维护脚本直接覆盖。

## 完整 main panel 清单

以下owner为DOM的 `data-la-owner`。具体catalog单元路由会优先使用unit.mode，因此 `#pr-vocabulary-tourism` 是重要例外。

| Panel route | DOM owner | 标题 | 正式HTML行 |
|---|---|---|---:|
| #background | study | 共用背景 | 473 |
| #vocabulary | study | 词汇 | 473 |
| #guide | study | 直接开始学习 | 5524 |
| #plan | workspace | 今天选的内容 | 5550 |
| #records | workspace | 学习记录与备份 | 5550 |
| #library | workspace | 原始资料 | 5564 |
| #reading | study | 阅读 | 5596 |
| #writing1 | study | 写作 · Task 1 | 5801 |
| #writing2 | study | 写作 · Task 2 | 5982 |
| #listening | study | 听力 | 6136 |
| #speaking | study | 口语 | 6448 |
| #materials | workspace | 我的资料 | 6568 |
| #course-window | study | 我的定制课程 | 6581 |
| #writing-workbench | workspace | 写作工作台 | 6581 |
| #study | study | 学习 | 6734 |
| #practice | practice | 练习 | 6734 |
| #tests | tests | 测试 | 6734 |
| #workspace | workspace | 学习工作台 | 6734 |
| #development | development | 开发工作台 | 6735 |
| #phrases | study | 短语 | 6742 |
| #practice-reading | practice | 阅读练习 | 6865 |
| #practice-listening | practice | 听力练习 | 6896 |
| #practice-writing1 | practice | 写作 · Task 1练习 | 6897 |
| #practice-writing2 | practice | 写作 · Task 2练习 | 6897 |
| #practice-speaking | practice | 口语练习 | 6897 |
| #practice-phrases | practice | 短语练习 | 6897 |
| #test-listening | tests | 听力整科测试 | 6897 |
| #test-reading | tests | 阅读整科测试 | 7148 |
| #test-writing | tests | 写作整科测试 | 7149 |
| #test-speaking | tests | 口语整科测试 | 7150 |
| #learning-projects | study | 学习项目 | 7214 |
| #my-vocabulary-materials | study | 我的词汇资料 | 7214 |
| #my-topic-materials | study | 我的话题资料 | 7214 |

## 待浏览器探针核对的最小场景

1. 从工作台分别开单词表、句子本、写作工作台，看顶栏归属与返回目标。
2. 学习卡加入今天后打开plan，再打开guide，核对两份安排是否有明确区别；不使用真实个人记录。
3. 分别打开pp-vocabulary与pr-vocabulary-tourism，核对侧栏高亮、页头和返回路。
4. 直接开始选择共用背景，核对topic-education页头是否显示写作Task2。
5. records中Task1/Task2进入章节，核对是否仅回到写作分类选择。
6. library进入pp-reading或case-bank，与目录卡直达具体单元比较页面范围；确认是否出现大面板展开或定位不清。

本报告没有提出新的导航设计或运行修改；先完成当前结构与实际打开结果的对照，再由主任务汇总。
