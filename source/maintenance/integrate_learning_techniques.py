"""Append technique lessons without rebuilding or replacing earlier resource content."""
from pathlib import Path
from html import escape as E
import json,re,hashlib,shutil
from markdown import markdown
from bs4 import BeautifulSoup

HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN=BOOK/'开始学习.html'
data=json.loads((HERE/'learning-techniques.json').read_text(encoding='utf8'))
units=data['units']
page=MAIN.read_text(encoding='utf8')
original=BeautifulSoup(page,'html.parser')
old_fields={x['data-save'] for x in original.select('[data-save]') if not x['data-save'].startswith(('resource-learned-tech-','resource-review-tech-','resource-note-tech-'))}
backup=HERE/'backups'/'开始学习-before-techniques-20260916.html'
backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(MAIN,backup)
page=re.sub(r'<!--TECHNIQUES-20260916:[^>]+-->.*?<!--/TECHNIQUES-20260916-->','',page,flags=re.S)
def mark(key,body):return '<!--TECHNIQUES-20260916:'+key+'-->'+body+'<!--/TECHNIQUES-20260916-->'
def insert_section(sid,body):
    global page
    pattern=r'(<section\b[^>]*\bid="'+sid+r'"[^>]*>)'
    assert len(re.findall(pattern,page))==1,sid
    page=re.sub(pattern,lambda m:m[1]+mark(sid,body),page,count=1)
def p(s,cls=''):return '<p'+(' class="'+cls+'"' if cls else '')+'>'+E(s)+'</p>'
def md(s):return markdown(s,extensions=['tables','nl2br','sane_lists'])
def ul(arr,ordered=False):
    tag='ol' if ordered else 'ul'
    return '<'+tag+'>'+''.join('<li>'+E(x)+'</li>' for x in arr)+'</'+tag+'>'
def link(anchor,text):return '<a href="#'+anchor+'">'+E(text)+'</a>'

# These are code-native teaching diagrams, with all chart values repeated in text.
svg_start='''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="430" viewBox="0 0 720 430" role="img"><style>text{font-family:Arial,sans-serif;font-size:17px;fill:#243b38}.small{font-size:14px}.box{fill:#edf2ee;stroke:#53716b;stroke-width:2}.line{fill:none;stroke:#53716b;stroke-width:2}</style><rect width="720" height="430" fill="#fff"/>'''
figures={}
figures['commuting']=svg_start+'<text x="50" y="32">Commuting in city L (%)</text>'
for val in range(0,71,10):
    y=350-val*4
    figures['commuting']+=f'<path d="M70 {y}H650" stroke="#e0e7e3"/><text class="small" x="35" y="{y+5}">{val}</text>'
for i,year in enumerate([2010,2015,2020,2025]):figures['commuting']+=f'<text x="{65+i*190}" y="377">{year}</text>'
for label,color,vals,y in [('Public transport','#245d77',[30,35,40,45],400),('Car','#ad2430',[60,50,40,30],400),('Cycling','#4a713b',[10,15,20,25],400)]:
    idx=['Public transport','Car','Cycling'].index(label)
    pts=' '.join(f'{80+i*185},{350-v*4}' for i,v in enumerate(vals))
    figures['commuting']+=f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>'
    for i,v in enumerate(vals):figures['commuting']+=f'<circle cx="{80+i*185}" cy="{350-v*4}" r="5" fill="{color}"/>'
    figures['commuting']+=f'<rect x="{50+idx*235}" y="391" width="18" height="8" fill="{color}"/><text x="{75+idx*235}" y="403" class="small">{label}</text>'
