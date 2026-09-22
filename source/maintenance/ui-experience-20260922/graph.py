"""Actual UI ownership × content × activity × persisted-field relation graph."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib
P=Path(__file__).resolve().parent
raw=(P/'candidate.html').read_bytes();s=BeautifulSoup(raw,'html.parser')
nodes=[];edges=[]
def node(id,label,kind,parent=None,**props):
    nodes.append(dict(id=id,label=label,kind=kind,**props))
    if parent:edges.append(dict(source=parent,target=id,relation='contains'))
def edge(a,b,kind):edges.append(dict(source=a,target=b,relation=kind))
node('site','IELTS 当前入口与记录','root')
for n in s.select('#workspace-navigation [data-go]'):node('nav:'+n['data-go'],n.get_text(strip=True),'primary','site',route=n['data-go'])
for p in s.select('main>.panel'):
    owner=p.get('data-la-owner',p['id']);owner='workspace' if owner=='development' else owner
    node('panel:'+p['id'],p.get('data-la-title',p['id']),'panel','nav:'+owner,route=p['id'])
for u in json.loads(s.find(id='learning-adjust-data').string)['units']:
    target=s.find(id=u['id']);panel=target.find_parent('section',class_='panel') if target else None
    if target and 'panel' in target.get('class',[]):panel=target
    if panel:node('content:'+u['id'],u['title'],'content','panel:'+panel['id'],route=u['id'])
for f in s.select('[data-save]'):
    p=f.find_parent(class_='panel')
    node('field:'+f['data-save'],f['data-save'],'field','panel:'+p['id'] if p else 'site',field=f['data-save'])
for id,label,parent,uses in [
 ('learn','直接背词','vocabulary-review',['lookup-history-v1','word-learning-state-v1']),
 ('recall','自动到期复习','word-review',['lookup-history-v1']),
 ('spelling','拼写自测','word-review',['lookup-history-v1']),
 ('sentence','句子翻译、收藏与原句返回','sentence-learning',['sentence-collection-v1']),
 ('query','查词、最近查询与重点收藏','lookup-learning',['lookup-history-v1']),
 ('history','真实背词与复习事件','review-history',['lookup-history-v1']),
 ('library','已收录词表与释义编辑','word-library',['lookup-history-v1'])]:
    node('activity:'+id,label,'activity','panel:'+parent)
    for field in uses:edge('activity:'+id,'field:'+field,'reads/writes' if id!='history' else 'reads')
edge('content:topical-vocabulary','activity:learn','1000词 / 30话题，原词卡身份复用')
edge('activity:learn','activity:recall','学过自动接续，收藏非前提')
edge('activity:query','activity:recall','查过自动接续，收藏非前提')
edge('activity:spelling','activity:history','保留输入、正确性与提示状态')
edge('activity:sentence','nav:study','返回实际收藏来源；无来源时不伪造')
for skill in ['listening','reading','writing','speaking']:
    aid='activity:test-'+skill
    node(aid,skill+' 自测与历次作答','activity','panel:test-'+skill)
    edge('panel:tests',aid,'读取本次进度；直接继续或查看历次记录')
    edge(aid,'field:'+s.find(id='learning-adjust-state')['data-save'],'独立测试记录；包含历史归档')
    for field in s.select('#test-'+skill+' [data-save]'):edge(aid,'field:'+field['data-save'],'复用原题作答字段')
node('activity:writing-directory','32题目录 / 草稿筛选','activity','panel:writing-workbench')
node('activity:backup','导出与恢复真实文字记录','activity','panel:records')
edge('activity:backup','activity:writing-directory','整册备份包含首稿及修订')
data={'source_sha256':hashlib.sha256(raw).hexdigest(),'axes':['入口层级','内容对象','活动用途','保存归属'],'meaning':'多轴关系图；不是统计置信概率或新的用户数据存储。字段节点只描述契约，不包含用户记录。','nodes':nodes,'edges':edges}
(P/'interface-tensor.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
template='''<!doctype html><meta charset="utf-8"><title>当前接口分层关系图</title><style>body{margin:0;background:#10251f;color:#d7e5d8;font:14px system-ui}header{padding:20px 28px;display:flex;gap:20px;align-items:center;border-bottom:1px solid #365346}h1{font-size:19px;margin:0}p{margin:7px 0;font-size:12px;color:#9cb1a2}main{display:grid;grid-template-columns:1fr 330px;height:calc(100vh - 125px)}canvas{width:100%;height:100%}aside{padding:22px;overflow:auto;border-left:1px solid #365346}label{white-space:nowrap}select,input{background:#203f32;color:#def0df;border:1px solid #52765b;padding:7px}button{background:#335640;color:white;border:0;padding:8px;cursor:pointer}pre{white-space:pre-wrap;font-size:12px;line-height:1.8}a{color:#9fcea7}</style><header><div><h1>入口 × 内容 × 活动 × 保存字段</h1><p>分层投影 · 真实 DOM 与保存契约 · 不包含个人记录</p></div><label>栏目 <select id="scope"><option value="all">全站</option></select></label><label>深度角 <input id="angle" type="range" min="-70" max="70" value="24"></label><label><input id="fields" type="checkbox">显示字段</label></header><main><canvas id="c"></canvas><aside><p id="meta"></p><pre id="detail">点击节点检查关系；默认收起 4092 个保存字段。单词栏目共用词记录，句子保留自己的原有字段。</pre><p>原料 → 切片 → 用途全图：<a href="../research/content-tensor-20260921/内容分级张量图.html">资料关系图</a></p></aside></main><script>const D=__DATA__,c=document.querySelector('#c'),ctx=c.getContext('2d'),scope=document.querySelector('#scope'),angle=document.querySelector('#angle'),fields=document.querySelector('#fields'),detail=document.querySelector('#detail'),by=new Map(D.nodes.map(n=>[n.id,n])),parents=new Map(D.edges.filter(e=>e.relation==='contains').map(e=>[e.target,e.source]));for(const n of D.nodes.filter(n=>n.kind==='primary')){const o=document.createElement('option');o.value=n.id;o.textContent=n.label;scope.append(o)}scope.value='nav:vocabulary-review';let points=[];const depths={root:0,primary:1,panel:2,content:3,activity:3,field:4},colors={root:'#fff',primary:'#91d5a2',panel:'#9dbde8',content:'#c6c093',activity:'#db9a78',field:'#ae98d0'};function family(n){let k=n.id;for(let i=0;i<8;i++){if(k.startsWith('nav:'))return k;k=parents.get(k);if(!k)break}return null}function draw(){const box=c.getBoundingClientRect();c.width=box.width*devicePixelRatio;c.height=box.height*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);const w=box.width,h=box.height,a=+angle.value*Math.PI/180;const shown=D.nodes.filter(n=>(fields.checked||n.kind!=='field')&&(scope.value==='all'||family(n)===scope.value||n.id==='site'));const levels={};for(const n of shown)(levels[depths[n.kind]]??=[]).push(n);points=[];for(const [z,list]of Object.entries(levels)){list.forEach((n,i)=>{const cols=Math.max(1,Math.ceil(list.length/18)),col=Math.floor(i/18),row=i%18;const x=50+z*(w-170)/5+Math.sin(a)*row*4+col*8,y=60+row*(h-100)/18+Math.cos(a)*z*20;points.push({...n,x,y})})}const pby=new Map(points.map(n=>[n.id,n]));ctx.clearRect(0,0,w,h);ctx.strokeStyle='#355448';for(const e of D.edges){const f=pby.get(e.source),t=pby.get(e.target);if(!f||!t)continue;ctx.globalAlpha=e.relation==='contains'?.3:.8;ctx.beginPath();ctx.moveTo(f.x,f.y);ctx.lineTo(t.x,t.y);ctx.stroke()}ctx.globalAlpha=1;ctx.font='11px system-ui';for(const p of points){ctx.fillStyle=colors[p.kind];ctx.beginPath();ctx.arc(p.x,p.y,p.kind==='field'?2:5,0,7);ctx.fill();if(p.kind!=='field'&&(shown.length<120||p.kind==='primary'||p.kind==='root'))ctx.fillText(p.label.slice(0,20),p.x+9,p.y+4)}document.querySelector('#meta').textContent=`${shown.length} / ${D.nodes.length} 个节点 · ${D.edges.length} 条关系 · ${D.source_sha256.slice(0,12)}`}c.onclick=e=>{const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const p=points.reduce((b,n)=>Math.hypot(n.x-x,n.y-y)<Math.hypot(b.x-x,b.y-y)?n:b,points[0]);if(p)detail.textContent=JSON.stringify({node:by.get(p.id),relations:D.edges.filter(e=>e.source===p.id||e.target===p.id)},null,2)};scope.onchange=angle.oninput=fields.onchange=draw;window.onresize=draw;draw();</script>'''
(P/'interface-tensor.html').write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')),encoding='utf8')
print(json.dumps({'nodes':len(nodes),'edges':len(edges),'source':data['source_sha256']}))
