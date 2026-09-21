"""Reviewed, incremental teaching repairs. Original tasks and answers stay in place."""
from html import escape as E

C21 = '原始参考/8ee8170c-Cambridge IELTS 21 - Academic.pdf'
MONIKA = 'https://ielts.org/organisations/ielts-for-organisations/understanding-ielts-scoring/resources-for-setting-your-ielts-scores'

def field(key, label, rows=3):
    return f'<label class="field"><span>{E(label)}</span><textarea data-save="prereq-{key}" rows="{rows}"></textarea></label>'

def answer(body, label='完成后核对'):
    return f'<details class="prereq-key"><summary>{label}</summary>{body}</details>'

def source(page, label):
    return f'<a href="{C21}#page={page}" target="_blank" rel="noopener">{label}</a>'

def block(key, title, body):
    return f'<section class="prereq-lesson" id="prereq-{key}"><h3>{title}</h3>{body}</section>'

EDUCATION = block('education', '把教育概念用到具体问题里', '''
<p>先用两个课堂情境检查理解，再看一道正式写作题怎样限定讨论范围。前两题是本册编写的理解练习。</p>
<ol><li>两名学生都能参加科学项目。甲会测量，但听不懂课堂指令；乙能理解指令，却需要练习测量。给两人同一份作业是否就满足了各自的学习需要？各写一种帮助，并说明帮助解决的困难。</li>
<li>学校给所有学生安排相同的项目目标，同时为需要的学生提供双语词表和额外练习时间。这属于改变学习目标，还是改变参与方式？用 access to education 和 equal opportunity 解释：已有名额，还缺什么？</li></ol>'''
+ field('education-scenarios','我的判断与理由')
+ answer('''<p>① 甲需要理解指令的支持，例如关键术语表或一次演示；乙需要测量练习和反馈。两人都能入学，不代表都已获得适合的支持。② 目标相同，支持方式不同；平等机会可以通过不同帮助实现，不必把“公平”理解成每个人得到完全一样的东西。具体措施还受教师时间与可用资源限制。</p>''')
+ '''<h4>正式题：小学课堂的正式学习与游戏</h4>
<p class="english">Some people argue that primary schools focus too much on formal learning.<br>To what extent do you agree with this opinion?<br>How important do you think it is for children to play as well as learn in the primary school classroom?</p>
<p>原题要求说明理由并举相关例子，完整作文至少 250 词，建议 40 分钟。本次只练审题与一个理由段，不计作完成整篇作文。</p>
<ol><li>写出题目中的两项要求，并明确讨论对象与场景。</li><li>设计一个课堂活动，说明孩子在其中学什么、怎样参与、为什么需要游戏。再补一句：什么情况下需要额外的学习支持？</li></ol>'''
+ field('education-paragraph','两项要求 + 一个理由段',5)
+ answer('''<p>两项要求分别是：是否同意小学过于重视正式学习；游戏在小学课堂里有多重要。范围是小学课堂，不能只讨论大学就业或入学机会。</p>
<p>原创示例：A simple shop game can help children practise addition while taking turns as customers and shopkeepers. They use numbers for a clear purpose and learn to cooperate. A child who struggles with the instructions may need a demonstration before joining in. 这里“游戏—计算与合作—示范支持”逐项对应 practical skills 和 learners’ needs；它是理由段示例，没有官方分数。</p>
<p>打开同题考生稿：找出第 2 段支持正式学习的两点，以及第 3 段说明游戏价值的两点。再读评语，修改自己段落里最笼统的一句。</p>
<p>核对：考生稿谈到纪律与尊重、考试检验学习；游戏段谈到社交与创造技能、减少无聊并激发长期学习兴趣。考官认可回应两问和相关展开，同时指出结论笼统、句首连接词过多，以及个别搭配错误。7.5 分属于这份考生原稿，并不说明其中每句话都值得照抄。</p>''')
+ f'<p>{source(96,"完整题面")} · {source(139,"同题考生稿与评语（7.5 分）")} · {source(140,"续页评语")}</p>')

