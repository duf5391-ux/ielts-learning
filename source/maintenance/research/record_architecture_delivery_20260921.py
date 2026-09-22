from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
manifest=read(ROOT/'github-publication/manifest.json');health=read(ROOT/'architecture-repair-20260921/release-live.json');ui=read(ROOT/'architecture-repair-20260921/qa-live.json')
assert health['pass'] and ui['pass'];assert health['checks'][0]['detail']['sha256']==manifest['published_html_sha256']
path=ROOT/'research/github-pages-migration-status.json';old=read(path)
write(ROOT/'architecture-repair-20260921/prior-publication-status.json',old)
probes=read(ROOT/'research/github-publication-probes-20260921T141958.277540Z/summary-recovered.json')
now=datetime.now(timezone.utc).isoformat();commit='e66f73f133bb602ad17d0fbc29ad10996f6a3449';run=35611402372
status={**old,'source_commit':commit,'workflow_run_id':run,'workflow_url':f'https://github.com/duf5391-ux/ielts-learning/actions/runs/{run}',
 'updated_at':now,'source_html_sha256':manifest['source_html_sha256'],'published_html_sha256':manifest['published_html_sha256'],
 'published_files':manifest['published_files'],'expanded_bytes':manifest['total_bytes'],'save_fields':manifest['save_fields'],
 'usability_status':'published_browser_verified_four_mainland_nodes_passed_unallocated_networks_unknown',
 'verification':{'browser':{'passed':True,'evidence':['architecture-repair-20260921/release-live.json','architecture-repair-20260921/qa-live.json'],'scope':'architecture, old records, 3 reading units from two entrances, original resources, health and mobile word marks'},
 'mainland':{'evidence':'research/github-publication-probes-20260921T141958.277540Z/summary-recovered.json','resources':[{'key':r['key'],'nodes':len([n for n in r['nodes'] if n['country']=='CN']),'passed':sum(n['response_checks_passed'] for n in r['nodes'] if n['country']=='CN')} for r in probes['resources']],
 'limits':'Only Shanghai Unicom, Nanning Unicom and two cloud-network nodes allocated; other requested mainland networks unknown. API retrieval TLS failures preserved and recovered using same measurement IDs. Node measurements span deployment, not source-version verification.'}},
 'previousVerification':'architecture-repair-20260921/prior-publication-status.json'}
write(path,status)
p=ROOT/'architecture-repair-20260921/installation.json';d=read(p);d.update(status='published',commit=commit,workflowRun=run,liveVerifiedAt=now);write(p,d)
header=f'''# 2026-09-21 第一轮架构修正与三份新资料精读已上线

正式册 SHA-256：`{manifest['source_html_sha256']}`，3371字段、227单元。单词表、句子本、写作工作台归学习；工作台保留原始资料、记录备份和资料接入进度；定制课程只留待开放窗口。修复 Task 1/2 分类返回、背景/词汇归属、资源索引混排和自选清单命名。新增三份同源精读，入口显示编辑难度、参考置信度和来源。

原429地址逐一重开通过；桌面/手机主要入口、旧记录恢复、三份双入口精读和健康流程通过本地及线上检查。Actions [{run}](https://github.com/duf5391-ux/ielts-learning/actions/runs/{run})成功，线上首页SHA与发布包一致。大陆本轮分配到4节点，首页及两条音频均4/4；其余请求网络未分配，不能推广为全国可用。

本轮不代表全站修完：词卡收藏承接、句子来源、写作新题覆盖、口语录音衔接等仍待修。1063来源已建立关系图；1445阅读切片为原料，不是1445份已编写课程；两组新听力待原音核查，未发布测试。详见[本轮交付与剩余清单](research/architecture-content-delivery-20260921.md)。下方为历史状态。

'''
p=ROOT/'README.md';p.write_text(header+p.read_text(encoding='utf8'),encoding='utf8')
p=ROOT/'AGENTS.md';text=p.read_text(encoding='utf8');p.write_text('# 最新架构状态（2026-09-21）\n\n'+header.split('\n\n',1)[1]+'\n'+text,encoding='utf8')
p=ROOT/'PUBLIC_DEPLOYMENT.md';text=p.read_text(encoding='utf8');text='当前最新已发布：83346245 正式册，3371字段、227单元，Actions 35611402372；首页SHA 8c77a35f。验证边界见 research/architecture-content-delivery-20260921.md。以下旧数字以此为准。\n\n'+text;p.write_text(text,encoding='utf8')
print(json.dumps({'published':commit,'workflow':run,'liveFingerprintMatches':True}))
