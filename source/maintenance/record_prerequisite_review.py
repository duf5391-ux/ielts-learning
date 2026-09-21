"""Version-specific content addendum; previous full audits remain historical snapshots."""
from pathlib import Path
from bs4 import BeautifulSoup
import json, hashlib
from integrate_prerequisites import ROOT,BOOK,OUT,MAIN,sha,LISTENING

def main():
    text=MAIN.read_text(encoding='utf8');s=BeautifulSoup(text,'html.parser')
    expected=json.loads((ROOT/'research/prerequisite-repair-20260920.json').read_text(encoding='utf8'))
    assert expected['phase']=='written' and sha(text)==expected['afterSHA256']
    cases=[
      ('audit-045','#topic-education','达标','教育背景与具体运用','补课堂情境、教育机会与支持差异练习；接 C21 小学学习/游戏原题、两问审题、理由段与同题7.5分评语。Davies 保留为另行阅读。'),
      ('audit-046','#topic-work','达标','工作背景与具体运用','分别练地点/时间灵活、收入/稳定性与岗位条件；用 Monika 官方样本的解释链连接工作压力、加班与家庭生活，并提供具体安排参考。'),
      ('audit-047','#topic-technology','达标','实施条件与概念辨析','AI Q31/G、Q33/C 对应基础设施与人才；原创社区预约任务区分 access/skills/privacy/security，并给两句有条件的表达。'),
      ('audit-067','[data-enrichment="vocab-strike-balance"]','达标','搭配结构与应用','当前正文已使用 imparting knowledge / encouraging students to think independently；实际结构与同源释义相符，保留已有修订。'),
      ('audit-069','[data-enrichment="vocab-make-progress"]','达标','搭配意义与例子身份','真题题卡和本地原创人物经历分开标明；用比赛变化说明进步，不把题卡身份当成高分作答身份。'),
      ('audit-070','[data-enrichment="vocab-draw-distinction"]','达标','搭配与概念区别','当前正文已改为 being aware of health advice and following it，另有 explaining the difference 的具体参考。'),
      ('audit-083','[data-enrichment="speaking_part1_natural_answers"]','达标','口语内容流程与静态集成','一问首录、回听、时间点定位一处、同题再录；两遍不同录音ID，保留原冻结首稿与修订字段，转写先折叠。未实测麦克风。'),
      ('audit-084','[data-enrichment="speaking_part3_explain_compare"]','达标','口语内容流程与静态集成','地位观点加追问，检查理由和范围，只修一处再录；题页广告问题与本次片段覆盖范围明确分开。未实测麦克风。'),
      ('audit-118','#usage-05','达标','因果连接词的上下文','补原文相邻两句、原因/结果辨认及可核对反馈，避免把附近出现的洪水直接当作当前句的原因。'),
      ('audit-135','#topical-vocabulary','存疑','完整真实语境教学与 IELTS 总体频率证据','1000张卡均可进入主动造句，原句/义项→表达→核对→修订→隔天换情境的记录已补齐，解决旧TC-135的主动使用路径缺口。仍不把1000个词条说成1000个逐一核实的真题例句，也不外推全考试频率。'),
    ]
    items=[]
    for ident,selector,status,scope,reason in cases:
        node=s.select_one(selector);assert node is not None
        plain=node.get_text(' ',strip=True)
        if ident=='audit-067':assert 'imparting knowledge' in plain
        if ident=='audit-069':assert '原创参考作答' in plain
        if ident=='audit-070':assert 'being aware of health advice' in plain
        items.append({'id':ident,'selector':selector,'status':status,'scope':scope,'reason':reason,'sha256':sha(str(node))})
    for no,(_,label,qs) in LISTENING.items():
        node=s.find(id=f'supplement-audit-{no:03}')
        items.append({'id':f'TC-{no:03}','status':'达标','scope':'原课程保留；新增正式听力的同源材料与静态流程','reason':label+'：本地原音、原题、逐题作答、独立记录、默认折叠转写与答案；不是把另一段课堂音频当同题原音。未逐秒重听或现场播放。','sha256':sha(str(node))})
    frequency=BOOK/'词频与原文证据.html'
    items.append({'id':'deep-244','status':'达标','scope':'既有语料内词频与原件回查','reason':'27篇均补发布原件入口：23篇本地PDF及物理页、4篇网页原入口和已有正文快照；数值和统计正文未改，不认证总体IELTS高频。','sha256':sha(frequency.read_bytes())})
    report={'date':'2026-09-20','reviewer':'主任务直接复核；未追加实施 agent','mainSHA256':sha(text),'reviewScope':'15个具体缺口/整改点，不是整册292项全量重审','summary':{'reviewed':len(items),'passed':sum(i['status']=='达标' for i in items),'uncertain':sum(i['status']=='存疑' for i in items),'failed':sum(i['status']=='不达标' for i in items)},'items':items,'limits':['浏览器策略拒绝打开本地主学习页，本轮没有完整浏览器联调，不通过其他渠道绕过。','Energy Control 的8项纯逻辑及隔离DOM测试通过；不等同在实际学习册完成现场测试。','1000条词库的逐条真实语境与整场考试频率不在已认证范围。'],'later':['保留工作区；完整四科模拟考与单科完整测试另设入口。','听说读写教学/练习与纯测试分开，话题、小练、集成学习组织及界面再设计另行处理。']}
    (ROOT/'research/prerequisite-content-review-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report['summary'],ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf8');main()
