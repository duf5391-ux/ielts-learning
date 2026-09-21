from pathlib import Path
from collections import Counter
from html import escape
import json, re, shutil
from bs4 import BeautifulSoup
from markdown import markdown

HERE = Path(__file__).resolve().parent
BOOK = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN = BOOK / '开始学习.html'
OUTCOMES = {
 'family': ['区分实际照料、陪伴和家庭分工，并各举一个生活例子。', '用具体安排解释孩子的选择怎样与时间、接送相配合。', '用 take turns、keep in touch 等表达描述一次家庭互动。'],
 'food': ['区分食材、一道菜与一顿饭；说明单位价格与实际付款的区别。', '用做饭步骤、餐桌细节和使用数量解释自己的选择。', '正确使用 cook from scratch、a helping 和 value for money。'],
 'travel': ['区分行程、预订、目的地和景点。', '按计划、变化和回应讲清一次旅途经历。', '用具体例子说明游客与居民各自的需要。'],
 'media': ['区分传播渠道、目标受众和产品细节。', '从一次广告或推荐经历中说清注意、了解和选择的过程。', '正确区分 advertisement 与 advertising，并使用 recommend 和 suggest 的常用结构。'],
}

def fragment(html):
    return BeautifulSoup(html, 'html.parser')

def insert_children(parent, html):
    for child in list(fragment(html).contents): parent.append(child.extract())

def md(text):
    return markdown(text, extensions=['tables', 'fenced_code', 'nl2br'])

def replace_md(node, text):
    node.clear();insert_children(node,md(text))

def tag(soup, name, text=None, **attrs):
    n=soup.new_tag(name, attrs=attrs)
    if text is not None:n.string=text
    return n

def header(soup, reader, title, intro, category, minutes, outcomes, read_input=None):
    toolbar=tag(soup,'div',**{'class':'reader-toolbar ui-only'})
    toolbar.append(tag(soup,'a','← 资料目录',href='#background'))
    label=tag(soup,'label',**{'class':'read-toggle'})
    if read_input is None:read_input=tag(soup,'input',type='checkbox',**{'data-save':'topic-read-'+reader['id'].removeprefix('topic-')})
    label.append(read_input);label.append(' 已读过');toolbar.append(label)
    reader.append(toolbar)
    reader.append(tag(soup,'p',category,**{'class':'eyebrow'}))
    reader.append(tag(soup,'h2',title))
    if intro:reader.append(tag(soup,'p',intro,**{'class':'orientation'}))
    reader.append(tag(soup,'p',f'约 {minutes} 分钟 · 可分次阅读',**{'class':'background-read-meta'}))
    if outcomes:
        box=tag(soup,'div',**{'class':'background-outcomes'})
        box.append(tag(soup,'strong','这一页学什么'))
        ul=tag(soup,'ul')
        for goal in outcomes:ul.append(tag(soup,'li',goal))
        box.append(ul);reader.append(box)

def add_outline(soup, reader):
    headings=reader.select('.background-lesson h3')
    if not headings:return
    nav=tag(soup,'nav',**{'class':'background-outline','aria-label':'本页内容'})
    seen=set()
    for i,h in enumerate(headings):
        name=h.get_text(' ',strip=True)
        if i==0:label='认识话题'
        elif re.search(r'情境|例子|再看一个',name):label='情境与讲解'
        elif re.search(r'词|搭配|表达',name) and not re.search(r'句子|混淆|易混',name):label='常用表达'
        elif re.search(r'混淆|易混',name):label='辨析用法'
        elif re.search(r'回顾|读懂|理解检查|确认|检验',name):label='回顾一下'
        else:continue
        if label in seen:continue
        seen.add(label);nav.append(tag(soup,'button',label,type='button',**{'data-background-jump':str(i)}))
    target=reader.select_one('.enrichment-body, .background-lesson')
    target.insert_before(nav)

