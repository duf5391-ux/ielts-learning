from pathlib import Path
from pypdf import PdfReader
import json,re,html,hashlib

ROOT=Path(__file__).parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
D=Path('D:/Codex-IELTS-2026-09-14/expansion-2026-09-14')
out={'date':'2026-09-19','cases':[],'assetsToCopy':[]}
def clean(t):return re.sub(r'\s+',' ',t).strip()
def page(path,n):return PdfReader(path).pages[n-1].extract_text() or ''
def source(path,title,pages,answerpage,answerpath=None,kind='官方样题'):
    p=Path(path)
    if p.is_absolute():
        try:rel=p.relative_to(BOOK).as_posix()
        except ValueError:
            rel='case-assets/reading-official-'+p.name
            out['assetsToCopy'].append({'source':p.as_posix(),'target':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    else:rel=str(path)
    return {'id':hashlib.sha256(rel.encode()).hexdigest()[:12],'title':title,'originalUnit':title,'path':rel,'page':pages,'answerPage':answerpage,**({'answerPath':answerpath} if answerpath else {}),'kind':kind}
def add(cid,title,src,paras,typ,instruction,qs,intensive):
    c={'id':cid,'skill':'reading','title':title,'source':src,'questionTypes':[typ],'instructions':instruction,'paragraphs':[{'label':label,'text':text} for label,text in paras],'questions':qs,'intensive':intensive,'wordCount':sum(len(re.findall(r"\b[\w’-]+\b",t)) for _,t in paras),'status':'达标','verified':{'source':'完整原材料、原题和答案页已逐项读取','answer':'答案与原件核对；证据取自展示片段'}}
    out['cases'].append(c);return c
def q(n,p,a,e,why,options=None):return {'number':n,'prompt':p,'answer':a,'evidence':e,'explanation':why,**({'options':options} if options else {})}
def save():
    for c in out['cases']:
        if c['id'] in ('rd-official-diagram','rd-official-table'):
            c['footnotes']=['原题 Glossary：dung — the droppings or excreta of animals','原题 Glossary：cow pats — droppings of cows']
    out['summary']={'cases':len(out['cases']),'questions':sum(len(c['questions']) for c in out['cases'])}
    (ROOT/'authentic-reading-official-cases.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')

miles=BOOK/'原始参考/b09e5747-miles-student.pdf'
raw=page(miles,1)+page(miles,2)
raw=re.sub(r'Page \d+ of 10\s+IELTS is jointly owned by.*?takeielts.britishcouncil.org','',raw,flags=re.S)
raw=raw[raw.index('A  At the age'):raw.index('https://takeielts')]
raw=re.sub(r'1 An iconoclast is somebody who challenges traditional beliefs or customs','',raw)
segments=re.split(r'\n\s*([B-F])\s+(?=[A-Z])',raw)
paras=[('A',clean(segments[0][1:]))]+[(segments[i],clean(segments[i+1])) for i in range(1,len(segments),2)]
assert [p[0] for p in paras]==list('ABCDEF')
headings={'i':'A legacy is established','ii':'Formal education unhelpful','iii':'An education in two parts','iv':'Branching out in new directions','v':'Childhood and family life','vi':'Change necessary to stay creative','vii':'Conflicted opinions over Davis’ earlier work','viii':'Davis’ unique style of trumpet playing','ix':'Personal and professional struggles'}
explanations=[
 ('viii','These early lessons, paid for and supported by his father, had a profound effect on shaping Davis’ signature sound.','父亲和13岁是背景，核心是独特的straight tone及其终身保留，故v childhood太宽且偏离主旨。'),
 ('iii','he continued his musical education both in the clubs and in the classroom.','课堂与俱乐部是两部分。虽然退学并批评学校，后来仍承认理论与技巧训练有价值，不能选ii。'),
 ('i','Davis’ legacy as one of the most innovative musicians of his era.','先写创新风格，再写当时失败、后来历史认可，段落落点是确立legacy，不是只谈当时意见分歧。'),
 ('ix','his romance with a French actress and some musical partnerships that ruptured as a result of creative disputes.','关系破裂属个人困境，音乐合作冲突和被评论家忽视属职业困境，两半共同满足ix。'),
 ('iv','began to diversify his output across a range of musical styles.','funk→fusion→pop→hip hop是扩展音乐方向，年份本身不是主旨。'),
 ('vi','remaining stylistically inert would have hampered his ability to develop new ways of producing music.','批评是引入，末句说明变化释放音乐潜能；重点是为何必须变化而非只列别人不赞成。')]
for idx,letters in enumerate(['ABC','DEF'],1):
    ps=[p for p in paras if p[0] in letters]
    qs=[q(14+i,'Paragraph '+letter,explanations[i][0],explanations[i][1],explanations[i][2],headings) for i,letter in enumerate('ABCDEF') if letter in letters]
    add('rd-official-miles-'+str(idx),'Miles Davis：'+('独特音色、双重教育与音乐遗产' if idx==1 else '困境、跨界与创造力'),source(miles,'British Council · Academic Practice Test 2 · Miles Davis · Q14–19',[1,2],2,'原始参考/e885c438-miles-teacher-feedback.pdf'),ps,'matching-headings','Choose the correct heading for each paragraph from the list of headings. Write the correct Roman numeral, i–ix. 本组保留原题号；同一标题不可重复使用。',qs,{'structure':'先给每段写一个完整主旨，再看标题；人物、年份和曲名用于定位，不能取代段落整体意思。','sentences':explanations[0 if idx==1 else 5][1],'phrases':'signature sound＝独特音色；in hindsight＝事后回看；stylistically inert＝风格停滞。'})

older=BOOK/'原始参考/2539b427-older-workers-student.pdf'
raw=page(older,1);raw=raw[raw.index('The general assumption'):].strip()
oparas=[('1',clean(raw[:raw.index('One innovation')])),('2',clean(raw[raw.index('One innovation'):raw.index('The best way')])),('3',clean(raw[raw.index('The best way'):raw.index('If the job market')])),('4',clean(raw[raw.index('If the job market'):]))]
qs=[q(1,'In paragraph one, the writer suggests that companies could consider','A','Take away seniority-based pay scales, and older workers may become a much more attractive employment proposition.','建议取消按资历定薪的制度。piece-rates只用作反例，不是作者建议废除它。',{'A':'abolishing pay schemes that are based on age.','B':'avoiding pay that is based on piece-rates.','C':'increasing pay for older workers.','D':'equipping older workers with new skills.'}),q(2,'Skill Team is an example of a company which','C','thus allowing it to retain access to some of the intellectual capital it would otherwise have lost.','保留经验和知识正对应expertise。88%不是加薪，工作到60岁不是想多久就多久。',{'A':'offers older workers increases in salary.','B':'allows people to continue working for as long as they want.','C':'allows the expertise of older workers to be put to use.','D':'treats older and younger workers equally.'}),q(3,'According to the writer, ‘bridge’ jobs','D','those who continue working because they have to and those who continue working because they want to','两类人的动机不同，D概括distinct groups。美国研究发生地不能推出起源于美国，最佳和最差薪酬者也不等于中间薪资。',{'A':'tend to attract people in middle-salary ranges.','B':'are better paid than some full-time jobs.','C':'originated in the United States.','D':'appeal to distinct groups of older workers.'}),q(4,'David Storey’s study found that','B','70% of businesses started by people over 55 survived, compared with an overall national average of only 19%.','较高企业存活比例支持经营表现，未给自雇人数随时间增多趋势或年轻人拥有企业的比例。',{'A':'people demand more from their work as they get older.','B':'older people are good at running their own businesses.','C':'an increasing number of old people are self-employed.','D':'few young people have their own businesses.'})]
add('rd-official-older-workers','Older workers：薪资条件与两种继续工作的动机',source(older,'IELTS.org Academic Reading Sample Tasks 2023 · Older workers · Q1–4',[1,2],1,'原始参考/beeea772-older-workers-answer-key.pdf'),oparas,'multiple-choice','Choose the correct letter, A, B, C or D. Write the correct letter in boxes 1–4.',qs,{'structure':'一般假设→企业方案→桥接岗位→创业能力。四题各取一段，保留条件与比较对象。','phrases':'in spite of而非because of；retain access to intellectual capital＝继续利用知识经验；bridge jobs＝全职与退休间的过渡岗位。','sentences':'The general assumption is that… 标为社会假设，不代表作者认定所有年长工作者低产。'})
save()

audit=json.loads((ROOT/'audit-content-20260919.json').read_text(encoding='utf8'))
supp=[]
for aid,cid in [(75,'rd-official-miles-1'),(76,'rd-official-older-workers')]:
    c=next(c for c in out['cases'] if c['id']==cid);a=next(a for a in audit['items'] if a['id']==f'audit-{aid:03d}')
    h='<h4>'+html.escape(c['title'])+'</h4><p>以下原文与题号构成独立补充，原导读保留其待核状态。</p>'+''.join('<p lang="en">'+html.escape(p['label']+' '+p['text'])+'</p>' for p in c['paragraphs'])+'<h4>原题答案与具体证据</h4>'+''.join('<p>Q'+str(q['number'])+' '+html.escape(q['prompt'])+'：'+html.escape(q['answer'])+'。'+html.escape(q['explanation'])+'</p><blockquote>'+html.escape(q['evidence'])+'</blockquote>' for q in c['questions'])
    supp.append({'auditId':a['id'],'target_selector':a['target_selector'],'anchor':a['anchor'],'title':c['title'],'caseIds':[cid],'teachingHtml':h,'sourceRefs':[{'label':c['source']['title'],'path':c['source']['path'],'page':1},{'label':'原答案','path':c['source']['answerPath'],'page':c['source']['answerPage']}],'verification':{'status':'达标（新增补充）','originalStatus':'可疑','sourceRead':True,'answer':'原教师答案/官方答案已逐题核对','doesNotCertifyUnchangedOriginal':True}})
for m in supp:
    c=next(c for c in out['cases'] if c['id']==m['caseIds'][0])
    options=[]
    for question in c['questions']:
        op=question.get('options',{})
        text='；'.join(str(k)+' '+str(v) for k,v in op.items()) if isinstance(op,dict) else '；'.join(op)
        if text and text not in options:options.append(text)
    block='<h4>原题选项</h4>'+''.join('<p>'+html.escape(t)+'</p>' for t in options)
    m['teachingHtml']=m['teachingHtml'].replace('<h4>原题答案与具体证据</h4>',block+'<h4>原题答案与具体证据</h4>')
(ROOT/'reading-official-remediations.json').write_text(json.dumps({'supplements':supp},ensure_ascii=False,indent=2),encoding='utf8')

diagram=next(D.glob('*115012*.pdf'));table=next(D.glob('*115018*.pdf'))
text=page(diagram,1);text=text[text.index('Introducing dung'):text.index('Glossary')]
begins=['Introducing dung','Dung beetles work','For maximum dung']
parts=[text[text.index(s):text.index(begins[i+1]) if i<2 else len(text)] for i,s in enumerate(begins)]
beetles=[(str(i+1),clean(t).replace('dung1','dung').replace('pats2','pats')) for i,t in enumerate(parts)]
opts=['French','Spanish','Mediterranean','South African','Australian native','South African ball roller']
c=add('rd-official-diagram','蜣螂隧道：用深度和形状读图',source(diagram,'Cambridge Academic Reading official sample · Dung beetles',[1,2],3),beetles,'diagram-label-completion','Label the tunnels on the diagram below using words from the box. Write your answers in boxes 6–8. 按原图位置作答，词框完整保留。',[q(6,'原图标号6所指隧道的种类','South African','South African beetles dig narrow tunnels of approximately 20 cm below the surface of the pat.','左侧隧道约20cm，匹配South African；ball roller把球滚离粪堆，不能因同国别选它。',opts),q(7,'原图标号7所指隧道的种类','French','Some large species originating from France excavate tunnels to a depth of approximately 30 cm below the dung pat.','中间最深约30cm，与French对应，sausage-shaped chambers补充形状证据。',opts),q(8,'原图标号8所指隧道的种类','Spanish','The shallowest tunnels belong to a much smaller Spanish species','右侧最浅且分叉如梨树，matching shallowest；不是用甲虫体长当隧道深度。',opts)],{'structure':'引入方法→隧道与球滚行为→不同季节的物种互补。答图示以第二段为关键，前后段帮助区分物种与生态功能。','phrases':'approximately表示约数；shallowest是最浅；below surface以地表为参照。','sentences':'Most species… 并不意味着所有物种均挖隧道，下一句surface-dwelling明确另有方式。'})
c['contextNote']='原官方样题完整保留连续三段，图示与下一组表格为同篇材料的不同正式题组，不计作两篇独立原文。'
def attach_image(c,name):
    file=ROOT/name;rel='case-assets/'+name;c['image']=rel
    out['assetsToCopy'].append({'source':file.as_posix(),'target':rel,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
attach_image(c,'official-diagram-original.png')
c=add('rd-official-table','蜣螂物种：沿表格列名核对信息',source(table,'Cambridge Academic Reading official sample · Dung beetles',[1,2],3),beetles,'table-completion','Complete the table below. Choose NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes 9–13. 原表保留行列及已给数据。',[q(9,'Spanish → Preferred climate → 9 …','temperate','temperate-climate Spanish species','Spanish行气候列；cool在示例French行，不能横向抄错。'),q(10,'Spanish → Start of active period → 10 …','early spring','The latter, which multiply rapidly in early spring','latter回指Spanish，不是French的late spring。'),q(11,'Spanish → Number of generations per year → 11 …',['two to five','2-5'],'produce two to five generations annually','annually对应per year，不能填French的一到两代；两种写法来自原答案。'),q(12,'South African ball roller → Preferred climate → 12 …','sub-tropical','The South African ball-rolling species, being a sub-tropical beetle','气候不是地点，northern/coastal New South Wales是分布地区，不符合列名。'),q(13,'South African ball roller → Complementary species → 13 …',['South African tunneling','South African tunnelling'],'it commonly works with the South African tunneling species','works with对应complementary；必须写区分tunneling，不能只写South African。')],{'structure':'先按行锁定Spanish或South African ball roller，再看列问气候、活动起始、代数还是互补物种；former/latter须回指正确。','phrases':'temperate-climate→temperate；annually→per year；works with→complementary species。','sentences':'The former… The latter… 两句的对照从上一句French与Spanish的出现次序确定。'})
attach_image(c,'official-table-original.png')
c['contextNote']='与蜣螂图示组共用同一篇完整原文；这是原题Q9–13的另一种信息组织方式。'

food=next(D.glob('*115026*.pdf'));text=page(food,1);text=text[text.index('Fancy Foods wishes'):]
starts=['Fancy Foods wishes','If you have any jars','No payment will','Jars of Fancy','Fancy Foods will pay a reward']
ps=[text[text.index(s):text.index(starts[i+1]) if i<4 else len(text)] for i,s in enumerate(starts)]
ps=[(str(i+1),clean(t).replace('REWARD','').replace('piec es','pieces').replace('bat ches','batches').replace('plea se','please').replace('they  can','they can').replace('F ancy','Fancy').replace(' fo r ',' for ')) for i,t in enumerate(ps)]
add('rd-official-short-answer','产品召回：批次、退款与联系人',source(food,'Cambridge General Training Reading official sample · Product return',[1],2),ps,'short-answer-questions','Answer the questions below. Choose NO MORE THAN THREE WORDS AND/OR A NUMBER from the text for each answer. Write your answers in boxes 4–8.',[q(4,'What has been found in some Fancy Foods products?','pieces of metal','pieces of metal have been found in some jars','问发现的异物，不问产品名称。三词恰好符合上限。'),q(5,'Where can you find the batch number on the jars?',['the bottom','on the bottom'],'The batch number is printed on the bottom of each jar.','是罐底，不是退货地点supermarket。'),q(6,'How much will you receive for an opened jar of contaminated Chicken Curry?','$5','$10 for each jar returned unopened and $5 for each jar already opened.','opened与unopened对应两种金额，empty则不给钱。'),q(7,'If you have eaten Chicken Curry from a jar with one of the batch numbers listed, whom should you contact?',['Retailing Manager','the Retailing Manager'],'the Retailing Manager will be interested to hear from people who have consumed chicken curry','吃过产品找Retailing Manager；提供谁投放金属的线索找Customer Relations Manager，勿交换两个身份。'),q(8,'What is the maximum reward Fancy Foods is offering for information about who contaminated their product?','$50,000','a reward of $10,000 to $50,000','maximum取区间上限，不能取首次看到的10,000。')],{'structure':'召回对象→退货及金额→空罐与已食用者→不受影响口味→悬赏。完整五段不能省掉第四段的排除条件。','phrases':'batch number＝批号；preferably＝最好而非必须；maximum＝上限。','sentences':'No payment… However…区分空罐不退款与希望已食用者联系；不退款不代表无需联系。'})
save()
