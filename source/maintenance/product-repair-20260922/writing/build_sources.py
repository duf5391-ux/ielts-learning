"""Capture only already published complete writing questions and their exact sources."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
page=(BOOK/'开始学习.html').read_text(encoding='utf8');soup=BeautifulSoup(page,'html.parser')
cases=json.loads((ROOT/'authentic-writing-cases.json').read_text(encoding='utf8'))['cases']
old={'wc-c21-t1-jobs':'jobs','wc-official-bricks':'bricks','wc-c21-t2-cafe':'cafe','wc-c21-t4-primary':'primary','wc-official-tourism':'tourism','wc-c21-t1-homes':'housing'}
extra={
'wc-c21-t1-jobs':[('writing1-first','学习',['writing1-essay','writing1-revision']),('writing1-text-us-jobs','学习',[]),('pr-writing1-jobs','练习局部',['pr-writing1-jobs-q1','pr-writing1-jobs-q2']),('test-writing','测试',['full-test-writing-task1'])],
'wc-official-bricks':[('writing1-text-bricks','学习',[]),('pr-writing1-bricks','练习局部',['pr-writing1-bricks-q1','pr-writing1-bricks-q2'])],
'wc-c21-t2-cafe':[('pr-writing1-cafe','练习局部',['pr-writing1-cafe-q1','pr-writing1-cafe-q2'])],
'wc-c21-t4-primary':[('pr-writing2-primary','练习局部',['pr-writing2-primary-q1','pr-writing2-primary-q2'])],
'wc-official-tourism':[('writing2-text-tourism','学习',[]),('pr-writing2-tourism','练习局部',['pr-writing2-tourism-q1','pr-writing2-tourism-q2'])],
'wc-c21-t1-homes':[('pr-writing2-housing','练习局部',['pr-writing2-housing-q1','pr-writing2-housing-q2']),('test-writing','测试',['full-test-writing-task2'])],
'wc-c21-t2-entertainment':[('writing2-first','学习',['writing2-essay','writing2-revision']),('writing2-text-theatres','学习',[])],
'wc-official-wealth':[('writing2-text-family-wealth','学习',[])],
'wc-official-education':[('writing1-text-further-education','学习',[])]}
for cid,r,prefix in [('wc-official-education','learn-writing1_compare_groups','enrich-writing1_compare_groups'),('wc-official-bricks','learn-writing1_process_branches','enrich-writing1_process_branches'),('wc-official-wealth','learn-writing2_position_mechanism','enrich-writing2_position_mechanism'),('wc-official-tourism','learn-writing2_weigh_consequences','enrich-writing2_weigh_consequences')]:
 extra.setdefault(cid,[]).append((r,'学习局部',[prefix+'-answer',prefix+'-revision']))
rows=[]
for case in cases:
 cid=case['id'];origin=case['skill']+'-case-'+cid;node=soup.find(id=origin)
 prompt=node.select_one('.case-task[lang="en"]')
 assert prompt.get_text(' ',strip=True)==case['prompt'],cid
 if case.get('image'):assert node.select_one('.case-figure')['src']==case['image'] and (BOOK/case['image']).is_file()
 aliases=[dict(route=origin,label='练习段落',fields=['case-'+cid+'-answer','case-'+cid+'-revision'])]+[dict(route=r,label=l,fields=f) for r,l,f in extra.get(cid,[])]
 for a in aliases:assert soup.find(id=a['route']),a
 rows.append(dict(id='ww-'+old.get(cid,cid+'-v1'),questionId=cid,version=1,title=case['title'],skill=case['skill'],type=case['questionType'],prompt=case['prompt'],instruction=case['originalTaskInstruction'],image=case.get('image'),sourceHtml=str(node.select_one('.case-source')),source=case['source'],origin=origin,aliases=aliases,existing=cid in old,prepHtml=str(node.select_one('.material-writing') or ''),confidence='高（题面与来源已核对；练习讲解为编写内容）'))
for node in soup.select('.jj-unit[id*="-v1"]'):
 if not node.select_one('.jj-prompt'):continue
 origin=node['id'];info=node.select_one('p.small');source=node.select('p.small')[-1]
 rows.append(dict(id='ww-'+origin.removeprefix('pr-'),questionId=origin,version=1,title=node.h2.get_text(' ',strip=True),skill='writing2',type='Task 2',prompt=node.select_one('.jj-prompt').get_text(' ',strip=True),instruction='Write at least 250 words.',image=None,sourceHtml=str(source)+str(info),source={'title':'九分学长','kind':'非官方题目参考','url':'https://www.9fnnn.com/'},origin=origin,aliases=[dict(route=origin,label='练习',fields=[origin+'-essay'])],existing=False,prepHtml='',confidence='中（原题已下载，具体考场与日期未核实）',difficultyHtml=str(node.select_one('.jj-update-meta'))+str(node.select_one('.jj-difficulty'))))
refpath=BOOK/'机经资料/jijing-20260920/writing-task2.html';ref=BeautifulSoup(refpath.read_text(encoding='utf8'),'html.parser')
for node in ref.select('section[id]'):
 qid=node['id'];origin='pr-'+qid;title=node.h2.get_text(' ',strip=True).split(' · ',1)[1];link=node.select_one('a[href]');url=link['href']
 sourcehtml='<p class="ww-muted">IELTS Actual Tests 题干参考；来源标为2026年9月回忆，具体考场未核实。'+str(link)+f' · <a href="机经资料/jijing-20260920/writing-task2.html#{qid}">本批保留题面</a></p>'
 version=2 if qid.endswith('v2') else 1
 if version==2:sourcehtml+='<p class="ww-muted">此题沿用已发布 v2：仅整理英文语法与搭配，题意不变。</p>'
 rows.append(dict(id='ww-'+qid,questionId=qid,version=version,title=title,skill='writing2',type='Task 2',prompt=node.select_one('[lang=en]').get_text(' ',strip=True),instruction='Give reasons for your answer and include any relevant examples from your own knowledge or experience. Write at least 250 words.',image=None,sourceHtml=sourcehtml,source={'title':'IELTS Actual Tests','kind':'非官方题目参考','url':url},origin=origin,aliases=[dict(route=origin,label='完整题面',fields=[])],existing=False,newOrigin=True,prepHtml='',confidence='中（题干参考；具体考场与日期未核实）',difficultyHtml=str(node.select_one('.jj-update-meta'))+str(node.select_one('.jj-difficulty'))))
assert len(rows)==32 and sum(x['existing'] for x in rows)==6
(HERE/'questions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
script=next(s.get_text() for s in soup.find_all('script') if "const root = document.getElementById('writing-workbench');" in s.get_text())
(HERE/'original-controller.js').write_text(script,encoding='utf8')
(HERE/'source-check.json').write_text(json.dumps(dict(formalSha256=hashlib.sha256((BOOK/'开始学习.html').read_bytes()).hexdigest(),questions=32,task1=8,task2=24,oldTasks=6,referenceSha256=hashlib.sha256(refpath.read_bytes()).hexdigest()),indent=2),encoding='utf8')
print('32 questions captured from formal content and its published reference asset')