figures['commuting']+='</svg>'
figures['process']=svg_start+'''<text x="28" y="32">Paper recycling</text><defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#53716b"/></marker></defs>
<g class="box"><rect x="30" y="65" width="160" height="60" rx="7"/><rect x="270" y="65" width="160" height="60" rx="7"/><rect x="30" y="220" width="160" height="60" rx="7"/><rect x="270" y="220" width="160" height="60" rx="7"/><rect x="510" y="220" width="180" height="60" rx="7"/><rect x="510" y="345" width="180" height="55" rx="7"/></g>
<g text-anchor="middle"><text x="110" y="101">Collect waste paper</text><text x="350" y="101">Sort</text><text x="110" y="256">Remove rejects</text><text x="350" y="256">Make pulp</text><text x="600" y="256">Press and dry</text><text x="600" y="379">Recycled paper</text></g>
<g class="line" marker-end="url(#arr)"><path d="M190 95H267"/><path d="M350 125V217"/><path d="M280 125L135 217"/><path d="M430 250H507"/><path d="M600 280V342"/></g><text class="small" x="365" y="172">Usable paper</text><text class="small" x="35" y="165">Unsuitable material</text></svg>'''
figures['maps']=svg_start+'''<text x="26" y="32">Community centre: 2010 and 2025</text><text x="140" y="70">2010</text><text x="490" y="70">2025</text><path d="M675 72V30l-5 9m5-9 5 9" class="line"/><text x="668" y="95">N</text>
<g class="box"><rect x="25" y="105" width="310" height="290"/><rect x="375" y="105" width="310" height="290"/></g><g class="line"><path d="M180 105V395M25 250H335M530 105V395M375 250H685"/></g>
<g text-anchor="middle"><text x="103" y="180">Reading room</text><text x="257" y="180">Office</text><text x="103" y="325">Garden</text><text x="257" y="325">Entrance</text><text x="453" y="180">Café</text><text x="607" y="180">Office</text><text x="453" y="325">Study room</text><text x="607" y="325">Entrance</text></g></svg>'''
figures['collector']=svg_start+'''<text x="30" y="32">Rain collector — label parts 1–4</text><path d="M70 68L280 68L210 138V160H140V138Z" class="box"/><path d="M115 173H235V188H115Z" class="box"/><path d="M122 173L135 188m8-15 13 15m8-15 13 15m8-15 13 15m8-15 13 15" class="line"/>
<rect x="98" y="207" width="155" height="128" rx="6" class="box"/><path d="M100 287H251" stroke="#62a0af" stroke-width="3"/><path d="M253 314H408V354" stroke="#53716b" fill="none" stroke-width="10"/><path d="M380 350V402H448V350" class="line"/>
<g class="line"><path d="M435 100H250"/><path d="M435 180H238"/><path d="M435 244H255"/><path d="M585 314H413"/></g><text x="448" y="106">1. ________</text><text x="448" y="186">2. ________</text><text x="448" y="250">3. ________</text><text x="595" y="320">4. ____</text><text x="476" y="388">measuring cup</text><path d="M470 381H448" class="line"/>
<path d="M160 43V60m30-17v17m30-17v17" class="line"/></svg>'''
figdir=HERE/'technique-figures';figdir.mkdir(exist_ok=True)
dest=BOOK/'扩展资料'/'learning-techniques';dest.mkdir(parents=True,exist_ok=True)
for name,svg in figures.items():
    (figdir/(name+'.svg')).write_text(svg,encoding='utf8')
    (dest/(name+'.svg')).write_text(svg,encoding='utf8')
figure_alts={'commuting':'城市L通勤方式折线图，2010至2025年。公共交通30、35、40、45%；汽车60、50、40、30%；骑行10、15、20、25%。', 'process':'废纸收集后分类，不适用材料移出流程，可用纸制浆、压制干燥，产出再生纸。','maps':'社区中心2010年和2025年对照平面图，上方为北。西北阅览室改为咖啡区，西南花园改为学习室，东北办公室和东南入口保留。','collector':'雨水收集装置。1指顶部漏斗形入口，2指其下方横向网层，3指下方储水容器，4指容器底部通往已标记measuring cup的管道。'}

def controls(uid):
    return f'''<div class="res-track"><label><input type="checkbox" data-save="resource-learned-{uid}"> 我已学习本单元</label><label><input type="checkbox" data-save="resource-review-{uid}"> 加入我的复习</label></div><label class="field"><span>我的练习答案／证据／下次要改的一步（可留空）</span><textarea rows="4" data-save="resource-note-{uid}"></textarea></label>'''
