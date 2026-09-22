# Kimi 独立架构/数据质量审查 · 2026-09-21

范围：只读审查 `quality_contract_v1.json`、`content-tensor-20260921/`（validation、quality-audit、graph、build 脚本）、`CONTENT_ARCHITECTURE.md`、`COURSE_WINDOW.md`、`architecture-repair-20260921/build.py`、`reviewed-package.json`，并对 `ui-repair-20260921/baseline.html` 与 `architecture-repair-20260921/candidate.html` 做路由存在性抽查。未改动任何正式册、下载目录或发布产物。缺证处标 unknown，不补猜。

## 一、内容图与契约的真实逻辑缺口

已核实的好基础：1063 来源 ID 唯一、1060 条正文 SHA 一致、精确重复为零、1445 阅读切片连续覆盖通过、5002 活动全部带 status 与 exposureFamily、3 条已审精读在图中正确标记为 reviewed_unpublished 且难度字段符合契约（reason/assessor/version 齐全）。以下按严重度列缺口。

**P0-1 记录层整体缺席。** 用户要求的张量是「来源/片段/用途/入口/记录」，现图只有前四层，没有 Attempt/Exposure 节点，也没有任何 recordOwner 绑定。契约把 test 的门槛写成 "shared-material exposure check, separate attempt identity"，但图里没有任何可查询的曝光事件结构——测试条件实际无法执行。在发布任何测试类活动前，必须先定义最小曝光/作答记录契约（owner、键空间、内容版本引用、材料接触与答案接触分开），哪怕先复用拟议的 `ielts-pp-exposure-v1`。

**P0-2 曝光家族粒度过粗。** exposureFamily 一律为 `jiufen:<sourceId>`，1063 个家族一源一个。契约第 8 条要求「看过原文」与「看过本题答案」分开；一个听力来源含 10 题，源级家族会把任何一题的答案接触污染成全源已曝光。需要拆成两个通道：materialExposure（source/fragment 级）与 answerExposure（activity/question 级）。

**P0-3 活动无 contentVersion。** 5002 个活动节点该字段为 0；契约 identity 第一项就是它。节点上的 sourceVersion 只是原料 SHA，不能代替「活动渲染负载」的版本。没有它，「改题出新版本、旧答绑旧版」对所有派生活动不可执行。凡进入 published 的活动必须先补内容指纹。

**P1-4 入口「existing:true」是硬编码，构建器不断言。** 我本次手工核对：图中 10 个入口路由在 `ui-repair-20260921/baseline.html` 全部真实存在（含 study-writing1/2-list、practice-writing1/2-list），candidate.html 亦一致——当前声明属实，但脚本改路由名不会有任何报警。应在 build 脚本加一行对基线页 id 的断言。

**P1-5 派生物件无血缘边。** source 节点只挂 rawSha256；已存在的 text/md 与 slice 文件（reviewed-package 里有独立 SHA）在图中无节点、无 derived_from 边。派生物静默失配时无法定位。

**P1-6 双套 ID 词汇并存。** 图中 fragment ID 带 `fragment:` 前缀，reviewed-package 用裸 slice ID（`jiufen-reading-…-v1`），靠一次相等比较连接；activity ID 内嵌中文角色名，角色改名即键变。建议角色用稳定代码（topic/study/practice/test），ID 与显示名分离。

**P1-7 测试候选只有文字条件。** 679 个 conditional 活动的 scope、时限、评分依据均为散文，无可机检字段；679 个 needs_validation 活动有 questionCount 但无逐题核查清单身份。另：usageTensor 5001 条与活动节点 5002 差 1（已发布的旧题活动不在映射中），属一致性瑕疵。缺正文 3 条来源的具体 ID 本次未逐一列出，可按 `normalized-sources.json` 中 bodyAcquired=false 筛出——此项为 unknown 而非已排除。

## 二、同一原料能否转学习/练习/测试的判定

判定权在材料条件，不在置信度；置信度只决定处理顺序（听口先做题、阅读先精读、写作居中）。

