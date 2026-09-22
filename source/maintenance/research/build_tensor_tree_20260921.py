"""Evidence-indexed, typed sparse adjacency tensor and layered 3D inspector."""
from pathlib import Path
from collections import Counter
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/tensor-tree-20260921'
OUT.mkdir(exist_ok=True)
PROBE = ROOT / 'research/ui-route-probe-20260921'
def read(path): return json.loads(path.read_text(encoding='utf-8'))
mapping = read(ROOT / 'research/interface-map-20260921/interface-map.json')
inventory = read(PROBE / 'inventory.json')
baseline = ROOT / 'ui-repair-20260921/baseline.html'
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == mapping['baseline_sha256']
soup = BeautifulSoup(baseline.read_text(encoding='utf-8'), 'html.parser')
nodes, edges = {}, {}
def node(id, label, kind, group='global', **metadata):
    if id not in nodes: nodes[id] = dict(id=id, label=label, kind=kind, group=group, **metadata)
    return id
def edge(a, b, relation, evidence):
    if a == b: return
    key = (a, b, relation)
    if key not in edges: edges[key] = dict(source=a, target=b, relation=relation, evidence=evidence)
def rid(x): return 'route:' + x.lstrip('#')
node('root', 'IELTS 当前系统', 'root')
panels = {x['id']:x for x in inventory['panels']}
units = {x['id']:x for x in inventory['units']}
ledger = {x['requested']: x for x in mapping['ledger']}
for id, row in ledger.items():
    panel = panels.get(row['panel'], {})
    owner = units.get(id, {}).get('mode', panel.get('owner', 'unknown'))
    node(rid(id), row['title'] or id, 'route', owner, route='#'+id,
         panel=row['panel'], actual=row['actual'], unit=units.get(id),
         routeType='panel' if id in panels else 'unit' if id in units else 'category' if '分类路由' in row['from'] else 'anchor',
         probe='ui-route-probe-20260921/full-content/'+row['file'],
         coverage='逐页打开与DOM读取；全部操作未认证',
         controls=row['controls'], visibleControls=row['visibleControls'], savedFields=row['savedFields'])

def nearest(element, include_self=False):
    for p in ([element] if include_self else []) + list(element.parents):
        if p.get('id') in ledger: return rid(p['id'])
    return 'root'
for id, row in ledger.items():
    el = soup.find(id=id)
    parent = nearest(el) if el else 'root'
    edge(parent, rid(id), 'contains', '正式HTML最近已建模祖先；无祖先则网站根')
    if row['actual'].lstrip('#') in ledger and row['actual'] != '#'+id:
        edge(rid(id), rid(row['actual']), 'observed_redirect', row['file'])
    owner = nodes[rid(id)]['group']
    if owner in ledger and owner != id:
        edge(rid(owner), rid(id), 'declared_owner', 'catalog.mode 或面板 data-la-owner')

# Fields belong to their narrowest source ancestor. Runtime snapshots can include
# ancestor content, so they are separate observation edges, never ownership proof.
fields = set()
for el in soup.select('[data-save]'):
    key = el['data-save']
    fields.add(key)
    a = nearest(el, True)
    b = node('field:'+key, key, 'field', nodes[a]['group'], sourceAttribute='data-save')
    edge(a, b, 'binds_field', '正式HTML data-save；不等于已验证保存')

standalone = read(PROBE / 'interface-inventory.json')['results']
documents = {}
for row in standalone:
    path = unquote(row['requested']).split('?')[0].split('#')[0]
    documents[path] = node('document:'+path, row.get('title', path), 'document', 'resources',
                           path=path, probe='ui-route-probe-20260921/interface-inventory.json',
                           coverage='独立页面已打开；全部操作未认证')
    edge('root', documents[path], 'contains', '独立HTML文件')

for id, row in ledger.items():
    data = read(PROBE / 'full-content' / row['file'])
    for link in data['links']:
        href = unquote(link.get('href') or '')
        target = None
        if href.startswith('#') and href[1:] in ledger:
            target = rid(href)
        elif not urlsplit(href).scheme:
            target = documents.get(href.split('?')[0].split('#')[0])
        if target:
            edge(rid(id), target, 'observed_href', row['file']+'；DOM链接，含隐藏内容，不等于点击成功')

for i, f in enumerate(mapping['functions']):
    a = node('function:'+str(i), f['name'], 'function', f['group'], function=f)
    edge('root', a, 'contains', '人工功能清单')
    for target in re.findall(r'#([A-Za-z0-9_-]+)', f['entry']):
        if target in ledger: edge(a, rid(target), 'function_entry', '42功能清单')

