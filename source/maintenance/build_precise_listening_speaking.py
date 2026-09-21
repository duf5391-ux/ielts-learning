import json, re, html
from pathlib import Path
from reviewed_text_corrections import correct_transcription

ROOT=Path(__file__).parent
LIB=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/materials-library')
AUDIT=LIB/'listening-audit-2026-09-14'
BASE='https://www.cambridgeenglish.org/exams-and-tests/ielts/preparation/'
OFFICIAL='https://ielts.org/take-a-test/preparation-resources/sample-test-questions/academic-test'
cases={x['id']:x for x in json.loads((ROOT/'support-remediations.json').read_text('utf-8'))['cases']}
units=[]

def text_file(path):
    return correct_transcription(re.sub(r'\s+', ' ', Path(path).read_text('utf-8')).strip())

def base(id,section,part,title,source):
    return dict(id=id,section=section,part=part,title=title,source=source,originNote='',context=[],instructions='',prompt='',questions=[],reference='',reasoning=[],pitfalls=[],sourceCaseIds=[],challengeMechanism='')

u=base('pr-listening-p1','listening','Listening Part 1','货物运输',dict(title='Cambridge · Listening sample task · Multiple choice · Questions 9–10',url=BASE,path='原始参考/support-e8b979a4-cambridge-zip-115008_Listening_sample_task_-_Multiple_choice.pdf',page=1,kind='official-sample'))
u.update(context=['Questions 9–10'],instructions='Choose the correct letter, A, B or C.',prompt='A customer is arranging to send a large box overseas.',questions=[dict(id='9',prompt='Type of insurance chosen',options=[dict(id='A',text='Economy'),dict(id='B',text='Standard'),dict(id='C',text='Premium')]),dict(id='10',prompt='Customer wants goods delivered to',options=[dict(id='A',text='port'),dict(id='B',text='home'),dict(id='C',text='depot')])],reference='9 C; 10 A.',sourceCaseIds=['support-listening-insurance'],challengeMechanism='A rejected past experience mentions Economy; the final decision is stated by relative coverage rather than option name. Three delivery locations are all heard.',audio=dict(src='原始参考/c31e6351-recording-2.mp3',title='Recording 2 · Questions 9–10'),transcript=text_file(AUDIT/'transcripts/listening-115008.txt'))
units.append(u)

u=base('pr-listening-p2','listening','Listening Part 2','社区活动',dict(title='Cambridge · Listening sample task · Short-answer questions · Questions 11–16',url=BASE,path='原始参考/support-cb76d836-cambridge-zip-115011_Listening_sample_task_-_Short-answer_questions.pdf',page=1,kind='official-sample'))
u.update(context=['Questions 11–16'],instructions='Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.',prompt='You will hear an extract from a talk given to a group who are going to stay in the UK.',questions=[dict(id='11',prompt='What TWO factors can make social contact in a foreign country difficult? — First answer'),dict(id='12',prompt='What TWO factors can make social contact in a foreign country difficult? — Second answer'),dict(id='13',prompt='Which types of community group does the speaker give examples of? — theatre; ______; ______ (first blank)'),dict(id='14',prompt='Which types of community group does the speaker give examples of? — theatre; ______; ______ (second blank)'),dict(id='15',prompt='In which TWO places can information about community activities be found? — First answer'),dict(id='16',prompt='In which TWO places can information about community activities be found? — Second answer')],reference='11–12 language; customs (in either order). 13–14 music (groups); local history (groups) (in either order). 15–16 (the) (public) library/libraries; (the) town hall (in either order).',sourceCaseIds=['support-listening-social'],challengeMechanism='Additive not just...but; distinguish examples of groups from roles within theatre and places supplying information; theatre already supplied.',audio=dict(src='原始参考/precise-recording-3.mp3',title='Recording 3 · Questions 11–16'),transcript=text_file(AUDIT/'transcripts/listening-115011.txt'))
units.append(u)

u=base('pr-listening-p3','listening','Listening Part 3','远程学习',dict(title='Cambridge · Listening sample task · Sentence completion · Questions 27–30',url=BASE,path='原始参考/support-50078fae-cambridge-zip-115010_Listening_sample_task_-_Sentence_completion.pdf',page=1,kind='official-sample'))
u.update(context=['Questions 27–30'],instructions='Write NO MORE THAN TWO WORDS for each answer.',prompt='Rachel and Paul are discussing studying with the Open University.',questions=[dict(id='27',prompt='Studying with the Open University demanded a great deal of ______.'),dict(id='28',prompt='Studying and working at the same time improved Rachel’s ______ skills.'),dict(id='29',prompt='It was helpful that the course was structured in ______.'),dict(id='30',prompt='She enjoyed meeting other students at ______.')],reference='27 motivation; 28 time management / time-management; 29 modules; 30 summer school(s).',sourceCaseIds=['support-listening-open-university'],challengeMechanism='Different speakers and purposes: Rachel studied with full-time work while Paul intends part-time work; course units versus degree length; home study versus summer-school meeting.',audio=dict(src='原始参考/bb61bf2b-recording-4.mp3',title='Recording 4 · Questions 27–30'),transcript=text_file(AUDIT/'transcripts/listening-115010.txt'))
units.append(u)

