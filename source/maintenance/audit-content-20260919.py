"""Read-only content audit. Writes only this audit's JSON/Markdown reports."""
from pathlib import Path
from collections import Counter
from urllib.parse import unquote
import json,re,hashlib
from bs4 import BeautifulSoup
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN=BOOK/'开始学习.html'
raw=MAIN.read_bytes();soup=BeautifulSoup(raw.decode('utf8'),'html.parser')
# Ignore previously rendered audit UI in the read-only parse; never edit MAIN.
for marker in soup.select('[data-content-audit]'):
    marker.decompose()
for marked in soup.select('[data-audit-target]'):
    del marked['data-audit-target']
def read(name,book=False):return json.loads(((BOOK if book else HERE)/name).read_text(encoding='utf8'))
source_map=read('source-map.json',True)
skills={x['id']:x for x in read('skills-resources.json')['units']}
speaking={x['id']:x for x in read('current-speaking.json')['topics']}
techniques={x['id']:x for x in read('learning-techniques.json')['units']}
enrich={}
for file in ['enrichment-reading.json','enrichment-writing.json','enrichment-speaking.json','enrichment-listening.json','enrichment-topics.json','enrichment-vocabulary.json']:
    for x in read(file,True):enrich[x['id']]={**x,'audit_data_file':file}
items=[]

def refs(node):
    found=[];seen=set()
    for a in node.find_all('a',href=True):
        href=a['href']
        if not href or href.startswith(('#','data:','javascript:')) or href in seen:continue
        seen.add(href)
        row={'label':a.get_text(' ',strip=True),'href':href}
        if not href.startswith(('http:','https:','mailto:')):
            path=BOOK/unquote(href.split('#')[0].split('?')[0]);row.update(local_path=str(path),exists=path.exists())
        found.append(row)
    return found

def add(selector,title,status,basis,reason,action,category,anchor=None,source_kind='unresolved',context='已检查当前可见教学与其配套材料；不按统一最低词数判定。',answer='已检查有无可对应的参考与解释；并不提供学习者成绩评定。',composition='见依据及理由。',source_refs=None,scope_note=None,data_file=None):
    nodes=soup.select(selector);assert len(nodes)==1,(selector,len(nodes));n=nodes[0]
    if not anchor:
        p=n if n.get('id') else n.find_parent(id=True);anchor=p.get('id') if p else None
    item={'id':'audit-'+str(len(items)+1).zfill(3),'target_selector':selector,'anchor':anchor,'title':title,'status':status,'category':category,'source_kind':source_kind,'source_basis':basis,'reason':reason,'next_action':action,'checks':{'source_traceability':basis,'composition':composition,'context_sufficiency':context,'answer_evidence':answer},'source_refs':refs(n) if source_refs is None else source_refs,'scope_note':scope_note or '只评价本条指向的教学块，不将结论扩展至整个章节。','observed_text_chars':len(n.get_text(' ',strip=True))}
    if data_file:item['data_file']=data_file
    items.append(item)

