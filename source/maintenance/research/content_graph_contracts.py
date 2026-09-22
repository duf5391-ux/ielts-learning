"""Executable graph invariants; contract nodes are NOT fabricated user events."""
import hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup

ROLE_CODES={'话题资料':'topic','阅读学习':'study-reading','听力学习':'study-listening','写作学习':'study-writing','听力练习':'practice-listening','写作练习':'practice-writing','测试候选':'test'}
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def enrich(root,nodes,edges,mapping,approved,entry_map,entry_ids):
    candidate=root/'architecture-repair-20260921/combined.html'
    verification=root/'word-review-separation-20260921/latest-live-verification.json'
    current=root/'product-repair-20260922/candidate.html'
    verified=False
    if verification.exists() and current.exists():
        check=json.loads(verification.read_text(encoding='utf8'))
        verified=check.get('pass') and hashlib.sha256(current.read_bytes()).hexdigest()==check.get('sourceSha256')
        if verified:candidate=current
    page=BeautifulSoup(candidate.read_text(encoding='utf-8'),'html.parser')
    ids={n['id'] for n in page.select('[id]')}
    for route in entry_ids.values():assert route in ids,route
    for key in entry_map.values():nodes[key]['routeEvidence']={'file':str(candidate.relative_to(root)),'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'assertion':'DOM id exists; not an interaction test'}
    # Graph namespace is separate from the canonical fragment identity.
    for n in list(nodes.values()):
        if n['kind']=='fragment':n['fragmentId']=n['id'].removeprefix('fragment:')
    renames={}
    for n in nodes.values():
        if n['kind']=='activity' and n.get('role') in ROLE_CODES:
            code=ROLE_CODES[n['role']];n['roleCode']=code
            renames[n['id']]=n['id'].rsplit(':',1)[0]+':'+code
    for old,new in renames.items():n=nodes.pop(old);n['id']=new;nodes[new]=n
    new_edges={}
    for e in edges.values():
        e['source']=renames.get(e['source'],e['source']);e['target']=renames.get(e['target'],e['target'])
        new_edges[(e['source'],e['target'],e['relation'])]=e
    edges.clear();edges.update(new_edges)
    for m in mapping:m['activity']=renames.get(m['activity'],m['activity']);m['activityRole']=ROLE_CODES.get(m['use'],m['use'])
    def edge(a,b,r,evidence):edges[(a,b,r)]={'source':a,'target':b,'relation':r,'evidence':evidence}
    def contract(id,label,kind,**extra):nodes[id]={'id':id,'label':label,'kind':kind,'group':'records','depth':4,**extra}
    contract('contract:attempt','独立作答契约（未接运行时）','record',status='contract_only',runtimeImplemented=False,
             required=['attemptId','activityId','contentVersion','startedAt','scope','responsesByQuestion','feedbackOpenedAt'],
             owner='current browser profile',storageKey=None,legacyMigration='old answer fields remain in their original store; never fabricate historical attempts')
    contract('contract:material-exposure','材料接触契约（未接运行时）','exposure',status='contract_only',runtimeImplemented=False,
             required=['eventId','sourceId','sourceVersion','fragmentId','kind','at'],kinds=['text-visible','audio-played'])
    contract('contract:answer-exposure','答案接触契约（未接运行时）','exposure',status='contract_only',runtimeImplemented=False,
             required=['eventId','activityId','contentVersion','sourceQuestionId','kind','at'],kinds=['answer-revealed','explanation-revealed'])
    reviewed={u['id']:u for u in (approved or {}).get('units',[])}
    for n in list(nodes.values()):
        if n['kind']!='activity':continue
        parents=[e['source'] for e in edges.values() if e['target']==n['id'] and e['relation']=='supports_use']
        assert len(parents)==1,n['id']
        f=nodes[parents[0]];sid=f['sourceId'];n['sourceId']=sid;n['fragmentId']=f['fragmentId']
        n['sourceVersion']=nodes['source:'+sid].get('sourceSha256')
        n['exposureChannels']={'material':{'sourceId':sid,'fragmentId':n['fragmentId']},'answer':{'activityId':n['id'],'questionIds':f.get('questionIds',[])}}
        n['contentVersion']=None;n['contentVersionStatus']='not-authored'
        unitid=n.get('contentUnitId') or n.get('route','').lstrip('#')
        if unitid in reviewed:
            n['contentVersion']='sha256:'+digest(reviewed[unitid]);n['contentVersionStatus']='reviewed-unpublished'
            if verified:
                n['status']='published';n['contentVersionStatus']='published-reviewed-payload'
                for e in edges.values():
                    if e['source']==n['id'] and e['relation']=='entry_mapping':e['evidence']='Published source SHA verified against live assembly; concrete entry probes passed'
        elif n['status']=='published':
            elem=page.find(id=unitid);assert elem is not None,unitid
            n['contentVersion']='sha256:'+hashlib.sha256(str(elem).encode()).hexdigest();n['contentVersionStatus']='existing-rendered-content'
        elem=page.find(id=unitid) if unitid else None
        n['recordBinding']={'owner':'ielts-finished-book-v1.fields','keys':[x['data-save'] for x in elem.select('[data-save]')],'status':'candidate-binding' if n['status']!='published' else 'legacy-binding'} if elem else {'owner':None,'keys':[],'status':'not-implemented'}
        n['testGate']={'eligible':False,'scope':None,'timeLimitSeconds':None,'scoringBasis':None,'answerBasisVerified':False,'attemptRuntimeImplemented':False,'exposureRuntimeImplemented':False}
        edge(n['id'],'contract:attempt','requires_record','contract requirement; not evidence of a saved attempt')
        edge(n['id'],'contract:material-exposure','tracks_material','separate material exposure; runtime pending')
        edge(n['id'],'contract:answer-exposure','tracks_answer','question-specific answer exposure; runtime pending')
        if n['recordBinding']['keys']:
            rid='record:'+unitid;contract(rid,'保存字段 · '+unitid,'record',binding=n['recordBinding'],sourceId=sid,status='observed-DOM-binding')
            edge(n['id'],rid,'binds_record','existing data-save DOM attributes; persistence needs browser probe')
        if not any(m['activity']==n['id'] for m in mapping):
            mapping.append(dict(sourceId=sid,fragment=parents[0],activity=n['id'],activityRole='existing-practice',use=n.get('use'),entry=unitid,status=n['status'],conditions=['Existing legacy activity, preserve answers'],exposureFamily='jiufen:'+sid))
            eid='entry:existing:'+unitid;nodes[eid]={'id':eid,'label':'#'+unitid,'kind':'entry','group':'entries','depth':3,'route':'#'+unitid,'existing':unitid in ids}
            assert unitid in ids;edge(n['id'],eid,'entry_mapping','existing formal unit route')
    for m in mapping:
        n=nodes[m['activity']];m.update(status=n['status'],contentVersion=n['contentVersion'],fragmentId=n['fragmentId'],recordBinding=n['recordBinding'],testEligible=n['testGate']['eligible'])
    for u in reviewed.values():
        aid='artifact:'+u['id'];p=root/u['sourceLocalPath'];assert hashlib.sha256(p.read_bytes()).hexdigest()==u['sourceSha256']
        nodes[aid]={'id':aid,'label':p.name,'kind':'artifact','group':'reading','depth':1,'sourceId':u['sourceId'],'path':u['sourceLocalPath'],'sha256':u['sourceSha256'],'status':'verified-derived-source'}
        edge('source:'+u['sourceId'],aid,'derives_artifact','raw source and derived HTML have separate hashes')
        edge(aid,'fragment:'+u['fragmentId'],'provides_context','reviewed package ties exact paragraph to original fragment ID')
    activities=[n for n in nodes.values() if n['kind']=='activity']
    assert {n['id'] for n in activities}=={m['activity'] for m in mapping}
    assert all(n['contentVersion'] for n in activities if n['status'] in ['published','reviewed_unpublished'])
    assert all(e['source'] in nodes and e['target'] in nodes for e in edges.values())
    return {'activityMappingEquality':True,'entryRoutesAsserted':len(entry_ids),'eventCount':0,'recordRuntime':'legacy fields only; new attempt/exposure contracts NOT implemented','testEligible':0}
