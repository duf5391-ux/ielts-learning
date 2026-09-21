from pathlib import Path
from bs4 import BeautifulSoup
import json, hashlib, re

root = Path(__file__).resolve().parent
snapshot = root.parent / 'architecture-audit-qa/current-book-snapshot.html'
raw = snapshot.read_text(encoding='utf-8')
soup = BeautifulSoup(raw, 'html.parser')
ignored = {k:len(soup.select(k)) for k in ['[data-learning-audit]','[data-content-audit]']}
for node in soup.select('[data-learning-audit],[data-content-audit]'):
    node.decompose()
report = json.loads((root/'local-learning-architecture.json').read_text(encoding='utf-8'))
items = {i['id']: i for i in report['items']}

def change(id, title, status, scope, locations, quotes, problem, impact, action, acceptance, priority='P1'):
    item=items[id]
    item['previous_review']={'status':item['status'],'title':item['title'],'source':'research/local-learning-architecture.json','superseded_reason':'当前固定快照相应正文已有改写或范围需收窄；旧证据不得套用当前版本。'}
    item.update(title=title,status=status,scope=scope,locations=locations,evidence_quotes=quotes,problem=problem,learning_impact=impact,improvement=action,action=action,acceptance=acceptance,priority=priority)
    item['evidence']=[{'quote':q,'selectors':locations,'note':'当前固定快照正文；已移除旧审核标签，不以材料身份判定教学质量。'} for q in quotes]

change('LA-07','既有核心复习仍区分熟题与迁移，但不覆盖新增case','合格',
 '原reading/writing1/listening/speaking复习主干；不把结论延伸到改写后的Task2复习或新增case集合',
 ['#reading-review','#writing1-review','#listening-review','#speaking-review'],
 ['熟题和新题分开记录，不把单题组结果换算 band。','这是从折线图到平面图的较远迁移，主要检查“选择并概括重要信息”，不测试 increase by/to 是否会用。','熟片正确不记作陌生材料提升。'],
 '旧主干的边界仍在。新增阅读复习说明先独立答，但正文又预告animals dream Q9、AI Q38等答案；不能据原四章合格概括全部新增材料均能作未见检查。',
 '保留原主干的证据价值，同时避免新增已讲题被计作陌生诊断。',
 '保留熟题/支持条件记录；新增case进入独立检查前，按题号排除已在技巧或复习导读公开答案的题。',
 '核心熟题与陌生结果分列；新增case的未见状态按题号和是否已看解释判断，不仅按是否提交过答案判断。','保留')

change('LA-09','背景阅读入口与应试写作任务边界混杂','不合格',
 '当前家庭与儿童背景样本及topic-use总说明；不是对所有新背景逐项判差',
 ['.enrichment-unit[data-enrichment="background_family_children"]','#topic-use'],
 ['家庭与儿童：财富是否决定成年应对能力','Write at least 250 words.','按上方真实题目留下自己的回答或录音简记；参考内容用于对照，不必复述示范中的经历。','理解题可默想，不要求提交。','熟悉的段落直接跳过；累时读懂一段即可。'],
 '原生活概念/四情境读本已改成Task2题干和两段主体示范；同一背景单元同时出现原题250词指令、留下自己的回答、理解题不提交，未明确区分仅阅读背景与选择写作练习。旧“背景内容和可选回顾充分”不再适用于该替换稿。',
 '以理解背景为目的进入者可能误以为必须写作文，也失去原先低负荷的生活概念入口。问题是用途与边界，不是用了官方题。',
 '在题干前明确“这里只作话题理解，250词为原考试指令，本次无需作文”；把个人写作按钮标为可选并跳专项；恢复可分段概念解释/理解入口，保留现有范段作可选示范。',
 '学习者能只理解一个概念或段落后离开，不被视为未完成写作；原题要求和本次活动要求并列说明，无矛盾。')

change('LA-12','改写技巧课具有证据对照讲解结构','合格',
 '当前定位、判断、标题三个技巧的示范讲解结构；不认证所有原题答案准确或独立练习完整',
 ['#reading-tech-locate','#reading-tech-judgement','#reading-tech-headings'],
 ['精读时记录“题干概括词→原文具体表现”，不要只抄共同词noise。','“公开展出/首次展出”都不等于受欢迎','干扰项v Childhood and family life 只覆盖开头背景，无法概括音色训练、与他人对比及终身延续。'],
 '旧图书馆/高楼短示范已被替换，不应再引用旧例句。当前仍有题干主张→文本证据→干扰项边界的解释，可承担示范。合格依据是讲解对应关系，不是原材料官方化；答案逐项校核由另项内容复核承担。',
 '能够示范定位和整段判断，但读完示范的对应题不再是未见题。',
 '保留证据解释；明确示范题号，另选未公开解释的题给独立应用。若原始难度过高，可用短支架解释，不必强迫先读完整难文。',
 '每个示范可指出题干中的哪项关系被哪句支持；示范题号与独立练习题号明确分开；来源身份不替代教学判据。','保留')