# All 40 expandable resource lessons, including the newer 12 technique lessons.
for n in soup.select('.res-unit'):
    anchor=n['id']; title=n.find('summary').get_text(' ',strip=True)
    if n.get('data-technique'):
        uid=n['data-technique'];u=techniques[uid]
        extra='三个完整参考范文分别为169、167、170词，其余为明确的局部示范。' if u['section']=='writing1' else '阅读短例可以演示单一逻辑，但不能替代带上下文的原题教学。'
        add('#'+anchor,u['title'],'未达标','learning-techniques-sources.md明确说明题面、英文短文、图表数值与图形为本地教学设计；IELTS/BC/IDP/Cambridge只支持方法规则。','主体例子没有具体真题或官方样题锚点；补齐参考答案与证据后仍未解决题面自编问题。','保留可用方法，将主示范换成已存原题或可追溯官方样题；使用完整原件入口、必要上下文及逐题/逐数据解析。','技巧单元',source_kind='local_task_with_rule_sources',context=extra+'现有解释能对应自身题面；本项不因篇幅一律否定。',answer='已存在示范答案和原文/图示证据；检查对象是这些证据本身仍来自自编题面。',composition='原创题面＋原创参考作答，不是“对真实题面的原创参考作答”。',data_file='learning-techniques.json / writing-worked-answers.json / reading-worked-answers.json')
    elif anchor.startswith('speaking-new-'):
        u=speaking[anchor.removeprefix('speaking-new-')]
        wc=len(u['context_en'].split());mw=len(u['model']['answer_en'].split())
        add('#'+anchor,u['title'],'未达标','current-speaking.json整体说明：公开回忆仅提供主题；情境、题面、示范与练习为本地原创。两份汇编有相互引用关系。','主题回忆不能证明当前示范题是原题；本单元主体语境和练习问句已重写，缺少可核对的具体题卡或题号。','选定可追溯题卡或官方样题，以其真实问题与追问作主线；原创回答可保留但须逐项回应真实题面，补足需要的展开。','口语资源',source_kind='recall_theme_then_local_task',context=f'主语境{wc}词、model答句{mw}词；可作片段练习，尚不足以单独展示完整Part 2长回答过程。Part 1短答不强制加长。',answer='有讲解和练习参考，但只能验证本地情境内部对应，不能反推题干的真题身份。',composition='来源主题为非官方回忆；当前问句、故事与示范由本地编写。',data_file='current-speaking.json',source_refs=[{'source_id':x} for x in u.get('sourceIds',[])])
    else:
        uid=anchor.split('-new-',1)[1];u=skills[uid]
        if u['section']=='listening':
            add('#'+anchor,u['title'],'可疑',u['source_note'],'原课程音频/稿件有明确原始材料依据，但讲解前的微型示例另行自编，理解题也改编；尚未建立每题到原稿段落或音频位置的完整映射。','主示范改为同一课程原稿的一段完整互动并定位；保留原音和答案，明确这是真实通用英语课程而非IELTS真题。','听力资源',source_kind='official_general_english_mixed_examples',context='原音和课程PDF提供完整语境；独立自编示范通常只有一两句。课程本身非真题不等于质量差。',answer='现有解释列出具体答案与含义；本轮核看稿件可用性，未逐段重新试听全部音频。',composition='真实课程原音＋本地理解题与示例。',data_file='skills-resources.json')
        else:
            add('#'+anchor,u['title'],'未达标',u['source_note'],'当前主阅读短文、图表数据或写作题干明确为原创/改写；规则页或回忆主题没有提供与这些题面一致的原题依据。','用本地已存真题或具体官方样题替换主体题面，并迁移已有解题步骤；对真实写作题编写参考作答可继续使用。','阅读/写作资源',source_kind='local_task_with_rule_or_recall_sources',context='现有材料含连续短文或完整写作示范，问题主要是题面依据，不是所有内容都短。',answer='有参考答案与解析且大体对应自编题面；未逐条校验所有新写事实。',composition='确认原创题面，不只是原创答案。',data_file='skills-resources.json')

# Background material: the currently rendered version, not unused newer JSON drafts.
basebg={x['id']:x for name in ['background-topics-a.json','background-topics-b.json'] for x in read(name,True)}
addbg={x['id']:x for x in read('background-additions.json')['topics']}
for n in soup.select('.topic-reader'):
    aid=n['id'];uid=aid.removeprefix('topic-');title=n.find('h2').get_text(' ',strip=True)
    if uid in addbg:
        status='未达标';basis='background-additions.json声明四个独立背景的语境、示范与教学为原创，sources为空。';reason='主语境为虚构教学情境，未与具体真题文章/原题形成导读关系。';comp='数据源已确认本地原创。'
    elif basebg.get(uid,{}).get('material_type'):
        status='未达标';basis=basebg[uid]['material_type'];reason='主背景短文明确是自编材料，没有具体真题文本作为导读对象。';comp='数据源明确标为教学自编背景短文。'
    else:
        status='可疑';basis='background-topics-a.json保留背景短文与用法，但未提供具体source identity、册次/篇章或原件定位。';reason='当前展示的是概念性背景短文；未找到把这段文字对应到真实文章的证据，不应仅因主题相同视为真题导读。';comp='无法从当前数据证明主短文来自原始材料，不擅自认定为真题。'
    add('#'+aid,title,status,basis,reason,'选择相关真题/官方材料作为导读对象，给出标题、段落/页码和本地原件入口；可保留概念说明作辅助。','话题背景',source_kind='local_background' if status=='未达标' else 'background_without_source_mapping',composition=comp,context='正文有背景、英文语境和用法；并非空白或仅一句话，但缺少真实材料主线。',answer='背景导读不强制设置考题；现有可选练习解释只能验证本地情境。',data_file='background-additions.json' if uid in addbg else ('background-topics-a.json' if uid in ['education','work','technology','cities'] else 'background-topics-b.json'))