def format_lesson(reader):
    for p in reader.select('.background-lesson p'):
        text=p.get_text(' ',strip=True)
        if len(re.findall(r'\b[A-Za-z]+\b',text))>=45 and len(re.findall(r'[\u4e00-\u9fff]',text))<6:
            p['class']=list(dict.fromkeys(p.get('class',[])+['learning-english']))
    for table in reader.select('.background-lesson table'):
        labels=[h.get_text(' ',strip=True) for h in table.select('thead th')]
        for row in table.select('tbody tr'):
            for i,cell in enumerate(row.find_all('td',recursive=False)):
                if i<len(labels):cell['data-column-label']=labels[i]

def add_bottom(soup, reader):
    p=tag(soup,'p',**{'class':'reader-bottom'})
    p.append(tag(soup,'a','← 返回资料目录',href='#background'));reader.append(p)

def merge_words(glossary, words, topic):
    for w in words:
        term=re.sub(r'\s+',' ',w['term'].strip().lower())
        entry={k:w[k] for k in ('meaning','pos','chunk','example')};entry['source']='话题背景 · '+topic
        prev=glossary.get(term,[])
        glossary[term]=[entry]+[x for x in prev if any(x.get(k)!=entry[k] for k in ('meaning','pos','chunk','example'))]

def unify():
    source_groups=[json.loads((HERE/f'unified-background-{g}.json').read_text(encoding='utf8')) for g in 'abc']
    lessons=[u for group in source_groups for u in group]
    assert len(lessons)==12
    extended=[json.loads((HERE/f'expanded-{name}.json').read_text(encoding='utf8')) for name in ['family','food','travel','media']]
    personal=json.loads((HERE/'personal-background-expansion.json').read_text(encoding='utf8'))
    page=MAIN.read_text(encoding='utf8');soup=BeautifulSoup(page,'html.parser');background=soup.select_one('#background')
    before=Counter(x['data-save'] for x in soup.select('[data-save]'))
    before_ids={x['id'] for x in soup.select('[id]')}
    before_enrich=Counter(x['data-enrichment'] for x in soup.select('[data-enrichment]'))
    before_audio=[str(x) for x in soup.select('audio')]
    glossary_node=soup.select_one('#lookup-glossary');glossary=json.loads(glossary_node.string)
    original={u['id']:fragment(u['html']).find('article') for u in json.loads((HERE/'background-existing-readers.json').read_text(encoding='utf8'))}
    catalog_entries=[]
    for u in lessons:
        reader=background.select_one('#'+u['id']);assert reader is not None
        read=reader.select_one('[data-save^="topic-read-"]');read=read.extract() if read else None
        extras=[]
        for n in reader.select('.res-track, label.field'):
            if n.select_one('[data-save]'):extras.append(n.extract())
        reader.clear();reader['class']=['topic-reader','background-reader','is-updated','resource-added']
        header(soup,reader,u['title'],u['intro'],'主题学习',u['minutes'],u.get('learning_outcomes',[]),read)
        lesson=tag(soup,'div',**{'class':'prose background-lesson'});replace_md(lesson,u['lesson_md']);reader.append(lesson)
        anchors=original[u['id']].select('.source-anchor')
        if anchors:
            material=tag(soup,'details',**{'class':'background-material'})
            material.append(tag(soup,'summary','配套阅读'))
            for a in anchors:material.append(a.extract())
            reader.append(material)
        if extras:
            box=tag(soup,'details',**{'class':'background-recall'});box.append(tag(soup,'summary','我的学习记录'))
            for n in extras:box.append(n)
            reader.append(box)
        format_lesson(reader);add_outline(soup,reader);add_bottom(soup,reader)
        merge_words(glossary,u['glossary'],u['title'])
        catalog_entries.append(dict(id=u['id'],title=u['title'],intro=u['intro'],kind='theme',minutes=u['minutes'],updated=True,terms=[w['term'] for w in u['glossary']]))

    for name,u in zip(['family','food','travel','media'],extended):
        reader=background.select_one(f'[data-enrichment="{u["id"]}"]');assert reader is not None
        body=reader.select_one('.enrichment-body').extract()
        read=reader.select_one('[data-save^="topic-read-"]');read=read.extract() if read else None
        reader.clear();reader.name='article';reader.attrs.pop('open',None)
        reader['id']='topic-'+u['id'].removeprefix('background_').replace('_','-')
        reader['class']=['topic-reader','background-reader','background-expanded','is-updated']
        header(soup,reader,u['title'],u['intro'],'主题学习',u['minutes'],OUTCOMES[name],read)
        lesson=body.find('div',class_='prose',recursive=False);replace_md(lesson,u['lesson_md']);lesson['class']=['prose','background-lesson']
        for n in body.select('.resource-added'):n['class']=[c for c in n['class'] if c!='resource-added']
        old_recall=body.select_one('.background-recall')
        if old_recall:old_recall.unwrap()
        recall=tag(soup,'details',**{'class':'background-recall'});recall.append(tag(soup,'summary','回顾与我的表达（可选）'))
        for n in list(body.select('.enrichment-attempt,.enrichment-feedback')):recall.append(n.extract())
        body.append(recall);reader.append(body)
        background.append(reader.extract())
        format_lesson(reader);add_outline(soup,reader);add_bottom(soup,reader)
        merge_words(glossary,u['glossary'],u['title'])
        catalog_entries.append(dict(id=reader['id'],title=u['title'],intro=u['intro'],kind='theme',minutes=u['minutes'],updated=True,terms=[w['term'] for w in u['glossary']]))
    for section in background.select(':scope > .enrichment-section'):
        if not section.select('[data-enrichment]'):section.decompose()

    for u in personal:
        reader=background.select_one('#'+u['id']);assert reader is not None
        if not reader.select_one('.personal-original-lesson'):
            read=reader.select_one('[data-save^="topic-read-"]').extract()
            reader.select_one('.reader-toolbar').decompose()
            reader.select_one('.eyebrow').decompose()
            title=reader.find('h2',recursive=False).get_text(' ',strip=True);reader.find('h2',recursive=False).decompose()
            intro_node=reader.find('p',recursive=False);intro=intro_node.get_text(' ',strip=True);intro_node.decompose()
            for h in list(reader.select('h3')):
                if h.get_text(strip=True)=='同一主题，不同任务':
                    following=h.find_next_sibling()
                    if following and following.name=='p':following.decompose()
                    h.decompose()
            keep=list(reader.contents);reader.clear()
            header(soup,reader,title,intro,'生活片段',u['minutes'],u['learning_outcomes'],read)
            original_lesson=tag(soup,'div',**{'class':'prose background-lesson personal-original-lesson'})
            original_lesson.append(tag(soup,'h3','先读一段生活经历'))
            for n in keep:original_lesson.append(n.extract())
            reader.append(original_lesson)
        else:
            title=reader.find('h2',recursive=False).get_text(' ',strip=True);intro=reader.select_one('.orientation').get_text(' ',strip=True)
            for n in reader.select('.personal-added-lesson,.background-outline,.reader-bottom'):n.decompose()
        reader['class']=['personal-reader','background-reader','is-updated']
        added=tag(soup,'div',**{'class':'prose background-lesson personal-added-lesson'});replace_md(added,u['lesson_md']);reader.append(added)
        format_lesson(reader);add_outline(soup,reader);add_bottom(soup,reader)
        merge_words(glossary,u['glossary'],title)
        catalog_entries.append(dict(id=u['id'],title=title,intro=intro,kind='personal',minutes=u['minutes'],updated=True,terms=[w['term'] for w in u['glossary']]))

    authentic=background.select_one('.authentic-background')
    if authentic:
        for i,n in enumerate(list(authentic.select('.authentic-excerpt')),1):
            title=n.select_one('summary strong').get_text(' ',strip=True);intro=n.select_one('summary span').get_text(' ',strip=True)
            content=n.select_one('.authentic-content').extract()
            reader=tag(soup,'article',id=f'topic-original-{i:02}',**{'class':'topic-reader background-reader original-background-reader','data-original-topic':intro})
            header(soup,reader,title,intro,'原文阅读',8,[])
            reader.append(content);add_bottom(soup,reader);background.append(reader)
        authentic.decompose()
    for reader in background.select('.original-background-reader'):
        catalog_entries.append(dict(id=reader['id'],title=reader.find('h2',recursive=False).get_text(' ',strip=True),intro=reader.get('data-original-topic','原文与词汇注释'),kind='original',minutes=8,updated=False,terms=[n.get_text(' ',strip=True) for n in reader.select('.authentic-content b')]))
    assert len(catalog_entries)==34
    catalog=background.select_one('.topic-catalog')
    additions=catalog.select_one('#topic-additions');additions=additions.extract() if additions else None
    catalog.clear();catalog['class']=['topic-catalog','background-library','ui-only']
    insert_children(catalog,'<p class="background-library-intro">先认识话题，再通过情境、词语和句子把意思学清楚。选择一篇开始，也可以搜索想了解的内容。标题标红的是本次补充或扩写的材料。</p><div class="background-library-tools"><label for="background-search">找话题、生活场景或表达</label><input id="background-search" type="search" placeholder="例如：家庭、旅行、keep in touch"/><div class="background-filters" role="group" aria-label="资料类型"><button type="button" data-background-filter="theme" aria-pressed="true">主题学习 · 16</button><button type="button" data-background-filter="personal" aria-pressed="false">生活片段 · 6</button><button type="button" data-background-filter="original" aria-pressed="false">原文阅读 · 12</button><button type="button" data-background-filter="all" aria-pressed="false">全部</button></div></div><p id="background-result-count" class="background-library-count" aria-live="polite"></p>')
    grid=tag(soup,'div',**{'class':'topic-grid'})
    order=['topic-education','topic-work','topic-technology','topic-cities','topic-environment','topic-health','topic-culture','topic-everyday','topic-family-children','topic-food-consumption','topic-travel-tourism','topic-media-advertising','topic-crime','topic-government','topic-society','topic-space']
    catalog_entries.sort(key=lambda e:order.index(e['id']) if e['id'] in order else 30+(['personal','original'].index(e['kind'])))
    names={'theme':'主题学习','personal':'生活片段','original':'原文阅读'}
    for e in catalog_entries:
        card=tag(soup,'a',href='#'+e['id'],**{'class':'topic-tile'+(' is-updated' if e['updated'] else ''),'data-background-kind':e['kind'],'data-search':(' '.join([e['title'],e['intro']]+e['terms'])).lower()})
        short,_,subtitle=e['title'].partition('：')
        insert_children(card,f'<div class="topic-tile-top"><span>{names[e["kind"]]} · 约 {e["minutes"]} 分钟</span><span class="topic-read-label" data-read-status="{e["id"].removeprefix("topic-")}">未标记</span></div><h3>{escape(short)}</h3><p>{escape(subtitle or e["intro"])}</p><div class="tile-terms">{escape(" · ".join(e["terms"][:2]))}</div>')
        grid.append(card)
    catalog.append(grid);catalog.append(tag(soup,'p','没有匹配的内容，试试另一个话题或表达。',id='background-empty',hidden=''))
    if additions:catalog.append(additions)
    insert_children(catalog,'<div class="background-library-footer"><a href="#topic-coverage">话题对照表</a><a href="#resource-update">当季话题与其他学习资源</a><a href="#topic-use">安排一次背景学习</a></div>')
    chapter=background.find('header',class_='chapter-head',recursive=False)
    chapter.select_one('h1').string='话题背景'
    chapter.select_one('p:not(.eyebrow):not(.ui-kicker)').string='进入具体题目之前，先把概念、内容和常用表达学清楚。'
    background.insert(0,chapter.extract());chapter.insert_after(catalog.extract())
    for n in background.select(':scope > .new-library-entry'):n.decompose()
    for n in background.select(':scope > .background-start, :scope > .background-download'):n['data-background-catalog-only']='true'
    coverage=background.select_one('#topic-coverage')
    mapping={'艺术、媒体与广告、阅读':('topic-media-advertising','媒体与广告'),'住房与城市规划、交通、旅游':('topic-travel-tourism','旅游与当地生活'),'健康、食物与饮食、运动':('topic-food-consumption','食物与消费'),'家庭与儿童、休闲':('topic-family-children','家庭与儿童')}
    for row in coverage.select('tbody tr'):
        cells=row.find_all('td',recursive=False)
        if cells and cells[0].get_text(strip=True) in mapping:
            target,label=mapping[cells[0].get_text(strip=True)];cells[1].append(' · ');cells[1].append(tag(soup,'a',label,href='#'+target)) if not cells[1].select_one(f'a[href="#{target}"]') else None
    glossary_node.string=json.dumps(glossary,ensure_ascii=False).replace('</',r'<\/')
    for n in list(soup.select('#background-expansion-style,#background-library-style,#background-library-script')):n.decompose()
    for n in soup.select('style'):
        if '.res-grid' in (n.string or '') and '.resource-added' in (n.string or ''):n.string=(HERE/'resource-expansion.css').read_text(encoding='utf8')
    style=tag(soup,'style',id='background-library-style');style.string=(HERE/'background-library.css').read_text(encoding='utf8');soup.head.append(style)
    for script in soup.select('script'):
        text=script.string or ''
        text=text.replace("setCount('#record-topics',readCount,'/ 14 段')","setCount('#record-topics',readCount,'/ '+$$('[data-save^=\"topic-read-\"]').length+' 篇')")
        text=text.replace("small.textContent='/ 18 段'","small.textContent='/ '+$$('[data-save^=\"topic-read-\"]').length+' 篇'")
        if script.string is not None and text!=script.string:script.string=text
    script=tag(soup,'script',id='background-library-script');script.string=(HERE/'background-library.js').read_text(encoding='utf8');soup.body.append(script)
    after=Counter(x['data-save'] for x in soup.select('[data-save]'))
    assert not (before-after),f'Lost saved fields: {before-after}'
    assert all(k.startswith('topic-read-') for k in after-before),after-before
    assert all(v==1 for v in after.values()),'Duplicated save keys'
    assert before_enrich==Counter(x['data-enrichment'] for x in soup.select('[data-enrichment]'))
    assert before_audio==[str(x) for x in soup.select('audio')]
    assert before_ids-{x['id'] for x in soup.select('[id]')} <= {'background-expansion-style'}
    assert len({x['id'] for x in soup.select('[id]')})==len(soup.select('[id]'))
    backup=HERE/'backups'/'开始学习-before-unified-background.html'
    if not backup.exists():shutil.copy2(MAIN,backup)
    MAIN.write_text(str(soup),encoding='utf8')
    (HERE/'background-library-manifest.json').write_text(json.dumps({'catalog':catalog_entries,'preserved_fields':sum(before.values()),'saved_fields':sum(after.values()),'new_fields':list((after-before).keys()),'topic_read_count':len(soup.select('[data-save^="topic-read-"]'))},ensure_ascii=False,indent=2),encoding='utf8')
    (BOOK/'background-library-data.json').write_text(json.dumps({'topics':lessons,'expanded':extended,'personal':personal},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'catalog':len(catalog_entries),'saved_fields':sum(after.values()),'added_read_markers':sum((after-before).values()),'main':str(MAIN)},ensure_ascii=False))

if __name__=='__main__':unify()
