import json
from pathlib import Path

OUT = Path('C:/Users/Admin1/Documents/ChatGPT/ielts/skills-resources.json')
BASE = 'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs'
BC = 'https://learnenglish.britishcouncil.org/free-resources/listening/b1/'
DOWNLOADS = 'D:/IELTS-downloads/2026-09-15-ni-batch-03/'
READING_RULE = 'https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-reading'
WRITING_RULE = 'https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing'
RECENT_WRITING = 'https://howtodoielts.com/recent-ielts-writing-topics-2022/'

def source(title, url=None, local_path=None, kind='official_guidance'):
    s = {'title': title, 'kind': kind, 'verified_at': '2026-09-16'}
    if url: s['url'] = url
    if local_path: s['local_path'] = local_path
    return s

def vocab(phrase, meaning, example, pitfall):
    return {'phrase': phrase, 'meaning': meaning, 'example': example, 'pitfall': pitfall}

def unit(id, section, title, topic, task_type, intro, lesson, task, feedback, transfer, vocabulary, minutes=22, sources=None, media=None, **extra):
    return {'id': id, 'section': section, 'title': title, 'topic': topic, 'task_type': task_type,
            'intro': intro, 'added': True, 'highlight': 'red', 'minutes': minutes,
            'source_note': extra.pop('source_note', '题面、中文讲解、词块例句与解释答案均为本次原创教学；题型规则参考 IELTS 官方页面。不是考试原题，也不据此换算 band。'),
            'sources': sources or [], 'media': media or [], 'lesson_md': lesson, 'task_prompt': task,
            'feedback_md': feedback, 'transfer_prompt': transfer, 'vocabulary': vocabulary,
            'study_balance': {'new_minutes': minutes - 4, 'review_minutes': 4, 'review_optional': True,
                              'note': '先学新资源，再任选两张旧词卡或一道错题提取；到时即可进入下一单元，复习不作为解锁条件。'}, **extra}

def listening_assets(slug, name, mp3, pdf):
    return [source('British Council · '+name, BC+slug, kind='official_general_english'),
            source('配套原课程 PDF（题目、文字稿及答案）', local_path=DOWNLOADS+pdf, kind='official_general_english')], \
           [{'type':'audio','path':DOWNLOADS+mp3,'url':'https://learnenglish.britishcouncil.org/sites/podcasts/files/'+mp3.split('-',1)[1],
             'label':'官方原音 · '+name,'verification':'本地 MP3 与 2026-09-15 下载清单课程来源匹配；本次核对文件和哈希。未制作时间轴。'}]

units=[]
s,m=listening_assets('arriving-late-class','Arriving late to class','48058dc8-LE_listening_B1_Arriving_late_to_class.mp3','dd0f6bb9-LearnEnglish-Listening-B1-Arriving-late-to_class.pdf')
units.append(unit('new-listening-campus-notes','listening','课堂通知：日期、数字与澄清请求','校园与学习安排','笔记填空 / 信息核对',
'把已经储备的校园原音变成可学单元：先抓问题指向，再记日期、页码和缩写。',
'''### 学会给数字找位置
同一段校园对话可能连续出现上课时间、考试返还日、书页和作业要求。数字本身不是答案，必须和它修饰的对象一起保存。听前先画四格：迟到多久／试卷返还日／当前页码／缩写含义。

第一次听不必写完整英文句。先记 10 min、Fri、p. 12 这一类短笔记，听完再整理（这些只是格式示例，不是本课答案）。遇到说话人没听清而让对方重复，这通常是重要信息再次出现的机会；不要因为句子重复就跳过。

### 自编语境示范（非原音文字稿）
“The lecture starts at ten, but please arrive at quarter to ten to collect your worksheet.” 这里要区分活动开始时间与要求到达时间；问 arrive 就不能填 10:00。

看完例句后就可以播放原音。可以随时暂停学习或重听；若要保留首次理解记录，先保存这一遍的答案。''',
'''播放上方 Arriving late to class。下面 4 题为本学习册自编，依据官方原音，非原课程题号。
1. 学生坐下时，老师大约已经讲了多少分钟？
2. 期中试卷将在哪一天返还？
3. 学生此时应翻到第几页？
4. SEO 中的 S 代表哪个英文词？
用短笔记作答；第 4 题只写一个词。再改正一句自编错误：The teacher will hand back them tomorrow.''',
'''1＝约 5 分钟。对方用“刚开始约五分钟”的意思说明已经错过的部分，并非整节课长度。
2＝下周二。这是试卷返还时间，不是考试举行日。
3＝34。把页码和日期分开记。
4＝Search。完整缩写指 Search Engine Optimisation；只问 S 时写 Search 即可。

改错：The teacher will hand them back tomorrow. 代词 them 放在 hand 与 back 中间。可再比较 hand them in（交上去）和 hand them back（还回来）。

错一题只重听对应信息，仍不清楚再开课程文字稿。记录“首次／查稿后”即可；这 4 道自编理解题不换算雅思分数。''',
'任选两项用 2 分钟回忆：说出“交作业”和“退回作业”的区别；把自编通知里的到达时间与开课时间各说一次。随后直接学下一项新资源，不需要四题全对。',
[
vocab('hand something back','把某物还给原持有人','The tutor handed our essays back on Friday.','代词须放中间：hand them back；hand in 表示提交。'),
vocab('be meant to do','按安排应该做','We are meant to read chapter four before class.','meant 后接 to + 动词；不是 mean doing 的“意味着”。'),
vocab('catch what someone said','听清对方的话','I did not catch the room number. Could you repeat it?','此处 catch 不是抓住物体；听懂和同意并不相同。'),
vocab('share something with someone','与某人共用／分享','Can I share this textbook with you today?','使用 share ... with；不要写 share to someone。')],sources=s,media=m,
source_note='British Council B1 通用英语官方原音，非 IELTS 真题。四道理解题、教学和例句为本次原创；日期按录音语境理解，不是当前课程通知。'))

