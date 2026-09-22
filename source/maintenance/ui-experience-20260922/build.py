from pathlib import Path
from hashlib import sha256
from bs4 import BeautifulSoup
import json
P=Path(__file__).resolve().parent;R=P.parent
baseline=R/'ui-polish-20260922/candidate.html';raw=baseline.read_bytes()
EXPECTED='3ba0baa50a6482d10b516112f0cfb2b8cb454b700ef11a141c30b4fbd65dabdc'
assert sha256(raw).hexdigest()==EXPECTED
s=BeautifulSoup(raw.decode(),'html.parser');frag=lambda html:BeautifulSoup(html,'html.parser')
oldfields=[str(n) for n in s.select('[data-save]')];oldids={n['id'] for n in s.select('[id]')};oldmedia=[str(n) for n in s.select('audio,source,img,video')]
def change(id,fn):n=s.find(id=id);n.string=fn(str(n.string))
change('learning-adjust-script',lambda j:j.replace("textContent=mode==='study'?'学习':'练习'","textContent=mode==='study'?'学习库':'专项练习'").replace("el('summary','以往作答 · '","el('summary','历次作答 · '"))
def history(j):
    old="hist.replaceChildren(el('summary','历次作答 · '+(t?.history.length||0)+' 次'));for"
    new="hist.replaceChildren(el('summary','历次作答 · '+((t?.history.length||0)+(submitted?1:0))+' 次'));if(submitted){const recent=el('div','','ux-current-result');recent.append(el('h3','最近一次 · 本次已提交'),el('p',new Date(t.submittedAt).toLocaleString()),button('查看本次结果',()=>result.scrollIntoView({block:'start'})));hist.append(recent);}else if(!t?.history.length)hist.append(el('p','还没有往期作答。新一轮开始后，之前的提交或草稿会保留在这里。','ux-history-empty'));for"
    assert old in j
    return j.replace(old,new)
change('learning-adjust-script',history)
# Copy/links left over from the old favorite-first word model.
popup=s.find(id='word-lookup');popup.select_one('.lookup-muted').string='查过的词自动进入复习，释义与原句留在本机。收藏只用于标记重点。'
popup.select_one('.lookup-dictionary')['href']='#lookup-learning';popup.select_one('.lookup-dictionary').string='查看查词与学习历史 →'
for a in s.select('#records a[href="#vocabulary-review"]'):a.string='背单词'
for a in s.select('#records a[href="#writing-workbench"]'):a.string='写作训练'
for a in s.select('a[href="#workspace"]'):
    if a.get_text(strip=True)=='← 返回工作台':a.string='← 资料与记录'
# Source records stay intact; make their backup controls easy to reach.
records=s.find(id='records');backup=records.select_one('.backup-box');backup.extract();heading=records.select_one('header');heading.insert_after(backup) if heading else records.insert(0,backup)
backup.select_one('h2').string='记录备份'
backup.insert_after(frag('<nav class="ux-record-links" aria-label="常用记录"><a href="#review-history">单词学习记录 <span>回忆 · 拼写 · 背词</span></a><a href="#tests">自测记录 <span>四科作答与历次结果</span></a><a href="#writing-workbench">写作稿件 <span>首稿 · 检查 · 修订</span></a></nav>'))
if records.select_one('.record-learning-links'):records.select_one('.record-learning-links')['hidden']=''
# Test dashboard: one real status surface per subject, retaining original routes.
glyphs={'listening':'<path d="M4 14v-3a8 8 0 0 1 16 0v3M4 12h3v8H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2Zm16 0h-3v8h3a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2Z"/>','reading':'<path d="M12 5v16M3 4h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v15h-5a5 5 0 0 0-4 2 5 5 0 0 0-4-2H3Z"/>','writing':'<path d="m4 16 12-12 4 4L8 20H4ZM13 7l4 4M12 21h8"/>','speaking':'<rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>'}
for skill,card in zip(glyphs,s.select('#tests .la-subject-card')):
    card['data-ux-test']=skill
    card.insert(0,frag(f'<div class="ux-subject-symbol"><svg viewBox="0 0 24 24" aria-hidden="true">{glyphs[skill]}</svg><span>{skill.upper()}</span></div>'))
    action=card.find('a');action['class']='ux-test-start';action.insert_before(frag('<div class="ux-test-status" role="status"></div>'))
    description=card.find_all('p',recursive=False)[-1];source=s.new_tag('details',attrs={'class':'ux-test-source'});summary=s.new_tag('summary');summary.string='题目来源';source.append(summary);description.insert_before(source);description.extract();source.append(description)
    card.append(frag(f'<a href="#test-{skill}" data-ux-history="{skill}" class="ux-test-history">历次作答 <span>0</span></a>'))
