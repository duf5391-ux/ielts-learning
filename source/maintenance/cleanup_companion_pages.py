from pathlib import Path
from bs4 import BeautifulSoup
import shutil,json,re,datetime

root=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
work=Path('C:/Users/Admin1/Documents/ChatGPT/ielts')
backup=work/'backups'/('cleanup-companion-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
names=['完整词汇来源库.html','词频与原文证据.html','扩展资料目录.html']
report={'backup':str(backup),'files':[]}

def change(node,text):
 node.clear();node.append(text)

for name in names:
 path=root/name
 shutil.copy2(path,backup/name)
 before=path.read_text(encoding='utf8')
 soup=BeautifulSoup(before,'html.parser')
 oldlinks=[a.get('href') for a in soup.select('a[href]') if not a.get('href','').startswith('http')]
 oldaudio=[a.get('src') for a in soup.select('audio')]
 if name=='完整词汇来源库.html':
  for n in soup.select('title,h1'):change(n,'词汇与表达 · 完整词库')
  change(soup.select_one('.scope'),'查找单词、短语、搭配和词族，按词表或词条类型筛选，结合原表与词典学习。')
  soup.select_one('#source')['aria-label']='词表'
  change(soup.select_one('#source option'),'全部词表')
  soup.select_one('#unit')['aria-label']='词条类型'
  change(soup.select_one('a[download]'),'下载完整词库')
  soup.select_one('.note').decompose()
  script=soup.script.string
  marker='const $=s=>document.querySelector(s)'
  i=script.index(marker)
  raw_data=script[:i]
  tail=script[i:]
  labels={'oxford-core':'核心词汇（按词性）','oxford3000-pdf':'基础词汇','oxford5000-extra-pdf':'进阶词汇','oxford-phrases':'常用短语','opal-written-words':'学术写作词汇','opal-spoken-words':'学术口语词汇','opal-written-phrases':'学术写作短语','opal-spoken-phrases':'学术口语短语','awl':'学术词族','acl-v3-2026':'学术搭配（2026）','acl-v2-2025':'学术搭配（2025）','avl-core':'学术核心词汇','avl-families':'学术词族成员'}
  tail='const sourceLabels='+json.dumps(labels,ensure_ascii=False)+';\n'+tail
  tail=tail.replace("o.textContent=key+' · '+sources[key].records", "o.textContent=(sourceLabels[key]||key)+' · '+sources[key].records")
  tail=tail.replace("filtered.length+' 条来源记录（库内共 '+data.length+' 条）'", "filtered.length+' 条词条（库内共 '+data.length+' 条）'")
  a=tail.index("return '<article><h2>'")
  b=tail.index("}).join('')",a)
  tail=tail[:a]+'''return '<article><h2>'+esc(r.text)+'</h2>'+((r.pos||r.cefr)?'<p class="meta">'+[r.pos,r.cefr?String(r.cefr).toUpperCase():null].filter(Boolean).map(esc).join(' · ')+'</p>':'')+(r.family?'<p>词族：'+esc(r.family)+'</p>':'')+(r.members?.length?'<p>词族成员：'+esc(Array.isArray(r.members)?r.members.join(', '):r.members)+'</p>':'')+(r.function?'<p>'+esc(r.function)+'</p>':'')+'<div class="tags"><a target="_blank" href="'+esc(s.href+(r.page?'#page='+r.page:''))+'">打开词表</a><a target="_blank" rel="noopener" href="https://dictionary.cambridge.org/dictionary/english/'+encodeURIComponent(r.text.trim().replace(/\\s+/g,'-'))+'">查词典</a></div></article>' '''+tail[b:]
  tail=tail.replace('取消来源筛选','取消词表筛选')
  script=soup.script
  script.string=raw_data+tail
  assert str(script.string).startswith(raw_data)
 elif name=='词频与原文证据.html':
  for n in soup.select('title,h1'):change(n,'词频与原文例句')
  change(soup.select_one('.scope'),'按阅读、听力或练习原文查词频，点击词形查看它在句子里的用法。use、used 等词形分别统计。')
  change(soup.select_one('main > p.meta'),'出现篇数是包含该词的文章数量；总次数是该词在这些文章中出现的次数。')
  change(soup.select_one('a[download]'),'下载词频与原文')
  for n in soup.select('th'):
   if n.get_text()=='备注':change(n,'词类')
  script=soup.script.string
  marker='const $=s=>document.querySelector(s)'
  i=script.index(marker)
  raw_data=script[:i];tail=script[i:]
  tail=tail.replace("o.textContent=g.label", "o.textContent=g.label.replace(/真题[／/]官方样题|真题与官方样题/g,'练习原文').replace(/官方/g,'')")
  tail=tail.replace("+' · 出处</h2>'", "+' · 原文例句</h2>'")
  tail=tail.replace("'<div class=\"quote\"><b>'+esc(d.title)+'</b><p class=\"meta\">原 PDF 页：'+esc((d.pages||[]).join(', ')||'见来源清单')+'</p><p>'", "'<div class=\"quote\"><b>'+esc(d.title)+'</b><p>'")
  tail=tail.replace('查看完整统计正文','阅读全文').replace('打开原 PDF','打开 PDF').replace('常见功能词（保留）','常见功能词')
  soup.script.string=raw_data+tail
  assert str(soup.script.string).startswith(raw_data)
 else:
  change(soup.select_one('header p'),'阅读、听力、写作和口语专项资料，含 135 份 PDF 与 24 段配套音频。按科目或用途筛选，打开文件即可练习。')
  overview=[('135','PDF 资料'),('32','四科教学教案'),('24','配套音频'),('727','资料页数')]
  for node,(count,label) in zip(soup.select('.overview > div'),overview):
   change(node.b,count);change(node.span,label)
  for n in soup.select('#kind option,.meta'):
   if '官方样题附件' in n.get_text():change(n,n.get_text().replace('官方样题附件','样题练习'))
  for card in soup.select('article'):
   skill=card['data-skill'];kind=card['data-kind'];p=card.find('p',recursive=False)
   title=card.h2.get_text().lower()
   if kind=='ielts_sample':
    desc='练习答案，用于作答后核对。' if 'answer' in title else '听力文字稿，用于听后核对与跟读。' if 'transcript' in title else '题型专项练习。'
   elif kind=='ielts_teaching':desc={'reading':'阅读题型讲解与专项练习。','listening':'听力题型讲解与专项练习。','writing':'写作结构、表达讲解与专项练习。','speaking':'口语回答方法与开口练习。'}[skill]
   else:desc={'reading':'阅读理解与话题表达积累。','listening':'听力理解与听后文本核对。','writing':'写作结构与表达练习。','speaking':'对话句型与开口练习。'}[skill]
   if p:change(p,desc)
  for a in soup.select('.links a'):
   if a.get('href','').startswith(('http://','https://')):a.decompose()
  for label in soup.select('.audio label'):change(label,'配套音频')
  if soup.footer:soup.footer.decompose()
  soup.script.string=soup.script.string.replace("n+' 份 PDF 资料 · 配套音频归在同一卡片；文件数不等于练习篇数'", "n+' 份 PDF 资料'")
 after=str(soup)
 path.write_text(after,encoding='utf8')
 check=BeautifulSoup(after,'html.parser')
 assert [a.get('href') for a in check.select('a[href]') if not a.get('href','').startswith('http')]==oldlinks
 assert [a.get('src') for a in check.select('audio')]==oldaudio
 scriptpaths=[]
 for i,s in enumerate(check.select('script')):
  target=work/('cleanup-companion-script-'+str(names.index(name))+'-'+str(i)+'.js')
  target.write_text(s.string or s.get_text(),encoding='utf8');scriptpaths.append(str(target))
 visible=check.get_text(' ',strip=True)
 report['files'].append({'file':str(path),'local_links_preserved':len(oldlinks),'audio_preserved':len(oldaudio),'scripts':scriptpaths,'remaining_metadata_visible':re.findall('官方|来源|核验|出处|哈希|SHA-256',visible)})

report['main_page_recommendations']={'remove':['details.tv-source','details.enrichment-sources','p.enrichment-origin','details whose direct summary is 资源出处与原件 / 话题来源与核验说明','resource-update source registration detail blocks'],'rewrite':['.res-meta: retain teaching content type, remove provenance and verification process','.authentic-content > p.small: retain article title or useful page locator only','.res-badge: retain date and content type only'],'preserve':['income/risk/material source wording in teaching','reading evidence and answer explanations','practice conditions and review metadata']}
(work/'cleanup-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