s,m=listening_assets('team-meeting-about-diversity','A team meeting about diversity','bfdbdf7e-LE_listening_B1_Team_meeting_about_diversity.mp3','49206872-LearnEnglish-Listening-B1-A-team-meeting-about-diversity.pdf')
units.append(unit('new-listening-team-roles','listening','会议分工：谁提出顾虑，谁负责执行','工作与团队合作','人物匹配 / 行动顺序',
'从多位说话人的讨论中分清建议、顾虑和最终分工，接上 Part 3 的人物追踪能力。',
'''### 给人名建立稳定标签
在纸上写 Nina／Brenda／Stefano 三列。听到一个建议时，先记它的内容；只有在明确分配任务或答应执行时，才放入“负责事项”。提出建议的人不一定执行它。

### 识别同意之后的保留意见
一句 That sounds good 后面如果跟 but，要继续听顾虑是什么。把顾虑理解成“整个计划被否决”会丢掉后续推进。动作还有先后：讨论先提到 workshops，并不一定意味着 workshops 最先开展。

### 自编语境示范（非原音文字稿）
Mia: “We could invite a guest speaker.” Jo: “Good idea. I can book the room, but could you contact the speaker?”
问谁安排场地，答案是 Jo；Mia 先提出的想法并不能推出她负责所有事。

词块先看意思即可，不必背完才播放。''',
'''听官方原音，完成本学习册自编匹配。人物可以重复使用：A Nina，B Brenda，C Stefano。
1. 担心员工只把新文件看成管理层的产物。
2. 负责寻找合适的培训师。
3. 负责寻找不同于普通研讨会的有趣场地。
4. 负责查找其他机构利用团队差异的经验。
5. 将计划的活动排序：收集员工点子的 workshops；让大家体验差异价值的 team-building sessions。
6. 自编迁移：上方示范中 Jo 同意负责什么？''',
'''1＝B；Brenda 的顾虑是参与感和实际关注度，不是说团队完全没有差异。
2＝C；Nina 把寻找培训师的行动明确交给 Stefano，他答应执行。
3＝B；Brenda 接到找场地的任务。不要把“培训师”和“培训地点”合并。
4＝A；Nina 自己继续查其他机构的经验。
5＝先 team-building sessions，再 workshops。会话先提到后者，随后补入“在那之前”的活动，要按实际计划排序。
6＝book the room。联系嘉宾是她请 Mia 做的另一项任务。

若人名匹配错，重听最后明确分工的一轮；若顺序错，重听插入先行步骤的位置。答案均依据原课程文字稿核对，题目是本学习册自编。''',
'下次开始新课前，盖住词卡，用 involve 与 be responsible for 各说一句自己的团队分工。任选一题重新解释证据，4 分钟到就结束复习。',
[
vocab('involve someone in doing','让某人参与做某事','We involved volunteers in choosing the workshop topics.','in 后接名词或动名词：in choosing，不是 in choose。'),
vocab('be responsible for','负责某事','Ravi is responsible for booking the meeting room.','for 后的动作使用 booking；responsible 不是动词。'),
vocab('specialise in','专门从事／擅长某领域','The trainer specialises in helping new teams communicate.','in 后接领域或动名词；美式 specialize 也正确。'),
vocab('make the most of','充分利用已有机会或资源','We made the most of the short meeting by preparing questions.','保留 the；不等于拥有最多数量。')],sources=s,media=m,
source_note='British Council B1 官方通用英语会议原音；非 IELTS Part 3 真题。人物匹配和排序题为原创教学应用。'))

s,m=listening_assets('weather-forecast','A weather forecast','4c87696e-LE_listening_B1_A_weather_forecast.mp3','aeff8f08-LearnEnglish-Listening-B1-A-weather-forecast.pdf')
units.append(unit('new-listening-weather-table','listening','天气播报：地区、时间与例外条件','天气与出行','表格笔记 / 地区信息定位',
'一次听懂播报中的地区切换与天气变化，避免把某一城市的情况套到全国。',
'''### 让每一条信息同时有地点和时间
天气播报不是一串形容词。建立“地点｜时间｜天气／数值”三列，听到新的地名就换行。north-west 与整个 north 不完全相同；today 与 by the weekend 也不是同一个时间窗口。

### 用转折更新状态
already cleared、will clear、will remain 表示不同时间关系。一个地方早上有雨而午后转晴并不矛盾。特别留意 escape、elsewhere、at least 这类范围或例外信号。

### 自编语境示范（非原音文字稿）
“Rain will reach the western hills tonight. The coast, however, will remain dry until morning.”
可以记成 hills／tonight／rain；coast／until morning／dry，而不是写“今晚所有地方下雨”。原音数字只代表课程内的预报，不作为现实天气服务。''',
'''听原音，填写以下自编信息表。可以先用中文，不限制词数。
1. Leeds 今天余下时间及今晚：雷暴，还是毛毛雨／小雨？
2. 接近 Wales 的一些地方今天可能出现什么？
3. 播报中本周较高气温给出的具体范围是多少度？
4. 按预报，雨最迟到什么时候会抵达 south coast？请写出星期及上午／下午。
5. 周末大约多少度？
6. 改写自编句而不扩大范围：A few western villages may have showers.（使用 some 与 might）''',
'''1＝毛毛雨／小雨。播报特意把 Leeds 与会有雷暴的地点区分。
2＝局部雾。是靠近 Wales 的一些地方，不能扩成所有地区全天有雾。
3＝29–30 度。后文还用较宽泛的高二十多到三十出头概括本周热度；此题问明确报出的范围。
4＝截至周六下午／不晚于周六下午。原音说 by Saturday afternoon，说明最迟到达时间，没有给出精确抵达时刻；不能改述为只在周六下午抵达。
5＝约 21 度。比本周较热时段低，但播报仍称温暖。
6＝Some western villages might have showers. 保留部分地点和可能性。写 All villages will have rain 就同时扩大了范围、提高了确定性。

错因优先标“地点串行／时间串行／程度变强／数值没听清”。只重听一个最不稳的格子即可。''',
'用 3 分钟凭记忆说一条带地点和时间的自编预报，再用 clear up 与 make way for 各造一句。可以跳过数值复测并进入新资源。',
[
vocab('clear up','天气转晴／某问题澄清','The clouds should clear up by late afternoon.','天气语境是变晴；不要机械理解成打扫。'),
vocab('isolated showers','局部零星阵雨','There may be isolated showers near the hills.','isolated 限定分布；不能改述成持续、普遍降雨。'),
vocab('throughout the day','在整天期间','Light rain continued throughout the day.','throughout 强调遍及某时间段；不等于 by the end of。'),
vocab('make way for','让位于／被随后事物替代','The morning mist made way for sunshine.','made way for sunshine 不表示阳光造成雾。')],sources=s,media=m,
source_note='British Council B1 官方通用英语原音；不是 IELTS 当季题库或今天的实际天气。表格问题与例句为原创，答案按原课程语境核对。'))

