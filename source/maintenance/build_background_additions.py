from pathlib import Path
import json

OUT=Path(__file__).resolve().parent
topics=[]
def add(id,title,intro,context,translation,concepts,language,prompt,model,explanation,practice,review):
    topics.append(dict(id=id,title=title,intro_zh=intro,context_en=context,context_zh=translation,
        concepts=[dict(term=a,meaning_zh=b) for a,b in concepts],
        language=[dict(chunk=a,meaning_zh=b,structure=c,example_en=d,error_zh=e) for a,b,c,d,e in language],
        model=dict(prompt_en=prompt,answer_en=model,explanation_zh=explanation),
        practice=[dict(prompt=a,answer=b,explanation_zh=c) for a,b,c in practice],
        optional_review=dict(prompt_en=review,checkpoints_zh=['换一个情境解释相同机制，不照抄原例。','使用两组新表达；不需要强行塞入全部词组。','记下仍需提示的用法，可以继续学习其他新内容。']),
        status='基础话题补齐 · 原创教学，非当季回忆题',sourceIds=[]))

add('crime','犯罪与惩罚：预防、回应与重新融入',
'讨论这类题时先拆目的：保护公众、阻止违法、让行为承担后果、降低再次违法的可能。不同措施服务不同目的。不要把“处罚越重越有效”或“给工作就能解决犯罪”写成无条件事实；要解释中间机制及适用范围。以下社区情境为教学虚构。',
'''Imagine a town discussing how to respond to repeated bicycle theft. Some residents want tougher penalties because they believe offenders should face clear consequences. Others want better lighting and secure bicycle storage, which could make theft more difficult. These proposals address different stages of the problem. A penalty responds to an offence, while a secure storage area aims to prevent one. A third proposal focuses on people who have already served a sentence. It would offer training and help them look for lawful employment. This support would not remove their responsibility for the original offence. Its purpose would be to make another offence less attractive or less necessary. None of these ideas should be treated as a guaranteed solution. Residents would still need to consider cost, implementation and evidence of results. A strong argument can support proportionate punishment while also explaining why prevention and rehabilitation deserve attention.''',
'一个虚构小镇要处理反复发生的自行车盗窃。加重处罚回应已发生的行为，照明和安全存放设施试图减少机会，培训与就业支持关注服刑后的生活。它们针对不同阶段，可以同时讨论。支持重新融入社会不等于免除责任，也不能保证不会再次违法；还要看成本、执行与结果。',
[('deterrence','威慑：让潜在违法者预期后果，从而可能放弃行动。'),('rehabilitation','帮助行为人改变行为、获得重新生活的能力。'),('proportionate punishment','惩罚与行为严重程度相称；proportionate 强调比例适当。')],
[
('deter someone from doing something','阻止某人产生行动意愿','deter + 人 + from + -ing','Visible security measures may deter people from stealing bicycles.','不能说 deter people to steal；may 避免把效果绝对化。'),
('hold someone accountable for','让某人为某事承担责任','hold + 人 + accountable + for + 名词/-ing','Offenders should be held accountable for the harm they cause.','responsible 与 accountable 都可涉及责任，不要把 accountable 当动词。'),
('serve a sentence','服刑','serve + a prison sentence','People who have served a sentence may need support when looking for work.','sentence 在此是刑期，不是语法中的句子。'),
('address the causes of','处理……的成因','address + the causes of + 问题','Prevention programmes should address the causes of repeated offending.','address 作及物动词，不能写 address to the causes。'),
('reduce the risk of reoffending','降低再次违法的风险','reduce + the risk of + -ing','Training may reduce the risk of reoffending by widening lawful choices.','risk 降低不等于行为一定消失。'),
('reintegrate into society','重新融入社会','reintegrate into + 群体','Stable work can help former offenders reintegrate into society.','帮助结构可用 help someone do，不能写 help someone doing。')],
'Should a town rely only on tougher penalties to reduce bicycle theft?',
'''Tougher penalties may be justified when repeated theft causes serious harm, but punishment alone would leave some problems untouched. If bicycles are easy to steal, secure storage could reduce opportunities for theft before it happens. Support after a sentence may also help people find lawful work. This does not mean removing responsibility: offenders can face consequences while receiving practical help to change their behaviour. I would therefore combine proportionate penalties with prevention and carefully evaluated support.''',
'先给有限立场，再分别解释“减少机会”和“增加合法选择”的机制，最后回应“支持等于纵容”的潜在反对。没有用虚构统计证明政策必然有效。',
[('改写：Training can prevent all former offenders to commit crimes.','Training may help some former offenders avoid committing further offences.','原句同时存在绝对范围 all、效果强度 prevent all 和结构错误；也可用 deter ... from committing，但语义侧重点不同。'),('安全存车设施与服刑后的就业支持，分别主要处理哪个环节？','前者处理犯罪机会；后者支持行为改变和重新融入。','它们不是同一措施的同义改写，论证时要分开解释。')],
'A school wants to reduce repeated rule-breaking. Explain one preventive measure and one form of support, without equating school discipline with criminal sentencing.')

