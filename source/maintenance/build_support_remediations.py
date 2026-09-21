import json, re, html, hashlib
from pathlib import Path
from reviewed_source_notes import annotate_source_html
from reviewed_text_corrections import correct_transcription
from pypdf import PdfReader

ROOT=Path(__file__).parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
LIB=BOOK.parent/'materials-library'
D=Path('D:/Codex-IELTS-2026-09-14/expansion-2026-09-14')
C21=LIB/'user-materials/Cambridge IELTS 21 - Academic.pdf'
AUDIT=json.loads((ROOT/'audit-content-20260919.json').read_text(encoding='utf8'))
BY={x['id']:x for x in AUDIT['items']}
R=PdfReader(C21)
OUT={'date':'2026-09-19','scope':'36项非读写未达标替换；38项可疑保留后补充。真实问题和转写与原创参考作答分开；共用材料明确复用，不计为不同原题。','replacements':[],'supplements':[],'cases':[],'coverage':{},'assetsToCopy':[]}
SOURCE_MAP=json.loads((BOOK/'source-map.json').read_text(encoding='utf8'))

def esc(s):return html.escape(str(s))
def para(s):return ''.join('<p>'+esc(p)+'</p>' for p in s.split('\n\n'))
def ref(label,path,page=1,url=None):
    absolute=str(path).replace('\\','/')
    normal=lambda s:re.sub('/+','/',s.replace('\\','/')).lower()
    matched=next((r for r in SOURCE_MAP if normal(r['source'])==normal(absolute)),None)
    if matched: relative=matched['packaged']
    else:
        relative='原始参考/support-'+hashlib.sha256(absolute.encode()).hexdigest()[:8]+'-'+Path(path).name
        if not any(x['target']==relative for x in OUT['assetsToCopy']):OUT['assetsToCopy'].append({'source':absolute,'target':relative,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()})
    return {'label':label,'path':relative,'page':page,'url':url,'originalPath':absolute}
def c21ref(test,page):return ref(f'Cambridge IELTS 21 Academic · Test {test} · 物理页{page} / 印刷页{page-1}',C21,page)
def link(r):return f'<a href="{esc(r["path"])}#page={r["page"]}" target="_blank" rel="noopener">{esc(r["label"])}</a>'
def add(aid,kind,case,title,body,refs,ver=None):
    a=BY[f'audit-{aid:03d}']
    body=annotate_source_html(body)
    item={'auditId':a['id'],'target_selector':a['target_selector'],'anchor':a['anchor'],'caseIds':[case],'title':title,'teachingHtml':body+'<p>完整原件：'+ '；'.join(link(r) for r in refs)+'</p>','sourceRefs':refs,'verification':{'materialType':'正式考试题面／官方样题','sourceRead':True,'promptAuthentic':True,'answerType':'原创参考作答或原件可核对答案；详见正文','status':'达标（本次补充或替换范围）','originalStatus':a['status'],'doesNotCertifyUnchangedOriginal':kind=='supplements',**(ver or {})}}
    OUT[kind].append(item)
    return item

def speak(aid,cid,title,test,page,part,questions,answer,notes,kind='replacements'):
    source=R.pages[page-1].extract_text()
    norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
    assert all(norm(q) in norm(source) for q in questions), (cid,questions)
    h='<h4>'+esc(title)+'</h4><p>本单元使用真实 '+part+' 问题。先看完整问题组，再比较参考作答如何逐问落实内容；人物经历为参考作答中的示例，不是原题事实或统一标准答案。</p><ol>'+''.join('<li>'+esc(q)+'</li>' for q in questions)+'</ol><h4>参考作答</h4>'+para(answer)+'<h4>逐项解释与练习</h4>'+para(notes)+'<p>练习：保留题目中的对象、时间和问法，换成自己的真实经历。先口头作答，再对照上面的具体内容逐项检查；不需要逐字背诵参考作答。</p>'
    item=add(aid,kind,cid,title,h,[c21ref(test,page)],{'promptMatch':'全部问题经归一化逐字匹配原PDF对应页','answerWordCount':len(re.findall(r"\b[\w]+(?:[’'-][\w]+)*\b",answer)),'answerType':'原创参考作答，回答正式原题；不称官方范文或唯一答案'})
    OUT['cases'].append({'id':cid,'title':title,'source':c21ref(test,page),'part':part,'questions':questions,'answer':answer,'explanation':notes})
    return item