s,m=listening_assets('introduction-lecture','An introduction to a lecture','4b345c07-LE_listening_B1_An_introduction_to_a_lecture.mp3','043b93eb-LearnEnglish-Listening-B1_An-introduction-to-a-lecture.pdf')
units.append(unit('new-listening-lecture-outline','listening','讲座导入：定义、例子与后文路线','心理学与专注','讲座结构 / 提纲排序',
'从短讲座建立定义和例证意识，再追踪 First／Then／Finally 所指的后续结构。',
'''### 先识别句子在做什么
讲座可能先提出问题，再给概念、解释概念、举例，最后预告后文。笔记时用“问题／定义／例子／后文安排”标签；一句提到艺术家的话可能只是例子，并不是整节课的研究对象。

### 复述定义时保留关键条件
下定义常出现 means、refers to 或 in other words。后一句可能只是同一概念换个说法，不必另开一个新主题。反过来，will look at 往往预告尚未展开的内容。

### 自编语境示范（非原音文字稿）
“By active listening, I mean checking that you understand the speaker. For example, you might briefly repeat the main point. Later, we will consider situations in which this is difficult.”
三句话分别承担定义、例子、后文预告。听本课时，不必先掌握专有姓名的拼写；抓住它指的是谁以及其理论内容就可以继续。''',
'''播放原音，完成 5 道自编题。
1. 这门新课总体属于什么学科方向？
2. 用中文概括讲座给出的 flow 状态，必须提到人与活动的关系。
3. 讲者用哪类人的工作作为启发理论的例子？A 运动员，B 艺术家，C 医生。
4. 给后文三部分排序：a 日常达到这种状态的活动；b 研究者生平与思想形成；c 产生这种状态的条件。
5. 讲者是否明确保证听完整门课就会终身快乐？指出确定性依据。''',
'''1＝积极心理学，关注如何帮助人更快乐。
2＝完全投入／专注于正在做的活动。单说“心情好”没有说明本课定义的核心关系。
3＝B。工作室里艺术家专注工作是说明理论来源的例子。
4＝b → c → a。最后的路线预告依次是生平、条件、日常活动。
5＝没有。讲者结尾保留不确定性，而非作出保证。

这一课的说法按录音中的理论介绍理解，不把它当作关于幸福的唯一科学结论。若顺序出错，只重听结尾的路线预告；若定义不完整，找定义的改述句即可，不必重听姓名很多次。''',
'下次学新课前用自己的话说一个“定义＋例子”，再背对材料口头给一场虚构演讲安排 first／then／finally。2–4 分钟即可。',
[
vocab('be absorbed in','全神贯注于','I was absorbed in drawing a map and forgot the time.','in 后接名词或动名词；不要写 absorbed on。'),
vocab('lose track of time','忘记时间的流逝','She lost track of time while repairing the bicycle.','lose 的过去式是 lost；常用 track 不加 the。'),
vocab('in other words','换句话说','The task needs no equipment; in other words, you can do it anywhere.','应保持同一意思，不能用它连接无关的新论点。'),
vocab('be associated with','与……相联系','The course is associated with practical skills.','association 不等于因果证明；with 后接关联对象。')],sources=s,media=m,
source_note='British Council B1 官方通用英语讲座原音，适合作为 IELTS 学术听力的基础训练。原创理解题；非 IELTS Part 4 原题。'))

units.append(unit('new-reading-urban-tfng','reading','城市绿化：区分反证与尚未提供的信息','城市与环境','True / False / Not Given',
'用一篇完整原创短文同时练范围、时间和因果，不靠题目里出现同一个词来猜答案。',
'''### 判定的是整条陈述
先拆成“对象＋行为／关系＋范围＋时间”。支持整条陈述才是 True；原文给出相反信息是 False；关键关系没有交代是 Not Given。不要用城市常识补空缺。

### 原创短文：A tree trial in Bellford
In 2024, Bellford Council began a small trial to find out whether additional trees could make a shopping street more comfortable in summer. Twelve young trees were planted on the eastern side of Market Street. The western side was left unchanged so that the two sides could be compared. Both sides already had several older trees.

During August, volunteers recorded the air temperature at four points on each side every afternoon. They also asked shoppers whether the street felt pleasant. People standing close to the new trees often reported greater comfort, even on days when the air-temperature difference between the two sides was small. The volunteers did not measure the temperature of the pavement.

The council published these early findings in October. It did not claim that the trial proved that all shopping streets would benefit equally. Some of the new trees still needed extra watering, and their roots had only begun to develop. A second summer of observations was planned before any decision about expanding the scheme. The report listed the cost of planting but gave no estimate of future maintenance costs.

Bellford、项目与数据均为自编教学情境。先读懂材料，再做题；可以直接学习，无需先做测试。''',
'''根据短文判断 True / False / Not Given，并给每题写一句证据概括。
1. Twelve new trees were planted on each side of Market Street.
2. There were some trees on the western side before the trial.
3. Volunteers measured pavement temperatures during August.
4. Greater comfort was sometimes reported despite a small difference in air temperature.
5. Future maintenance was expected to cost more than planting.
6. A decision about expanding the scheme was to follow another summer of observations.
再改正自编句：The pilot prove that trees always reduces heat.''',
'''1＝False。十二棵新树只种在东侧，each side 扩大为两侧都有。
2＝True。第一段明确两侧原本都有旧树；unchanged 不等于没有树。
3＝False。第二段直接说没有测量路面温度。不能因为测了空气温度就改成 Not Given。
4＝True。第二段把舒适感与两侧空气温差较小的日子联系起来；不是声称温差为零。
5＝Not Given。报告没有给将来维护成本估计，因此无法比较哪个更贵。提到 planting cost 不足以回答这个关系。
6＝True。扩大计划的决定安排在第二个夏季观察之后。

语法和意义共同修订：The pilot suggests that trees may improve comfort in some conditions. 原句语法有 prove／reduces 搭配问题，意义上的“证明、总是、降温”也超出材料。''',
'任选第 3、5 题说清区别：“明确没测”和“没提供比较”为什么不同？再把 maintenance 与 expand the scheme 用到自己的例句。约 4 分钟，复习可跳过。',
[
vocab('leave something unchanged','让某物保持不变','The designers left the main entrance unchanged.','unchanged 不是没存在过；leave 的过去式 left。'),
vocab('despite + noun / -ing','尽管存在某情况','Visitors stayed outside despite the light rain.','despite 后不直接接完整句；可用 although it rained。'),
vocab('maintenance costs','维护成本','The club needs to budget for maintenance costs.','maintenance 不可直接作动词；maintain 是动词。'),
vocab('expand a scheme','扩大一项计划','The school may expand the scheme to other classes.','expand to 指扩展到某范围；不得把计划写成已完成。')],
sources=[source('IELTS 官方：识别信息判断题',READING_RULE)],reading_text_original=True))