- **话题资料**：可读片段＋上下文＋来源身份即可，机械条件，可以自动升为 prepared（1445 条已正确如此处理）。
- **学习**：必须有贴着原文引句写出的具体讲解。来源自带解析不能换标题充当精读；只能自动生成脚手架，正文须创作＋复核。3 条 reviewed_unpublished 是正例。
- **练习**：题面完整、媒体在位、可保存作答、反馈状态显式声明。可自动晋级的前提是逐题结构核查通过；在无独立答案依据时必须显示「参考解析未经独立核验」，禁止自动判分。
- **测试**：永远不允许自动转换。需要声明范围与条件、独立答案/评分依据、曝光检查通过、独立作答身份。当前 canonicalAnswerFields=0，故全批合格测试活动数为 0，679 个 conditional 应长期保持候选态。
- **不可自动转的硬停止**：blocked（74 条，题界/媒体缺失）、缺正文来源、任何 answerStatus 含糊的题。

## 三、1063 条的合理成本处理

分层推进，每层产出诚实的状态而非「已完成」：

1. **L0/L1 已完成**：获取＋哈希、结构机械核对、精确去重——近零边际成本覆盖全批，继续保持。
2. **L2 逐题完整性的自动核查清单**（题号连续、选项数、媒体引用存在、解析非空），输出逐题 pass/fail，作为练习晋级门槛。这是下一步性价比最高的工作。
3. **L3 分层语义抽查**：沿用现有 seed=20260921 分层抽样设计，把 28 条扩到每「科目×Part×正确率档」层至少若干条（约 5%）；按层估计缺陷率——缺陷率超阈值的层全审，低于阈值的层抽复查。报告「各层估计残留缺陷率」，永远不写「整批已审」。
4. **近似去重**只做人工提示（标题＋内容指纹相似），不自动合并，符合架构文档第 8 条。
5. **复用与曝光联动**：existing_by_source 命中的已发布题必须经曝光家族关联，避免旧题当新题再发。
6. **发布按切片进行**：一次一个科目×Part 层，隔离浏览器验证 route→作答→保存→退出→续学后才标 published。

## 四、难度与参考置信度如何可解释地形成

- **参考置信度**：保持序数政策标签（高/中/低）＋一句依据，原样展示。禁止换算成命中概率、期望分数或答案可靠性。
- **难度**：维持编辑序数 1–5＋reason/assessor/version（契约与 reviewed-package 均已合规）。可解释化路径：先写一份特征 rubric（信息密度、抽象概念数、句法复杂度、听力语速口音、题型），在 20–30 条校准集上双人独立评估并如实记录一致程度，再放量。评估只引用可观察特征，不引用来源正确率。
- **当前不能做的统计估计**：IRT/项目反应难度（无作答数据）；sourceAccuracy 的置信区间（样本量 null）；正确率→难度的校准；命中概率的贝叶斯更新；把共享材料的题当独立样本的任何汇总。这些都已在 quality-audit 的 statisticalLimits 正确声明，继续保持。
- **以后可以做的**：站内积累带曝光控制的首答正误后，可按活动＋版本算描述性 p 值及区间；没有模型与样本量前仍不是 IRT。

## 五、多用途实例：观测与设计假设的边界

来源 `2062075620860411906`「Canadian Maple Syrup」（听力，政策高置信）：

- **观测（文件可证）**：原料 SHA 校验通过；1 个 part、10 个题目对象；10 题均带来源解析；标准答案字段 0；词数 880；sourceAccuracy=64.61 且样本量 null；图中 contains/splits_into 边由原始文件结构直接派生；三个活动状态分别为 needs_validation（练习）、needs_design（学习）、conditional（测试候选）；入口路由在基线页真实存在。
- **设计假设（非观测）**：它能成为练习——取决于逐题核查；同一题面能做学习而不泄露答案——需设计分离；它有一天能进测试——目前无独立答案依据，应视为当前不可达；难度为 null（待评估）；「高置信」只是用户策略序数。
- **边的性质**：contains、splits_into 是观测；supports_use 是受 status 约束的设计映射；entry_mapping 是计划，不是发布。

## 结论

图的骨架（身份唯一、哈希核对、状态分层、如实声明限制）是健康的；真正的 P0 缺口集中在记录层缺席、曝光粒度和活动版本三件事——它们不补，测试与旧答保护承诺都无法兑现。建议按 P0-1/2/3 → P1-4~7 → L2 逐题核查 → L3 分层抽查的顺序增量推进，全部可落在现有静态站与批次包结构内，不需要新基础设施。
