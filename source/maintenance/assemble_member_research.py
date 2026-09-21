"""Combine public member-area evidence and one actual free product walkthrough."""
from pathlib import Path
import json
from copy import deepcopy

ROOT=Path(__file__).resolve().parent
R=ROOT/'research'

def write(name,d): (R/name).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')

def normalize_course(node,legend):
    if isinstance(node,list): return [normalize_course(x,legend) for x in node]
    if not isinstance(node,dict): return node
    d={k:normalize_course(v,legend) for k,v in node.items()}
    if 'evidence_level' in d:
        d['evidence_level']=legend.get(d['evidence_level'],d['evidence_level'])
        if 'BC01' in d.get('source_ids',[]) or d.get('id')=='BC01':
            d['evidence_level']='官方手册检索文字及截图文字说明；PDF未成功获取，不算已目视截图'
    return d

def main():
    groups={k:json.loads((R/f'member-{k}.json').read_text(encoding='utf8')) for k in ['courses','vocabulary','mocks','road']}
    products=[];sources=[]
    for kind,d in groups.items():
        for item in d['products']:
            p=normalize_course(deepcopy(item),d.get('evidence_legend',{})) if kind=='courses' else deepcopy(item)
            p['category']={'courses':'雅思课程会员','vocabulary':'词汇增值功能','mocks':'模考与评测','road':'实际免费体验'}[kind]
            p['proofSummary']='已实际完成样例作答、批改、重做与答案查看' if kind=='road' else '依据官方操作资料与公开样本还原；未登录付费账户'
            if p['id']=='bc-ready-premium':
                p['coverage']='已读取官方手册检索文字，可还原首页与历史字段；PDF下载403，未目视手册截图。课程细分结合官方说明。'
            p['reportFile']=f'member-{kind}.md' if kind!='road' else '会员区补查与设计修订.md'
            products.append(p)
        sources.extend(d.get('sources',[]))
    # Source IDs are local to each report; attach that report's complete mapping to each product.
    for kind,d in groups.items():
        sm={s.get('id'):s for s in d.get('sources',[]) if s.get('id')}
        for p in products:
            if p['id'] not in {i['id'] for i in d['products']}: continue
            p['sourceIndex']=normalize_course(list(sm.values()),d.get('evidence_legend',{})) if kind=='courses' else list(sm.values())
    urls={s.get('url') for s in sources if s.get('url')}
    gallery=list(groups['road']['screenshots'])
    for a in groups['mocks'].get('evidence_assets',[]):
        gallery.append({'file':'member-mocks-evidence/'+a['file'],'title':a.get('product','')+' · '+a.get('observed',''),
                        'note':'官方公开内部界面／报告样本；非本次账户实测','sourcePage':a.get('url','')})
    findings=[
      {'title':'会员区是学、练、测和历史之间的连接','text':'IELTS Ready的手册导航、Magoosh的官方练习计划、TestGlider的复查流程都提供了具体连接。可以先采用清楚的静态入口与手工选路，不必等待自动排课。','sources':['https://www.britishcouncil.hk/ielts-ready-premium-user-guide-2026','https://blog.testglider.com/how-to-use-testglider-for-a-higher-ielts-band-score/']},
      {'title':'答案、评语、改写和再练是不同产物','text':'Road实际显示对错和参考答案；IOT/Flex公开样本还展示分项评语、转写或修改。报告字段丰富不证明评分准确；生成的改写也不能算本人会写。','sources':['https://rtiac.clarityenglish.com/#prefix=td','https://ieltsflex.com/flex-check/']},
      {'title':'词汇会员可能购买额度或内容，未必改变学习算法','text':'Quizlet不同订阅存在额度差异，墨墨付费词量与复习次数是两回事。不背的具体训练开关可查，会员打包权限仍需按产品内套餐核对。','sources':['https://help.quizlet.com/hc/en-au/articles/360041181691-Subscribing-to-Quizlet','https://www.maimemo.com/help30','https://api.maimemo.com/shop']},
      {'title':'练习完成与跨日掌握必须分开','text':'拼写训练有明确纠错和重试规则，间隔复习又是另一流程。借鉴状态和错误分支，不能把单轮全对直接映射成雅思技能掌握。','sources':['https://help.quizlet.com/hc/en-us/articles/360030645752-Studying-with-Spell-mode','https://help.quizlet.com/hc/en-us/articles/48324742264077-Studying-with-Spaced-Repetition']}
    ]
    changes=[
      {'id':'MR-01','title':'首页给一个可执行目标','maps_to':['今天学什么','记录与资料'],'proposal':'首页显示今天可用时间、一个具体卡点和主任务入口；用一句话说明为何推荐，并允许手工换任务。','acceptance':'学习者不必浏览整册便能开始；完成后知道下一步。','references':['bc-ready-premium','magoosh-ielts','TG-IELTS']},
      {'id':'MR-02','title':'统一最小教学闭环','maps_to':['专项学习'],'proposal':'每个任务明确本次目标、输入材料、题目、首答、反馈依据、一处修订和下一次新题；不要求所有背景选读都强制作答。','acceptance':'一个新用户可以不靠口头解释完成流程，且知道每步产物是什么。','references':['road-live','e2-ielts']},
      {'id':'MR-03','title':'报告保留原回答和证据','maps_to':['记录与资料','专项学习'],'proposal':'记录题号、原答、是否看稿/范例、对错或待判、证据位置、修订理由、重答；AI建议单列来源与不确定性。','acceptance':'看参考答案不覆盖首答；至少能追溯一次修改为什么成立。','references':['road-live','IOT','FLEX']},
      {'id':'MR-04','title':'词卡分清识别、拼写与主动表达','maps_to':['背景与表达','复习与重教'],'proposal':'同一词条标明本次具体义项及考查方式；拼错定位字母或音形，语境错回例句，再安排无提示使用。','acceptance':'答错后有一个对应操作；选择题通过不自动标记会拼写、会说或会写。','references':['quizlet-plus','bbdc-membership','maimemo-paid']},
      {'id':'MR-05','title':'复习记录支持选择下一项','maps_to':['复习与重教'],'proposal':'区分未学、本轮需练、有提示通过、无提示通过和待隔日检查；到期与新学分开显示，难项先重教再重复。','acceptance':'用户能看懂为何某项今天出现，能减少负荷或退出已稳定任务。','references':['quizlet-plus','memrise-pro','maimemo-paid']},
      {'id':'MR-06','title':'练习模式与模考模式各自交代支持条件','maps_to':['独立练习与模考'],'proposal':'练习可查材料、暂停与重试；模考声明计时、提示和录音条件。无配套音频的材料标为文字稿分析。','acceptance':'同题看过答案后的结果与首次无提示结果分开；缺关键素材时不伪装完整考试。','references':['road-live','BRO','TG-IELTS']}
    ]
    result={'title':'登录后与付费区内部结构补查','date':'2026-09-19',
            'method':'用户确认暂无账号，本轮使用官方免费体验、操作手册、开发者截图、公开报告样本与可见样课。未购买、注册或绕过权限。',
            'counts':{'products':len(products),'uniqueSourceUrls':len(urls),'liveWalkthroughProducts':1,'galleryImages':len(gallery)},
            'findings':findings,'designUpdates':changes,'products':products,'gallery':gallery,
            'limitations':['免费体验与付费账户不是同一权限；只对实际完成的步骤称实测。','官方截图反映其发布版本，历史额度不当作当前购买依据。','BC手册仅读取检索文字，未成功获取PDF或目视手册截图。','Cambridge One通用平台功能不自动等于IELTS产品已配置。']}
    write('member-research.json',result)
    lines=['# 会员区补查与设计修订','','日期：2026-09-19。用户确认暂无账号，本轮以免费内部体验和官方资料补查。','',
           f'覆盖{len(products)}个产品与版本，{len(urls)}个不同来源URL。1个平台实际走通部分练习流程；其余按官方内页、手册、样课和演示还原。','',
           '## 实际走通的内部流程','','Road to IELTS：首页 → 阅读专项 → 第1组简答 → 输入研究答案 → 批改 → 重做 → 看答案 → 进度区。结果能区分正确、错误、漏答；个人历史区明确需要账号。','',
           '[官方免费体验](https://rtiac.clarityenglish.com/#prefix=td) · [首页截图](evidence/member-area/road-home.png) · [批改截图](evidence/member-area/road-feedback.png) · [进度门槛](evidence/member-area/road-progress-gate.png)','']
    for f in findings: lines+=['## '+f['title'],'',f['text'],'','来源：'+' · '.join(f'[官方依据{i+1}]({url})' for i,url in enumerate(f['sources'])),'']
    lines+=['## 逐产品详细报告','','[雅思课程会员](member-courses.md) · [词汇增值功能](member-vocabulary.md) · [模考与评测](member-mocks.md)','',
            '## 对原设计的具体补充','','以下是设计提案，尚未作为新功能实现；本轮不重建教学正文。','']
    for c in changes: lines+=['### '+c['id']+' '+c['title'],'',c['proposal'],'','验收：'+c['acceptance'],'','对应入口：'+'、'.join(c['maps_to']),'']
    lines+=['## 证据边界','']+[f'- {x}' for x in result['limitations']]
    (R/'会员区补查与设计修订.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps(result['counts'],ensure_ascii=False))

if __name__=='__main__': main()