units.append(unit('new-reading-refill-summary','reading','循环消费：摘要填空与加工流程','消费与资源循环','摘要填空 / 词性与字数',
'看懂容器回收流程，并学会将正确原词放进改写后的句子，保持词性、单复数与字数一致。',
'''### 先判断空格在句子里做什么
填空不是找一个同主题名词。先看空格前后：a 后通常接单数可数名词；are 后可能需要过去分词；with 后常接名词。题目要求取自原文时，答案不能随意换同义词。

### 原创短文：A returnable-container trial
Three cafés in the fictional town of Northwick joined a trial for returnable lunch containers. Customers paid a small deposit when collecting a meal. They could return the empty container to any café in the group, where staff recorded its identification number. A damaged container was removed from use rather than sent back into circulation.

At a central washing station, workers first sorted the containers by size. They then washed them with detergent and hot water. After drying, each container passed through an inspection. Containers that still had visible marks were washed again. Clean ones were packed into sealed boxes and delivered to the cafés the following morning.

The project counted how often containers were used, but it did not calculate the environmental impact of every delivery journey. The organisers therefore described lower use of disposable packaging as one possible benefit, rather than claiming that the system was better under all conditions. They also kept a small supply of disposable boxes for customers who did not wish to join the trial.

detergent＝洗涤剂。所有场景与流程为原创，不作为真实行业研究。''',
'''Complete the summary. Choose NO MORE THAN TWO WORDS from the passage for each answer.
Customers initially paid a 1 ______. Staff noted each returned container's 2 ______. At the washing station, containers were sorted according to 3 ______ and washed using hot water and 4 ______. An 5 ______ took place after drying. Approved containers were transported in 6 ______.

最后回答：原文是否支持“每一次配送都比使用一次性盒更环保”？用一句中文说明缺少什么证据。''',
'''1＝deposit；冠词 a 后需要名词，small deposit 也在两词以内且意思正确。
2＝identification number；number 单独也可接受，因为 container\'s number 与原文相符且符合字数。完整词组含义最明确，需要“记录的对象”，不是客户名字。
3＝size；by size 改写成 according to size。
4＝detergent；原文把 detergent 与 hot water 并列，不要重复填 hot water。
5＝inspection；a/an + 名词，inspect 是动词不能直接填。
6＝sealed boxes 或 boxes；两者都取自原文、满足字数且填入后准确。sealed 补充状态，但题干没有要求必须写这一限定。保留复数 boxes。

不能支持“每次配送都更环保”。原文没有计算每一趟配送的环境影响，也明确保留条件。减少一次性包装只是项目可能的一个好处。

若定位正确却填错，检查字数和句法，而不是重新通读全文。练习总分可记 6，不换算 band。''',
'遮住文章，说出四步：分类、清洗、检查、打包；再把 inspection 改成对应动词写句子。随后转到新材料，避免把背熟这六个空当作新阅读能力。',
[
vocab('pay a deposit','支付押金','Customers pay a deposit before borrowing a tool.','deposit 在此可退押金，不一定是商品最终价格。'),
vocab('remove something from use','停止使用某物','The staff removed the cracked cup from use.','from 后接状态；remove 不必总翻译成物理搬走。'),
vocab('pass through an inspection','经过检查','Each repaired bicycle passes through an inspection.','inspection 是名词；inspect 是动词。'),
vocab('under all conditions','在所有条件下','The method does not work under all conditions.','all 是强限定，不应把某次成功改写成普遍有效。')],
sources=[source('IELTS 官方：摘要与流程填空',READING_RULE)],reading_text_original=True))

units.append(unit('new-reading-transport-information','reading','社区交通：找到例子、限制与纠正信息','交通与公共服务','信息匹配',
'补足“找具体信息”训练，用四段原创材料学习一段可以承载多条题目线索。',
'''### 问的是信息位置
每题先标功能：例子、原因、限制、纠正，还是比较？再读段落找承担该功能的句子。不必先给每段选一个标题，也不要假设一段只用一次。本单元题目明确允许字母重复。

### 原创短文：A community minibus
A. The village of Merefield introduced a minibus after its regular bus service was reduced. The new service was intended mainly for residents who found it difficult to reach shops and the railway station. It was not designed to replace every journey previously made by the old bus. A volunteer committee drew up the timetable after asking residents which destinations they used most often.

B. Bookings could be made online or by telephone. One resident, Mrs Patel, usually phoned because her internet connection was unreliable. She could book several journeys during the same call. The organisers said this option was essential: a service intended to improve access should not require every passenger to be confident online.

C. At first, the committee advertised twelve passenger seats on each trip. It later corrected the notice because space had to be reserved when a wheelchair user travelled. The number of available seats therefore depended on the bookings. Drivers also needed advance notice if a passenger required assistance getting on board.

D. In the first month, demand was highest on market days. Rather than adding trips throughout the week, the committee introduced an extra Tuesday morning service. It planned to review the timetable after three months. The report mentioned fuel costs but did not compare them with the cost of running the former bus service.

地名、人物与方案均为原创。''',
'''Which paragraph contains the following information? Write A, B, C or D. You may use any letter more than once.
1. A correction to an earlier statement about capacity.
2. An example of a passenger using a non-digital booking method.
3. A response to particularly strong demand on one day.
4. An explanation of why two booking methods were necessary.
5. A limit on what the new service was intended to replace.
6. A requirement to notify the service about help needed by a passenger.
任选两题，把题干关键词和原文对应表达配成一对。''',
'''1＝C。先宣传十二席，后因轮椅空间更正，符合 correction 的功能。
2＝B。Mrs Patel 的电话订位是一个具体例子。
3＝D。市集日需求高，所以增加周二上午班次；不是整周普遍加班。
4＝B。为网络不稳定或不熟悉网络的人保留电话，解释两种渠道的必要性。B 可以用两次。
5＝A。新车并不接替旧公交过去的每一趟行程，这是一项范围限制。
6＝C。需要协助上车时，应提前通知司机。

替换例：capacity 对应 number of available seats；non-digital booking 对应 phoned。题干换词并不妨碍同义定位。

如果把第 4 题选 A，说明只抓“询问居民”这一主题词，没核对“两种订位方法”的关系。''',
'盖住题目，从 B 段自己出一道“找原因”的中文题，再用 advance notice 造句。约 3 分钟，随后继续新学。',
[
vocab('be intended for','为某类人设计／准备','The workshop is intended for beginners.','intended 是设计目的，不能推出只可能由这些人使用。'),
vocab('draw up a timetable','拟订时间表','The team drew up a timetable after checking availability.','draw up 此处不是画图；过去式 drew up。'),
vocab('reserve space for','为某人或某物预留空间','The organiser reserved space for wheelchair users.','reserve 不意味着座位已被每个乘客预订。'),
vocab('give advance notice','提前通知','Please give advance notice if you need assistance.','advance 在此作定语；不要写 advanced notice。')],
sources=[source('IELTS 官方：信息匹配与标题匹配区别',READING_RULE)],reading_text_original=True))

