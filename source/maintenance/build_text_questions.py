"""Build the reviewed transcriptions of all 21 raster question pages in the workbook.

PDF text was compared with the embedded page images. Keep source spellings even
when unusual; only correct extraction errors, never rewrite a question or answer.
"""
from pathlib import Path
from reviewed_source_notes import annotate_source_html
from html import escape as E
import re, json

HERE = Path(__file__).resolve().parent
QA = HERE / 'text-conversion-qa'
units = []
def p(t): return '<p>'+E(t)+'</p>'
def h(t): return '<h4>'+E(t)+'</h4>'
def ul(items): return '<ul>'+''.join('<li>'+x+'</li>' for x in items)+'</ul>'
def flat(t): return re.sub(r'\s+', ' ', t).strip()
def pages(glob): return re.split(r'===PAGE \d+===',next(QA.glob(glob)).read_text(encoding='utf8'))[1:]
def between(t,a,b): return t.split(a,1)[1].split(b,1)[0]
def add(uid,title,chapter,images,body,**kw):
    units.append(dict(id=uid,title=title,chapter=chapter,images=images,html=annotate_source_html(body),**kw))
def slot(key,n): return f'<span class="qt-slot" data-move-field="{key}" data-number="{n}"></span>'
def blank(n): return f'<strong>{n}</strong> <span class="qt-blank">________</span>'
def options(items,kind='A'):
    return f'<ol class="qt-options" type="{kind}">'+''.join('<li>'+E(x)+'</li>' for x in items)+'</ol>'

# Miles Davis: rejoin the paragraph spanning pages 7 and 8, retain A-F labels.
mp=pages('*miles-student.txt')
raw='A '+between(mp[0],'\nA ', '\n1 An iconoclast')+' '+between(mp[1],'takeielts.britishcouncil.org','https://takeielts')
raw=raw.replace('up-\nand-coming','up-and-coming')
parts=re.split(r'(?:^|\n)\s*([A-F])\s+(?=[A-Z])',raw)
body=h('Surveying the text')+p('1 Survey the following reading passage. (20 seconds)')+h('MILES DAVIS')+p('Icon and iconoclast¹')
for label,text in zip(parts[1::2],parts[2::2]): body+=p(label+'  '+flat(text))
body+=p('¹ An iconoclast is somebody who challenges traditional beliefs or customs')
body+=p('2 What do you expect the text to be about?')+options(['Instructions on how to play a musical instrument','An autobiography of a famous musician','A description of a journey'],'a')
body+=h('Strategy for dealing with Matching Headings questions')
body+=p('3 Skim read the first 4 paragraphs.')+p('4 With a partner, discuss what you think each paragraph is generally about. You can write your ideas in the margin next to paragraphs A-D.')+p('5 Read the headings below, underline any keywords.')
body+=h('List of Headings')+options(['A legacy is established','Formal education unhelpful','An education in two parts','Branching out in new directions','Childhood and family life','Change necessary to stay creative','Conflicted opinions over Davis’ earlier work','Davis’ unique style of trumpet playing','Personal and professional struggles'],'i')
body+=p('6 Work in pairs. Try to match the topic sentences from A,B and D to the headings. Discuss the questions below.')
body+=p('A  These early lessons, paid for and supported by his father, had a profound effect on shaping Davis’ signature sound.')+p('B  Having graduated from high school in 1944, Davis moved to New York City, where he continued his musical education both in the clubs and in the classroom.')+p('D  Though Davis’ trumpet playing may have sounded effortless and breezy, this ease rarely carried over into the rest of his life.')
body+=ul([E(x) for x in ['Discuss how you made your match – which keywords helped you?','Which ones were you sure of?','Which ones were you less sure of and need to read more?','Were all of the topic sentences taken from the first line of the paragraphs?']])
body+=p('7 Put the following into a possible order to give you a strategy for dealing with Matching Headings questions.')
body+=options(['Make final choices as you read more of the text.','Survey the passage, titles, and diagrams.','Try to match the keywords of the headings with the first/topic sentences.','Skim the paragraphs, quickly reading first/topic sentences and final sentences to get an idea of what each paragraph is about.','Read the headings, underlining keywords.','Be careful when transferring answers, use the Roman numerals if provided (i-x).','If you can’t find a match, read the final sentence of the paragraph.','Eliminate any headings used as an example.','If you still can’t find a match, read the whole paragraph.','Repeat for each paragraph or section.'],'a')
body+=p('b)  ______  ______  ______  ______  ______  ______  ______  ______  ______')
body+=p('8 Write your answers to A, B and D. Use the strategy to answer the rest of the questions.')
body+=ul([f'{n}. Paragraph <strong>{label}</strong> ______' for n,label in enumerate('ABCDEF',14)])
add('miles','Miles Davis · 标题匹配','reading',[1,2,3,4],body)

