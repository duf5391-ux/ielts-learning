from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json, shutil
P=Path(__file__).resolve().parent;R=P.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
m=read(R/'github-publication/manifest.json');action=read(P/'action.json')
assert action['headSha']=='55d94a75eb3ad5174bf9234a2ed9a86b8db49097' and action['conclusion']=='success'
assert sha256((P/'live-index.html').read_bytes()).hexdigest()==m['published_html_sha256']
for name in ['verification.json','packed-verification.json','live-verification.json']:
    q=read(P/name);assert q['pass'] and q['source_sha256']==m['source_html_sha256']
cnpath=R/'research/github-publication-probes-20260922T024319.000006Z/summary.json';cn=read(cnpath)
resources=[]
for r in cn['resources']:
    nodes=[n for n in r['nodes'] if n['country']=='CN']
    resources.append({'key':r['key'],'passed':sum(not n['issues'] for n in nodes),'returned':len(nodes),'unallocated':r['unallocated_probe_count'],'failures':[{'city':n['city'],'asn':n['asn'],'error':n.get('error')} for n in nodes if n['issues']]})
shutil.copy2(cnpath,P/'mainland-summary.json')
statuspath=R/'research/github-pages-migration-status.json';prior=read(statuspath);write(P/'prior-publication-status.json',prior)
status={**prior,'status':'succeeded','usability_status':'published_browser_verified_mainland_partial','source_commit':action['headSha'],'workflow_run_id':action['databaseId'],'workflow_url':action['url'],'updated_at':datetime.now(timezone.utc).isoformat(),'source_html_sha256':m['source_html_sha256'],'published_html_sha256':m['published_html_sha256'],'published_files':m['published_files'],'expanded_bytes':m['total_bytes'],'save_fields':m['save_fields'],'homepage_bytes':(P/'live-index.html').stat().st_size,'local_sync_workflow':'publish_github.ps1 pushed successfully; Actions status request returned a transient EOF; independent gh run view confirmed matching commit deployed successfully.', 'verification':{'browser':{'passed':True,'evidence':['ui-polish-20260922/verification.json','ui-polish-20260922/packed-verification.json','ui-polish-20260922/live-verification.json'],'checksPerTarget':56,'viewportStatesPerTarget':24,'legacyRoutes':429,'legacyBinding':'ui-polish-20260922/route-binding.json'},'mainland':{'at':cn['created_at'],'evidence':str(cnpath.relative_to(R)).replace('\\','/'),'resources':resources,'limits':'大陆首页7/9、两条音频分别8/9。北京与上海移动首页超时，上海移动完整听力、武汉电信机经音频超时；天津联通未分配。只代表当时已分配节点，音频为前1024字节响应，不等于完整播放。'}},'evidence':['research/product-word-workspace-delivery-20260922.md','ui-polish-20260922/installation.json','ui-polish-20260922/live-verification.json'],'previousVerification':'ui-polish-20260922/prior-publication-status.json'}
write(statuspath,status);write(P/'release.json',status)
text=f'''# 单词栏目整合、历史与双端 UI 已上线 · 2026-09-22

正式页 `{m['source_html_sha256']}`；4092保存字段，原4091完整保留，236目录单元。提交 `{action['headSha']}`，Actions [{action['databaseId']}]({action['url']}) 成功。线上首页 `{m['published_html_sha256']}` 与发布包一致。

单词的一级入口统一，进入即出现背词卡，只需按需要选择话题。内部为背单词／复习／句子／查词与历史；旧复习、句子、词卡等深链继续可用。学习库、专项练习、自测、写作训练、资料与记录为其余一级入口。桌面与手机共同调整字阶、卡片、图标、当前态与触控布局。

复习自动承接查过或学过的词，收藏只标重点。直接点不会／模糊／会，成功保存后进入下一词；失败保留当前词。旧已标记词进入复习但不补造历史日期；新学写N，不由单次自评自动写K。看释义后刷新仍记得短期提示曝光，不算无提示成功。拼写自测保存具体输入与结果，学习记录支持按类型及词语查询。

句子移入单词栏目，沿用原收藏、修改、原句来源与保存字段。定制课程仍待开放；本轮没有把未审原料冒称新课程。

## 验证

- 本地候选、渐进加载发布包、实际HTTPS，各56项隔离检查；24个桌面/手机页面状态，无未捕获脚本异常或横向溢出。
- 包括直接背词、换话题、刷新续学、提示后刷新、保存失败回退、未收藏查询词入队、回忆、拼写错答保护、真实历史、旧词句记录保留、手机评分按钮避开底栏、更多抽屉、每日休息/继续/收工。
- 原429地址逐一重开通过。探针执行于7b0e候选；最终3ba0仅多一个不为无日期学习词补造查询事件的保护，`route-binding.json` 用精确回退SHA证明路由和页面未变。可达不等同于每道题内容与所有控件审查通过。
- 2460旧ID、111媒体节点不变；新增1个背词状态字段。关系图 `interface-tensor.html` 含4383节点、4395关系，标出入口／内容／活动／保存归属，不存个人记录。
- 发布脚本推送完成后，读取Actions状态一次EOF；重新查询对应提交确认成功，没有重复推送。

本轮大陆首页7/9、完整听力8/9、机经音频8/9。北京与上海移动首页、上海移动完整听力、武汉电信机经音频TCP连接超时；天津联通未分配。证据：`github-publication-probes-20260922T024319.000006Z/`。这是当时节点响应，音频只检查前1024字节，不能承诺全国长期可达或完整播放。

## 维护和剩余边界

`ui-polish-20260922/README.md`、构建器、独立JS/CSS、探针与回退文件共同维护；备份在其 `formal-backup/`。逐文件源码快照继续推送原 `codex/source-and-ui-audit-20260921` 分支。

桌面1440×1000与手机390×844为浏览器视口验证，真人手机麦克风、软键盘、设备安装仍有既有未测项。个人记录无云同步。1063原料来源、1445阅读切片及待核听力的原有审核状态不因UI改版升级；本轮不声称所有资料加工和全站内容审计结束。
'''
(R/'research/product-word-workspace-delivery-20260922.md').write_text(text,encoding='utf8')
intro=f'''# 最新单词与 UI 状态（2026-09-22）

正式册 SHA-256：`{m['source_html_sha256']}`，4092保存字段、236目录单元。用户最新要求优先：句子、复习、历史都归入单词；单词首页直接背词，最多选话题，查过与学过的词自动进入复习，无需先收藏。单词内含背单词／复习／句子／查词与历史；保留旧深链和记录。桌面与手机共同优化卡片、图标、字阶与布局。

[正式网址](https://duf5391-ux.github.io/ielts-learning/#vocabulary-review) 已更新，Actions [{action['databaseId']}]({action['url']}) 成功。候选、发布包及线上各56项检查，24个双端页面状态通过；原429路由重开通过且绑定最终差异。新增真实学习／拼写历史、保存失败不跳词、提示曝光保护。完整证据与边界见[本轮交付](research/product-word-workspace-delivery-20260922.md)，维护在 `ui-polish-20260922/`。

大陆本轮首页7/9、两条音频各8/9，保留节点超时和未分配情况；音频为前1024字节响应。未完成原料加工、真机验证和个人云同步不因UI改版变成完成。下方八个一级入口及“句子独立”等均为历史。

'''
for file,header in [('README.md',intro),('AGENTS.md','2026-09-22 最新单词整合：正式册3ba0baa5，4092字段、236单元，Actions35680317051成功。用户最新要求覆盖旧八入口：单词内统一背单词／复习／句子／查词与历史，进入直接背词，查过或学过自动进复习，收藏只标重点。维护与验证见 `ui-polish-20260922/README.md`、`research/product-word-workspace-delivery-20260922.md`。保留4091旧字段、旧ID、媒体及每日健康模块。大陆本轮首页7/9、两音频各8/9，节点失败和未分配必须保留。\n\n'),('PUBLIC_DEPLOYMENT.md',f'最新已发布：3ba0baa5正式册，4092字段、236单元，Actions {action["databaseId"]}；首页SHA4e3d8f43。本轮单词整合、双端UI和大陆探测见 research/product-word-workspace-delivery-20260922.md。下方旧数字为历史。\n\n')]:
    f=R/file;f.write_text(header+f.read_text(encoding='utf8'),encoding='utf8')
f=R/'source-publication/source/README.md';doc=f.read_text(encoding='utf8').replace('e2b9e12e58c8f03de4b43b8ec6bdb1b81a15130ddceb6b80ea5fff6a3d742075',m['source_html_sha256']).replace('e2b9e12e…','3ba0baa5…').replace('c84dab611f943c9e24b9a595321462392c96ef4a',action['headSha']).replace('4091个保存字段','4092个保存字段');doc=doc.replace('## 从这里开始','最新版单词内统一背词、复习、句子和历史。进入直接背词，查过或学过自动接续复习。新实现与验证见 [UI增量](maintenance/ui-polish-20260922/README.md)，[最新分层关系图](maintenance/ui-polish-20260922/interface-tensor.html)。\n\n## 从这里开始');f.write_text(doc,encoding='utf8')
print(json.dumps({'source':m['source_html_sha256'],'action':action['databaseId'],'mainland':resources},ensure_ascii=False))