units.append(unit('new-reading-ai-views','reading','数字学习工具：作者观点与他人主张','教育与科技','Yes / No / Not Given',
'把作者态度、他人宣传与事实信息分开，练习让步和条件中的立场判断。',
'''### 先标出观点是谁说的
Some companies claim 后面的说法属于公司；作者随后支持、反对或保留，才决定作者态度。句子里有正面词语也不代表作者赞成所有用途。根据本题要求填写 Yes／No／Not Given。

### 原创短文：Tools that answer too quickly
Digital study tools can now suggest explanations almost as soon as a learner asks a question. Some developers argue that this makes independent practice unnecessary. I find that claim unconvincing. An explanation may look clear on a screen while the learner remains unable to use the idea in a different situation.

This does not mean that such tools have no educational value. They can provide another example when a textbook explanation is difficult, and they can help a learner locate a mistake. The important decision is when to ask for help. I would encourage students to make an initial attempt and then use a tool to examine the point at which they became stuck. Requiring students to struggle indefinitely, however, would be just as unhelpful as supplying every answer immediately.

Schools should also examine whether a tool explains its suggestions. A fluent answer is not automatically a reliable one. Teachers can ask students to compare an explanation with a worked example or to justify a result in their own words. This gives a reason for using the tool without treating its output as final authority. I would judge a product by how well it supports these learning activities, rather than by the speed with which it produces answers.

本文观点与例子为原创教学讨论，不是产品评测或研究报告。''',
'''Do the following statements agree with the views of the writer? Write YES, NO or NOT GIVEN.
1. Clear explanations on a screen remove the need for independent practice.
2. Digital tools can be useful when a textbook explanation is difficult.
3. Students should continue struggling for as long as necessary before receiving any help.
4. A tool's fluency is sufficient evidence of reliability.
5. Most teachers currently ask students to justify results in their own words.
6. The value of a product should be judged by the learning it supports rather than answer speed alone.
再指出：第一段 developers 的立场和作者立场相同吗？''',
'''1＝NO。作者明确不相信“独立练习不再必要”的主张；不要把开发者的说法算给作者。
2＝YES。第二段承认难懂时可提供其他例子。
3＝NO。作者反对无限期挣扎；建议先尝试不等于永远不求助。
4＝NO。第三段明确流利不自动等于可靠。
5＝NOT GIVEN。can ask 是作者提出的可用做法，并未统计多数老师当前是否这样做。
6＝YES。结尾优先评价对学习活动的支持，而不是出答案速度。

两方立场不同。作者保留工具的辅助价值，同时反对因此取消独立练习。用“他完全反对科技”概括，会把有限度支持变成绝对否定。''',
'复习任选两题：用“说话者＋立场”复述第 1 题；解释第 5 题中 can 与 currently do 的区别。再学一个新话题，不需要整篇复测。',
[
vocab('find a claim unconvincing','认为某个主张缺乏说服力','I find the claim unconvincing because no example is provided.','find + 宾语 + 形容词；不是 claim is unconvince。'),
vocab('make an initial attempt','先作一次尝试','Learners can make an initial attempt before asking for help.','an initial attempt 不表示必须一次成功。'),
vocab('justify a result','说明结果为什么成立','Please justify the result with a calculation.','justify 要给理由；重复答案本身不足以 justify。'),
vocab('rather than','而不是／取舍比较','We assessed the quality rather than the length of the response.','两侧语法尽量平行；不要把句中比较扩大为全盘排斥。')],
sources=[source('IELTS 官方：识别作者观点',READING_RULE)],reading_text_original=True))

units.append(unit('new-writing1-library-map','writing1','地图改造：新增、替换与保留','公共空间与图书馆','Task 1 地图对比',
'补齐地图题的完整题面、概述、位置表达、整篇示范和新情境应用。',
'''### 先建立同一参照系
下面两张为原创教学地图，北在上，入口都在南边中央。每格表示相对位置，不代表面积比例。

| 2010 年 | 西侧 | 中部 | 东侧 |
| --- | --- | --- | --- |
| 北部 | Book shelves | Book shelves | Storage room |
| 中部 | Reading tables | Reading tables | Staff office |
| 南部 | Reception | Entrance | Car park |

| 2025 年 | 西侧 | 中部 | 东侧 |
| --- | --- | --- | --- |
| 北部 | Book shelves | Book shelves | Study room |
| 中部 | Reading tables | Computer area | Staff office |
| 南部 | Reception | Entrance | Garden |

### 概述与分组
先概括整体从传统阅读设施增添数字与学习空间，部分空间重新分配，同时入口与若干功能保留。细节按“北／中”和“南／保留项”分组，都比按格子逐个报数容易读。

过去两个时间点通常用过去时。was replaced by 表示原来的设施被新的替代；was converted into 强调空间改成另一用途。图未给建筑面积、座位数或设计原因，不补写。

可用开头：The maps show how a small library changed between 2010 and 2025. 后面的示范是完整原创回答，不是官方评分范文。''',
'''原创 Task 1 题目：The maps show changes to a small public library between 2010 and 2025. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.

可先用 10 分钟写概述＋两项变化（60–80 词），也可选完整模式写至少 150 词。先核对北方和南侧入口，再写；地图没有面积数值。

用法练习：将 A garden replaced the car park. 改成以 The car park 开头的被动句。''',
'''### 内容核对
三项变化是东北 storage→study room；中间 reading tables→computer area；东南 car park→garden。西侧阅读桌、北部书架、东侧员工办公室、西南前台与入口保留。

被动句：The car park was replaced by a garden. 不能写 was replaced to。

### 完整原创示范（不是官方范文或承诺分数）
The maps show how a small public library changed between 2010 and 2025, including the arrangement of facilities around its southern entrance.

Overall, the library gained a dedicated study room and a computer area, while the car park became a garden. Despite these changes, the entrance, reception, staff office and northern book shelves remained in their original locations.

In the northern part of the building, book shelves continued to occupy the western and central sections. The storage room in the north-east, however, was converted into a study room. Further south, the reading tables in the central section were removed to make room for computers. The tables to the west were retained, so the library still provided a separate area for reading.

The most noticeable change in the southern part was on the eastern side, where a garden replaced the car park. The entrance stayed in the middle of the southern boundary, with reception immediately to its west. The staff office also remained on the eastern side, between the new study room and the garden.

修订只优先处理一个最影响读者复原地图的问题：替换方向写反、方位错、或把保留项写成新增。''',
'隔日可用 4 分钟改写三句：was converted into、remained、to the east of。新情境：把学校北侧仓库改成音乐室，其余不变，写一个变化句和一个保留句；不要求重新写整篇。',
[
vocab('be converted into','被改造成另一用途','The garage was converted into a classroom.','into 引出新用途；不要把新旧对象写反。'),
vocab('be replaced by','被……取代','The old desk was replaced by a reception counter.','by 后为新设施；replace A with B 的主动结构不同。'),
vocab('remain in its original location','保留在原来的位置','The entrance remained in its original location.','remain 通常不使用被动：不用 was remained。'),
vocab('make room for','腾出空间给','Two tables were removed to make room for computers.','room 这里不可数；不是 make a room 的建一间房。')],
sources=[source('IELTS 官方 Academic Writing 任务与要求',WRITING_RULE)],writing_mode='complete_original_task_and_model',minutes=25))

