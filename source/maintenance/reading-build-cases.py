from pathlib import Path
from reviewed_text_corrections import correct_transcription
import json,re,hashlib
W=Path(__file__).parent
B=json.loads((W/'reading-source-c21-blocks.json').read_text(encoding='utf8'))
P=json.loads((W/'reading-source-c21-pages.json').read_text(encoding='utf8'))
cases=[]
FIX={'lmow':'know','well-lmown':'well-known','contemporaiy':'contemporary','·while':'While','Dares Salaam':'Dar es Salaam','Provenc;al':'Provençal','Franc;ois':'François','UlbeBosma':'Ulbe Bosma'}
def clean(t):
 for a,b in FIX.items():t=t.replace(a,b)
 return correct_transcription(t.strip())
def pars(*refs):
 out=[]
 for n,i,label in refs:out.append({'label':label,'text':clean(B[str(n)][i]),'page':n})
 return out
def q(n,p,a,e,x,options=None,typ=''):
 z={'number':str(n),'prompt':p,'answer':a,'evidence':e,'explanation':x}
 if options:z['options']=options
 if typ:z['type']=typ
 return z
def add(suffix,title,test,passage,paragraphs,questions,types,structure,phrases,sentences,instructions='按原题要求作答。'):
 pages=sorted(set(n for x in paragraphs for n in x.get('pages',[x['page']])))
 c={'id':'rd-c21-'+suffix,'skill':'reading','title':title,'questionTypes':types,'questionType':types[0],
 'source':{'id':'cambridge21-academic','title':'Cambridge IELTS 21 Academic','path':'原始参考/8ee8170c-Cambridge IELTS 21 - Academic.pdf','page':pages[0],'pages':pages,'questionPages':{(1,1):[19,20],(1,2):[23,24,25],(1,3):[28,29],(2,1):[41,42],(2,2):[45,46],(2,3):[49,50,51]}[(test,passage)],'answerPage':117+2*test,'test':f'Test {test}','kind':'真题','originalUnit':f'C21 Test {test} Passage {passage}','passageTitle':title.split('｜')[0]},
 'paragraphs':paragraphs,'questions':questions,'instructions':instructions,'intensive':{'structure':structure,'phrases':phrases,'sentences':sentences},
 'wordCount':sum(len(re.findall(r"\b[\w'-]+\b",x['text'])) for x in paragraphs),'verification':{'passage':'逐段对照本地PDF提取；保留连续原段','answers':'原书 Reading answer key 对照','cutRule':'不降难度；保留所选原题所需语境；全文已核对NOT GIVEN无补充信息'}}
 cases.append(c)
 save()
 return c
def save():
 (W/'authentic-reading-cases.json').write_text(json.dumps({'version':1,'cases':cases},ensure_ascii=False,indent=2),encoding='utf8')
