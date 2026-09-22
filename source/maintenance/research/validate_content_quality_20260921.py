"""Full-population mechanical audit; semantic review is explicitly separate."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib,json,re,unicodedata,random
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'downloads/jiufen-jijing-20260921'
OUT=ROOT/'research/content-tensor-20260921';OUT.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda x:hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
index=read(SOURCE/'materials-index.json');slices=read(SOURCE/'reading-slices-index.json')
def text(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',BeautifulSoup(str(s or ''),'html.parser').get_text(' ',strip=True))).strip()
def article(part):
    if part.get('article'):return text(part['article'])
    try:
        obj=json.loads(part.get('articleJson') or '{}')
        return ' '.join(seg.get('text') or ' '.join(sentence.get('text','') for sentence in seg.get('sentences',[])) for seg in obj.get('segments',[])).strip()
    except (ValueError,TypeError):return ''
raw_groups=defaultdict(list);passage_groups=defaultdict(list);task_groups=defaultdict(list)
rows=[];issues=[];question_owners=defaultdict(set)
for row in index['items']:
    sid=row['id'];path=SOURCE/row['rawPath'] if row.get('rawPath') else None
    acquired=row['bodyAcquired'];present=bool(path and path.is_file());verified=present and sha(path.read_bytes())==row['rawSha256']
    if acquired and not verified:issues.append(dict(sourceId=sid,kind='raw_hash_mismatch'))
    data=read(path).get('data',{}) if present and row['entryMode']!='memory_link' else {}
    parts=data.get('parts',[]);questions=[];content=[];prompts=[];media=[];question_keys=[]
    for p in parts:
        content.append(article(p));media.extend([p.get('audioUrl'),*[a.get('url') for a in p.get('assets',[])]])
        for g in p.get('groups',[]):
            prompts.append(text(' '.join(str(g.get(k) or '') for k in ['description','typeDescription','contentHtml','title','title1','title2'])))
            for q in g.get('questions',[]):
                questions.append(q);qid=str(q.get('id') or q.get('questionId') or '')
                if qid:question_owners[qid].add(sid)
                question_keys.append(qid)
                prompts.append(json.dumps({k:q.get(k) for k in ['qNumber','type','question','prompt','options']},ensure_ascii=False,sort_keys=True))
    if row['subject']=='reading':
        frags=[f for f in slices['fragments'] if f['sourceUnitId']==sid]
        content=[' '.join(p for f in frags for p in f['paragraphs'])]
    plain=' '.join(c for c in content if c).strip()
    content_hash=sha(plain.lower()) if plain else None
    task_hash=sha(json.dumps([plain,prompts,sorted(u for u in media if u)],ensure_ascii=False)) if questions else None
    if present:raw_groups[row['rawSha256']].append(sid)
    if content_hash:passage_groups[content_hash].append(sid)
    if task_hash:task_groups[task_hash].append(sid)
    keys=Counter(question_keys)
    duplicate_qids=[q for q,n in keys.items() if q and n>1]
    if duplicate_qids:issues.append(dict(sourceId=sid,kind='duplicate_question_id_in_source',ids=duplicate_qids))
    canonical=sum(q.get('rightAnswer') not in [None,'',[]] for q in questions)
    analysis=sum(bool(q.get('analyses') or q.get('analysisText')) for q in questions)
    rows.append(dict(sourceId=sid,subject=row['subject'],entryMode=row['entryMode'],title=row['title'],rawVerified=verified,
                     acquired=acquired,parts=len(parts),questionObjects=len(questions),canonicalAnswerFields=canonical,
                     questionsWithSourceAnalysis=analysis,contentHash=content_hash,taskHash=task_hash,
                     contentWords=len(re.findall(r'\b[A-Za-z]+\b',plain)),
                     sourceAccuracy=row.get('sourceAverageAccuracy'),sourceAccuracySampleSize=None,
                     confidence={'listening':'高','reading':'低','writing':'中'}[row['subject']],
                     semanticReview='not_yet_reviewed_in_this_audit'))

fragment_ids=[f['id'] for f in slices['fragments']]
assert len(fragment_ids)==len(set(fragment_ids))
assert all(f['sourceUnitId'] in {r['id'] for r in index['items']} for f in slices['fragments'])
coverage=[]
for material in slices['materials']:
    fs=sorted([f for f in slices['fragments'] if f['sourceUnitId']==material['id']],key=lambda f:f['paragraphStart'])
    ranges=[i for f in fs for i in range(f['paragraphStart'],f['paragraphEnd']+1)]
    okay=ranges==list(range(1,material['paragraphCount']+1))
    context=True
    all_paras=[p for f in fs for p in f['paragraphs']]
    for f in fs:
        start,end=f['paragraphStart'],f['paragraphEnd']
        if len(f['paragraphs'])!=end-start+1:context=False
        if f.get('previousParagraph')!=(all_paras[start-2] if start>1 else None):context=False
        if f.get('nextParagraph')!=(all_paras[end] if end<len(all_paras) else None):context=False
    coverage.append(dict(sourceId=material['id'],contiguousCoverage=okay,adjacentContextMatches=context))
    if not okay or not context:issues.append(dict(sourceId=material['id'],kind='fragment_context_mismatch'))

def duplicates(groups):return [dict(hash=k,sourceIds=v) for k,v in groups.items() if len(v)>1]
strata=defaultdict(list)
for row in rows:strata[row['subject']+' / '+row['entryMode']+' / '+('acquired' if row['acquired'] else 'missing')].append(row)
sample=[];rng=random.Random(20260921)
for label,items in sorted(strata.items()):
    for row in rng.sample(sorted(items,key=lambda r:r['sourceId']),min(5,len(items))):
        sample.append(dict(stratum=label,population=len(items),sampleSourceId=row['sourceId'],title=row['title'],reviewStatus='pending'))
report=dict(population=len(rows),rawAcquired=sum(r['acquired'] for r in rows),rawHashVerified=sum(r['rawVerified'] for r in rows),
            questionObjects=sum(r['questionObjects'] for r in rows),canonicalAnswerFields=sum(r['canonicalAnswerFields'] for r in rows),
            questionsWithSourceAnalysis=sum(r['questionsWithSourceAnalysis'] for r in rows),
            exactRawDuplicates=duplicates(raw_groups),sharedPassageGroups=duplicates(passage_groups),exactTaskDuplicates=duplicates(task_groups),
            sharedQuestionIds=[dict(questionId=k,sourceIds=sorted(v)) for k,v in question_owners.items() if len(v)>1],
            readingSources=len(coverage),readingFragments=len(fragment_ids),fragmentCoveragePassed=sum(r['contiguousCoverage'] and r['adjacentContextMatches'] for r in coverage),
            issues=issues,semanticSample=dict(method='固定种子，按科目×原料形态×取得状态分层随机抽样；当前仅生成待审清单，未声称语义审核通过',seed=20260921,count=len(sample)),
            statisticalLimits=['来源平均正确率无样本量，不能计算置信区间或校准难度',
                               '主观参考档位不是命中概率；不做无数据的贝叶斯数值更新',
                               '结构完整不是答案正确；机械检查通过率不是内容正确率',
                               '同段材料跨学习/练习/测试共用曝光家族，不能当独立样本'],rows=rows)
(OUT/'quality-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'semantic-review-sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'fragment-context-audit.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows','sharedQuestionIds','exactRawDuplicates','sharedPassageGroups','exactTaskDuplicates']},ensure_ascii=False))
print(json.dumps({k:len(report[k]) for k in ['exactRawDuplicates','sharedPassageGroups','exactTaskDuplicates','sharedQuestionIds']},ensure_ascii=False))