units.append(unit('new-writing1-transport-trends','writing1','趋势图：增长幅度、主次关系与百分点','交通方式变化','Task 1 时间序列表格',
'用完整原创数值题面练概述和比较，补足只有柱状图、流程局部片段的覆盖。',
'''### 原创数据题面
下表为虚构城市 Cedarford 成年居民在某年“主要通勤方式”的比例，每年总计 100%。数据为教学自编，不是真实调查。

| 主要通勤方式 | 2010 | 2015 | 2020 | 2025 |
| --- | --- | --- | --- | --- |
| Car | 60% | 54% | 46% | 40% |
| Bus | 25% | 28% | 31% | 35% |
| Bicycle | 10% | 12% | 17% | 20% |
| On foot | 5% | 6% | 6% | 5% |

### 概述先说方向和大小
汽车比例下降但始终第一；公交与自行车上升；步行总体稳定并最小。图里没有排名反转，因此不要为了写 overtook 而编一个。数据题不必包含每一种可能的高级表达。

汽车从 60% 到 40%：减少 20 个百分点（percentage points），相对起点约减少三分之一。自行车从 10% 到 20% 才是翻倍。不要把 increase by 与 increase to 混用，也不要把所占比例直接说成总人数减少。

### 一句准确比较
By 2025, cars accounted for 40% of main commutes, compared with 35% for buses. 这句比较相同年份、相同指标，避免跨组错配。''',
'''原创 Task 1 题目：The table shows the percentages of adults in Cedarford using four forms of transport as their main way of commuting between 2010 and 2025. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.

选短练习（一个概述＋两组数据，60–90 词）或完整至少 150 词。另完成：
1. Cycling rose ___ 10% ___ 20%. 填两个介词。
2. Car use fell by 20 percent. 若要表达绝对份额差，应改哪两个词？
3. 表格能否证明城市汽车通勤人数减少？''',
'''1＝from／to。也可说 rose by 10 percentage points，但不能 rose by 20% 表示终值。
2＝20 percentage points。40/60 所得相对降幅约为 33.3%，与份额差不同。
3＝不能。各年成年居民总数未提供，比例减少不必然意味着人数减少。

### 完整原创示范
The table compares the proportions of adults in Cedarford who used cars, buses, bicycles and walking as their main means of commuting in four years from 2010 to 2025.

Overall, travelling by car became less common in proportional terms but remained the leading choice throughout. The shares for both buses and bicycles increased, whereas walking accounted for the smallest proportion and showed little overall change.

In 2010, 60% of adults mainly commuted by car, more than twice the figure for buses, at 25%. The car share then fell at each recorded point, reaching 54% in 2015 and 46% in 2020 before ending at 40%. In contrast, bus use rose steadily to 35% in 2025. Consequently, the gap between these two methods narrowed from 35 percentage points to just five.

Cycling also gained ground, with its share doubling from 10% to 20% over the period. Its largest increase between the years shown occurred from 2015 to 2020, when the figure went from 12% to 17%. Walking varied only slightly, rising from 5% to 6% and then returning to its initial level by 2025.

数据示范没有解释燃油价格、交通政策等图外原因。若你换成其他准确分组与表达，也可接受。''',
'下次复习 3 分钟：不用全文，口头说 from／to 与 by 的区别。新数据：会员比例 15%→25%，写终值、百分点变化各一句。答案是 rose to 25% 与 rose by 10 percentage points。',
[
vocab('account for','占某一总量的比例','Buses accounted for 35% of main commutes in 2025.','不加被动：不要写 were accounted for 35%。'),
vocab('percentage points','百分点','The share increased by five percentage points.','百分点差与相对百分比变化不同。'),
vocab('narrow the gap','缩小差距','The gap between the two groups narrowed over time.','比较必须是同一指标；gap 从 35 到 5 才是缩小。'),
vocab('return to its initial level','回到最初水平','The figure returned to its initial level in the final year.','return to 后是回到的水平；不等于一直没变化。')],
sources=[source('IELTS 官方 Academic Writing 格式',WRITING_RULE)],writing_mode='complete_original_task_and_model',minutes=25))