def render(u):
    body=p(u['purpose'])+p(f"建议学习 {u['minutes']} 分钟；先读方法与例子，练习和复习可按需要展开。",'res-meta')
    sample=u.get('worked_example')
    body+='<h3>'+E(sample['title'] if sample else '看一个例子')+'</h3>'
    if u.get('figure'):
        f=u['figure'];body+='<figure class="technique-figure"><img class="res-figure" loading="lazy" src="扩展资料/learning-techniques/'+f+'.svg" alt="'+E(figure_alts[f],quote=True)+'"></figure>'
    if sample:
        body+='<div class="worked-prompt">'+md(sample['prompt_md'])+'</div>'
        body+='<section class="worked-answer"><h3>'+E(sample['answer_title'])+'</h3><div class="worked-answer-text" lang="en">'+md(sample['answer_md'])+'</div></section>'
        body+='<h3>答案为什么这样写</h3><div class="worked-reasons">'
        for i,x in enumerate(sample['explanations'],1):
            body+='<article class="worked-reason">'+p(str(i)+'. '+x['quote'],'worked-quote')+p('对应证据：'+x['evidence'])+p(x['explanation'])+'</article>'
        body+='</div>'
        if sample.get('contrasts'):
            body+='<h3>对照改一处</h3>'
            for x in sample['contrasts']:
                body+='<article class="worked-contrast">'+p('容易写成：'+x['wrong'])+p('改为：'+x['better'],'worked-correction')+p(x['why'])+'</article>'
    else:
        body+=md(u['example_md'])+p(u['explanation'])
    body+='<h3>再把方法用一遍</h3>'+ul(u['steps'],True)+'<h3>常见误区</h3>'+ul(u['pitfalls'])
    body+='<details class="technique-practice"><summary>动手练习</summary>'+md(u['practice_md'])+'<details class="technique-answer"><summary>参考答案与解释</summary>'+md(u['answer_md'])+'</details></details>'
    body+='<details><summary>换一份材料再用</summary>'+p(u['transfer'])+'</details>'+controls(u['id'])
    return '<details id="'+u['anchor']+'" class="res-unit resource-added technique-unit" data-technique="'+u['id']+'"><summary><span class="res-badge">新增技巧</span> '+E(u['title'])+' <span class="technique-time">'+str(u['minutes'])+' 分钟</span></summary><div class="res-body">'+body+'</div></details>'

for section,label in [('writing1','读图与写作专项技巧'),('reading','阅读专项技巧')]:
    arr=[u for u in units if u['section']==section]
    body='<section class="res-section technique-section"><h2 class="resource-added">'+label+'</h2>'
    if section=='writing1':
        body+=p('Academic Writing Task 1：把图表、地图或流程的主要信息写成连贯报告，至少 150 词，通常安排约 20 分钟。先对照完整范文或示范段看清答案，再读对应数据和写法解释。')
        body+=p('如果你说的“读图题”是在阅读文章中给图示填标签，请进入阅读图示标注。')+link('reading-tech-diagram','阅读图示标注 →')
    else:
        body+=p('先按卡点选方法：定位慢、判断不清、标题难分、填空失分，或看图对不上原文。每个单元都有步骤、英文例子和练习解释。')
        body+=p('Reading 图示标注是读文章后给图中部件填标签；Academic Writing Task 1 是根据图表写报告，两者任务不同。')+link('writing1-tech-read-chart','Task 1 读图与写作 →')
    body+='<div class="technique-jumps">'+''.join(link(u['anchor'],u['title'].split('：')[0]) for u in arr)+'</div>'+''.join(render(u) for u in arr)+'</section>'
    insert_section(section,body)