speak(25,'support-speaking-c21-t1-p2','旅游信息：一次具体使用经历',1,32,'Part 2',[
'Describe a time when you used information for tourists, for example from a guidebook or online.','where you got this information','what place this information was about','what information you got','and explain whether this information was very helpful for you.'],
"I'd like to talk about some information I found on a museum's website before a weekend trip. I was planning to visit the city with my cousin, and neither of us knew the area well. We only had one afternoon there, so I wanted to find out what we could realistically fit in.\n\nThe website explained how to get from the railway station to the museum. It also showed the opening hours, the ticket prices and the times of the guided tours. The most useful detail was that the last admission was earlier than the closing time. Without that warning, we might have arrived too late.\n\nI saved the directions on my phone and booked a tour for the middle of the afternoon. The information was helpful because we spent less time making decisions after we arrived. One bus stop had temporarily moved, so we still had to ask someone for help. Even so, having the basic plan meant that this small problem didn't spoil the visit.",
'题卡四点依次落在 museum website（来源）、museum in a city（地点）、交通／开放时间／最后入场时间（内容）、节省决策时间但公交站临时改变（有帮助与局限）。最后一项不是只说 useful：last admission 的具体后果解释了价值。练习核对：来源不应只说 online 而不说明什么网页；也无需编成网页永远准确。')
speak(26,'support-speaking-c21-t3-p3-future','园艺的未来：有条件地预测',3,75,'Part 3',['Will gardening be a more popular hobby in the future?'],
"I think it could become more popular, especially among people who want a break from screens. Growing something gives them a practical activity to concentrate on, and even a few herbs on a windowsill can be satisfying. There are also more ways to share advice online, which might help beginners keep going. However, I wouldn't expect everyone to take it up. People with very small homes may have little space, and plants still need regular care. So I would predict more interest in small-scale gardening, rather than assume that everybody will want a large garden.",
'could / might / would predict 表示预测而非已发生事实。screen break 和 advice 两条理由之后补空间与照料限制，结论收窄到 small-scale gardening。问题是未来普及程度，不能全程只描述自己家植物。')
speak(27,'support-speaking-c21-t3-p3-homes','住宅与花园：解释实际好处',3,75,'Part 3',['What are the advantages of having a home with a garden?'],
"One advantage is having an outdoor space that the household can use without travelling anywhere. Parents might let their children play nearby while they do something else, and adults can sit outside after work. A garden can also give people some control over their surroundings: they can grow flowers, put up a table or create a quiet corner. Those benefits depend on how much time and money they can spend maintaining it, though. A neglected garden may become another responsibility rather than a place to relax. So the space itself is useful, but looking after it is part of the benefit.",
'先答 advantage，再用 children / after work 说明谁受益；control over surroundings 后接三种具体行动，避免只堆 convenient、beautiful。末尾维护条件不否定优点，而是限制其适用范围。')
speak(28,'support-speaking-c21-t3-p1-shopping','购物方式与不必要消费',3,75,'Part 1',['When you go shopping, do you usually pay for things by cash or by card?','Have you ever spent money on something you didn\'t need?'],
"I usually pay by card because I don't like carrying a lot of cash. It's also easier to check what I've spent afterwards. I still keep a little cash with me in case a shop's card machine isn't working.\n\nYes, I once bought a pair of trainers mainly because they were on sale. I already had a similar pair, so I hardly wore the new ones. It wasn't a disaster, but it did make me stop and think before buying something just because the price looks attractive.",
'两题分开回答：usually 对应现在的习惯与一个例外；Have you ever 对应 yes 后的一次经历，主要叙述用过去时。sale 不等于 need，结尾明确反思怎样从经历产生。')
speak(29,'support-speaking-c21-t2-p3-honesty','诚实与儿童：比较观点',2,54,'Part 3',['Do you think children are more honest than adults?','Why do adults tell children it\'s important to be honest?'],
"In some situations they seem more direct. A young child may say exactly what they think about a meal, while an adult might hide a negative opinion to avoid hurting someone. But being direct isn't always the same as being honest. Children can also hide mistakes when they are afraid of getting into trouble.\n\nAdults probably emphasise honesty because it helps people trust each other. If a child admits breaking something, the parent can deal with the actual problem. If the child invents a story, everyone has to work out what happened first. The lesson is more convincing when adults admit their own mistakes too.",
'第一题不把 children more honest 当成普遍事实，先用餐评价区分 direct 与 honest，再提供反向情况。第二题 trust 的抽象理由由 breaking something 的具体后果说明。练习：删掉具体例子再读，会发现理由为何显空；补回因果链。')
speak(30,'support-speaking-c21-t3-p3-apartments','公寓里种植：给可行方案',3,75,'Part 3',['How could people living in apartment blocks grow plants and vegetables?'],
"They could start with containers on a balcony or a sunny windowsill. Herbs are a practical choice because people can grow small amounts and use them in everyday cooking. If the building has a shared outdoor area, residents might ask for permission to create a communal garden. That could provide more space, but they would need to agree on who waters the plants and how the produce is shared. Not every flat has enough sunlight, so I wouldn't present balcony gardening as a solution for everyone. The available light and the building's rules should guide the choice.",
'题目 How could 要求方法，不是只说种植很好。containers、communal garden 是两个层次；light / permission / shared care 说明实施条件。could 不保证所有公寓可用共享区域。')
speak(31,'support-speaking-c21-t2-p3-advertising','广告的准确性与购买决定',2,54,'Part 3',['Are there any claims in advertisements that are sometimes not true?','Why do people still buy things even when they know advertisements aren\'t completely accurate?'],
"Some advertisements make results sound more certain than they really are. For example, a product may be presented as if it will solve a problem for everyone, although people use it under very different conditions. I would distinguish that from an obvious joke, which viewers are not expected to take literally.\n\nPeople may still buy the product because accuracy isn't their only concern. They might trust the brand, like the design or simply need something quickly. A customer can doubt a dramatic promise and still believe that the product will be good enough for an ordinary purpose. That doesn't mean misleading claims are acceptable.",
'第一问是 claims not true，回答把过度承诺与明显玩笑区分。第二问解释消费者为何买而不是重复广告有影响。结尾明确解释行为不等于为误导辩护；原题没有给具体品牌，不要编成调查事实。')
speak(32,'support-speaking-c21-t4-p1-bread','面包与日常饮食',4,97,'Part 1',['When do you usually eat bread?','Have you tried any kinds of bread from other countries?'],
"I usually have bread at breakfast, especially when I need to leave home early. I toast a couple of slices and eat them with an egg. At weekends I have more time, so I sometimes make a different breakfast instead.\n\nYes, I've tried a French baguette from a bakery near my home. I liked the contrast between the crisp outside and the soft middle. I wouldn't say I'm an expert on French bread, but I'd happily buy it again, especially to share with friends at lunch.",
'When 用早餐与周末对比给出真实时间；Have you tried 用已试过的 baguette 再描述口感。reference answer 是原创答题示例，题面来自 Test4；不能把示例体验当成考生必须具备的经历。')
speak(33,'support-speaking-c21-t1-p1-hair','理发：习惯与最近变化',1,32,'Part 1',['Where do you go to get a haircut?','Have you changed your hairstyle recently?'],
"I normally go to a small barber's near my flat. The same person usually cuts my hair, so I don't have to explain what I want every time. It's convenient enough that I can fit a visit in after work.\n\nYes, I had it cut much shorter about a month ago. I'd been getting tired of drying it every morning, and I wanted something easier to look after. It took a few days to get used to the change, but now I'm glad I did it.",
'Where 的直接答案在首句，后面解释选择原因；recently 题答 a month ago 后叙述剪发动机和适应过程。get a haircut 是接受理发服务，不能一律替换成 I cut my hair（可能表示自己动手）。')
speak(34,'support-speaking-c21-t4-p2-competitive','有竞争心的人：具体事件支撑性格',4,97,'Part 2',['Describe a person you know who is very competitive.','who this person is','what this person is competitive about','how successful this person is','and explain why you think this person is so competitive.'],
"I'd like to describe a friend I met at university. We used to play badminton together, and he was much more competitive about it than anyone else in our group. Even during a casual game, he remembered the score carefully and tried to work out why he had lost a point.\n\nHe wasn't the best player when we first met, but he practised regularly and gradually started winning more matches. One year he reached the final of a small competition organised by our club. He didn't win, but he was pleased that the extra practice had made a difference.\n\nI think his competitiveness comes from wanting to see measurable progress. He likes having a clear target, and a match gives him immediate feedback. He can get frustrated with himself, although he usually congratulates the other player afterwards. That's why I enjoy playing with him: he takes the game seriously without treating his opponent badly. I wouldn't claim to know everything that motivates him, but improvement seems more important to him than showing off.",
'who=university friend；what=badminton；success=club final但未夺冠；why=measurable progress。第三段用 I think / seems 标明动机推断，避免把性格解释写成已核实的心理事实。竞争心用记分、分析失分、练习行动展示，不只重复 competitive。')
speak(35,'support-speaking-c21-t3-p1-saving','花钱与储蓄：程度和原因',3,75,'Part 1',['Are you generally careful about how much money you spend?','How important is it to you to save money for the future?'],
"Generally, yes. I compare prices before buying anything expensive, and I check my spending at the end of each month. I don't plan every small purchase, though. If I can afford a coffee with a friend, I don't want to turn it into a complicated decision.\n\nIt's quite important to me because having some savings makes unexpected expenses less stressful. I try to put a little aside when I get paid. I don't always save the same amount, but having the habit matters more to me than reaching a perfect figure every month.",
'generally 不等于 always，回答主动区分大件与小额消费。重要性题用 unexpected expenses 解释 quite important，再给储蓄习惯，不必编造收入或固定百分比。')
speak(36,'support-speaking-c21-t2-p2-false-information','不真实的信息：发现问题与核对',2,54,'Part 2',['Describe a time when you read or heard something that you thought was not true.','where you read/heard this','what you read/heard','why you thought it was not true','and explain how you felt about reading/hearing this thing that you thought was not true.'],
"I remember seeing a message in a group chat saying that our university library would close for an entire month. It appeared just before an important assignment was due, so several people were worried. The message looked like a screenshot of an announcement, but it didn't include a date or a link to the original notice.\n\nI doubted it because I had been in the library that morning and had seen nothing about a long closure. Rather than immediately telling everyone the message was wrong, I checked the library website. The actual notice said that one reading room would close for repairs while the rest of the building remained open.\n\nAt first I felt anxious, because I depended on the library for a quiet place to study. Once I had checked the notice, I felt relieved and a little frustrated that an incomplete message had caused so much confusion. I shared the link with the group and explained the difference. The experience reminded me to check the original context before passing on information that sounds urgent.",
'where=group chat；what=whole library closed one month；why=different recent observation + original notice核对；feelings=anxious→relieved/frustrated。题目是 thought not true，先怀疑再核对比把直觉当证据更清楚。本文事件是原创参考作答，不是新增真题文本。')
speak(37,'support-speaking-c21-t2-p1-cities','城市生活：吸引力与不便',2,54,'Part 1',['Do you think cities are exciting places to live?','Why do some people dislike living in a city?'],
"Yes, they can be. I enjoy having different places to eat and events to choose from, even if I don't go out every evening. Just knowing that I could try something new makes the city feel lively to me.\n\nI think the noise and crowds put some people off. A journey that looks short on a map can also take a long time during rush hour. If someone values peace and easy access to nature, those everyday frustrations may matter more than the entertainment a city offers.",
'两问视角不同：自己的兴奋感与 some people 的不喜欢。第二答不用 everyone hates，保留人群条件；rush hour 举出具体不便，最后说明不同价值取舍。')
speak(38,'support-speaking-c21-t3-p2-park','公园：从空间细节讲清兴趣',3,75,'Part 2',['Describe an interesting garden or park you have seen.','where this garden or park is','how big it is','what you saw in this garden/park','and explain why you think this garden/park is interesting.'],
"I'd like to talk about a park near the railway station in a city I visited last spring. It wasn't enormous; I could walk from one entrance to the other in about fifteen minutes. Even so, it contained several different areas, and that made it feel larger than it actually was.\n\nNear the entrance there was an open lawn where families were sitting. Further along, a narrow path led past flower beds to a small pond. I also noticed a section where local residents were growing vegetables. There were simple labels beside the plants, so visitors could see what was being grown.\n\nWhat interested me most was the contrast between the busy streets outside and the way people used the park. Some were exercising, while others were just talking or reading. The vegetable plots made it feel like a place that residents helped shape, rather than somewhere people only passed through. I spent longer there than I had planned because there was something different to notice around each corner.",
'题卡 how big 用 walk across in about fifteen minutes 给感知尺度，不虚报面积。what saw 是草坪／池塘／菜地；interesting 由居民参与与外部繁忙街道的对比解释。不要只罗列设施而漏掉为什么有趣。')
speak(39,'support-speaking-c21-t1-p3-attractions','景点：免费开放与失望原因',1,32,'Part 3',['Do you think tourist attractions such as museums should be free for local people to visit?','What can make a tourist attraction disappointing for visitors?'],
"Free admission can encourage local people to return regularly, especially families who would otherwise have to pay for several tickets. Museums may still need income for staff and maintenance, though, so one option is to offer free entry to the permanent collection and charge for some temporary exhibitions.\n\nVisitors can feel disappointed when the experience is very different from what was advertised. A famous view might be hidden by construction, or a small site might feel overcrowded after a long queue. Clear information beforehand can help, because people can decide whether the visit is still worth their time.",
'free for locals 需要兼顾进入机会和维持服务的费用；给出永久展／临展的具体方案，不断言所有博物馆预算相同。失望问题用预期与实际落差串起施工、拥挤两例。')
speak(40,'support-speaking-c21-t4-p3-sport','竞争与参与：比较体育观点',4,97,'Part 3',['How important is it to be very competitive at sport?','Why do some people think that taking part in sport is more important than winning?'],
"It depends on the purpose. For professional athletes, a strong desire to compete may help them keep training when progress is slow. In a casual game with friends, however, enjoying the activity and playing fairly may matter more than the result. Being competitive becomes a problem if it encourages someone to ignore rules or injuries.\n\nPeople who value participation often focus on the benefits that continue after a match ends, such as exercise, friendships and learning to work with others. Only one team can win, but both teams can gain those benefits. That is especially relevant when children are just starting a sport.",
'首问用 professional / casual 区分目的；第二问解释 taking part 的评价标准，不是说胜负永远无意义。Only one team can win 对比双方都能得到的长期收益，让观点可见。')

