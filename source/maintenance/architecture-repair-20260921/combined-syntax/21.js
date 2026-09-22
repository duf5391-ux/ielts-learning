
(() => {
  'use strict';
  const M=window.IELTSEnergyModel, host=document.getElementById('energy-control');
  if (!M || !host) return;
  const $=id=>document.getElementById('energy-'+id), field=$('control-state');
  let state, blocked=false, lastMode='', savedRaw=field.value;
  try {state=M.read(field.value,Date.now());} catch {state=M.initial();blocked=true;}
  function persist() {
    if(blocked){$('storage').hidden=false;$('storage').textContent='旧的提醒记录无法读取，已保留原值；本次提醒只在当前页面生效。';return;}
    const raw=JSON.stringify(state);
    if(raw===savedRaw)return;
    field.value=raw;field.dispatchEvent(new Event('input',{bubbles:true}));savedRaw=raw;
    const status=document.getElementById('save-status')?.textContent||'';
    const failed=/未能|无法|暂停自动/.test(status);
    $('storage').hidden=!failed;
    if(failed)$('storage').textContent='浏览器暂未保存本轮提醒；刷新前请先导出学习记录。';
  }
  function bookmark(){
    const panel=[...document.querySelectorAll('main>.panel')].find(n=>!n.hidden);
    if(!panel)return;
    const candidates=[...panel.querySelectorAll('[id]')].filter(n=>n.getClientRects().length && n.getBoundingClientRect().top<=160 && !host.contains(n));
    const node=candidates[candidates.length-1]||panel;
    state=M.reduce(state,{type:'bookmark',bookmark:{hash:location.hash,anchor:node.id,y:Math.max(0,window.scrollY)}},Date.now());
    persist();
  }
  function recording(){return [...document.querySelectorAll('[data-stop]')].some(b=>!b.disabled);}
  function announce(previousMode,action,origin){
    if(typeof window.dispatchEvent!=='function')return;
    const event=new Event('ielts-energy-change');
    event.detail=Object.freeze({previousMode,mode:state.mode,action,origin});
    window.dispatchEvent(event);
  }
  function act(type,origin='user'){
    if(type==='rest' && recording()){
      const message='录音还在进行。请先结束并下载录音，再开始休息。';$('message').textContent=message;
      if(!$('reminder').hidden && $('reminder').children[0])$('reminder').children[0].textContent=message;
      return false;
    }
    if(['rest','pause','stop'].includes(type))bookmark();
    const previousMode=state.mode;
    // The daily toolbar can begin a break directly, after the recording guard above.
    if(type==='rest'&&origin==='health-ui'&&['idle','ready'].includes(state.mode))state=M.reduce(state,{type:'start'},Date.now());
    state=M.reduce(state,{type},Date.now());persist();render();
    if(state.mode!==previousMode)announce(previousMode,type,origin);
    return state.mode!==previousMode;
  }
  function returnToPlace(){
    const b=state.bookmark;if(!b)return;
    const target=document.getElementById(b.anchor);
    if(!target){$('message').textContent='上次位置已变更，可以从原章节继续。';if(b.hash.startsWith('#'))location.hash=b.hash;return;}
    const panel=target.closest('main>.panel');
    if(panel)location.hash=target.id;
    let node=target;while(node){if(node.tagName==='DETAILS')node.open=true;node=node.parentElement;}
    requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'smooth'}));
  }
  function render(){
    const mode=state.mode, seconds=Math.ceil(M.left(state,Date.now())/1000), clock=Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');
    const labels={idle:'安排一小段学习',running:'本轮剩余 '+clock,paused:'已暂停 · 剩余 '+clock,due:'到休息时间了',break:'休息中 · 剩余 '+clock,ready:'休息结束，可继续或收工'};
    $('summary').textContent=labels[mode];
    $('minutes').value=String(state.minutes);$('rest').value=String(state.rest);
    $('minutes').disabled=$('rest').disabled=!['idle','ready'].includes(mode);
    $('start').hidden=!['idle','ready','paused'].includes(mode);$('start').textContent=mode==='paused'?'继续这段学习':'开始这一段';
    $('pause').hidden=mode!=='running';$('take-rest').hidden=!['running','paused','due'].includes(mode);
    $('snooze').hidden=mode!=='due';$('stop').hidden=mode==='idle';$('return').hidden=!state.bookmark;
    if(lastMode!==mode){
      const messages={idle:'开始前，选好这次要完成的一件小事。',running:'跨章节仍继续计时；到点后只提醒，不打断当前作答。',paused:'时间已暂停，作答仍在原处。',due:'这一段结束了。完成手头这一步后，可以起身活动、看看远处，或直接收工。',break:'休息一下。到点后由你决定继续还是结束，不会自动开始下一段。',ready:'休息结束。愿意继续时，再选一件小事；也可以就此结束。'};
      $('message').textContent=messages[mode];
      const reminder=$('reminder');reminder.replaceChildren();reminder.hidden=!['due','ready'].includes(mode);
      if(!reminder.hidden){
        const p=document.createElement('div');p.textContent=messages[mode];reminder.append(p);
        const button=document.createElement('button');button.type='button';button.textContent=mode==='due'?'现在休息':'打开学习安排';
        button.onclick=()=>{host.querySelector('details').open=true;if(mode==='due')act('rest');else host.scrollIntoView({block:'center'});};reminder.append(button);
        const hide=document.createElement('button');hide.type='button';hide.textContent='收起提醒';hide.onclick=()=>{reminder.hidden=true;};reminder.append(hide);
      }
      lastMode=mode;
    }
  }
  for(const [id,type] of [['start','start'],['pause','pause'],['take-rest','rest'],['snooze','snooze'],['stop','stop']])$(id).onclick=()=>act(type);
  $('return').onclick=returnToPlace;
  for(const id of ['minutes','rest'])$(id).onchange=()=>{state=M.reduce(state,{type:'settings',minutes:Number($('minutes').value),rest:Number($('rest').value)},Date.now());persist();render();};
  window.addEventListener('pagehide',()=>{if(state.mode!=='idle')bookmark();});
  let markTimer;
  window.addEventListener('scroll',()=>{if(['running','paused','due'].includes(state.mode)){clearTimeout(markTimer);markTimer=setTimeout(bookmark,800);}},{passive:true});
  function update(){const previousMode=state.mode,next=M.tick(state,Date.now());if(next!==state){state=next;persist();}render();if(state.mode!==previousMode)announce(previousMode,'tick','clock');}
  document.addEventListener('visibilitychange',update);
  window.addEventListener('pageshow',update);
  window.IELTSEnergyControl=Object.freeze({
    read:()=>JSON.parse(JSON.stringify(state)),
    pause:()=>state.mode==='running'&&act('pause','daily-study'),
    resume:()=>state.mode==='paused'&&act('start','daily-study'),
    endRest:()=>state.mode==='break'&&act('stop','health-ui'),
    requestRest:()=>act('rest','health-ui')
  });
  setInterval(update,1000);persist();render();
})();