for n in soup.select('.personal-reader'):
    aid=n['id'];title=n.find('h2').get_text(' ',strip=True) if n.find('h2') else n.find('h3').get_text(' ',strip=True)
    u=next(x for x in read('background-personal.json',True) if aid=='topic-personal-'+x['id'])
    add('#'+aid,title,'未达标',u['material_type'],'本单元整段生活故事为自编微型语境，未建立与真实题卡、访谈或课程原文的对应。','优先从已有真实口语样本/课程对话选一段有前后关系的材料，附人物、问题和用法解析。','个人生活背景',source_kind='local_background',context=f"当前主输入约{len(u['input_en'].split())}词，能呈现一个生活片段；尚缺真实材料前后文。",answer='此类背景无唯一标准答案；需核对讲解与原材料的关系，而非强设客观题答案。',composition='明确教学自编故事。',data_file='background-personal.json')

# Enrichment lessons have stable data-enrichment identifiers.
for n in soup.select('.enrichment-unit'):
    uid=n['data-enrichment'];u=enrich[uid];sel=f'.enrichment-unit[data-enrichment="{uid}"]'
    if uid.startswith('background_'):
        status='未达标';reason='虽附课程/教案链接，当前多段家庭生活故事和示例是本地扩写，未逐段对应所引课程，不能把规则/主题参考当原文。';action='将核心导读改接到具体原文或真题，以原段落解释词义；保留原创迁移情境为辅助。';kind='local_background_with_theme_sources'
    elif uid.startswith('vocab-'):
        status='可疑';reason='词义和结构有具体词典条目依据，例句与练习为自编；作为用法微课可用，但没有真实语境的较长主例。不是因为每一句词义示例都必须出自真题。';action='低优先级补一处可追溯的真实上下文并解释用法；不必删除短句练习或把它误称真题。';kind='dictionary_based_micro_lesson'
    elif uid in ['reading-headings-miles','reading-choice-older-workers']:
        status='可疑';reason='主练习有完整原材料、题号与答案解释，但前置示范仍用自编图书馆/班车短段代替从同一真实文章抽取例子。主原题部分可学，导读示范仍待调整。';action='保留原题与现有逐题解析；用Miles Davis或Older workers的一段作为开场示范，定位具体原题并解释干扰项。';kind='official_sample_with_local_leadin'
    elif uid.startswith('writing'):
        status='达标';reason='明确对应2023官方写作样题及页码，现有示范直接回答该真实题面并核对数据/题意；原创参考作答不等于原创题面。';action='保留；未来扩写完整范文时仍依原图/题目，局部60–110词训练不要冒充整篇答卷。';kind='official_sample_original_response'
    elif uid=='listening-insurance-choice':
        status='达标';reason='115008/Recording 2的9–10题、原稿与答案齐全，已核对原稿中highest对应Premium、port为最终地点；短搭配例句只是辅助。';action='保留；可增加原稿段落或音频定位帮助重听。';kind='official_sample'
    elif uid=='listening-customer-request':
        status='达标';reason='明确对应同一BC B1课程的原题、原音、稿件和6题答案，解释付款期限、请求与最终同意；不是IELTS真题但是真实可追溯课程。';action='保留为通用听力补充，并与IELTS原题分清用途；可补逐题音频定位。';kind='official_general_english'
    else:
        status='未达标';reason='数据源明确说明当前口语问句、示范和练习为自编；官方格式教案及通用课程仅提供教学思路，未证明问句是原题。';action='以明确题卡/官方样题问句组织示范，允许原创回答，但需与实际问题和追问逐项对应。';kind='local_speaking_task'
    add(sel,u['title'],status,u.get('source_note','未提供source_note'),reason,action,'补充教学单元',source_kind=kind,composition='以数据源source_note区分原题、原课程和自编示范。',context='已检查正文、任务与反馈；片段长度按其明确的局部教学目的判断，不统一要求150/250词。',answer='有task_prompt和feedback_md；阅读/听力附具体答案，写作是可接受参考而非唯一标准答案。',data_file=u['audit_data_file'])

