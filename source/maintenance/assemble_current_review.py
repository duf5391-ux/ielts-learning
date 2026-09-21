"""Publish reviewed evidence from the frozen final content snapshot."""
from pathlib import Path
from collections import Counter
import hashlib, json

ROOT=Path(__file__).resolve().parent
R=ROOT/'research'
SNAP=ROOT/'architecture-audit-qa/delivery-content-snapshot.html'

def save(name,data): (R/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')

def main():
    groups=[json.loads((R/name).read_text(encoding='utf8')) for name in ['teaching-current-a.json','teaching-current-b.json']]
    items=sorted([i for g in groups for i in g['items']],key=lambda i:i['id'])
    assert len(items)==24 and len({i['id'] for i in items})==24
    digest=hashlib.sha256(SNAP.read_bytes()).hexdigest()
    assert all(g['snapshotSha256']==digest for g in groups)
    counts=Counter(i['status'] for i in items)
    for item in items:
        if item['id']=='TC-023':
            item['repair_status']='部分问题已修复；附加听力问题仍未通过'
            item['repair_description']='早先版本的 by Saturday afternoon 误解，在交付快照中已修正：题干问最迟到达时间，答案写最迟周六下午，并区分精确抵达时刻。原课语义问题已核对；附加正式题缺对应录音入口的问题仍成立。'
    data={'date':'2026-09-19','title':'具体教学复核 · 最终固定快照',
          'scope':'24个教学样本及直接链接案例；合格只针对标注用途，不代表整册通过、全部题目核实或提分效果已证实。',
          'method':'三个独立方向复读正文和关联材料，排除旧审查标签；明确区分示范、带提示练习、独立测评。',
          'sourceFiles':[str(SNAP),'teaching-current-a.json','teaching-current-b.json'],
          'snapshotSha256':digest,'counts':{'total':24,'qualified':counts['合格'],'unqualified':counts['不合格']},
          'keyFindings':['已补入具体阅读材料；旧的“未交付材料”理由已撤销。合格不等于这些题都可以测独立迁移。',
                         '部分听力附加题有题面、文字稿和答案，但本单元无对应录音入口；读稿分析和听音训练分开判断。',
                         '导读内容可保留，部分口语练习仍缺录答、回听与重答；词库到主动表达的连接仍弱。'],
          'review_boundary':'当前主册可能继续更新；接入时按正文与关联材料指纹比较，已变化的目标单列，不把旧判定自动套到新内容。',
          'items':items}
    save('teaching-current-review.json',data)
    for filename,kind in [('teaching-current-review.json','teaching'),('current-learning-architecture.json','architecture')]:
        d=json.loads((R/filename).read_text(encoding='utf8'))
        lines=['# '+('具体教学复核' if kind=='teaching' else '学习架构复核'),'','日期：2026-09-19。固定快照审查；每项只对注明用途负责。','',
               '快照校验：`'+digest+'`','',str(d.get('scope','')),'',str(d.get('verdict','')),'']
        for i in d['items']:
            lines+=['## '+i['id']+' · '+i['title']+' · '+i['status'],'','用途：'+i.get('scope',''),'']
            for label,key in [('判断与问题','why' if kind=='teaching' else 'problem'),('可保留的部分','strength'),('学习影响','learning_impact'),('改善方案','improvement'),('验收标准','acceptance'),('修复核验','repair_description')]:
                v=i.get(key)
                if v: lines += [label+'：'+('；'.join(v) if isinstance(v,list) else str(v)),'']
            for e in i.get('evidence',[]):
                if isinstance(e,dict): lines+=['> '+e.get('quote','').replace('\n','\n> '),'','位置：`'+str(e.get('selector',e.get('selectors',[])))+'`','']
        (R/filename.replace('.json','.md')).write_text('\n'.join(lines),encoding='utf8')
    design=json.loads((R/'learning-redesign.json').read_text(encoding='utf8'))
    design['snapshot_update']='提案起草后，主册补入了具体练习与局部写作反馈。LA17、LA19现按限定用途合格；相关提案只补尚缺部分，不重复要求重建。以本次固定快照复核为基准。'
    design['implementation_boundary']['proposed']='六入口导航、目标卡、复习决策和整条独立练习路径仍为提案；具体题目入口和局部写作反馈已有部分落地，见各动作的快照进展。'
    for a in design['actions']:
        a['snapshot_progress']=('材料入口已补入，继续区分示范题、带提示题与真正未见题。' if a['id']=='RD-03' else
                               '旅游写作局部练习已补齐；补充口语的声音反馈仍需改进。' if a['id']=='RD-06' else
                               '该完整流程仍为提案；不以某个局部控件存在当作整条流程完成。')
    save('learning-redesign.json',design)
    md=R/'learning-redesign.md';text=md.read_text(encoding='utf8')
    marker='> 最终快照更新：'
    text='\n'.join(line for line in text.split('\n') if not line.startswith(marker))
    md.write_text(marker+design['snapshot_update']+'\n\n'+text,encoding='utf8')
    print(json.dumps(data['counts'],ensure_ascii=False))

if __name__=='__main__': main()