add('government','政府与公共支出：预算、优先次序与长期成本',
'这类讨论最常见的空洞句是“政府应该投入更多资金”。完整论证需要说清钱花在哪、谁受益、通过什么机制改善、会挤占什么资源。把建设费用和持续运营费用分开，把公共收益和某个使用者的收益分开。以下预算为虚构教学条件。',
'''A council has enough money to begin one major project this year: a new sports hall or repairs to several local libraries. The sports hall could give residents an indoor place to exercise, but the council would also need to pay for staff, cleaning and maintenance. Library repairs would be less visible, yet they could keep existing study spaces open. Choosing between the projects requires more than comparing the number of people who might attend an opening ceremony. The council should ask who currently lacks access, whether another facility already meets the need and how the service would be funded in later years. A smaller version of the sports project might leave some money for urgent repairs. This would involve compromise rather than a perfect solution. Public spending decisions can therefore be evaluated through need, expected benefit, opportunity cost and the ability to maintain a service over time.''',
'虚构地方议会只能先做一个项目：体育馆或图书馆修缮。新建筑除了建造，还需要人手和维护；修缮虽然不显眼，却能维持现有服务。比较时看需求缺口、实际受益、放弃的其他用途和长期运营能力，也可提出缩小规模的折中方案。',
[('opportunity cost','把资源用于一处时，放弃的其他可行用途。'),('capital cost / running cost','一次建设投入与持续运营支出。'),('public benefit','收益可能超出直接付费的使用者，但仍需解释具体如何产生。')],
[
('allocate funds to','向……分配资金','allocate + funds + to + 项目','The council could allocate funds to urgent library repairs.','allocate 是分配；不等于最终资金已有效使用。'),
('prioritise essential services','优先保障基本服务','prioritise + 名词','Local authorities may need to prioritise essential services.','不要用 priority 作动词。'),
('meet an unmet need','满足尚未得到满足的需求','meet + an unmet need','An evening study room could meet an unmet need among shift workers.','需求不能只用“大家都需要”断言，给具体群体与场景。'),
('cover running costs','支付运营成本','cover + costs','Ticket income may not cover running costs.','cover 在此不是遮盖，也不是说把成本降低。'),
('divert resources from','把资源从……转走','divert + resources + from + 原用途','A large project could divert resources from basic maintenance.','要给出来源用途，否则代价不具体。'),
('be accountable to','对……负有说明责任','be accountable to + 人/群体','Public bodies should be accountable to the communities they serve.','to 接责任对象；for 接需要承担责任的行为或结果。')],
'How should a council choose between a new leisure facility and repairs to existing public buildings?',
'''The council should first identify which need is least well served. If the town already has several affordable sports centres, repairing unsafe library rooms may offer a stronger immediate benefit. The decision should also include running costs, because opening a building is only the start of providing a service. A smaller leisure project could still be considered if it leaves enough funding for essential repairs. This approach would connect spending to local needs instead of assuming that the newest project is always the most valuable.''',
'用 if 限定判断条件，说明“已有替代服务”怎样影响优先次序，再把预算扩展到运营成本。最后提出折中，而非机械站队。',
[('补全并解释介词：The council allocated funds ___ repairs but remained accountable ___ residents.','to; to','两个 to 分别表示资金去向和责任对象；accountable for 则用于具体行为。'),('“新馆建设费已付清，所以该项目没有后续成本。”问题在哪里？','混淆一次建设费用和运营费用。','需要说明人员、清洁和维护等长期支出；不能仅凭建设完成推断资金可持续。')],
'Your school can fund a new computer room or extend library opening hours. Compare the options using need, benefit and running costs.')

