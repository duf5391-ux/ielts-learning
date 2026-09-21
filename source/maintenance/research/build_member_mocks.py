import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATE = '2026-09-19'
S = {}
def source(id, title, url, kind, note, published=None):
    S[id] = dict(id=id, title=title, url=url, evidence_type=kind, accessed=DATE, note=note, published=published)
source('MM01','TestGlider IELTS 专用入口','https://www.testglider.com/ielts/en','官方当前入口/搜索可见导航','IELTS独立路径；未进入登录后的试卷。直接抓取为空，导航由官方页面搜索快照可见。')
source('MM02','TestGlider IELTS 使用教程及成绩/学习页截图','https://blog.testglider.com/how-to-use-testglider-for-a-higher-ielts-band-score/','官方操作教程+内页截图','界面为2023年样本；可证明历史设计，不能把旧导航当作2026完整实测。','2023-06-21')
source('MM03','TestGlider IELTS Corrections 操作说明','https://blog.testglider.com/new-feature-ielts-writing-speaking-answer-corrections/','官方操作说明','明确说明成绩页、Review、按题/part改写及计次方式；配额是旧版本。','2023-07-21；页面更新2024-07-19')
source('MM04','IDP Hong Kong：TestGlider IELTS 练习产品','https://www.idp.com/hongkong/ielts/ai-mock-test-practice/?lang=en','IELTS主办方产品说明','确认确有IELTS，并列整套/分科、答案解释、学习推荐；合作不等于评分经独立认证。')
source('MM05','TestGlider IELTS 购买页','https://www.testglider.com/en/product?category=IELTS','官方当前公开销售页','本次工具仅提取到分类及新产品筹备提示，无法确认当前个人套餐价格/次数。')
source('MM06','IOT 题库总入口','https://ieltsonlinetests.com/ielts-exam-library','公开题库内页/HTML直接读取','实际读取了筛选项与年份月份集合；没有做题。')
source('MM07','IOT 2026 January 题集','https://ieltsonlinetests.com/collection/ielts-mock-test-2026-january','公开题集内页/模式弹层文本','单科Take Test指向登录；页面同时含不同完整模考说明，未登录不能判定哪套分支实际生效。','2026-01-09')
source('MM08','IOT AI 写作公开评测样本','https://ieltsonlinetests.com/ielts-writing-ai-examiner-evaluation','官方报告样本+操作说明','看到预置作文、修订理由、分维反馈、改写范答；未提交自己的作文。')
source('MM09','IOT AI 口语：新作答与历史作答评测','https://ieltsonlinetests.com/ielts-speaking-ai-examiner-evaluation','官方操作说明','具体说明历史记录选题和评测确认；本次未获得自己录音的评分。')
source('MM10','IOT 人工写作评测服务','https://ieltsonlinetests.com/ielts-writing-examiner-evaluation','官方服务流程/FAQ','包括提交、购买、站内/邮件结果、周末排除；人工资质仅记录供应方声明。')
source('MM11','IOT 人工口语评测服务','https://ieltsonlinetests.com/ielts-speaking-examiner-evaluation','官方服务流程/FAQ','按录音提交评测，并非本次验证的一对一实时面试。')
source('MM12','IELTS Flex 当前产品入口','https://ieltsflex.com/','官方产品入口/层级说明','确认GEL产品、40套构成、免费mini与付费反馈档位；效果百分比未采信。')
source('MM13','IELTS Flex 使用结构','https://ieltsflex.com/how-flex-works/','官方操作/模式说明','检索标题异常为404，但本次可提取完整模式和课程正文；作为可读取官方说明，不冒充登录实测。')
source('MM14','FlexCheck AI 公开报告样本','https://ieltsflex.com/flex-check/','官方报告样本+原始界面图片','查看默认口语样本及两张报告图；未操作动态切换/上传评分。')
source('MM15','IELTS Flex 层级与单次模考说明','https://ieltsflex.com/courses-and-fees/','官方套餐说明','Gateway/Advantage两档，完整模考可分科完成；无登录结算价格核验。')
source('MM16','雅思哥PC官方下载及内页展示','https://www.ieltsbro.com/pc/','官方内页截图/视觉读取','逐张读取P1–P6及口语题卡图片；广告演示截图，不是本机真实交卷。')
source('MM17','雅思哥四档会员说明','https://www.ieltsbro.com/info/260/','官方会员说明','免费、VIPLite、VIP、SVIP及一次完整免费模考；不将宣传效果作为有效性证据。','2026-07-01')
source('MM18','雅思哥PC/App与AI评测边界','https://www.ieltsbro.com/info/52/','官方服务说明','区分PC与App，明确AI写说维度；尚无本次可读完整AI报告。','2026-04-30')
source('MM19','雅思哥跨平台权益FAQ','https://www.ieltsbro.com/info/70/','官方FAQ','称账号可双端登录但购买权益不跨平台；未用账户确认，不推定买一档两端全通。','2026-05-08')
source('MM20','小站雅思机考活动说明','https://ielts.zhan.com/rumen121796.html','官方招募/功能说明','只确认活动入口与功能声称，缺可读报告样本/逐步操作演示；因此未算深度完成产品。')

