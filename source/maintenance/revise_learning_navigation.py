"""Navigation-only revision of the frozen audit candidate; never publishes it."""
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib,json,sys

ROOT=Path(__file__).resolve().parent
OUT=Path('D:/IELTS-Work/learning-adjust-20260920')
SOURCE=OUT/'开始学习-adjusted.html'
TARGET=OUT/'开始学习-navigation-v2.html'
EXPECTED='f3db37d7c40cd2825f09e83cd4b875436dbe72bd5302efadf83782d13368b1da'
def run():
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED,'Frozen audit candidate changed'
    s=BeautifulSoup(raw.decode('utf8'),'html.parser')
    def add(n,html):
        for c in list(BeautifulSoup(html,'html.parser').contents):n.append(c)
    nav=s.select_one('#workspace-navigation nav');nav.clear()
    for ident,title in [('study','学习'),('practice','练习'),('tests','测试'),('workspace','工作区')]:add(nav,f'<button data-go="{ident}" type="button"><span>{title}</span></button>')
    data=json.loads(s.find(id='learning-adjust-data').string);data['navigationVersion']=2
    for u in data['units']:
        if u['skill']=='phrases' and u['mode']=='practice':u['mode']='study'
    for mode in ['study','practice']:
        panel=s.find(id=mode);title=panel.select_one('.la-heading');title.find('p',class_=None).string='先选一科，再选择具体内容。'
        crumb=s.new_tag('nav',id=f'la-{mode}-location',attrs={'class':'la-section-links'});title.insert_after(crumb)
        for skill in ['listening','reading','writing','speaking','vocabulary','phrases','shared']:add(panel,f'<span id="{mode}-{skill}-list"></span>')
        picker=s.find(id=f'la-{mode}-skill');picker.clear();add(picker,'<option value="">全部写作</option><option value="writing1">Task 1</option><option value="writing2">Task 2</option>')
        label=picker.find_parent('label');label.contents[0].replace_with('写作类型')
        s.find(id=f'la-{mode}-count')['hidden']=''
        if mode=='study':
            links=panel.select_one(':scope > .la-links');links.clear();links['id']='la-study-extras'
            add(links,'<a href="#study-vocabulary-list">词汇</a><a href="#study-phrases-list">短语</a><a href="#study-shared-list">共用背景</a><a href="#course-window">我的学习项目</a>')
    # The four skills come first; the complete mock is a separate action beneath them.
    tests=s.find(id='tests');grid=tests.select_one(':scope > .la-grid');mock=tests.select_one(':scope > .la-card');grid.extract();mock.insert_before(grid)
    for card in grid.select('.la-card'):
        h=card.find('h2');h.string=h.get_text().replace('整科','')
    # Existing anchors remain valid; visible return labels match their new owners.
    for u in data['units']:
        node=s.find(id=u['id']);group='writing' if u['skill'].startswith('writing') else u['skill']
        for a in node.select('.reader-toolbar a[href="#background"]'):a['href']=f'#{u["mode"]}-{group}-list';a.string='← 返回本科内容'
    ui=s.find_all('script')[2]
    text=ui.string.replace("backgroundView(hash);if(pageId==='phrases')", "backgroundView(hash);if(pageId==='vocabulary'){vocabFilter='words';$('#vocab-search').value='';filterVocabulary();}if(pageId==='phrases')")
    ui.string=text
    s.find(id='learning-adjust-data').string=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    s.find(id='learning-adjust-script').string=(ROOT/'learning-adjust.js').read_text(encoding='utf8')
    style=s.new_tag('style',id='learning-navigation-v2-style');style.string='''[data-la-focus-hidden]{display:none!important}.la-focus-nav{display:flex;flex-wrap:wrap;gap:14px;padding:12px 0 22px;border-bottom:1px solid #d8e2d6;margin-bottom:24px}.la-focus-nav span{color:#61715e;font-size:14px}.la-toolbar[hidden],.la-links[hidden]{display:none!important}#tests>.la-grid{grid-template-columns:repeat(4,minmax(0,1fr))}#study>.la-grid,#practice>.la-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr))}@media(max-width:900px){#tests>.la-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:500px){#tests>.la-grid{grid-template-columns:1fr}}''';s.head.append(style)
    output=str(s).encode('utf8');TARGET.write_bytes(output)
    report={'sourceSHA256':EXPECTED,'sha256':hashlib.sha256(output).hexdigest(),'target':str(TARGET),'published':False,'primary':['学习','练习','测试','工作区'],'skills':['听力','阅读','写作','口语'],'existingContentAuditStillRequired':True}
    (ROOT/'research/navigation-v2-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');run()