add('society','社会与代际：参与机会、照护与自主选择',
'社会话题不能把“老年人”“年轻人”写成同质群体。先定义具体障碍，再讨论服务和选择。独立生活不等于完全不需要帮助；社会参与不等于必须工作。以下社区服务设计为教学虚构。',
'''A community centre plans to move all activity bookings online. For some residents, this would make joining a class easier because they could book at any time. Others might find the change difficult if they do not have a suitable device or are unfamiliar with the website. Age alone would not explain every difference: some older residents use digital services confidently, while some younger residents have limited internet access. The centre could keep a telephone option and provide short demonstrations at reception. It could also ask residents which activities they want instead of assuming that everyone of the same age shares the same interests. Support can increase independence when it helps people make their own choices. However, a service that decides everything for its users may do the opposite. A useful discussion of social inclusion therefore considers practical access, personal preferences and the opportunities people have to participate in community life.''',
'社区中心想把预约全部转到线上。有的人更方便，有的人受设备、网络或操作经验限制。年龄不是唯一解释。保留电话入口、提供演示、询问活动偏好，可以让帮助服务于自主选择。讨论社会包容时，需要同时看实际可达性、偏好和参与机会。',
[('social inclusion','不同群体能够参与服务和社区生活，避免因条件受限而被排除。'),('independence','能够作出并实施自己的选择，不等于拒绝一切支持。'),('digital exclusion','因设备、网络、技能或设计障碍无法方便使用数字服务。')],
[
('participate in community life','参与社区生活','participate in + 活动/领域','Accessible events can help more residents participate in community life.','participate 不直接接名词，通常需要 in。'),
('remove barriers to participation','减少参与障碍','barriers to + 名词/-ing','A telephone booking option could remove barriers to participation.','to 为介词，不接动词原形 participate。'),
('maintain independence','保持自主生活能力','maintain + independence','Practical support can help people maintain independence.','independent 是形容词；independence 才是名词。'),
('have access to support','能够获得支持','have access to + 名词','Residents should have access to support when using the new system.','access 通常不可数；不是 have an access。'),
('take individual needs into account','考虑个体需要','take + 名词 + into account','Service design should take individual needs into account.','不要把一个人的困难推广为整个年龄群体的特征。'),
('place pressure on','给……带来压力','place pressure on + 对象','Long journeys to appointments can place pressure on family carers.','pressure 在此通常不可数；具体说明压力来自时间还是费用。')],
'Should public services become entirely digital?',
'''Digital services can save time, but an entirely online system may exclude people who lack reliable access or need assistance. A community centre, for instance, could make online booking its main option while keeping telephone support. This would preserve the convenience of the new system without assuming that every resident has the same resources. The aim should be to widen participation and maintain personal choice. Staff could then review which channels residents actually use before making further changes.''',
'让步后定位风险人群，用同一服务的多个入口解决具体障碍；结尾加入观察使用情况，避免从印象直接推断所有人的需要。',
[('修订：Old people cannot use technology, so they must not book online.','Some residents may need help with online booking, so the centre should offer support and an alternative channel.','修复群体刻板概括，同时保留个人选择。不能只替换成 more elderly people 仍断言。'),('“帮助别人”什么时候可能削弱自主性？','替他们决定全部事项，而不是帮助他们实现自己的选择时。','答案需要区分支持与代替决定，不能把所有帮助都视为依赖。')],
'A university offers all advice through an app. Explain how it could support students with different needs while preserving their choices.')

