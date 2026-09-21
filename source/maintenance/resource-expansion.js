(()=>{'use strict';
const catalog=__CATALOG__;
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
let filter='all';
function filterCards(){let n=0;const q=$('#res-search').value.trim().toLowerCase();$$('.res-card').forEach(c=>{const matches=filter==='all'||(filter==='current'?c.dataset.resCurrent==='true':c.dataset.resSection===filter);c.hidden=!(matches&&(!q||c.textContent.toLowerCase().includes(q)));if(!c.hidden)n++;});$('#res-count').textContent='显示 '+n+' / '+catalog.length+' 个教学单元';$('#res-empty').hidden=n>0;$$('[data-res-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.resFilter===filter)));}
function records(){const learned=[],reviews=[];for(const c of catalog){if($('[data-save="resource-learned-'+c.id+'"]')?.checked)learned.push(c);if($('[data-save="resource-review-'+c.id+'"]')?.checked)reviews.push(c);}
function list(id,arr,empty){const node=$(id);node.replaceChildren();if(!arr.length){const li=document.createElement('li');li.textContent=empty;node.append(li);}for(const c of arr){const li=document.createElement('li'),a=document.createElement('a');a.href='#'+c.anchor;a.textContent=c.title;li.append(a);node.append(li);}}
list('#res-learned-list',learned,'还未标记已学；打开新资源，学习后按需要记录。');list('#res-review-list',reviews,'在任意新增单元勾选“加入我的复习”，这里会保留入口。');$('#res-progress').textContent='新增资源已学 '+learned.length+' / '+catalog.length+'；加入复习 '+reviews.length+' 项。两项分别记录，不计入原五章首次作答。';
const count=$$('[data-save^="topic-read-"]').filter(x=>x.checked).length;const el=$('#record-topics');if(el){el.replaceChildren(document.createTextNode(count+' '));const small=document.createElement('small');small.textContent='/ 18 段';el.append(small);}}
function route(){const hash=decodeURIComponent(location.hash.slice(1));if(hash==='resource-update'){$('#current-page-label').textContent='本季题目与新增资源';document.title='本季题目与新增资源 · IELTS Work';}if(hash==='resource-new-list'){location.hash='resource-update';requestAnimationFrame(()=>$('#resource-new-list').scrollIntoView({block:'start'}));}records();}
document.addEventListener('input',e=>{if(e.target.id==='res-search')filterCards();if(e.target.matches('[data-save]'))requestAnimationFrame(records);});
document.addEventListener('click',e=>{const b=e.target.closest('[data-res-filter]');if(b){filter=b.dataset.resFilter;filterCards();}if(e.target.closest('[data-res-scroll-new]'))requestAnimationFrame(()=>$('#resource-new-list').scrollIntoView({block:'start'}));const a=e.target.closest('a[href^="#"]');if(a){const target=document.getElementById(a.getAttribute('href').slice(1));if(target?.classList.contains('res-unit')){target.open=true;requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));}}});
window.addEventListener('hashchange',route);filterCards();route();
})();
