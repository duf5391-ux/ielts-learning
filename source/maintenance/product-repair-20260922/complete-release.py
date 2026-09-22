"""Record the verified release without losing previous publication evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
probe_path=Path(sys.argv[1])
if not probe_path.is_absolute():probe_path=ROOT/probe_path
probe=read(probe_path)
probe_relative=probe_path.relative_to(ROOT).as_posix()
deployment=read(HERE/'deployment.json')
build=read(HERE/'publication-build.json')
for name in ['release-live.json','frontend/qa-live.json','frontend/qa-packed.json']:
    q=read(HERE/name)
    assert q['pass'] and q['source_html_sha256']==build['source_html_sha256']
assert deployment['conclusion']=='success' and deployment['headSha']==build['commit']
resources=[]
for r in probe['resources']:
    cn=[n for n in r['nodes'] if n['country']=='CN']
    resources.append(dict(key=r['key'],nodes=len(cn),passed=sum(n['response_checks_passed'] for n in cn),
                          measurement_id=r['measurement_id'],client_error=r.get('client_error')))
assert len(resources)==3 and all(r['nodes']>0 for r in resources),'No current mainland evidence'
all_cn=all(r['nodes']==r['passed'] and not r['client_error'] for r in resources)
network_text='、'.join(f"{r['key']} {r['passed']}/{r['nodes']}" for r in resources)
limits='本轮实际分配节点的当时结果；其余请求网络未分配或未证实，不代表全国、所有运营商或长期可用。音频仅检查前1024字节响应，不等于完整播放。'
status=read(HERE/'prior-publication-status.json')
status.update(dict(status='succeeded',usability_status='published_browser_verified_mainland_allocated_nodes_passed' if all_cn else 'published_browser_verified_mainland_partial',
    source_commit=deployment['headSha'],workflow_run_id=deployment['databaseId'],workflow_url=deployment['url'],updated_at=datetime.now(timezone.utc).isoformat(),
    source_html_sha256=build['source_html_sha256'],published_html_sha256=build['published_html_sha256'],published_files=build['published_files'],
    expanded_bytes=build['bytes'],save_fields=4091,learning_units=236,homepage_bytes=159012,progressive_loading=True,
    previousVerification='product-repair-20260922/prior-publication-status.json',
    local_sync_workflow='publish_github.ps1 prepared and committed; initial push HTTP408, confirmed old remote, retried the same commit successfully; matching Actions success and HTTPS exact hashes verified',
    verification=dict(browser=dict(passed=True,evidence=['product-repair-20260922/frontend/qa-live.json','product-repair-20260922/release-live.json'],scope='Phone navigation, word search/favorite restoration, cross-mode search return, 32 writing tasks and draft restoration, daily health and dock geometry; isolated records'),
                      mainland=dict(evidence=probe_relative,resources=resources,limits=limits)),
    evidence=['research/product-redesign-delivery-20260922.md','product-repair-20260922/release-acceptance.json','product-repair-20260922/frontend/qa-packed.json',probe_relative],
    next='Real device microphone/keyboard and four-platform installation checks remain separate. No personal cloud sync or nationwide access claim.'))
write(ROOT/'research/github-pages-migration-status.json',status)
task=read(HERE/'task-state.json')
task['kimi_tasks'].append(dict(task_id='msg-66269e08-36d4-4f88-99b4-b718045c96ae',status='completed',runtime_model='k3-agent',result='research/product-entry-visual-review-kimi-20260922.md'))
task.update(publication='Installed, packed/browser verified, same-site Actions succeeded and HTTPS verified',source_html_sha256=build['source_html_sha256'],workflow_url=deployment['url'],mainland_evidence=probe_relative)
write(HERE/'task-state.json',task)
report=ROOT/'research/product-redesign-delivery-20260922.md'
body=report.read_text(encoding='utf8').replace('当前：候选完成，等待最终验收与同站发布。候选 SHA-256','当前：已安装并同步原网址，发布包与正式HTTPS验收通过。正式册 SHA-256').replace('13项可靠性组合检查和9项写作检查','13项可靠性组合检查和10项最终写作检查')
body=body[:body.index('## 发布记录')]+f'''## 发布记录

- 正式网址：https://duf5391-ux.github.io/ielts-learning/ 。
- 提交 `{deployment['headSha']}`；[Actions {deployment['databaseId']}]({deployment['url']}) 成功。首轮push HTTP408后先确认远端仍旧版，再推送同一提交恢复；未重新生成或替换验收源。
- 正式册 `{build['source_html_sha256']}`；线上首页 `{build['published_html_sha256']}`，159012字节；渐进清单与发布包一致，4091字段完整组装。1093文件、261890674字节。
- `product-repair-20260922/frontend/qa-packed.json` 和 `qa-live.json` 各6组代表性流程通过，0页面脚本异常：手机导航/更多、词卡首屏检索收藏与刷新、跨范围搜索返回、32题写作目录到首稿及刷新、学习/休息/继续/收工和底栏无重叠。
- `product-repair-20260922/release-live.json` 核对Actions、线上首页和渐进清单SHA，两个关键音频206/MP3/ID3及Range正确。不是完整音频播放测试。
- 本轮大陆节点：{network_text}。证据 `{probe_relative}`。{limits}
- 原正式册及安装恢复记录：`product-repair-20260922/formal-backup/`；当前状态 `research/github-pages-migration-status.json`，之前的线上证据已保存为 `product-repair-20260922/prior-publication-status.json`。
'''
report.write_text(body,encoding='utf8')
prefix=f'''# 最新产品状态（2026-09-22）

正式册 SHA-256：`{build['source_html_sha256']}`，4091保存字段、236目录单元；原3371字段/227单元与旧地址保留。用户最新明确要求常用内容独立、材料容易找到，已由Kimi K3负责入口设计与截图复审，前端和写作分工完成。此处优先于下方“工具归学习”及“保持旧导航”的历史描述。

当前8入口：学习、单词、复习、句子、练习、测试、写作工作台、工作台。手机底栏学习/单词/复习/句子/更多，更多平铺4项；学习/练习为分组内容行及直接标题链接，搜索可跨学习/练习，返回保留查询和位置。32道完整写作题可检索直接开写；词卡收藏承接、句子真实来源返回、口语进度/逐次本地录音恢复已修。

[正式网址](https://duf5391-ux.github.io/ielts-learning/)已更新，Actions [{deployment['databaseId']}]({deployment['url']}) 成功。发布包与HTTPS代表性手机流程通过，线上首页SHA `0bab2fa197699cb83087528a3769e4be81035420b70933eedcf56b1707a95336`。本轮大陆：{network_text}；{limits}

维护及验证边界见[本轮交付](research/product-redesign-delivery-20260922.md)，增量与备份在 `product-repair-20260922/`。旧429地址只证明可达，不等于逐题课程审查。真人手机麦克风、软键盘与四端安装仍未验证；录音不进整册JSON，个人记录无云同步。1063来源关系图与1445原料切片不等于已编写课程，两组待核听力未发布。下方为历史状态。

'''
for name in ['README.md','AGENTS.md']:
    p=ROOT/name;p.write_text(prefix+p.read_text(encoding='utf8'),encoding='utf8')
p=ROOT/'PUBLIC_DEPLOYMENT.md';old=p.read_text(encoding='utf8')
p.write_text(f"当前最新已发布：e2b9e12e 正式册，4091字段、236单元，Actions {deployment['databaseId']}；首页SHA 0bab2fa1。发布包、HTTPS与本轮大陆证据见 research/product-redesign-delivery-20260922.md。下方旧数字为历史。\n\n"+old,encoding='utf8')
print(json.dumps({'status':'recorded','workflow':deployment['url'],'mainland':resources},ensure_ascii=False))
