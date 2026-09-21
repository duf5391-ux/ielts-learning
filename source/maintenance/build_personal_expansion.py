from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
DATA = [
 dict(id='topic-personal-home_neighbourhood', outcomes=['用位置、用途和感受介绍家中一个地方。','比较两个住处时，说明一种便利与一种不便。'],
 title='再看一个例子：搬家后，生活有什么变化',
 english="Before moving, I rented a large room on the edge of town. It had plenty of storage space, but my daily commute took almost an hour. My new room is smaller and costs a little more. However, I can walk to work and come home for lunch. At first, I missed having a balcony. I have now put a few plants by the window, and I am getting used to the smaller space. The move has made my weekdays easier, although I have to think carefully about where to keep things.",
 explain='第一段介绍一个住处的特点；这一段比较搬家前后。同样的“小房间”，放到上班距离和日常生活里，评价就更具体。storage space 是放东西的空间，commute 指往返住处与工作地点的通勤。例子同时交代了得到的方便和仍存在的不便。',
 teaching='**I am getting used to the smaller space.** 表示正在逐渐适应。**get used to + 名词／-ing**，例如 I am getting used to sharing a kitchen.（我正在习惯共用厨房。）**I used to rent a large room.** 则表示过去曾经租一间大房间；两种结构不能互换。',
 check='比较 I used to live near work. 与 I am used to living near work.。哪句说过去的居住情况，哪句说已经习惯？',
 answer='第一句说过去住得近，现在通常暗示已有变化；第二句说已经习惯住得近。used to 后用 live，be used to 后用 living。',
 words=[('rent','租用；租金','v./n.','rent a room','I rent a room near the station.'),('commute','通勤；上下班的路程','n./v.','a daily commute','My daily commute takes twenty minutes.'),('storage space','储物空间','n. phrase','plenty of storage space','There is plenty of storage space under the bed.'),('privacy','隐私；不受打扰的空间','n.','have some privacy','A separate room gives me some privacy when I need to work.'),('get used to','逐渐习惯；适应','v. phrase','get used to a smaller space','I am getting used to sharing the kitchen.')]),
 dict(id='topic-personal-relationships', outcomes=['用一次具体互动说明对一个人的评价。','用建议、解释和回应描述一次意见不一致。'],
 title='再看一个例子：关系好，也会有不同意见',
 english="My friend and I planned a birthday meal for another classmate. She wanted to book a busy restaurant, while I thought our classmate would prefer somewhere quieter. Instead of rejecting her idea, I explained that he had mentioned finding loud places tiring. She suggested a small cafe she knew, and we checked its menu together. I offered to make the booking while she contacted the others. We reached an agreement without either of us making every decision. I appreciated how willing she was to listen, and she said my explanation had helped.",
 explain='原来的例子用“先听，再提建议”说明表姐的帮助。这里通过商量聚餐地点展示另一种互动：提出不同看法，给一个与朋友有关的理由，再共同确定安排。reliable（可靠）、patient（耐心）等评价，要能接上具体行动；本段最直接支持的是 willing to listen（愿意听别人的想法）。',
 teaching='**I offered to make the booking.**＝我主动提出由我来预订。**offer to do** 强调提出帮助；**suggest doing** 强调提出一个做法：She suggested trying a quieter cafe. 两句话可以同时出现，但所说的动作不同。',
 check='如果朋友说“我可以去订位”，用 offered to book 还是 suggested booking 更能明确谁准备行动？',
 answer='offered to book 明确朋友主动提出自己去订位。suggested booking 表示建议预订，单靠这几个词还不知道谁去订。',
 words=[('reliable','可靠的；能让人放心的','adj.','a reliable friend','She is reliable and always lets me know if she is running late.'),('disagree','意见不同；不同意','v.','disagree about a plan','We sometimes disagree about where to meet.'),('reach an agreement','达成一致','v. phrase','reach an agreement on a plan','We reached an agreement on a quieter place to eat.'),('offer to help','主动提出帮忙','v. phrase','offer to help someone','My friend offered to help me move the table.'),('appreciate','感激；欣赏','v.','appreciate someone’s help','I appreciate the time she spends listening to me.')]),
 dict(id='topic-personal-daily_choices', outcomes=['说明一种选择适合什么场合。','区分尺寸合适、外观适合与价格是否值得。'],
 title='再看一个例子：两件外套之间怎么选',
 english="I needed a jacket for cycling to work, so I tried on two in a local shop. The first was cheaper and looked smart, but the sleeves felt tight when I reached forward. The second had more room and a pocket large enough for my phone. I walked around the shop in it before deciding. Although it cost more, I expected to wear it most weekdays. I chose it because it suited the way I would actually use it. For a jacket I would wear only once, I might have made a different choice.",
 explain='前一个例子把工作日与周末分开，说明场合会影响偏好；这一段进一步交代选择过程。叙述者试着伸手、走动和放手机，是在检查衣服能否满足实际使用需要。expected to wear 并不是报告已经穿过很多次，而是在说购买时对未来使用的预计。',
 teaching='**fit / suit**：The jacket fits me. 通常说尺寸合适；The jacket suits me. 常说款式或颜色适合我。若说适合某种用途，可以用 **suit my needs**：It suits my needs because I can move comfortably in it. **try on** 后若接代词，要说 try it on。',
 check='“这件外套尺码合适，但颜色不适合我”怎样填空？The jacket ___ me, but the colour does not ___ me.',
 answer='fits；suit。第一空说尺寸，第二空说颜色与人的搭配。不要把 fit 和 suit 都只记成没有语境的“适合”。',
 words=[('try on','试穿','v. phrase','try a jacket on','I tried the jacket on before buying it.'),('fit','尺寸合适；容纳得下','v.','fit me well','These shoes fit me well, even with thick socks.'),('suit my needs','符合我的需要','v. phrase','choose something that suits my needs','This small bag suits my needs for a short walk.'),('durable','耐用的','adj.','a durable bag','I wanted a durable bag for carrying books every day.'),('make a decision','作决定','v. phrase','make a decision after comparing','I made a decision after comparing the two jackets.')]),
 dict(id='topic-personal-interests_skills', outcomes=['区分喜欢一项活动与能完成其中某个动作。','用起点、调整和可观察的变化说明进步。'],
 title='再看一个例子：怎样说清自己进步了',
 english="When I started learning the guitar, I wanted to play a complete song straight away. However, I kept stopping whenever I had to change chords. My teacher asked me to slow down and practise just two chords for a few minutes each day. I recorded a short attempt on my phone at the end of each week. After a month, I could hear fewer pauses, even though I was still playing slowly. I cannot play every song I like, but I can now finish one simple song without losing the rhythm.",
 explain='原来的速写例子从“什么都画”调整到“一次画一个物体”；吉他例子从整首歌退回到两组和弦。两者都有具体的练习对象和可观察的变化。这里的 fewer pauses 是停顿变少，without losing the rhythm 是能保持节奏；它们比只说 I improved a lot 更容易让人理解。',
 teaching='**I kept stopping whenever I had to change chords.** 这里 **keep doing** 表示动作反复发生，不一定是一直连续进行。**whenever** 表示每当。**I can now finish ...** 把变化落在现在能完成的动作上；可以与 **At first, I could only ...** 配对。',
 check='“我很擅长吉他”和“我现在能不停下来地弹完一首简单的歌”，哪句提供了可以观察的进步？再补一句起初的困难。',
 answer='第二句给出了具体表现。起初可以说：At first, I kept stopping when I changed chords.（起初每次换和弦，我都反复停下来。）前后讨论的是同一个动作，因此能看出变化。',
 words=[('beginner','初学者','n.','a complete beginner','The class is suitable for complete beginners.'),('make progress','取得进步','v. phrase','make progress with practice','I made progress after practising the same short section.'),('slow down','放慢','v. phrase','slow down when practising','I slowed down to play each note clearly.'),('concentrate on','把注意力集中在','v. phrase','concentrate on one part','I concentrated on changing between two chords.'),('keep doing','不断或反复做某事','v. pattern','keep making the same mistake','I kept missing one note until I practised it separately.')]),
 dict(id='topic-personal-experiences_changes', outcomes=['按原计划、变化、行动和结果讲清一件事。','区分当时的打算与后来实际发生的事。'],
 title='再看一个例子：把时间顺序讲清楚',
 english="I was going to help at a community book sale on Sunday morning. On Saturday evening, the organiser called to say that the boxes would arrive two hours later than expected. I had already arranged to meet a friend in the afternoon, so I could not simply stay longer. I offered to prepare the price labels at home and come in when the books arrived. Another volunteer agreed to cover the earlier tasks. In the end, I finished my part on time. The change was manageable because we discussed who could do each job.",
 explain='博物馆的例子是在到达以后才发现变化；这次提前收到了消息，可以和别人分工。**was going to** 交代当时的计划；**had already arranged** 说明下午的约定在接电话之前已经作好；**in the end** 再交代最后结果。读者因此知道事情不是同时发生的。',
 teaching='**two hours later than expected**＝比预期晚两小时。不要与 **two hours later** 混淆：后者通常是相对于叙述中前一个时间点的“两小时后”。**I was going to help ...** 只交代原本打算，后文才告诉我们计划怎样调整。',
 check='活动原定十点开始，实际十二点开始。可以说 two hours later than expected 吗？这句话是在比较什么？',
 answer='可以。它比较实际时间十二点与原来预期的十点。只说 two hours later 时，需要前文先给出一个时间点，读者才能知道从何时算起。',
 words=[('be going to','打算；计划做某事','v. pattern','was going to help','I was going to help at the sale on Sunday.'),('unexpected','没想到的；意外的','adj.','an unexpected change','An unexpected change meant we had to divide the work differently.'),('postpone','推迟到以后','v.','postpone a meeting','We postponed the meeting until Friday.'),('in the end','最后；经过过程后的结果','adverbial','in the end, we finished','In the end, we finished before lunch.'),('work out','进展或结果如何；另可指想出办法','v. phrase','work out well','The new arrangement worked out well for everyone.')]),
 dict(id='topic-personal-places_weather', outcomes=['用具体感官细节介绍一个地方。','把天气条件与活动安排联系起来，并区分原因结构。'],
 title='再看一个例子：同一个地方，不同的到访方式',
 english="There is a small square near the library where I sometimes meet a friend. In the morning, it is bright and busy with people buying breakfast. Later in the day, the buildings cast a shadow over the benches, which makes the square a pleasant place to sit. Last Sunday, a strong wind kept blowing our paper cups over. We moved to a sheltered corner beside the entrance instead of leaving immediately. I still enjoyed watching people pass by, but I realised that the best place to sit depended on the weather as well as the view.",
 explain='运河例子选了水面的光和交通噪声；广场例子补上时间带来的变化：早上明亮热闹，下午有建筑的阴影。最后的风并没有让两人完全取消活动，而是改变坐的位置。**sheltered** 在这个场景中指有遮挡、风吹不到那么多的地方；它与 quiet（安静）描述不同特点。',
 teaching='**because of + 名词／名词短语**：We moved because of the wind. **because + 句子**：We moved because the wind was blowing our cups over. 两句都说明原因，但后面的结构不同。**a place to sit** 是“可以坐的地方”，适合用于介绍公共空间。',
 check='改正 We went indoors because of it was raining.，用两种结构各说一次。',
 answer='We went indoors because it was raining. / We went indoors because of the rain. 第一句在 because 后接完整句子；第二句在 because of 后接名词短语。',
 words=[('breeze','微风','n.','a gentle breeze','A gentle breeze came through the open window.'),('sheltered','有遮挡的；能避风雨的','adj.','a sheltered corner','We found a sheltered corner beside the building.'),('shade','阴凉处；遮阴','n.','sit in the shade','We sat in the shade of a large tree.'),('crowded','拥挤的','adj.','a crowded square','The square was crowded when the market opened.'),('because of','因为；由于，后接名词等','preposition','because of the rain','We changed our meeting place because of the rain.')]),
]

out=[]
for d in DATA:
    rows='\n'.join(f'| **{t}** | {m} | {e} |' for t,m,p,c,e in d['words'])
    lesson=f"""### {d['title']}

{d['english']}

**读懂内容**：{d['explain']}

**句子与用法**：{d['teaching']}

### 再积累几组相关表达

| 词与搭配 | 中文理解 | 例句 |
|---|---|---|
{rows}

### 确认自己读懂了（可选）

{d['check']}

<details>
<summary>查看解释</summary>
<p>{d['answer']}</p>
</details>
"""
    out.append({'id':d['id'],'learning_outcomes':d['outcomes'],'lesson_md':lesson,'minutes':15,'glossary':[dict(term=t,meaning=m,pos=p,chunk=c,example=e) for t,m,p,c,e in d['words']]})
(HERE/'personal-background-expansion.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Wrote six personal reading extensions.')