def fact(stage, detail, ids, strength='官方说明，未端到端实测', caveat=None):
    return dict(stage=stage, detail=detail, evidence=[dict(source_id=i,url=S[i]['url'],evidence_type=S[i]['evidence_type']) for i in ids], verification=strength, limitation=caveat)

products = [
dict(id='TG-IELTS',name='TestGlider IELTS',depth='深入：官方操作路径+历史内页样本；当前付费区未登录',investigation_priority='优先借鉴报告到专项学习的连接',
 identity='确有IELTS产品；不是把TOEFL报告或2026托福改版功能套到雅思。',
 journey='IELTS入口 → 整套/分科模考 → 成绩列表 → Review → 指定答案 → Correction；另一支由成绩进入学习推荐。',
 facts=[
 fact('入口与题库','当前IELTS入口可检索到学习中心、模考、练习题和考试记录导航；IDP介绍的IELTS套餐含整套与单科、8套试卷以及按题型练习。',['MM01','MM04'],'官方入口及主办方产品说明','8套为该说明套餐口径，不保证当前所有地区库存。'),
 fact('考试模式','官方IELTS教程把完整测试与单科测试分开；学习页另设练习题，避免把每次练习都组织成整场考试。',['MM02'],'官方历史操作教程','未验证计时锁定、暂停、自动交卷或选词标记；不能从仿真宣传补写控件。'),
 fact('成绩页实际字段','官方截图显示每次测试名称、时间、听读写说四分、总分和Review入口；样本四科为9/9/7/8，总分8.5。整套与单科成绩分栏。',['MM02'],'已视觉读取官方内页截图','这是演示数据，非本次成绩。'),
 fact('逐答反馈与改写','从成绩或练习记录打开Review，选一份回答后请求Correction，改写结果位于题目复查页右侧；官方说明高分回答可能只得到另一种表达，不保证加分。',['MM03'],'官方明确点击流程','本次未验证逐词差异标记，也未把生成改写当学习者掌握。'),
 fact('复盘到下一步','教程以一次整套结果触发课程推荐，听读练习按容易失误题型推荐；学习页截图同时显示目标/最高成绩、考试倒计时、题卡题型和完成比例。',['MM02','MM04'],'官方说明+已视觉读取学习页','推荐算法效果、是否有延迟复测未验证。'),
 fact('AI与人工','IELTS套餐明确提供AI评分、写说改写、每题解释及范答。未找到本次套餐含逐份人工复核的证据。',['MM03','MM04']),
 fact('会员边界','2023/24说明把Correction按写作每题、口语整科测试每part或单题练习每题计次，并曾给免费1次/会员5次。当前销售页无法提取有效套餐，旧次数不可作现行购买依据。',['MM03','MM05'],'历史规则与当前读取边界分列'),
 ],
 report_schema=['测试名称与日期','四科分数与总分','整套/单科成绩分栏','题目复查','本人回答与AI改写','解释/参考回答','学习推荐'],
 unknowns=['当前个人会员期限、次数和价格','IELTS实际考试页完整控件','改写后是否可一键重交并保留版本','2026报告是否与2023样本同版'],
 learning_takeaway='可借鉴“成绩记录→具体回答→一处修复→专项入口”；本地demo可手工选择下一项，不必复制AI评分。'),

dict(id='IOT',name='IELTS Online Tests',depth='深入：题库/模式公开内页+完整AI写作样本+人工与AI路径',investigation_priority='优先借鉴作答和评测分离、报告层级',
 identity='IOT学习网站；其页脚明确不等同官方IELTS Online考试。',
 journey='题库筛A/G与技能 → 年份/月题集 → 套题/单科 → 选择练习或模拟 → 登录作答 → 提交 → 当次或历史记录选择AI/人工评测 → 报告复查。',
 facts=[
 fact('题库组织','公开题库提供A类/G类、四技能、最新/热门/高评分筛选，按年份与月份进入集合；2026年1月页列两套练习，每套再分四科。',['MM06','MM07'],'已读取公开内页','日期题集是站方命名，不能推定当月官方真题。'),
 fact('模式与可见控件','题集页面包含练习/模拟选择；练习分支可选part/task和时间上限，再开始。单科入口实际链接到登录；完整测试有进度百分比与开始按钮。',['MM07'],'已读取公开页面模板，未点击登录后控件','同页同时保留三科约2时45分与四科约3小时说明，当前完整口语分支不能据此确认。'),
 fact('写作报告长什么样','公开预置报告按题目、原答及修订、四维评语、范答组织；修订逐处列增删及原因，随后提供改写范答与改进摘要。',['MM08'],'实际读取官方预置报告','未提交个人作文；所示band不是本次独立评分验证。'),
 fact('报告质量边界','同一公开样本的修订处显示277词，但评语又说仅差1词达标，存在样本内部不一致。可借鉴报告结构，不能据该演示认证评分准确。',['MM08'],'样本内部字段交叉检查'),
 fact('历史作答再评测','写作可提交后购评，也可先购买，再在历史记录选择过去作答。口语明确先留录音，历史记录选测并确认，或给刚完成的测试使用评测。',['MM08','MM09'],'官方点击流程','保存作答与是否购买反馈是两件事；未验证再写/再录的版本比较。'),
 fact('AI付费边界','公开服务页分别展示写作AI每次4.99美元、口语AI每次9.99美元；本轮证据是按次评测，不支持推定一个会员包无限覆盖全部服务。',['MM08','MM09'],'2026-09-19公开标价，未结算','税、地区、促销、套餐最终价格未核验。'),
 fact('人工写作路径','站内选题并提交作文，评测可前购或后购；结果在网站查看并由邮件送达。公开价每次19.99美元，48小时说明排除周末。',['MM10'],'官方服务流程/FAQ','正文允许自选题联系咨询、FAQ又说只选题库，是否接受外题待客服确认；未发送咨询。'),
 fact('人工口语路径','从口语题库录制并上传，再购买人工评价；报告反馈内容、表达和发音。它是录音批改服务，本轮未证实真人实时追问。',['MM11'],'官方服务流程/FAQ','页面给出每次19.99美元；评阅者资质为供应方声明。'),
 ],
 report_schema=['作答原题','本人原答','修改位置及理由','写作四维分与文字评语','参考改写','改进摘要','提交/处理中/完成状态','历史测试评测入口'],
 unknowns=['听读真实交卷报告的逐题证据定位控件','登录后当前完整模考是否包含口语','是否按错误类型自动生成下一套练习','重交是否另收费以及旧稿保留政策'],
 learning_takeaway='本地demo可先保留首答，再单独打开支持材料；反馈应连回具体原句/题号，而不是只有总分或大段范文。'),

dict(id='FLEX',name='IELTS Flex / FlexCheck AI（GEL）',depth='深入：模式说明+公开报告截图+套餐区分',investigation_priority='优先借鉴练习/模考分离与声音证据',
 identity='GEL提供的IELTS Flex；与其为British Council提供的学习生态相关，但不把另一产品的全部权益自动视为Flex权益。',
 journey='免费账户探索/mini诊断 → A/G完整模考或不限时练习 → 分科作答 → 听读逐题反馈/写说FlexCheck报告 → Guided Skills补弱；需人审时另选FlexLesson。',
 facts=[
 fact('题库与入口','公开产品列40套（25套Academic、15套General）；免费层有mini测试及写说AI试用，完整学习包另包括技能课程和直播/回放。',['MM12'],'官方产品结构','未确认所有40套当前题面、原创来源或难度。'),
 fact('考试与练习条件','官方说明阅读/写作练习不限制时间，模考为60分钟；听力练习可控制音频、模考按规定时间。口语在线可录回放，真人模拟属于另一服务。',['MM13'],'官方模式说明','未按按钮实测音频锁定或超时交卷。'),
 fact('报告首页','默认口语样本显示目标7、总分预测6；流利连贯/词汇/语法各6，发音5，并明确预测分不等于官方成绩。',['MM14'],'已读取公开样本字段'),
 fact('报告展开内容','实际样本图把问题与回答折叠，把本人表现单列：完整转写加CEFR词汇层级图及词例；图中提醒超过5分钟可能不能完整转写。',['MM14'],'已视觉读取官方报告图片','没有操作其动态展开；词汇层级不代表只用难词即可提分。'),
 fact('听读订正与课程返回','听读每题自动结果及反馈；Guided Skills按技能组织课程、训练和练习，可用完整/短版/选段。',['MM13'],'官方使用结构','未看见本次真实听读报告的证据高亮；也未证实自动错题重排。'),
 fact('AI层级','Gateway提供写说分维预测与词汇分析；Advantage追加详细个人反馈和本地语言支持、发音分析。公开报告提供口语/写作及两档切换入口。',['MM12','MM14','MM15'],'官方层级说明+样本入口','纯文本抽取不能辨识费用页全部打勾/禁用样式；以首页明确的增量描述为准。'),
 fact('人工反馈与单次模考','FlexLessons可购买老师辅导、真人口语模拟或写作批阅；完整模考套餐允许分科在各自时间完成，不必一次连续做完。',['MM13','MM15'],'官方服务说明','账户/课时/结算未操作；不把AI套餐等同含人工逐份批阅。'),
 ],
 report_schema=['目标与预测总分','四项分维预测','题目/回答折叠区','录音转写','CEFR词汇分布与例词','高阶详细评语/发音分析（官方描述，未全量展开）'],
 unknowns=['真实测试作答页全部控件','当前不同套餐价格与人工课时数量','Gateway/Advantage所有动态报告差异','看完报告是否强制/自动重教与复测'],
 learning_takeaway='本地可照这个结构保存原音、转写和具体问题，人工标记一次反馈；不限时学习与严格模考必须留下不同作答条件。'),

dict(id='BRO',name='雅思哥机考 / 写说评测',depth='深入：官方多张真实内页演示截图；AI完整报告未获得',investigation_priority='优先借鉴中文机考控件、题库与错题复盘',
 identity='PC端机考与移动App并存，本轮重点PC官方展示，未安装或登录。',
 journey='机考侧栏 → 剑雅册号/套卷卡 → 轻松或仿真 → 开始考试 → 题号/Part导航作答 → 机考记录/答案解析 → 听力原文定位或阅读证据 → 专项再练。',
 facts=[
 fact('题库布局与起步','官方截图按剑雅册号分行、Test分卡，卡片列四科和完成标记；侧栏把机考、机经、练习、课程与记录入口分开，口语卡另示题目和已练进度。',['MM16'],'已视觉读取官方P1与口语题卡','截图日期/当前题量不能由册号推定。'),
 fact('模式差异','截图可选轻松/仿真；仿真开始页明确四科完成后才看结果。会员说明另给新用户一次完整模考机会。',['MM16','MM17'],'已视觉读取模式弹层+官方说明','没有实测中途退出/暂停/重进规则。'),
 fact('作答控件','截图展示选中文字后的Note/Highlight、侧边笔记抽屉及删除；阅读有三档字体、文章复制填空、底部Part与题号/未答状态；写作有倒计时和字数。',['MM16'],'已视觉读取P2/P5/P6','这些是该产品演示控件，不证明与现行官方考试逐项相同。'),
 fact('听读报告和证据','阅读展示正确答案与本人答案并排、错项异色及逐题依据。听力精听界面有译文开关、速度/时间、随音原文、题目选项与原文句号定位。',['MM16'],'已视觉读取P4/P5','实际账号交卷未测；听力辅助在复盘界面，不能推定严格考试也允许倍速。'),
 fact('AI反馈','官方说明可对口语单题或整套作答给四维量化反馈；PC写作按任务、连贯、词汇、语法维度出报告。',['MM18'],'仅官方服务说明','本次没有完整AI写说样本，不能确认逐句批注、音素诊断、原音定位或复改版本。'),
 fact('会员层级','免费层供基础练习与一次完整试用；VIPLite增加逐题解释/精听/定位，VIP加机经与参考答案/范文/课程，SVIP加写说AI与带练。',['MM17'],'官方会员说明','只确认分层原则，不认证命中/提分，不给未经结算核验价格。'),
 fact('平台与人工边界','官网FAQ称同账号可双端登录但权益不跨平台。四科带练不等于每篇作文由真人精批，本轮没有人工批改订单和报告样本可证实。',['MM18','MM19'],'官方FAQ及证据边界','购买前需按实际PC/App套餐确认；本轮未注册或购买。'),
 ],
 report_schema=['机考记录入口','题号与完成状态','正确答案/本人答案','逐题解析','听力原文/译文/句子定位','写说四维报告（只有官方描述）'],
 unknowns=['完整AI报告真实字段与批注交互','当前PC与App会员实际同步规则','题目来源授权与机经真实性','是否有自动难题重教/延迟复测','当前人工逐份批改服务'],
 learning_takeaway='最值得移植的是“错在哪一题→对应哪一句→只重听/重读相关片段”的短路径，不是复制其机经命中宣传。'),
]

