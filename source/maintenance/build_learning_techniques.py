"""Author the Chinese technique lessons; examples and figures are new teaching exercises."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
units=[]
def unit(key,section,title,minutes,purpose,steps,example,explanation,pitfalls,practice,answer,transfer,sources,figure=None):
    units.append(dict(id='tech-'+key,anchor=section+'-tech-'+key,section=section,title=title,minutes=minutes,purpose=purpose,steps=steps,example_md=example,explanation=explanation,pitfalls=pitfalls,practice_md=practice,answer_md=answer,transfer=transfer,source_ids=sources,figure=figure))

unit('read-chart','writing1','读图起手：对象、单位、时间与比较口径',12,
'看见折线、柱状或饼图时，先读清图在衡量什么，再选语言。适用于 Academic Writing Task 1。',
['用一句中文回答：谁／什么指标、在哪里、哪个时间段。标题给主题，横纵轴和图例给变量。',
'核对单位与基数：人数、百分比、吨还是千吨？百分比的分母是什么群体？不同图的单位或分母不同，先分别理解。',
'判断是跨时间变化还是同一时点比较。前者可以写 rose / fell；后者通常写 higher / lower，不能把两个类别误读为先后。',
'沿每条线读起点、终点、最高最低及重要转折，再横向比较类别。仅有离散年份时，不推断点与点之间的精确路径。',
'写前留下三个笔记：一条整体特征、一个主要对比、两组支持数据。笔记用于组织思路，成文仍用完整段落。'],
'''**通勤方式占比（%）**：城市 L 的通勤者，每年各类别合计 100%。

| 年份 | 公共交通 | 汽车 | 骑行 |
|---|---:|---:|---:|
| 2010 | 30 | 60 | 10 |
| 2015 | 35 | 50 | 15 |
| 2020 | 40 | 40 | 20 |
| 2025 | 45 | 30 | 25 |

The chart compares the proportions of commuters using three forms of transport in city L between 2010 and 2025.''',
'主语是通勤者的比例，不是车辆数，也不是出行总次数。2020 年公共交通和汽车相等；到 2025 年公共交通最高。数据只显示占比，不能据此断言骑行总人数增加了多少。',
['看到线就写“波动”：图中公共交通四个观察点持续上升，没有反复升降。','把百分比写成人数，或给没有原因的图补“因为票价下降”。','把 2020 年的相等写成全程相同。'],
'''纠正两句话，并说明各自错在哪里：

1. The number of cyclists was 25 in 2025.
2. Public transport increased from 30% to 45% because fares became cheaper.''',
'''1. **Cycling accounted for 25% of commuters in 2025.** 25 是百分比；图没有给出骑行人数。
2. **The share of commuters using public transport rose from 30% in 2010 to 45% in 2025.** 补清指标与时间，删除图中未给出的票价原因。

可接受同义写法；检查对象、单位与事实是否保持一致。''',
'换成一个只有 2025 年数据的柱状图，写一句类别比较；不要使用 rose 或 fell。',
['ielts-writing','idp-focus'], 'commuting')

unit('overview','writing1','从读图到 Overview：抓整体、分组、选证据',15,
'解决“每个数字都写了，却没有重点”。把概览与细节的工作分清，再组织段落。',
['先遮住细小数字，用中文概括总体方向、主导类别或明显例外。概览要让读者知道这张图最值得注意的关系。',
'回图验证概览：是否漏了重要类别？“全部上涨”“始终最高”需要每个相关点都支持。',
'给细节分组：相同走势放一起，反向走势另组；静态图可按高低类别分组。分组应服务比较，不强求固定两组。',
'每条重要判断后选有代表性的数字，包括起终点、交叉点或峰值；不必逐格抄写。',
'多图题先概括各图，再找可比较的共同对象。百分比与总量可以并列描述，不能不核对分母就直接相减。'],
'''看本单元通勤图：2010 → 2025 年，公共交通 30% → 45%，汽车 60% → 30%，骑行 10% → 25%。

**概览**：Overall, public transport and cycling gained a larger share of commuters, while car use declined. Public transport was the largest category by the end of the period.

**细节分组笔记**：
- 汽车：60% → 30%，由最高降至第二。
- 两种增长方式：公共交通 30% → 45%；骑行 10% → 25%；两者均增加 15 个百分点。

**比较句**：The shares for public transport and cycling each rose by 15 percentage points, reaching 45% and 25% respectively.''',
'概览选择变化方向和终点排名；比较句再用数字支撑。respectively 要和前面两个类别的顺序对应。这是一个可用组织方式，段数、概览位置和句数都不必机械固定。',
['把 overview 写成“The chart shows some changes”，没有实际特征。','概览列满数字，细节段再次照抄，却没有分组比较。','只挑最大值而漏掉反向趋势；混合图只描述其中一张。'],
'''另一个练习表：A 服务用户 2015 年 20 千、2025 年 40 千；B 为 30 千、60 千；C 为 50 千、45 千。

1. 写一句 overview。
2. A 与 B 是“增加量相同”还是“增长比例相同”？写一句比较。
3. “All three services became more popular.” 能成立吗？''',
'''1. **Overall, user numbers increased for A and B but fell slightly for C, with B becoming the largest service in 2025.** 同时涵盖方向和排名变化。
2. **Both A and B doubled their user numbers, although B recorded a larger absolute increase.** A 增 20 千，B 增 30 千；两者均增长 100%，绝对增加量不同。
3. 不能：C 从 50 千降至 45 千。且 popular 最好落实为已知的 user numbers，避免扩大含义。''',
'在下一张图旁各写一行“整体关系”和“支持数字”；写完检查每个数字是否服务一个判断。',
['ielts-writing-resources','idp-focus'], 'commuting')

unit('precision','writing1','数据表达：百分点、倍数、近似值与静态比较',12,
'用准确的短句表达比较，避免高级词掩盖单位和算术错误。',
['先写最朴素的数值关系：A 从什么到什么，或同一年 A 比 B 高多少。确认无误再改写。',
'比例相减得到百分点：20% → 30% 是增加 10 percentage points；相对增长为 (30−20)÷20 = 50%。',
'数量翻倍用 doubled 或 twice as many / much as。避免含义可能模糊的“two times higher”。',
'近似值用 about / approximately；just under 表示略低，just over 表示略高。没有精确标签时，不编小数。',
'复核 from、to、by：from 起点，to 终点，by 变化量。静态比较使用 higher / lower / accounted for，不暗示时间变化。'],
'''**同一年的图书馆借阅构成**：纸书 60%，电子书 25%，有声书 15%。

Printed books accounted for 60% of loans, compared with 25% for e-books.

**跨年份变化**：会员数 2,000 → 3,000。

Membership rose by 1,000 to 3,000. / Membership increased by 50%.

**比例变化**：电子书占比 20% → 30%。

The share of e-book loans increased by 10 percentage points.''',
'同一年三类借阅构成合计 100%，可以比较占比；不能说有声书“跌至”15%。20% 到 30% 的百分点差与相对增幅不是同一概念，写 from ... to ... 也能清楚避免混淆。',
['把 by 30% 当成 to 30%。','把份额上涨理解为人数必然上涨：总基数可能变化。','用 dramatically 描述每个小变化；优先给读者具体数值。'],
'''1. 某比例从 40% 变成 50%，分别计算百分点变化与相对增幅。
2. 某年 A 有 80 辆车，B 有 40 辆。写一句无歧义倍数比较。
3. 柱高略低于 70，缺少精确标注。选择：a) 69.37；b) just under 70。''',
'''1. **增加 10 个百分点；相对增长 25%。** (50−40)÷40 = 0.25。
2. **A had twice as many vehicles as B.** 80÷40 = 2，as many 对应可数复数 vehicles。
3. **b)** 图的精度不足以支持 69.37。''',
'从自己的一段 Task 1 中找出所有数字，逐一对上原图的单位、年份和类别；只改最先发现的一处。',
['idp-focus','ielts-writing'])

unit('process','writing1','流程图专项：起终点、分支与主被动',15,
'把图中的箭头变成清楚的过程描述，区分先后、并行、条件与循环。',
['找到输入、输出和箭头方向，先判断是有终点的流程还是回到起点的循环。',
'逐个框写“对象＋动作”。先看箭头关系，再考虑合并阶段；不要为了凑固定阶段数把分支写成连续步骤。',
'概览交代过程的大方向和主要阶段；若阶段边界明确，可说明数量，但数量不是必须背出的句式。',
'物品接受处理时常用 is sorted / is packed；对象自己变化时可用 water evaporates。不要把每个动词都强改为被动。',
'细节段按图的关系展开：after / once 表先后，while 可表并行，if 表条件。只写图中展示的工序和条件。'],
'''**纸张回收流程**：废纸收集 → 分类 → 分为“可用纸”和“不适用材料”；可用纸 → 制浆 → 压制、干燥 → 再生纸，不适用材料 → 移出流程。

Overall, waste paper is collected and sorted before the usable material is processed into recycled paper. Unsuitable material is removed after sorting.

After the paper is sorted, unsuitable material is removed. The usable paper is then turned into pulp, which is pressed and dried.''',
'分类后有两个去向，不是“不适用材料也进入制浆”。is removed 描述接受处理，which 指向 pulp。概览交代输入、输出和分支，没有添加温度、成本或环保效果。',
['只数框，不读箭头，把两条分支强行串起来。','擅自加入图中没有的加热温度、处理时间或机器名称。','The water is evaporated 与 water evaporates 一概互换：要看图是在描述外力处理还是自然变化。'],
'''1. 纠正：After unsuitable material is removed, it is turned into pulp.
2. 给“水蒸发 → 云形成 → 降水 → 水回到湖泊”的循环写一句概览。
3. 本单元回收图能否写“the process takes two days”？''',
'''1. **After unsuitable material is removed, the usable paper is turned into pulp.** 原句 it 紧接 unsuitable material，指代造成事实错误。
2. **Overall, water moves through a cycle of evaporation, cloud formation and precipitation before returning to the lake.** 准确表达回到起点。
3. 不能。图中没有时长，不能用常识补上。''',
'选一个流程图，只用箭头和动词先口述一遍；每遇分支就说清哪一部分进入哪条路径。',
['idp-focus','ielts-writing-resources'], 'process')

unit('maps','writing1','地图专项：位置锚点、变化分类与规划时态',15,
'比较地图时围绕“哪里发生了什么变化”组织语言，处理保留、迁移、替换与扩建。',
['先读年份及图例。区分两个已发生的年份与未来规划，规划不能写成已经完成。',
'选不变锚点，例如入口、主路、河流；核对北箭头。无指北标记时可用 left / right 或 next to 等相对位置。',
'把变化分为保留、增加、移除、替换、迁移和扩建。没有“迁移”证据时，不仅凭两个相似名称就认定同一建筑搬走。',
'概览概括整体布局或功能的主要改变；细节按区域、路线或变化类型分组，并补充重要的不变设施。',
'用具体动词及位置：was replaced by、was added to the east of、remained unchanged。不要推测开发原因或擅自评价“更好”。'],
'''**社区中心平面图**：2010 年，北侧依次是阅览室、办公室；南侧是花园与入口。2025 年，北侧阅览室位置改为咖啡区，办公室保留；南侧花园改为学习室，入口保留。

Overall, the centre gained a café and a study room, while the office and entrance remained in the same positions.

The reading room in the north-west was replaced by a café. A study room was built on the site of the former garden in the south-west.''',
'先看同一位置前后的用途，再使用 replaced。这里有北箭头，所以 north-west 有依据。图只显示用途改变，不能推出办公人数增加或访客更满意。',
['把“被替换”写反：A was replaced by B 表示 B 成为新设施。','把 planned / proposed 地图统一写成一般过去时。','逐图各写一遍但不连接同一位置的前后变化。'],
'''1. 2030 年规划拟把停车场改为运动场；今天仍是停车场。改写：The car park was replaced by a sports court in 2030.
2. 写一句本图中未改变的设施。
3. 本图能否推出“The centre became more popular”？''',
'''1. **The car park is planned to be replaced by a sports court in 2030.** 这是规划，不是已发生的事实。
2. **The office in the north-east remained unchanged.** 位置与用途均保持一致；入口也可作答。
3. 不能。图中没有人流或满意度数据。''',
'给下一组地图每个变化点标一个动词，再按区域口述；最后检查是否把“新建”与“迁移”混淆。',
['idp-focus','ielts-writing-resources'], 'maps')

unit('locate','reading','阅读起手：略读地图、扫读定位、精读证据',12,
'解决全文逐词翻译和只找相同词两个常见问题，让不同读法各司其职。',
['先读题目指令与任务目标：找主旨、找细节，还是判断观点？据此决定阅读深度。',
'略读标题与各段，给每段记一个短功能标签，例如“问题”“试验方法”“结果限制”。首尾句常有线索，但要看中间是否转折。',
'用题干里的名称、年份、独特术语扫读定位；普通词要准备同义表达和词形变化，不只寻找原词。',
'找到候选位置后放慢速度，读完整句及必要的前后句；追清代词、比较对象、否定和条件。',
'选答案后指出“题目哪一部分被哪条证据支持”。定位只能找到候选段，精读才完成判断。'],
'''**A** A city library extended its evening opening hours in March. Managers wanted to make the building easier to use after work.

**B** A survey in June found that evening visits had risen. However, weekend attendance had not changed.

**C** Staff warned that the survey covered only one branch, so its findings might not apply to the whole city.

题目：Which paragraph mentions a limitation of the evidence?''',
'段落地图：A 改变及目的；B 结果；C 限制。limitation 不在原文，但 only one branch 和 might not apply 表示证据适用范围有限，答案是 C。不是见到 survey 就选 B。',
['每个生词都停下来查，导致忘记整段关系。','看见同义词就立即答题，忽略后面的 however。','把一套“先读题／先读文”变成所有题型唯一程序；应看自己的理解负担与任务。'],
'''1. 哪段给出改变开放时间的目的？
2. 判断：The longer opening hours increased weekend attendance.（TRUE / FALSE / NOT GIVEN）
3. 写出第 2 题必须精读的短句。''',
'''1. **A**。wanted to ... 表达目的。
2. **FALSE**。B 明确说周末到访人数没有变化，与题干“增加”相反。
3. **weekend attendance had not changed**。不能把 evening visits 的增长移用到周末。''',
'下一篇先给每段写不超过一句话的功能标签，再做三题；复盘哪一题卡在定位、哪一题卡在精读。',
['bc-reading-lessons','ielts-reading'])

unit('judgement','reading','判断题专项：TRUE／FALSE／NOT GIVEN 与观点归属',15,
'用证据关系区分相反与缺失，防止常识、绝对词和人物观点干扰。',
['先确认答题体系：信息题用 TRUE / FALSE / NOT GIVEN；作者观点题用 YES / NO / NOT GIVEN，照题目要求填写。',
'把陈述拆成主体、动作、时间、范围与比较条件。only、all、some、before、more than 都可能影响整体真假。',
'找到涉及同一主体的相关段落，读前后句。作者转述某人的话，不自动等于作者赞成。',
'原文支持完整陈述才判 TRUE / YES；明确与其中的关键主张矛盾判 FALSE / NO；缺少所需信息、无法支持或推翻则判 NOT GIVEN。',
'对 NOT GIVEN 写出“缺的是哪一项关系”，而非仅写“没找到词”。对 FALSE 写出双方相反的内容。'],
'''The museum opened in 2012. Entry is free for children under twelve. Adult visitors pay a fee. The director hopes to extend free entry to students next year.

- The museum opened before 2015. → **TRUE**：2012 早于 2015。
- All visitors can enter without paying. → **FALSE**：成人需要付费。
- Students currently pay less than other adults. → **NOT GIVEN**：只说了未来希望，未比较现行学生票与成人票。''',
'绝对词只是检查线索，不自动意味着 FALSE。All visitors 若得到原文完整支持也可为 TRUE。未说明的信息可能与现实常识一致，仍不能靠常识作答。',
['原文没有逐字出现题干，就选 NOT GIVEN。','原文只说 some 就认定不是 all：some 本身不一定排除 all，必须看有无明确反证。','把研究人员、批评者与作者的立场混为一谈。'],
'''原文：Some planners claim that taller buildings always improve city life. I disagree: in areas with poor transport, they can make congestion worse.

按作者观点回答 YES / NO / NOT GIVEN：
1. Taller buildings always improve city life.
2. Taller buildings may worsen traffic in some places.
3. Improving public transport is cheaper than limiting building height.''',
'''1. **NO**。作者 I disagree 明确反对，并给出反例。
2. **YES**。can make congestion worse 与 may worsen traffic 对应，in areas with poor transport 限定了范围。
3. **NOT GIVEN**。没有比较两种措施的成本。此处题型要求 YES / NO，不能写 TRUE / FALSE。''',
'选一道错题，写三行：题干主张、原文证据、相同／相反／缺失的关系。只背答案无法检查推理。',
['ielts-reading','bc-reading-lessons'])

unit('headings','reading','标题匹配：段落主旨与例子分开',12,
'从段落在做什么出发选标题，避免被同词与单个例子吸引。',
['略读整段，用自己的话写“主题＋本段关于它的主要意思”。先形成短标签，再比较标题。',
'识别段落功能：提出问题、解释原因、比较方案、评价结果。标题不仅要主题相同，还要涵盖这一功能。',
'留意 but / however / instead 等转折：段首可能只提供背景，中后段才落到作者重点。',
'两项难分时逐一检查范围：哪一个只覆盖一个例子？哪一个扩大到全文或加入未说的因果？',
'核对题目要求的段落与标题编号。不要重复使用同一标题；有些标题会闲置。'],
'''Early roof gardens were praised for their appearance. Their main value in dense cities, however, is now seen as environmental. Plants can reduce roof temperatures, and the soil can hold some rainwater. These effects help buildings manage heat and runoff.

标题：
i. The visual design of roof gardens
ii. Environmental benefits of roof gardens
iii. The cost of constructing roof gardens

答案：**ii**。''',
'appearance 是背景；however 后面明确转向环境作用，降温和蓄水都是支撑例子。i 只对应首句，不概括整段；iii 没有成本信息。主旨句可能在开头、结尾或段中，不能只读第一句。',
['标题里有原文词就选，忽略该词在段落只是一个例子。','把解释“为什么”误配成说明“如何操作”。','先选标题再强行把所有句子解释成支持它。'],
'''The first repair café attracted few visitors. Organisers then moved it next to the weekly market and advertised short demonstrations. Attendance increased within a month, suggesting that location and visibility mattered more than the original team had expected.

选最合适标题：
i. Why repair cafés use expensive tools
ii. Changes that improved participation
iii. The history of the weekly market

再用中文写一句段落主旨。''',
'''**ii**。本段讲搬位置和增加展示后，参与人数提高。可概括为“提升可见度与调整位置改善了参与情况”。

i 的工具成本没有出现；iii 的 market 是新位置的背景，不是本段在讲市场历史。''',
'下次遇两项犹豫时，写出每个标题覆盖了哪几句；只有一句例子支持的选项需要警惕。',
['cambridge-headings','bc-reading-lessons'])

unit('matching','reading','信息与人物匹配：找细节、追踪归属',15,
'分清“哪段含这个信息”与“谁提出这个观点”，建立能重复使用的定位笔记。',
['信息匹配先圈任务类型：例子、原因、对比、时间变化或研究限制。它找具体信息，不要求是整段主旨。',
'给段落记简短内容索引；一道题未定位时先保留候选，后续读段落时再顺带验证。不要假设题号总按原文顺序。',
'人物／特征匹配先定位姓名或类别，再找其观点。圈 said / argued / disagreed / supported 以及 he / she / they 的所指。',
'区分“被某人提到”与“被某人赞成”：同一句可能引用别人的主张后反驳。',
'核对选项能否重复：只有指令允许时才复用；每题仍需独立证据，不按配对数量猜剩余答案。'],
'''**A** Lin argued that shorter bus routes would be easier to run reliably. Patel questioned this view, warning that passengers might need to change buses more often.

**B** Morgan supported Patel's concern but suggested testing the plan on one route before rejecting it. Lin agreed that a trial would be useful.

人物：L = Lin；P = Patel；M = Morgan。可重复使用。

谁最先提出换乘次数可能增加？→ **P**。谁建议先在一条线路上试行？→ **M**。''',
'Patel 的观点在 A 中紧接 Lin，却由 Patel 自己提出。B 中 supported Patel’s concern 表示 Morgan 支持这一担忧，后半句才是 Morgan 的试行建议。Lin 赞同试行，不等于最先提出它。',
['定位到姓名后，只读最近一个名词。','信息匹配选段落主旨最接近的项，却没找到要求的具体例子。','把所有匹配都当成一对一；忽略“可重复”指令。'],
'''用以上 A / B 两段作答（段落可重复）：
1. 哪段明确描述乘客可能需要增加换乘次数这一不利影响？
2. 哪段建议进行小范围试验？

再答人物题：谁既支持他人的担忧，又提出试验方案？L / P / M。''',
'''1. **A**：换乘可能增多是方案的不利影响。
2. **B**：testing the plan on one route 是小范围试验。
3. **M**：Morgan 同时做了 supported ... 和 suggested ... 两件事，需核对整个陈述。''',
'下一次把“人物—主张—态度”写成三列表，只摘一行关键词，然后回原文确认代词。',
['ielts-reading','bc-reading-lessons'])

unit('completion','reading','填空专项：字数、词性、原词与语义',12,
'适用于句子、摘要、笔记、表格及流程填空；按各题指令控制答案形式。',
['先确定答案来自原文还是给定词库，允许多少词、是否允许数字。每个空都重新核对限制。',
'读空格左右，预测语法位置与语义类别，例如可数名词、材料名或动作；预测只缩小范围，不能凭语法猜答案。',
'找整句意思的同义表达。摘要可能重组原文顺序；句子填空通常按原文顺序，不能把该规则套到所有填空。',
'从规定位置取词，保留需要的形式；原文取词题不要自行换成同义词或增添冠词。词库题按指令写词或字母。',
'把答案放回题目检查：语义、搭配、单复数、拼写、字数都成立吗？多词短语不等于可以随意删到只剩核心词。'],
'''The boxes were lined with recycled paper to protect the glass bottles. Each shipment contained twelve boxes.

Choose **NO MORE THAN TWO WORDS** from the passage for each answer.

1. The lining material was ______.
2. The containers held ______.

答案：1 **recycled paper**；2 **glass bottles**。''',
'lining material 与 lined with 对应；containers 在题中指 boxes。recycled paper 是完整材料名，glass bottles 给出具体内容物。不能写 a recycled paper，也不能把 bottles 改成单数 bottle。',
['字数限制允许两个词就每空硬填两个；有时一个词已经足够。','把 NO MORE THAN TWO WORDS 当成“两个词再加一个数字”，数字是否允许需看完整指令。','按语法猜出正确概念，却写了原文没有的同义词。'],
'''原文：The sensor is powered by solar energy. It sends readings every six hours. Its outer case is made of stainless steel.

Choose **NO MORE THAN TWO WORDS** from the passage for each answer.
1. Power source: ______
2. Interval between transmissions: ______
3. Case material: ______''',
'''1. **solar energy**：is powered by 表示能源来源。
2. **six hours**：两词；every 已由 Interval between 的题意表达，无须再抄。
3. **stainless steel**：made of 对应材料。

every six hours 是三词，超过限制；只写 six 会丢失时长单位。''',
'给下一次三个填空分别写一个检查标签：“字数”“原词”“语法”；错题记录哪一步没过。',
['ielts-reading','bc-reading-lessons'])

unit('diagram','reading','阅读图示标注：把原文位置关系落到图上',15,
'Reading diagram-label completion 是依据阅读文章给图中部件填标签；这里不需要写 Task 1 图表报告。',
['先看指令、图的标题、已有标签和箭头端点：每个空究竟指向容器、管道、材料还是出口？',
'用已有标签和部件功能定位原文相关段落；图能帮助理解结构，答案仍需由文字提供。',
'追踪位置与连接词：above / below、inside / outside、at the base、leads to、passes through。结合箭头与指代重建路径。',
'逐一把文字描述对应到具体部件。空号不一定与原文顺序一致，不要靠从上到下顺序猜。',
'按字数限制填原词或按题给选项作答，再查拼写与箭头落点。认识装置不代表可以用课外名称替代文章用词。'],
'''**Rain collector**

Rainwater enters a wide funnel at the top. It then passes through a mesh filter, which removes leaves. Below the filter is a storage tank. A narrow outlet pipe carries water from the base of the tank to a measuring cup.

看本单元示意图。引线指向各部件；measuring cup 已给出，不需要填写。

Choose **NO MORE THAN TWO WORDS** from the passage for each answer.

1. 图顶端漏斗形部件：______
2. 漏斗下方横向网层：______
3. 网层下方储水部件：______
4. 储水部件底部通向杯子的管道：______''',
'funnel 是顶部入口，mesh filter 对应去除树叶的网层，storage tank 位于它下面，outlet pipe 从底部通向量杯。below 和 from the base of ... to ... 同时提供位置与连接证据。先自行尝试，再展开答案。',
['根据常识把 funnel 写成 roof，把 mesh filter 换成文章没有的 screen。','把第 4 空指向的管道误看成已经标出的量杯。','以为图号顺序保证等于原文顺序；必须核对描述与箭头。'],
'''先完成上方 1–4，再答两个检查问题：

5. “Which part removes leaves?” 答案是什么？
6. 若第 4 空写成 narrow outlet pipe，为什么不合要求？''',
'''1. **funnel**；2. **mesh filter**；3. **storage tank**；4. **outlet pipe**。

1 对应 at the top；2 对应 removes leaves；3 对应 Below the filter；4 对应 from the base ... to a measuring cup。

5. **mesh filter**。which 指向它，功能也能帮助定位。
6. **narrow outlet pipe** 有三个词，超过两词限制；当前短文也没有 narrow 这个修饰词。填写原文的 **outlet pipe**，既对应管道，又符合两词上限。''',
'找下一道图示标注，先指着每个箭头说“我要找什么”，再到文中圈一条位置关系；两者对不上就继续核对。',
['cambridge-diagram','ielts-reading'], 'collector')

unit('choices-review','reading','选择题与限时复盘：判断整句、控制卡题',15,
'排除“词相同但意思不对”的选项，并把错题归因转成下一次练习动作。',
['读清问的是原因、目的、结果还是作者态度，并检查选一个还是多个答案。',
'定位后先用自己的话回答问题，再比较选项；检查每个选项的主体、范围、时间和因果。',
'给干扰项标理由：与原文矛盾、只说对一半、主题有关但未回答问题、原文未提。不能只写“感觉不对”。',
'限时训练可先给三篇各约 18 分钟、留约 6 分钟检查，按篇幅与强弱调整；这是练习起点，不是每题强制秒数。卡住且没有新证据时先标记后回看。',
'复盘先不看答案重读定位段，再核对解释。记录错误属于找不到位置、同义替换、逻辑范围、题意或拼写；下一次只选一类重点修。'],
'''The trial reduced energy use in the test building. Because the study lasted only two weeks, the researchers said it was too early to estimate annual savings.

Why did the researchers avoid estimating annual savings?

A. Energy use increased during the trial.
B. The observation period was too short.
C. The building was larger than expected.
D. The equipment was too expensive.

答案：**B**。''',
'because 引出原因，only two weeks 与 observation period was too short 对应。A 与 reduced 相反；C、D 都没提。研究取得短期结果，与不能可靠估计年度节省量可以同时成立。',
['选项提到 energy 就认为答到题；先看问题问什么关系。','把所有阅读题都当顺序题：不同题型的顺序规律不同。','重复做熟题后正确率升高，就认为陌生文章已经同等提高。'],
'''原文：Visitors preferred the audio guide because it let them explore at their own pace. Some still asked staff for directions.

1. Why was the audio guide preferred?
A. It was free. B. It allowed flexible pacing. C. It replaced all staff. D. It contained more facts.

2. “No visitor needed staff assistance.” 与原文是什么关系？
3. 如果你选了 C，下次做选择题要增加哪一步？''',
'''1. **B**：at their own pace 表示按自己的节奏。
2. **相反**：some ... asked staff for directions 明确存在仍需帮助的人。
3. 检查选项的范围词 all，以及后句是否构成反例。不能由“喜欢导览”扩大成“不再需要任何员工”。

阅读整场为 60 分钟、40 题；最后检查要覆盖未答项、选项数量及填空限制。分段耗时与调整方法请记在笔记中，下一次用未看过的短文验证。''',
'复盘后另找一段未见短文，用相同技巧做两题；把“熟题修正”和“新材料应用”分别记下。',
['ielts-reading','bc-reading-lessons'])

assert len(units)==12
worked={}
for filename in ['writing-worked-answers.json','reading-worked-answers.json']:
    path=HERE/filename
    assert path.is_file(), f'Missing worked answers: {filename}'
    additions=json.loads(path.read_text(encoding='utf8'))
    assert not (set(worked)&set(additions)), 'Duplicate worked examples'
    worked.update(additions)
assert set(worked)=={u['id'] for u in units}, 'Each technique needs its worked example'
for u in units:
    sample=worked[u['id']]
    assert sample['prompt_md'] and sample['answer_md'] and sample['explanations']
    u['worked_example']=sample
(HERE/'learning-techniques.json').write_text(json.dumps({'date':'2026-09-16','units':units},ensure_ascii=False,indent=2),encoding='utf8')
print('Wrote',len(units),'learning technique units')
