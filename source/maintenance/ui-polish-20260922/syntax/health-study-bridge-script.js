
/* Couple explicitly started study/reminder sessions; never control media or exam timers. */
(() => {
  'use strict';
  const energy=window.IELTSEnergyControl,field=document.getElementById('daily-study-state');
  if(!energy||!field||window.IELTSHealthStudyBridge)return;
  let linkedSessionId=null,pausedByStudyId=null,scheduled=false;
  function daily(){
    try{
      const session=JSON.parse(field.value||'null')?.session;
      if(!session||typeof session.id!=='string'||!['active','paused','completed','ended'].includes(session.status))return null;
      // The daily controller deliberately pauses restored sessions in memory before its next save.
      const paused=document.getElementById('ds-pause')?.textContent==='继续';
      return {id:session.id,status:session.status==='active'&&paused?'paused':session.status,storedStatus:session.status};
    }catch{return null;}
  }
  function pauseDaily(){
    const state=daily(),button=document.getElementById('ds-pause');
    if(state?.status==='active'&&button&&!button.disabled)button.click();
  }
  function sync(){
    const reminder=energy.read(),study=daily();
    document.body.classList.toggle('health-resting',reminder.mode==='break');
    if(reminder.mode==='break'&&study?.status==='active'){
      // Entering rest already paused daily in the Energy event handler. A later
      // committed active state is the user's explicit "end rest and continue".
      energy.endRest();document.body.classList.remove('health-resting');return;
    }
    const current=daily();
    if(!current||!['active','paused'].includes(current.status)){
      // A completed/ended linked session must not leave its reminder counting unattended.
      if(linkedSessionId&&(!current||current.id===linkedSessionId)&&reminder.mode==='running')energy.pause();
      linkedSessionId=null;pausedByStudyId=null;return;
    }
    if(linkedSessionId&&linkedSessionId!==current.id){linkedSessionId=null;pausedByStudyId=null;}
    if(current.status==='active'&&reminder.mode==='running')linkedSessionId=current.id;
    if(linkedSessionId===current.id&&current.status==='paused'&&reminder.mode==='running'){
      if(energy.pause())pausedByStudyId=current.id;
    }else if(linkedSessionId===current.id&&current.status==='active'&&reminder.mode==='paused'&&pausedByStudyId===current.id){
      // Only an explicit daily continuation reaches this state; a finished break never does.
      pausedByStudyId=null;energy.resume();
    }
  }
  function schedule(){
    if(scheduled)return;scheduled=true;
    // Let the daily controller finish its commit or rollback before reading the shared field.
    Promise.resolve().then(()=>{scheduled=false;sync();});
  }
  window.addEventListener('ielts-energy-change',event=>{
    const change=event.detail||{},study=daily();
    if(change.origin!=='daily-study'){
      pausedByStudyId=null;
      // Explicitly starting/stopping Energy while daily is paused means independent use.
      if(change.action==='stop'||(change.action==='start'&&study?.status!=='active'))linkedSessionId=null;
    }
    if(change.mode==='break')pauseDaily();
    schedule();
  });
  field.addEventListener('input',schedule);
  document.addEventListener('visibilitychange',schedule);
  window.addEventListener('pageshow',schedule);
  window.addEventListener('pagehide',sync);
  const restored=daily();
  if(restored?.storedStatus==='active'&&restored.status==='paused'&&energy.read().mode==='running')linkedSessionId=restored.id;
  window.IELTSHealthStudyBridge=Object.freeze({
    read:()=>Object.freeze({linkedSessionId,pausedByStudyId,resting:energy.read().mode==='break'}),
    requestRest:()=>energy.requestRest()
  });
  sync();
})();
