"""Review current listening/speaking resource lessons, without changing the book."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re
ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
s=BeautifulSoup((BOOK/'开始学习.html').read_text(encoding='utf8'),'html.parser')
old=json.loads((ROOT/'audit-content-remediated-20260919.json').read_text(encoding='utf8'))
items=[]
observations={
25:'题卡来源、地点、信息内容及帮助程度均有对应；最后入场时间与临时公交变更使例子有实际因果和限制。',
26:'未来趋势用could/might限定，分别解释屏幕休息与线上建议，并用空间和照料要求收窄结论。',
27:'户外空间的便利由儿童活动、下班休息举例支撑；末句把维护负担说成benefit，表达逻辑不够精确，宜改成trade-off。',
28:'现金/刷卡习惯与曾买不需要商品分开作答；时态与usually/ever对应，例子能解释反思。',
29:'区分直接说话与诚实，不把儿童特征绝对化；trust由承认打破物品后可直接处理问题的因果支撑。',
30:'回应How could，给出容器与共享园地两级方法，并保留阳光、许可、分工条件。',
31:'区分夸大承诺与明显玩笑；第二问另解释品牌、设计、便利，未用广告有影响重复问题。',
32:'两题分别回应时间习惯与外国面包经历；口感对比具体，没有把个人经验包装成普遍事实。',
33:'地点与改变发型的经历分别对应Where与recently；正确说明get a haircut的服务语义。',
34:'人物、竞争事项、成绩及动机均覆盖；赛事亚军和练习行动支撑competitive，动机保留推测语气。',
35:'generally与例外相配，储蓄价值由应对意外开销解释；不强行编收入或比例。',
36:'消息来源、内容、怀疑原因与感受变化均覆盖；核对原通知后区分全馆与一间阅览室。',
37:'自己的城市体验与some people的不喜分开，拥挤与通勤有具体机制和条件。',
38:'位置、大小、所见及有趣之处均覆盖；用步行时长表达尺度，居民菜地解释兴趣。',
39:'免费开放讨论进入机会和运营成本，失望讨论预期落差；两问各自展开。',
40:'竞技与休闲分场景，长期运动收益解释重在参与；不把所有运动目标简化为输赢。'}
bench='https://ielts.org/organisations/ielts-for-organisations/understanding-ielts-scoring/resources-for-setting-your-ielts-scores'
for x in old['items']:
 n=int(x['id'].split('-')[-1]) if re.fullmatch(r'audit-\d+',x['id']) else 0
 if not 21<=n<=40:continue
 node=s.select_one(x['target_selector'])
 item={k:x[k] for k in ['id','target_selector','title','category','source_basis']}
 item['audit_round']='current'
 if n>=25:
  text=node.get_text(' ',strip=True)
  part=re.search(r'真实 (Part \d)',text).group(1)
  item.update(status='达标',scope=part+' 的真实题面、原创参考作答和内容展开教学；不认证口语总分、流利度或发音。',reason=observations[n],evidence=observations[n],fit_summary='题目对象、时间、问法与示范逐项对应；写成文章的参考稿不证明现场口语表现，且没有官方分数。',next_action='用官方录音与考官评语校准表达方式，再独立录音作答；不背诵示例经历。',benchmark_links=[{'title':'官方已评分口语：Hendrik 7 / Kopi 8 / Kenn 8.5 / Anuradha 9','url':bench,'note':'定位同名考生；适合比较Part 3组织与语言，不宣称与本题同题。'}])
  if part=='Part 3':
   item['found_status']='存疑'
   item['resolved_issue']='原统一练习要求“换成自己的真实经历”，与Part 3一般讨论不合；已改为一般判断、理由、例子和条件。'
  if n==27:
   item['found_status']='存疑';item['resolved_issue']=item.get('resolved_issue','')+' 已把维护称作trade-off，保留优点与代价的区别。'
  item['source_refs']=x.get('source_refs',[])
 else:
  topics={21:('arriving-late-class','课堂通知','四题答案约5分钟、下周二、34页、Search均与官方文字稿对应；hand them back的代词位置解释正确。'),22:('team-meeting-about-diversity','会议分工','顾虑属Brenda、培训师属Stefano、场地属Brenda、研究属Nina；先team-building后workshops，与最终分工和before that对应。'),23:('weather-forecast','天气播报','发现时把by Saturday afternoon误作精确下午到达；现已改成最迟周六下午，保留截止边界。其余地区、天气、温度答案与文字稿对应。'),24:('introduction-lecture','讲座结构','积极心理学、投入活动的flow、艺术家例子、生平→条件→活动的顺序及maybe的非保证语气与文字稿对应。')}
  slug,title,reason=topics[n];url='https://learnenglish.britishcouncil.org/free-resources/listening/b1/'+slug
  item.update(status='达标',scope='B1通用英语原音基础听力：信息定位、条件与结构；不是IELTS整套考试或官方原题评分。',reason=reason,evidence=reason,source_basis='British Council LearnEnglish官方课程文字稿、原音及worksheet；本轮核对文字稿答案，未逐秒重听。',fit_summary='可训练IELTS所需的局部技能；课程题型、可暂停和中文作答不能等同正式考试条件。',next_action='基础练习后转入学习册已有IELTS原题练习；开场短例按原创迁移示范使用。',benchmark_links=[{'title':'British Council · '+title+'原音与文字稿','url':url}])
  if n==23:item.update(found_status='不达标',resolved_issue='题干改问“最迟什么时候”，答案改为“最迟周六下午；无法确定恰好下午抵达”。')
 items.append(item)
data={'date':'2026-09-19','scope':'4个新增听力基础单元与16个口语真题参考作答单元。状态按修正后当前限定用途。','items':items,'limitations':['口语题面沿用当前本地C21原页与既有来源核对；本轮复核示范及练习，未给原创作答估分。','听力核对官方在线文字稿与问题解释，不声称逐秒试听。']}
(ROOT/'research'/'listening-speaking-fit-20260919.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(len(items))
