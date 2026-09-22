"""Source -> fragment -> activity -> existing entry, with explicit readiness."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, re
from bs4 import BeautifulSoup
from content_graph_contracts import enrich

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'downloads/jiufen-jijing-20260921'
OUT=ROOT/'research/content-tensor-20260921';OUT.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
index=read(ARCHIVE/'materials-index.json'); slices=read(ARCHIVE/'reading-slices-index.json')
policy={'reading':'低','listening':'高','speaking':'高','writing':'中'}
labels={'reading':'阅读','listening':'听力','speaking':'口语','writing':'写作'}
nodes={};edges={};mapping=[];normalized=[];missing=[]
def node(id,label,kind,group='global',depth=0,**extra):
    nodes[id]=dict(id=id,label=label,kind=kind,group=group,depth=depth,**extra);return id
def edge(a,b,r,evidence):edges[(a,b,r)]=dict(source=a,target=b,relation=r,evidence=evidence)
node('root','新资料内容处理关系','root')
entry_ids={
 'topic':'study-shared-list','study-reading':'study-reading-list',
 'study-listening':'study-listening-list','practice-listening':'practice-listening-list',
 'practice-writing1':'practice-writing1-list','practice-writing2':'practice-writing2-list',
 'study-writing':'study-writing-list','test-listening':'test-listening','test-writing':'test-writing',
 'materials':'library'}
for kind,route in entry_ids.items():node('entry:'+kind,'#'+route,'entry','entries',3,route='#'+route,existing=True)
entry_map={k:'entry:'+k for k in entry_ids}
by_source=defaultdict(list)
for f in slices['fragments']:by_source[f['sourceUnitId']].append(f)
existing=read(ROOT/'feature-fixes-20260921/jijing/new-units.json')['units']
existing_by_source={u['sourceId']:u for u in existing}
approved_path=ROOT/'content-pipeline/batches/jiufen-jijing-20260921/cleaned-luna-20260921/reviewed-package.json'
approved=read(approved_path) if approved_path.exists() else None

def difficulty(row, paragraphs):
    if row['id'] in existing_by_source:return {**existing_by_source[row['id']]['difficulty'],'status':'已编辑评估'}
    # Without calibrated features or an editorial reading, neither the Part
    # number, passage length nor an unreported-sample accuracy is a coefficient.
    return dict(level=None,status='待评估',scale='1–5；编辑系数，不是统计难度',
                reason='尚未逐项完成难度评估；来源正确率缺样本量与独立校验，不用于换算',
                sourceDifficulty=row.get('difficulty'),sourceAccuracy=row.get('sourceAverageAccuracy'))

def activity(source,fid,role,entry,status,conditions,**extra):
    aid=f'activity:{fid}:{role}'
    node(aid,role+' · '+nodes[fid]['label'],'activity',source['subject'],2,role=role,status=status,
         conditions=conditions,sourceId=source['id'],sourceVersion=source.get('rawSha256'),
         exposureFamily='jiufen:'+source['id'],**extra)
    edge(fid,aid,'supports_use','用途映射；必须结合status读取')
    edge(aid,entry_map[entry],'entry_mapping',status+'；映射不代表已发布')
    mapping.append(dict(sourceId=source['id'],fragment=fid,activity=aid,use=role,entry=entry_ids[entry],status=status,
                        conditions=conditions,exposureFamily='jiufen:'+source['id']))

for row in index['items']:
    sid='source:'+row['id'];subject=row['subject'];title=row.get('titleZh') or row['title']
    original=ARCHIVE/row['rawPath'] if row.get('rawPath') else None
    hash_ok=bool(original and original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()==row.get('rawSha256'))
    if row.get('bodyAcquired') and not hash_ok:missing.append(row['id'])
    paragraphs=[p for f in by_source[row['id']] for p in f['paragraphs']]
    diff=difficulty(row,paragraphs)
    normalized.append(dict(sourceId=row['id'],title=title,subject=subject,confidence=policy[subject],
       confidenceBasis='用户指定机经参考策略；不是命中概率或标准答案认证',difficulty=diff,
       source='九分学长',sourcePath=row.get('rawPath'),sourceSha256=row.get('rawSha256'),sourceHashVerified=hash_ok,
       bodyAcquired=row['bodyAcquired'],answerStatus=row['answerStatus'],mediaMissing=row.get('missingMedia',[]),
       canonicalAnswerFields=row.get('canonicalAnswerFields',0),exposureFamily='jiufen:'+row['id']))
    node(sid,title,'source',subject,0,sourceId=row['id'],confidence=policy[subject],difficulty=diff,
         source='九分学长',sourcePath=row.get('rawPath'),sourceSha256=row.get('rawSha256'),sourceHashVerified=hash_ok,
         answerStatus=row['answerStatus'],bodyAcquired=row['bodyAcquired'])
    edge('root',sid,'contains','下载索引；按来源ID去重')
    if subject=='reading':
        for f in by_source[row['id']]:
            fid='fragment:'+f['id'];node(fid,title+f" · 段{f['paragraphStart']}–{f['paragraphEnd']}",'fragment',subject,1,
               sourceId=row['id'],sourceParagraphRange=[f['paragraphStart'],f['paragraphEnd']],
               paragraphs=f['paragraphs'],previousParagraph=f.get('previousParagraph'),nextParagraph=f.get('nextParagraph'),
               fullSource=row.get('path'),confidence='低',difficulty=diff,status='已拆分原料，尚非教学活动')
            edge(sid,fid,'splits_into','reading-slices-index.json；保留相邻段与全文')
            activity(row,fid,'话题资料','topic','prepared',['原文及上下文已取得；主题归类待编辑复核；接入时复用原材料身份'])
            activity(row,fid,'阅读学习','study-reading','needs_design',['需补具体内容解释、词块和长句关系，不能仅展示切片冒充精读'])
            reviewed=next((u for u in (approved or {}).get('units',[]) if u['fragmentId']==f['id']),None)
            if reviewed:
                aid='activity:'+fid+':阅读学习';nodes[aid].update(status='reviewed_unpublished',difficulty=reviewed['difficulty'],reviewedPackage=str(approved_path.relative_to(ROOT)),contentUnitId=reviewed['id'])
                for m in mapping:
                    if m['activity']==aid:m.update(status='reviewed_unpublished',conditions=['主任务修正后精读内容通过复核；仍需真实入口和浏览器验收'])
                key=(aid,entry_map['study-reading'],'entry_mapping')
                edges[key]['evidence']='reviewed_unpublished；正文已复核，尚未发布'
        if row['id'] in existing_by_source:
            u=existing_by_source[row['id']];fid='fragment:'+row['id']+':existing-task'
            node(fid,u['title'],'fragment',subject,1,sourceId=row['id'],status='既有已发布题面与参考')
            edge(sid,fid,'splits_into','已发布小批，不重复新建同题')
            aid='activity:existing:'+u['id'];node(aid,u['title'],'activity',subject,2,status='published',route='#'+u['id'],
                use='既有阅读练习与精读',exposureFamily='jiufen:'+row['id']);edge(fid,aid,'supports_use','旧题及旧答保留，低置信不删除已核查教学内容')
    else:
        raw=read(original).get('data',{}) if hash_ok and row['entryMode']!='memory_link' else {}
        parts=raw.get('parts',[])
        if not parts:
            fid='fragment:'+row['id']+':unstructured';node(fid,title+' · 待核查结构','fragment',subject,1,sourceId=row['id'])
            edge(sid,fid,'splits_into','回忆条目或缺正文；不伪造题目边界')
            activity(row,fid,'听力练习' if subject=='listening' else '写作练习','practice-listening' if subject=='listening' else 'practice-writing2','blocked',
                     ['先核对题目边界、题号、题面、必要媒体与来源版本；高置信不抵消内容缺口'])
        for pi,part in enumerate(parts):
            pid=str(part.get('id') or part.get('partId') or pi);fid='fragment:'+row['id']+':part:'+pid
            qs=[q for g in part.get('groups',[]) for q in g.get('questions',[])]
            node(fid,title+' · '+str(part.get('partNum') or part.get('partNumber') or pi+1),'fragment',subject,1,
                 sourceId=row['id'],partId=pid,questionIds=[q.get('id') or q.get('questionId') for q in qs],
                 sourcePath=row['rawPath'],confidence=policy[subject],difficulty=diff)
            edge(sid,fid,'splits_into','原始parts/groups/questions；保留题号和源ID')
            writing_part='practice-writing1' if '1' in str(part.get('partNum') or part.get('partNumber')) else 'practice-writing2'
            activity(row,fid,'听力练习' if subject=='listening' else '写作练习','practice-listening' if subject=='listening' else writing_part,
                     'needs_validation',['题干/图/音逐项核查后可保存作答','未核实答案不得自动判分；写作需核对标准'],questionCount=len(qs))
            activity(row,fid,'听力学习' if subject=='listening' else '写作学习','study-listening' if subject=='listening' else 'study-writing',
                     'needs_design',['可复用同一题面与原音；另补有依据的讲解/示范','关联练习曝光记录，不生成第二份重复原料'])
            activity(row,fid,'测试候选','test-listening' if subject=='listening' else 'test-writing','conditional',
                     ['明确部分测试或完整考试的范围','满足题面、媒体、时限及核对依据','检查与练习/讲解共用的曝光家族；已见材料标为再测','不把零散题组拼成有官方分数的整卷'])

assert len(normalized)==1063
assert len({r['sourceId'] for r in normalized})==1063
contract_checks=enrich(ROOT,nodes,edges,mapping,approved,entry_map,entry_ids)
relations=sorted({e['relation'] for e in edges.values()});node_index={id:i for i,id in enumerate(nodes)}
data=dict(schema='ielts-content-lineage-v1',nodes=list(nodes.values()),edges=list(edges.values()),relations=relations,
 tensor=dict(notation='A[source_node,target_node,relationship]',shape=[len(nodes),len(nodes),len(relations)],
 entries=[[node_index[e['source']],node_index[e['target']],relations.index(e['relation']),1] for e in edges.values()]),
 semantics={'contains':'来源清单','splits_into':'原料拆分','supports_use':'同源多用途；状态区分可用与计划','entry_mapping':'现有入口映射；非已发布保证'},
 usageTensor=dict(axes=['sourceId','fragmentId','activityRole','existingEntry','readiness'],storage='COO',entries=mapping),
 policy=policy,limits=['本图是完整来源处理方案与证据索引，不代表全批已经发布','来源/难度/置信度标在入口，教学正文不重复堆标签',
 '低置信阅读优先资料与精读；高置信听口优先做题；写作中置信','测试不是练习的简单别名：版本、曝光、条件与作答记录必须独立'])
(OUT/'graph.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'normalized-sources.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2),encoding='utf-8')
summary=dict(contractChecks=contract_checks,sources=len(normalized),bySubject=dict(Counter(x['subject'] for x in normalized)),confidence=dict(Counter(x['confidence'] for x in normalized)),
 nodeTypes=dict(Counter(x['kind'] for x in nodes.values())),activitiesByState=dict(Counter(x['status'] for x in mapping)),
 sourceHashMismatches=missing,canonicalAnswers='原索引标准答案字段0；不从参考置信度推断答案正确',
 speaking='本批未取得口语材料；政策高置信已定义，没有凭空增加口语题')
(OUT/'validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
template=(ROOT/'research/tensor_tree_viewer.html').read_text(encoding='utf-8')
template=template.replace("colors={root:'#ffffff',route:'#72d6ab',function:'#8ca9ee',document:'#d1b37d',state:'#73cce6',field:'#9b8dbe',issue:'#f08e7d'}", "colors={root:'#fff',source:'#72d6ab',fragment:'#8ca9ee',activity:'#d1b37d',entry:'#73cce6',record:'#c799e8',exposure:'#ecad88',artifact:'#87b2bd'}")
template=template.replace("typeNames={root:'系统根',route:'入口 / 内容',function:'功能',document:'独立页面',state:'动态状态',field:'保存字段',issue:'已复现问题'}", "typeNames={root:'处理全景',source:'原始来源',fragment:'原料片段',activity:'活动用途',entry:'现有入口',record:'记录绑定 / 契约',exposure:'曝光契约',artifact:'派生物件'}")
template=template.replace("new Set(['root','route','function','document','state','issue'])", "new Set(['root','source','fragment','activity','entry','record','exposure','artifact'])")
template=template.replace("const zLayers={root:-130,function:-220,route:0,document:170,state:300,field:450,issue:-390};", "const zLayers={root:-130,source:-220,fragment:0,activity:240,entry:410,record:600,exposure:740,artifact:-80};")
template=template.replace("choose('route:vocabulary-review');","choose('source:2062075620860411906');")
template=template.replace('IELTS / 分级张量立体关系树','IELTS / 资料拆分与用途张量图').replace('基线 2f870d2c · 已复现问题 17 项','1063 来源 · 1445 阅读切片 · 多用途与发布条件')
template=template.replace('字段层默认折叠；搜索可找到全部字段。','搜索来源ID或题名，再选择一跳邻域检查同源用途。').replace('字段未执行保存验证。','活动状态区分：已发布 / 原料已备 / 待设计 / 待核查 / 有条件测试。')
template=template.replace('__GRAPH_JSON__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(OUT/'内容分级张量图.html').write_text(template,encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
