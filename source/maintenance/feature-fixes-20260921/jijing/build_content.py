"""Build an independently owned, fixed-snapshot subset. Never touches the book."""
import json, hashlib, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'.codex-tools/jijing-libs'))
from bs4 import BeautifulSoup

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(name, obj): (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def text(s): return BeautifulSoup(s or '', 'html.parser').get_text(' ',strip=True)
DATE='2026-09-21'

def difficulty(level, dimensions, reason, scope='同科材料的编辑评估'):
    return {'level':level,'scaleMax':5,'label':{1:'入门',2:'较易',3:'中等',4:'较难',5:'高挑战'}[level], 'dimensions':dimensions,'reason':reason,'scope':scope,'reviewedAt':DATE,'officialBand':None,'learnerMastery':None}

READING_ID='pr-jiufen-20260921-origin-language-v1'
raw=read(HERE/'source-snapshot/raw/exams/2026548860543401986.json')
part=raw['data']['parts'][0]
article=BeautifulSoup(part['article'],'html.parser')
paragraphs=[n.get_text(' ',strip=True) for n in article.find_all('div',recursive=True) if re.match(r'^\([A-H]\) ',n.get_text(' ',strip=True))]
assert len(paragraphs)==8
# The raw page has an answer key field set to null. These are independently
# reasoned answers tied to the actual passage, not imported official keys.
answers=[
 ('27','C','A段末将大量研究活动与有限进展并置，因此作者对二者不相称感到意外。只是列举学科不等于批评学科过多。','A'),
 ('28','A','B段质疑把脑容量直接关联到语言能力的理论：文中所述化石与考古证据使这种关联无法自洽。其余选项与段落明确内容相反，或错误称没有证据。','B'),
 ('29','A','D段认为现代作者应向Rousseau学习把音乐与语言放在一起研究。作者没有把他的思想视作过时。','D'),
 ('30','D','G段先承认Bickerton的贡献，再否定其关于早期语言构成的核心假设。作者说自己曾受说服，现已改变看法。','G'),
 ('31','C','H段末把语言、音乐的起源与祖先的情感生活连接起来；这是作者明确写出的研究意义。','H'),
 ('32','D','A段写巴黎语言学会禁止讨论语言起源，与“不应讨论”对应。','A'),
 ('33','H','C段写Darwin在讨论人类进化的著作中用若干页讨论音乐的发展。','C'),
 ('34','A','C段中Blacking把音乐视为人类内在且普遍的特质；该观点对应音乐是每个人的重要组成部分。','C'),
 ('35','B','D段说Christiansen与Kirby的书自称全面权威，却在17章中没有提及音乐。','D'),
 ('36','E','G段转述Bickerton的观点：早期语言把词串在一起，语法很少或没有。这里考查观点归属，不表示作者赞同。','G'),
 ('37','G','H段转述Wray的观点：早期交流以整体信息为单位，不由可自由组合的单词构成。','H'),
 ('38-40','A、D、E（顺序不限）','B、C、F段分别指出考古与化石证据、音乐、情感受到的关注不足。最后三题作为一个选三项任务保存；三项顺序不限，重复字母不算三个不同选择。','B / C / F')
]
questions=[]
groups=[]
for gi,g in enumerate(part['groups']):
    common=g['questions'][0].get('options',[])
    qlist=g['questions'] if gi<2 else g['questions'][:1]
    ids=[]
    for q in qlist:
        number=q['qNumber'] if gi<2 else '38-40'
        opts=q.get('options') or common
        item={'id':'q'+number,'originalNumber':number,'sourceQuestionIds':[x['id'] for x in g['questions']] if gi==2 else [q['id']], 'prompt':text(q['question']), 'options':[{'label':o['optionNum'],'text':text(o.get('optionContent') or o['option'])} for o in opts], 'responseType':'three-letters' if gi==2 else 'one-letter'}
        questions.append(item);ids.append(item['id'])
    groups.append({'title':g['qRange'],'instructions':text(g['description']),'questionIds':ids})
reading={
 'id':READING_ID,'version':1,'title':'语言起源 · The origin of language','skill':'reading','part':'Passage 3','minutes':30,'estimatedAnswerMinutes':20,
 'sourceId':'2026548860543401986','sourceName':'九分学长','sourceUrl':'https://www.9fnnn.com/','sourceSnapshot':'source-snapshot/raw/exams/2026548860543401986.json','addedAt':DATE,
 'sourceNature':'九分学长下载资料；原文署名Stephen Mithen。具体考场与考试日期未核实，按非官方阅读材料使用。参考答案及中文材料精读由本项目依据本文整理。',
 'instructions':'阅读A–H段后作答。保留原题号27–40；27–31选一个字母，32–37选句尾字母，38–40在同一答题框填三个不同字母，顺序不限。预计作答20分钟、核对与材料精读10分钟；可随时暂停。',
 'contextParagraphs':paragraphs,'contextIntroduction':'The archaeologist Stephen Mithen talks about the ideas behind his new book on the origin of language.',
 'questionCount':14,'responseFieldCount':12,'groups':groups,'questions':questions,
 'answers':[{'id':'q'+n,'answer':a,'explanation':exp,'evidenceParagraphs':p} for n,a,exp,p in answers],
 'answerProvenance':'项目编辑逐题依据原文整理；下载的rightAnswer字段为空。与来源解析交叉比对后重写解释，不声称官方答案或独立盲审。',
 'difficulty':difficulty(4,{'语言抽象度':4,'观点与指代整合':4,'作答结构':3},'讨论语言演化的抽象概念，须持续分清多位研究者与作者的观点；包含单选、句尾匹配和三选项任务。'),
 'closeReadingHtml':'''<h3>这篇文章在讨论什么</h3>
<p>这是一篇作者介绍自己研究思路的论说文。Mithen提出：语言起源研究虽然热闹，进展仍有限；他认为原因包括忽视实物证据、音乐和情感，以及沿用一种他已不再赞同的早期语言模型。全文不是给出已经公认的语言起源结论，而是在解释作者为什么主张另一条研究路径。</p>
<p><strong>A–B段：</strong>A段用研究热度与研究进展的反差提出问题，B段开始解释。关于Neanderthals的语言能力，本文转述的是作者用来质疑脑容量推论的判断；理解时要保留这一观点归属，不把“脑更大”直接读成“语言能力更强”，也不把本文的历史论述当成当代科学定论。</p>
<p><strong>C–D段：</strong>C段把音乐引入讨论，并列举Darwin、Blacking作为曾关注音乐的例外；D段再比较Rousseau与后来的一本书。作者在意的是研究对象之间有没有建立联系，而非简单判断哪一本书出版得更早。</p>
<p><strong>E–F段：</strong>E段提出“音乐有什么作用”，F段以情感回应，并构成一条关系：忽略祖先的情感生活，会让音乐被忽视，继而限制对语言的理解。作者用音乐把情感与语言研究接起来。</p>
<p><strong>G–H段：</strong>G段先肯定Bickerton的学术贡献，再反对他的具体模型；H段引入Wray的替代模型。两种模型的区别不仅是“有没有语法”，更是基本单位：前者是串联的词，后者是不可再拆的整体信息。作者认为后者能同时联系音乐、语言与情感。</p>
<h3>有用的词块与使用边界</h3>
<ul><li><strong>be plagued by</strong>：长期受到某种问题困扰，语气比have a problem强。A段指讨论被奇怪理论搅扰。</li>
<li><strong>a surge of research</strong>：研究活动短期明显增长。surge说的是增长，不自动说明研究质量或成果。</li>
<li><strong>an assumed association between A and B</strong>：A与B之间被假定存在的关联。assumed保留“尚待证实”的距离，不能删去后写成既定因果。</li>
<li><strong>insufficient concern with</strong>：对某事关注不足；这里concern是关注，不是担忧。多次重复把作者的几个理由串起来。</li>
<li><strong>broach the idea that…</strong>：提出某个想法供讨论，不等于证明了这个想法。</li>
<li><strong>draw on</strong>：借鉴、利用已有思想或经验；H段说作者的替代看法借鉴了Wray。</li>
<li><strong>holistic / compositional</strong>：前者按整体起作用，后者由较小单位组合而成。本文把它们用于交流系统的结构，不是“好坏”评价。</li></ul>
<h3>长句拆解</h3>
<p>G段“Bickerton’s idea that the precursor of modern language consisted of words strung together with limited, if any, grammar is, I believe, fundamentally mistaken.”主干是“Bickerton’s idea is fundamentally mistaken”。that从句说明这个想法的内容；strung together修饰words；with limited, if any, grammar意为“语法很少，甚至可能没有”；I believe明确这是Mithen的评价。作者反对的是一套特定模型，不能简化为他认为“任何无语法交流都不存在”。</p>
<p>H段“But in Wray’s proto-language, they were not composed out of smaller units of meaning (i.e. words) which could be combined together using a rule system (i.e. grammar) to make more complex messages with emergent meanings.”they指前面的messages。主干是否定这些信息由更小意义单位构成；which从句解释现代词语可以怎样借助语法组合。层层修饰的作用，是把“完整信息”与“由词组成的信息”区分开。</p>
<h3>指代与篇章关系</h3>
<p>E段the latter回指language，后面的its specific evolutionary history仍谈语言；F段That question承接E段最后对音乐作用的追问。F段This回指忽视情感生活，which再承接对音乐的忽视，形成递进因果链。G段once与now对照作者过去和现在的立场。H段both回指music与language，并不把所有前述理论都合并为作者观点。</p>
<p>回读G–H段，留意作者怎样先承认某人的贡献，再准确界定自己不同意的部分。这种区分让论证有明确对象，不需要把整位学者或整项研究一概否定。需要以后再看时，可收藏文中词句；这里无需额外笔记或测试。</p>'''
}

WRITING=[
 {'sourceId':'2083004583069663233','slug':'adult-literacy','title':'成人读写困难','level':3,'dimensions':{'题意约束':3,'论点抽象度':3,'组织负荷':3},'reason':'须同时解释成人读写困难带来的具体不利处境，并提出由政府实施的对应帮助；不能只写儿童教育。',
 'rubric':['完整回应两问：分别解释成年人不能读写造成的不利处境，以及政府能够采取的帮助。','至少把一个困难说清楚：例如难以理解招聘信息、公共服务说明或医疗文字；说明为什么会产生影响，不只列词。','政府措施应对应前面的困难，例如便利时间的成人课程或易理解的公共信息；交代措施如何产生作用。','使用连贯段落，理由与例子支持同一中心；不要把“成人不识字”泛化成“没有大学学历”。'],
 'language':'<p><strong>Despite better access to education</strong>是让步背景：教育可及性改善了，困难仍存在。access to表示能够获得机会，并不表示每个人已经完成学习。<strong>In what ways are they disadvantaged?</strong>中的they指前面的成年人，问的是处于哪些不利处境；它没有要求先解释识字率低的成因。最后一问把措施的行动主体限定为governments。</p><p><strong>still cannot read or write</strong>强调读写能力，不能随意改成没有高等教育。写作时可使用have difficulty accessing…说明实际障碍，用provide access to…说明支持，但必须根据自己的论点补足对象。</p>'},
 {'sourceId':'2082721901793837057','slug':'work-life-balance','title':'工作与生活的平衡','level':2,'dimensions':{'题意约束':2,'论点抽象度':2,'组织负荷':2},'reason':'常见生活议题，任务是原因与解决办法；主要负荷是建立原因和措施的具体对应，避免只罗列建议。',
 'rubric':['回答为什么难以平衡以及如何改善两部分，保持论点围绕工作与生活其他部分的关系。','解释一个可理解的机制，例如长工时或下班后联系怎样挤压家庭、休息或个人事务。','提出与原因对应、主体明确的办法；说明个人、雇主或其他行动者能够改变什么。','例子应支持因果关系；不必声称所有人都有相同处境，也不把平衡直接等同于工时完全相等。'],
 'language':'<p><strong>balance their work with other parts of their lives</strong>指在工作和生活其他部分之间协调，不是数学上的时间对半分。other parts可以包括家庭、休息、健康或兴趣，题目没有强迫每方面都写。<strong>find it hard to…</strong>里it是形式宾语，真正困难的动作在后面的不定式。</p><p><strong>What are the reasons for this?</strong>中的this回指难以平衡的现象。<strong>How can this problem be overcome?</strong>询问怎样克服该问题；需要说明办法起作用的过程，而不只是列出“提高意识”。</p>'},
 {'sourceId':'2082028220178825218','slug':'species-extinction','title':'自然灭绝与人为保护','level':4,'dimensions':{'题意约束':4,'论点抽象度':4,'组织负荷':3},'reason':'需判断自然过程能否推出不应阻止的主张；可从原因、影响或保护成本等角度论证，不要求固定立场或论证框架。',
 'rubric':['明确同意、不同意或有限度同意题干的主张，并在全文维持可辨认的立场。','分别处理“灭绝是自然过程”与“因此没有理由阻止”之间的推论，避免只泛谈环保。','若区分自然变化与人类造成的加速，解释这种区别怎样影响保护责任或政策选择。','给出具体而不过度概括的理由和例子；可以持不同立场，不以是否选择某个观点判断答案好坏。'],
 'language':'<p><strong>It is a natural process for animal species to become extinct</strong>以it引出不定式内容，先陈述一种过程。<strong>There is no reason why…</strong>随后作出范围很强的判断：不存在应阻止它的理由。前一句的事实性说法与后一句的行动主张不是同一种句子功能。</p><p><strong>prevent this from happening</strong>中的this承接物种灭绝；prevent…from…表示阻止某事发生。<strong>To what extent</strong>允许明确说明同意的程度与条件，不要求采用唯一立场。species可作单数或复数，具体数取决于上下文。</p>'}
]
writing=[]
for cfg in WRITING:
    p=read(HERE/f"source-snapshot/raw/writing/{cfg['sourceId']}.json")['data']['parts'][0]
    art=read_json=json.loads(p['articleJson'])
    prompts=[' '.join(s['text'] for s in seg['sentences']) for seg in art['segments']]
    assert p['writingTaskType'].startswith('task2')
    writing.append({'id':f"pr-jiufen-20260921-{cfg['slug']}-v1",'version':1,'title':cfg['title']+' · Task 2','skill':'writing2','part':'Task 2','minutes':48,'estimatedAnswerMinutes':40,'addedAt':DATE,'sourceId':cfg['sourceId'],'sourceName':'九分学长','sourceUrl':'https://www.9fnnn.com/','sourceSnapshot':f"source-snapshot/raw/writing/{cfg['sourceId']}.json",'sourceNature':'九分学长下载的Task 2题目；具体考场与考试日期未核实。核对要点和题干语言说明由本项目编写；允许不同成立观点，不自动评雅思分数。','instructions':p['description'],'promptParagraphs':prompts,'supplement':p['groups'][0].get('supplementPrompt2') or 'Give reasons for your answer and include any relevant examples from your own knowledge or experience.','rubric':cfg['rubric'],'closeReadingHtml':'<h3>回看这道题的词句</h3>'+cfg['language'],'difficulty':difficulty(cfg['level'],cfg['dimensions'],cfg['reason']),'responseField':'essay','referenceType':'task-specific-self-check-not-model-answer'})

old=ROOT/'content-pipeline/batches/jijing-20260920'
legacy=[read(old/'listening-unit.json'),read(old/'reading-unit.json')]
legacy_difficulties={legacy[0]['id']:difficulty(2,{'词汇与情景':2,'信息区分':2,'记录形式':2},'熟悉的求职对话和短答案笔记；需区分条件、数字、拼写与转折。未按口音或语速另行评级。'),legacy[1]['id']:difficulty(3,{'语言与术语':3,'时间及因果关系':3,'作答结构':3},'食品保存技术的历史说明含专业词、时间转换与因果限制，并结合填空和TRUE/FALSE/NOT GIVEN。')}
decision=read(old/'content-review/release-decision.json')
refs=[r for r in read(old/'content-review/writing-clean.json')['items'] if r['id'] in decision['approved_reference_ids']]
scores=[3,4,4,2,2,3,3,4,3]
titles=['全球文化趋同','偏远自然地区旅游','广告对消费者的影响','儿童在校注意力','儿童学习数学','网络学习与学校','中学国际新闻课程','驾驶最低年龄','独居趋势']
reasons=['需比较文化趋同的利弊并作出权衡，不能只列两边现象。','同时覆盖游客与目的地国家两类主体，各自利弊的组织负荷较高。','一问程度、一问保护措施，需把影响机制与措施对象说清楚。','熟悉的学校情境，需把具体原因与可实行的解决办法对应。','熟悉的学习体验，需解释不喜欢的原因和促进兴趣的办法。','须区分获取信息与学校的其他功能，回应“不再必要”的较强主张。','两种看法与自身意见都要覆盖，说明课程机会成本。','“最好的办法”要求比较措施效果，不能只证明提高年龄有一点作用。','同时解释独居的原因并评价趋势，避免把个人选择等同于统一社会结果。']
for r,s,t,why in zip(refs,scores,titles,reasons):
    legacy_difficulties[r['id']]=difficulty(s,{'题意约束':s,'论点展开':s,'组织负荷':4 if s==4 else s},why,'题干要求的编辑评估；仅参考题干')
    r['displayTitle']=t
    r['difficulty']=legacy_difficulties[r['id']]
write('new-units.json',{'batchId':'jiufen-reviewed-20260921-v1','sourceSnapshotAt':'2026-09-21','units':[reading]+writing})
write('difficulty.json',{'version':1,'reviewedAt':DATE,'scale':'1–5，数值越大表示材料任务负荷越高；只在同科内作相对参考。','method':'按已读题面和材料的语言抽象度、信息/观点整合、作答结构逐项进行编辑判断；不由来源热度、个人作答或未知样本正确率自动换算。','labels':{'1':'入门','2':'较易','3':'中等','4':'较难','5':'高挑战'},'limits':'非官方难度或Band等级，非个人掌握度、预测命中率或统计正确率。无同水平样本校准，1–5是粗略等级，不是精密测量。','officialSources':[{'title':'IELTS Listening format','url':'https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-listening'},{'title':'IELTS Academic Reading format','url':'https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-reading'},{'title':'IELTS Academic Writing format','url':'https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing'},{'title':'IELTS scoring in detail','url':'https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail'}],'items':{**legacy_difficulties,**{u['id']:u['difficulty'] for u in [reading]+writing}}})
write('legacy-reference-display.json',{'items':refs})
print(json.dumps({'newUnits':4,'originalReadingQuestions':14,'newSavedFields':15,'difficultyItems':len(legacy_difficulties)+4},ensure_ascii=False))