limits = [
    '本轮没有登录、注册、购买、使用他人账号，也没有提交个人答案或录音。',
    '所有交卷评分均未实测：报告字段由官方预置样本或官方界面截图支持；功能说明与样本明确分层。',
    '没有绕过登录/付费；公开HTML中存在的模板分支只记录可见文本，不当作实际账户权限或可执行状态。',
    '官网的精准评分、考官级、预测命中和提分百分比均不构成独立有效性证明。',
    '旧版教程仅作设计参考；当前价格、额度和运行行为若未核验均保留未知。',
]
decisions = [
dict(pattern='试卷组织和技能练习分离',basis=['TG-IELTS','IOT','FLEX','BRO'],local_use='完整模考以套卷为单位；日常学习以技能和局部材料为单位，两个入口保留清晰条件。'),
dict(pattern='首答先保存，评价后追加',basis=['IOT','TG-IELTS'],local_use='原答不被参考答案覆盖；报告是附在一次作答上的解释，允许之后手动补老师评语。'),
dict(pattern='总览→具体证据→修复',basis=['BRO','TG-IELTS','IOT'],local_use='点击错题直接回到句子/录音片段；写作反馈指出本人原句和改法，随后要求本人修一处。'),
dict(pattern='口语报告保留声音来源',basis=['FLEX','IOT'],local_use='录音、转写和文本语言问题分别记录；发音不能仅凭转写判断。'),
dict(pattern='把付费边界写在功能旁边',basis=['IOT','FLEX','BRO'],local_use='本地demo无需收费，但同样应在入口明确哪些环节已具备、需人工核对或仅有示范。'),
dict(pattern='报告不自动等于掌握',basis=['TG-IELTS','FLEX','IOT'],local_use='以上产品证据没有普遍证明延迟/陌生复测闭环；本地可手动安排新题复测，不凭AI改写或范文评分宣布学会。'),
]
assets = [
dict(product='TG-IELTS',source='MM02',file='tg-results.png',url='https://i0.wp.com/blog.testglider.com/wp-content/uploads/2023/06/IELTS-Full-Mock-Test-AI-Grading-Band-Score-Result.png?resize=1290%2C414&ssl=1',observed='成绩列表、四科分数、总分、复查按钮'),
dict(product='TG-IELTS',source='MM02',file='tg-study.jpg',url='https://i0.wp.com/blog.testglider.com/wp-content/uploads/2023/06/TestGlider-Study-Page.jpg?resize=1200%2C600&ssl=1',observed='目标/倒计时、四科切换、推荐题型、练习记录'),
dict(product='FLEX',source='MM14',file='flex-speaking-1.png',url='https://ieltsflex.com/static/00-1-39bad766a04f781a563cd4d9eac6dbb5.png',observed='题目与回答折叠标题'),
dict(product='FLEX',source='MM14',file='flex-speaking-2.png',url='https://ieltsflex.com/static/00-2-ec79e1c434813591703ecb289c92fd1f.png',observed='本人转写、5分钟限制提示、CEFR词汇分布图'),
]
bro = [('P1','f296cafe','题库册号/套卷/模式弹层'),('P2','7d0b3f85','Note/Highlight及笔记抽屉'),('P3','9af3f098','机经分类卡；不采信命中声称'),('P4','0780b6d5','精听原文、译文、倍速及句定位'),('P5','6cdcf7b4','阅读字体、复制填空、题号、答案对照'),('P6','ebc5834a','写作字数/计时')]
for n,h,o in bro: assets.append(dict(product='BRO',source='MM16',file='bro-'+n+'.png',url=f'https://www.ieltsbro.com/_next/static/media/{n}.{h}.png',observed=o))
for n,h in [('1','9d3ac17e'),('4','4ea66842'),('7','0fb47913')]: assets.append(dict(product='BRO',source='MM16',file='bro-oral-'+n+'.png',url=f'https://www.ieltsbro.com/_next/static/media/pc_oral_{n}.{h}.png',observed='话题、问题内容、已练数量与练习按钮'))
for a in assets:a['local_path']=str(BASE/'member-mocks-evidence'/a['file']);a['verification']='已视觉读取官方图片；非本次操作截图'

