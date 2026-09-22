(() => {
  'use strict';
  const root=document.getElementById('writing-workbench');
  const rows=JSON.parse(document.getElementById('writing-question-map').textContent);
  const map=new Map(rows.map(q=>[q.id,q]));
  const sessionOrigins=new Map();
  const input=key=>document.querySelector('[data-save="'+key+'"]');
  const value=key=>input(key)?.value || '';
  const meaningful=key=>!!value(key).trim() && value(key).trim()!=='暂时不会';
  const directory=root.querySelector('.ww-directory');
  const search=root.querySelector('#ww-directory-search');
  const taskFilter=root.querySelector('#ww-directory-task');
  function hasDraft(q){return meaningful(q.id+'-first')||meaningful(q.id+'-revision')||meaningful(q.id+'-first-at');}
  function browse(show,scroll=false) {
    root.dataset.wwBrowsing=String(show);directory.hidden=!show;
    if(show){filter();if(scroll)directory.scrollIntoView({block:'start'});}
  }
  function filter(){
    const query=search.value.trim().toLocaleLowerCase(),skill=taskFilter.value;
    let count=0;
    directory.querySelectorAll('[data-ww-pick]').forEach(row=>{
      row.hidden=!!(skill&&row.dataset.wwSkill!==skill)||!row.dataset.wwSearch.toLocaleLowerCase().includes(query)||(document.getElementById('ux-writing-progress').value==='started'&&!hasDraft(map.get(row.dataset.wwPick)))||(document.getElementById('ux-writing-progress').value==='new'&&hasDraft(map.get(row.dataset.wwPick)));
      if(!row.hidden)count++;
    });
    document.getElementById('ux-writing-empty').hidden=count>0;directory.querySelector('.ww-directory-count').textContent=count?'共 '+count+' 道 · 选择题目即可开始首稿或继续已有稿':'没有匹配的题目，试试其他关键词或Task。';
  }
  function routeCatalogue(){
    let hash='';try{hash=decodeURIComponent(location.hash.slice(1));}catch{return;}
    if(hash==='writing-workbench') {
      const active=map.get(value('ww-active-task'));
      const current=active&&hasDraft(active)?active:rows.find(hasDraft);
      browse(!current);
      if(current && current!==active){location.hash=current.id;}
    } else if(document.getElementById(hash)?.closest('[data-ww-unit]'))browse(false);
  }
  function status(q) {
    if (value(q.id+'-first-at')) return '首稿已保留'+(meaningful(q.id+'-revision')?' · 有修订稿':'');
    return meaningful(q.id+'-first')?'首稿写作中':'尚未开始';
  }
  function update() {
    for(const q of rows) {
      const labels=[...new Set(q.aliases.filter(a=>a.fields.some(meaningful)).map(a=>a.label))];
      const badge=root.querySelector('[data-ww-related="'+q.id+'"]');
      badge.hidden=labels.length===0;badge.textContent=labels.length?'已在'+labels.join('、')+'留下作答 · 各处记录独立保留':'同题各处作答分别保存；工作台首稿与修订可从任一入口继续。';
      const returnId=sessionOrigins.get(q.id)||value(q.id+'-return-route');
      const valid=q.aliases.some(a=>a.route===returnId)?returnId:q.origin;
      root.querySelectorAll('[data-ww-return="'+q.id+'"]').forEach(a=>a.href='#'+valid);
      document.querySelectorAll('[data-ww-source-status="'+q.id+'"]').forEach(n=>n.textContent=status(q));
      const row=directory.querySelector('[data-ww-row-status="'+q.id+'"]');
      row.textContent=(hasDraft(q)?status(q)+' · 继续 →':'开始首稿 →')+(labels.length?' · 曾在'+labels.join('/')+'作答':'');
      const option=root.querySelector('option[value="'+q.id+'"]');
      option.dataset.wwBase ||= option.textContent;
      option.textContent=option.dataset.wwBase+(labels.length?' · 曾在'+labels.join('/')+'作答':'');
    }
  }
  document.addEventListener('click',event=>{
    if(event.target.closest('[data-ww-catalogue]')){browse(true,true);return;}
    const promptButton=event.target.closest('[data-ww-prompt-toggle]');
    if(promptButton){const topic=promptButton.closest('[data-ww-unit]').querySelector('.ww-topic');topic.open=true;topic.scrollIntoView({block:'start'});return;}
    const pick=event.target.closest('[data-ww-pick]');
    if(pick){browse(false);if(location.hash===pick.hash)window.dispatchEvent(new Event('hashchange'));return;}
    const link=event.target.closest('[data-ww-open]');
    if(!link)return;
    const q=map.get(link.dataset.wwOpen);
    if(!q || !q.aliases.some(a=>a.route===link.dataset.wwFrom))return;
    const route=input(q.id+'-return-route');
    sessionOrigins.set(q.id,link.dataset.wwFrom);
    if(route && !window.IELTSRecordStore?.commit({[route.dataset.save]:link.dataset.wwFrom},{expectedFields:{[route.dataset.save]:route.value}})) {
      const notice=root.querySelector('#ww-notice');
      notice.textContent='本次返回位置未能保存；当前仍可回到原题。已有作文与修订保持原样。';notice.hidden=false;
    }
    // Preserve only existing, explicit reading→writing relationships; never infer a new match.
    const prep=document.getElementById(q.id).querySelector('.ww-reading-prep');
    const origin=document.getElementById(link.dataset.wwFrom);
    if(prep && origin) {
      const active=[...origin.querySelectorAll('.mr-source-group[data-reading-source]')].filter(n=>!n.hidden && n.open).map(n=>n.dataset.readingSource);
      if(active.length){prep.open=true;prep.querySelectorAll('.mr-source-group').forEach(n=>{n.hidden=!active.includes(n.dataset.readingSource);n.open=active.includes(n.dataset.readingSource);});}
    }
    update();
  });
  let pending;
  document.addEventListener('input',()=>{clearTimeout(pending);pending=setTimeout(update,100);});
  window.addEventListener('storage',()=>setTimeout(update,0));
  window.addEventListener('hashchange',update);
  window.addEventListener('hashchange',routeCatalogue);
  document.getElementById('ux-writing-progress').addEventListener('change',filter);document.getElementById('ux-writing-clear').addEventListener('click',()=>{search.value='';taskFilter.value='';document.getElementById('ux-writing-progress').value='all';filter();search.focus();});search.addEventListener('input',filter);taskFilter.addEventListener('change',filter);
  update();
  routeCatalogue();
})();
