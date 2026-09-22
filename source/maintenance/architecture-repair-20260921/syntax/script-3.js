(()=>{'use strict';
 const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
 const chapters=['reading','listening','writing1','writing2','speaking'];
 const names={guide:'学习首页',background:'话题背景',vocabulary:'词汇与表达',reading:'阅读',listening:'听力',writing1:'写作 · Task 1',writing2:'写作 · Task 2',speaking:'口语',plan:'学习安排',records:'学习记录',library:'资源目录',materials:'新增资料'};
 function stored(){try{const s=JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'{}');return {fields:s.fields||{},snapshots:s.snapshots||{}}}catch{return {fields:{},snapshots:{}}}}
 function message(text){const box=$('#toast');box.textContent=text;box.hidden=false;clearTimeout(message.timeout);message.timeout=setTimeout(()=>box.hidden=true,4000)}
 function setMenu(open){document.body.classList.toggle('nav-open',open);$('#mobile-menu').setAttribute('aria-expanded',String(open));$('.nav-scrim').hidden=!open;if(open)$('.sidebar nav button[aria-current="page"]')?.focus();}
 $('#mobile-menu').addEventListener('click',()=>setMenu(!document.body.classList.contains('nav-open')));
 $('.nav-scrim').addEventListener('click',()=>setMenu(false));
 document.addEventListener('keydown',e=>{if(!document.body.classList.contains('nav-open'))return;if(e.key==='Escape'){setMenu(false);$('#mobile-menu').focus()}if(e.key==='Tab'){const nodes=$$('.sidebar a,.sidebar button').filter(el=>el.getClientRects().length),first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}});
 document.addEventListener('click',e=>{if(e.target.closest('.sidebar [data-go],.sidebar a'))setMenu(false)});
 const articleNodes=$$('#background .topic-reader,#background .personal-reader');
 function backgroundView(hash){
   const catalog=$('.topic-catalog');const header=$('#background>.chapter-head');const isCatalog=hash==='background'||!hash.startsWith('topic-');
   catalog.classList.toggle('ui-filtered',!isCatalog);header.classList.toggle('ui-filtered',!isCatalog);
   articleNodes.forEach(n=>n.classList.add('ui-filtered'));
   $$('#background .topic-extension').forEach(n=>{n.classList.add('ui-filtered');n.classList.remove('ui-single')});
   if(!isCatalog){const target=document.getElementById(hash);if(target){target.classList.remove('ui-filtered');const extension=target.closest('.topic-extension');if(extension){extension.classList.remove('ui-filtered');if(target!==extension)extension.classList.add('ui-single');else extension.querySelectorAll('.personal-reader').forEach(a=>a.classList.remove('ui-filtered'));}requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'instant'}));}}
 }
 let vocabFilter='all';const cards=$$('.word-card,.usage-card');
 const extraVocab=$$('#vocabulary [data-enrichment]'),extraVocabSection=$('#vocabulary .enrichment-section');
 if(extraVocabSection){$('.vocab-toolbar').after(extraVocabSection);const b=document.createElement('button');b.dataset.vocabFilter='practice';b.setAttribute('aria-pressed','false');b.textContent='搭配练习 '+extraVocab.length;$('.filter-tabs').insertBefore(b,$('[data-vocab-filter="saved"]'));$('[data-vocab-filter="all"] span').textContent=String(cards.length+extraVocab.length);}
 function filterVocabulary(){const q=$('#vocab-search').value.trim().toLowerCase();let words=0,uses=0;
   for(const card of cards){const isWord=card.classList.contains('word-card'),saved=card.querySelector('.bookmark input').checked;const matchType=vocabFilter==='all'||(vocabFilter==='words'&&isWord)||(vocabFilter==='usage'&&!isWord)||(vocabFilter==='saved'&&saved);const visible=matchType&&(!q||card.textContent.toLowerCase().includes(q));card.classList.toggle('ui-filtered',!visible);if(visible){if(isWord)words++;else uses++;}}
   let extras=0;for(const card of extraVocab){const saved=card.querySelector('.bookmark input').checked,match=vocabFilter==='all'||vocabFilter==='practice'||(vocabFilter==='saved'&&saved),visible=match&&(!q||card.textContent.toLowerCase().includes(q));card.classList.toggle('ui-filtered',!visible);if(visible)extras++;}if(extraVocabSection)extraVocabSection.classList.toggle('ui-filtered',!extras);
   $('#core-words').classList.toggle('ui-filtered',!words);$('.word-grid').classList.toggle('ui-filtered',!words);$('#usage-cards').classList.toggle('ui-filtered',!uses);$('#usage-cards').nextElementSibling.classList.toggle('ui-filtered',!uses);$('.usage-grid').classList.toggle('ui-filtered',!uses);$('#vocab-empty').hidden=!!(words+uses+extras);$('#vocab-result').textContent=(words+uses+extras)+' 项内容'+(extras?' · 含 '+extras+' 组搭配练习':'')+(q?' · 已按关键词筛选':'');
   $$('[data-vocab-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.vocabFilter===vocabFilter)));
 }
 $$('[data-vocab-filter]').forEach(b=>b.addEventListener('click',()=>{vocabFilter=b.dataset.vocabFilter;filterVocabulary()}));$('#vocab-search').addEventListener('input',filterVocabulary);
 $$('.bookmark input').forEach(c=>c.addEventListener('change',filterVocabulary));
 $('#library-search').addEventListener('input',()=>{const q=$('#library-search').value.trim().toLowerCase();let n=0;$$('.source-file').forEach(a=>{const visible=a.textContent.toLowerCase().includes(q);a.classList.toggle('ui-filtered',!visible);if(visible)n++});$('#library-empty').hidden=!!n});
 function updateProgress(){const s=stored(),entries=Object.entries(s.fields),n=chapters.filter(c=>s.snapshots[c]).length;$('#home-count').textContent=n+' / 5';$('#home-progress').style.width=n*20+'%';$('#record-total').replaceChildren(document.createTextNode(String(n)+' '));const totalSmall=document.createElement('small');totalSmall.textContent='/ 5 章';$('#record-total').append(totalSmall);
   const setCount=(id,num,suffix)=>{const el=$(id);el.replaceChildren(document.createTextNode(String(num)+' '));const small=document.createElement('small');small.textContent=suffix;el.append(small)};
   const readCount=$$('[data-save^="topic-read-"]').filter(el=>el.checked).length;const savedCount=$$('.bookmark input,.tv-star input').filter(el=>el.checked).length;setCount('#record-topics',readCount,'/ 18 段');setCount('#record-saved',savedCount,'条内容');
   for(const cid of chapters){const done=!!s.snapshots[cid];const raw=s.fields[cid+'-minutes'];const meaningful=entries.some(([k,v])=>k.startsWith(cid+'-')&&/-q\d+$|-essay$|-record-note$/.test(k)&&String(v).trim());const label=done?'首次稿已保留':meaningful?'正在作答':'待开始';const state=$(`[data-chapter-state="${cid}"]`);state.textContent=label;state.classList.toggle('has-answer',done);$(`[data-record-status="${cid}"]`).textContent=label;$(`[data-record-minutes="${cid}"]`).textContent=raw!==undefined&&raw!==''?raw+' 分钟':'未记录用时';
     for(const a of $$(`#${cid} .chapter-outline [data-stage]`)){const locked=['learn','feedback'].includes(a.dataset.stage)&&!done;a.classList.toggle('is-locked',locked);a.setAttribute('aria-disabled',String(locked));}}
   $$('[data-read-status]').forEach(el=>{const input=$(`[data-save="topic-read-${el.dataset.readStatus}"]`);el.textContent=input?.checked?'已读过':'未标记'});
   const active=chapters.find(c=>!s.snapshots[c]&&entries.some(([k,v])=>k.startsWith(c+'-')&&/-q\d+$|-essay$|-record-note$/.test(k)&&String(v).trim()));
   const link=$('#next-link');if(active){$('#next-title').textContent='接着完成这份答案';$('#next-description').textContent=names[active]+'里已经有你的作答，继续时可以先回看。';link.firstChild.textContent='继续'+names[active]+' ';link.href='#'+active;}else if(n){$('#next-title').textContent='回看一次，修好一处';$('#next-description').textContent='已经保留了 '+n+' 份首次作答。回到自己的答案，挑一处具体问题修订。';link.firstChild.textContent='查看学习记录 ';link.href='#records';}else{document.getElementById('next-title').textContent='这一轮，从背景开始';document.getElementById('next-description').textContent='选一个熟悉的主题，看看意思如何组织成自然的英语。';link.firstChild.textContent='选一个话题 ';link.href='#background';}
 }
 function onRoute(){document.getElementById("toast").hidden=true;const hash=decodeURIComponent(location.hash.slice(1))||'study';let pageId=document.getElementById(hash)?.closest('main>.panel')?.id||hash;$('#current-page-label').textContent=names[pageId]||'学习首页';document.title=(names[pageId]||'学习首页')+' · IELTS Work';backgroundView(hash);if(pageId==='vocabulary'){vocabFilter='words';$('#vocab-search').value='';filterVocabulary();}if(pageId==='phrases'){vocabFilter='usage';$('#vocab-search').value='';filterVocabulary();}if(pageId==='vocabulary'&&(hash==='usage-cards'||hash==='core-words')){vocabFilter=hash==='usage-cards'?'usage':'words';$('#vocab-search').value='';filterVocabulary();requestAnimationFrame(()=>document.getElementById(hash)?.scrollIntoView({behavior:'instant',block:'start'}));}
   $$('.chapter-outline a').forEach(a=>a.classList.toggle('is-current',a.hash==='#'+hash||(hash===pageId&&a.hash==='#'+pageId+'-first')));updateProgress();}
 document.addEventListener('click',e=>{const a=e.target.closest('.chapter-outline a.is-locked');if(a){e.preventDefault();message('先保留本章的首次作答，再进入学习与反馈。');}if(e.target.closest('[data-freeze]'))queueProgress();});
 let progressPending=false;function queueProgress(){if(progressPending)return;progressPending=true;requestAnimationFrame(()=>{progressPending=false;updateProgress();});}
 document.addEventListener('input',e=>{if(e.target.dataset.save)queueProgress();});
 window.addEventListener('hashchange',onRoute);filterVocabulary();onRoute();
})();