tests=s.find(id='tests');tests.select_one('.la-heading p:last-child').string='选一科开始，或接着上次作答。提交后查看结果，历次作答随时可回看。'
tests.select_one('.la-heading').append(frag('<div id="ux-test-summary" aria-label="自测记录概况"></div>'))
for skill in glyphs:
    panel=s.find(id='test-'+skill);hist=panel.select_one('[data-test-history]');hist['id']='ux-test-history-'+skill
    control=panel.select_one('.la-test-controls');control.select_one('[data-test-progress]').insert_before(frag(f'<button type="button" class="ux-history-jump" data-ux-history="{skill}">历次作答</button>'))
    parts=panel.select('.la-test-part')
    nav=s.new_tag('nav',attrs={'class':'ux-part-nav','aria-label':'测试分区'})
    for i,part in enumerate(parts,1):
        id=part.get('id',f'ux-{skill}-part-{i}');part['id']=id
        nav.append(frag(f'<button type="button" data-ux-part="{id}">{part.select_one("h2").get_text(strip=True).split(" · ")[0]}</button>'))
        images=part.select(':scope > .la-test-page');sheet=part.select_one(':scope > .la-test-sheet')
        if images and not sheet and skill=='writing':
            sheet=s.new_tag('div',attrs={'class':'la-test-sheet ux-writing-answers'})
            nodes=list(images[-1].find_next_siblings());images[-1].insert_after(sheet)
            for n in nodes:n.extract();sheet.append(n)
        if images and sheet:
            layout=s.new_tag('div',attrs={'class':'ux-paper-layout'});paper=s.new_tag('div',attrs={'class':'ux-paper-pages','id':id+'-paper'})
            if skill=='writing':layout['class'].append('ux-writing-layout')
            images[0].insert_before(layout)
            for image in images:image.extract();paper.append(image)
            sheet.extract();sheet['id']=id+'-answers';layout.append(paper);layout.append(sheet)
            toggle=s.new_tag('div',attrs={'class':'ux-paper-toggle','aria-label':'题页与答题框'})
            toggle.append(frag(f'<button type="button" data-ux-view="paper" aria-controls="{id}-paper" aria-pressed="true">看题页</button><button type="button" data-ux-view="answers" aria-controls="{id}-answers" aria-pressed="false">写答案</button>'))
            layout.insert_before(toggle);part['data-ux-view']='paper'
    control.insert_after(nav)
# A compact dashboard above the existing question catalogue; no new saved state.
directory=s.select_one('#writing-workbench .ww-directory')
directory.insert(0,frag('<div class="ux-writing-intro"><span class="ux-eyebrow">WRITING STUDIO</span><h2>把想法写清楚。</h2><p>选一道题，接着写。题面、首稿与修订保存在同一处。</p><div id="ux-writing-summary"></div></div>'))
directory.select_one('.ww-directory-tools').append(frag('<label>进度<select id="ux-writing-progress"><option value="all">全部题目</option><option value="started">我写过的</option><option value="new">还未开始</option></select></label>'))
directory.select_one('.ww-directory-count').insert_after(frag('<div id="ux-writing-empty" hidden><h3>没有找到匹配的题目</h3><p>换个关键词，或清除筛选再看看。</p><button type="button" id="ux-writing-clear">清除筛选</button></div>'))
def writing(j):
    j=j.replace("||!row.dataset.wwSearch.toLocaleLowerCase().includes(query)","||!row.dataset.wwSearch.toLocaleLowerCase().includes(query)||(document.getElementById('ux-writing-progress').value==='started'&&!hasDraft(map.get(row.dataset.wwPick)))||(document.getElementById('ux-writing-progress').value==='new'&&hasDraft(map.get(row.dataset.wwPick)))")
    j=j.replace("directory.querySelector('.ww-directory-count').textContent=count?", "document.getElementById('ux-writing-empty').hidden=count>0;directory.querySelector('.ww-directory-count').textContent=count?")
    j=j.replace("badge.textContent=labels.length?", "badge.hidden=labels.length===0;badge.textContent=labels.length?")
    j=j.replace('工作台尚未开始','尚未开始')
    j=j.replace('search.addEventListener(\'input\',filter);',"document.getElementById('ux-writing-progress').addEventListener('change',filter);document.getElementById('ux-writing-clear').addEventListener('click',()=>{search.value='';taskFilter.value='';document.getElementById('ux-writing-progress').value='all';filter();search.focus();});search.addEventListener('input',filter);")
    return j
change('writing-entry-controller',writing)
for card in s.select('#workspace .la-card'):
    card['class']=card.get('class',[])+['ux-resource-card']
    title=card.select_one('h2');title.insert_before(frag('<span class="ux-resource-index">'+str(list(s.select('#workspace .la-card')).index(card)+1).zfill(2)+'</span>'))
style=s.new_tag('style',id='ux-upgrade-style');style.string=(P/'upgrade.css').read_text(encoding='utf8');s.head.append(style)
script=s.new_tag('script',id='ux-upgrade-controller');script.string=(P/'upgrade.js').read_text(encoding='utf8');s.body.append(script)
assert [str(n) for n in s.select('[data-save]')]==oldfields,'Do not change or reorder saved controls'
assert oldids<={n['id'] for n in s.select('[id]')}
assert oldmedia==[str(n) for n in s.select('audio,source,img,video')]
out=str(s).encode();(P/'candidate.html').write_bytes(out)
report={'baseline':EXPECTED,'candidate':sha256(out).hexdigest(),'fields':len(oldfields),'idsRetained':len(oldids),'mediaRetained':len(oldmedia)};(P/'build.json').write_text(json.dumps(report,indent=2),encoding='utf8')
check=P/'syntax';check.mkdir(exist_ok=True)
for i,n in enumerate(s.select('script:not([src])')):
    if n.get('type','') not in ['application/json','application/ld+json']:(check/(n.get('id',f'script-{i}')+'.js')).write_text(n.string or '',encoding='utf8')
print(json.dumps(report))