# Extend the existing catalogue payload, leaving its filtering and record logic intact.
pat=r'const catalog=(?=\[)'
matches=list(re.finditer(pat,page));assert len(matches)==1,'Expected one resource catalogue'
start=matches[0].end();catalog,consumed=json.JSONDecoder().raw_decode(page[start:])
catalog=[x for x in catalog if not x['id'].startswith('tech-')]
for u in units:catalog.append({'id':u['id'],'anchor':u['anchor'],'section':u['section'],'title':u['title'],'status':'学习技巧','current':False,'uses':0})
page=page[:start]+json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')+page[start+consumed:]
catalog_head_pattern=r'(<section\b[^>]*\bid="resource-update"[^>]*>.*?</header>)'
head_match=re.search(catalog_head_pattern,page,re.S);assert head_match,'Missing catalogue heading'
head=head_match[1]
head,changes=re.subn(r'\d+ 个教学单元(?= · 136 组用法)',str(len(catalog))+' 个教学单元',head,count=1)
assert changes==1,'Missing catalogue total'
page=page[:head_match.start()]+head+page[head_match.end():]
cards=''.join('<a class="res-card resource-added technique-card" href="#'+u['anchor']+'" data-res-section="'+u['section']+'" data-res-current="false"><span class="res-badge">新增技巧 · '+('阅读' if u['section']=='reading' else 'Task 1')+'</span><h3>'+E(u['title'])+'</h3>'+p(str(u['minutes'])+' 分钟 · 步骤 / 例子 / 练习与解释')+'</a>' for u in units)
assert page.count('<div class="res-grid">')==1
page=page.replace('<div class="res-grid">','<div class="res-grid">'+mark('cards',cards),1)
css='''.technique-jumps{display:flex;gap:10px 18px;flex-wrap:wrap;margin:18px 0 26px}.technique-jumps a{font-size:14px;text-underline-offset:4px}.technique-time{font-size:12px;color:var(--muted,#65726c);font-weight:400;white-space:nowrap}.technique-unit .res-body>ol{padding-left:24px}.technique-unit li{margin:10px 0;line-height:1.9}.technique-figure{margin:20px 0;max-width:760px}.technique-figure img{display:block;width:100%;height:auto;border:1px solid var(--line,#d9ded4);border-radius:8px}.technique-practice{margin-top:24px}.technique-answer{background:#f5f7f3}.technique-unit table{font-size:15px}.technique-unit td,.technique-unit th{padding:9px 14px}@media(max-width:700px){.technique-jumps{gap:12px}.technique-unit .res-body{padding-left:0;padding-right:0}.technique-unit summary{overflow-wrap:anywhere}.technique-unit .res-body>ol{padding-left:22px}.technique-unit td,.technique-unit th{padding:7px}}'''
page=page.replace('</head>',mark('style','<style>'+css+'</style>')+'</head>',1)
worked_css='''.worked-answer{margin:24px 0;padding:20px 24px;background:#f0f4ef;border:1px solid #cddacf;border-left:4px solid #52735e;border-radius:8px}.worked-answer h3{margin-top:0}.worked-answer-text p{line-height:1.95;margin:0 0 16px}.worked-answer-text p:last-child{margin-bottom:0}.worked-reason{padding:12px 0;border-bottom:1px solid #e6ded9}.worked-quote,.worked-correction{font-weight:600}.worked-reason p{margin:8px 0}.worked-contrast{padding:12px 18px;background:#f7f3ed;border-radius:8px;margin:12px 0}.worked-prompt{margin:18px 0}.worked-answer,.worked-prompt{overflow-wrap:anywhere}.worked-prompt table,.worked-answer table{max-width:100%}@media(max-width:700px){.worked-answer{padding:16px}.worked-contrast{padding:12px}.worked-answer-text{font-size:15px}}'''
page=page.replace('</head>',mark('worked-style','<style>'+worked_css+'</style>')+'</head>',1)
from merge_resource_directory import merge_html
page=merge_html(page)
new=BeautifulSoup(page,'html.parser')
assert old_fields.issubset({x['data-save'] for x in new.select('[data-save]')})
ids=[x['id'] for x in new.select('[id]')];assert len(ids)==len(set(ids)),'Duplicate IDs'
assert len(new.select('.technique-unit'))==12
assert len(new.select('.res-card'))==len(catalog)
assert len(new.select('.technique-unit [data-save]'))==36
for x in new.select('.technique-section'):
    assert not re.search('https?://|官方|出处|核验|自编',x.get_text()),'Provenance leaked into learner UI'
MAIN.write_text(page,encoding='utf8')
shutil.copy2(HERE/'learning-techniques.json',BOOK/'learning-techniques.json')
report={'date':data['date'],'units':len(units),'catalog_units':len(catalog),'new_record_fields':36,'figures':list(figures),'anchors':[u['anchor'] for u in units],'main_sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest(),'catalog':catalog}
(HERE/'learning-techniques-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='catalog'},ensure_ascii=False))