op=pages('*older-workers-student.txt')
raw=('The general assumption'+op[0].split('The general assumption',1)[1]).replace('part- time','part-time')
body=p('[Note: This is an extract from a Part 1 text about older people in the workforce.]')
body+=''.join(p(flat(t)) for t in re.split(r'\n\s*\n',raw) if flat(t))
body+=h('Questions 1–4')+p('Choose the correct letter, A, B, C or D.')+p('Write the correct letter in boxes 1-4 on your answer sheet.')
qtext=op[1].split('answer sheet.',1)[1]
for q,block in re.findall(r'\n\s*([1-4])\s+(.*?)(?=\n\s*[1-4]\s+|\Z)',qtext,re.S):
    pieces=re.split(r'\n\s*[A-D]\s+',block)
    body+=p(q+' '+flat(pieces[0]))+options([flat(t) for t in pieces[1:]])
add('older-workers','Older workers · 单项选择','reading',[5,6],body)

cp=pages('*Cambridge IELTS*txt')
raw1=cp[16];raw2=cp[17]
body=p('You should spend about 20 minutes on Questions 1–13, which are based on Reading Passage 1 below.')+h('The Davies Sisters')
body+=p('Between 1908 and 1924, Gwendoline and Margaret Davies amassed one of the largest collections of late-nineteenth and early-twentieth-century French paintings in Britain')
raw='Gwendoline (1882'+between(raw1,'Gwendoline (1882','• philanthropic:')
raw+='\n'+between(raw2,'Reading\n','*** Impressionist:') if 'Reading\n' in raw2 else '\n'+between(raw2,'Reading \n','*** Impressionist:')
corrections={'·while':'While','Jean- Baptiste':'Jean-Baptiste','lmow':'know','contemporaiy':'contemporary','well-lmown':'well-known','Cezanne':'Cézanne','Provenc;al':'Provençal','Franc;ois':'François'}
for a,b in corrections.items():raw=raw.replace(a,b)
starts=['Gwendoline (1882','While there was','The sisters began','The sisters\' journals','However, it was','The First World War','It was tedious','Commentators have','By the early 1920s','The sisters collected']
paras=re.split(r'\n(?=(?:'+'|'.join(re.escape(x) for x in starts)+'))',raw.strip())
assert len(paras)==10,len(paras)
body+='<div class="qt-passage">'+''.join(p(flat(x)) for x in paras)+'</div>'
body+='<div class="qt-footnotes">'+p('* philanthropic: seeking to promote the welfare of others, often by charitable funding')+p('** Old Master: a highly respected artist of great skill who worked in Europe before about 1800')+p('*** Impressionist: an artist with a style of painting that developed in France in the late 1800s by Renoir, including his well-known painting La Parisienne')+'</div>'
body+=h('Questions 1–7')+p('Complete the notes below.')+'<p>Choose <strong>ONE WORD ONLY</strong> from the passage for each answer.</p>'+p('Write your answers in boxes 1–7 on your answer sheet.')+h('Gwendoline and Margaret Davies')
rs=lambda n:slot('reading-q'+str(n),n)
body+=h('Family and early life')+ul(["their grandfather’s wealth came from "+rs(1)+' and transportation businesses','their upbringing gave them a sense of social responsibility','their '+rs(2)+' was designed to give them an interest in activities such as collecting art','their governess took them on trips to art galleries','they took lengthy '+rs(3)+' about the things they saw in art galleries'])
body+=h('The sisters as art collectors')+ul(['their '+rs(4)+' showed they liked Old Master paintings, but they were expensive to buy','their early purchases were safe, popular paintings','the first Impressionist paintings they bought showed places in '+rs(5)])
body+=h('Impact of First World War')+ul(['they helped bring artists from Belgium to Wales','they worked in a '+rs(6)+' for soldiers in France'])
body+=h('Opinions about the sisters as art collectors')+ul(['were not considered typical collectors – they lived in isolation in the countryside and did not have any '+rs(7)+' who were artists'])
body+=h('Questions 8–13')+p('Do the following statements agree with the information given in Reading Passage 1?')+p('In boxes 8–13 on your answer sheet, write')
body+='<dl class="qt-rules"><dt>TRUE</dt><dd>if the statement agrees with the information</dd><dt>FALSE</dt><dd>if the statement contradicts the information</dd><dt>NOT GIVEN</dt><dd>if there is no information on this</dd></dl>'
statements=['The Davies sisters’ childhood influenced the way they decided to use their wealth.','The Jean-Baptiste-Camille Corot paintings in the Davies sisters’ collection were purchased from a gallery in France.','Hugh Blaker opposed the Davies sisters’ decision to buy art by French Impressionists.','The exhibition of Cézanne paintings at the Bath gallery was very popular with the public.','The impact of the First World War encouraged Gwendoline to reconsider her interest in collecting art.','The Davies sisters bought French Impressionist art during a period when very few people were doing so.']
body+=''.join('<div class="qt-question">'+p(str(n)+'  '+t)+rs(n)+'</div>' for n,t in enumerate(statements,8))
add('davies','The Davies Sisters · 原文与 1–13 题','reading',[7,8,9,10],body)

