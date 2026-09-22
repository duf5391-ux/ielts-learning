# cleaned-luna-20260921：阅读低置信纯精读小批

本包从 downloads/jiufen-jijing-20260921/reading-slices-index.json 逐项核对，并以对应的 reading-slices/ 片段及 materials/、text/ 原件保存段落和相邻上下文。每个单元只有一个可定位的原文段，稳定 ID 形如 jiufen-close-<sourceId>-v1；原材料、文字版和切片 HTML 的 SHA-256 均写入 package.json。

## 选择与正式覆盖核对

| sourceId | 标题 | 选段 | 主题 | 难度 | 可复用用途 |
|---|---|---|---|---:|---|
| 2017137445982277634 | The Voynich Manuscript | C（切片 p4-4） | 语言与传播 | 4/5 | 语言与密码话题资料；人工语言、证据与观点归属精读；词块和长句 |
| 2017137445957111811 | Insect-inspired robots | C（切片 p5-5） | 科技与工程 | 4/5 | 仿生科技话题资料；过程关系、指代和并行信息结构；词块和长句 |
| 2017137445986471939 | Neanderthal Technology | D（切片 p5-5） | 历史与文明 | 4/5 | 考古证据话题资料；推测语气、证据链和复杂修饰结构；词块和长句 |

本地查重结果：3 个 sourceId 均未出现在根目录 authentic-reading*.json 的正式真题/样题源中，也未出现在当前 content-pipeline/intensive/reading-base.json、reading-cambridge.json、reading-official-gap-ai.json。它们在旧批 content-pipeline/batches/jijing-20260920/content-review/ 中存在题面审阅记录，因此本批将其视为“原料已有审阅、正式精读包未覆盖”的可复用内容，未将它们描述为从未出现的新原料。

## 可复用用途与状态

- proposed：三份均可作为阅读学习/资料入口，支持同段纯精读、词块收藏候选、长句与指代讲解、话题拓展。
- blocked（测试）：三份都没有本包独立编写的可作答测试，也没有独立核验的标准答案；不能把旧题面解析当作新测试依据，不能自动判分。
- ready（材料精读）：仅表示段落、相邻上下文、原件路径和解释字段齐全，仍需主集成器接入真实入口并做隔离数据验证；不等于已发布或公网可用。
- unknown（外部事实）：各段原作者所引研究/历史/技术说法未在本包外独立核实；解释严格使用“文中称、研究者认为、发掘者提出”等归属。

## 自查

- 3 个单元 ID 唯一且均为 jiufen-close-<sourceId>-v1。
- sourceSha256、文字版 SHA-256、切片 SHA-256 已从当前本地原件计算并写入包；未修改下载原件。
- 每个 originalParagraphs 只有一个完整连续段；precedingContext、followingContext 均存在且来自同一切片的“相邻上下文”。
- 词汇各 4 条，引用短语均可在对应原段连续找到；句子各 2 条，均为原段完整连续句，未混入题干、选项或来源解析。
- 解释不提供题号、选项、答案定位或解题方法；保留技术、历史与考古说法的作者/研究者归属及不确定性。
- 本批只新增 cleaned-luna-20260921/package.json 与 review.md；未改正式 HTML、下载文件、主架构候选、发布仓库或根 README。