# The 14 text-question blocks are assessed as materials, with their surrounding feedback identified.
qt_basis={
'miles':('British Council Reading: Matching headings；原教案学生页7–10，题14–19；教师页4–6，答案在原第5页。','reading-headings-miles','official_teaching_sample'),
'older-workers':('IELTS Academic Reading Sample Tasks 2023，原第27–28页，单选1–4；原第29页答案。','reading-choice-older-workers','official_sample'),
'davies':('Cambridge IELTS 21 Academic（2026），Test 1 Reading Passage 1，The Davies Sisters，题1–13；原册与Test 1答案页在本地。','reading-feedback','published_exam_practice'),
'further-education':('IELTS Academic Writing Sample Tasks 2023，Task 1A，原第3页，英国继续教育柱状图。','writing1_compare_groups','official_sample'),
'bricks':('IELTS Academic Writing Sample Tasks 2023，Task 1C，原第5页，制砖流程。','writing1_process_branches','official_sample'),
'us-jobs':('Cambridge IELTS 21 Academic（2026），Test 1 Writing Task 1，原书第29页，美国1960–2020年四行业就业。','writing1-feedback','published_exam_practice'),
'family-wealth':('IELTS Academic Writing Sample Tasks 2023，Task 2A，原第6页，家庭财富与成年生活准备。','writing2_position_mechanism','official_sample'),
'tourism':('IELTS Academic Writing Sample Tasks 2023，Task 2B，原第7页，国际旅游利弊。','writing2_weigh_consequences','official_sample'),
'theatres':('Cambridge IELTS 21 Academic（2026），Test 2 Writing Task 2，原书第52页，数字时代剧院/影院。','writing2-feedback','published_exam_practice'),
'insurance':('Cambridge公开听力样题115008 / Recording 2，题9–10；题页、文字稿与答案均在原始参考目录。','listening-insurance-choice','official_sample'),
'customer-call':('British Council LearnEnglish B1，A phone call from a customer；课程PDF题面、p3文字稿、p4答案配套。','listening-customer-request','official_general_english'),
'shipping':('Cambridge公开听力样题115005 / Recording 1，题1–8，货运报价单；原稿与答案在本地。','listening-feedback','official_sample'),
'open-university':('Cambridge公开听力样题115010 / Recording 4，题27–30，Open University；原稿与答案在本地。','listening-review','official_sample'),
'important-object':('Cambridge公开Speaking Part 2样题：重要物品题卡；考生录音115049、文字稿115051及同题追问。','speaking-feedback','official_sample')}
for u in read('text-questions.json')['units']:
    uid=u['id'];anchor=u['chapter']+'-text-'+uid;basis,peer,kind=qt_basis[uid]
    peer_node=soup.select_one(f'.enrichment-unit[data-enrichment="{peer}"]') or soup.find(id=peer)
    add('#'+anchor,u['title'],'达标',basis,'可追溯原题/原材料已文字化，保留原图；答案或参考解释在对应教学块。材料本身与其导读分别评判，不把此结论扩展至上级单元的自编开场。','保留文字题及原图；后续逐字校订仍以原页为准，必要时在题面旁连到已有解析。','文字化原题/原材料',source_kind=kind,context='整组题面保留所需文本/图形；听力须同时使用配套原音。正式节选材料不因不是全文而判差。',answer='配套解释位置：'+peer+'。写作/口语参考有多种合法表达，不称唯一标准答案。',composition='本地转写原题；未因转写或原创参考作答判为自编题面。',source_refs=refs(peer_node) if peer_node else [],scope_note='仅评价文字题材料及可访问的配套入口，不代表导读和所有迁移例子均达标。',data_file='text-questions.json / source-map.json')