change('LA-15','跨核心课、技巧课与新增case仍缺清楚选路','不合格',
 '当前44项技巧/主题目录与新增case、核心五章的关联路径',
 ['#library','#reading','#writing1'],
 ['先按卡点选方法：定位慢、判断不清、标题难分、填空失分，或看图对不上原文。','继续做原题片段：','对应原题练习：'],
 '已新增具体case跳转，旧“同通勤图连续三课”不再成立。现在有更多可做任务，但主干、技巧和case依旧未告诉学习者该先做哪项、哪项已讲可跳、何时回原稿；同题可从多入口反复出现。',
 '资源更充足，但选择与重复练习的负担仍可能增加。',
 '每科给一条默认最短路径；链接旁写示范/练习/检查、对应题号与返回目标，不要求做完所有case。',
 '用户从一个实际错误进入一个必要微课，再回原稿或明确的新题；重复入口不计独立材料。')

change('LA-16','示范题与独立题身份仍未在入口充分分开','不合格',
 '当前判断/标题技巧到case的首次作答用途；不再断言没有新增材料',
 ['#reading-tech-judgement','#reading-tech-headings','#reading-case-rd-official-miles-1','#reading-case-rd-c21-dreams-2'],
 ['标准答案：Q14＝viii，Davis’ unique style of trumpet playing。','再核对Q15＝iii，An education in two parts。','14. Paragraph A','15. Paragraph B','16. Paragraph C','Do animals dream?｜章鱼行为与研究边界'],
 '判断已接入不同文章的8题，标题case也有未在技巧页讲解的Q16，旧“完全重复、没有新题”应撤回。但技巧先显示Miles Q14/15答案，随后case仍以未作答整组呈现Q14–16；判断也同时链接已解释的Davies/AI题。未作答不能表示未见，哪道可独立测没有标清。',
 '将已读答案的题和未见题混成同一首次表现，会高估独立应用；新增材料本身不能修复这种证据混用。',
 '把已示范题标为有输入支持/熟题；给可独立做的具体题号，或先从未讲case作答再读技巧；按题号记录条件。',
 '看过Q14/15示范后做case，Q14/15不能作为无提示初测；Q16及其他未讲题可单独留下首次证据。')

change('LA-17','技巧课已提供具体可做材料与核对入口','合格',
 '当前定位、判断、标题及读图技巧的材料落点可执行性；不包括材料陌生性与逐题准确性',
 ['#reading-tech-locate','#reading-tech-judgement','#reading-tech-headings','#writing1-tech-read-chart','#writing1-case-wc-official-bicycle'],
 ['练原题：Why we need silence｜漂浮舱的两项实验','练原题：Do animals dream?｜章鱼行为与研究边界','练原题：Miles Davis：独特音色、双重教育与音乐遗产','练原题：自行车使用率：年龄比较与百分点差'],
 '旧“下一篇/换柱图但未给材料”已被实际case和原件核对入口替代。用户可从本页到可作答题目，不再需要临时自找或编题。此处转合格只针对材料落地；独立性问题仍见LA-16。',
 '从方法进入实际任务的阻力降低。',
 '保留具体入口；进一步标默认练哪几题、看过后的替代项及返回目标，避免整组堆叠。',
 '从技巧页能找到具体题面、作答区域和答后核对；材料与题号可识别；已讲题按支持后练习记录。','保留')

change('LA-18','新增口语已有实际开口要求，声音反馈回路仍不足','不合格',
 '当前旅游信息Part2样本（原出行ID保留）；不推及全部16组',
 ['#speaking-new-sep26-journeys'],
 ['旅游信息：一次具体使用经历','练习：保留题目中的对象、时间和问法，换成自己的真实经历。先口头作答，再对照上面的具体内容逐项检查；不需要逐字背诵参考作答。','我的新表达／本次复习记录（可留空）'],
 '现已改真实旅游信息题并明确先口头作答，旧“只有继续说三部分题”过时。单元仍主要检查内容回应，未明确保留录音、回听时间点、修复一处再重答；范答先展示，也不能把随后作答记未见首答。',
 '学员确有开口任务，但难以比较实际声音和修复效果，可能只对照内容觉得已经会说。',
 '复用核心录音器或自用录音：保存首答→回听一处→内容/用词/声音中只修一项→重答；注明已看范例。',
 '至少留一条声音与一处时间点证据，以及修复后的实际重答；不要求内置自动评分，不以文字判断发音。')

change('LA-19','旅游写作case已形成可自查的局部段落练习','合格',
 '当前国际旅游权衡微课及对应case的两主体段教学；不认证完整作文、个性化评分或所有新增Task2',
 ['#writing2-new-new-writing2-environment-discussion','#writing2-case-wc-official-tourism'],
 ['写两个主体段，约180–220词；同时覆盖local inhabitants与environment。','保留作答，打开答案与精读','比较标准是影响是否可逆以及承载能力，而非无依据地宣布旅游总是坏。','我的修订／证据笔记'],
 '旧国际协调/本地执行课已换为旅游权衡。当前case有具体本人写作任务、参考段、收益归属/居民环境成本/可逆性标准、结构与句子解释、修订笔记；足够承担该窄范围指导练习，旧仅有全文范文和笼统自检的缺口已明显补齐。',
 '学员可用可逆性、受益受损对象核对自己的论证，而不只是模仿范文词句。',
 '保留现有case；明确微课已见参考后作答是支持下练习，修订至少指出一处原句关系；如要独立检查，另选未讲题。',
 '能在本人两段中标出收益归属、居民/环境成本和比较标准，并修一处；允许其他有理据立场；不依据范段估band。','保留')

