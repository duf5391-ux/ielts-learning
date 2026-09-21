(()=>{'use strict';
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
let active='theme';
function filter(){
 const q=$('#background-search').value.trim().toLowerCase();let visible=0;
 $$('.background-library [data-background-kind]').forEach(card=>{const match=(active==='all'||card.dataset.backgroundKind===active)&&(!q||card.dataset.search.includes(q));card.hidden=!match;if(match)visible++;});
 $$('.background-filters button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.backgroundFilter===active)));
 $('#background-result-count').textContent='显示 '+visible+' 项';$('#background-empty').hidden=visible!==0;
}
function route(){
 const id=decodeURIComponent(location.hash.slice(1))||'guide';
 const catalog=id==='background'||!id.startsWith('topic-');
 $$('#background>[data-background-catalog-only]').forEach(n=>n.classList.toggle('ui-filtered',!catalog));
 const target=document.getElementById(id);
 if(target?.classList.contains('background-reader'))requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'instant'}));
}
$('#background-search').addEventListener('input',filter);
document.addEventListener('click',e=>{
 const tab=e.target.closest('[data-background-filter]');if(tab){active=tab.dataset.backgroundFilter;filter();}
 const jump=e.target.closest('[data-background-jump]');if(jump){const reader=jump.closest('.background-reader');const headings=reader.querySelectorAll('.background-lesson h3');headings[Number(jump.dataset.backgroundJump)]?.scrollIntoView({block:'start',behavior:'smooth'});}
});
window.addEventListener('hashchange',route);filter();route();
})();