# Core teaching and feedback get separate markers so a whole panel is never blanket-approved.
core_basis={'reading':qt_basis['davies'][0],'writing1':qt_basis['us-jobs'][0],'writing2':qt_basis['theatres'][0],'listening':qt_basis['shipping'][0],'speaking':qt_basis['important-object'][0]}
names={'reading':'阅读','writing1':'Task 1','writing2':'Task 2','listening':'听力','speaking':'口语'}
for section in core_basis:
    for part in ['learn','feedback','review']:
        aid=section+'-'+part
        if part!='review':
            status='达标';basis=core_basis[section];reason='导读/反馈围绕明确原题展开，指向原文证据、图中关系或录音内容；原创解释和局部参考作答具有真实题面锚点。';action='保留原题主线；增加示范长度时优先扩展同一材料，不用新编题面替换。';kind='authentic_task_guided_teaching'
            if section=='speaking':reason='重要物品真实样题、考生钢琴回答的录音/稿件可用；反馈具体讲时间表达和个人意义，未把范文当唯一答案。'
        else:
            if section=='writing2':status='未达标';basis='writing2-review明确称在家工作/办公室协作为工作区新情境，非真题。';reason='主迁移题和段落都是本地编写，没有具体真实题目锚点。';action='换用已有明确出处的讨论双方真题，保留60–90词局部论证训练和核对步骤。';kind='local_transfer_task'
            elif section=='listening':status='达标';basis=qt_basis['open-university'][0];reason='主新任务使用真实115010原题及独立录音4，有答案变体和原稿入口；周五取椅子短换句仅是辅助，不替代原题。';action='保留；继续区分熟片重听与真实新题表现。';kind='authentic_transfer_with_auxiliary_example'
            else:
                status='可疑';kind='mixed_authentic_and_local_transfer'
                basis={'reading':'原题后附自编Mira图书馆三题；另有官方大字版Rags to Riches第1–6题原件。','writing1':'自编800→1100万与汽车销量换句；另有C21 Test 2 Task 1咖啡馆图及考官样本。','speaking':'真实题卡追问Would it be easy to replace?；另有本地新增change one thing追问及活动迁移。'}[section]
                reason='同一区域混合真实后续题与自编迁移。真实部分有依据，但主开场/新增追问没有逐题原始材料映射。';action='保留明确真实题；把主迁移演示优先接回可追溯题目，自编单句只作辅助并分开用途。'
        add('#'+aid,names[section]+'｜'+{'learn':'核心导读与学习','feedback':'核心参考与证据','review':'后续迁移与复习'}[part],status,basis,reason,action,'核心教学/反馈/复习',source_kind=kind,context='检查该块及其明确链接的原题、原稿或反馈；局部示范不冒充完整范文。',answer='客观题提供答案与证据；写作/口语给事实核对或多种可接受表达。复习块混合性质在理由中单列。',composition='按真实题面的原创教学解释，与无原题的原创任务分别处理。',source_refs=refs(soup.find(id=section+'-feedback'))+refs(soup.find(id=aid)),scope_note='只限#'+aid+'，不包含本页顶部资源/技巧单元。')