add('space','太空与科研：研究价值怎样与现实需求比较',
'太空题不要直接套“环保很重要”的段落。先分清科学探索、提供具体服务的技术项目和其他公共支出；比较的是预算取舍、目标与不确定性。以下任务设计完全虚构，不报告真实航天项目成果。',
'''Imagine a research agency proposing two projects. One would study a distant object to answer a scientific question. The other would test an instrument intended to improve observations of conditions on Earth. Supporters might defend the first project because basic research can expand knowledge even when its practical uses are unclear. They might defend the second through its proposed service. These are different arguments, and neither should be replaced by a vague claim that all technology is useful. Critics could reasonably ask about cost, uncertainty and competing public needs. The agency should explain what each project aims to discover, how progress would be assessed and which benefits remain uncertain. It should also avoid presenting a possible future application as a guaranteed result. A balanced position can recognise the value of long-term research while demanding clear priorities and responsible spending. The key is to compare specific projects and trade-offs rather than treating space research as a single activity with a single purpose.''',
'虚构研究机构提出两个项目：回答远处天体的科学问题，以及试验可能用于观测地球状况的仪器。知识价值与具体服务价值是不同论据，都需解释目标、成本与不确定性。可能的未来应用不能当作已保证收益；支持研究也可以要求明确优先次序。',
[('basic research','首先为了理解问题而开展的研究，未必有即时用途。'),('practical application','知识或技术用于解决具体任务的方式。'),('uncertain returns','投入可能产生价值，但价值的大小与时间尚不确定。')],
[
('advance scientific understanding','推进科学理解','advance + scientific understanding of + 问题','The project aims to advance scientific understanding of the object.','aims to 表示目标，不等于已实现。'),
('have practical applications','具有实际应用','have + practical applications in + 领域','A new instrument may have practical applications in environmental observation.','不能以 may 推导“已经证明有效”。'),
('justify public investment','论证公共投入的合理性','justify + 名词/-ing','Researchers should explain how the project could justify public investment.','justify 不等于 guarantee；不要写 justify to invest。'),
('compete for limited funding','争取有限资金','compete for + 资源','Research programmes compete for limited funding with other services.','for 是争取对象；with 是共同竞争的其他项目。'),
('assess long-term value','评估长期价值','assess + 名词','A review should assess long-term value as well as immediate cost.','assess 是评估，不等于确认一定有价值。'),
('lead to new insights','带来新认识','lead to + 名词/-ing','An unexpected result could lead to new insights.','lead to 后不能直接接 discover；可用 discoveries。')],
'Is immediate practical benefit the only reason to fund scientific exploration?',
'''Immediate usefulness is an important consideration, but it should not be the only test for scientific funding. Some projects aim to answer questions whose applications are not yet clear. That uncertainty does not automatically make them worthless, although it does mean that supporters should avoid promising benefits they cannot demonstrate. I would fund a limited range of well-defined exploratory projects alongside essential services, with clear budgets and regular reviews. This would allow room for discovery while recognising that public resources have other valuable uses.''',
'区分“当前用途不清楚”和“毫无价值”，再给有边界的支持：有限范围、明确预算与定期审查。段落不使用虚构科研数据。',
[('判断推理：The instrument may have practical uses. Therefore, the project will definitely pay for itself.','不能推出。','may 与 definitely 强度不一致；有用途也不代表财务收入足以覆盖成本。'),('补全：The programme competes ___ funding and could lead ___ new insights.','for; to','compete for 资源；lead to 结果。注意结果仍是可能而非确定。')],
'A city considers funding experimental energy research. Explain knowledge value and uncertainty without claiming that a future invention is guaranteed.')

(OUT/'background-additions.json').write_text(json.dumps({'version':1,'checkedAt':'2026-09-16','note':'四个旧目录明确缺少的背景读本；语境、例句和教学全部原创。属于基础补齐，未列为本季回忆题。','sources':[],'topics':topics},ensure_ascii=False,indent=2),encoding='utf8')
print('Created',len(topics),'background lessons and',sum(len(x['language']) for x in topics),'usage units')