def writing(n,topic,question=''):
    return h('WRITING TASK '+str(n))+p('You should spend about '+('20' if n==1 else '40')+' minutes on this task.')+(p('Write about the following topic:') if n==2 else '')+'<div class="qt-task">'+p(topic)+(p(question) if question else '')+'</div>'+p('Summarise the information by selecting and reporting the main features, and make comparisons where relevant.' if n==1 else 'Give reasons for your answer and include any relevant examples from your own knowledge or experience.')+p('Write at least '+('150' if n==1 else '250')+' words.')
add('further-education','英国继续教育 · Task 1','writing1',[17],writing(1,'The chart below shows the number of men and women in further education in Britain in three periods and whether they were studying full-time or part-time.'),crop=[100,430,720,1020],crop_alt='Men and women in further education (thousands). Male and Female; 1970/71, 1980/81, 1990/91; Full-time education and Part-time education.')
add('bricks','制砖流程 · Task 1','writing1',[18],writing(1,'The diagram below shows the process by which bricks are manufactured for the building industry.'),crop=[95,475,720,1050],crop_alt='Brick Manufacturing. Digger, clay, metal grid, roller, sand + water, wire cutter or mould, bricks, drying oven 24–48 hrs, kiln moderate 200°C–980°C then high 870°C–1300°C, cooling chamber 48–72 hrs, packaging, delivery.')
add('us-jobs','美国四行业就业 · Task 1','writing1',[19],writing(1,'The graph below gives information about the number of jobs in four sectors of the economy in the US between 1960 and 2020.'),crop=[205,580,1060,1070],crop_alt='Number of jobs in four sectors of the economy in the US, 1960–2020. Jobs in millions; Year; Manufacturing, Retail, Agriculture, Healthcare.')
add('family-wealth','家庭经济与成年生活 · Task 2','writing2',[20],writing(2,'Children who are brought up in families that do not have large amounts of money are better prepared to deal with the problems of adult life than children brought up by wealthy parents.','To what extent do you agree or disagree with this opinion?'))
add('tourism','国际旅游利弊 · Task 2','writing2',[21],writing(2,'International tourism has brought enormous benefit to many places. At the same time, there is concern about its impact on local inhabitants and the environment.','Do the disadvantages of international tourism outweigh the advantages?'))
add('theatres','数字时代的剧院与影院 · Task 2','writing2',[22],writing(2,'Some people say that in the digital age, theatres and cinemas are no longer important as people can watch all the entertainment they want online. Others argue that theatres and cinemas are still important both economically and culturally.','Discuss both these views and give your own opinion.'))
body=h('SECTION 1 · Questions 9 and 10')+p('Choose the correct letter, A, B or C.')+p('9  Type of insurance chosen')+options(['Economy','Standard','Premium'])+p('10  Customer wants goods delivered to')+options(['port','home','depot'])
add('insurance','运输保险 · 听力 9–10 题','listening',[23],body)
body=h('A phone call from a customer')+p('Listen to the phone call from a customer to practise and improve your listening skills.')+h('Before listening')+p('Do the preparation task first. Then listen to the audio and do the exercises.')+h('Preparation task')+p('Match the definitions (a–h) with the vocabulary (1–8).')
body+='<div class="qt-matching"><div>'+h('Vocabulary')+options(['______ '+x for x in ['an exception','payment terms','an invoice','an extension','delivery confirmation','cash flow','a regulation','to appreciate']],'1')+'</div><div>'+h('Definition')+options(['proof that a delivery has been made','the conditions of when a customer should make payment','when more time is allowed for something','an official or organisational rule','a document which shows how much a customer has to pay, for what and by when','when something doesn’t follow the usual rule','to show someone you are grateful for something they have done','the timing and amount of money coming in and going out of a company'],'a')+'</div></div>'
body+=h('Tasks · Task 1')+p('Are the sentences true or false?')
body+='<table class="qt-table"><thead><tr><th scope="col">Sentence</th><th scope="col">Answer</th></tr></thead><tbody>'+''.join('<tr><td>'+str(n)+'. '+E(t)+'</td><td>True / False</td></tr>' for n,t in enumerate(['The delivery hasn’t arrived yet.','Andrea is having cash flow issues and needs a payment extension.','Andrea usually asks for an extension of the payment terms.','Andrea has a new order to place, even bigger than the last one.','Junko can extend the payment terms on the last order to 60 days.','Junko will send Andrea an email confirmation.'],1))+'</tbody></table>'
add('customer-call','客户来电 · 词汇与判断题','listening',[24],body)
ls=lambda n:slot('listening-q'+str(n),n)
body=h('SECTION 1 · Questions 1–8')+p('Complete the form below.')+'<p>Write <strong>NO MORE THAN THREE WORDS AND/OR A NUMBER</strong> for each answer.</p>'+h('PACKHAM’S SHIPPING AGENCY – customer quotation form')
body+='<table class="qt-table qt-shipping"><tbody>'
for label,value in [('Example · Country of destination','Kenya'),('Name','Jacob '+ls(1)),('Address to be collected from',ls(2)+' College, Downlands Rd'),('Town','Bristol'),('Postcode',ls(3)),('Size of container · Length','1.5m'),('Width',ls(4)),('Height',ls(5)),('Contents','clothes<br>'+ls(6)+'<br>'+ls(7)),('Total estimated value','£ '+ls(8))]:
    body+='<tr><th scope="row">'+E(label)+'</th><td>'+value+'</td></tr>'