def save():
    OUT['coverage']={'replacementCount':len(OUT['replacements']),'supplementCount':len(OUT['supplements']),'realMaterialGroups':len(OUT['cases']),'note':'同页不同原问题组可以分别教学；复用case不计为新增独立原始材料。'}
    (ROOT/'support-remediations.json').write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding='utf8')

def pdftext(path,page):
    text=PdfReader(path).pages[page-1].extract_text() or ''
    text=text.replace('\u00ad','')
    lines=text.splitlines()
    if lines and re.search(r'(Reading|Listening|Speaking) sample task',lines[0],re.I):lines=lines[1:]
    cleaned=[]
    for chunk in re.split(r'\n\s*\n','\n'.join(lines)):
        joined=re.sub(r'\s+',' ',chunk).strip()
        if joined:cleaned.append(joined)
    return correct_transcription('\n\n'.join(cleaned))

def c21page(page):
    # The supplied PDF is rotated. Its line axis is text-matrix x; larger gaps
    # separate the real paragraphs, while the ordinary extractor loses them.
    chunks=[];last=[None];block=[]
    def flush():
        if block:chunks.append(re.sub(r'\s+',' ',' '.join(block)).strip());block.clear()
    def collect(t,cm,tm,font,size):
        if not t.strip():return
        s=t.strip()
        if s in ['Reading','READING'] or (s==str(page-1) and tm[4]>800) or re.fullmatch(r'Test \d+',s) or s.startswith('➔'):return
        axis=tm[4]
        if last[0] is not None and abs(axis-last[0])>20:flush()
        block.append(s);last[0]=axis
    R.pages[page-1].extract_text(visitor_text=collect)
    flush()
    text='\n\n'.join(chunks)
    if page==50:
        text=re.sub(r'A reliability.*?approval','A reliability\n\nB funding\n\nC skills\n\nD prejudices\n\nE computers\n\nF equality\n\nG framework\n\nH confidentiality\n\nI approval',text,flags=re.S)
    if page==29:
        text=re.sub(r'A national.*?and businesses','A national governments\n\nB agricultural developments\n\nC less wealthy nations\n\nD untrained workers\n\nE small-scale cultivation\n\nF outdated methods\n\nG financial controls\n\nH migrant workers\n\nI powerful individuals and businesses',text,flags=re.S)
    # Explicitly restore known OCR glyphs against the readable source pages.
    if page in [47,48,49,50,51]:text=re.sub(r'\bAl\b','AI',text)
    text=text.replace('politicians proclaim\n\nthe transformative','politicians proclaim the transformative')
    return correct_transcription(text)

def sample(stem):return next(D.glob('*'+stem+'*.pdf'))

def samplecase(cid,title,stem,textpages,qpages,apage,notes):
    path=sample(stem)
    body='<h4>'+esc(title)+'</h4><p>以下为正式样题原始材料。先按原题要求作答，再看原答案与对应解释；材料描述的是原文中的语境，不把历史数据当作当前事实。</p>'
    for p in textpages:body+='<h4>原材料 · 第'+str(p)+'页</h4><div class="authentic-source-text">'+para(pdftext(path,p))+'</div>'
    for p in qpages:
        if p not in textpages:body+='<h4>原题</h4>'+para(pdftext(path,p))
    if apage:body+='<h4>原答案</h4>'+para(pdftext(path,apage))
    body+='<h4>具体解释</h4>'+para(notes)
    refs=[ref(title+' · 完整题面、原材料与答案',path,1)]
    OUT['cases'].append({'id':cid,'title':title,'sourceRefs':refs,'teachingHtml':body,'answerPage':apage,'materialPages':textpages,'questionPages':qpages,'explanation':notes})
    return body,refs