data=dict(title='登录/付费模考内部结构调查',date=DATE,status='调研完成；未实施设计或提交评分',scope='4个产品深入，另记录小站证据不足；不改主册或既有审查结论',source_count=len(S),sources=list(S.values()),products=products,evidence_assets=assets,limitations=limits,
 evidence_legend={'已读取公开内页':'真正取得的公开页面/字段，但不声称点击执行','已视觉读取官方截图':'供应商公开演示，不是本机交卷','官方操作说明':'能复原路径，但执行及效果未经本轮验证','未验证':'缺证据，不等同产品没有'},
 excluded_or_limited=[dict(name='小站雅思机考',status='只作候选，不算深入完成',source_id='MM20',url=S['MM20']['url'],verified='官方活动文给出联系报名入口，并声称有音频调节、阅读高亮、写作字数、自动判分及考点分析。',not_verified='未找到可直接读的完整报告、题库层级或会员操作说明；活动原价/限免不代表常态会员价格。',fallback='以IELTS Flex公开报告和操作页补足内部结构研究。')],design_findings=decisions,
 retrieval_notes=['British Council香港GEL手册PDF在本轮web与直接读取均超时，未引用其内部截图或内容。','TestGlider当前直接HTML几乎空壳，导航由官方搜索快照核对；旧教程/截图单独标日期。','IOT题库web读取偶发超时，改用同一公开URL的HTML正常读取；没有调用账户API或绕登录。','IELTS Flex费用页文字抽取无法确认所有图标的启用态，不由隐藏/排版文本推断额外权益。'])

