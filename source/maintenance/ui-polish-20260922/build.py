"""Incremental word workspace/UI integration; never rebuild from historical sources."""
from pathlib import Path
from hashlib import sha256
import json, re
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'product-repair-20260922/candidate.html'
EXPECTED='e2b9e12e58c8f03de4b43b8ec6bdb1b81a15130ddceb6b80ea5fff6a3d742075'
raw=BASE.read_bytes(); assert sha256(raw).hexdigest()==EXPECTED
s=BeautifulSoup(raw.decode('utf8'),'html.parser')
frag=lambda text:BeautifulSoup(text,'html.parser')
old_fields={n['data-save'] for n in s.select('[data-save]')}
old_ids={n['id'] for n in s.select('[id]')}
old_media=[str(n) for n in s.select('audio,video,source,img')]
def script(id,transform):
    n=s.find(id=id); n.string=transform(str(n.string))
def replace_required(text,old,new):
    assert old in text,old
    return text.replace(old,new)

# Only one primary vocabulary entry. All former deep links remain valid.
names={'study':'学习库','vocabulary-review':'单词','practice':'专项练习','tests':'自测','writing-workbench':'写作训练','workspace':'资料与记录'}
icons={
 'study':'<path d="M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4zM13 7a3 3 0 0 1 3-3h4v15h-3a4 4 0 0 0-4 2"/>',
 'vocabulary-review':'<rect x="3" y="3" width="18" height="18" rx="4"/><path d="m7 16 4-9 4 9M8.5 13h5M17 8v8"/>',
 'practice':'<path d="m14 4 6 6-11 11H3v-6zM11 7l6 6M15 3l2-2 6 6-2 2"/>',
 'tests':'<rect x="5" y="4" width="14" height="17" rx="3"/><path d="M9 4V2h6v2M9 12l2 2 4-5M9 18h6"/>',
 'writing-workbench':'<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M15 3l6 6M14 3v7h7M8 14h7M8 17h5"/>',
 'workspace':'<path d="M3 7h7l2-3h9v15a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 7V5a2 2 0 0 1 2-2h4"/>',
 'more':'<circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/>'}
def icon(id):return '<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">'+icons[id]+'</svg>'
nav=s.select_one('#workspace-navigation nav'); nav.clear()
for id,name in names.items():
    nav.append(frag(f'<button type="button" data-go="{id}">{icon(id)}<span>{name}</span></button>'))
    panel=s.find(id=id); panel['data-la-title']=name
    h=panel.select_one('.la-heading h1,.la-heading h2,.ww-heading h1,h1')
    if h:h.string=name
mobile=s.find(id='product-mobile-nav');mobile.clear()
for id,name in [('study','学习'),('vocabulary-review','单词'),('practice','练习'),('writing-workbench','写作')]:
    mobile.append(frag(f'<a href="#{id}">{icon(id)}<span>{name}</span></a>'))
mobile.append(frag(f'<button type="button" id="product-more">{icon("more")}<span>更多</span></button>'))

# The old dynamic word-list host is kept as a secondary view, with no duplicated stores.
word=s.find(id='vocabulary-review');word.clear()
word.append(frag('<div id="word-learn-app"></div><textarea id="word-learning-state" data-save="word-learning-state-v1" hidden aria-hidden="true"></textarea>'))
word['data-la-title']='背单词'
s.main.append(frag('<section id="word-library" class="panel workspace-panel learning-tool-panel" data-la-owner="vocabulary-review" data-la-title="已收录词语" hidden></section>'))
s.main.append(frag('<section id="review-history" class="panel workspace-panel learning-tool-panel" data-la-owner="vocabulary-review" data-la-title="学习记录" hidden><h1>学习记录</h1><p class="ui-subtitle">背词、回忆与拼写，每次作答都有迹可循。</p><div id="ui-review-history"></div></section>'))
for id,title in [('word-review','单词复习'),('sentence-learning','句子'),('lookup-learning','查词与历史')]:
    panel=s.find(id=id);panel['data-la-owner']='vocabulary-review';panel['data-la-title']=title
    for n in panel.select(':scope > .word-tool-links'):n.decompose()
    h=panel.select_one('h1,h2')
    if h:h.string=title
