"""Product entry redesign. Works after reliability and writing patches."""
from pathlib import Path
from bs4 import BeautifulSoup
import re
HERE=Path(__file__).resolve().parent
frag=lambda html:BeautifulSoup(html,'html.parser')

def apply(page):
    s=BeautifulSoup(page,'html.parser')
    assert not s.find(id='product-entry-style'), 'Apply to the shared baseline once'
    energy=s.select_one('#energy-control summary')
    if energy:
        for node in list(energy.find_all(string=True,recursive=False)):
            if 'Energy Control' in str(node):node.replace_with(str(node).replace('Energy Control','学习与休息'))
    nav=s.select_one('#workspace-navigation nav');nav.clear()
    for id,title in [('study','学习'),('vocabulary-review','单词'),('word-review','复习'),('sentence-learning','句子'),('practice','练习'),('tests','测试'),('writing-workbench','写作工作台'),('workspace','工作台')]:
        nav.append(frag(f'<button data-go="{id}" type="button"><span>{title}</span></button>'))
        if s.find(id=id):s.find(id=id)['data-la-owner']=id
    goal=s.select_one('#workspace-navigation .sidebar-goal');goal.clear();goal.append(frag('<p>按自己的节奏学习。</p>'))
    s.main.append(frag('<section id="word-review" class="panel workspace-panel learning-tool-panel" data-la-owner="word-review" data-la-title="复习" hidden><header class="vr-heading"><h1>单词复习</h1></header><nav class="word-tool-links" aria-label="词句工具"><a href="#vocabulary-review">我的单词</a><a href="#sentence-learning">重看句子</a></nav></section>'))
    for id in ['vocabulary-review','sentence-learning','writing-workbench']:
        for n in s.select('#'+id+' > .la-section-links'):n['hidden']=''
    history=s.find(id='lookup-learning');history.extract();history['class']='panel workspace-panel learning-tool-panel';history['data-la-owner']='vocabulary-review';history['data-la-title']='查词历史';history['hidden']=''
    history.insert(0,frag('<nav class="word-tool-links"><a href="#vocabulary-review">← 单词</a></nav>'));s.main.append(history)
    for node in s.select('.workspace-topbar a[href="#records"]'):node['hidden']=''
    sentences=s.find(id='sentence-learning');about=s.new_tag('details',attrs={'class':'product-sentence-about'});summary=s.new_tag('summary');summary.string='如何收藏句子';about.append(summary)
    for node in list(sentences.find_all('p',recursive=False)):
        if not node.get('id'):node.extract();about.append(node)
    sentences.append(about)
    v=s.find(id='vocabulary-review-controller');js=str(v.string)
    js=js.replace('if (!lookup || !host) return;',"const reviewHost=document.getElementById('word-review');if (!lookup || !host || !reviewHost) return;")
    assert 'const reviewHost=' in js
    js=js.replace('host.replaceChildren();',"host.replaceChildren();const links=el('nav','','word-tool-links');for(const [id,label] of [['word-review','开始复习'],['topical-vocabulary','话题词卡'],['lookup-learning','查词历史']]){const a=el('a',label);a.href='#'+id;links.append(a);}host.append(links);")
    for name in ['stats','controls','status','stage','note']:js=js.replace('host.append('+name+')','reviewHost.append('+name+')')
    js=js.replace("stage.hidden=false; library.open=false; nextCard();","stage.hidden=false; library.open=true;location.hash='word-review'; nextCard();")
    js=js.replace('stage.hidden=true;library.open=true;session=null;refresh();}',"stage.hidden=true;library.open=true;session=null;refresh();location.hash='vocabulary-review';}")
    js=js.replace('function announce(text) { status.textContent=text; }',"function announce(text) { status.textContent=text;const n=document.getElementById('word-list-status');if(n)n.textContent=text; }")
    js=js.replace('host.append(heading);',"host.append(heading);const listStatus=el('p','','vr-muted');listStatus.id='word-list-status';listStatus.setAttribute('role','status');host.append(listStatus);")
    js=js.replace('summary.textContent=`查看单词表 · ${rows.length} 个词与词组`;', 'summary.textContent=`查看单词表 · ${rows.length} 个词与词组`;title.querySelector("h1").textContent="我的单词 · "+rows.length;')
    # Keep direct grading visible. Secondary detail/actions fold inside each row.
    js=js.replace("card.append(quick,el('p',row.selfAssessment?", "card.append(quick,el('p',row.selfAssessment?")
    v.string=js
    for id in ['study','practice']:
        root=s.find(id=id)
        for p in root.select('.la-heading p'):p['hidden']=''
        toolbar=root.select_one('.la-toolbar')
        search=s.find(id='la-'+id+'-search');searchLabel=search.find_parent('label');search.extract();searchLabel.decompose()
        search['aria-label']='搜索全部内容' if id=='study' else '搜索练习内容'
        searchbar=s.new_tag('div',attrs={'class':'product-search'});searchbar.append(search)
        count=s.find(id='la-'+id+'-count');count.extract();searchbar.append(count)
        for key,label,choices in [('difficulty','难度',[('','全部'),('1','1/5'),('2','2/5'),('3','3/5'),('4','4/5'),('5','5/5')]),('confidence','参考置信度',[('','全部'),('高','高'),('中','中'),('低','低')]),('status','状态',[('','全部'),('new','未开始'),('started','进行中'),('done','本项已完成')])]:
            labelNode=s.new_tag('label');labelNode.append(label);select=s.new_tag('select',id='la-'+id+'-'+key)
            for value,text in choices:
                opt=s.new_tag('option',value=value);opt.string=text;select.append(opt)
            labelNode.append(select);toolbar.append(labelNode)
        details=s.new_tag('details',attrs={'class':'product-filters'});summary=s.new_tag('summary');summary.string='筛选';details.append(summary)
        toolbar.insert_before(searchbar);toolbar.insert_before(details);toolbar.extract();details.append(toolbar)
        location=s.find(id='la-'+id+'-location');location.extract();searchbar.insert_after(location)
        cards=s.find(id='la-'+id+'-cards');cards['class']='product-content-list'
    quick=s.find(id='la-study-quick');resume=s.find(id='la-resume');resume.extract();quick.clear()
    quick.append(frag('<a class="product-today" href="#guide">直接开始 · 安排一段学习 →</a>'));quick.append(resume)
    quick.append(frag('<div class="product-quick-links"><a href="#plan" id="product-plan-link">自选清单 →</a><a href="#learning-projects">学习项目 →</a></div>'))
    # The existing source index and custom-material entries stay accessible without a giant tool section.
    s.find(id='study').append(frag('<nav class="product-index-foot"><a href="#my-vocabulary-materials">我的词汇资料</a><a href="#my-topic-materials">我的话题资料</a><a href="#resource-update">学习资源索引</a></nav>'))
    workspace=s.find(id='workspace');workspace['data-la-title']='资料与记录'
    workspace.select_one('h1').string='资料与记录'
    if not workspace.select_one('a[href="#development"]'):workspace.append(frag('<p class="product-index-foot"><a href="#course-window">定制课程 · 待开放</a><a href="#development">开发与维护</a></p>'))
    # This promise was left behind after custom courses were disabled.
    materials=s.find(id='materials')
    for node in list(materials.find_all(string=True)):
        text=str(node)
        if '把你的材料，做成贴合考试的课程' in text:node.replace_with(text.replace('把你的材料，做成贴合考试的课程','保存和整理自己的材料'))
        elif '选取相关考试材料，配上讲解和分阶段练习' in text:node.replace_with(text.replace('选取相关考试材料，配上讲解和分阶段练习','查看资料接入进度；已编写内容会进入学习与练习'))
    for unit in s.select('details[data-learning-unit]'):
        summary=unit.find('summary',recursive=False)
        heading=unit.select_one('.res-body h4,.res-body h3')
        if summary and heading and summary.get_text(' ',strip=True)==heading.get_text(' ',strip=True):heading['hidden']=''
    topical=s.find(id='topical-vocabulary')
    about=s.new_tag('details',attrs={'class':'product-topic-about'});summary=s.new_tag('summary');summary.string='词卡说明与来源';about.append(summary)
    for node in list(topical.select(':scope > .tv-intro,:scope > .tv-scope,:scope > .tv-links,:scope > .ui-kicker')):
        node.extract();about.append(node)
    lesson=s.find(id='prereq-vocabulary-usage');lesson.extract()
    practice=s.new_tag('details',attrs={'class':'product-topic-practice'});summary=s.new_tag('summary');summary.string='用选中的词造句（可选）';practice.append(summary);practice.append(lesson)
    topical.append(practice);topical.append(about)
    for card in topical.select('.tv-card'):
        if not card.get('id'):card['id']='word-card-'+card['data-tv-id']
    s.body.append(frag('<nav id="product-mobile-nav" aria-label="常用导航"><a href="#study">学习</a><a href="#vocabulary-review">单词</a><a href="#word-review">复习</a><a href="#sentence-learning">句子</a><button type="button" id="product-more">更多</button></nav>'))
    adjust=s.find(id='learning-adjust-script');j=str(adjust.string)
    j=j.replace("const learningTools = {", "const learningTools = {'word-review':'单词复习',")
    begin=j.index('  function unitCard(u) {');end=j.index('  function renderToday()',begin)
    j=j[:begin]+(HERE/'catalog-view.js').read_text(encoding='utf8')+'\n'+j[end:]
    begin=j.index('      if(category){');end=j.index('      if(!u&&',begin)
    j=j[:begin]+"      if(category){lastCategory={mode:category[1],skill:category[2]};restoreFilters(category[1],category[2]);}\n      else if(h==='study'||h==='practice')restoreFilters(h,'');\n"+j[end:]
    j=j.replace("guide:'今天',study:'学习'", "'word-review':'复习','vocabulary-review':'单词','sentence-learning':'句子','writing-workbench':'写作工作台',guide:'今天',study:'学习'")
    j=j.replace("['search','skill','topic','type','part']", "['search','skill','topic','type','part','difficulty','confidence','status']")
    j=j.replace("renderToday();renderParts();refreshGates();\n  }", "renderToday();renderParts();refreshGates();\n    if(panel.id==='study'||panel.id==='practice'){const y=listPositions.get(panel.id+':'+scope[panel.id])||0;requestAnimationFrame(()=>requestAnimationFrame(()=>window.scrollTo(0,y)));}\n    document.dispatchEvent(new CustomEvent('product-route-ready'));\n  }")
    j=j.replace("el('span',u.title)", "el('span','','product-crumb-detail')")
    j=j.replace("u?sectionName+' / '+u.skillLabel+' / '+u.title", "u?sectionName+' / '+u.skillLabel")
    j=j.replace('panel.prepend(nav);', "const origin=entryOrigins.get(u.id);if(origin){const back=nav.querySelector('a');back.href='#'+origin.hash;back.textContent=origin.search?'← 返回搜索结果':'← 返回'+(origin.mode==='study'?'学习内容':'练习列表');}else if(u.id==='topical-vocabulary'){const back=nav.querySelector('a');back.href='#vocabulary-review';back.textContent='← 单词';}panel.prepend(nav);")
    j=j.replace("const owner=panel.dataset.laCollectionTitle?", "const owner=u?.id==='topical-vocabulary'?'vocabulary-review':panel.dataset.laCollectionTitle?")
    # A sentence/word/workbench is a real last object; no empty resume card is needed.
    j=j.replace("else resume.append(el('p','还没有学习记录，选一项即可开始。','la-empty'));", "else resume.hidden=true;")
    adjust.string=j
    style=s.new_tag('style',id='product-entry-style');style.string=(HERE/'navigation.css').read_text(encoding='utf8');s.head.append(style)
    # Carry styles originally scoped only to the word-library into the separate review page.
    for oldStyle in list(s.find_all('style')):
        if oldStyle is style:continue
        text=oldStyle.string or ''
        if '#vocabulary-review' in text and '.vr-stage' in text:
            shared=s.new_tag('style',id='product-review-shared-style');shared.string=text.replace('#vocabulary-review','#word-review');s.head.append(shared);break
    style.extract();s.head.append(style)
    script=s.new_tag('script',id='product-entry-controller');script.string=(HERE/'navigation.js').read_text(encoding='utf8');s.body.append(script)
    return str(s)