add('davies-1','The Davies Sisters｜成长背景与收藏起点',1,1,pars((17,6,'原文第1段'),(17,7,'原文第2段'),(17,8,'原文第3段'),(17,9,'原文第4段')),[
q(1,"Family and early life: their grandfather's wealth came from 1 __________ and transportation businesses",'mining','a fortune in the shipping and mining industries','transportation对应shipping；and并列的另一行业是mining。答案限一词。'),
q(2,'their 2 __________ was designed to give them an interest in activities such as collecting art','education',"the sisters' education was rigorously geared toward such pursuits",'designed to give them an interest是was geared toward的改写，主语为education。'),
q(3,'they took lengthy 3 __________ about the things they saw in art galleries','notes','making extensive notes on the collections there','lengthy对应extensive；took notes对应making notes，保留复数。'),
q(4,'their 4 __________ showed they liked Old Master paintings, but they were expensive to buy','journals',"The sisters' journals reveal their preference for Old Master",'showed they liked对应reveal their preference；注意不能把其他段落的notes填进来。'),
q(8,"The Davies sisters' childhood influenced the way they decided to use their wealth.",'TRUE','Their religious upbringing in rural Wales gave them a deep sense of social responsibility','童年教养产生社会责任感，下一分句明确说因此把遗产用于文化及慈善，完整因果支持题干。')],['note-completion','true-false-not-given'],
'第1段交代财富与责任；第2段解释教育如何培养兴趣；第3段澄清顾问与姐妹的主导关系；第4段转向偏好与购买能力的限制。先建立时间/因果地图，再按题目中的角色和动作定位。',
[{'phrase':'be geared toward','meaning':'以……为目标','explanation':'education was geared toward such pursuits解释教育的目的，不是已经完成收藏。'},{'phrase':'beyond their means','meaning':'超出财力','explanation':'与后面的beyond what they were willing to pay形成“买不起/不愿付”的区分。'}],
[{'text':'While it was long assumed that these men were largely responsible for the nature of the sisters’ collection, it has recently been accepted that Gwendoline and Margaret retained a far more active role in the process.','explanation':'While引导让步/对照：过去把收藏方向归功于男性顾问；如今认为姐妹更主动。读到前半句不能就结束。'}],
'Q1–4：Complete the notes. Choose ONE WORD ONLY from the passage for each answer. Q8：TRUE / FALSE / NOT GIVEN。原题号保留。')
add('davies-2','The Davies Sisters｜印象派转向与战时收藏',1,1,pars((18,1,'原文第5段'),(18,2,'原文第6段'),(18,3,'原文第7段')),[
q(5,'the first Impressionist paintings they bought showed places in 5 __________','Venice','their first purchases of Impressionist art, made in October 1912, were scenes of Venice','题干问画中的地点，不是买画地点；Paris是干扰信息。'),
q(6,'they worked in a 6 __________ for soldiers in France','canteen','both sisters decided to volunteer at a canteen for troops at Troyes','soldiers对应troops；a后填地点canteen，不能答城市Troyes。'),
q(10,"Hugh Blaker opposed the Davies sisters' decision to buy art by French Impressionists.",'FALSE','Hugh Blaker, as a champion of contemporary French art had a hand in the decision','champion与had a hand in说明支持并参与，和opposed相反，属于明确反证。'),
q(11,'The exhibition of Cezanne paintings at the Bath gallery was very popular with the public.','NOT GIVEN','the first works by Cezanne to go on display in a public gallery in Britain','原文只确认首次公开展出，没有观众反响或人数。全文也未提供其受欢迎程度；first与popular不可互换。')],['note-completion','true-false-not-given'],
'三段保持原顺序：收藏方向改变→战时志愿服务→在巴黎购画并送至Bath展出。人物、作品地点、购买地点、展出地点必须分开。',
[{'phrase':'have a hand in','meaning':'参与、对……有影响','explanation':'这里与champion共同构成反对opposed的证据。'},{'phrase':'go on display','meaning':'开始展出','explanation':'只说明展出事实，不包含观众评价。'}],
[{'text':'Whatever the precise reason for this change, their first purchases of Impressionist art, made in October 1912, were scenes of Venice by the French artist Claude Monet.','explanation':'Whatever引导让步；主干是purchases were scenes of Venice，日期和作者是插入信息。Q5必须取主干中画面所示地点。'}],
'Q5–6：Choose ONE WORD ONLY from the passage. Q10–11：TRUE / FALSE / NOT GIVEN。')
add('davies-3','The Davies Sisters｜收藏停止与文化遗产',1,1,pars((18,4,'原文第8段'),(18,5,'原文第9段'),(18,6,'原文第10段')),[
q(7,'were not considered typical collectors – they lived in isolation in the countryside and did not have any 7 __________ who were artists','friends',"they didn't make friends with artists or gallery owners",'题干把make friends改为have friends；any后用复数friends，不是advisers。'),
q(12,'The impact of the First World War encouraged Gwendoline to reconsider her interest in collecting art.','TRUE','Gwendoline felt increasingly uncomfortable buying art works when faced with the poverty and social upheaval created by the First World War','战后贫困与动荡使她不安，随后慈善转向社会事业并停止购买，是reconsider的具体证据链。'),
q(13,'The Davies sisters bought French Impressionist art during a period when very few people were doing so.','TRUE','at a time when such art was routinely ignored by individuals and institutions alike','ignored by individuals and institutions同时覆盖个人与机构，与very few people were doing so同义。')],['note-completion','true-false-not-given'],
'第8段纠正“孤立收藏家”的刻板印象；第9段按时间解释停止收藏；末段评价长期贡献。区分作者评价、当时市场事实和姐妹个人选择。',
[{'phrase':'feel obliged to','meaning':'觉得有义务/不得不','explanation':'否定形式说明她们不受流行趣味约束。'},{'phrase':'individuals and institutions alike','meaning':'个人与机构都一样','explanation':'alike扩大描述范围，是Q13判断当时普及程度的依据。'}],
[{'text':'Yet they didn’t feel obliged to follow fashionable tastes and were free to pursue their own preferences.','explanation':'Yet转折的是“偏远、缺少艺术圈朋友”的负面刻板印象，转出独立选择的优势；不能把这句话误读为没有顾问。'}],
'Q7：Choose ONE WORD ONLY from the passage. Q12–13：TRUE / FALSE / NOT GIVEN。')
people=['A Nick Antonio','B Justin Feinstein','C Tai Dotan Ben-Soussan','D Eric Pfeifer']
add('silence-1','Why we need silence｜噪声风险与城市降噪',1,2,pars((21,4,'A'),(21,5,'B'),(21,6,'C')),[
q(14,'examples of strategies to decrease the noise that the public are exposed to','C','quieter buses, reducing noise from roads and also controlling noise from aircraft','C列举公交、道路、飞机以及禁令等多项策略；不是只说噪声有害的B。',list('ABCDEFG'),'matching-information'),
q(15,'data indicating the extent of the problem of excessive noise','B','at least 1 in 5 people consistently exposed to levels considered harmful to health','extent看覆盖范围；1 in 5与城市夜间分贝限制构成具体数据证据。',list('ABCDEFG'),'matching-information'),
q(16,'a description of physiological changes in our bodies when we hear sudden noises','A','Our blood pressure goes up, muscles tense and glands release hormones','blood pressure、muscles、glands是身体变化，不是社会影响。',list('ABCDEFG'),'matching-information'),
q(23,'The trend towards creating quieter urban locations is likely to increase in the coming years.','A','I expect we will see much more of this in the future.','这句话属于Antonio的直接引语，预测降噪趋势继续增加。',people,'matching-features')],['matching-information','matching-features'],
'A解释生理机制；B用机构结论与数据展示规模；C转向解决办法。信息匹配按“数据/机制/措施”的段落功能分类，比只找noise更有效。',
[{'phrase':'be exposed to','meaning':'暴露于、接触到','explanation':'与题干public are exposed to直接对应，定位后还要区分风险段和措施段。'},{'phrase':'turn the volume down','meaning':'降低噪声','explanation':'C首句给出整段功能，后面城市例子展开此主旨。'}],
[{'text':'When we are exposed to too much noise over the long term, however, those responses can lead to a multitude of health issues, from sleep disturbance to even cardiovascular disease.','explanation':'however将短期有益的应激反应转为长期风险；those responses回指升压、肌肉紧张和激素释放。'}],
'Q14–16：Which section contains the following information? 原选项A–G保留，本片段含A–C。Q23：Match the statement with the correct person, A–D. You may use any letter more than once.')
add('silence-2','Why we need silence｜漂浮舱的两项实验',1,2,pars((21,7,'D'),(22,1,'E（第一段）'),(22,2,'E（第二段）')),[
q(18,'According to Justin Feinstein, flotation tanks allow people to concentrate on their own 18 __________, which helps them relax and enables them to meditate.','breath','the ability to focus on the breath','concentrate on与focus on同义；不是描述感官幻觉的humming sounds。'),
q(19,'Feinstein and his colleagues conducted an experiment in which 50 people, who were all suffering from stress and related issues, were given a 19 __________ to complete before and after using a flotation tank.','questionnaire','answer a questionnaire prior to and following a flotation session','50 people唯一锁定第一项实验，before and after对应prior to and following。'),
q(20,'Participants reported a reduction in their symptoms after an hour in the tank, together with signs of relaxation and improved general 20 __________.','wellbeing','an increase in feelings of relaxation and overall wellbeing','general对应overall；答案是整体状态wellbeing，不是症状pain。'),
q(21,'In another experiment, the researchers had 48 people spend periods of 90 minutes either lying back in a chair or floating in a tank. Brain scans then revealed that those people who had been in a tank had decreased activity in parts of the brain associated with 21 __________.','depression','a collection of brain regions commonly linked with depression','associated with对应linked with；48人/90分钟与上一项50人/一小时必须分开。'),
q(24,"When our body's senses are completely deprived of input, our minds compensate for this by creating the illusion of images and sounds.",'B','the brain tries to fill the void to make sense of this dark and silent world','D引语来自Feinstein；visual effects与humming sounds对应images and sounds。',people,'matching-features')],['summary-completion','matching-features'],
'D解释漂浮舱体验与放松机制；E先报告50人的问卷实验，再报告48人的脑扫描实验。作答后画两列：样本/时长/测量/结果，防止跨实验拼答案。',
[{'phrase':'prior to and following','meaning':'在……之前和之后','explanation':'等于before and after，描述问卷测量的时间点。'},{'phrase':'sensory deprivation','meaning':'感官剥夺','explanation':'指外部感官输入减少，不等于大脑停止活动。'}],
[{'text':'Float sessions uniquely decreased activity in the default mode network (DMN), a collection of brain regions commonly linked with depression.','explanation':'主干是sessions decreased activity；逗号后是DMN同位语。Q21要填相关病症depression，不能抄机制名称DMN。'}],
'Q18–21：Complete the summary. Choose ONE WORD ONLY from the passage for each answer. Q24：Match the statement with the correct person A–D.')
add('silence-3','Why we need silence｜主动安静与短时收益',1,2,pars((22,3,'F（第一段）'),(22,4,'F（第二段）'),(22,5,'G')),[
q(17,'evidence that a relatively quiet environment can be more beneficial than a totally silent one','G','more relaxation and less boredom when they sat quietly in an outdoor garden compared with a completely silent room','必须有两种环境的比较；G中花园与完全静音房间的结果符合题干。',list('ABCDEFG'),'matching-information'),
q(22,'It is unpleasant and upsetting for people to be placed in a silent environment against their will.','C','When people do not want silence, it can be very distressing.','F第二段Ben-Soussan把自愿性列为前提，against their will对应do not want。',people,'matching-features'),
q(25,'Even a short amount of silent time can have a positive impact.','D','Just finding those places in your daily life where you can find some silence ... can make a big difference.','G的Pfeifer明确说几分钟、高频也有益，不要求一次持续数小时。',people,'matching-features'),
q(26,'External and internal quietness makes us more conscious of events occurring in our surroundings and helps us react appropriately to these events.','C','more aware of what is happening around us and what the situation may require from us','F第一段Ben-Soussan提到外部与内在安静，进而更好回应环境。',people,'matching-features')],['matching-information','matching-features'],
'F讨论自愿参与的条件；G承认例外后提出两个修正：不必完全无声、不必单次很长。人物匹配先标引语说话人，再看代词she/he的归属。',
[{'phrase':'to the same extent','meaning':'达到同样程度','explanation':'否定句限制效果普遍性，不是否定安静的所有价值。'},{'phrase':'concede that','meaning':'承认某一点','explanation':'G先承认高压力人群可能无法放松，再提出引导与短时练习。'}],
[{'text':'It is likely better to have more frequency of silence for a few minutes at a time than a longer period of silence only once a week.','explanation':'better…than比较的是频率与单次时长的组合；不能截成“越长越好”。'}],
'Q17：Which section A–G contains the information? Q22/25/26：Match statements with people A–D. You may use any letter more than once.')
add('sugar-1','The World of Sugar｜全球贸易与误解纠正',1,3,pars((26,5,'原文第1段'),(26,6,'原文第2段'),(26,7,'原文第3段')),[
q(27,'What does the reviewer suggest about the cultivation and trading of sugar in the first paragraph?','B','massively subsidised and sold at artificially low prices on world markets','补贴让甜菜糖以人为低价竞争，支持B。文中并未比较甘蔗糖品质。',['A Sugar has played a major role in international relations.','B Beet sugar has been made more internationally competitive.','C Cane sugar is thought to be of superior quality to beet sugar.','D New locations for cultivating sugar have increased production.']),
q(28,'In the second paragraph, when discussing the sugar market in Britain, the reviewer stresses','A','first bought cane sugar from their own slavery-dependent colonial plantations','first→Following→Towards the end→Only in the 20th century构成来源随时间变动的序列。',['A how the sources used changed over time.','B how developments in agriculture affected trade.','C the increased demand for sugar over the years.','D the growing support for ethical methods of cultivation.']),
q(29,'What is the reviewer doing in the third paragraph?','C','Contrary to popular belief, cane sugar production was never just restricted to large, dedicated plantations','首句提出劳动力历史，Contrary to popular belief明确纠正普遍误解，小农Java例子服务于该功能。',['A describing an efficient approach to sugar cultivation','B explaining why the use of sugar plantations declined','C addressing a misconception about the growing of sugar cane','D evaluating different approaches to the cultivation of sugar cane'])],['multiple-choice'],
'第1段全球范围→甜菜糖补贴竞争；第2段按时间讲英国糖源转移；第3段用Java小农反驳“大种植园专属”的认识。三题分别问事实含义、段落重点、作者动作。',
[{'phrase':'artificially low prices','meaning':'人为压低的价格','explanation':'subsidised提供原因，competitive是其结果性概括。'},{'phrase':'contrary to popular belief','meaning':'与普遍看法相反','explanation':'是Q29判断作者纠正误解的强信号。'}],
[{'text':'Following the abolition of slavery in the British Empire, cane sugar was imported to Britain from places which retained the practice, such as Cuba and Brazil.','explanation':'which retained the practice修饰places，practice回指slavery；英国废奴不等于进口供应地也废奴，排除凭道德进步常识选D。'}],
'Choose the correct letter A, B, C or D. 原题Q27–29。')
sugar_options=['A national governments','B agricultural developments','C less wealthy nations','D untrained workers','E small-scale cultivation','F outdated methods','G financial controls','H migrant workers','I powerful individuals and businesses']
add('sugar-2','The World of Sugar｜劳动组织与行业权力',1,3,pars((26,8,'原文第4段'),(26,9,'原文第5段')),[
q(31,'In the big industries in both Germany and the US, sugar farming depended on 31 __________.','H','German beet fields employed Polish workers; Mexicans and many others, including Sicilians, were vital to US sugar production','波兰人赴德、墨西哥人等赴美均是跨地迁移劳工，概括为migrant workers。',sugar_options),
q(32,'However, in other parts of the world such as South Asia and Latin America, 32 __________ continued.','E','traditional methods on small farms','small farms与small-scale cultivation对应；F outdated带有落后评价，原文只说traditional。',sugar_options),
q(33,'Sugar production has also involved 33 __________ who were eager to protect their markets.','I','a history of capitalists and sugar dynasties, as well as corporations','资本家、糖业家族与公司合并概括为powerful individuals and businesses。',sugar_options),
q(34,'In countries such as Cuba the sugar industry therefore had a major influence on 34 __________.','A','Great firms and great interests have had profound influence on the policies of states','policies of states和politics对应national governments，不是农业技术。',sugar_options),
q(35,'To support the interests of sugar producers, 35 __________ were established.','G','their interests were consequently protected by trade barriers and subsidies','贸易壁垒与补贴是financial controls的实例，不能只靠相同词选项。',sugar_options),
q(36,'As a result of this, 36 __________ were penalised.','C','it was inevitably the poor countries which came off worse','poor countries对应less wealthy nations，came off worse对应were penalised。',sugar_options)],['summary-completion-options'],
'两段分别讲劳动/农场规模和企业/政府权力。摘要把具体国籍、农场、政策抽象成类别词，六个空依靠“例子→概括”关系而非原词照抄。',
[{'phrase':'come off worse','meaning':'处于更不利的位置','explanation':'对应摘要were penalised，主语是贫穷国家。'},{'phrase':'trade barriers and subsidies','meaning':'贸易壁垒与补贴','explanation':'两种保护生产者利益的经济措施，共同对应financial controls。'}],
[{'text':'In many places - not just the British Caribbean but Cuba and the Philippines too - a powerful sugar bourgeoisie played a major role in politics and their interests were consequently protected by trade barriers and subsidies.','explanation':'破折号内容扩大地理范围；主干是糖业阶层影响政治→利益受保护。consequently给出Q34、35之间的因果关系。'}],
'Complete the summary using the list of words A–I. Write the correct letter A–I. 原选项完整保留；Q31–36。')
add('sugar-3','The World of Sugar｜工业化、消费与作者立场',1,3,pars((27,1,'原文第6段'),(27,2,'原文第7段'),(27,3,'原文第8段')),[
q(30,"In the final paragraph, what does the reviewer suggest is the overall message of Bosma's book?",'A','we could always have done without sugar and that today we have many alternative sources of sweetness','前文解释危害，末段强调可不依赖糖与替代来源，A概括全书结论。末句贫困者生计不等于作者主张继续扩大糖业。',['A Sugar is a harmful and unnecessary product.','B Economic pressure is needed to control sugar production.','C Conditions for workers in sugar production should be improved.','D Intensive marketing of sugar has had disastrous consequences.'],'multiple-choice'),
q(37,'Sugar has now become available in large quantities due to a range of agricultural developments.','YES','new techniques, varieties, fertilisers, irrigation systems and much more have turned gleaming white sugar into a ubiquitous chemical','new techniques等列举支持农业变化让糖大量普及；ubiquitous为无处不在。'),
q(38,'Advertisers initially marketed sugar as a luxury product.','NOT GIVEN','Once regarded as a luxury, sugar came to be promoted as a valuable source of energy.','过去被视为奢侈品，不等于广告商当时把它作为奢侈品营销；全文无该营销主体与初始策略信息。'),
q(39,'The invention of high-fructose corn syrup was a positive development.','NO','the recent past has seen worrying new developments in mass sweetening','作者用worrying并关联肥胖，明确与positive相反；便宜只是事实，不代表作者支持。'),
q(40,'High-fructose corn syrup is an ingredient in many processed foods.','YES','having been adopted in the making of soft drinks and a large number of processed foods','adopted in the making对应is an ingredient；many对应a large number。')],['yes-no-not-given','multiple-choice'],
'第6段描述工业生产机制；第7段从产量转消费危害，穿插产业阻力与高果糖糖浆；第8段书评收束。事实句可以支持YES，但立场题还要识别worrying等评价词。',
[{'phrase':'in the face of','meaning':'面对、在……阻力下','explanation':'连接产业阻挠与政府征税，不能误判政府主动鼓励消费。'},{'phrase':'do without','meaning':'没有……也能过','explanation':'末段用could always have done without表达糖并非必需。'}],
[{'text':'But as the consumption of sugar has increased, so has the harm it does, whether to people’s teeth or weight.','explanation':'as…so…形成同步增长关系；so has the harm倒装，主语是harm。无论牙齿还是体重均属危害。'}],
'Q30：Choose A–D. Q37–40：Do the statements agree with the views of the writer? YES / NO / NOT GIVEN。')
add('dreams-1','Do animals dream?｜跨物种睡眠研究',2,1,pars((39,5,'原文第1段'),(39,6,'原文第2段'),(39,7,'原文第3段'),(39,8,'原文第4段')),[
q(1,'Research into sleep and dreaming — 1 __________: similar brain patterns were observed when active and sleeping; indicative of dreaming','rats','the brain patterns of rats running through a maze when awake with their brain patterns during REM sleep','表格此行要求动物类别；清醒走迷宫与REM睡眠对比的是rats。'),
q(2,'Pigeons: when sleeping, pigeons displayed activity in parts of the brain that deal with 2 __________ input; may have been dreaming of flying','visual','brain regions involved in processing visual information','input对应information；空前deal with与processing相对应，所需形容词为visual。'),
q(3,'Whales and dolphins: still have 3 __________ their brain awake when they sleep','half','only half of it, keeping the rest awake','只关闭一半，所以另一半保持清醒。句子逻辑转换但数值不变。'),
q(4,"Whales and dolphins: don't experience REM sleep, as this could affect their sensitivity to 4 __________",'temperature','during REM sleep animals are more vulnerable to extremes of temperature','原因落在末句；temperature而不是前文machinery或lives。'),
q(5,'Whales and dolphins: their dreams are probably not very 5 __________','vivid','non-REM dreams, which are less vivid','less vivid改写为not very vivid；保持形容词词性。')],['table-completion'],
'第1段先定义人类REM与non-REM；第2–4段依次比较鼠、鸽子与鲸豚。表格的物种、研究结果、评论是三个独立维度，不能把评论当作实验证实的结果。',
[{'phrase':'indicative of','meaning':'表明、暗示','explanation':'题干使用的indicative of dreaming仍表示间接证据。'},{'phrase':'vulnerable to','meaning':'易受……影响','explanation':'这里指REM睡眠时更易受极端温度影响，解释鲸豚为什么可能缺少REM。'}],
[{'text':'Intriguingly, REM sleep activity was high in brain regions involved in processing visual information, especially images related to physical activities such as flying, which suggests that this may possibly be what the pigeons were dreaming about.','explanation':'主干报告脑区活动；which suggests和may possibly连续限制推断强度，不能说研究已直接看见鸽子的梦。'}],
'Complete the table below. Choose ONE WORD ONLY from the passage for each answer. 各行研究结果与评论合并为可输入题面，物种及原空号保留。')
add('dreams-2','Do animals dream?｜章鱼行为与研究边界',2,1,pars((40,1,'原文第5段'),(40,2,'原文第6段'),(40,3,'原文第7段'),(40,4,'原文第8段'),(40,5,'原文第9段'),(40,6,'原文第10段')),[
q(6,'Dreaming about past experiences helps us to create lasting memories of them.','TRUE','when events are replayed in dreams, this helps to integrate memories into longer-term storage','replayed events是过去经历，longer-term storage对应lasting memories。'),
q(7,'It is now possible to tell what type of dream a dog is having.','FALSE',"the truth is that we don't know if there is an internal experience of chasing rabbits",'行为可以被观察，但不知道狗的内部体验，直接否定“现在可以判断梦类型”。'),
q(8,"David Scheel's documentary was influential on other research into the sleeping patterns of octopuses.",'NOT GIVEN','In 2019, while making a documentary, David Scheel of Alaska Pacific University in the USA housed an octopus named Heidi in a tank in his living room.','只说明拍摄纪录片时的观察；后续另一报告不等于受其影响，全文没有研究之间的影响关系。'),
q(9,'While it was asleep, the octopus called Costello reacted as if it was hunting.','FALSE','as though he were being attacked by a predator','Costello表现为被捕食者攻击，题干hunting把角色反转；前一只Heidi才像追逐螃蟹。'),
q(10,"Scheel believes more research into octopuses' dreams should be carried out.",'TRUE','as well as outward behaviour, brain imaging is needed','需要脑成像来核验行为解释，说明更多研究仍有必要。'),
q(11,'We may soon be able to share the dreams of other human beings.','FALSE',"we will never be able to experience any animal's dreams. That goes for other humans' dreams too.",'never与soon be able相反，后句明确将结论扩展到其他人类。'),
q(12,'Hearing may be an important part of the dreams of some animals.','NOT GIVEN','Dogs primarily navigate the world using smell while spiders rely much more on vibrations.','该段举视觉、嗅觉、振动，但没有讨论hearing在梦中的地位；不能自行把振动等同听觉。'),
q(13,'Interest in the reasons why humans dream has increased greatly in recent times.','NOT GIVEN','better understanding of these purposes might shed light on the true purpose of our own dreams','全文谈研究前景，没有比较近期与过去关注度，故不存在increased greatly的依据。')],['true-false-not-given'],
'这六段形成完整推理：记忆功能→无法读取主观体验→两只章鱼的观察→方法限制→跨感官想象→研究前景。做完逐题圈出“观察结果、解释、进一步研究”三类语句。',
[{'phrase':'let alone','meaning':'更不用说','explanation':'强调连清醒体验都难理解，更不能自信描述动物梦境。'},{'phrase':'shed light on','meaning':'帮助理解、阐明','explanation':'末句表达潜在研究价值，不表示关注度已经上升。'}],
[{'text':'He argues that as well as outward behaviour, brain imaging is needed to show that the octopuses are replaying sequences of activities from their waking lives in dreams.','explanation':'as well as把现有行为证据与仍需补充的脑成像区分；needed是Q10的关键，不是已完成的研究。'}],
'Do the following statements agree with the information? TRUE / FALSE / NOT GIVEN。原题Q6–13；NG对照完整原篇后确认，未用裁切缺失信息制造答案。')
map1=pars((43,5,'A'),(43,6,'B'),(43,7,'C'))
map1[-1]['text']+=' '+clean(B['44'][1])
map1[-1]['page']=43
map1[-1]['pages']=[43,44]
add('mapungubwe-1','Mapungubwe｜农业、居所与社会等级',2,2,map1,[
q(16,"a mention of the location where members of the king's family are thought to have lived",'C','grander residences dotted around the outskirts of Babandyanalo, and these probably belonged to male relatives of the king','male relatives对应king’s family；地点是outskirts，不能把国王hilltop宫殿当成亲属居所。',list('ABCDEFG')),
q(18,'an estimate of the size to which the Mapungubwe community grew','B','The total population of Mapungubwe at its peak in the mid-13th century was around 5,000 people','size指人口规模，peak与around表示高峰估计值；不是面积5 hectares。',list('ABCDEFG')),
q(19,'a mention of agricultural produce being exchanged for other items','A','a surplus that could be traded for needed goods','农牧业产生剩余→交换所需物品，traded对应exchanged。',list('ABCDEFG'))],['matching-information'],
'A以农业剩余解释国家基础；B按地势描述国王与普通居民住处；C补充墓地、王室亲属及地方酋长。人物群体和地理位置逐一对应，避免看到king就选。',
[{'phrase':'at its peak','meaning':'在鼎盛时期','explanation':'人口估计对应一个历史时段，不是现在的人口。'},{'phrase':'probably belonged to','meaning':'大概属于','explanation':'保存考古解释的不确定性，对应题干are thought to。'}],
[{'text':'The kings of Mapungubwe were buried at the top of the hill site in a demarcated area away from the dwellings, while other members of the community were buried at the surrounding valley level.','explanation':'while连接社会等级与墓葬地势对照；buried不是lived，Q16必须继续读下一句亲属居所。'}],
'Which paragraph contains the following information? Write A–G. 保留完整原候选字母；本片段为A–C，C跨PDF43–44页连续接回。')
map_options=['A Not everyone in Mapungubwe used gold as a form of payment.','B Items of gold were placed close to where Mapungubwe kings were buried.','C The most valuable item discovered in Mapungubwe was a sceptre made of gold.','D The way gold was decorated in Mapungubwe was also practised in another kingdom.','E Working with gold was a respected occupation in the Mapungubwe community.']
add('mapungubwe-2','Mapungubwe｜贸易、器物与衰落',2,2,pars((44,2,'D'),(44,3,'E'),(44,4,'F'),(44,5,'G')),[
q(14,'a mention of the uncertainty regarding the purpose of certain objects','E','The figures may have been used in ceremonies as offerings to ancestors, but their precise function is not known.','不确定性是precise function is not known，对象为figures；不是所有出土器物用途均不明。',list('ABCDEFG'),'matching-information'),
q(15,'the likelihood that a climatic factor increased the problems Mapungubwe faced','G','a situation that may have been brought to a crisis point by a series of droughts','droughts是气候因素，进一步加剧过度人口带来的资源压力。',list('ABCDEFG'),'matching-information'),
q(17,'a reference to people who brought goods by ship','D','merchants travelling from India by sea','merchants是带货商人，by sea对应by ship。',list('ABCDEFG'),'matching-information'),
q('20–21','The archaeological record reveals information about gold and the kingdom of Mapungubwe. Which TWO pieces of information are mentioned by the writer?',['B','D'],'These objects were all found at the royal burial site','B对应王室墓地；D由“found nowhere else except Great Zimbabwe”支持。C把“可能是权杖”升级为“最有价值”，原文没有；E无职业声望信息。',map_options,'multiple-choice-multiple'),
q(22,"The Mapungubwe community's 22 __________ is indicated by the amount of professionally made pottery discovered at the site.",'prosperity','another indicator of the prosperity of Mapungubwe society','专业制陶规模是社会繁荣的指标；题干amount与large enough呼应。',None,'summary-completion'),
q(23,'Other finds include round ceramic objects, 23 __________ and figures of various animals','whistles','There are also ceramic discs, and whistles.','ceramic discs已由round ceramic objects改写，下一并列项是whistles。',None,'summary-completion'),
q(24,'as well as models of people with stretched 24 __________.','bodies','humans with elongated bodies and short limbs','stretched对应elongated，而limbs被描述为short，应答bodies。',None,'summary-completion'),
q(25,'It is possible that these had a role in ceremonies to honour 25 __________.','ancestors','used in ceremonies as offerings to ancestors','to honour对应as offerings to，保留祖先的复数。',None,'summary-completion'),
q(26,'In addition, pieces of 26 __________ made from a local metal have been found at the site.','jewellery / jewelry','small jewellery items made from locally sourced copper','local metal具体为copper，题干问金属制成的物品而非金属名；原答案接受英美拼写。',None,'summary-completion')],['matching-information','multiple-choice-multiple','summary-completion'],
'D国际贸易，E陶器与铜饰，F金饰及价值，G衰落原因。E的it is possible/precise function未知和F的may have been均要求保持推断边界；多选要找两条独立直接证据。',
[{'phrase':'as opposed to','meaning':'而不是、与……相对','explanation':'F区分金本身价值和货币功能，不支持“不是所有人使用金币”的数量判断。'},{'phrase':'brought to a crisis point','meaning':'推向危机点','explanation':'G先说人口压力，再用干旱说明加剧因素。'}],
[{'text':'A type of decoration, found nowhere else except Great Zimbabwe, involved the crafting of gold into small rectangular sheets and carving geometrical patterns into it.','explanation':'插入成分说明只有另一王国也有这种装饰法，直接支持多选D；不能误读为“Mapungubwe独有”。'}],
'Q14/15/17：段落信息匹配A–G。Q20–21：Choose TWO letters A–E，顺序不限。Q22–26：Complete the summary. Choose ONE WORD ONLY from the passage.')
ai_raw=re.sub(r'\s+',' ',P[46]['text']+' '+P[47]['text'])
ai_raw=ai_raw[ai_raw.index('In many countries'):].replace(' 46 the transformative',' the transformative').replace(' Reading The medical',' The medical').removesuffix('47 ').strip()
ai_starts=['In many countries','While it is undeniable','In only a few years','We are now seeing','One of the most promising','AI systems need','For these reasons','One of the many difficulties','If we are to reap','Most importantly','The medical profession','Similar difficulties','There are some crucial lessons']
ai_pos=[ai_raw.index(x) for x in ai_starts]+[len(ai_raw)]
ai=[{'label':f'原文第{i+1}段','text':clean(ai_raw[ai_pos[i]:ai_pos[i+1]]),'page':47 if i<7 else 48} for i in range(13)]
ai[-1]['text']=re.sub(r'\s+47$','',ai[-1]['text'])
ai[6]['pages']=[47,48]
add('ai-1','Artificial Intelligence｜公众想象与解决一切的误区',2,3,ai[:3],[
q(27,'What is the writer doing in the first paragraph?','B','Just looking at the media headlines, you might think that we are already living in a future where AI has infiltrated every aspect of society.','you might think标记媒体造成的公众印象，不是作者预测AI一定实现所有益处。',['A predicting the future impact of AI','B describing a public perception of AI','C outlining some possible benefits of AI','D highlighting the breadth of the influence of AI']),
q(28,'When discussing AI solutionism in the second paragraph, the writer','A','this mindset actually jeopardises the value of machine intelligence','jeopardises与disregarding safety/setting unrealistic expectations明确提出这种思维的风险，未追溯起源或列主要支持者。',['A points out a risk involved.','B specifies its probable origins.','C mentions its chief supporters.','D weighs up some pros and cons.'])],['multiple-choice'],
'第1段呈现媒体与公众印象；第2段先承認AI机会，再批评“给足数据就解决一切”的思维；第3段描写该思维从技术圈进入政策圈。读选项时区分作者陈述、媒体宣传与他人信念。',
[{'phrase':'no shortage of','meaning':'大量、不缺','explanation':'描述夸张新闻的数量，不是赞同新闻内容。'},{'phrase':'jeopardise the value of','meaning':'损害……的价值','explanation':'第二段真正的评价落在风险；前面的promising opportunities只是让步。'}],
[{'text':'While it is undeniable that AI has opened up a wealth of promising opportunities, it has also led to the emergence of a mindset that can be best described as “AI solutionism”.','explanation':'While承认机会，主句引入需要批评的心态。Q28问作者在本段做什么，要继续读But后的负面判断。'}],
'Choose the correct letter A, B, C or D. 原题Q27–28。')
ai_options=['A reliability','B funding','C skills','D prejudices','E computers','F equality','G framework','H confidentiality','I approval']
add('ai-2','Artificial Intelligence｜公共部门实施条件',2,3,ai[3:6],[
q(29,'In the fourth paragraph, the writer suggests that many politicians may','C','they fail to realise the complexity around deploying advanced machine learning systems in the real world','unaware of challenges对应fail to realise complexity；国家竞争只是背景。',['A have failed to appreciate the true potential of AI initiatives.','B have misunderstood the function of the machine-learning sector.','C be unaware of the challenges of implementing national AI initiatives.','D be too keen to enter the race to dominate the machine-learning sector.'],'multiple-choice'),
q(30,'Neural networks are a promising area of AI technology for governments. However, many politicians overestimate their capabilities, believing that the mere addition of a neural network will produce solutions and promote 30 __________.','F','does not mean it will be instantaneously more inclusive or fair','inclusive or fair概括为equality；注意摘要描述政治家过度期待，不是作者认可。',ai_options,'summary-completion-options'),
q(31,'Most public sector organisations have not set up the necessary 31 __________ to manage the huge amount of data required to enable AI to function.','G','does not have the appropriate data infrastructure','data infrastructure对应管理数据的framework，不只是computers。',ai_options,'summary-completion-options'),
q(32,'Complex bureaucracy is another issue, as each person involved needs 32 __________ to access the relevant data, which is often spread across different departments.','I','each require special permissions to be accessed','permissions对应approval；confidentiality是保密性，不是取得访问权。',ai_options,'summary-completion-options'),
q(33,'But the main problem is that few public sector employees have the 33 __________ to take full advantage of machine intelligence.','C','lacks the human talent with the right technological capabilities','capabilities概括为skills；Above all对应摘要main problem。',ai_options,'summary-completion-options')],['multiple-choice','summary-completion-options'],
'三段从政治承诺缩到神经网络，再落到数据基础设施、跨部门权限与人才。摘要同义链为fair→equality、infrastructure→framework、permissions→approval、capabilities→skills。',
[{'phrase':'reap the benefits of','meaning':'获得……的益处','explanation':'题干take full advantage of与此表达同义。'},{'phrase':'buried in bureaucracy','meaning':'被繁琐行政流程束缚','explanation':'随后跨部门special permissions解释这一障碍具体是什么。'}],
[{'text':'But what many politicians do not understand is that simply adding a neural network to a problem will not automatically mean that you’ll find a solution.','explanation':'主语是what从句，表语that从句否定自动解决问题。simply/automatically共同限定“加了就有效”的因果推断。'}],
'Q29：Choose A–D. Q30–33：Complete the summary using words A–I. 原选项完整保留。')
add('ai-3','Artificial Intelligence｜部署、安全与公众担忧',2,3,ai[6:10],[
q(36,"Stuart Russell's proposals regarding the use of AI are impractical.",'NO','a more sensible and realistic approach that focuses on simple everyday applications of AI','作者赞成sensible and realistic，明确与impractical相反；无需评价Russell现实成就。'),
q(37,"Rodney Brooks' view has attracted unfair criticism from supporters of AI.",'NOT GIVEN','almost all innovations in robotics and AI take far, far, longer to be really widely deployed','全文只引用Brooks对部署耗时的判断，没有支持者如何回应他的观点，unfair更无依据。'),
q(38,'Nowadays, the need to protect AI systems is always taken into account when they are set up.','NO','AI security remains an often overlooked topic when machine learning systems are installed','often overlooked直接反驳always taken into account；不是只缺少资料。'),
q(39,"In order to benefit from AI and minimise the harms, we have to explore people's concerns about its use.",'YES','we need to have a discussion about AI ethics and the distrust that many people have towards machine learning','concerns概括ethics与distrust；need to have a discussion支持have to explore。')],['yes-no-not-given'],
'第7段引专家批评不现实的宣传；第8段指出对抗攻击与安全忽视；第9段要求讨论伦理和不信任；第10段划清能力与幻想。判断观点时保留作者态度词与量词。',
[{'phrase':'adversarial attacks','meaning':'对抗攻击','explanation':'本段随即解释为一个恶意AI诱导另一个AI错误预测。'},{'phrase':'separate … from …','meaning':'将……与……区分开','explanation':'最后要求区分实际能力和幻想，呼应开篇对夸张宣传的批评。'}],
[{'text':'Many researchers have warned against the rolling out of AI without appropriate security standards and defence mechanisms. Still, AI security remains an often overlooked topic when machine learning systems are installed.','explanation':'第一句是研究者警告，Still后的第二句才是实际部署状态。被警告不等于每次实施都已做到，正好反驳Q38。'}],
'Do the following statements agree with the claims of the writer? YES / NO / NOT GIVEN. 原题Q36–39；Q37已核对全文无回应信息。')
add('ai-4','Artificial Intelligence｜医疗与司法失败案例',2,3,ai[10:13],[
q(34,'The medical profession experimented with an AI programme, but their experts had little faith in its 34 __________, and the programme was abandoned.','A','human experts found it hard to trust the machine','hard to trust是对reliability的信任不足；不是缺钱funding。',ai_options),
q(35,'US courts also abandoned the use of algorithms when it was found that these reflected and magnified the existing 35 __________ within the legal profession.','D','The system was found to amplify structural racial discrimination','amplify对应magnified，racial discrimination对应prejudices；没有说系统只缺技能。',ai_options)],['summary-completion-options'],
'三段构成案例—平行案例—结论：医疗系统因专家难以信任而被多数试点医院弃用；司法算法放大已有歧视；作者推出AI不适合所有问题。不能把两个失败机制混写。',
[{'phrase':'for the sake of','meaning':'仅仅为了','explanation':'for the sake of AI批评为使用技术而使用技术，不等于拒绝所有技术。'},{'phrase':'amplify structural racial discrimination','meaning':'放大结构性的种族歧视','explanation':'这里算法强化既存偏见，摘要用reflected and magnified改写。'}],
[{'text':'Even though it was developed to deliver the best recommendations, human experts found it hard to trust the machine.','explanation':'Even though区分设计目标与实践反应。“本为提供最佳建议”不等于建议实际上可靠，Q34看后半句。'}],
'Complete the summary using the list of words A–I. Write the correct letter A–I. 原题Q34–35。全篇主旨Q40需阅读全文，未作为本裁切的局部题。')
merged=cases[-2]
tail=cases.pop()
merged['title']='Artificial Intelligence｜部署边界、医疗与司法案例'
merged['paragraphs'].extend(tail['paragraphs'])
merged['questions'].extend(tail['questions'])
merged['questionTypes'].append('summary-completion-options')
merged['intensive']['structure']+=' 后三段以医疗信任与司法偏见两个案例展示失败机制，再收束到并非所有问题都适合自动化。'
merged['intensive']['phrases'].extend(tail['intensive']['phrases'])
merged['intensive']['sentences'].extend(tail['intensive']['sentences'])
merged['instructions']='Q36–39：YES / NO / NOT GIVEN。Q34–35：选词摘要填空，完整选项A–I保留。按原文顺序编排本段题组，原题号不变。全篇主旨Q40需阅读全文，未列入裁切。'
footnotes={
 'rd-c21-davies-1':['* philanthropic: seeking to promote the welfare of others, often by charitable funding','** Old Master: a highly respected artist of great skill who worked in Europe before about 1800'],
 'rd-c21-davies-2':['*** Impressionist: an artist with a style of painting that developed in France in the late 1800s by Renoir, including his well-known painting La Parisienne'],
 'rd-c21-mapungubwe-1':['* palisade: typically a row of closely placed, high vertical wooden or iron posts used as a means of defence']}
for c in cases:
 for p in c['paragraphs']:
  p['text']=p['text'].replace('ProvençalL andscape','Provençal Landscape').replace('I-hour float','1-hour float')
 c['wordCount']=sum(len(re.findall(r"\b[\w'-]+\b",x['text'])) for x in c['paragraphs'])
 if c['id'] in footnotes:c['footnotes']=footnotes[c['id']]
save()
if __name__=='__main__':print('saved',len(cases),'cases')