u=base('pr-listening-p4','listening','Listening Part 4','学习研究',dict(title='IELTS · Learner Persistence · Questions 33–37',url=OFFICIAL,path='原始参考/precise-listening-part-4-questions.html',kind='official-sample'))
u.update(context=['Research findings · Questions 33–37'],instructions='播放整卷原音中的 Part 4，完成第 33–37 题。Write ONE WORD ONLY for each answer.',prompt='Complete the research findings below.',questions=[dict(id='33',prompt='First level of importance · Personal Characteristics: Enjoyment of a ______'),dict(id='34',prompt='Second level of importance · Social and Environmental Factors: Positive experiences at ______'),dict(id='35',prompt='Second level of importance · Other Factors: Good ______'),dict(id='36',prompt='Second level of importance · Personal Characteristics: Many ______ in daily life'),dict(id='37',prompt='Third level of importance · Social and Environmental Factors: Good interaction with the ______')],reference='33 challenge; 34 school; 35 health; 36 interests; 37 tutor / tutors.',sourceCaseIds=[],challengeMechanism='Three categories crossed with three importance levels, in continuous academic monologue; success contrasted with grades; tutor relationships distinguished from family support.',audio=dict(src='原始参考/precise-official-listening-full.mp3',title='IELTS 整卷原音 · Part 4 · Questions 33–37',segment='Part 4 · Learner Persistence · research findings · Questions 33–37',duration=1778.393438),transcript=text_file(AUDIT/'batch-03/transcripts/current-official-support-10.txt'))
u['verification']={'audioPairing':'Official cached full-demo metadata content item 128122089 includes ILI40154PT as Part 4. MP3 present and earlier browser metadata duration 1778.393438. No independently verified timestamp, therefore none supplied.','questions':'Official QTI ILI40154PT_ib-2. Table cells linearised with original row and column labels retained.','answers':'batch-03/answers/official-answer-mapping.json maps standalone official key 1–5 to full-demo 33–37.','sourceRechecked':'IELTS official academic sample page visited 2026-09-19; confirms Part 4 learner-persistence task.','transcriptDisplay':'Keep hidden until answer submission.'}
units.append(u)

def speaking(id,title,case_id,extra=None):
    c=cases[case_id]
    src=dict(title=c['source']['label'],path=c['source']['path'],page=c['source']['page'],kind='user-provided-exam-material')
    u=base(id,'speaking','Speaking '+c['part'],title,src)
    u.update(recordingRecommended=True,sourceCaseIds=[case_id],reference=c['answer'],referenceType='原创参考作答；无唯一答案',questions=[dict(id=str(n+1),prompt=q) for n,q in enumerate(c['questions'])])
    if extra:
        e=cases[extra]
        u['sourceCaseIds'].append(extra)
        u['questions'] += [dict(id=str(n+len(c['questions'])+1),prompt=q) for n,q in enumerate(e['questions'])]
        u['reference'] += '\n\n'+e['answer']
    return u

u=speaking('pr-speaking-p1','购物与储蓄','support-speaking-c21-t3-p1-shopping','support-speaking-c21-t3-p1-saving')
u.update(instructions='依次口头回答。',challengeMechanism='Habit versus a single past event; unnecessary purchase contrasted with usual care; degrees of importance and future intention.')
units.append(u)
u=speaking('pr-speaking-p2','一个有竞争心的人','support-speaking-c21-t4-p2-competitive')
cue=cases['support-speaking-c21-t4-p2-competitive']['questions']
u.update(instructions='准备 1 分钟，然后连续说 1–2 分钟。',prompt=cue[0],context=['You should say:']+cue[1:],questions=[dict(id='1',prompt='开始作答。')],challengeMechanism='Sustain one coherent person description while covering domain, success, and an inferred motive; concrete event evidence rather than repeated trait adjectives.')
units.append(u)
u=speaking('pr-speaking-p3','体育中的竞争与参与','support-speaking-c21-t4-p3-sport')
u.update(instructions='依次口头回答。',challengeMechanism='Evaluate competitive drive across recreational and professional contexts; explain a position without treating participation and winning as mutually exclusive; qualification and counterexample possible.')
units.append(u)

out={'units':units,'assetCopies':[{'source':str(AUDIT/'audio/recording-3.mp3'),'destination':'原始参考/precise-recording-3.mp3'},{'source':str(LIB/'expansion-2026-09-14/inspera-media-128122089.mp3'),'destination':'原始参考/precise-official-listening-full.mp3'},{'source':str(AUDIT/'batch-03/questions/part-4.html'),'destination':'原始参考/precise-listening-part-4-questions.html'}]}
(ROOT/'precise-listening-speaking.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'units':len(units),'questions':sum(len(u['questions']) for u in units),'assetCopies':[{'sourceExists':Path(a['source']).exists(),'destination':a['destination']} for a in out['assetCopies']]},ensure_ascii=False))
