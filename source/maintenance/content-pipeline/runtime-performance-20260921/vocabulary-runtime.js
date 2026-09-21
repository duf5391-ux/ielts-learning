(()=>{'use strict';
// RUNTIME-PERFORMANCE-V1: keep every saved control; build the search index in small batches.
const $=s=>document.querySelector(s),root=$('#topical-vocabulary');
const cards=[...root.querySelectorAll('.tv-card')],index=[],size=25;
const search=$('#tv-search'),topic=$('#tv-topic'),status=$('#tv-status');
const count=$('#tv-count'),pageLabel=$('#tv-page'),prev=$('#tv-prev'),next=$('#tv-next'),empty=$('#tv-empty');
let page=0,found=[],shown=[],ready=false,ticket=0,queued=false;
root.setAttribute('aria-busy','true');prev.disabled=next.disabled=true;empty.hidden=true;
count.textContent='正在准备词汇…';pageLabel.textContent='';
function active(){let hash;try{hash=decodeURIComponent(location.hash.slice(1));}catch{return false;}const n=document.getElementById(hash);return n===root||!!(n&&root.contains(n));}
function draw(){
  page=Math.max(0,Math.min(page,Math.max(0,Math.ceil(found.length/size)-1)));
  const rows=found.slice(page*size,(page+1)*size),visible=new Set(rows.map(r=>r.el));
  for(const node of shown)if(!visible.has(node))node.hidden=true;
  for(const row of rows)if(row.el.hidden)row.el.hidden=false;
  shown=rows.map(r=>r.el);
  count.textContent=found.length+' 条匹配 · 共 '+cards.length+' 条';
  pageLabel.textContent=(page+1)+' / '+Math.max(1,Math.ceil(found.length/size));
  prev.disabled=page===0;next.disabled=(page+1)*size>=found.length;empty.hidden=found.length>0;
}
function filter(){
  if(!ready){schedule(true);return;}
  const q=search.value.trim().toLowerCase(),t=topic.value,s=status.value;
  found=index.filter(r=>(t==='all'||t===r.topic)&&(!q||r.text.includes(q))&&(s==='all'||(s==='saved'&&r.star.checked)||(s==='new'&&!r.level.value)||r.level.value===s));
  page=0;draw();
}
function batch(deadline){
  let processed=0;
  while(index.length<cards.length&&processed<50){
    if(processed>0&&deadline&&!deadline.didTimeout&&deadline.timeRemaining()<2)break;
    const el=cards[index.length];el.hidden=true;
    const parts=el.querySelectorAll('h3,.tv-meaning,.tv-chunk,input,select');
    let star,level;const words=[];
    for(const part of parts){if(part.tagName==='INPUT')star=part;else if(part.tagName==='SELECT')level=part;else words.push(part.textContent);}
    index.push({el,topic:el.dataset.tvTopic,text:words.join(' ').toLowerCase(),star,level});processed++;
  }
  if(index.length===cards.length){ready=true;filter();root.dataset.tvReady='true';root.setAttribute('aria-busy','false');}
  else{if(active())count.textContent='正在准备词汇… '+index.length+' / '+cards.length;schedule();}
}
function schedule(urgent=false){
  if(ready||(queued&&!urgent))return;
  const own=++ticket;queued=true;
  const work=deadline=>{if(own!==ticket||ready)return;queued=false;batch(deadline);};
  if(urgent||active())requestAnimationFrame(()=>work(null));
  else if(window.requestIdleCallback)window.requestIdleCallback(work,{timeout:1500});
  else setTimeout(()=>work(null),80);
}
for(const control of [search,topic,status])control.addEventListener('input',filter);
prev.onclick=()=>{if(!ready||prev.disabled)return;page--;draw();root.scrollIntoView({block:'start'});};
next.onclick=()=>{if(!ready||next.disabled)return;page++;draw();root.scrollIntoView({block:'start'});};
root.addEventListener('change',e=>{
  if(!e.target.closest('.tv-card'))return;
  if((e.target.tagName==='INPUT'&&status.value==='saved')||(e.target.tagName==='SELECT'&&!['all','saved'].includes(status.value)))filter();
});
document.addEventListener('ielts-record-committed',()=>{if(ready&&status.value!=='all')filter();});
$('#import-state')?.addEventListener('change',()=>setTimeout(filter,300));
window.addEventListener('hashchange',()=>{if(active()&&!ready)schedule(true);});
schedule(active());
})();