LISTEN={}
LISTEN[21]=samplecase('support-listening-shipping','运输表单：姓名、地址、尺寸与总价','115005',[2,3],[1],4,
'Q1 Mkere 由逐字拼写 M-K-E-R-E 确认；Q2 Westall 也有拼写复核，不能用同一句中的 Road 替换学院名。Q3 BS8 9PU 是邮编。Q4 0.75m 是宽度、Q5 0.5m 是高度，1.5m 为题面已给长度。Q6–7 books / toys 顺序不限，clothes 已在表上。Q8 1700 是1500加200后的估价，不是听到的第一个数字。练习先合上原稿完成1–8，再逐句指出信息类型与更正／汇总处。')
LISTEN[22]=samplecase('support-listening-insurance','保险选择：解释、经历与最终决定','115008',[2],[1],3,
'Q9 C（Premium）：客户先说经济保险以前出过问题，再选 highest，回指最高档 Premium；不能因 economy 被重复就选它。Q10 A（port）：客户自己有交通工具，所以从港口取走；town/depot 是代理给出的其它选择。先圈出选项差异，再把 final decision 与此前解释分开。')
LISTEN[23]=samplecase('support-listening-social','海外生活讲座：两项困难与社区入口','115011',[2],[1],3,
'Q11–12 language / customs：not just … but … 将语言与习俗并列，不是用习俗否定语言。Q13–14 music / local history：theatre 是题面已有例子，不可重复填；set designers 属戏剧组内部角色。Q15–16 library / town hall 是获得信息的地点，不是活动种类。各对答案顺序不限，严格按三词和／或数字上限。')
LISTEN[24]=samplecase('support-listening-open-university','远程学习：动机、时间安排与模块','115010',[2],[1],3,
'Q27 motivation 对应 maintain a high level of motivation；Q28 time management 由同时全职工作和学习解释。Q29 modules 对应可以在模块之间休息，不能填 degree。Q30 summer schools 是认识同学的活动，home 是大多数学业进行的地点，不能误填。原题限制两词，time-management 连字符形式及 summer school(s) 的可接受形式见原答案。')
for aid,(body,refs) in LISTEN.items():
    add(aid,'supplements',OUT['cases'][-4+(aid-21)]['id'],OUT['cases'][-4+(aid-21)]['title'],body,refs,{'answerType':'正式样题原答案＋逐题原稿证据解释','sourceRead':'已读取完整题面、完整转写、答案PDF','audioNote':'本补充为可读原题及转写教学；已有音频入口保持，未伪造新录音'})

SAMPLE_SPEAK={}
for part,stem,promptstem,cid,title,explain in [
 (1,'115045','115041','support-speaking-official-p1','真实回答：家乡的四次问答','四问依次问类型、特色、工作、居住评价。原回答用距苏黎世20km、山上城堡、农民／银行职员／记者、安静但友善逐项回应。注意这是公开考生实录，含自我修正和语言瑕疵，并非无误范文：some medicines 应改为 some doctors 或其他人物职业；不要照背。练习：逐题用一个具体事实支持结论，再复述连接关系。'),
 (2,'115051','115047','support-speaking-official-p2','真实长答：钢琴为什么重要','原回答覆盖物品（piano）、来源（parents）、时间（12岁生日、约9年）、重要性（放松、暂时忘掉问题）；追问 replace 区分功能可替代与情感独特。原录音有错误：to my twelve birthday 可改为 for my twelfth birthday；I have it for about nine years 改为 I have had it for about nine years。改写是教学修正，不伪称原录音如此说。'),
 (3,'115057','115053','support-speaking-official-p3','真实讨论：地位象征与未来变化','第一组问答以汽车、服装说明地位象征；追问要求评价和未来判断。回答预测衣服仍重要，但汽车可能因环境问题改变；probably / not so sure 呈现不确定性。示范不是事实调查：应标为考生观点。原表达 first thing which comes in my mind 可改为 first thing that comes to mind；in the society 一般改为 in society。')]:
    transcript=sample(stem);prompt=sample(promptstem)
    body='<h4>'+title+'</h4><h4>完整正式题面</h4>'+para(pdftext(prompt,1))+'<h4>完整回答转写</h4>'+para(pdftext(transcript,1))+'<h4>回答与证据解释</h4>'+para(explain)
    refs=[ref('Speaking Part '+str(part)+' 正式题面',prompt,1),ref('Speaking Part '+str(part)+' 原录音转写',transcript,1)]
    SAMPLE_SPEAK[part]=(cid,title,body,refs)
    OUT['cases'].append({'id':cid,'title':title,'teachingHtml':body,'sourceRefs':refs,'answerType':'官方发布的考生实录；包含原有语言错误，另给具体修正'})
for aid,part in [(83,1),(84,3)]:
    cid,title,body,refs=SAMPLE_SPEAK[part]
    add(aid,'replacements',cid,title,body,refs,{'answerType':'公开真实考生回答＋对应分析，不冒充标准答案'})
cid,title,body,refs=SAMPLE_SPEAK[2]
add(113,'supplements',cid,title,body,refs,{'answerType':'公开真实考生回答＋逐点核对＋语言修正'})

# 个人主题沿用保存键，教学对象改为真实题卡；明确标记复用同一题，不冒充新增题。
for aid,sourceid,title,focus in [
 (53,37,'居住经验：城市的吸引力与取舍','把题目中的 some people 与自己的喜好分开。先说生活体验，再用交通或安静程度解释，不能把示范中的价值判断当作所有人的看法。'),
 (54,34,'认识的人：竞争心如何体现','用真实人物与可回忆事件替换大学朋友；分别核对认识方式、竞争领域、成功程度和你的解释。成功不必等于冠军，进入决赛同样可以描述。'),
 (55,28,'日常选择：付款与购买教训','保留usually与Have you ever的时态差异；把示例鞋子换成自己确实买过但用得少的东西，明确价格诱因与实际需求不同。'),
 (56,38,'兴趣与地方：观察公园细节','先按题卡地点、规模、所见、兴趣完成，再试用两句讲菜地为什么改变你对公园的印象。不要只列设施名字。'),
 (57,36,'经历与变化：核对一条信息','参考答题情节只是示例；若自己没有图书馆经历，应换真实的不实消息。要解释怀疑根据与核对方法，不需要编造戏剧性诈骗。'),
 (58,25,'旅行计划：信息怎样帮助行动','同一旅游信息原题在这里复习个人经历表达。核对来源、地点、内容、作用四点，说明一项具体信息怎样影响你的行动。')]:
    original=next(x for x in OUT['replacements'] if x['auditId']==f'audit-{sourceid:03d}')
    b='<h4>'+title+'</h4><p>本单元复用同一正式题卡，练习个人经历组织；不计作另一道新题。</p>'+para(focus)+original['teachingHtml'].split('<p>完整原件：')[0]
    add(aid,'replacements',original['caseIds'][0],title,b,original['sourceRefs'],{'reuseOfAuditId':original['auditId'],'answerType':'对真实题目的原创参考作答，复习角度不同但原题相同'})

def c21case(cid,title,test,pages,qpages,answerpage,notes):
    body='<h4>'+esc(title)+'</h4><p>先读这一组完整原文页，再完成对应原题。以下时代、数量与观点均按考试文章语境理解。</p>'
    for p in pages:body+='<h4>原文 · 印刷页'+str(p-1)+'</h4>'+para(c21page(p))
    for p in qpages:body+='<h4>原题 · 印刷页'+str(p-1)+'</h4>'+para(c21page(p))
    body+='<h4>答案与证据解释</h4>'+para(notes)
    refs=[c21ref(test,pages[0]),c21ref(test,qpages[0]),c21ref(test,answerpage)]
    OUT['cases'].append({'id':cid,'title':title,'sourceRefs':refs,'teachingHtml':body,'answerPage':answerpage,'materialPages':pages,'questionPages':qpages,'explanation':notes})
    return body,refs

