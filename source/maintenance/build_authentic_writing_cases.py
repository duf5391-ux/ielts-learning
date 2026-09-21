from pathlib import Path
import json, shutil, re, html, hashlib

BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
LIB = BOOK.parent / 'materials-library'
ROOT = Path(__file__).parent
CASES = []

def ref(pattern, title, page, test, kind='真题'):
    p = next(BOOK.rglob(pattern))
    return dict(id=p.stem, originalUnit=title+' · '+test, title=title, path=p.relative_to(BOOK).as_posix(), page=page, test=test, kind=kind,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def package(src, name):
    p=BOOK/'case-assets'/name
    shutil.copy2(src,p)
    return p

package(LIB/'writing/ielts-academic-writing-sample-tasks-2023.pdf','writing-official-sample-tasks-2023.pdf')
package(LIB/'supplement/ielts-academic-writing-access-arrangement-modified-large-print-question-paper.pdf','writing-official-large-print.pdf')
package(LIB/'expansion-2026-09-14/cambridge-zip-115028_Academic_Writing_sample_task_-_Task_2.pdf','writing-official-transport.pdf')
package(LIB/'expansion-2026-09-14/cambridge-zip-115030_General_Training_Writing_sample_task_-_Task_2.pdf','writing-official-elder-care.pdf')

def c21(page, test): return ref('8ee8170c*.pdf','Cambridge IELTS 21 Academic',page,test)
def off(page,test): return ref('writing-official-sample-tasks-2023.pdf','IELTS Academic Writing Sample Tasks (2023)',page,test,'官方样题')
def mod(page,test): return ref('writing-official-large-print.pdf','IELTS Academic Writing — modified large print',page,test,'官方样题')
def add(id, skill, typ, title, source, prompt, practice, paragraphs, explanation, structure, phrases, sentences, image=None, data=None):
    c=dict(id=id,skill=skill,questionType=typ,title=title,source=source,prompt=prompt,
           practicePrompt=practice,modelAnswer=paragraphs,modelAnswerLabel='参考写法（编写示范，基于本题；非官方范文，也非唯一答案）',
           explanation=explanation,intensive=dict(structure=structure,phrases=phrases,sentences=sentences),
           answerPolicy='先完成自己的写作，再展开参考写法、数据核对和精读。',
           originalTaskInstruction=('Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words.' if skill=='writing1' else 'Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words.'),
           wordCount=sum(len(p.split()) for p in paragraphs),
           status='达标',verified=dict(prompt='对照数据库原始PDF',page='PDF页码，从1开始',model='原创参考写法已与原题核对；无虚构调查或分数承诺'))
    if image: c['image']='case-assets/'+image
    if data: c['sourceData']=data; c['verified']['diagram']='已逐张渲染原始PDF并视觉核对；保留原图'
    CASES.append(c)

add('wc-c21-t1-jobs','writing1','折线图','美国四行业就业：峰值、交叉与最终排名',c21(30,'Test 1 · Task 1'),
'The graph below gives information about the number of jobs in four sectors of the economy in the US between 1960 and 2020.',
'先独立写Overview，再写两个主体段（共约150–180词）：一段写制造业与农业，另一段写零售与医疗。必须给出单位，并交代制造业中途的峰值；不逐点流水账。',
[
'Overall, manufacturing provided the most jobs at the beginning of the period, but it was overtaken by both retail and healthcare by 2020. Healthcare experienced the strongest growth, whereas agricultural employment declined and remained the smallest of the four sectors at the end.',
'Manufacturing employment rose from 15 million in 1960 to a peak of 20 million in 1980. It then fell to approximately 17 million in 2000 and 13 million in 2020. Agriculture followed a different pattern: its workforce dropped from about 6 million to 3 million during the first twenty years, remained at that level in 2000, and decreased to roughly 2 million by the end.',
'By contrast, the number of retail jobs increased throughout, from around 6 million in 1960 to 10 million in 1980 and 15 million in 2000, before reaching about 16 million in 2020. Healthcare grew from only 2 million jobs to 5 million and then 11 million, eventually matching retail at approximately 16 million.'
],
['原图纵轴是Jobs in millions：15表示1500万个岗位，不是15%或15万人。','制造业1980年达到20 million，之后下降；不能概括为1960–2020持续下降。','零售与医疗2020年约16 million并列；医疗从2到16增长约14 million，增幅最大。农业1980与2000均约3 million，不能写每阶段都下降。'],
['Overview回答主导行业更替与两组趋势。','主体一合并峰值后下降的制造业和总体下降的农业。','主体二并写增长行业，用最终并列收束比较。'],
['rise to a peak of 20 million：峰值位置与单位同时保留。','be overtaken by：排名改变；这里由2020年的终点比较支持。','eventually matching retail：结果分词短语，不再重复整句。'],
['Manufacturing employment rose from 15 million in 1960 to a peak of 20 million in 1980. → from交代起点，to交代终点；of连接峰值大小。','Healthcare grew ... eventually matching retail ... → matching的主语仍是Healthcare，不是2020。'],
'writing-c21-30.png',{'years':[1960,1980,2000,2020],'unit':'million jobs','manufacturing':[15,20,17,13],'retail':[6,10,15,16],'agriculture':[6,3,3,2],'healthcare':[2,5,11,16]})

add('wc-c21-t2-cafe','writing1','地图','学院咖啡厅改造：保留设施与功能替换',c21(52,'Test 2 · Task 1'),
'The plans below show a college café before it was redesigned and how it looks now.',
'对照前后两张原图，写Overview和两个主体段（约150–180词）：第一段写室内功能替换，第二段写保留设施与室外扩展。原图没有指北针，用left/right/top/bottom或相对设施定位。',
[
'Overall, the café has been redesigned to offer a wider range of food and drink services, and an outdoor seating area has been added. The kitchen and toilets remain in their original positions, while the former staff dining rooms now serve different purposes.',
'Previously, all food and drink were available from a single serving area directly below the kitchen. This counter is now used for hot meals, and a salad bar has been installed along the left-hand wall of the main seating area. The two staff dining rooms along the upper edge of the main seating area have been converted into a takeaway food outlet and a coffee bar respectively. Tables and chairs still occupy the main central area.',
'At the bottom of the present plan, an outdoor seating area extends beyond the former café boundary, with a barbecue at its left end. New doorways connect this area to the interior. Near the entrance on the right-hand side, recycling bins have replaced the original bin, while the toilets remain in the lower-right corner.'
],
['不是“图书馆改造”：真实材料是college café。两间staff dining rooms分别变为take away food和coffee bar，必须对应两处功能。','厨房与厕所位置保留；增设沙拉吧、室外座位、barbecue，bin改为recycling bins。','原图对比过去与现在，故用previously + past、now + present以及has been added；没有未来规划，不能用will be built。'],
['概述先概括服务多样化和室外扩展，再点出保留。','室内按厨房—服务区—原职工餐厅的邻接关系走图。','室外扩展与入口附近小变化同段收尾。'],
['have been converted into：旧功能转为新功能。','remain in their original positions：明确保留而不是遗漏。','beyond the former café boundary：说明扩展到原边界之外。'],
['The two staff dining rooms ... have been converted into a takeaway food outlet and a coffee bar respectively. → respectively按列举顺序配对，不能互换位置。','with a barbecue at its left end → its指outdoor seating area；没有虚构东南西北。'],
'writing-c21-52.png',{'retained':['kitchen','toilets','central tables and chairs'],'converted':{'staff dining room left':'take away food','staff dining room right':'coffee bar','serving area':'hot meals'},'added':['salad bar','barbecue','outdoor seating','recycling bins']})

add('wc-c21-t3-rainshadow','writing1','自然流程图','雨影沙漠：越山前后的水分变化',c21(73,'Test 3 · Task 1'),
'The diagram below shows how one type of desert, known as a rain-shadow desert, is formed.',
'写Overview与两个主体段（约150–180词），沿原图7个编号描述迎风坡降雨及背风坡干燥；只使用图中可见机制，不添加温度数值或当地名称。',
[
'Overall, rain-shadow deserts form inland after winds have crossed a mountain range. The key contrast is between the windward side, where rising moist air produces clouds and rain, and the leeward side, where the air continues towards the interior in a dry state.',
'The process begins when winds approach the coast from the sea. On reaching the mountains, they are pushed upwards along the windward slope. As the moist air rises, it cools, and clouds form above this side of the mountains. Rain then falls, removing moisture from the air before it passes over the mountain range. These are successive stages rather than two separate routes through the diagram.',
'The remaining dry air continues over the summit and moves down the leeward side. Dry winds subsequently reach areas further inland, where a rain-shadow desert is found. The diagram indicates that the distance from the coast towards this inland area can extend over thousands of kilometres, emphasising that the final dry region lies beyond the mountain barrier.'
],
['原图7步：海风到岸→被迫抬升→湿空气升高冷却→云形成→下雨→干空气越山→干风抵达内陆。','用windward与leeward形成机制对比，而不是编造沙漠经历采矿或开垦。','图上仅标thousands of kilometres，不能改为准确3000公里；这是空间尺度，不是形成所需时间。'],
['Overview交代终点与关键转变：湿气在越山前被降雨带走。','主体一描述迎风坡上的连续阶段。','主体二描述背风坡及最终形成的内陆干燥区。'],
['on reaching the mountains：on + 动名词表示“一到达”。','as the moist air rises：as联系同步发生的上升与冷却。','in a dry state：准确描述性质变化而非另加数字。'],
['As the moist air rises, it cools, and clouds form ... → 一个时间/伴随从句连接三个连续变化。','where a rain-shadow desert is found → where修饰areas further inland，不指海岸。'],
'writing-c21-73.png',{'stages':7,'start':'winds approach coast','end':'dry winds reach inland areas','spatialScale':'thousands of kilometres'})

add('wc-c21-t4-library','writing1','饼图与表格','图书馆用户与满意度：两图的不同分母',c21(95,'Test 4 · Task 1'),
'The chart and table below show the results of a survey of library users at a university.',
'写Overview、用户构成段和满意度段（约150–180词）。用表格中的真实百分数作比较；说明44%不是“本科生满意率”，并准确表达percentage points。',
[
'Overall, full-time undergraduates formed the largest group of library users, while academic staff accounted for the smallest share. Satisfaction was particularly strong for staff helpfulness and opening hours, whereas journals and wi-fi attracted the highest proportions of dissatisfied responses.',
'Full-time undergraduates represented 44% of users, followed by full-time postgraduates at 25%. Part-time postgraduates made up a further 16%, meaning that postgraduate students together accounted for 41%, slightly less than the undergraduate group. Distance learners and academic staff comprised the remaining 8% and 7% respectively.',
'Turning to the services, 95% of users were very satisfied with staff helpfulness, compared with 65% for opening hours, a difference of 30 percentage points. Neither item received any dissatisfied responses. The shares who were very satisfied with books, journals and wi-fi were considerably lower, at 50%, 45% and 48%. Dissatisfaction with journals was highest at 20%, closely followed by wi-fi at 19%, while the figure for books was 10%.'
],
['饼图分母为所有library users；表格每行是该服务的满意度分布。44%本科用户不能说成44%本科生满意。','95%与65%的差是30个百分点，不是“30%增长”；本题没有年份变化。','研究生两组25%+16%=41%，与本科44%可作合并比较；原图各类总计100%。'],
['概述分别覆盖用户构成、服务评价。','一段只处理饼图，合理合并两类研究生。','一段处理表格，先最佳两项，再比较较弱三项。'],
['accounted for / represented / made up：静态占比动词。','a difference of 30 percentage points：两个百分数相减。','closely followed by：指出19%与20%接近。'],
['Neither item received any dissatisfied responses. → neither覆盖刚提到的staff helpfulness和opening hours。','meaning that postgraduate students together accounted for 41% → 合并的是同一总体下的两个互斥类别。'],
'writing-c21-95.png',{'users':{'full-time undergraduate':44,'full-time postgraduate':25,'part-time postgraduate':16,'distance learning':8,'academic staff':7},'satisfactionColumns':['very satisfied','fairly satisfied','not satisfied'],'satisfaction':{'opening hours':[65,35,0],'staff':[95,5,0],'books':[50,40,10],'journals':[45,35,20],'wifi':[48,33,19]}})

add('wc-official-education','writing1','柱状图','英国继续教育：人数与学习形式',off(3,'Task 1A'),
'The chart below shows the number of men and women in further education in Britain in three periods and whether they were studying full-time or part-time.',
'写Overview及两个主体段（约150–180词）：按part-time/full-time分组，跨性别和年份作比较。纵轴是thousands，图上非刻度交点的数使用about。',
[
'Overall, part-time study was much more common than full-time study among both men and women in all three periods. Female participation increased in both modes, and by 1990/91 women outnumbered men in part-time education, while the numbers studying full-time were similar.',
'About one million men studied part-time in 1970/71, compared with roughly 750,000 women. Male participation then declined to around 850,000 in 1980/81 before recovering to about 900,000 in 1990/91. The corresponding female figure rose steadily, reaching just over 800,000 in the middle period and approximately 1.1 million in the final one. Thus, the initial male lead was reversed by the end.',
'Full-time numbers were considerably smaller. Around 100,000 men followed full-time courses in 1970/71, compared with fewer than 100,000 women. Both figures subsequently increased. Female full-time participation had moved above the male figure by 1980/81, and by 1990/91 the totals for the two sexes were both in the region of a quarter of a million.'
],
['纵轴thousands：1000相当于1,000,000人；不能把灰柱1000写成1000人或1000%。','灰柱part-time始终远高于黑柱full-time。男性part-time先降后回升，不能写三期持续上升。','女性part-time最终约1.1 million高于男性约0.9 million；采用图形估读的约数，不把粗图假装精确调查数据。'],
['Overview横跨两个性别和两种形式。','主体一用part-time的起点差距、转折、终点反转构成比较链。','主体二把较小的full-time群体集中处理。'],
['outnumbered men：人数超过男性，而非增长率超过男性。','the corresponding female figure：省去重复part-time participation。','in the region of a quarter of a million：粗图估读的稳妥表达。'],
['Male participation then declined ... before recovering ... → before后动名词标示先降后升。','Thus, the initial male lead was reversed by the end. → 总结比较，不添加原因。'],
'writing-official-3.png',{'unit':'thousands of people','periods':['1970/71','1980/81','1990/91'],'partTimeMaleApprox':[1000,850,900],'partTimeFemaleApprox':[750,825,1100],'readingNote':'柱宽、扫描精度限制下全日制值采用约数；最后男女都约250 thousand。'})

add('wc-official-audiences','writing1','折线图','广播与电视受众：同一天的双峰比较',off(4,'Task 1B'),
'The graph below shows radio and television audiences throughout the day in 1992.',
'保留图中一天的完整时间轴，写Overview及两个主体段（约150–180词）。须写清百分比人群、广播早高峰与电视晚高峰；不能把一天内的时段变化写成年增长。',
[
'Overall, radio attracted its largest audience in the morning, while television viewing was concentrated in the evening. Television reached a substantially higher peak than radio, and both media had very small audiences during the early hours of the morning.',
'At 6 a.m., approximately 5% of the UK population aged over four listened to the radio, while virtually nobody was watching television. Radio listening rose rapidly to a peak of about 27% at around 8 a.m. It then generally declined through the day, despite a modest recovery in the late afternoon. By late evening, the figure had fallen to well below 10%, and it approached zero during the night.',
'Television viewing remained below 10% throughout the morning before rising around lunchtime and overtaking radio early in the afternoon. After a brief period near 15%, the television audience increased sharply in the late afternoon and evening, peaking at roughly 45–47% around 8 p.m. It subsequently dropped steeply, especially after midnight, and was only a few per cent by the following morning.'
],
['对象是UK population over 4 years old；百分比不能写成millions。图题范围October–December 1992，横轴6am到次日6am。','广播峰值约27%，电视约45–47%；粗线图允许about，不需要虚构47.3%。','“overtaking radio early in the afternoon”来自两线相交；不能把晚间电视优势扩成全天每时段都更高。'],
['Overview先比峰值出现时段，再比峰值大小。','广播段按主要升降，不追逐每个小波动。','电视段突出午后反超、晚间最高、午夜后下降。'],
['was concentrated in the evening：集中发生的时间。','despite a modest recovery：概括主趋势中的小反向变化。','virtually nobody：接近零，不强行写0.0%。'],
['It then generally declined ... despite a modest recovery ... → generally给真实波动留空间。','After a brief period near 15%, ... → 介词短语给出第二次明显上涨前的平台。'],
'writing-official-4.png',{'population':'UK, over 4 years old','surveyPeriod':'October–December 1992','radioPeakApprox':'27% around 8 a.m.','tvPeakApprox':'45–47% around 8 p.m.'})

add('wc-official-bricks','writing1','制作流程图','制砖：并行成形路径与温度阶段',off(5,'Task 1C'),
'The diagram below shows the process by which bricks are manufactured for the building industry.',
'写Overview及两个主体段（约150–180词）。保留wire cutter / mould的二选一分支、24–48小时干燥、两档窑温和48–72小时冷却；按工序分段。',
[
'Overall, brick manufacture begins with the excavation of clay and ends with the packaging and delivery of the finished product. The material passes through preparation, shaping, drying, heating and cooling, with two alternative methods available for forming individual bricks.',
'First, clay is dug from the ground by a mechanical digger and placed on a metal grid above a roller. The material is broken into smaller pieces before sand and water are added. The resulting mixture is then shaped into bricks either by a wire cutter or by being placed in moulds. These are alternative routes at the same stage, rather than consecutive operations that every brick must undergo.',
'The newly formed bricks are dried in an oven for 24 to 48 hours. They are then heated in a kiln, initially at a moderate temperature of 200–980°C and subsequently at a higher temperature of 870–1300°C. After this, they spend 48 to 72 hours in a cooling chamber. Finally, the cooled bricks are packaged and loaded for delivery by truck.'
],
['原图or连接wire cutter和mould，参考写法用either ... or，不能写先切后入模。','干燥24–48h与冷却48–72h不同；窑炉先200–980°C、后870–1300°C，区间重叠是原图数据，不自行“纠正”。','被动语态描述材料经历：is dug / are added / are dried；无需凭空添加工人或工厂地点。'],
['Overview起终点加主要加工阶段。','前段写原料准备与成形分支。','后段写热处理、冷却和配送。'],
['either by a wire cutter or by being placed in moulds：两种方式保持平行。','initially ... subsequently：区分两档窑温。','the resulting mixture：回指已经加入沙和水的黏土。'],
['The material is broken into smaller pieces before sand and water are added. → 两个被动结构保留明确先后。','They are then heated ... initially ... and subsequently ... → 同一heated谓语承接两个温度阶段。'],
'writing-official-5.png',{'shaping':['wire cutter','mould'],'dryingHours':[24,48],'kilnModerateC':[200,980],'kilnHighC':[870,1300],'coolingHours':[48,72]})

add('wc-official-bicycle','writing1','表格','自行车使用率：年龄比较与百分点差',mod(4,'Task 1'),
'The table below gives information about the percentage of the population by age group in one town who rode a bicycle in June 2011.',
'写Overview及两个比较段（约150–180词），先比较儿童/青少年，再比较成人；指出最低组和60+回升。列出最大性别差距并用percentage points表达。',
[
'Overall, cycling was most common among children under ten and least common in the 40–59 age group. Males had higher participation rates than females in every category, although the difference between the sexes was very small among the youngest children.',
'Among those aged 0–9, 51.3% of males and 50.3% of females rode a bicycle, a gap of just one percentage point. Participation was lower among 10–17-year-olds, at 42.2% for males and 24.6% for females. This group therefore had the largest gender difference, amounting to 17.6 percentage points, with the male figure considerably higher than the female one.',
'The proportions were smaller in both adult groups below sixty. For people aged 18–39, the rates were 17.1% and 9.7% respectively, falling to 12.3% and 8.0% among 40–59-year-olds. However, the figures rose again in the oldest category: 18.5% of men and 13.2% of women aged sixty or above cycled. Thus, participation did not simply decrease continuously across the age groups.'
],
['这是June 2011单月横截面：年龄组之间差异不证明同一批人随时间减少骑行。','10–17岁差距42.2−24.6=17.6个百分点；0–9岁差距1.0个百分点。','两性最低都是40–59岁，60+均回升；不能写年龄越大比例总是越低。'],
['Overview同时覆盖年龄高低与性别关系。','前段突出高参与儿童及最大差距青少年。','后段写成人低谷与60+例外。'],
['a gap of just one percentage point：不是one per cent decrease。','amounting to 17.6 percentage points：补充精确差值。','across the age groups：年龄间比较，避免错误时间趋势。'],
['For people aged 18–39, the rates were 17.1% and 9.7% respectively ... → 顺序沿用前段male/female。','However, the figures rose again in the oldest category ... → rose描述相邻年龄组数值变化，最后一句明确并非持续时间变化。'],
'writing-bicycle-4.png',{'ageGroups':['0–9','10–17','18–39','40–59','60+'],'male':[51.3,42.2,17.1,12.3,18.5],'female':[50.3,24.6,9.7,8.0,13.2],'unit':'percent'})

# Task 2 cases practise two connected body paragraphs, not an abbreviated whole essay.
def w2(id,typ,title,source,prompt,practice,p1,p2,explain,structure,phrases,sentences):
    add(id,'writing2',typ,title,source,prompt,practice,[p1,p2],explain,structure,phrases,sentences)

w2('wc-c21-t1-homes','同意程度','高层住宅是否是城市住房的最佳方案',c21(31,'Test 1 · Task 2'),
'The best way to provide enough homes in large cities is to build tall apartment blocks. To what extent do you agree or disagree with this statement?',
'只写两段主体，约170–210词：先解释高层住宅怎样增加住房，再论证best way的适用边界。明确你赞成到什么程度；不把题目弱化为“高层住宅有没有好处”。',
'Tall apartment blocks can make an important contribution where urban land is scarce. By placing many homes on the same site, a city can accommodate more residents without continually expanding into surrounding farmland. A development near an existing railway station may also allow more households to reach jobs without long car journeys. These benefits support the use of high-rise housing in well-connected districts. They are especially relevant when the alternative is low-density construction that provides relatively few homes on valuable central land.',
'However, building upwards is not automatically the best response to every housing shortage. If the new flats are unaffordable, an increase in the total housing supply may do little for families who need reasonably priced accommodation. A large tower can also add pressure to schools, water systems and public transport if these services are not expanded. I would therefore favour tall buildings as one part of a wider strategy that also renovates empty properties and provides affordable homes. Their value depends on location, price and supporting infrastructure, rather than height alone.',
['题眼是best way，不只是a useful way。第二段用可负担性与配套条件检验“最佳”的范围。','第一段链条：同一地块更多住房→少向农地扩张；交通站点例子用may，不伪装统计研究。','两段最后形成“有条件赞成”：认可高层的贡献，同时不支持它作为所有城市的唯一最佳办法。'],
['优势机制—条件化例子—回扣城市土地约束。','限制条件—影响—明确程度立场。'],
['where urban land is scarce：限定论据适用地点。','do little for families who ...：解释新增供给为何不必然解决可负担问题。','one part of a wider strategy：表达有条件赞成。'],
['If the new flats are unaffordable, an increase ... may do little ... → 条件句直接检验题目的“provide enough homes”。','Their value depends on ... rather than height alone. → Their指tall buildings，结尾仍围绕建筑方案。'])

w2('wc-c21-t2-entertainment','讨论双方','线上娱乐与剧院影院的经济文化价值',c21(53,'Test 2 · Task 2'),
'Some people say that in the digital age, theatres and cinemas are no longer important as people can watch all the entertainment they want online. Others argue that theatres and cinemas are still important both economically and culturally. Discuss both these views and give your own opinion.',
'写两段主体，约180–220词：第一段把“线上足够”的理由讲完整，第二段解释剧院影院的经济和文化价值，并明确你的判断。不能只写我喜欢看电影。',
'Those who question the importance of theatres and cinemas can point to the convenience of online entertainment. Viewers can choose what to watch and when to watch it, without paying for transport or arranging an evening around a fixed screening time. Online access may be particularly valuable to people living far from major cultural venues or caring for children at home. For these audiences, a subscription can offer a practical alternative to frequent visits. This makes the claim that physical venues are less necessary understandable, especially when the main aim is simply to see a film.',
'Nevertheless, I believe these venues retain functions that a personal screen cannot fully reproduce. Economically, a performance supports performers, technicians and other staff, while audiences may also spend money in nearby businesses. Culturally, theatres can stage local stories and create a shared encounter between performers and spectators. Even in a cinema, an audience experiences a film together rather than as separate individuals at home. Online services can therefore widen access without removing the value of physical venues. The two forms can coexist, serving different circumstances and offering different kinds of participation.',
['第一段真正解释第一方观点：选择时间、出行成本、照顾孩子与地域可达性；没有直接贴标签后马上反驳。','第二段分别回应economically与culturally：岗位/周边消费与本地故事/共同体验。','立场是仍有价值、可共存；不是讨论互联网是否总体有害。'],
['解释线上取代说的合理条件与实际受益者。','转折后经济、文化两条机制，最后给出共存判断。'],
['a practical alternative to：适合替代某项活动，不等于完全替代所有功能。','retain functions that ... cannot fully reproduce：区分可替代与不可完全复制部分。','can coexist：立场收束而非非黑即白。'],
['Online access may be particularly valuable to people living ... or caring ... → living与caring平行修饰people。','The two forms can coexist, serving ... and offering ... → 两个分词补充共存的理由。'])

w2('wc-c21-t3-placement','利弊权衡','本科海外学习或实习：收益能否超过代价',c21(74,'Test 3 · Task 2'),
'All university undergraduate courses should include a period of time spent studying abroad or doing a work placement. Do you think the advantages of this would outweigh the disadvantages?',
'写两段主体，约170–210词：一段承认费用和安排的代价，另一段讨论学习/就业收益，并按“能否控制、持续多久、影响多大”作权衡。注意abroad OR work placement，不要强制把两者都做。',
'A compulsory period away from normal university classes can create real difficulties. Studying abroad may involve travel and accommodation costs, while even a local work placement can reduce the time available for paid employment. Students with caring responsibilities may find these demands particularly difficult. Universities also need enough suitable placements; an experience consisting only of routine administrative work would offer limited educational value. These drawbacks matter because the proposal applies to all undergraduate courses, including students and subjects for which arranging an appropriate experience may be challenging.',
'Even so, I consider the potential advantages greater if institutions offer flexible, well-supported options. A relevant placement allows students to apply classroom ideas to actual workplace problems and obtain feedback from experienced colleagues. Overseas study can expose them to different academic approaches and require greater independence. These gains may continue to influence later study and employment, whereas some financial and practical barriers can be reduced through funding and local placement alternatives. The stronger policy is therefore to provide a meaningful choice between suitable forms of experience, with clear learning goals, rather than require every student to travel abroad.',
['题目是abroad or placement，末句明确保留本地实习选项；不能误写所有学生必须出国。','outweigh要求比较：长期学习收益与可缓解的成本相对照，而不是两边各列三点后不判断。','承认all courses的实施难题，立场带条件但清楚支持收益更大。'],
['负担—更脆弱人群—低质量安排的风险。','收益机制—长期价值—降低成本的方法—权衡结论。'],
['the proposal applies to all ...：抓住题目范围词。','may continue to influence ... whereas ...：把持续性作为权衡依据。','with clear learning goals：限制支持对象，防止无条件夸大。'],
['These drawbacks matter because the proposal applies to all undergraduate courses ... → because不是重复缺点，而是解释“为什么重要”。','... rather than require every student to travel abroad → 排除的是误读后的强制出国，不是否认原题。'])

w2('wc-c21-t4-primary','双问','小学正式学习与课堂游戏：两个问题分别回应',c21(96,'Test 4 · Task 2'),
'Some people argue that primary schools focus too much on formal learning. To what extent do you agree with this opinion? How important do you think it is for children to play as well as learn in the primary school classroom?',
'写两个主体段，约180–220词：第一段回答是否“过分”重视formal learning，第二段回答课堂游戏有多重要及其教育机制。游戏不是课外体育的同义词。',
'I agree that formal learning can receive too much attention when a primary timetable leaves little space for exploration. Direct instruction is necessary for teaching children basic reading and arithmetic, and structured practice helps them become accurate. However, long sequences of worksheets and tests can make pupils focus on producing the expected answer rather than understanding an idea. For example, a child may memorise a calculation procedure but struggle to explain why it works. The problem is therefore not formal teaching itself, but an imbalance that treats written performance as the only useful evidence of learning.',
'Play has an important complementary role inside the classroom. In a pretend shop, children can practise counting, explain prices and take turns serving one another. The activity joins mathematical language with social interaction, giving a purpose to skills that might otherwise appear abstract. Building a model together can similarly require planning, discussion and revision after something fails. Such activities still need thoughtful guidance from the teacher, so that enjoyment supports a clear learning aim. I would consequently regard purposeful play as a regular part of primary education, rather than a reward offered only after all the serious work is finished.',
['第一段明确同意的范围：当formal learning挤压exploration时过多，而非主张取消识字算术。','第二段给出课堂内的假想商店与合作模型，回应primary classroom，不跑题到放学后娱乐。','play as well as learn提示两者结合；不是“玩”和“学”完全对立。'],
['先回答程度，再解释不平衡如何损害理解。','另段回答重要性，以具体课堂活动展示机制。'],
['an imbalance that ...：把批评集中到比例失衡。','an important complementary role：补充作用，不是否定正式教学。','purposeful play：有学习目的的课堂游戏。'],
['The problem is therefore not formal teaching itself, but an imbalance ... → 保持部分同意立场一致。','... so that enjoyment supports a clear learning aim → 目的从句解释教师指导的作用。'])

w2('wc-official-wealth','同意程度','家庭财富与成年问题应对：避免绝对化',off(6,'Task 2A'),
'Children who are brought up in families that do not have large amounts of money are better prepared to deal with the problems of adult life than children brought up by wealthy parents. To what extent do you agree or disagree with this opinion?',
'写两段主体，约170–210词：解释有限预算可能培养什么能力，再指出财富不自动决定教养方式。比较双方，不把贫穷浪漫化为必然优势。',
'Children in families with limited money may gain useful experience of making choices under constraints. If a household cannot afford every desired purchase, a child may have to save gradually, distinguish needs from wants and accept that one decision rules out another. Shared responsibilities can also encourage practical independence. These experiences resemble some of the budgeting and prioritising required in adult life. They provide a plausible reason why growing up without abundant resources could help a person cope with certain financial problems later on.',
'However, I do not think family wealth alone determines how well someone is prepared. Persistent financial insecurity can create stress and restrict access to education or supportive activities, leaving children with fewer resources for future challenges. Conversely, wealthy parents can require their children to manage an allowance, contribute to household tasks and take responsibility for mistakes. Such practices may develop the same judgment and resilience without serious deprivation. I therefore reject the general comparison in the question: preparation depends more on the responsibilities, guidance and opportunities children receive than on whether their parents have a large income.',
['没有把may写成all poor children：有限预算可能培养技能，但严重匮乏也会限制机会。','对比对象始终是两类家庭中的孩子及成年应对能力，不转成贫富差距政策文章。','第二段以同样责任训练可存在于富裕家庭反驳“财富决定论”，给出明确不同意。'],
['承认一方可能的培养机制。','反例与变量区分，回应原题总体比较。'],
['distinguish needs from wants：与预算管理直接相关。','family wealth alone determines：抓住单一变量推断的问题。','responsibilities, guidance and opportunities：结尾归纳前文机制。'],
['If a household cannot afford every desired purchase, ... → 假设场景，不声称调查证明。','Such practices may develop the same judgment ... → Such practices回指前一句三项养育安排。'])

w2('wc-official-tourism','利弊权衡','国际旅游：经济收益与社区成本如何比较',off(7,'Task 2B'),
'International tourism has brought enormous benefit to many places. At the same time, there is concern about its impact on local inhabitants and the environment. Do the disadvantages of international tourism outweigh the advantages?',
'写两个主体段，约180–220词；同时覆盖local inhabitants与environment。结尾必须比较影响而非只说“都有优缺点”；不杜撰游客比例或经济统计。',
'International tourism can provide substantial benefits when visitors spend money in local businesses. Hotels, restaurants and transport operators need staff, and smaller enterprises can earn income from guiding, food or crafts. This can be especially valuable in places with few alternative sources of employment. Visitor interest may also give a community an incentive to maintain historic buildings and cultural activities. These benefits are strongest when local residents own businesses or obtain secure jobs, rather than when most revenue leaves the destination through external companies.',
'The costs can nevertheless outweigh those gains where visitor numbers exceed a place’s capacity. Housing converted into short-term accommodation may become less available to residents, while crowded streets and heavy demand for water can disrupt everyday life. Natural sites can also be damaged if waste and access are poorly managed. Unlike an extra sale in a restaurant, the loss of affordable housing or a fragile habitat may be difficult to reverse. I therefore judge the balance to depend on how tourism is controlled: unmanaged expansion can produce greater harm, whereas limits on pressure and a fair local share of income can preserve its advantages.',
['收益讲清谁拿到收入；成本区分居民住房/公共资源与自然环境。','比较标准是影响是否可逆以及承载能力，而非无依据地宣布旅游总是坏。','结尾提供明确的条件性判断：unmanaged expansion时坏处可能更大；管理有效时能保留优势。'],
['收入机制—就业—文化维护—收益归属条件。','居民与环境成本—可逆性比较—条件性权衡结论。'],
['exceed a place’s capacity：把过量客流与损害联系。','a fair local share of income：对应第一段收益归属。','difficult to reverse：权衡的重要性而非数点。'],
['Housing converted into short-term accommodation ... → converted into是后置修饰housing，不是一个新的谓语。','Unlike an extra sale ..., the loss ... may be difficult to reverse. → 比较收益与损失的不同性质。'])

w2('wc-official-science','同意程度','科研由政府控制：公共利益与研究多样性',mod(10,'Task 2'),
'Scientific research should be carried out and controlled by governments, rather than by private companies. To what extent do you agree or disagree?',
'写两个主体段，约170–210词。区分carried out与controlled：政府监督不必等于政府独占全部执行；针对题中的排他性rather than表态。',
'Government involvement in research is essential where the public benefit is large but the prospect of commercial profit is uncertain. Long-term environmental monitoring, for example, may be socially valuable even when no product can immediately be sold. Public funding can support this work and make its findings available for wider use. Governments also have a responsibility to establish ethical rules and require appropriate safety checks. Leaving every decision to firms seeking a financial return could mean that important questions receive too little attention.',
'However, these arguments do not justify excluding private companies from carrying out research. A firm developing a new material or production method may combine specialist knowledge with the ability to turn a discovery into a usable product. If only government bodies conducted research, potentially useful lines of investigation could be lost. I therefore support public oversight and substantial government funding, but not an exclusive government monopoly. Clear standards, transparent reporting and independent review can apply to both public and private laboratories. This arrangement recognises the risks of commercial interests while retaining the different resources and expertise that companies can contribute.',
['第一段支持公共资助与伦理规则；第二段明确反对排除私企。与原题控制/执行两个动作分别对应。','环境监测和新材料为合理例子，没有伪造研究结果或真实机构案例。','立场并非第一段同意、第二段反悔：始终赞成监管，反对政府独占。'],
['公共利益及市场激励不足—政府职责。','私人研发贡献—反对独占—说明公共监督如何与多元执行共存。'],
['public oversight：监督，不等于所有研究由政府亲自完成。','an exclusive government monopoly：准确回应rather than的排他意味。','apply to both public and private laboratories：保持规则一致。'],
['These arguments do not justify excluding private companies ... → These arguments回指公共利益和伦理需求，解释它们不足以推出独占。','... while retaining ... → 同时实现监督和利用不同资源。'])

w2('wc-official-transport','同意程度','鼓励替代交通与国际限车规定',ref('writing-official-transport.pdf','Cambridge / IELTS Academic Writing sample task',1,'Task 2A','官方样题'),
'The first car appeared on British roads in 1888. By the year 2000 there may be as many as 29 million vehicles on British roads. Alternative forms of transport should be encouraged and international laws introduced to control car ownership and use. To what extent do you agree or disagree?',
'写两个主体段，约180–220词：分别回应encourage alternatives和international laws。题干历史预测按原文保留，不当作今天的数据；不只讨论交通污染。',
'I strongly support making alternatives to private cars more attractive. A dependable bus or rail service can give commuters a practical reason to leave their vehicles at home, particularly when routes connect residential areas with major workplaces. Safe walking and cycling routes can serve shorter journeys. Encouragement should therefore involve reliable infrastructure and convenient connections, not merely publicity asking people to change their behaviour. If the available alternatives are slow or unsafe, restrictions on driving may impose a burden without providing people with a workable way to travel.',
'I am less convinced that car ownership should be governed by uniform international laws. A dense city with frequent public transport and a remote community with limited services have very different needs. A single ownership limit could therefore affect people unfairly while failing to target the busiest roads. International cooperation on vehicle emissions may be useful, but local authorities are better placed to decide when and where to restrict car use. Measures such as parking controls or charges in congested areas can be linked to local conditions. I thus agree with encouraging alternatives, while supporting a more locally adaptable approach to regulation.',
['题目两项主张必须分开回答；只谈替代交通会漏international laws。','历史题干中2000年是预测语境；参考段落不把29 million冒充2026年统计。','第二段不是完全反对国际合作，而是质疑统一ownership limits，保持部分同意清晰。'],
['替代交通如何改变行为—必要条件。','国际统一规定的适用差异—地方调节—逐项表态。'],
['a workable way to travel：可执行的出行选择。','uniform international laws：统一规则，准确对应题目。','linked to local conditions：给出监管层级的理由。'],
['If the available alternatives are slow or unsafe, ... → 条件解释为何“鼓励”需要配套。','I thus agree with ..., while supporting ... → 用同一句明确两项主张的不同支持程度。'])

w2('wc-official-eldercare','观点选择','老年照护费用：政府与家庭如何分担',ref('writing-official-elder-care.pdf','Cambridge / IELTS General Training Writing sample task',1,'Task 2','官方样题'),
'In Britain, when someone gets old they often go to live in a home with other old people where there are nurses to look after them. Sometimes the government has to pay for this care. Who do you think should pay for this care, the government or the family?',
'写两个主体段，约170–210词。提出明确分担原则，再解释家庭在何种条件下出资；原题是GT官方Task2，论证训练可迁移到Academic，但不得伪标Academic真题。',
'The government should guarantee essential care for older people who cannot afford it. The need for nursing support may arise independently of how carefully a person has saved, and the cost can exceed an ordinary household’s resources. If access depends entirely on family payments, an older person with poor relatives or no close family could be left without adequate help. Public funding can establish a minimum standard of care and spread this financial risk across society. This is a stronger basis for essential support than making each family bear an unpredictable burden alone.',
'Families can reasonably contribute when they have sufficient resources, but the contribution should depend on their means. Requiring the same payment from a low-income household and a wealthy one would be unfair and might damage the care of other dependants. A means-tested arrangement could protect essential living costs while asking those able to afford additional support to share the expense. Families may also choose to pay for optional facilities beyond the publicly funded minimum. My view is therefore that the state should secure access to necessary care, with family contributions supplementing that guarantee rather than determining whether care is available at all.',
['原题问谁付钱，答案用政府保障底线、家庭按能力补充的可操作原则回应。','没有将“照顾亲人是美德”当成费用分担的全部论据；讨论的是资源、风险和公平。','明确来源为GT官方样题；并非声称这是Academic考试题。'],
['公共保障理由：风险不可预测、家庭资源不均。','按支付能力限定家庭责任，最后重新给出明确分担立场。'],
['depend on their means：means指经济能力。','a minimum standard of care：基本保障而非无限开支。','supplementing that guarantee：补充而非取代公共保障。'],
['If access depends entirely on family payments, ... → 把公平风险与支付规则直接相连。','... rather than determining whether care is available at all → 结尾强调家庭收入不应决定基本照护资格。'])

w2('wc-bc-graduates','原因与措施','高学历毕业生失业：原因和措施一一对应',ref('9464a2d7*.pdf','British Council — Writing Task 2: Developing paragraphs',10,'Worksheet 3','官方教辅'),
'In many countries today there are many highly qualified graduates without employment. What factors may have caused this situation and what, in your opinion, can/should be done about it?',
'写两个主体段，约180–220词：第一段构造两个具体原因，第二段让措施分别对应。原题来自官方IELTS教学材料，保持考试任务，不降低难度；不照抄教辅的示范立场。',
'One reason qualified graduates may struggle to find employment is a mismatch between their education and the requirements of available jobs. A degree can provide substantial theoretical knowledge without giving students enough experience of applying it in a workplace. Employers may consequently hesitate to recruit applicants who need extensive practical training. A second difficulty arises when many students enter the same popular fields while local vacancies are concentrated elsewhere. In that situation, even capable candidates can compete for a limited number of positions, and the possession of a qualification alone does not create demand for their skills.',
'Universities and employers should address the first problem through relevant placements and jointly designed practical projects. These would allow students to demonstrate their abilities and help firms assess potential recruits before offering permanent work. To reduce the second mismatch, students need clearer information about employment patterns and opportunities beyond the most familiar occupations. Careers services could support applications across related industries, while flexible retraining programmes could help graduates acquire additional skills. These measures cannot guarantee a job for every individual, but they respond directly to the gaps in experience and information rather than simply encouraging everyone to obtain another degree.',
['真实题干来自BC教辅第10页；参考论证是重新编写并标明，不冒充官方范文。','原因1缺应用经验→实习/实际项目；原因2热门专业与空缺错配→就业信息/跨行业申请/补充培训。','最后承认措施边界，避免“政府增加工作岗位”这种无机制口号。'],
['两个原因分别说明为什么学历不自动转化为就业。','依次给出对应措施、作用机制和可实现边界。'],
['a mismatch between ... and ...：明确错配双方。','demonstrate their abilities：解释实习为何帮助招聘。','respond directly to the gaps ...：回扣原因而不是另起政策话题。'],
['In that situation, even capable candidates can compete for a limited number of positions ... → even强调个人能力不足不是唯一原因。','These measures cannot guarantee ... but they respond ... → 承认边界仍支持措施相关性。'])

w2('wc-bc-overfishing','原因与措施','过度捕捞：从激励与监管写到对策',ref('609824ad*.pdf','British Council — Writing Task 2: Problems and solutions',7,'Worksheet 1','官方教辅'),
'Overfishing of the world’s oceans threatens many species with extinction and is putting the livelihood of millions of people around the world at risk. What are the causes of this problem and what can be done to prevent it from happening?',
'写两个主体段，约180–220词。第一段写捕捞能力与逐利/监管，第二段分别提出限制和执行机制；同时照顾生态与依靠渔业的社区，不编造研究数字。',
'Overfishing can result from the combination of powerful fishing methods and incentives to maximise the immediate catch. Large vessels and efficient equipment allow operators to remove substantial quantities of fish, while each business may fear losing income if competitors continue fishing. Where catch limits are weak or poorly enforced, individual firms have little reason to leave fish in the sea for future seasons. The problem is intensified when the same stocks move across national boundaries, because restrictions in one area may be undermined by heavy fishing elsewhere.',
'Effective action therefore requires both enforceable limits and cooperation between the authorities responsible for shared waters. Catch quotas and temporary closures can reduce pressure on vulnerable stocks, but they need monitoring and credible penalties; a rule that is routinely ignored changes little. Governments should also support fishing communities during restrictions, for example through assistance in moving towards less damaging practices or alternative sources of income. Without that support, measures designed to protect future livelihoods may face resistance from people struggling to survive now. The aim should be to make sustainable fishing a practical long-term choice, rather than simply announce a ban.',
['原因段没有堆抽象名词：设备提高捕捞能力，竞争激励促使当下多捕，跨界鱼群削弱单方限制。','措施段逐项承接：限额/休渔对应压力，监测/处罚对应执行，跨区域协作对应跨界问题。','livelihood题干范围被保留：过渡支持说明保护鱼群与渔民短期收入怎样协调。'],
['能力—激励—执行薄弱—跨界扩大。','限制—执行—协作—社区过渡支持。'],
['credible penalties：能落实的惩罚，避免只有法规名称。','shared waters：衔接跨界鱼群。','a practical long-term choice：让结论落在可执行性。'],
['... because restrictions in one area may be undermined by heavy fishing elsewhere → because解释国际协调的必要。','Without that support, ... may face resistance ... → 解释社区支持为何不是无关福利。'])

w2('wc-bc-childhealth','原因与措施','儿童肥胖：原因—措施对应而非空泛建议',ref('609824ad*.pdf','British Council — Writing Task 2: Problems and solutions',12,'Worksheet 5','官方教辅'),
'A rise in childhood obesity is a real threat to health with an increasing number of children now classified as overweight. What are the causes of the problem and what measures can be taken to solve them?',
'写两个主体段，约180–220词：解释饮食环境与活动机会两个原因，再分别匹配学校/社区措施。这里练考试论证，不作个人医疗建议，也不写没有来源的研究数字。',
'One contributing factor is that energy-dense convenience foods can be easier to obtain than balanced meals in children’s daily surroundings. Busy households may rely on ready-made options, and frequent promotion of snacks can make these products particularly appealing. At the same time, some children have limited opportunities to be physically active. Long periods spent sitting at school or using screens may be combined with a lack of safe places to play nearby. These circumstances can reinforce one another: an environment that encourages frequent snacking while making activity inconvenient creates persistent difficulties for healthy routines.',
'Responses should make healthier routines easier to maintain, rather than rely only on telling children to show more self-control. Schools can provide balanced meals and practical food education, while clear information for families can help them compare everyday choices. The lack of activity opportunities also needs a direct response. Safe routes to school, accessible play areas and regular opportunities for movement during the school day can reduce barriers to being active. Parents, schools and local authorities each influence part of this environment, so coordinated changes are more likely to be useful than an isolated awareness campaign that leaves the underlying conditions unchanged.',
['原因1食品获取/营销环境→学校均衡供餐和实用信息；原因2活动机会不足→安全路线、场地、在校活动。','不用“kids are lazy”作为单一原因；解释环境如何影响日常选择，避免道德评判。','参考段落是任务论证示范，未用虚构数字、未经核验研究或诊疗建议增加权威感。'],
['饮食与活动环境两个原因，最后交代相互强化。','按同样次序匹配措施，并解释为何宣传单独不够。'],
['contributing factor：因素之一，避免假装唯一原因。','reduce barriers to being active：措施如何起效。','underlying conditions：回指便利食品与活动机会环境。'],
['These circumstances can reinforce one another ... → 指代上文两类环境而非增加新原因。','... rather than rely only on telling children ... → 论证措施应改变条件，不只发口号。'])

for c in CASES:
    assert (BOOK/c['source']['path']).is_file(), c['id']
    assert len(c['modelAnswer'])>=2
    assert c['wordCount']>=145,(c['id'],c['wordCount'])
    if c.get('image'): assert (BOOK/c['image']).is_file()

payload={'schemaVersion':1,'date':'2026-09-19','policy':{'difficulty':'保留正常考试任务，无难度分级','counting':'每道独立原题计一次；同题不同练法不新增计数','writingAnswers':'原创参考写法明确标示，不伪装官方答案','sourceOrder':['Cambridge21真题','官方考试样题','官方IELTS教辅原题']},'summary':{'cases':len(CASES),'independentTasks':len(CASES),'task1':sum(c['skill']=='writing1' for c in CASES),'task2':sum(c['skill']=='writing2' for c in CASES),'modelWords':sum(c['wordCount'] for c in CASES)},'cases':CASES}
(ROOT/'authentic-writing-cases.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(payload['summary'],ensure_ascii=False))
print([(c['id'],c['wordCount']) for c in CASES])

by_id={c['id']:c for c in CASES}
remediations=[]
def replacement(aid,title,ids,body,reason):
    refs=[]
    for cid in ids:
        c=by_id[cid]
        refs.append(dict(label=c['source']['title']+' · '+c['source']['test']+' · PDF '+str(c['source']['page'])+' 页',href=c['source']['path']+'#page='+str(c['source']['page']),local_path=str(BOOK/c['source']['path']),exists=True))
    links='<p class="case-related">对应原题练习：'+' · '.join('<a href="#'+cid+'">'+html.escape(by_id[cid]['title'])+'</a>' for cid in ids)+'</p>'
    remediations.append(dict(auditId=aid,title=title,caseIds=ids,teachingHtml=body+links,newStatus='达标',reason=reason,sourceRefs=refs,
                            verification={'source_traceability':'每题可追溯到本地原始PDF页','composition':'原题/原图保持；参考写法明确原创','context_sufficiency':'保留完整写作题干与完整图形，段落练习不改变原任务','answer_evidence':'下文具体回答与图中数字、题干对象逐项对应'}))

replacement('audit-012','读图起手：用真实就业图核对对象、单位与时间',['wc-c21-t1-jobs','wc-official-bicycle'],'''
<p>先读剑桥21 Test 1 的就业原图。题干的对象是美国四个行业的 <strong>number of jobs</strong>，纵轴是 <strong>millions</strong>，横轴是1960、1980、2000、2020。三个信息决定你只能描述“岗位数随时间变化”，不能写工资、人数占比或失业率。</p>
<p><strong>核对答案：</strong>制造业1960年为15 million，1980年20 million，2000年约17 million，2020年13 million。因此“Manufacturing employment declined throughout the period”不成立：它先升后降。可改成：<em>Manufacturing employment rose from 15 million in 1960 to a peak of 20 million in 1980, before falling to 13 million by 2020.</em></p>
<p>把同一读图动作迁移到官方自行车表格：该表只给June 2011一个时点，行是年龄组，列是male/female。<strong>51.3%是0–9岁男性组的骑车比例，不是所有骑车者中男孩占51.3%</strong>。年龄组差异也不能当成同一批人多年后的变化。</p>
<p>本题先答四项再写：①量的名称是什么？②单位是什么？③横轴是时间还是类别？④能比较的分母是否相同？核对答案分别为就业图的jobs / millions / 时间 / 同一单位岗位数；自行车表为participation / % / 年龄类别 / 各年龄与性别组内部比例。</p>
''','已撤换自编图表，以C21原图和官方原表进行对象、单位及时间口径核验；提供具体错误句及有数据的修正。')

replacement('audit-013','Overview：用真实原图找全局关系，再选择证据',['wc-c21-t4-library','wc-official-audiences'],'''
<p>Overview不是把几个最大数字连在一起。剑桥21图书馆题同时含“用户构成”和“服务满意度”，因此总览应覆盖两种信息。饼图最大项是全日制本科生44%，最小项是academic staff 7%；满意度里staff helpfulness最佳，journals与wi-fi负面反馈最多。</p>
<p><strong>可直接核对的参考总览：</strong><em>Overall, full-time undergraduates formed the largest group of library users, while academic staff accounted for the smallest share. Satisfaction was strongest for staff helpfulness, whereas journals and wi-fi attracted the highest proportions of dissatisfied responses.</em></p>
<p>为什么不在总览里抄完所有数字？主体段才用95% very satisfied与20%/19% not satisfied证明判断。注意表格有三列：不能把“fairly satisfied”与“不满意”混在一起。</p>
<p>再看官方广播/电视折线图。这里最值得写的不是起点都小，而是峰值时段错开、电视峰值更高。<strong>参考总览：</strong><em>Radio attracted its largest audience in the morning, while television viewing peaked in the evening. Television reached a substantially higher peak, and both audiences were small during the early hours.</em>主体证据是广播约27%在早上8点附近，电视约45–47%在晚8点附近。先给关系，再用数据证明关系。</p>
''','已用两道独立官方原题展示总览与证据的对应关系，替代泛化/自编范例；总览覆盖每张图。')

replacement('audit-014','数据精确表达：真实表格里的百分点、比例和近似值',['wc-official-bicycle','wc-c21-t4-library'],'''
<p>官方自行车表格的10–17岁一行：male 42.2%，female 24.6%。<strong>差值标准答案是42.2−24.6=17.6个百分点</strong>。参考句：<em>The male participation rate was 17.6 percentage points higher than the female rate among 10–17-year-olds.</em></p>
<p>“higher by 17.6%”不是同一意思：相对差需要以24.6为基数，(42.2−24.6)/24.6≈71.5%。原题描述没有必要引入这个更复杂的换算；用17.6 percentage points既直接又准确。0–9岁51.3%与50.3%之差则只有1.0个百分点。</p>
<p>剑桥21图书馆表也可核对：staff helpfulness的very satisfied为95%，opening hours为65%，差30个百分点。<em>The proportion who were very satisfied with staff helpfulness was 30 percentage points higher than the figure for opening hours.</em>这是静态比较，不能写“rose by 30 percentage points”，因为题中没有前后年份。</p>
<p>读精确表格按给定小数写；读粗线图用about/approximately。两个不同群体的百分比相加前先检查分母：图书馆25%全日制研究生+16%非全日制研究生可以合为41%，因为二者是同一用户总体中的互斥类别；自行车不同年龄组的比例不能随意相加成总体骑行率。</p>
''','全部数值来自官方原表，验证17.6、1.0、30个百分点及41%合并依据，提供具体参考句与错误边界。')

replacement('audit-015','流程图：真实制砖分支与雨影形成机制',['wc-official-bricks','wc-c21-t3-rainshadow'],'''
<p>先沿官方制砖图的箭头走一次：clay挖出→metal grid / roller处理→加入sand + water→两种成形方式之一→drying oven→两档kiln→cooling chamber→packaging→delivery。最关键的分支词是原图中的<strong>or</strong>，不是then。</p>
<p><strong>分支参考答案：</strong><em>The mixture is shaped into bricks either by a wire cutter or by being placed in moulds.</em>如果写“the bricks are cut and then put into moulds”，就把两条并行路径误写成每块砖都经历的连续操作。</p>
<p><strong>热处理参考答案：</strong><em>The bricks are dried for 24 to 48 hours, then heated first at 200–980°C and subsequently at 870–1300°C. They are cooled for 48 to 72 hours before packaging.</em>这里24–48与48–72不可对调；原图的温度区间确有重叠，应忠实保留。</p>
<p>再看剑桥21雨影图。这里不是人工生产，主要用一般现在时描写自然机制：<em>As moist air rises on the windward side, it cools and clouds form. Rain falls before the dry air continues over the mountain towards inland areas.</em>总览应强调迎风坡降雨与背风坡干燥。原图的thousands of kilometres是空间范围，不能改写成“经过数千年”。</p>
''','以两道真实流程题替代自编循环；分支、数值、自然因果和时空单位均可逐项核验。')

replacement('audit-016','地图题：咖啡厅改造的定位、替换与保留',['wc-c21-t2-cafe'],'''
<p>剑桥21 Test 2给出学院咖啡厅before redesign与today两张平面图。两图没有指北针，也没有将来日期，因此用left/right、near the entrance、below the kitchen定位，使用过去与现在的对照。</p>
<p><strong>功能替换参考答案：</strong><em>The two staff dining rooms along the upper edge of the main seating area have been converted into a takeaway food outlet and a coffee bar respectively.</em>原图左间对应take away food，右间对应coffee bar；respectively要求列举顺序对应，不能只说“更多设施被建了”。</p>
<p><strong>新增与保留参考答案：</strong><em>An outdoor seating area has been added along the bottom of the café, with a barbecue at its left end. The kitchen and toilets remain in their original positions.</em>这同时覆盖扩展与稳定部分。室内原serving area改为hot meals，左墙加salad bar，入口旁bin改recycling bins，均可在两图中找到。</p>
<p>写两个主体段时，一段处理室内服务功能，另一段处理室外扩展和保留设施。不要虚构面积、容量、装修原因，也不要把“today”改成未来计划。下方练习使用同一咖啡厅原题；这里和地图资源单元共用原题，不计为两道独立地图题。</p>
''','自编规划图已由真实咖啡厅前后图替代，明确图上无方位针、无未来规划；具体改造对应有完整参考句。')

replacement('audit-017','咖啡厅改造：在真实两张平面图间建立对应',['wc-c21-t2-cafe'],'''
<p>这次导读使用剑桥21 Test 2的college café原题。先找三类信息：<strong>保留</strong>厨房、厕所与中央座位区；<strong>转换</strong>两间职工餐厅变takeaway与coffee bar、统一服务台变hot meals；<strong>新增</strong>salad bar、outdoor seating及barbecue。</p>
<p><strong>导读问题及参考答案：</strong>“Which changes show a wider range of services?”——<em>The single serving area is now used for hot meals, the former staff dining rooms have become a takeaway outlet and a coffee bar, and a salad bar has been installed.</em>这段说明“服务更丰富”的证据，而不是没有细节地说“the café is more modern”。</p>
<p>“What has remained unchanged?”——<em>The kitchen and toilets are still in the same locations, and the main central area continues to contain tables and chairs.</em>原图没有明确数字，不能写桌椅数量翻倍。写作中保留这些稳定参照物，读者才知道变化发生在哪里。</p>
<p>下方case要求Overview加两段主体；先自己写，再查看完整参考写法，逐句核对位置和变化。此题与地图技巧单元共用，同源练法只算一道原题。</p>
''','删除虚构图书馆导读并换为C21咖啡厅实际图；导读问题有明确有源答案和保留信息，重复引用不虚增题量。')

replacement('audit-018','真实折线图：就业结构变化与受众时段差异',['wc-c21-t1-jobs','wc-official-audiences'],'''
<p>先做剑桥21就业图的比较。1960年制造业15 million最高，医疗2 million最低；2020年零售与医疗均约16 million，并列最高，农业约2 million最低。<strong>主导行业换位</strong>比逐点抄数更值得进入Overview。</p>
<p><strong>主体段参考开头：</strong><em>Manufacturing employment rose from 15 million in 1960 to 20 million in 1980, before declining to 13 million in 2020. In contrast, healthcare grew from only 2 million to approximately 16 million over the period.</em>一升后降与持续增长形成对照；制造业1980年峰值不能遗漏。</p>
<p>换一张独立原图：官方广播与电视受众题。二者比较的是同一日的时段，广播早高峰、电视晚高峰。<strong>参考句：</strong><em>Radio listening peaked at about 27% in the morning, whereas television viewing reached roughly 45–47% in the evening.</em>这题用百分比，不可套前题的million；题中1992是调查背景，横轴仍是一天内时间。</p>
<p>答完后检查三个具体错误：是否把15 million写成15%；是否把广播最高时刻写成电视最高时刻；是否把制造业“先增后减”错误概括为全程下降。两道原题的完整多段参考写法在各自case内。</p>
''','自编交通趋势撤换为两道独立真实折线题，真实单位、峰值和终点比较明确，给出具体参考答案。')

replacement('audit-019','国际旅游：基于官方原题比较环境代价和社区收益',['wc-official-tourism'],'''
<p>使用IELTS官方Task 2B原题：国际旅游带来收益，同时影响当地居民与环境；问题是<strong>Do the disadvantages ... outweigh the advantages?</strong>。这是利弊权衡，不是自编的国际协作/本地执行双边讨论。</p>
<p><strong>立论参考：</strong><em>Unmanaged tourism can create costs that outweigh its benefits when visitor numbers exceed a destination’s capacity.</em>后文必须说明“为什么更重”：住房改成短租影响居民居住，自然栖息地损害可能难以逆转；这类长期代价不能只用一次消费收入抵消。</p>
<p><strong>具体论证片段：</strong><em>Housing converted into short-term accommodation may become less available to residents, while crowded streets and heavy demand for water can disrupt everyday life. Unlike an extra sale in a restaurant, the loss of affordable housing or a fragile habitat may be difficult to reverse.</em>第一句覆盖local inhabitants，第二句加入environment并完成比较，而不是空写“tourism damages the environment”。</p>
<p>另一段要公平交代收益：游客消费支持本地商家和就业，文化维护也可能获益；再讨论收入是否真正留在当地。答后对照case的两段参考写法，找出你的比较标准、利益获得者与受损对象。范例为本册编写的参考论证，题干为官方原文，不是假称的官方高分范文。</p>
''','将无真实题面的环境双边讨论换为官方旅游利弊原题；两类对象与outweigh指令均得到具体回答。')

replacement('audit-020','过度捕捞：真实题干中的原因与措施对应',['wc-bc-overfishing','wc-bc-graduates'],'''
<p>这两个原因措施题均出自British Council官方IELTS教学材料，按原题保留，不冒称剑桥真题。过度捕捞题同时提到species extinction和millions of people’s livelihood，因而生态保护与社区生计都在任务范围内。</p>
<p><strong>原因参考：</strong><em>Powerful fishing methods allow operators to take large catches, while weak enforcement gives individual firms little reason to leave fish for future seasons.</em>这里既有捕捞能力，也有激励和监管，不是只给“people are greedy”标签。</p>
<p><strong>措施参考：</strong><em>Catch quotas and temporary closures can reduce pressure, but they need monitoring and credible penalties. Governments should also support fishing communities during restrictions so that protecting future livelihoods does not leave families without income now.</em>限额对数量压力，监测处罚对执法不足，过渡支持对题干的livelihood。</p>
<p>再迁移到毕业生失业原题：应用经验不足→相关实习及真实项目；求职方向与职位错配→就业信息、跨行业申请和补充训练。不要在原因段谈技能、措施段却只写惩罚企业，两边失去对应。每题下方都有两段约190词参考论证，用同一问题的完整机制检查自己的段落。</p>
''','自编社区安全题撤换为两道可追溯的BC官方IELTS原因措施原题，提供因果链和一一对应解法；来源性质明确。')

replacement('audit-107','Task 2复习：用四道真实题检查任务回应',['wc-c21-t1-homes','wc-c21-t2-entertainment','wc-c21-t3-placement','wc-c21-t4-primary'],'''
<p>复习直接回到剑桥21四道原题，先写自己的两段主体再核对。不要把题型名称当作答案；每题都必须保留范围词和动作要求。</p>
<ol><li><strong>高层住宅：</strong>best way要求评判是不是最佳方案。参考判断为“高层能节省土地，但可负担性与公共设施决定它是否适合，因此有条件赞成”。只写节省土地没有回答best。</li><li><strong>剧院影院：</strong>Discuss both views要求认真解释线上娱乐的便利，同时回应economically与culturally。参考论证分别用时间/地点自由、场馆就业及本地文化共同体验支撑，并明确仍然重要的立场。</li><li><strong>海外学习或实习：</strong>原题为abroad <em>or</em> work placement，不要求两项都做。参考权衡用长期实践能力与可通过资助/本地实习缓解的成本比较，才能完成outweigh。</li><li><strong>小学课堂：</strong>第一问是formal learning是否过多，第二问是play有多重要。参考写法一段讨论正式教学失衡，另一段以假想商店和合作模型解释游戏怎样支持课堂学习，两问各有清楚答案。</li></ol>
<p>每写完一题，给自己的句子标注“回答题干哪一部分”“理由的机制”“具体例子”“例子怎样支持判断”。例如影院题的本地演出带动技术人员岗位对应economically；共同观看本地故事对应culturally。若只写“important to society”，就还没有完成具体展开。</p>
<p>四题的完整双段参考写法、结构和句子精读都在对应case中。复习同一道题属于再次练习，不新增独立题数；所有写作范例均为明确标注的参考写法。</p>
''','复习中的泛化自编题已换为C21四道实际Task2的范围词核验、具体立场和答案机制，配套完整双段case。')

supplements=[dict(auditId='audit-104',preserveOriginal=True,caseIds=[c['id'] for c in CASES if c['skill']=='writing1'],
                  title='补充：8道有源Task 1原题检验同一读图方法',
                  teachingHtml='<p>原复习内容保留为可疑材料；补充练习采用8道独立的真题或官方考试样题。对照真实原图练习对象/单位、Overview、分组与证据：就业与广播电视为折线，继续教育为柱状，自行车为表格，图书馆为饼图+表格，咖啡厅为地图，雨影与制砖为自然/制造流程。答后有完整参考段落、数据核对和句子精读。每题只计一次，重复练法不增加独立材料数。</p>',
                  status='可疑',supplementStatus='达标')]
result=dict(date='2026-09-19',replacements=remediations,supplements=supplements,
            coverageNote='地图在本地材料库379个PDF（按文件内容去重221份）的可提取文本扫描中仅找到C21咖啡厅一道独立写作原题；另一次地图命中为听力题。未拿同图拆分伪增。',
            inventoryEvidence='writing-source-cache/map-inventory.json',
            validation={'replacements':len(remediations),'supplements':len(supplements),'taskCases':len(CASES),'sourceImagesVisuallyChecked':8,'modelWords':sum(c['wordCount'] for c in CASES)})
(ROOT/'writing-remediations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print('Writing remediations:',len(remediations),'supplement:',len(supplements))