change('LA-23','正文仍以来源牵连旧材料可疑，需与教学用途分开','不合格',
 '已剔除全部data-learning-audit/data-content-audit节点后，复习正文残留的质量表述；不重复评旧标签',
 ['#reading-review','#writing1-review'],
 ['本补充保留已有复习记录及原可疑示范，另外加入可查证的独立真题。','原复习内容保留为可疑材料；补充练习采用8道独立的真题或官方考试样题。'],
 '旧标签全部被本次复核忽略，但当前教学正文仍把已有示范/复习称为可疑，并以另加可查证真题作对照。没有说明旧内容到底错在哪里或只是非真题，依然容易把材料身份与教学质量混淆。根任务已做的历史标签区分不等于这些新插正文已清理。',
 '用户仍可能把合法受控练习视为教学差，或把新增真题当作完整教学质量保证。',
 '把这些正文改为中性用途说明：原项是自编控制练习、用于窄目标；新增项是原题应用。若确有教学错误，列具体错误与修正，不能只因自编称可疑。',
 '移除旧标签后正文也不以自编/官方自动推出质量结论；每个不合格都有当前具体教学问题；原材料身份单列。')

report['date']='2026-09-19'
report['reviewer']='learning_architecture_review/current-snapshot-recheck'
report['snapshot']={'path':str(snapshot),'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'ignored_audit_nodes':ignored,'note':'只评此固定快照，后续主册修改须另复核。'}
report['method']='基于旧24条快速复核固定快照；删除全部[data-learning-audit]、[data-content-audit]后读正文及关键case。核心未变条核对原证据仍在；重点更新LA07/09/12/15/16/17/18/19/23。教学原文逐字真实性、全部新增题答案及浏览器运行另由对应审查承担。'
report['verdict']='核心首答与证据反馈仍可保留；技巧课已接具体case，旅游写作局部练习已补齐。但示范题与独立题身份、部分口语声音反馈、背景用途边界及跨单元决策仍需改进。不能因大规模换成官方材料整体判合格。'
cache={}
def text_at(q):
    if q not in cache:
        e=soup.select_one(q)
        cache[q]=e.get_text(' ',strip=True) if e else ''
    return cache[q]
norm=lambda t:re.sub(r'\s+','',t)
for item in report['items']:
    quotes=item.get('evidence_quotes',[])
    for ev in item['evidence']:
        ev['matched_selectors']=[q for q in item['locations'] if norm(ev['quote']) in norm(text_at(q))]
    item['current_review']={'snapshot':'architecture-audit-qa/current-book-snapshot.html','updated': 'previous_review' in item,'all_current_quotes_found':all(ev['matched_selectors'] for ev in item['evidence']),'source_note':'当前正文核验；不是沿用审核徽章。'}
    assert item['current_review']['all_current_quotes_found'], item['id']
    item['confidence']='当前固定快照中指定用途的架构判断；不是全部题目准确率或学习成效认证。'
report['counts']={'qualified':sum(x['status']=='合格' for x in report['items']),'unqualified':sum(x['status']=='不合格' for x in report['items'])}
report['catalog_scope']='content_catalog保留原147项旧目录作ID对照，不是当前内容总数；多项同ID正文与标题已改，新增case未全部纳入。不可据147项声称当前内容已全覆盖。'
for c in report['content_catalog']:
    c['catalog_version']='旧147项目录，仅用于定位对照'
    c['current_content_reaudited']=False
for page in report['page_inventory']:
    page['inventory_version']='沿用旧12面板信息架构基线；当前面板ID仍在，子模块/标题/数量不代表新增后完整目录。'
    page['current_panel_exists']=bool(soup.select_one('#'+page['anchor']))
    if page['anchor'] in ['background','reading','writing1','writing2','speaking']:
        page['current_change_note']='本快照存在大量原题化改写或新增case；旧子模块名称/内容形态不能直接当当前完整盘点，见本轮逐项更新与其他内容复核。'
report['inventory_method']='保留旧12主面板及147内容目录作历史基线，本轮仅验证12面板仍在；新增case未完整编目。'
report['limitations']=['仅当前固定快照；主HTML后续变动不在本判定范围。','24条为学习架构评审点，不是当前所有教学内容数量或质量百分比。','新增case的全文来源、答案和语言准确性另由内容审查复核；未因官方材料身份直接判教学合格。','没有浏览器交互或存储回归；不把静态保留作答控件当保存可靠性证据。']
out=root/'current-learning-architecture.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(out),'items':len(report['items']),'counts':report['counts'],'updated':[x['id'] for x in report['items'] if x['current_review']['updated']],'quotes':'all matched current body'},ensure_ascii=False))