BACK={}
BACK['davies']=c21case('support-reading-c21-davies','姐妹收藏家：教育、财富与公共文化',1,[17,18],[19,20],119,
'Q1–7：mining、education、notes、journals、Venice、canteen、friends。依次对应祖父行业、学校教育、画廊笔记、日记偏好、画面中的城市、战时工作地点、没有艺术家朋友。每空一词，transportation对应shipping，不能把已给意思重复填入。Q8 TRUE：宗教成长背景使她们把继承财产用于文化与慈善；Q9 NOT GIVEN：早期买Corot但没有购买画廊所在地；Q10 FALSE：Blaker支持当代法国艺术并参与转向；Q11 NOT GIVEN：英国首次公开展出不等于观众人数很多；Q12 TRUE：战后贫困改变Gwendoline的关注；Q13 TRUE：她们买印象派时个人与机构常忽视这种艺术。背景重点是教育、财力限制与个人偏好的共同作用，不能简化为富有就能买所有画作。')
BACK['sugar']=c21case('support-reading-c21-sugar','食糖的历史：贸易、劳动与健康',1,[26,27],[28,29],119,
'Q27 B：补贴与人为低价使beet sugar更具国际竞争力；Q28 A：英国进口来源按时间更换；Q29 C：Contrary to popular belief 后纠正甘蔗只来自富人种植园的误解；Q30 A：末段 could always have done without sugar 与 alternative sources of sweetness 支撑有害且非必需的评价。Q31–36 H/E/I/A/G/C，分别是移民劳工、小规模耕作、权势个人和公司、国家政府、金融控制、较贫穷国家。Q37 YES：农业技术带来大量供应；Q38 NOT GIVEN：文章说曾被视为奢侈品，却没说广告最初怎样宣传；Q39 NO：作者把高果糖玉米糖浆称为令人担忧的进展；Q40 YES：大量加工食品含它。这里是书评的作者判断，不把历史文章直接当当前营养建议。')
BACK['ai']=c21case('support-reading-c21-ai','人工智能：承诺、实施条件与制度风险',2,[47,48],[49,50,51],121,
'Q27–29 B/A/C：首段呈现公众由媒体获得的印象；第二段警告solutionism忽视安全并设不现实期待；第四段说政治人物没意识到部署复杂性。Q30–35 F/G/I/C/A/D：fair→equality，data infrastructure→framework，special permissions→approval，human talent→skills，难以信任→reliability，放大种族歧视→prejudices。Q36 NO：Russell主张现实日常应用；Q37 NOT GIVEN：没有Brooks遭不公平批评的信息；Q38 NO：security remains overlooked反驳always considered；Q39 YES：需讨论ethics和distrust；Q40 B：全文限制与实例支撑“AI未必是解决方案”。读出技术能力、制度条件与人的判断之间的区别。')
BACK['saiga']=c21case('support-reading-c21-saiga','赛加羚羊：适应、威胁与保护',3,[61,62],[63,64],123,
'Q1–7 dust/blood/coat/horns/habitat/routes/streams：鼻孔过滤尘土、冷却血液，冬毛适应温度；偷猎为角，农业和定居挤占栖息地、屏障挡迁徙路线，干旱使溪流消失。Q8 FALSE：90%以上在哈萨克斯坦，不是四国均匀；Q9 FALSE：20世纪多数时候数量恢复；Q10 TRUE：鼓励用赛加角代替犀牛角反而造成灾难；Q11 NOT GIVEN：没有跨地区严重程度比较；Q12 TRUE：项目保护生态系统及其中许多物种；Q13 NOT GIVEN：联合国认可不等于已说明新增资金。不要把考试文本的now数量移植成当前统计。')
BACK['dart']=c21case('support-reading-c21-dart','城市公交：可达性、排队与实施问题',3,[65,66],[67,68],123,
'Q14 NOT GIVEN：有多组增长预测，但没有实际比以前预测更快的比较；Q15 FALSE：single-storey与high-rise冲突；Q16 NOT GIVEN：没有铁路居民咨询；Q17 TRUE：without any agreed strategy说明无规划；Q18 FALSE：Unlike many cities说明并非照搬众多城市的地铁计划。Q19–26 lanes/boarding/wheelchairs/fuel/flood/smartcards/gates/queues。轮椅通达性来自step-free；停空调为了节油；洪水使车辆不足；读卡器与扫描器坏了导致人工检票和队列。好处与实施缺陷同时存在，不能只摘“公交更好”。')
BACK['foods']=samplecase('support-reading-product-return','食品召回：批次、金额与联系对象','115026',[1],[],2,
'Q4 pieces of metal：问题问污染物，不是产品名称。Q5 (on) the bottom：批号的位置不是商店。Q6 $5：opened jar对应5，未开封10；空罐不给钱。Q7 (the) Retailing Manager：吃过受影响食品联系此人；提供破坏者线索才联系Customer Relations Manager，两个角色不能交换。Q8 $50,000：问maximum，应取奖励区间上限。每答最多三词和／或数字。')
BACK['coal']=samplecase('support-reading-coal','能源与环境：产业陈述的范围','115024',[1,2],[3,4],5,
'Q1 D：首段把温室气体增长关联人口、生活水平与生活方式；Q2 B：coal总贡献18%，其中约一半来自发电，不能把18%再随意换成题中其它数。Q3 B：燃烧与气化技术对应提高效率；Q4 A：clean煤更洁净且更高效；Q5 D：含沉淀物的径流水经处理后抑尘；Q6 C：全文讨论煤产业与环境，A只涵盖控制污染一部分。语境是原正式样题中的产业论述及历史预测，并非今日排放数据核验。')
BACK['bees']=samplecase('support-reading-bees','蜜蜂实验：移动食物与解码方向','115025',[1],[2],3,
'Q38 feeding dish：科学家主动移动的是喂食盘，不能填bee或hive。Q39 food (source)：蜂箱外直线方向直接指向食物，不能把蜂箱内太阳参照规则套入。Q40 sun：蜂箱内以重力及垂直线代表太阳方向，偏离垂直线的角度对应食物相对太阳的角度。原题最多两词；实验中的距离、节拍数据按原文理解，不自行修成现实科普值。')
BACK['bike']=samplecase('support-reading-bike','集体骑行：时间安排、规则和援助','115020',[1,2],[3],4,
'Q1 TRUE：no earlier than30minutes与not more than half an hour同义。Q2 NOT GIVEN：文中说出示身份卡，但没说寄送时间。Q3 TRUE：many roads closed但not always说明有正常车流。Q4 FALSE：would like to see every cyclist wearing是倡议，不是compulsory。Q5 FALSE：prices表明收费。Q6 NOT GIVEN：停下休息的手势不是必须离开路面。Q7 FALSE：急救员只能给bin liners；Q8 TRUE：charged for all costs对应需付运回费用。')