# Trace all 20 source-quotation cards to the packaged PDF when available.
pdfcache={}
def norm(t):return re.sub(r'[^a-z0-9]','',t.lower())
for u in read('background-vocabulary.json',True):
    aid=u['id'];name=u['source_file'].replace('\\','/').split('/')[-1]
    hit=next((x for x in source_map if x['source'].replace('\\','/').split('/')[-1]==name),None)
    path=BOOK/hit['packaged'] if hit else None;match=False;machine_note=''
    if path and path.exists() and path.suffix.lower()=='.pdf':
        if str(path) not in pdfcache:pdfcache[str(path)]=[p.extract_text() or '' for p in PdfReader(path).pages]
        text=' '.join(pdfcache[str(path)][i-1] for i in u['pdf_pages'] if 0<i<=len(pdfcache[str(path)]))
        match=bool(u['original_quote']) and norm(u['original_quote']) in norm(text)
        machine_note='所列PDF页可归一化匹配原句。' if match else '所列PDF页未能通过机器文本匹配；未据此认定引文虚假，需核看扫描/排版原页。'
    else:machine_note='当前source-map未找到对应本地原文文件映射，或未提供可展示原句。'
    if match:
        status='达标';reason='有可定位原文片段、语义/指代解释和完整原件入口；短句服务特定用法，附带自编迁移不取代主原句。';action='保留；需要更长语境时从同一原文相邻句与原件入口补充，避免无必要整篇转载。'
    else:
        status='可疑';reason='数据声称有原文或保留材料依据，但当前本地映射/逐页匹配尚不能充分验证。'+machine_note;action='补齐可访问原件及正确页码，人工核看原页；若材料需保留未见，另选已学真实原文作主例，不必泄露保留试卷。'
    add('#'+aid,u['label']+'｜原文用法卡',status,('原文：'+u.get('source_title','未展示')+'；数据文件：'+u.get('source_file','无')+'；PDF页：'+str(u.get('pdf_pages',[]))+'。'+machine_note),reason,action,'原文用法卡',source_kind='source_quote_verified_locally' if match else 'source_quote_pending_verification',context='原句'+str(len(u.get('original_quote','').split()))+'词；另有中文语境、结构与对比说明。短不自动判差，取决于能否解释该用法。',answer='词义卡无客观题答案要求；本轮核原句与教学义项/语境关系。',composition='原句与日常自编迁移句分开展示；两者身份不混同。',data_file='background-vocabulary.json',source_refs=([{'local_path':str(path),'exists':path.exists(),'pages':u['pdf_pages']}] if path else []))

# Inspect vocabulary as vocabulary, not as a reading passage: no per-word failure rule.
add('#core-words','24个跨话题常见词｜语境与例句抽查','可疑','background-core-words.json：词形覆盖统计来自27篇训练快照；当前教学例句明确为自编，未逐词给真实原句。','词义、搭配与短句可作为词汇索引；但统计词形出现不等于当前例句来自真实材料，较长真实语境仍待补。','保留便查功能，优先给学习者常用/难懂词补具体原文上下文；不要求所有释义短句均出自真题。','词汇索引汇总',source_kind='corpus_selected_words_local_examples',context='24词逐条结构扫描，每条有释义、搭配、单句、误区；未逐条重新做词典语义鉴定。',answer='无客观题，不按缺少答案判差。',composition='真实语料选词统计＋本地解释/例句。',scope_note='汇总评价紧随#core-words的24张.word-card；不是给每条词下错误判定。',data_file='background-core-words.json')
add('#topical-vocabulary','30话题／1000词条｜词库语境覆盖','可疑','topic-vocabulary-*.json主要引Oxford主题页/词典与Cambridge B1词表；词头核对不证明本地搭配取自真题。','词库提供词、释义和短搭配，适合检索；绝大多数条目尚未连到完整真实语境，不能把1000词条等同1000个真实材料教学例。','保留词库索引；按学习用途分批连接具体原文段落或真实课程，不机械给所有词扩成整篇。','词汇索引汇总',source_kind='dictionary_and_wordlist_index',context='已扫描1000张.tv-card的结构及30话题元数据，未逐条人工复核1000词义；短搭配符合索引用途，不因短而判未达标。',answer='词库不是试卷，无标准答案要求。',composition='词表/词典支持词头，中文释义和搭配为本地整理。',scope_note='仅标注词库整体语境覆盖；不将汇总结论伪装为1000项逐条准确性审核。',data_file='topic-vocabulary-*.json')

