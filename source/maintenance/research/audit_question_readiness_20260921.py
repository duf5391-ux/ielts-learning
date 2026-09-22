"""L2 mechanical checklists. Presence cannot establish question semantics."""
from pathlib import Path
from collections import Counter
import json,hashlib,re
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];ARCH=ROOT/'downloads/jiufen-jijing-20260921';OUT=ROOT/'research/content-tensor-20260921'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
plain=lambda v:BeautifulSoup(str(v or ''),'html.parser').get_text(' ',strip=True)
assets=read(ARCH/'media-index.json')['assets'];rows=[];parts=[];skipped=[]
for source in read(ARCH/'materials-index.json')['items']:
 if not source['bodyAcquired'] or source['entryMode']=='memory_link':
  skipped.append({'sourceId':source['id'],'reason':'missing-body' if not source['bodyAcquired'] else 'unstructured-memory-link'});continue
 raw=ARCH/source['rawPath'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==source['rawSha256']
 for part in read(raw).get('data',{}).get('parts',[]):
  qs=[q for g in part.get('groups',[]) for q in g.get('questions',[])];nums=[str(q.get('qNumber') or '') for q in qs]
  numeric=[int(n) for n in nums if n.isdigit()]
  number_status='pass' if numeric and len(numeric)==len(nums) and numeric==list(range(min(numeric),max(numeric)+1)) else 'review'
  audio=assets.get(part.get('audioUrl'),{});audio_path=ARCH/audio['path'] if audio.get('path') else None
  audio_status='not-required' if source['subject']!='listening' else 'pass' if audio_path and audio_path.is_file() else 'missing'
  part_id=str(part.get('id'));parts.append({'sourceId':source['id'],'partId':part_id,'questionCount':len(qs),'numberSequence':number_status,'audioPresence':audio_status,'audioSemantics':'unreviewed'})
  seen=Counter(str(q.get('id')) for q in qs)
  for group in part.get('groups',[]):
   group_text=plain(group.get('contentHtml'));instructions=plain(group.get('typeDescription') or group.get('description'))
   for q in group.get('questions',[]):
    qid=str(q.get('id'));prompt=plain(q.get('question') or q.get('prompt'));options=q.get('options') or []
    checks={'uniqueId':'pass' if qid not in ['None',''] and seen[qid]==1 else 'fail',
      'questionNumber':'pass' if str(q.get('qNumber') or '').isdigit() else 'review',
      'promptPresence':'direct' if prompt else 'group-context-needs-mapping' if group_text else 'missing',
      'instructionsPresence':'pass' if instructions else 'review',
      'optionsPresence':'present' if options else 'group-or-type-review',
      'sourceAnalysis':'present-unverified' if q.get('analyses') or q.get('analysisText') else 'missing',
      'mediaPresence':audio_status,'canonicalAnswer':'present-unverified' if q.get('rightAnswer') not in [None,'',[]] else 'absent'}
    rows.append({'checklistId':f"l2:{source['id']}:{part_id}:{qid}:v1",'sourceId':source['id'],'sourceVersion':source['rawSha256'],
      'partId':part_id,'questionId':qid,'number':q.get('qNumber'),'type':q.get('type'),'subject':source['subject'],'checks':checks,
      'practiceEligible':False,'reason':'requires semantic prompt mapping, media verification, feedback and browser save checks','testEligible':False})
summary={'questionObjects':len(rows),'bySubject':dict(Counter(r['subject'] for r in rows)),'parts':len(parts),'skippedSources':len(skipped),
 'checkCounts':{k:dict(Counter(r['checks'][k] for r in rows)) for k in rows[0]['checks']},'practiceAutomaticallyPromoted':0,'testEligible':0,
 'limits':['Presence checks only; source analyses are not verified answers','Writing task objects are counted separately from listening/reading questions','Shared group prompts require explicit question-to-blank mapping; unknown is not pass']}
(OUT/'question-readiness.json').write_text(json.dumps({'summary':summary,'parts':parts,'skippedSources':skipped,'questions':rows},ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'question-readiness-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False))