for aid,key,title,focus in [
 (41,'ai','司法与技术：算法风险的真实阅读语境','重点看法律实例与Q35：算法放大既有偏见。题目要求从词表选D prejudices；不是根据“犯罪”主题自由发挥惩罚政策。'),
 (42,'dart','公共治理：公交方案怎样落地','重点比较Q18与Q19–26：选择较便宜可行公交和实际设备故障是不同层次。需要同时读实施效果与条件。'),
 (43,'davies','社会责任：财富如何用于公共文化','连接首段social responsibility与末段遗赠；Q8、Q12、Q13各有不同时间证据。'),
 (44,'bees','科学发现：从观察到验证','原太空自编背景改为有完整正式材料的动物行为实验。本资料库此轮未核验可替换的太空原题，不伪造同题材文本。'),
 (49,'saiga','环境保护：威胁之间的关系','把偷猎、栖地丧失、疾病、气候变化分开，Q4–7对应不同名词，不能用笼统environment代替全部。'),
 (50,'sugar','健康与消费：读出作者评价','重点Q37–40与最后两段：供应增长、宣传、健康危害、加工食品之间并非同一论断。'),
 (51,'davies','文化遗产：个人偏好与收藏选择','复用Davies完整真题，从教育与品味看收藏；不是另一篇独立材料。优先Q2–5及末段。'),
 (52,'foods','日常生活：读懂产品召回通知','重点理解batch number、opened/unopened、两个Manager。定位词必须结合产品条件。'),
 (59,'saiga','生命与照护：保护措施的意外后果','原家庭自编背景改为实证材料导读；聚焦Q10非预期后果与Q12多物种受益，不声称此文是家庭原题。'),
 (60,'sugar','食物与消费：来源、产业与后果','复用Sugar完整原题，从生产、贸易、消费三个层次组织理解；重点Q27–36。'),
 (61,'bike','旅行活动：一份骑行说明的完整语境','正式GT考试样题用于活动信息理解，不是分级读物；规则、收费、协助方式都在完整原文中。'),
 (62,'ai','媒体信息：新闻承诺与实际能力','聚焦Q27–29：媒体印象、solutionism风险、部署复杂性。避免把文章前段夸张承诺当作者赞同。')]:
    body,refs=BACK[key]
    case=next(x['id'] for x in OUT['cases'] if x.get('teachingHtml')==body)
    add(aid,'replacements',case,title,para(focus)+body,refs,{'answerType':'完整原题＋原答案核对＋逐题证据说明','sourceRead':'完整原文、题页与答案页已读取','reuseExplicit':key in ['davies','sugar','ai','saiga','dart']})

for aid,key,focus in [(45,'davies','教育背景通过文化学习和画廊记录塑造收藏兴趣，Q2 education与Q3 notes可直接验证。'),(46,'sugar','劳动语境重点Q31–32：移民工人与传统小规模生产并存，不把一种劳动组织泛化成全部。'),(47,'ai','科技语境重点Q30–35：公平、框架、审批、人才、可信度、偏见逐项对应。'),(48,'dart','城市语境重点Q14–18：增长、单层住房、规划与交通选择，不只有拥堵关键词。')]:
    b,refs=BACK[key];case=next(x['id'] for x in OUT['cases'] if x.get('teachingHtml')==b)
    add(aid,'supplements',case,'真实材料补充：'+BY[f'audit-{aid:03d}']['title'],para(focus)+b,refs,{'answerType':'原题标准答案与逐项证据；原概念文保留可疑标记'})

# 保持太空与家庭主题：采用全库中的行星生命探测正式任务和正式家庭写作题。
spacebase=LIB/'listening-audit-2026-09-14/batch-03'
spacepdf=spacebase/'transcripts/current-official-support-12.pdf'
spaceq=spacebase/'questions/part-3-AILI30064EVO_ib-2.txt'
spaceans=D/'current-official-support-11.pdf'
spacebody='<h4>太空与生命：样本怎样成为证据</h4><p>两位生物学生准备比较地球和其它行星上的生命证据。材料是正式听力流程图任务的完整转写；按“取样—检查化石—粉碎—加热—质谱分析—对照数据”理解步骤。不要把假设有生命写成已发现生命。</p><h4>原材料</h4>'+para('\n\n'.join(pdftext(spacepdf,p) for p in [1,2]))+'<h4>原题 Q26–30</h4>'+para(spaceq.read_text(encoding='utf8'))+'<h4>答案与证据</h4><p>26 F site；27 E radiation；28 C heat；29 G microbes；30 D results。26的定语has organic material修饰地点；27考更正：A问contamination，B明确No，实际原因是表面辐射可能杀死生命。28 exposure to heat对应subjected to；29 microbes比fossils小，是质谱寻找的潜在线索；30比较的是结果与地球数据，water只是地球取样环境，不是最终比较对象。官方独立样题答案号1–5对应本套演示题26–30，答案文字一致；字母按本题A–H选项映射。</p>'
spacerefs=[ref('官方演示题 Part3 · Q26–30 原题',spaceq,1),ref('行星生命探测完整原转写',spacepdf,1),ref('同任务独立样题答案1–5',spaceans,1)]
sp=next(x for x in OUT['replacements'] if x['auditId']=='audit-044')
sp.update(title='太空与生命：样本怎样成为证据',caseIds=['support-listening-planet-life'],teachingHtml=spacebody+'<p>完整原件：'+'；'.join(link(r) for r in spacerefs)+'</p>',sourceRefs=spacerefs)
sp['verification'].update(answerType='官方答案文字＋题号映射＋原稿逐项解释',sourceRead='已读完整QTI抽取原题、2页原转写及官方独立答案页')
OUT['cases'].append({'id':'support-listening-planet-life','title':sp['title'],'teachingHtml':spacebody,'sourceRefs':spacerefs,'answerMapping':{'26':'F site','27':'E radiation','28':'C heat','29':'G microbes','30':'D results'}})
wf=ROOT/'authentic-writing-cases.json'
if wf.exists():
    wc=next(c for c in json.loads(wf.read_text(encoding='utf8'))['cases'] if c['id']=='wc-official-wealth')
    wealthbody='<h4>家庭与儿童：财富是否决定成年应对能力</h4><h4>完整原题</h4>'+para(wc['prompt'])+para(wc['originalTaskInstruction'])+'<h4>导读</h4><p>题目比较两类家庭中的孩子应对成年问题的准备程度。贫穷与富裕是条件；独立性、预算取舍、指导和机会才是可解释的机制。下面是针对正式原题的两段主体参考，不是完整250词作文，也不是原题自带文章。</p><h4>参考主体段</h4>'+para('\n\n'.join(wc['modelAnswer']))+'<h4>逐段解释</h4>'+para('\n\n'.join(wc['explanation']))+'<p>练习：先找出第一段的条件词may、could，再找第二段的反例。参考答案：有限预算可能培养选择能力，但压力和机会不足会削弱准备；富裕家庭也能通过责任与家务培养判断。因此无法只凭收入推出更充分的准备。</p>'
    wref={'label':wc['source']['originalUnit'],'path':wc['source']['path'],'page':wc['source']['page'],'url':None}
    it=next(x for x in OUT['replacements'] if x['auditId']=='audit-059')
    it.update(title='家庭与儿童：财富是否决定成年应对能力',caseIds=['wc-official-wealth'],teachingHtml=wealthbody+'<p>完整原件：'+link(wref)+'</p>',sourceRefs=[wref])
    it['verification'].update(answerType='真实写作题＋原创主体段参考作答；181词主体段明确非完整作文',crossModule='authentic-writing-cases.json / wc-official-wealth')

def backsupp(aid,key,title,focus,model=None):
    b,refs=BACK[key]
    cid=next(x['id'] for x in OUT['cases'] if x.get('teachingHtml')==b)
    h='<h4>'+esc(title)+'</h4>'+para(focus)
    if model:h+='<h4>基于原题的参考改述</h4>'+para(model)+'<p>此句是对下方真题事实的原创改述，目标搭配不冒称原文用词。</p>'
    return add(aid,'supplements',cid,title,h+b,refs,{'answerType':'真实完整材料与原题答案；搭配改述明确为教学原创','reuseExplicit':True})
