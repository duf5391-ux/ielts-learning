(() => {
  'use strict';
  const $=s=>document.querySelector(s);
  const nav=$('#product-mobile-nav');
  $('#product-more').addEventListener('click',()=>$('.mobile-menu')?.click());
  let wordSearch='',lastRoute='';
  document.addEventListener('click',event=>{
    if(event.target.closest('.product-content-title[href="#topical-vocabulary"]'))wordSearch=$('#la-study-search').value.trim();
  },true);
  function compactWords(){
    for(const card of document.querySelectorAll('.vr-list-card:not([data-product-compact])')){
      card.dataset.productCompact='true';
      const details=document.createElement('details');details.className='product-word-details';
      const summary=document.createElement('summary');summary.textContent='释义、原句与更多操作';details.append(summary);
      for(const child of [...card.children])if(!child.matches('.vr-card-heading,.vr-quick-marks'))details.append(child);
      card.append(details);
    }
  }
  function update(){
    const panel=$('main>.panel:not([hidden])');if(!panel)return;
    if(location.hash!==lastRoute){
      lastRoute=location.hash;
      if(lastRoute==='#topical-vocabulary')requestAnimationFrame(()=>requestAnimationFrame(()=>window.scrollTo({top:0,behavior:'instant'})));
    }
    if(location.hash==='#topical-vocabulary'&&wordSearch){
      const q=wordSearch.toLowerCase();wordSearch='';
      if([...document.querySelectorAll('.tv-card')].some(n=>n.textContent.toLowerCase().includes(q))){$('#tv-topic').value='all';$('#tv-status').value='all';$('#tv-search').value=q;$('#tv-search').dispatchEvent(new Event('input',{bubbles:true}));}
    }
    const wordRoutes=['vocabulary-review','word-review','sentence-learning','lookup-learning','review-history','word-library'];
    const title={'vocabulary-review':'单词 · 背单词','word-review':'单词 · 复习','sentence-learning':'单词 · 句子','lookup-learning':'单词 · 查词与历史','review-history':'单词 · 学习记录','word-library':'单词 · 已收录词语','writing-workbench':'写作训练'}[panel.id];
    if(title){$('#current-page-label').textContent=title;document.title=title+' · IELTS';}
    let id=panel.id;
    const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if(wordRoutes.includes(id)||target?.closest('#topical-vocabulary'))id='vocabulary-review';
    else if(!['study','practice','writing-workbench'].includes(id))id='product-more';
    for(const a of nav.children){const active=a.id===id||a.getAttribute('href')==='#'+id;if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
    try{
      const state=JSON.parse($('#learning-adjust-state').value||'{}');
      $('#product-plan-link').textContent='自选清单'+(state.today?.length?' · '+state.today.length+' 项':'')+' →';
      $('#la-resume').hidden=!state.last;
      const daily=JSON.parse($('[data-save="daily-study-state"]').value||'{}');
      const link=$('.product-today');link.textContent=daily.session&&daily.session.status!=='completed'?'每日安排 · 查看本次学习 →':'直接开始 · 安排一段学习 →';
    }catch{}
    compactWords();
  }
  document.addEventListener('product-route-ready',update);
  document.addEventListener('ielts-record-committed',update);
  window.addEventListener('hashchange',()=>requestAnimationFrame(update));
  document.addEventListener('focusin',event=>{if(event.target.matches('textarea,input:not([type=checkbox]):not([type=radio]),select'))document.body.classList.add('product-input-focused');});
  document.addEventListener('focusout',()=>requestAnimationFrame(()=>{if(!document.activeElement.matches('textarea,input:not([type=checkbox]):not([type=radio]),select'))document.body.classList.remove('product-input-focused');}));
  const list=$('#vr-list');if(list)new MutationObserver(compactWords).observe(list,{childList:true});
  update();
})();