units.append(unit('new-writing2-environment-discussion','writing2','环境治理：国际协调与本地执行','环境与国际合作','Task 2 讨论双方与观点',
'参考 2026 年有日期的非官方写作回忆主题，改写成完整原创讨论题，练双方机制和有条件立场。',
'''### 近期主题来源和本题边界
How to do IELTS 的列表把环境治理应由国际机构还是各国承担的观点题标记为 2026 年 3 月 25 日考生回忆。该信息没有官方题目确认，不能保证复现。本单元只采用主题，改成“讨论双方”题型，并用原创题面与范文训练。

### 把双方的有效范围说清楚
国际协调的理由可以是跨境影响：一国减少排放的努力可能被邻国抵消，因此共同标准、数据共享有帮助。本地执行的理由是具体条件不同：地形、产业和公共服务各异，同一条操作规则可能不适合所有地方。

写两边时，每边都解释为什么，不要给第一方真正的论证，第二方只写 Some people disagree。个人观点可以主张两级分工，但必须说明由谁做什么，而不是空泛说“二者都重要”。

### 原创展开示范
A shared river illustrates the need for coordination: action upstream can affect people downstream. Local agencies, however, may be better placed to inspect individual factories. 这是合理情境说明，不是捏造某份研究。

完整回答至少 250 词；本次也可只学习词块、结构和一段，再继续其他新资源。''',
'''原创改编题（不是回忆原句）：Some people believe that international organisations should lead efforts to protect the environment. Others think national and local authorities should take the main responsibility. Discuss both views and give your own opinion.

先写两个机制箭头：国际协调为何有用；本地执行为何有用。再选 90–120 词段落练习或至少 250 词整篇。

用法题：补全 Governments should cooperate ___ one another ___ reducing pollution.；改正 Local authorities is familiar with the area.。''',
'''介词为 with／on（cooperate with one another in reducing pollution 也可接受）；主谓修正为 Local authorities are familiar with the area. authority 作机构时注意单复数。

### 完整原创示范
Environmental damage often extends beyond the place where it begins. Some people therefore favour international leadership, while others believe that national and local authorities should take primary responsibility. In my view, international bodies should coordinate shared goals, but the practical work should usually be carried out by authorities closer to the problem.

There are clear reasons for international involvement. Pollution in a river can travel across a border, and emissions from one country can affect conditions elsewhere. If governments act entirely independently, one country's efforts may be weakened by another's inaction. An international organisation can help them agree on common standards and share information. It can also provide a forum in which countries with different resources negotiate what each is able to contribute. These functions are difficult for a single national government to perform on behalf of all its neighbours.

However, local knowledge is essential when an agreement is put into practice. Officials who understand an area's industries and geography are better placed to identify the main sources of damage. They can inspect particular sites, organise waste collection and explain requirements to businesses and residents. A uniform programme designed far away may overlook practical difficulties, such as limited transport or a shortage of suitable equipment. Local authorities also give residents a more direct place to raise concerns and ask how public resources are being used.

For these reasons, I would divide the responsibilities rather than give one level complete control. International organisations should set shared aims and support cooperation, while national and local authorities should choose workable measures and report their results. This combination recognises both the cross-border nature of environmental problems and the need for practical action in specific communities.

自检：两边都解释了“为什么”；立场交代分工；没有编造研究比例。不同立场也能成立，关键是回应双方并给出一致判断。''',
'新课前 4 分钟选两张词卡回忆，再把“跨境协调＋本地执行”换到灾害预警情境，说一个共同工作和一个本地工作；不必重写熟题范文。',
[
vocab('cross-border problems','跨境问题','Cross-border problems require communication between neighbouring countries.','cross-border 作定语；不要据此推断所有问题只能国际解决。'),
vocab('put an agreement into practice','将协议付诸实施','Local teams put the agreement into practice.','into practice 是实施；in practice 常表示实际情况。'),
vocab('be better placed to do','更适合／更有条件做','Local officials may be better placed to identify damaged roads.','保留 to + 动词；may 体现条件而非必然。'),
vocab('cooperate with someone on something','与某人就某事合作','The two councils cooperated on improving river access.','with 后接合作对象；on 后接事项。')],
sources=[source('2026 年 3 月写作主题回忆列表（非官方）',RECENT_WRITING,kind='unverified_candidate_recall'),source('IELTS 官方写作要求',WRITING_RULE)],
source_note='2026-09-16 核查非官方列表有 2026-03-25 日期的环境治理主题；只是选题参考，无官方真题确认。本题改为讨论双方，题面、讲解、词卡与整篇示范均原创；不是预测题库。',writing_mode='complete_original_task_and_model',minutes=27))

units.append(unit('new-writing2-community-causes','writing2','社区安全感：原因与措施逐一对应','城市生活与社区','Task 2 原因与对策',
'参考 2026 年有日期的安全感主题回忆，练“具体原因→作用过程→对应措施”，避免万能建议。',
'''### 从结果退回原因
题目谈感到不安全，不能自动写成所有地区的犯罪率都上升。实际环境、信息来源与个人经历都可能影响感受；文章可以在有限范围内解释，不需要杜撰数字。

### 让措施回应刚才的原因
如果原因是公共空间照明差，措施应涉及检查和维护；如果原因是居民无法获得可信的本地信息，措施应涉及可核对的信息和沟通。只写 government should pay attention 没告诉读者谁做什么、如何改变原因。

### 原创小链条
Poorly maintained paths may discourage people from walking after dark → fewer people use the area → some residents may feel more isolated. A clear maintenance schedule addresses the initial problem. 这是一种可能机制；不要写“修灯必然消灭犯罪”。

How to do IELTS 在 2026 年 3 月 1 日条目中列出居家和外出安全感的原因与对策回忆，本题缩小为社区公共空间，属原创迁移，不是逐字复刻真题。''',
'''原创情境题：In some communities, residents feel unsafe when using local public spaces, even when they are unsure whether crime has increased. What factors may contribute to this feeling, and what can communities do to address it?

先列两组“原因→措施”，每组各用一句具体说明。选 90–120 词段落练习或至少 250 词整篇。

用法题：改正 Poor lighting can result to anxiety.；补全 Providing reliable information may help residents make ___ decisions.（informed / informing）''',
'''改为 result in anxiety；最后填 informed，意为依据充分信息作出的决定。

### 完整原创示范
Feeling unsafe in a public space does not always mean that crime has become more common there. In some communities, the physical condition of an area and the way information is shared can both influence residents' perceptions. Addressing these factors requires practical maintenance as well as clear communication.

One possible cause is an environment that appears neglected. Broken lights, poorly maintained paths and unused buildings may make an area uncomfortable to enter, especially after dark. Residents may avoid it because they cannot easily see their surroundings or find assistance. As fewer people use the space, those who remain may feel even more isolated. Communities can respond by reporting faults through a simple system and publishing a schedule for repairs. Local authorities should prioritise problems that obstruct visibility or access, and residents can help identify the places where improvement is most needed.

Another factor is uncertainty about local events. A dramatic incident shared repeatedly online can create the impression of a continuing threat, even when little is known about its frequency. Rumours may also spread when residents have no trusted source to consult. A useful response is to provide regular, clearly explained local information and opportunities to ask questions. This should acknowledge real concerns rather than dismiss them, while distinguishing confirmed events from speculation. Meetings with community representatives can also help people explain difficulties that a general announcement might overlook.

These measures cannot guarantee that every resident will feel safe, and perceptions will still differ according to personal experience. Nevertheless, well-maintained spaces and reliable communication address two identifiable sources of unease. They offer a more focused response than assuming that every expression of fear proves a rise in crime.

核对逻辑：第一个措施回应物理环境；第二个回应信息不确定；结尾限定效果，没有把安全感当成犯罪率统计。可以提出其他有解释的原因与对应办法。''',
'隔日 3–4 分钟任选一个旧原因，再换到“新学生不敢使用校园设施”的情境，写一条对应措施。保留一条旧词卡即可继续新内容。',
[
vocab('contribute to','是造成某结果的因素之一','Poor lighting may contribute to a sense of unease.','to 是介词；不代表唯一原因或必然因果。'),
vocab('result in','导致某结果','Unclear instructions can result in avoidable mistakes.','result in 后接结果；result from 后接原因。'),
vocab('make informed decisions','在了解信息后作决定','Clear guidance helps residents make informed decisions.','informed 修饰 decisions；informing 意义不同。'),
vocab('distinguish A from B','区分 A 与 B','Readers should distinguish confirmed information from speculation.','保留两个比较对象，不能仅用 distinguish about。')],
sources=[source('2026 年 3 月原因与对策主题回忆（非官方）',RECENT_WRITING,kind='unverified_candidate_recall'),source('IELTS 官方写作要求',WRITING_RULE)],
source_note='2026-09-16 核查非官方列表 2026-03-01 安全感原因对策主题。日期只是该站回忆标记，未获官方确认；本题缩小情境，正文与教学原创，不是预测。',writing_mode='complete_original_task_and_model',minutes=27))