sentence=s.find(id='sentence-learning');sentence.select_one('.st-kicker').string='SENTENCES / IN CONTEXT'
hist=s.find(id='lookup-learning')
for n in hist.find_all('p',recursive=False):
    if '每次查询都会' in n.get_text():n.string='查过或学过的词都会留在这里，自动进入复习。收藏用于标记重点。'
hist.insert(0,frag('<button type="button" id="ui-query-word">查一个词</button>'))
# Shared store also includes studied words; do not mislabel them as lookups.
hist.select_one('h2').string='查过与学过的词'

def review(js):
    js=replace_required(js,"document.querySelector('#vocabulary-review')","document.querySelector('#word-library')")
    js=replace_required(js,'lookup.getHistory().filter(row => row.favorite === true)','lookup.getHistory()')
    a=js.index('host.replaceChildren();');b=js.index('\n  const heading',a)
    js=js[:a]+'host.replaceChildren();'+js[b:]
    replacements={
      '我的单词表':'已收录词语','我的单词 · ':'已收录词语 · ',
      '查词和话题词卡的收藏都在这里，可直接标记会不会。':'查过和学过的词自动收录；收藏只用于标记重点。',
      '加练全部收藏':'加练已收录词','搜索收藏的词语':'搜索已收录词语','全部收藏':'全部词语',
      '已收藏':'已收录','新收藏':'新收录',
      '还没有收藏。查词或在话题词卡中点“收藏”，就能在这里复习。':'还没有学过或查过的词。背一个词，就能在这里接着复习。',
      '去话题词卡挑选 →':'开始背单词 →',
      "a.href='#topical-vocabulary';list.append(a);":"a.href='#vocabulary-review';list.append(a);",
      '取消收藏只移出复习队列，查询和复习历史继续保留。':'取消收藏仅取消重点标记，词语和复习历史继续保留。',
      '现在没有待复习词，可以继续收藏或稍后回来。':'现在没有到期的词。可以继续背新词，或加练已收录词。',
      '返回单词表':'继续背单词','收藏的英文词':'学过或查过的英文词',
      "button('取消收藏',()=>safe(()=>lookup.setFavorite(row.term,false)))":"button(row.favorite?'取消重点收藏':'标为重点收藏',()=>safe(()=>lookup.setFavorite(row.term,!row.favorite)))",
    }
    for a,b in replacements.items():js=replace_required(js,a,b)
    a=js.index('  function renderLegacy()');b=js.index('  function refresh()',a)
    js=js[:a]+'  function renderLegacy() { legacy.replaceChildren(); }\n'+js[b:]
    return js
script('vocabulary-review-controller',review)
script('lookup-controller',lambda js:js.replace('☆ 收藏到单词表','☆ 标为重点收藏').replace('去单词表复习 →','开始复习 →').replace("link.href='#vocabulary-review'; link.addEventListener('click',close)","link.href='#word-review'; link.addEventListener('click',close)").replace("link.href='#vocabulary-review';link.className='product-word-list-link'","link.href='#word-library';link.className='product-word-list-link'").replace('去单词表','查看已收录词语').replace('已收藏 · 在单词表','已重点收藏'))
script('lookup-controller',lambda js:js.replace('个查询词或词组','个查过或学过的词').replace("row.favorite ? '已收藏' : '查询记录'","row.favorite ? '重点收藏' : row.learning ? '学过的词' : '查询记录'").replace("row.count===0?'从话题词卡收藏'","row.count===0?(row.learning?'来自背词或已标记的词卡':'来自话题词卡')"))
script('lookup-controller',lambda js:js.replace("(old ? [{at:old.lastAt || old.firstAt || now,context:old.context || '',legacy:true}] : [])","(old && old.count>0 && (old.lastAt||old.firstAt) ? [{at:old.lastAt || old.firstAt,context:old.context || '',legacy:true}] : [])"))