for aid,key,title,focus,model in [
 (63,'ai','take into account：安全是否被考虑','先做原题Q38。原题本身使用taken into account；原文security remains an often overlooked topic与always相矛盾，因此NO。把整个安全论证读完再学搭配，不能看到关键词就选YES。',None),
 (64,'dart','meet needs：具体说明谁的需要','原题Q21答案wheelchairs，证据step-free且entire route accessible。这一具体设计对应“需要”，不能泛称系统满足全部居民所有需求。','Step-free buses help meet the needs of passengers who use wheelchairs.'),
 (65,'saiga','raise awareness：从真实威胁组织内容','先完成Q4–7，分别说出角、栖地、路线、溪流对应的威胁。下方参考改述说明这篇文本的教学作用；不是断言保护机构确实举办了宣传活动。','This account can raise awareness of the different threats facing saiga, including poaching and the loss of migration routes.'),
 (66,'saiga','pose a threat：确定威胁对象与机制','原文Climate change poses a further threat紧接疾病段。Q7 streams与干旱导致小溪消失对应；温度异常可能触发疾病，但may不能改成确定因果。',None),
 (67,'coal','strike a balance：读懂需兼顾的三方','完整正式样题首段用attain a sustainable balance between population, economic growth and the environment。这里学习同义改述，不能改成任何一方完全不受限制；Q1 D定位人口生活方式驱动。','The passage presents a need to strike a balance between population growth, economic development and environmental protection.'),
 (68,'bike','take measures：行动要具体','先完成Q3–8：交通不全封闭、头盔是倡议、维修条件与坏天气用品分别有规则。下句把具体行动概括为measures，不能凭常识添加原文没有的强制规定。','The organisers take measures to support riders, including providing marshals and Mechanics Points, but riders still need to act safely.'),
 (70,'sugar','draw a distinction：区分不等于对立','Q27 B来自甜菜糖补贴与低价；开篇明确不仅写甘蔗糖也写甜菜糖。先读两者生产地点与交易关系，再概括区分。','The review draws a distinction between cane sugar and beet sugar before explaining how subsidies affected competition.'),
 (71,'bees','reach a conclusion：结论对应实验变化','Q38 feeding dish是实验改变，Q39–40区分箱外直接方向和箱内太阳参照。不要只看到结论而省掉比较条件。','Von Frisch reached a conclusion about the dances by changing the position of the feeding dish and observing the bees.'),
 (72,'dart','address a problem：方案与问题配对','Q19 lanes减少堵车，Q20 boarding前付票减停站，Q21wheelchairs说明通达；设备故障又造成Q26queues。address表示着手解决，不保证问题已消失。','Separate bus lanes address delays caused by other traffic, although the system still faces problems with vehicles and ticket equipment.'),
 (73,'coal','allocate resources to：资源投到哪里','原文完整句The worldwide coal industry allocates extensive resources to researching and developing new technologies and ways of capturing greenhouse gases。to后接researching/developing，不是to research。Q3 B具体指出气化技术。',None),
 (74,'davies','make a difference：用可核对结果解释影响','Q12说明战争改变收藏方向；末段说1951与1963向National Museum Wales捐赠。参考改述的cultural legacy有全文支持，不虚构参观人数或经济收入。','By donating their collections, the sisters made a lasting difference to the cultural resources available in Wales.')]:backsupp(aid,key,title,focus,model)
# make progress 使用真实Part2参考回答，明确不是原题提供的事件。
original=next(x for x in OUT['replacements'] if x['auditId']=='audit-034')
add(69,'supplements',original['caseIds'][0],'make progress：真实题卡中的成功程度','<p>真题明确要求how successful this person is。参考答题用逐渐赢得更多比赛、进入俱乐部决赛说明进步；可概括为He made steady progress through regular practice。人物事件与概括句是原创参考作答，不是声称考试题面给了这些事实。</p>'+original['teachingHtml'].split('<p>完整原件：')[0],original['sourceRefs'],{'answerType':'真实Part2题卡＋原创参考回答与搭配归纳','reuseExplicit':True})

backsupp(116,'saiga','according to：准确标明证据来源','末段according to an aerial survey earlier this year把人口估计归于航空调查。结合前面的不同年份、地区和数量阅读，不能把文章的earlier this year解读成现在的年份。Q8仍是FALSE，因为大部分在哈萨克斯坦。')
farmbody,farmrefs=samplecase('support-reading-farming','农业补贴：连锁后果与段落主旨','115016',[1,2,3],[],4,
'原题Q1–5分别为Section A/B/C/D/F，答案v/vii/ii/iv/i；Section E是题面示例vi。A概括政府如何影响环境；B说农业与粮食产量；C论现代农业的环境影响；D看富国政策；F看新国际贸易协定的可能影响。E段从发展中国家肥料补贴讲到过量使用、减少轮作／休耕、加重土壤侵蚀；That, in turn中的That回指前一环节，不是只表示随后某天。F段预测新国际贸易协定带来的生产转移及环境后果；New Zealand研究在D、IRRI研究在E，不能混作F段主旨。')
add(117,'supplements','support-reading-farming','in turn：完整因果链',farmbody,farmrefs,{'answerType':'正式标题匹配原题与答案；从E段逐环解析'})
backsupp(118,'dart','as a result：结果须回指完整原因','第二页坏读卡器→纸票→无扫描器→人工撕票→高峰队列。As a result, queues are considerable at peak times回指这些票务问题，Q26 queues。不能仅因flood也出现，就说这句只表示洪水直接导致排队。')
mapbody,maprefs=c21case('support-reading-c21-mapungubwe','考古发现：器物证据与推测边界',2,[43,44],[45,46],121,
'Q14–19 E/G/C/D/B/A；Q20–21 B与D（任意顺序）。Q22 prosperity、Q23 whistles、Q24 bodies、Q25 ancestors、Q26 jewellery/jewelry。E段大量陶器暗示专业制陶与繁荣；陶盘与口哨之外In addition继续列牛羊、人形；may have been used提示祭祀用途只是推测，不能写成确定用途。')
add(120,'supplements','support-reading-c21-mapungubwe','in addition：考古证据如何递进',mapbody,maprefs,{'answerType':'真题原文、完整原题和原答案解释'})
cid,title,b,refs=SAMPLE_SPEAK[1]
add(122,'supplements',cid,'as well as：原实录中并列两类职业','<p>原回答先提村中农民，再用as well as并列去苏黎世工作的银行职员／记者。不是说所有村民都在城市工作；后续teachers/doctors仍是其它职业。先读四次完整问答，再指出这一句回答的是哪一问：What kind of jobs…。</p>'+b,refs,{'answerType':'官方发布真实口语转写；原错误单独说明'})
backsupp(124,'davies','responsible for：责任归属如何被修正','第一原文页先说长期以为两位顾问largely responsible for收藏性质，随后指出姐妹角色更主动。不能把旧看法当作作者最终认同，也不能把responsible简单等同有罪。结合Q2–4看教育、记录、日记与选择。')
healthpath=D/'cambridge-classroom-reading-3.pdf'
healthbody='<h4>健康观念：身体、环境与相互作用</h4>'+para(pdftext(healthpath,4))+para(pdftext(healthpath,5))+'<h4>原任务与答案</h4>'+para(pdftext(healthpath,3))+'<p>原教师答案：Q1 1946（C）；Q2 social, economic, environmental（E）；Q3 1970s（D）。contribute to出现在E段，三种条件相互作用而非独立。问三大领域不是只答physical/mental/social：那是前面1946定义中的维度。这里沿用正式教学材料原问题与原教师答案，非新增考场题号。</p>'
healthrefs=[ref('Cambridge Academic Reading Short-answer Activity · 完整材料',healthpath,4),ref('原题与教师答案',healthpath,2)]
OUT['cases'].append({'id':'support-reading-health','title':'健康观念的变化','teachingHtml':healthbody,'sourceRefs':healthrefs})
add(125,'supplements','support-reading-health','contribute to：多个条件相互作用',healthbody,healthrefs,{'materialType':'Cambridge官方教辅原任务；非考场题号','answerType':'Cambridge正式题型教学原任务＋原教师答案，不冒称考场题号'})
backsupp(127,'coal','likely to：概率表述与尚在试验的技术','原文Efficiencies are likely to be improved dramatically，后接技术仍处pilot/demonstration阶段。Q3 B气化技术是研发方向，不应把likely改成has definitely；保留文中预测语气和历史语境。')