resources = [
 {'id':'cambridge21-official','title':'Cambridge IELTS 21 Academic · 2026 官方练习册','url':'https://www.cambridgeenglish.org/exams-and-tests/ielts/preparation/','kind':'official_recent_authentic_practice','verified_at':'2026-09-16','access':'既有本地原书；官方页面可查看产品，数字资源按书内方式使用','local_path':BASE+'/materials-library/user-materials/Cambridge IELTS 21 - Academic.pdf','note':'2026 年版在官方备考页列出，作为最近正式出版练习的优先入口。不是 9–12 月季节题库。原书不是新下载。'},
 {'id':'cambridge21-public-excerpt','title':'Cambridge IELTS 21 Academic · 官方公开节选','url':'https://assets.cambridge.org/97810098/26723/excerpt/9781009826723_excerpt.pdf','kind':'official_public_excerpt','verified_at':'2026-09-16','access':'公开 PDF','note':'新补官方节选入口，可核对出版社和考试格式；不是完整免费原书。'},
 {'id':'ielts-official-sample-tests','title':'IELTS 官方样题与机考熟悉资源','url':'https://ielts.org/take-a-test/preparation-resources/sample-test-questions','kind':'official_practice_hub','verified_at':'2026-09-16','access':'官方公开入口','note':'按题型选择专项练习；已公开样题不冠以 2026 新题。'},
 {'id':'ielts-reading-official-format','title':'IELTS Academic Reading · 当前题型规则','url':READING_RULE,'kind':'official_guidance','verified_at':'2026-09-16','access':'免费网页','note':'用于核对判断题、信息匹配、摘要填空等要求。'},
 {'id':'ielts-writing-official-format','title':'IELTS Academic Writing · 当前任务要求','url':WRITING_RULE,'kind':'official_guidance','verified_at':'2026-09-16','access':'免费网页','note':'完整练习时 Task 1 至少 150 词、Task 2 至少 250 词；单元短练习单独标记。'},
 {'id':'recent-writing-reference','title':'2026 写作主题回忆列表 · 非官方选题参考','url':RECENT_WRITING,'kind':'unverified_candidate_recall','verified_at':'2026-09-16','access':'主题列表公开，部分范文收费','note':'已核实页面实际列出 2026-03-25 环境治理和 2026-03-01 安全感条目。只采用主题；不复制付费范文，不保证考试命中。'},
]
for u in units[:4]:
    resources.append({'id':u['id']+'-audio','title':u['sources'][0]['title'],'url':u['sources'][0]['url'],'kind':'official_general_english_audio','verified_at':'2026-09-16','access':'本地 MP3 立即可播放；官方课程网页备份入口','local_path':u['media'][0]['path'],'audio_url':u['media'][0]['url'],'note':'已储备原音补成完整教学，不把旧录音称作新题。'})

OFFICIAL_LISTENING = 'https://takeielts.britishcouncil.org/prepare/ielts-free-practice-mock-tests/academic/listening'
BC_PDF = 'https://takeielts.britishcouncil.org/sites/default/files/%5Bdownloads%5D/'
resources.extend([
 {'id':'official-map-audio-sample','title':'官方地图听力 · 美国城镇导览（3题）','url':'https://ielts.inspera.com/player/?assessmentRunId=189695339&context=exam','kind':'official_interactive_audio_sample','verified_at':'2026-09-16','access':'官方题面与原音在同一交互入口；浏览器打开','source_page':OFFICIAL_LISTENING,'answer_url':BC_PDF+'ielts-listening-computer-delivered-plan-map-diagram-labelling-answer-key.pdf','transcript_url':BC_PDF+'ielts-listening-computer-delivered-plan-map-diagram-labelling-transcript.pdf','note':'新增题型资源入口，非完整新教学单元。官方页面明确为 Part 2 导览原音＋地图题；答案 PDF 为 H／A／C。已核对来源、文稿与答案；工具直接抓取交互播放器返回403，未独立试听，不以另一份无原音的图书馆纸题代替。'},
 {'id':'official-academic-multi-speaker','title':'官方学术多人讨论 · Judy 的研究（3题）','url':'https://ielts.inspera.com/player/?assessmentRunId=189697549&context=exam','kind':'official_interactive_audio_sample','verified_at':'2026-09-16','access':'官方题面与原音在同一交互入口；浏览器打开','source_page':OFFICIAL_LISTENING,'answer_url':BC_PDF+'ielts-listening-computer-delivered-multiple-choice-one-answer-answer-key.pdf','transcript_url':BC_PDF+'ielts-listening-computer-delivered-multiple-choice-one-answer-transcript.pdf','note':'新增 IELTS Part 3 多人学术讨论入口，题型为单选。已核对官方课程说明和独立答案、文稿；播放器需浏览器加载，未独立试听。不要与 B1 团队会议原音计为同一道题或同等难度。'},
 {'id':'official-matching-familiarisation','title':'官方机考匹配入口 · Part 2 人员职责／Part 3 化石分类','url':'https://demo-ielts.inspera.com/player/?assessmentRunId=131012334&context=exam','kind':'official_familiarisation_partial_feedback','verified_at':'2026-09-16','access':'官方机考熟悉入口；含原音，工具直取交互页403','source_page':OFFICIAL_LISTENING,'existing_audit_path':BASE+'/materials-library/listening-audit-2026-09-14/batch-03/index.html','note':'本地已配题面图形与原音，已有清单核对含匹配题。但本地整卷有24题未取得官方答案，不能当完整可评分模考，未包装为完成教学单元。可先在官方界面熟悉匹配操作；本轮没有宣称 IELTS 听力全题型均补齐。'},
])

payload = {'schema_version':'1.0','updated_at':'2026-09-16','scope_note':'资源优先：补齐已储备官方原音的教学层，并新增原创阅读与写作完整单元。最近正式出版资源优先 Cambridge IELTS 21；官方样题与 B1 基础材料按能力用途保留。听、读、写不声称存在已核实的季节题库。',
 'learning_balance':{'default_new_to_review':'约 4:1（可调整）','policy':'每单元先学新材料，末尾可用 2–4 分钟回忆两张旧词卡或一道错题。新学、复习并行，不清零旧错题也能继续。该比例是产品安排，不声称来自不背单词的专有算法。'},
 'coverage_note':'完成 12 个可直接学习单元；另外补官方地图、学术多人讨论与匹配交互入口。入口资源不等同已制作完整教学；机考熟悉卷仍有答案缺口，不作为整卷可评分模考。',
 'resource_catalog':resources,'units':units}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps({'path':str(OUT),'units':len(units),'resources':len(resources),'vocabulary':sum(len(u['vocabulary']) for u in units)},ensure_ascii=False))