dynamic = read(PROBE / 'dynamic-interfaces.json')['results']
for i, state in enumerate(dynamic):
    route = urlsplit(state['url']).fragment
    a = node('state:'+str(i), state['name'], 'state', nodes.get(rid(route),{}).get('group','resources'),
             probe='ui-route-probe-20260921/dynamic-interfaces.json',
             checkedAt=state['checkedAt'], coverage='隔离数据实际点击所得状态')
    edge(rid(route) if rid(route) in nodes else 'root', a, 'observed_state', '动态探针 results['+str(i)+']')

issues = [
 ('词句嵌在记录页；写作归工作台', ['records','vocabulary-review','sentence-learning','writing-workbench']),
 ('话题词卡收藏未进入单词表', ['topical-vocabulary','vocabulary-review']),
 ('句子收藏缺少原材料返回路径', ['sentence-learning']),
 ('写作工作台六题，新题衔接缺失', ['writing-workbench','writing2']),
 ('今天清单与每日安排无衔接，日期含义不明', ['plan','guide']),
 ('首页继续上次不覆盖独立学习工具', ['study','writing-workbench','course-window','vocabulary-review','sentence-learning']),
 ('原始资料页混入教学与练习目录', ['library']),
 ('练习包装入口和单元入口显示范围不同', ['pp-reading','reading-case-bank']),
 ('旅游词汇的模式、归类、题型不一致', ['pp-vocabulary','pr-vocabulary-tourism']),
 ('每日背景任务落入写作Task 2', ['guide','topic-education']),
 ('Task 1/2旧入口均丢失具体类别', ['records','writing1','writing2']),
 ('手机重复标题、筛选与边框层次过多', ['vocabulary-review','study','speaking']),
 ('写作手机输入区远；阶段快捷键可用', ['writing-workbench']),
 ('首次口语保存后进度仍0/0', ['speaking-first']),
 ('新口语任务缺同题录音入口', ['speaking']),
 ('资料来源hidden标签被CSS显示', ['materials']),
 ('定制课程归学习但主入口在工作台', ['workspace','course-window'])]
for i, (label, routes) in enumerate(issues, 1):
    a = node('issue:'+str(i).zfill(2), label, 'issue', 'issues', status='已复现，未修复',
             evidence='ui-experience-audit-20260921.md#'+str(i).zfill(2))
    for route in routes:
        if rid(route) in nodes: edge(a, rid(route), 'issue_affects', '审查报告问题 '+str(i).zfill(2))

parent = {e['target']:e['source'] for e in edges.values() if e['relation']=='contains'}
def depth(id, seen=None):
    seen = set() if seen is None else seen
    assert id not in seen, 'Containment cycle '+id
    if id not in parent: return 0
    return 1 + depth(parent[id], seen|{id})
for id, n in nodes.items(): n['depth'] = depth(id)
relations = sorted({e['relation'] for e in edges.values()})
node_index = {id:i for i,id in enumerate(nodes)}
relation_index = {r:i for i,r in enumerate(relations)}
assert len(ledger) == 429 and len(fields) == 3368 and len(standalone) == 9 and len(dynamic) == 24
assert all(e['source'] in nodes and e['target'] in nodes for e in edges.values())
data = dict(schema='ielts-evidence-graph-v1', baseline_sha256=mapping['baseline_sha256'],
            nodes=list(nodes.values()), edges=list(edges.values()), relations=relations,
            tensor=dict(notation='A[source_node,target_node,relation_type]', shape=[len(nodes),len(nodes),len(relations)],
                        storage='COO binary presence; unlisted pairs UNKNOWN, not proven absent',
                        entries=[[node_index[e['source']],node_index[e['target']],relation_index[e['relation']],1] for e in edges.values()]),
            semantics={'contains':'物理HTML层级或图册层级', 'declared_owner':'导航归属；不是物理父级',
                       'observed_href':'读取到链接；不是已验证点击', 'binds_field':'静态字段绑定；不是保存成功',
                       'observed_redirect':'实际打开后地址变化', 'observed_state':'实际点击后界面状态',
                       'function_entry':'功能清单入口','issue_affects':'已复现问题关联'},
            limits=['429地址全部打开不等于所有交互穷尽', '字段保持独立身份；未合并同材料的不同作答',
                    '没有边表示未知；图形交叉、环路和多入口不自动判定为错误',
                    '存储键/写入路径尚需逐控制器补证；不从data-save推断事务或云同步'])
(OUT/'graph.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
counts = dict(nodes=len(nodes), edges=len(edges), nodeTypes=dict(Counter(n['kind'] for n in nodes.values())),
              relations=dict(Counter(e['relation'] for e in edges.values())),
              tensorShape=data['tensor']['shape'], danglingEdges=0,
              baseline_sha256=mapping['baseline_sha256'])
(OUT/'validation.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2),encoding='utf-8')
template = (ROOT/'research/tensor_tree_viewer.html').read_text(encoding='utf-8')
(OUT/'分级张量立体树.html').write_text(template.replace('__GRAPH_JSON__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
print(json.dumps(counts,ensure_ascii=False))
