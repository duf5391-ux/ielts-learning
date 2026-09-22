"""Product reliability repairs. Parent owns navigation, formal install and publication."""
from pathlib import Path
from collections import Counter
import hashlib, json, re
from bs4 import BeautifulSoup

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MARK='product-reliability-20260922'

def apply(page):
    if f'id="{MARK}"' in page:return page
    before=BeautifulSoup(page,'html.parser')
    s=BeautifulSoup(page,'html.parser')
    for name in ['lookup-controller','vocabulary-review-controller','selection-tools-script']:
        assert s.find(id=name),name
        s.find(id=name).string=(HERE/(name+'.js')).read_text(encoding='utf8')
    catalog=json.loads(s.find(id='learning-adjust-data').string)
    for u in catalog['units']:
        uid=u['id']
        if uid=='speaking-first':
            u['steps']=[dict(kind='saved-first',key='speaking')];u['progressLabel']='首答已保存'
        elif uid.startswith('pr-speaking-p'):
            u['steps']=[dict(kind='any-answer',keys=[uid+'-record-note'])];u['progressLabel']='作答已记录'
        elif uid.startswith('speaking-new-sep26-'):
            unit=s.find(id=uid);assert unit
            fragment=BeautifulSoup(f'''<section class="product-speaking-response" id="{uid}-response"><h4>先留下自己的回答</h4><p>可以直接开口，也可以先写文字草稿；录音和文字任选一种。参考内容在后面，按需查看。</p><div class="recorder" data-recorder="{uid}"><button type="button" data-record="{uid}">开始录音</button><button type="button" data-stop="{uid}" disabled>结束并保留</button><a data-download="{uid}" hidden>下载录音</a><audio controls data-preview="{uid}" hidden preload="none"></audio><label class="audio-import">载入已有录音<input type="file" accept="audio/*" data-upload="{uid}"/></label><p class="small" data-rec-status="{uid}">录音按题保存在本浏览器；换设备请下载音频，文字备份不包含声音。</p></div><input type="hidden" data-save="{uid}-audio-saved"/><label class="field"><span>文字草稿（可选）</span><textarea rows="3" data-save="{uid}-draft" placeholder="不便录音时，先把自己的回答写在这里。"></textarea></label></section>''','html.parser')
            content=unit.select_one('.remediated-teaching');assert content
            prompt=content.find(['ol','ul'])
            if prompt:prompt.insert_after(fragment)
            else:
                h=content.find(['h4','h3']);h.insert_after(fragment)
            u['steps']=[dict(kind='any-answer',keys=[uid+'-draft',uid+'-audio-saved'])]
            u['progressLabel']='作答已记录'
    s.find(id='learning-adjust-data').string=json.dumps(catalog,ensure_ascii=False,separators=(',',':'))
    js=str(s.find(id='learning-adjust-script').string)
    old="s.kind === 'checked' ? !!state.checked[s.key] : s.kind === 'check' ? value(s.key) === true : M.filled(value(s.key))"
    new="s.kind === 'saved-first' ? savedFirst(s.key) : s.kind === 'any-answer' ? s.keys.some(k=>savedAnswer(k)) : "+old
    assert old in js
    js=js.replace(old,new)
    marker='  function unitProgress(u)'
    assert marker in js
    js=js.replace(marker,"  function savedFirst(key){try{return !!JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'{}').snapshots?.[key]?.at;}catch{return false;}}\n  function savedAnswer(key){try{return M.filled(JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'{}').fields?.[key]);}catch{return false;}}\n"+marker)
    js=js.replace("  document.addEventListener('ielts-record-committed',()=>queueViews());","  document.addEventListener('ielts-record-committed',()=>queueViews());\n  document.addEventListener('click',event=>{if(event.target.closest('[data-freeze]'))queueViews();});")
    s.find(id='learning-adjust-script').string=js
    style=s.new_tag('style',id=MARK)
    style.string='''.sentence-source-highlight{background:#fff2b7!important;outline:2px solid #b79536;outline-offset:5px;scroll-margin-block:100px}.sentence-return-bar{padding:10px 14px;margin:10px 0;background:#edf4e9;border-radius:10px;font-size:14px}.product-speaking-response{border:1px solid #cddac9;border-radius:14px;padding:16px;margin:18px 0}.product-speaking-response .recorder{margin:10px 0}.product-speaking-response audio{width:100%;max-width:480px}.recorder [data-audio-history]{display:block;width:100%;max-width:480px;margin:8px 0;min-height:44px}.tv-card input[data-save^="topic-vocab-star-"]{min-width:22px;min-height:22px}.tv-card label:has(input[data-save^="topic-vocab-star-"]){display:inline-flex;align-items:center;min-height:44px}@media(max-width:600px){.product-speaking-response{padding:12px}.product-speaking-response button{min-height:44px}.st-sentence> a{display:block;padding:10px 0}}'''
    s.head.append(style)
    page=str(s)
    start,end='/*SPEAKING-RECORDER-FIX:START*/','/*SPEAKING-RECORDER-FIX:END*/'
    assert page.count(start)==1 and page.count(end)==1
    page=re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda m:start+'\n'+(HERE/'speaking-recorder.js').read_text(encoding='utf8')+'\n'+end,page,flags=re.S)
    after=BeautifulSoup(page,'html.parser')
    fields=lambda d:Counter((e['data-save'],e.name,e.get('type',''),e.get('value',''),e.get_text()) for e in d.select('[data-save]'))
    assert fields(before)<=fields(after)
    assert Counter(e['id'] for e in before.select('[id]'))<=Counter(e['id'] for e in after.select('[id]'))
    for id in ['record-concurrency-model-script','health-study-ui-script','health-study-bridge-script','energy-control-script','daily-study-script','daily-study-model-script']:
        assert str(before.find(id=id))==str(after.find(id=id)),id
    return page

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--input',default=str(ROOT/'architecture-repair-20260921/combined.html'));p.add_argument('--output',default=str(HERE/'candidate.html'));a=p.parse_args()
    source=Path(a.input);target=Path(a.output);assert source.resolve()!=target.resolve()
    page=apply(source.read_text(encoding='utf8'));assert apply(page)==page;target.write_text(page,encoding='utf8')
    report={'baseline':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate':hashlib.sha256(target.read_bytes()).hexdigest(),'fields':len(BeautifulSoup(page,'html.parser').select('[data-save]')),'scope':['02','03','14','15'],'navigationChanged':False,'recordingStorage':'IndexedDB, per-task append-only takes; JSON backup excludes audio'}
    (HERE/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