WORK = block('work', '从工作条件说到生活安排', '''
<p>下面两个情境为本册编写。先分清“时间、地点、稳定性”，再用正式口语样本观察怎样解释工作与休息的关系。</p>
<ol><li>甲可以在家工作，但每天必须在线到晚上十点。乙必须到工作场所，但下班时间固定。谁的工作地点更灵活？能否据此断定谁有更好的 work-life balance？还需要哪些信息？</li>
<li>一份工作薪水较高，但短期合同即将到期；另一份收入较低，长期合同和工时较稳定。说明两者在收入与 job security 上的取舍。为需要接送孩子的人提出一种具体安排，并说明岗位能否支持它。</li></ol>'''
+ field('work-scenarios','概念、缺少的信息与具体安排',4)
+ answer('''<p>① 甲的地点选择更多，但长时间在线可能减少休息；还要看总工时、通勤、家庭责任和个人需要。工作地点灵活不自动等于生活更平衡。② 合同期限与稳定预期有关，薪水高低是另一维度；固定提前下班或错峰上班可能有帮助，但需要覆盖岗位职责，不能直接假定所有岗位都能远程完成。</p>''')
+ f'''<h4>正式口语样本：Monika 的工作与休闲讨论</h4>
<p>在 <a href="{MONIKA}" target="_blank" rel="noopener">IELTS 官方样本页</a> 找到 Band 8 | Monika, Germany，播放工作与休闲部分，或展开转写。本段用来观察理由怎样展开；示例中的社会情况是考生当时的看法。</p>
<p>中文任务提要：考官顺着她关于工作和休闲失衡的观点，要求进一步解释。她将岗位竞争与保住工作、加班、休闲时间减少和家庭生活联系起来。</p>
<ol><li>按“压力来源 → 工作行为 → 生活影响”记录她的解释链。</li><li>她关于未来的回答是确定事实还是预测？记录她怎样限制确定程度。</li><li>给自己熟悉的一种岗位提出改善时间安排的办法，用两句说明效果和限制。</li></ol>'''
+ field('work-source','解释链与我提出的安排',4)
+ answer('''<p>核对：岗位竞争／保住工作的压力 → 增加加班 → 休闲与家庭时间受到挤压。未来部分带有不确定性，是预测。考官认可长回答的连贯展开、词汇与语音表现，同时指出少数搭配和时态问题；官方 8 分针对该考生表现。</p>
<p>原创参考：A customer-service team could stagger its shifts so that some staff finish earlier without leaving the service desk unattended. This would require enough staff during busy periods, so a very small team might have less flexibility. 先给安排，再补适用条件；不用把灵活工作说成对所有人都有效。</p>'''))

TECHNOLOGY = block('technology', '技术是否可用：条件、风险与人的判断', '''
<p>先回到下方 Artificial Intelligence 阅读原文，找到数据基础设施和专业人员两个条件。再完成 Q31 与 Q33；答案在原题词表中，不直接照抄整句。</p>
'''+field('technology-evidence','Q31 / Q33 的选择，以及各自对应的原文信息')
+ answer('''<p>Q31 选 G（framework），对应 data infrastructure；Q33 选 C（skills），对应 human talent。能做算法不等于机构已经具备部署条件：整理和使用数据的基础、能实施与维护的人都需要考虑。</p>''')
+ '''<h4>换到一个具体服务（原创理解练习）</h4>
<p>一家社区中心推出网上预约。部分居民没有稳定网络；另一些人有手机却不会操作。系统要求填写身份证号码，并可能受到恶意攻击。请把四件事分别对应 digital access、digital skills、privacy 与 security，再提出一项保留人工帮助的做法。</p>'''
+ field('technology-application','四项对应 + 一项人工帮助',4)
+ answer('''<p>稳定网络属于 access；会不会使用属于 skills；身份证号码为何收集、谁能看到和保留多久涉及 privacy；防止未授权访问与攻击涉及 security。两者相关，但安全措施完善不表示所有个人信息收集都合理。可保留电话或现场预约，并让工作人员解释必要信息。</p>
<p>原创表达：An online service can make booking easier, provided that users have reliable internet access and know how to use it. Staff should still be available to help people who cannot complete the process online. 用 provided that 写条件，第二句给出需要人工参与的具体环节。</p>
<p>AI 原文支持的是实施条件、攻击风险与人的判断。这里的社区预约和隐私讨论是迁移情境，不是声称原文证明了这些服务的实际效果。</p>''')
+ f'<p>{source(47,"AI 原文")} · {source(50,"Q30–35 与词表")} · {source(121,"原书答案")}</p>')

