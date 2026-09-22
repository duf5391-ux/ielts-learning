(function(){
  'use strict';
  const field=document.getElementById('daily-study-state');
  function refresh(){
    let session=null;try{session=JSON.parse(field?.value||'null')?.session;}catch{}
    const active=session&&['active','paused'].includes(session.status);
    const current=active?session.steps[session.index]:null;
    const completedReadings=active?new Set(session.steps.slice(0,session.index).filter(s=>s.skill==='reading'&&s.materialCaseId).map(s=>s.materialCaseId)):new Set();
    for(const block of document.querySelectorAll('[data-writing-case]')){
      const contextual=active&&current.skill.startsWith('writing')&&session.steps.some(s=>s.materialCaseId);
      const groups=[...block.querySelectorAll('[data-reading-source]')];
      for(const group of groups){
        group.hidden=contextual&&(current.writingCaseId!==block.dataset.writingCase||!current.readingSourceId||!completedReadings.has(current.readingSourceId)||group.dataset.readingSource!==current.readingSourceId);
        if(contextual&&!group.hidden)group.open=true;
      }
      block.hidden=contextual&&!groups.some(g=>!g.hidden);
      block.querySelector('.mr-prep-note').textContent=contextual?'这些表达来自你刚读完的材料；例句按眼前这道写作题编写，可按需要使用。':'下面的表达来自阅读材料，例句按本题语境编写。展开相关材料即可查看。';
    }
    let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
    const target=document.getElementById(id);
    if(target?.matches('.material-reading,.material-writing,.mr-source-group')){
      const unit=target.closest('.exam-case'),bank=unit?.closest('.case-bank');
      if(bank&&unit.hidden){
        bank.querySelector('[data-case-search]').value='';bank.querySelector('[data-case-filter]').value='all';
        bank.querySelector('[data-case-type="全部"]').click();
      }
    }
    if(target?.classList.contains('mr-source-group')){
      const block=target.closest('[data-writing-case]');block.hidden=false;
      for(const group of block.querySelectorAll('[data-reading-source]')){group.hidden=group!==target;group.open=group===target;}
      for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
      block.querySelector('.mr-prep-note').textContent='这里是所选阅读材料中适合本题的表达；例句按本题语境编写。';
    }
    if(target?.classList.contains('material-reading'))for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
    if(target?.classList.contains('material-writing')){
      for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
      if(!contextFor(target,current))for(const group of target.querySelectorAll('[data-reading-source]'))group.open=true;
    }
  }
  function contextFor(block,current){return current?.writingCaseId===block.dataset.writingCase;}
  document.addEventListener('input',e=>{if(e.target===field)refresh();});
  window.addEventListener('hashchange',refresh);refresh();
})();