(BASE/'member-mocks.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# 登录与付费模考内部结构调查',f'调查日期：{DATE}。4个产品深入、20个主来源；官方图片作为对应来源的附属证据。','',
'**已大致还原实际路径：进入试卷、模式选择、保存作答、成绩/报告、具体反馈和下一步。没有交卷评分实测，也没有注册或购买。**','',
'最值得对照的是：雅思哥的听读证据定位，IOT的历史作答补评与逐处修订报告，TestGlider的成绩到专项推荐，IELTS Flex的练习/模考和AI/人工分层。','',
'## 证据边界','']
md += ['- '+x for x in limits]
for p in products:
    md += ['',f"## {p['name']}",'',p['depth']+'。'+p['identity'],'', '**用户路径：** '+p['journey'],'']
    for f in p['facts']:
        cites=' '.join(f"[{e['source_id']}]({e['url']})" for e in f['evidence'])
        md += [f"**{f['stage']}：** {f['detail']} {cites}",f"证据：{f['verification']}。"+(f" 限定：{f['limitation']}" if f['limitation'] else ''),'']
    md += ['报告结构：'+' → '.join(p['report_schema'])+'。','', '尚未确认：'+'；'.join(p['unknowns'])+'。','', '**对本地demo的启发：** '+p['learning_takeaway']]