def adjust(js):
    js=replace_required(js,"'vocabulary-review':'我的单词表'","'vocabulary-review':'背单词','word-library':'已收录词语','review-history':'学习记录','lookup-learning':'查词与历史'")
    js=js.replace("'sentence-learning':'我的句子本'","'sentence-learning':'句子'").replace("'writing-workbench':'写作工作台'","'writing-workbench':'写作训练'")
    js=js.replace("study:'学习',practice:'练习',tests:'测试',workspace:'工作台'","study:'学习库',practice:'专项练习',tests:'自测',workspace:'资料与记录'")
    return js
script('learning-adjust-script',adjust)
def product(js):
    a=js.index("    const title={'vocabulary-review'");b=js.index('    try{',a)
    js=js[:a]+'''    const wordRoutes=['vocabulary-review','word-review','sentence-learning','lookup-learning','review-history','word-library'];
    const title={'vocabulary-review':'单词 · 背单词','word-review':'单词 · 复习','sentence-learning':'单词 · 句子','lookup-learning':'单词 · 查词与历史','review-history':'单词 · 学习记录','word-library':'单词 · 已收录词语','writing-workbench':'写作训练'}[panel.id];
    if(title){$('#current-page-label').textContent=title;document.title=title+' · IELTS';}
    let id=panel.id;
    const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if(wordRoutes.includes(id)||target?.closest('#topical-vocabulary'))id='vocabulary-review';
    else if(!['study','practice','writing-workbench'].includes(id))id='product-more';
    for(const a of nav.children){const active=a.id===id||a.getAttribute('href')==='#'+id;if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
''' +js[b:]
    return js
script('product-entry-controller',product)

# Existing styles for the preserved library remain available at its new route.
for style in list(s.find_all('style')):
    if '#vocabulary-review' in (style.string or '') and '.vr-stage' in (style.string or ''):
        copy=s.new_tag('style',id='ui-library-compat-style');copy.string=style.string.replace('#vocabulary-review','#word-library');s.head.append(copy);break
style=s.new_tag('style',id='ui-polish-style');style.string=(HERE/'polish.css').read_text(encoding='utf8')+'\n'+(HERE/'word-learning.css').read_text(encoding='utf8');s.head.append(style)
for id,file in [('word-learning-controller','word-learning.js'),('word-history-controller','history.js'),('word-navigation-controller','word-navigation.js')]:
    node=s.new_tag('script',id=id);node.string=(HERE/file).read_text(encoding='utf8');s.body.append(node)
new_fields={n['data-save'] for n in s.select('[data-save]')}
assert old_fields <= new_fields and new_fields-old_fields=={'word-learning-state-v1'}
assert old_ids <= {n['id'] for n in s.select('[id]')}, old_ids-{n['id'] for n in s.select('[id]')}
assert old_media==[str(n) for n in s.select('audio,video,source,img')]
assert 'DAILY-STUDY-V1' in str(s)
out=str(s).encode('utf8');(HERE/'candidate.html').write_bytes(out)
syntax=HERE/'syntax';syntax.mkdir(exist_ok=True)
for i,node in enumerate(s.select('script:not([src])')):
    if node.get('type') in ['application/json','application/ld+json']:continue
    (syntax/(node.get('id',f'script-{i}')+'.js')).write_text(node.string or '',encoding='utf8')
report={'baseline':EXPECTED,'candidate':sha256(out).hexdigest(),'oldFields':len(old_fields),'fields':len(new_fields),'idsRetained':len(old_ids),'mediaRetained':len(old_media),'primaryEntries':names}
(HERE/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