backsupp(134,'ai','跨话题词汇：在完整真题中追踪论证','本补充把24词索引接入一篇完整文章。练习先找benefits、capabilities、data、security、limitations在段落中的对象与论证作用，再做Q30–35。答案应落实为fair→equality、infrastructure→framework、permissions→approval、talent→skills、trust→reliability、discrimination→prejudices。只验证这篇语境覆盖，不把24条所有例句都改判为真题引文。')
backsupp(135,'sugar','话题词库：用完整真题连接生产与消费','从一篇完整文章建立production→labour→trade→consumption→harm关系，再做Q27–40。特别说明第31空migrant workers与第32空small-scale cultivation属于不同生产组织；第35空financial controls与第36空less wealthy nations是措施与受影响对象。本补充覆盖食物／工作／贸易／健康交叉语境，不等于其余1000词条都已有独立真实长语境；原词库整体仍保留可疑范围说明。')

for aid,name,pages,title,notes in [
 (143,'hwatai-cambridge6-sample.pdf',[9,10],'运动成绩：从科研到训练支持','导读问题（教师编写，非原考试题号）：AIS与ASC各怎样支持运动员？参考答案：AIS让年轻及职业运动员在教练监督下训练并使用科学与医疗人员；ASC为96项运动的项目提供资金。两者都提供密集训练、设施、营养建议。再问科学工作的目标是什么：B段最后的winning及教练改善运动表现。C段用极小的时间／距离改善累积成绩说明做法，不能简化成只靠运动员天赋。'),
 (144,'hwatai-cambridge8-sample.pdf',[9,10],'计时工具：自然周期与技术限制','导读问题（教师编写，非原考试题号）：三个自然周期分别是什么？参考答案：solar day对应地球自转，lunar month对应月相，solar year对应绕太阳公转产生季节。为什么不同纬度重视不同周期：赤道附近月相较季节更显眼，北方农业更依赖太阳年。读后续水钟与摆钟段，将器械工作条件与技术改进分开；不要把every calendar都说成同一种周期。')]:
    path=D/name
    b='<h4>'+title+'</h4><p>保留原摘读的待核标记；补充下面两页完整真题文章语境与具体导读答案。此公开样本的摘录没有提供这篇全部原题和答案，本补充作为背景阅读，教师问题明确另行标识。</p>'+''.join(para(pdftext(path,p)) for p in pages)+'<h4>导读与参考答案</h4>'+para(notes)
    refs=[ref('Cambridge公开真题样本 · 文章原页',path,pages[0])]
    cid='support-background-'+('sport' if aid==143 else 'timekeeping')
    add(aid,'supplements',cid,title,b,refs,{'answerType':'完整真实阅读材料＋教师导读问题与有据参考答案','scope':'背景阅读，不声称补全原考试题组','oldExcerptStillSuspicious':True})
    OUT['cases'].append({'id':cid,'title':title,'teachingHtml':b,'sourceRefs':refs})

filmtext="Though we might think of film as an essentially visual experience, we really cannot afford to underestimate the importance of film sound. A meaningful sound track is often as complicated as the image on the screen, and is ultimately just as much the responsibility of the director. The entire sound track consists of three essential ingredients: the human voice, sound effects and music. These three tracks must be mixed and balanced so as to produce the necessary emphases which in turn create desired effects. Topics which essentially refer to the three previously mentioned tracks are discussed below. They include dialogue, synchronous and asynchronous sound effects, and music."
filmbody='<h4>电影声音：三个组成部分怎样协同</h4>'+para(filmtext)+'<h4>原题</h4><p>Q14. In the first paragraph, the writer makes a point that</p><ol type="A"><li>the director should plan the sound track at an early stage in filming.</li><li>it would be wrong to overlook the contribution of sound to the artistry of films.</li><li>the music industry can have a beneficial influence on sound in film.</li><li>it is important for those working on the sound in a film to have sole responsibility for it.</li></ol><p>Q24. The audience’s response to different parts of a film can be controlled …</p><p>选项：A when the audience listens to the dialogue. B if the film reflects the audience’s own concerns. C if voice, sound and music are combined appropriately. D when the director is aware of how the audience will respond. E when the actor’s appearance, voice and moves are consistent with each other.</p><h4>参考答案与证据</h4><p>Q14 B：cannot afford to underestimate直接表明不能忽视声音的重要性；A的early stage未写，C把电影声音偷换成音乐产业，D的sole与导演同样有责任冲突。Q24 C：three tracks must be mixed and balanced→combined appropriately，necessary emphases/create desired effects→控制观众反应。原研究PDF未附这两题答案表，这里是依据可见原文逐句推导的参考答案；不冒称官方答案键。</p><p>进一步导读：human voice、sound effects、music不是同义词。in turn连接混合平衡、突出重点、产生效果三环；原页随后具体区分同步／异步音效以及配乐。打开同页继续读完整论证，再判断仅听对白为何不足。</p>'
filmrefs=[ref('Cambridge Research Notes68 · Appendix5原文',D/'cambridge-research-notes68.pdf',30),ref('Appendix5原题Q14–26',D/'cambridge-research-notes68.pdf',31)]
add(147,'supplements','support-reading-film','电影声音：完整原页与原题证据',filmbody,filmrefs,{'answerType':'真实原题；教师推导参考答案，原件不附答案键','verificationMethod':'已渲染并目检物理页30与31，逐项核对Q14与24及选项','oldExcerptStillSuspicious':True})
OUT['cases'].append({'id':'support-reading-film','title':'电影声音：声音组成与功能','teachingHtml':filmbody,'sourceRefs':filmrefs})

# 读写四个可疑由root按其独立case补充；本文件只给映射请求，不伪造已完成内容。
for aid,title,request in [(75,'Miles Davis原段落导读','以真实Miles文章相应段＋真实heading题答案替换自编导读'),(76,'Older workers原段落导读','以真实Older workers条件范围段＋对应单选原答案补充'),(101,'阅读迁移：另一篇完整真题','保留原迁移块，另附一组完整真实阅读case'),(104,'Task1迁移：另一道真实图题','保留原迁移块，另附独立真实Task1 case与足量参考作答')]:
    a=BY[f'audit-{aid:03d}']
    body=annotate_source_html(body)
    OUT['supplements'].append({'auditId':a['id'],'target_selector':a['target_selector'],'anchor':a['anchor'],'title':title,'caseIds':[],'teachingHtml':'','sourceRefs':[],'verification':{'status':'待root按读写case集成','crossModule':True,'reason':request}})

save()