md += ['', '## 小站：保留为候选，不夸大调查深度','',
'本轮只有[官方活动说明](https://ielts.zhan.com/rumen121796.html)能证实报名入口和功能声称；没有取得可读完整报告或会员操作路径，所以用IELTS Flex补足深入比较。活动限免不是常态套餐。','',
'## 可直接指导本地demo的结构结论','']
for x in decisions:md += [f"- **{x['pattern']}：** {x['local_use']}（依据：{'、'.join(x['basis'])}）"]
md += ['','这些是从本轮产品结构推导的设计判断，不代表已经实施，也不是学习效果实验。','', '## 内页证据资产','']
for a in assets:
    md += [f"- {a['product']}：{a['observed']}。[官方原图]({a['url']}) · [本地证据](<{a['local_path'].replace(chr(92),'/')}> )"]
md += ['','## 来源目录','']
for s in S.values():md += [f"- **{s['id']}** [{s['title']}]({s['url']}) — {s['evidence_type']}；{s['note']}"+(f" 发布/更新：{s['published']}。" if s['published'] else '')]
md += ['', '## 读取限制','']+['- '+x for x in data['retrieval_notes']]
(BASE/'member-mocks.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
assert len(products)>=3 and 12<=len(S)<=20
assert all(f['evidence'] for p in products for f in p['facts'])
assert all(Path(a['local_path']).exists() for a in assets)
print(json.dumps({'products':len(products),'sources':len(S),'facts':sum(len(p['facts']) for p in products),'assets':len(assets),'files':['research/member-mocks.json','research/member-mocks.md']},ensure_ascii=False))
