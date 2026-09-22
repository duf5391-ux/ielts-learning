"""Record only the matching successful deployment and independently checked release."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, shutil, sys

P = Path(__file__).resolve().parent
R = P.parent
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')

m = read(R/'github-publication/manifest.json')
b = read(P/'build.json')
a = read(P/'action.json')
assert a['status'] == 'completed' and a['conclusion'] == 'success'
assert a['headSha'] == (P/'deployed-commit.txt').read_text(encoding='utf-8-sig').strip()
assert b['candidate'] == m['source_html_sha256']
assert sha256((P/'live-index.html').read_bytes()).hexdigest() == m['published_html_sha256']
checks = []
for name in ['verification.json', 'packed-verification.json', 'live-verification.json']:
    q = read(P/name)
    assert q['pass'] and q['source_sha256'] == b['candidate']
    checks.append({'path': 'ui-experience-20260922/'+name, 'checks': len(q['checks']) if isinstance(q['checks'], list) else q['checks']})
cnpath = Path(sys.argv[1]).resolve()
assert cnpath.parent.parent == (R/'research').resolve()
cn = read(cnpath)
assert cn['created_at'] > read(P/'installation.json')['installedAt']
resources = []
for row in cn['resources']:
    nodes = [n for n in row['nodes'] if n['country'] == 'CN']
    resources.append({'key': row['key'], 'passed': sum(not n['issues'] for n in nodes), 'returned': len(nodes),
                      'unallocated': row['unallocated_probe_count'],
                      'failures': [{'city': n['city'], 'asn': n['asn'], 'error': n.get('error'), 'issues': n['issues']} for n in nodes if n['issues']]})
assert len(resources) == 3
shutil.copy2(cnpath, P/'mainland-summary.json')
cncounts = '、'.join(f"{label}{r['passed']}/{r['returned']}" for label, r in zip(['首页','完整听力音频','机经音频'], resources))
limitations = '仅代表本次已分配节点。超时及未分配情况见原始证据；音频只检查前1024字节，不等于完整播放或全国长期可达。'
statuspath = R/'research/github-pages-migration-status.json'
prior = read(statuspath)
assert prior['source_html_sha256'] == b['baseline'], 'Publication status advanced: reconcile before overwriting.'
write(P/'prior-publication-status.json', prior)
status = {**prior, 'status':'succeeded', 'usability_status':'published_browser_verified_mainland_partial' if any(r['failures'] or r['unallocated'] for r in resources) else 'published_browser_verified_observed_mainland_nodes_passed',
          'source_commit':a['headSha'], 'workflow_run_id':a['databaseId'], 'workflow_url':a['url'],
          'updated_at':datetime.now(timezone.utc).isoformat(), 'source_html_sha256':m['source_html_sha256'],
          'published_html_sha256':m['published_html_sha256'], 'published_files':m['published_files'],
          'expanded_bytes':m['total_bytes'], 'save_fields':m['save_fields'], 'homepage_bytes':(P/'live-index.html').stat().st_size,
          'local_sync_workflow':'publish_github.ps1; matching commit Actions success, HTTPS fingerprint and browser interactions independently verified.',
          'verification':{'browser':{'passed':True,'targets':checks,'viewportStatesPerTarget':19},
                          'mainland':{'at':cn['created_at'],'evidence':cnpath.relative_to(R).as_posix(),'resources':resources,'limits':limitations}},
          'evidence':['research/product-ui-experience-delivery-20260922.md','ui-experience-20260922/installation.json','ui-experience-20260922/live-verification.json'],
          'previousVerification':'ui-experience-20260922/prior-publication-status.json'}
write(statuspath,status)
write(P/'release.json',status)

delivery = f'''# 前端、视觉与交互升级已上线 · 2026-09-22

正式册 `{m['source_html_sha256']}`，4092保存字段、236目录单元。部署提交 `{a['headSha']}`，Actions [{a['databaseId']}]({a['url']}) 成功。线上首页SHA `{m['published_html_sha256']}` 与发布包一致。

## 已实施

- 自测入口统一视觉，四科展示真实作答进度、开始／继续／查看结果；本次提交立即进入历次作答，重做时原轮次保留。
- 阅读和写作测试桌面题页／作答并排，手机可切换看题页／写答案；分区跳转定位原题，刷新保留输入。
- 写作目录增加草稿／修订状态、已开始／未开始筛选及可恢复空状态；专注题目时隐藏重复总标题。
- 资料页修复网格选择器，记录页备份前置；查词提示、焦点、弹窗与底栏避让统一。
- 背词支持1／2／3键，输入框与弹窗中不误触；复习空状态与到期提示更加明确。
- 六个一级入口及单词内背词／复习／句子／查词与历史保持；定制课程仍未启用。

Kimi App K3仅做指定截图与DOM的审查；任务返回 `executor=kimi-app, model=k3-agent`，没有使用Claw、没有新增Codex子agent。主线程独立核实建议、修改与发布，未照搬全部建议。审查及运行来源证据见 `ui-experience-20260922/kimi-verification.json`、`kimi-review.md`；使用的技能为[本机 cowork-kimi SKILL.md](C:/Users/Admin1/.codex/plugins/cache/personal/cowork-kimi/1.0.0+codex.20260919114234/skills/cowork-kimi/SKILL.md)。

## 验证和边界

候选、渐进加载发布包、实际HTTPS分别43项隔离浏览器检查、19个截图状态；包括填写、提交、当前结果／旧轮历史、重做、刷新、筛选、写稿、导出、收藏句子、查词、键盘和每日休息／继续／收工。桌面1440×1000与手机390×844无横向溢出和未捕获脚本异常。恢复导入和麦克风真机不属于本轮新增验证，沿用已有边界。

4092原字段完整保留且顺序一致，2470旧ID、111媒体节点保留。没有改答案、没有生成AI评分，测试产生的记录仅在隔离浏览器。候选失败探针曾发现整卡点击层遮住按钮和备份位置靠后，已修正后复验通过；失败候选未发布。

最新分层关系图含4389节点、4495关系，绑定本轮正式指纹，增加自测、稿件和备份读写关系。字段节点不是用户记录。前轮429地址可达的旧证据保留；本轮43检查不能宣称每道题、所有音频和所有控件审查完成。

大陆复测：{cncounts}。本轮上海移动首页及两条音频超时，北京移动与北京AS45090机经音频超时；每个资源均有3个请求节点未分配。{limitations} 证据：`{cnpath.relative_to(R).as_posix()}`。

维护文件和备份在 `ui-experience-20260922/`；源码同步原 `codex/source-and-ui-audit-20260921` 分支。个人记录无云同步；内容清洗和各平台实机的未完成项不因UI升级变成完成。
'''
(R/'research/product-ui-experience-delivery-20260922.md').write_text(delivery,encoding='utf8')
intro = f'''# 最新前端与交互状态（2026-09-22）

正式册 `{m['source_html_sha256']}`，4092字段、236目录单元；[原网站](https://duf5391-ux.github.io/ielts-learning/#tests) 已同步，Actions [{a['databaseId']}]({a['url']}) 成功。本轮增加自测真实进度／历次作答、双端题页与作答布局、写作状态筛选、前置备份、背词快捷键和弹窗避让。原六个一级栏目与单词内四分区保持。

Kimi App K3评审，根线程独自实施，没有Claw或新增Codex子agent。候选、发布包、HTTPS各43项检查和19个截图状态通过；4092字段、2470旧ID、111媒体保留。分层图4389节点／4495关系。维护见 [ui-experience-20260922/README.md](ui-experience-20260922/README.md)，完整证据与限制见[本轮交付](research/product-ui-experience-delivery-20260922.md)。

大陆本轮{cncounts}；音频为前1024字节响应，保留超时及未分配，不保证全国长期稳定。资料清洗、录音与四端真机、个人云同步仍按已有实际状态。下方旧版指纹和数字为历史。

'''
headers = {'README.md':intro,
           'AGENTS.md':f"2026-09-22 最新前端交互：正式册{b['candidate'][:8]}，4092字段、236单元，Actions {a['databaseId']} 成功。保留单词内四分区、六个一级栏目及原健康／每日模块。增加真实自测进度和历次作答、双端题答布局、写作状态筛选、前置备份和安全背词快捷键。维护与证据见 `ui-experience-20260922/README.md`、`research/product-ui-experience-delivery-20260922.md`。Kimi App K3评审，未用Claw／未开新Codex子agent。大陆本轮{cncounts}，具体失败与未分配必须保留。\n\n",
           'PUBLIC_DEPLOYMENT.md':f"最新已发布：{b['candidate'][:8]}正式册，4092字段、236单元，Actions {a['databaseId']}；首页SHA {m['published_html_sha256'][:8]}。本轮前端／交互与大陆复测见 research/product-ui-experience-delivery-20260922.md。下方旧数字为历史。\n\n"}
for name, header in headers.items():
    f=R/name
    f.write_text(header+f.read_text(encoding='utf8'),encoding='utf8')
source = R/'source-publication/source/README.md'
doc = source.read_text(encoding='utf8').replace(b['baseline'],b['candidate']).replace(b['baseline'][:8]+'…',b['candidate'][:8]+'…').replace(prior['source_commit'],a['headSha'])
doc = doc.replace('## 从这里开始','本轮前端与交互见 [自测、写作与双端UI](maintenance/ui-experience-20260922/README.md)、[本轮关系图](maintenance/ui-experience-20260922/interface-tensor.html)。候选、发布包、HTTPS各43项检查通过，Kimi App K3提供评审。\n\n## 从这里开始')
source.write_text(doc,encoding='utf8')
print(json.dumps({'source':b['candidate'],'action':a['databaseId'],'mainland':resources},ensure_ascii=False))
