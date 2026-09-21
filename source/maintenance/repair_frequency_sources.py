"""Complete existing corpus provenance. Never change corpus bodies or word counts."""
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
from urllib.parse import quote
import json, hashlib, re, shutil, argparse

ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
EXTRA=Path('D:/Codex-IELTS-2026-09-14/expansion-2026-09-14')
OUT=Path('D:/IELTS-Work/content-repair-20260920')

def apply(data):
    before=json.loads(json.dumps(data))
    additions=[]
    exam={i for row in data['groups']['exam']['items'] for i in row['document_ids']}
    handoff={i['id']:i for i in json.loads((EXTRA/'verified-reading-handoff-index.json').read_text(encoding='utf8'))}
    mappings={
      'cambridge21-academic-':'8ee8170c-Cambridge IELTS 21 - Academic.pdf',
      'ielts-modified-academic-':'188a4619-ielts-academic-reading-access-arrangement-modified-large-print-text-booklet.pdf',
      'official-sample-idp-29':'5856a161-idp-29.pdf',
      'official-sample-idp-31':'326008c2-idp-31.pdf',
      'official-sample-idp-32':'frequency-idp-32.pdf',
      'official-practice-2007-spider-silk':'frequency-cambridge-collected-papers-34.pdf',
      'hwatai-cambridge5-sample':'e0428977-hwatai-cambridge5-sample.pdf',
      'hwatai-cambridge6-sample':'ad0a33c0-hwatai-cambridge6-sample.pdf',
      'hwatai-cambridge7-sample':'237b7194-hwatai-cambridge7-sample.pdf',
      'hwatai-cambridge8-sample':'d04994b0-hwatai-cambridge8-sample.pdf',
      'hwatai-cambridge10-sample':'99437c83-hwatai-cambridge10-sample.pdf',
      'official-cambridge-classroom-health':'dfacdd41-cambridge-classroom-reading-3.pdf',
      'official-cambridge-research68-film-sound':'04f17772-cambridge-research-notes68.pdf'
    }
    for src,name in [('idp-32.pdf','frequency-idp-32.pdf'),('cambridge-collected-papers-34.pdf','frequency-cambridge-collected-papers-34.pdf')]:
        additions.append((EXTRA/src,BOOK/'原始参考'/name))
    evidence=[];readers={}
    normalize=lambda x:re.sub(r'[^a-z0-9]','',x.lower())
    for ident in sorted(exam):
        d=data['documents'][ident]
        if ident.startswith('official-inspera'):
            d['source_url']=handoff[ident]['source_url']
            local=EXTRA/Path(handoff[ident]['source_file']).name
            assert local.is_file()
            assert normalize(d['title']) in normalize(local.read_text(encoding='utf8')),(ident,'Title not in archived source')
            d['source_kind']='web'
            evidence.append({'id':ident,'source':d['source_url'],'archive':str(local),'titleMatched':True})
        else:
            matches=[fn for prefix,fn in mappings.items() if ident.startswith(prefix)]
            assert len(matches)==1,ident
            rel='原始参考/'+matches[0];p=BOOK/rel
            actual=next((src for src,target in additions if target==p),p)
            if actual not in readers:readers[actual]=PdfReader(actual)
            doc=readers[actual];text=' '.join(doc.pages[n-1].extract_text() for n in d['pages'])
            # Article titles occasionally contain editorial prefixes; use a verified distinctive phrase.
            title=d['title'].replace('Book review: ','')
            aliases={'official-sample-idp-29':'agriculture','official-sample-idp-31':'smoking','official-sample-idp-32':'motor','cambridge21-academic-t1-p3':'world of sugar','official-cambridge-classroom-health':'The concept of health holds different meanings'}
            needle=aliases.get(ident,title)
            visual=ident=='official-cambridge-research68-film-sound'
            if visual:
                # Source page is a rotated image. Root inspected this existing page render.
                assert d['pages']==[30] and 'Appendix 5' in text
                assert (EXTRA/'research68-reading-30.png').is_file()
            else:assert normalize(needle) in normalize(text),(ident,needle,'Page/source mismatch')
            d['pdf_href']=rel;d['source_kind']='pdf'
            if ident in handoff:d['source_url']=handoff[ident].get('source_url')
            if ident=='official-practice-2007-spider-silk':d['source_url']='https://www.cambridgeenglish.org/Images/735098-studies-in-language-testing-volume-34.pdf'
            evidence.append({'id':ident,'source':rel,'pages':d['pages'],'titleMatched':True,'method':'Visual review of research68-reading-30.png' if visual else 'PDF text/title or distinctive content match'})
        assert (BOOK/d['text_href']).is_file()
    assert before['groups']==data['groups']
    for ident,d in data['documents'].items():
        assert before['documents'][ident]['body']==d['body']
        assert before['documents'][ident]['pages']==d['pages']
    return data,additions,evidence

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    path=BOOK/'词汇数据/词频完整数据.json';page=BOOK/'词频与原文证据.html'
    before=path.read_text(encoding='utf8');html=page.read_text(encoding='utf8')
    data,assets,evidence=apply(json.loads(before))
    s=BeautifulSoup(html,'html.parser')
    script=max(s.select('script'),key=lambda n:len(n.get_text()))
    body=script.get_text();end=body.index(';const $=')
    js='const data='+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+body[end:]
    old="+(d.pdf_href?' · <a target=\"_blank\" href=\"'+esc(d.pdf_href+'#page='+(d.pages?.[0]||1))+'\">打开 PDF</a>':'')"
    new="+(d.pdf_href?' · <a target=\"_blank\" rel=\"noopener\" href=\"'+esc(d.pdf_href+'#page='+(d.pages?.[0]||1))+'\">原件 PDF · 第 '+esc(d.pages?.join('、')||1)+' 页</a>':'')+(d.source_url?' · <a target=\"_blank\" rel=\"noopener\" href=\"'+esc(d.source_url)+'\">官方来源'+(d.source_kind==='web'?'（网页题目可能更新）':'')+'</a>':'')"
    if old in js:js=js.replace(old,new)
    else:assert new in js
    script.string=js
    for n in list(s.select('[data-deep-audit-ui]')):n.decompose()
    for n in list(s.find_all(['aside','section','div'])):
        if n.find('script'):continue
        if '统计核验：达标' in n.get_text() and len(n.get_text())<1800:n.decompose()
    for a in list(s.select('a[href="词条逐项审核.html"]')):a.decompose()
    note=s.find(id='frequency-source-scope')
    if not note:
        note=s.new_tag('p',id='frequency-source-scope');s.find('h1').insert_after(note)
    note.string='频次只描述这里收录的文本：23 篇通用阅读、24 篇通用听力、27 篇考试与练习文本。TF 是出现次数，DF 是出现篇数；不同词形分别统计，不能据此推算考试出现概率。点击词形可回查统计正文及原件；4 篇网页材料保留文本快照，并链接原发布入口。'
    after=str(s);serialized=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'词频与原文-reviewed.html').write_text(after,encoding='utf8')
    (OUT/'frequency-repaired.json').write_text(serialized,encoding='utf8')
    if args.write:
        for src,target in assets:
            if target.exists():assert target.read_bytes()==src.read_bytes()
            else:shutil.copy2(src,target)
        for p,oldtext,newtext in [(path,before,serialized),(page,html,after)]:
            if oldtext==newtext:continue
            backup=OUT/('before-frequency-'+p.name)
            if not backup.exists():backup.write_text(oldtext,encoding='utf8')
            tmp=p.with_suffix('.prereq.tmp');tmp.write_text(newtext,encoding='utf8')
            assert p.read_text(encoding='utf8')==oldtext,'Concurrent edit'
            tmp.replace(p)
    report={'stage':'written' if args.write else 'reviewed','documents':len(evidence),'pdfDocuments':sum('pages' in e for e in evidence),'webDocuments':sum('archive' in e for e in evidence),'wordCountsAndBodiesUnchanged':True,'evidence':evidence}
    (ROOT/'research/frequency-source-repair-20260920.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='evidence'},ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf8');main()