VOCABULARY = block('vocabulary-usage','让选中的词进入自己的句子', '''
<p>这 1000 条是按话题整理的词义与搭配索引，例搭配为教学编写。查词时可把词条连同正在阅读的原句收藏到“我的单词表”，再做回忆与拼写。学会拼写后，用下面这一步检查自己是否会用。</p>
<ol><li>从当前话题选 1–3 个自己需要的词或词组；记录它在当前文章中指什么。没有文章语境时，先看本地词典中的对应义项与搭配。</li><li>合上解释，写一个与自己经历或当前题目有关的句子；再补一句条件、原因或具体例子。</li><li>展开词典核对意思与结构。标记一处修改，隔天换一个情境再用。</li></ol>'''
+field('vocab-terms','本次词或词组 + 义项／来源句',3)
+field('vocab-use','我的两句表达',3)
+answer('''<p>以 access 为例：Students need access to reliable internet to join the online class. The school could provide a study room for those without a connection at home. 第一处 access 是名词，结构是 access to + 名词；第二句补了具体支持。把“有机会使用”和“已掌握技能”分开表达。</p>
<p>检查三件事：词义是否符合本意；搭配和词形是否正确；句子是否说出了可理解的具体内容。若仍不确定，留下具体疑点再查来源；不要仅因句子包含目标词就标为已掌握。</p>''')
+field('vocab-revision','我修改了什么／还不确定什么',3)
+field('vocab-later','隔天换情境的两句表达',3)
+'<p><a href="#vocabulary-review">进入我的单词表</a> · <a href="词频与原文证据.html">在本地语料中查实际用法</a></p>')

AS_RESULT = block('as-result','先找原因，再接结果', '''
<p>下方 Dar es Salaam 原文写到机器故障后改用纸票，入口没有扫描器，需要工作人员手工撕票：</p>
<blockquote class="english">Staff stand by the gates and tear tickets as people enter. As a result, queues are considerable at peak times.</blockquote>
<p>先写出原因和结果各是什么；再判断：这句话能否只解释为“因为洪水，所以排队”？</p>'''
+field('as-result','原因 → 结果；我的判断',2)
+answer('''<p>人工验票流程导致高峰时段较长的队列。As a result 回指前面的票务与验票问题，不能越过这一段具体机制，只抓较远处的洪水作直接原因。原题 Q26 的答案是 queues。</p><p>原创再用：The ticket machines stopped working. As a result, staff had to check each ticket by hand. 后一句写结果；若用 as a result of，后面应接原因名词短语。</p>''')
+f'<p>{source(66,"原文所在页")}</p>')

SPEAKING = {
 'speaking_part1_natural_answers': {
  'title':'先说一问，再回听并重说',
  'prompt':'What kind of place is your home town or village?',
  'task':'用自己的真实情况回答这一问，说 2–3 句即可：先说地方类型，再补一个相关细节。先录音，再展开考生转写；已看过转写也可以练，记为学习后应用。',
  'check':'回听第一遍：首句是否直接回应地方类型？细节是否有关？在影响理解的一处停顿、重复或含糊表达旁记下时间点。只选一处修改，再重说同一问，对比两段声音。',
  'example':'例如只说 It is a nice place 太笼统，可以补一个自己的事实，如 It is a small coastal town, and most shops are within walking distance of my home. 这是原创内容示例；地点和事实要换成自己的。',
  'next':'下一次换问：Tell me about the kind of accommodation you live in. 不看家乡示范，用自己的住宿情况回答，并补一处细节。题页另列的住宿四问不属于下方家乡转写的覆盖范围。'
 },
 'speaking_part3_explain_compare': {
  'title':'说清观点，接一次追问',
  'prompt':'What kind of things give status to people in your country?',
  'task':'本次只练地位象征。先口答这一问：给出观点、一个具体原因和适用范围；随即回答追问 Can you tell me a little bit more about that? 录下整段，再展开下方考生片段。',
  'check':'回听第一遍：原因怎样支持观点？追问后是否增加了具体内容，还是重复上一句？找一处影响理解的停顿或理由缺口，记下时间点，只改这一处，再回答同一问和追问。',
  'example':'例如：In some professions, qualifications carry more weight than expensive possessions because they signal specialised training. 追问时可解释某个具体职业为什么重视资格；用 in some professions 限定范围。这是原创示例，不必套用同一立场。',
  'next':'下一次练未来变化：Do you think this will change in the future? 给一个可能的变化和条件。下方官方题页还有广告话题；本次转写没有覆盖完整广告讨论，留作之后独立选题。'
 }
}
