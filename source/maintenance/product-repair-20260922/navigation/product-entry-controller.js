(() => {
  'use strict';
  const $=s=>document.querySelector(s);
  const nav=$('#product-mobile-nav');
  $('#product-more').addEventListener('click',()=>$('.mobile-menu')?.click());
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
    let id=panel.id;
    if(['study','practice'].includes(id)){}else if(!['vocabulary-review','word-review','sentence-learning'].includes(id))id='product-more';
    for(const a of nav.children){const active=a.id===id||a.getAttribute('href')==='#'+id;if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
    try{
      const state=JSON.parse($('#learning-adjust-state').value||'{}');
      $('#product-plan-link').textContent='自选清单'+(state.today?.length?' · '+state.today.length+' 项':'')+' →';
      $('#la-resume').hidden=!state.last;
      const daily=JSON.parse($('#daily-study-state').value||'{}');
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