body+='</tbody></table>'
add('shipping','货运报价单 · 听力 1–8 题','listening',[25],body)
body=h('SECTION 3 · Questions 27–30')+p('Complete the sentences below.')+'<p>Write <strong>NO MORE THAN TWO WORDS</strong> for each answer.</p>'
for n,(start,end) in enumerate([('Studying with the Open University demanded a great deal of ','.'),('Studying and working at the same time improved Rachel’s ',' skills.'),('It was helpful that the course was structured in ','.'),('She enjoyed meeting other students at ','.')],27):
    body+='<p>'+E(start)+slot('listening-review-q'+str(n-26),n)+E(end)+'</p>'
add('open-university','开放大学 · 听力 27–30 题','listening',[26],body)
body=h('Part 2 – Individual long turn')+h('Candidate Task Card')+'<div class="qt-task">'+p('Describe something you own which is very important to you.')+p('You should say:')+ul([E(x) for x in ['where you got it from','how long you have had it','what you use it for']])+p('and explain why it is important to you.')+'</div>'
body+=p('You will have to talk about the topic for 1 to 2 minutes.')+p("You have one minute to think about what you’re going to say.")+p('You can make some notes to help you if you wish.')+h('Rounding off questions')+ul([E(x) for x in ['Is it valuable in terms of money?','Would it be easy to replace?']])
add('important-object','重要物品 · 口语 Part 2','speaking',[27],body)

assert len(units)==14
assert sum(len(u['images']) for u in units)==21
(HERE/'text-questions.json').write_text(json.dumps({'version':1,'units':units},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'units':len(units),'pages':21,'characters':sum(len(u['html']) for u in units)}))
