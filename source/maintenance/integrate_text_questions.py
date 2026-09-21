"""Integrate reviewed text into the live book, preserving records and source images.

Idempotent: on later runs update only qt-unit blocks, CSS, index, and script.
Never restore a historical whole-page backup over the live workbook.
"""
from pathlib import Path
from html import escape as E
from bs4 import BeautifulSoup
from PIL import Image
import json, base64, hashlib, shutil, re

HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN=BOOK/'开始学习.html'
QA=HERE/'text-conversion-qa';QA.mkdir(exist_ok=True)
data=json.loads((HERE/'text-questions.json').read_text(encoding='utf8'))
s=BeautifulSoup(MAIN.read_text(encoding='utf8'),'html.parser')
def frag(t): return BeautifulSoup(t,'html.parser')
def digest(t): return hashlib.sha256(t.encode()).hexdigest()
before={'fields':[x['data-save'] for x in s.select('[data-save]')], 'ids':[x['id'] for x in s.select('[id]')], 'scripts':[digest(x.get_text()) for x in s.select('script:not(#qt-script)')], 'audio':[x.get('src') for x in s.select('audio source,audio[src]')]}
backup=HERE/'backups'/'开始学习-before-text-questions-20260919.html'
if not backup.exists():
    shutil.copy2(MAIN,backup)
    (QA/'baseline.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
reference_images=list(BeautifulSoup(backup.read_text(encoding='utf8'),'html.parser').select('img'))
images_by_hash={digest(im.get('src','')):im for im in s.select('img')}
out=BOOK/'assets'/'text-questions';out.mkdir(exist_ok=True)
report=[]

for u in data['units']:
    anchor=u['chapter']+'-text-'+u['id']
    old=s.find(id=anchor)
    # Source figures always live in their associated original-pages disclosure.
    figures=list(old.select('.qt-originals > figure')) if old else [images_by_hash[digest(reference_images[i]['src'])].find_parent('figure') for i in u['images']]
    assert len(figures)==len(u['images']),anchor
    hashes=[digest(f.img['src']) for f in figures]
    field_pool={x['data-save']:x for x in old.select('[data-save]')} if old else {}
    for x in field_pool.values(): x.extract()
    unit=frag('<article class="qt-unit" id="'+anchor+'"><h3>'+E(u['title'])+'</h3><div class="qt-body" lang="en">'+u['html']+'</div><details class="qt-originals"><summary>查看原图 · '+str(len(figures))+' 页</summary></details></article>').article
    if u.get('crop'):
        import io
        im=Image.open(io.BytesIO(base64.b64decode(figures[0].img['src'].split(',',1)[1])))
        im.crop(tuple(u['crop'])).save(out/(u['id']+'.png'))
        chart=frag('<figure class="qt-diagram original"><img src="assets/text-questions/'+u['id']+'.png" alt="'+E(u['crop_alt'],quote=True)+'" loading="lazy"><figcaption>'+E(u['crop_alt'])+'</figcaption></figure>').figure
        unit.select_one('.qt-body').append(chart)
    for placeholder in list(unit.select('[data-move-field]')):
        key=placeholder['data-move-field']; n=placeholder['data-number']
        control=field_pool.pop(key,None)
        if control is None:
            found=s.select('[data-save="'+key+'"]');assert len(found)==1,(key,len(found))
            control=found[0]
            label=control.parent if control.parent.name=='label' else None
            control.extract()
            if label and label.parent and 'answer-grid' in label.parent.get('class',[]):label.decompose()
        control['class']=list(set(control.get('class',[])+['qt-input']))
        control['aria-label']='第'+n+'题答案'
        control['spellcheck']='false'
        if key.startswith('reading-q') and int(n)>=8:control['list']='qt-tfng'
        label=frag('<label class="qt-inline-answer"><span>'+n+'</span></label>').label
        label.append(control);placeholder.replace_with(label)
    assert not field_pool,field_pool.keys()
    if old:old.insert_before(unit)
    else:figures[0].insert_before(unit)
    originals=unit.select_one('.qt-originals')
    for f in figures:originals.append(f.extract())
    if old:old.decompose()
    assert [digest(f.img['src']) for f in originals.select('figure')]==hashes
    report.append({'id':anchor,'title':u['title'],'pages':len(figures),'sourceHashes':hashes,'textCharacters':len(unit.select_one('.qt-body').get_text()),'fields':[x['data-save'] for x in unit.select('[data-save]')]})

# The original inputs are now next to the questions, using precisely the same keys.
for grid in s.select('.answer-grid'):
    if not grid.select('[data-save]'):
        grid.replace_with(frag('<p class="qt-answer-note">直接在题目旁填写答案，文字会自动保存。</p>').p)
for cid in ['reading','listening']:
    area=s.select_one('#'+cid+'-first .work-area')
    if area:area['class']=list(set(area.get('class',[])+['qt-work-area']))

if not s.find(id='qt-tfng'):
    s.body.append(frag('<datalist id="qt-tfng"><option value="TRUE"></option><option value="FALSE"></option><option value="NOT GIVEN"></option></datalist>').datalist)

css='''
.qt-unit{margin:20px 0 28px;padding:26px 28px;background:#fff;border:1px solid #dce3d5;border-radius:10px;min-width:0;scroll-margin-top:100px}
.qt-unit>h3{font-size:19px;color:#354f35;margin:0 0 24px;line-height:1.5}
.qt-body{font:17px/1.85 Georgia,"Times New Roman",serif;color:#29392e;overflow-wrap:anywhere}
.qt-body p{font:inherit;color:inherit;margin:0 0 17px}.qt-body h4{font:600 18px/1.5 Arial,sans-serif;margin:27px 0 13px;color:#263c2d}
.qt-body ul,.qt-body ol{padding-left:27px;margin:12px 0 22px}.qt-body li{font:inherit;line-height:1.85;margin:9px 0;padding-left:3px}
.qt-body .qt-options li{margin:5px 0}.qt-passage p{margin-bottom:22px}.qt-footnotes{border-top:1px solid #dfe5da;padding-top:15px;margin-top:24px}.qt-footnotes p{font:14px/1.6 Arial,sans-serif}
.qt-task{padding:20px;background:#f5f7f1;border-left:3px solid #718b64;margin:20px 0}.qt-task p:last-child{margin-bottom:0}
.qt-rules{display:grid;grid-template-columns:110px 1fr;gap:8px 15px;margin:20px 0}.qt-rules dt{font-weight:bold}.qt-rules dd{margin:0}
.qt-question{padding:14px 0;border-bottom:1px solid #e5eadd}.qt-question p{margin-bottom:8px}
.qt-inline-answer{display:inline-flex!important;align-items:baseline;gap:7px;vertical-align:baseline;max-width:100%;margin:4px 3px!important;font:600 14px/1.5 Arial,sans-serif!important;color:#506746!important}
.qt-inline-answer .qt-input{display:inline-block;width:145px;max-width:100%;min-width:0;padding:8px 9px;margin:0;border:1px solid #b6c8ab;border-radius:5px;background:#fbfcf7;font:16px/1.4 Arial,sans-serif;color:#243a2b}
.qt-input:focus{outline:2px solid #6c895b;outline-offset:2px}.qt-input[readonly]{background:#eef1e9;color:#40533a}
.qt-table{width:100%;border-collapse:collapse;table-layout:fixed;margin:20px 0;font:16px/1.7 Arial,sans-serif}
.qt-table th,.qt-table td{padding:12px 13px;border:1px solid #d8e0ce;text-align:left;vertical-align:top;overflow-wrap:anywhere}.qt-table th{font-weight:500;background:#f2f5ec}.qt-shipping th{width:36%}.qt-table .qt-inline-answer{display:flex!important}.qt-table .qt-input{width:100%;max-width:170px}
.qt-matching{display:grid;grid-template-columns:1fr 1.7fr;gap:20px}.qt-diagram{margin:24px 0 0!important}.qt-diagram img{display:block;width:100%;height:auto;max-height:none!important;object-fit:contain}.qt-diagram figcaption{font:13px/1.7 Arial,sans-serif;color:#66795b;margin-top:12px}
.qt-originals{margin:24px 0 0!important;padding:0!important;border:0!important;border-top:1px solid #e1e6d8!important;background:transparent!important}.qt-originals>summary{font:14px/1.7 "Microsoft YaHei",sans-serif;color:#657b57;padding:15px 0!important;cursor:pointer}.qt-originals:not([open])>figure{display:none}.qt-originals img{max-width:100%;height:auto}.qt-originals .original{margin:15px 0}
#reading-first .qt-work-area,#listening-first .qt-work-area{grid-template-columns:1fr}.qt-work-area>.response{position:static}.qt-work-area>.material{min-width:0}
.qt-catalog{margin:30px 0;padding:24px;border:1px solid #dce3d5;background:#f7f9f3;border-radius:10px}.qt-catalog h2{margin:0 0 12px;font-size:22px}.qt-catalog label{display:block;font-size:14px}.qt-catalog input{display:block;width:100%;padding:12px;margin:10px 0;border:1px solid #becdaf;border-radius:6px;font-size:16px;background:white}.qt-results{display:grid;grid-template-columns:1fr 1fr;gap:0 25px;margin:15px 0;padding:0;list-style:none}.qt-results li{padding:13px 0;border-bottom:1px solid #dfe6d7}.qt-results a{font-size:15px;line-height:1.7;text-decoration:underline;text-underline-offset:3px}.qt-results [hidden]{display:none!important}.qt-count{font-size:13px;color:#6c7e5e}.qt-answer-note{font-size:14px}
@media(max-width:700px){.qt-unit{padding:18px 15px;margin:16px 0 22px}.qt-body{font-size:16px;line-height:1.85}.qt-body h4{font-size:17px}.qt-rules{grid-template-columns:1fr;gap:3px}.qt-rules dd{margin-bottom:10px}.qt-matching{grid-template-columns:1fr;gap:0}.qt-table{font-size:14px}.qt-table th,.qt-table td{padding:9px 8px}.qt-shipping th{width:37%}.qt-inline-answer .qt-input{width:122px}.qt-table .qt-input{width:100%;min-width:0}.qt-catalog{padding:18px}.qt-results{grid-template-columns:1fr}.qt-task{padding:15px}}
@media print{.qt-catalog,.qt-originals{display:none!important}.qt-unit{padding:0;border:0;break-inside:auto}.qt-body{font-size:11pt;line-height:1.55}.qt-input{background:white!important;border:0!important;border-bottom:1px solid #777!important}.qt-diagram{break-inside:avoid}.qt-work-area>.response:before{content:'在题目旁填写答案。'}}
'''
old=s.find(id='qt-style')
if old:old.decompose()
style=s.new_tag('style',id='qt-style');style.string=css;s.head.append(style)
old=s.find(id='text-question-directory')
if old:old.decompose()
catalog=frag('<section class="qt-catalog" id="text-question-directory"><h2>文字题目</h2><p>原文、题干和选项可以选词查义。搜索题名或英文原句，直接进入练习。</p><label for="qt-search">搜索全部文字题目<input id="qt-search" type="search" placeholder="例如 Davies、payment terms、tourism" autocomplete="off"></label><p class="qt-count" id="qt-count" aria-live="polite">14 组题目</p><ul class="qt-results"></ul><p id="qt-empty" hidden>没有找到匹配题目，请换一个关键词。</p></section>').section
for u in data['units']:
    a=u['chapter']+'-text-'+u['id']
    catalog.ul.append(frag('<li data-text-target="'+a+'"><a href="#'+a+'">'+E(u['title'])+'</a></li>').li)
# Integrate into the existing directory, after its title rather than add navigation.
lib=s.find(id='library');header=lib.find('h1') or lib.find('h2')
if header:header.insert_after(catalog)
else:lib.insert(0,catalog)
old=s.find(id='qt-script')
if old:old.decompose()
script=s.new_tag('script',id='qt-script');script.string='''(()=>{
const input=document.getElementById('qt-search');
const norm=t=>t.toLowerCase().normalize('NFKC').replace(/[’‘]/g,"'").replace(/\\s+/g,' ').trim();
const rows=[...document.querySelectorAll('[data-text-target]')].map(row=>({row,text:norm(document.getElementById(row.dataset.textTarget).querySelector('.qt-body').textContent+' '+row.textContent)}));
input.addEventListener('input',()=>{const words=norm(input.value).split(' ').filter(Boolean);let n=0;for(const item of rows){const match=words.every(w=>item.text.includes(w));item.row.hidden=!match;if(match)n++;}document.getElementById('qt-count').textContent=n+' / '+rows.length+' 组题目';document.getElementById('qt-empty').hidden=n>0;});
})();''';s.body.append(script)

# Update two source-image link labels to point at the usable text in the page.
for a in s.select('a'):
    if a.get_text(strip=True)=='先打开原题图' and '115010' in a.get('href',''):
        a['href']='#listening-text-open-university';a.string='打开文字题目'

after_fields=[x['data-save'] for x in s.select('[data-save]')]
assert sorted(before['fields'])==sorted(after_fields),'Record keys changed'
assert len(after_fields)==len(set(after_fields)),'Duplicate record keys'
assert set(before['ids']).issubset({x['id'] for x in s.select('[id]')}),'Existing anchor lost'
assert before['scripts']==[digest(x.get_text()) for x in s.select('script:not(#qt-script)')],'Existing script changed'
assert before['audio']==[x.get('src') for x in s.select('audio source,audio[src]')],'Audio changed'
assert len(s.select('.qt-originals img'))==21
assert not [im for im in s.select('img') if im.get('src','').startswith('data:') and not im.find_parent('details',class_='qt-originals')]
assert len(s.select('.qt-unit'))==14
ids=[x['id'] for x in s.select('[id]')];assert len(ids)==len(set(ids))
MAIN.write_text(str(s),encoding='utf8')
shutil.copy2(HERE/'text-questions.json',BOOK/'text-questions.json')
result={'units':report,'convertedPages':21,'preservedFields':len(after_fields),'preservedScripts':len(before['scripts']),'preservedAudio':len(before['audio']),'main':str(MAIN)}
(QA/'integration-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='units'},ensure_ascii=False))