# These 12 real-material excerpts have no IDs; audit their actual blockquotes and
# the exact physical PDF page linked in the rendered HTML, not metadata alone.
authentic_rows=read('background-authentic-excerpts.json',True)
authentic_nodes=soup.select('#background > .authentic-background > details.authentic-excerpt')
assert len(authentic_nodes)==len(authentic_rows)==12
for i,(n,u) in enumerate(zip(authentic_nodes,authentic_rows),1):
    sel=f'#background > .authentic-background > details.authentic-excerpt:nth-of-type({i})'
    quote=n.find('blockquote').get_text(' ',strip=True)
    a=n.select_one('a[href*="#page="]');assert a,'Missing source-page link'
    relative,physical_page=unquote(a['href']).split('#page=');path=BOOK/relative;pg=int(physical_page)
    if str(path) not in pdfcache:pdfcache[str(path)]=[p.extract_text() or '' for p in PdfReader(path).pages]
    extracted=pdfcache[str(path)][pg-1]
    quote_match=norm(quote) in norm(extracted)
    metadata_match=norm(quote)==norm(u['excerpt_en'])
    assert metadata_match,(u['id'],'DOM quote differs from metadata')
    words=len(quote.split())
    pnodes=n.select('.authentic-body > p')
    lead=' '.join(p.get_text(' ',strip=True) for p in pnodes)
    if not lead:
        lead=' '.join(p.get_text(' ',strip=True) for p in n.find_all('p') if not p.find_parent('blockquote'))
    status='达标' if quote_match else '可疑'
    basis=u['source_title']+f'；页面链接为本地原件物理PDF第{pg}页；原件存在。'
    if quote_match:
        reason=f'当前实际显示的{words}词连续引文与所链接PDF页文字归一化匹配；另有中文导读、3条词汇注释及完整原件入口，足以承担该局部主题导读，不因未转载全文判差。'
        action='保留这一真实材料主线；扩写时从同一篇章补必要上下文、原题或证据解释，避免用新编故事替换。'
    else:
        gap='该页抽取文本只有202字符，主要原文为嵌入扫描图。' if i==12 else '该页可抽取正文，但整段未归一化匹配，可能涉及分栏、字形或转写差异。'
        reason=f'实际显示{words}词并提供中文导读、注释及原页链接；来源身份明确，但本轮未完成整段逐字原页核对。'+gap+'不据机器匹配失败认定引文虚假。'
        action='先人工逐句核看所链接原页图，定位分栏/字形/转写差异，确认后再升级达标；保留原件与现有语境。'
    add(sel,u['title'],status,basis,reason,action,'真实材料摘读',anchor='background',source_kind='authentic_excerpt_page_verified' if quote_match else 'authentic_excerpt_visual_check_pending',context=f'实际引文{words}词；有可辨识完整段落或连续段落片段，当前中文说明补充指代/主题边界，词汇注释3项。'+u.get('coverage_note',''),answer='这是主题导读而非答题单元，不要求凭空加标准答案；已核看导读主题与引文内容相符。当前未逐条重新做词典核验。',composition='真实文章引文＋中文导读/词义教学，不是原创题面；metadata与当前DOM引文归一化一致。',source_refs=[{'local_path':str(path),'exists':path.exists(),'physical_pdf_page':pg,'quote_words':words,'normalized_page_text_match':quote_match,'page_extracted_chars':len(extracted),'href':a['href']}],scope_note='仅评价这条真实摘读及配套导读；不扩展至同主题自编背景、整章或尚未展示的原题。',data_file='background-authentic-excerpts.json')

