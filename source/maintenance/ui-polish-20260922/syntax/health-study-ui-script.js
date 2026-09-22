
/* Small interaction improvements layered onto the existing daily study UI. */
(function () {
  'use strict';
  const dock=document.getElementById('daily-study-dock');
  if(!dock || dock.dataset.healthUi)return;
  dock.dataset.healthUi='1';
  const actions=dock.querySelector('.ds-dock-actions');
  const copy=dock.querySelector('.ds-dock-copy');
  const instruction=dock.querySelector('.ds-dock-instruction');
  const field=document.getElementById('daily-study-state');
  const energy=()=>window.IELTSEnergyControl;
  const readDaily=()=>{try{return JSON.parse(field.value)?.session;}catch{return null;}};
  const create=(text,id,handler)=>{const b=document.createElement('button');b.type='button';b.id=id;b.textContent=text;b.addEventListener('click',handler);return b;};
  instruction.id='hs-current-instruction';
  const detail=create('说明','hs-details',()=>{
    const expanded=dock.classList.toggle('hs-expanded');detail.setAttribute('aria-expanded',String(expanded));
  });
  detail.setAttribute('aria-expanded','false');detail.setAttribute('aria-controls',instruction.id);detail.setAttribute('aria-label','展开或收起任务说明和笔记操作');
  let restError='';
  const rest=create('休息','hs-rest',()=>{
    restError='';
    const accepted=window.IELTSHealthStudyBridge?.requestRest();
    if(accepted===false)restError=document.getElementById('energy-message')?.textContent||'暂时无法开始休息，当前作答已保留。';
    sync();
  });
  rest.setAttribute('aria-label','休息一下，暂停本次学习计时');
  const end=create('收工','hs-finish',()=>{
    if([...document.querySelectorAll('[data-stop]')].some(button=>!button.disabled)){
      restError='录音还在进行。请先结束并下载录音，再收工。';sync();return;
    }
    restError='';sync();
    document.getElementById('ds-end')?.click();
    if(readDaily()?.status==='ended'){
      document.getElementById('energy-stop')?.click();
      requestAnimationFrame(()=>document.getElementById('ds-completed')?.scrollIntoView({block:'center',behavior:'instant'}));
    }
  });
  end.setAttribute('aria-label','今天先到这里，保留当前学习记录');
  for(const child of actions.children){
    if(child.tagName==='A' || (child.tagName==='BUTTON'&&!child.id))child.dataset.hsSecondary='';
  }
  const next=document.getElementById('ds-next');
  actions.insertBefore(detail,next);actions.insertBefore(rest,next);actions.insertBefore(end,next);
  const status=document.createElement('p');status.className='hs-rest-status';status.hidden=true;status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  const clock=document.createElement('span');clock.className='hs-rest-clock';clock.setAttribute('aria-hidden','true');
  copy.append(status,clock);
  const error=dock.querySelector('.ds-message');if(error){error.setAttribute('role','status');error.setAttribute('aria-live','polite');}
  const menu=document.getElementById('mobile-menu');
  let lastStatus='',lastTitle='';
  function sync(){
    const showing=!dock.hidden, mode=energy()?.read().mode;
    document.body.classList.toggle('hs-dock-visible',showing);
    const navigationOpen=menu?.getAttribute('aria-expanded')==='true';
    dock.inert=!!navigationOpen;
    const title=dock.querySelector('.ds-dock-title')?.textContent;
    if(title!==lastTitle){lastTitle=title;dock.classList.remove('hs-expanded');detail.setAttribute('aria-expanded','false');}
    const text=restError||(mode==='break'?'正在休息，学习计时已暂停；点继续可提前结束休息。':mode==='due'?'这一段到休息时间了，可以休息或就此结束。':mode==='ready'?'休息结束，愿意时再继续，也可以收工。':'');
    if(text!==lastStatus){status.textContent=text;status.hidden=!text;lastStatus=text;}
    rest.disabled=mode==='break';
    rest.textContent=mode==='break'?'休息中':'休息';
    rest.setAttribute('aria-label',mode==='break'?'正在休息':'休息一下，暂停本次学习计时');
    const pause=document.getElementById('ds-pause');
    if(pause){pause.setAttribute('aria-label',mode==='break'?'结束休息并继续学习':pause.textContent);pause.title=mode==='break'?'结束休息并继续学习':'';}
    const remaining=mode==='break'?Math.max(0,Math.ceil((energy().read().dueAt-Date.now())/1000)):0;
    clock.textContent=mode==='break'?Math.floor(remaining/60)+':'+String(remaining%60).padStart(2,'0'):'';
  }
  new MutationObserver(sync).observe(dock,{attributes:true,attributeFilter:['hidden']});
  if(menu)new MutationObserver(sync).observe(menu,{attributes:true,attributeFilter:['aria-expanded']});
  const title=dock.querySelector('.ds-dock-title');if(title)new MutationObserver(sync).observe(title,{childList:true,characterData:true,subtree:true});
  window.addEventListener('ielts-energy-change',()=>{restError='';sync();});
  window.addEventListener('hashchange',sync);
  // Reserve the actual fixed-bar height so the last input can always scroll clear.
  if(typeof ResizeObserver==='function')new ResizeObserver(entries=>{
    const entry=entries[0],size=entry.borderBoxSize;
    const height=size?(Array.isArray(size)?size[0]:size).blockSize:entry.contentRect.height+32;
    document.body.style.setProperty('--hs-dock-space',Math.ceil(height+36)+'px');
  }).observe(dock);
  setInterval(()=>{if(!dock.hidden)sync();},1000);
  sync();
})();