counts=Counter(x['status'] for x in items);cats=Counter(x['category'] for x in items)
report={'date':'2026-09-19','scope':{'main_file':str(MAIN),'source_html_sha256':hashlib.sha256(raw).hexdigest(),'unit_level_items':len(items),'categories':dict(cats),'dom_counts':{k:len(soup.select(k)) for k in ['.res-unit','.topic-reader','.personal-reader','.enrichment-unit','.qt-unit','.authentic-excerpt','.usage-card','.word-card','.tv-card']},'method':'以当前HTML实际存在内容为准，在只读解析中排除旧审核标记；读取关联JSON及本地原件，检查资料身份、主体是否自编、语境与答案依据。12条真实摘读另核实际blockquote及其链接的物理PDF页。未修改正文。','not_fully_reviewed':['1000词条仅结构/来源类型汇总，非逐条词义与搭配准确性人工认证。','未重新逐秒试听全部录音；核查原音/稿件入口与已有答案说明。','图片式图表未在本轮逐个重新量取读数；现有原图保留，不把机器抽取失败当图中无证据。','资源目录链接的整本PDF、独立扩展资料网页及浏览器用户自添内容未逐篇审查。','12条真实摘读已全部纳入；其中体育、计时、电影声音三条待视觉逐字核看，另9条已与链接物理页归一化匹配。']},'criteria':{'达标':'具体真实题面/原始课程或原文可追溯，配套上下文及局部教学目的充分，答案/解释与证据对应。原创参考作答可达标，不要求复制官方范文。','可疑':'来源映射、原件匹配、示例和主材料关系或语境充分性仍需核实；或者真实主任务与自编开场混合，需局部调整。','未达标':'主体题面/导读情境确认自编且没有真实材料锚点，或缺少足以服务其声称任务的完整语境/答案证据。不是判定语言一定错误。','application':'以真题为主是主体教学选择准则；词义短句、辅助迁移、对真题的原创参考答案不一刀切。版权限制不作为质量缺陷；合法本地原件＋足够导读定位可达标。官方规则来源≠例子来自真题。','hierarchy':'每条只评价target_selector和scope_note指定内容；题面达标不自动使其所在整章达标。'},'summary':{'total':len(items),'by_status':dict(counts),'by_category':dict(cats),'primary_findings':['12技巧虽有规则来源和答案解释，主体题面仍为自编。','16口语资源仅主题来自未独立验证的回忆汇编，当前主情境/问句为原创。','12条真实摘读均已纳入，实际引文73–107词；9条原页匹配且局部导读充分，3条需视觉逐字核验。初版称其无节点有误，已纠正。','原有官方样题与Cambridge21核心教学有可追溯材料，应保留并作为替换入口。','14文字题逐项作为材料检查；上级导读是否使用自编示范另列。','词库与用法卡按用途审查，未把所有短词义例句直接判为未达标。']},'items':items}
(HERE/'audit-content-20260919.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
md=['# 学习册内容审查与先行标记','',f"审查日期：{report['date']}。共 {len(items)} 条教学块/汇总项："+'；'.join(k+str(v)+'项' for k,v in counts.items())+'。','',f'当前学习册：`{MAIN}`。本报告只做审查与标记，不替换教学正文。','', '## 判定口径','']
for k,v in report['criteria'].items():md.append('- **'+k+'**：'+v)
md+=['','## 覆盖与限制','', '覆盖：'+'；'.join(k+str(v)+'项' for k,v in cats.items())+'。','']
for x in report['scope']['not_fully_reviewed']:md.append('- '+x)
md+=['','## 优先处理','']+[str(i+1)+'. '+x for i,x in enumerate(report['summary']['primary_findings'])]
md+=['','## 逐项结果','', '| 标记 | 内容 | 定位 | 依据与问题 | 下一步 |','|---|---|---|---|---|']
for x in items:
    vals=[x['status'],x['title'],'`'+x['target_selector']+'`',x['source_basis']+' '+x['reason'],x['next_action']]
    md.append('| '+' | '.join(v.replace('|','／').replace('\n',' ') for v in vals)+' |')
md+=['','逐项的四维检查、原件链接与作用范围见同名 JSON。达标表示本轮可核实范围内符合该教学目的，不等于逐字校勘、版权授权认证或提分效果保证。']
(HERE/'audit-content-20260919.md').write_text('\n'.join(md)+'\n',encoding='utf8')
print(json.dumps({'items':len(items),'statuses':dict(counts),'categories':dict(cats),'unique_selectors':len({x['target_selector'] for x in items})},ensure_ascii=False))
