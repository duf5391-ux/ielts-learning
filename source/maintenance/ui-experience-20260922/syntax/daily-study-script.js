
(function () {
  'use strict';
  const M = window.IELTSDailyStudy, $ = s => document.querySelector(s);
  const root = $('#daily-study-home'), field = $('#daily-study-state');
  if (!M || !root || !field) return;
  const catalog = JSON.parse($('#daily-study-catalog').textContent);
  const labels = Object.fromEntries(catalog.map(c => [c.skill, c.label]));
  const capacity = {15:1,30:2,60:4};
  let state, blocked = false, saving = false, preview, clockAt = performance.now(), lastFlush = clockAt, expanded = false;
  const node = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
  const button = (text, action, cls) => { const b = node('button',text,cls); b.type='button'; b.addEventListener('click',action); return b; };
  const ongoing = () => ['active','paused'].includes(state.session?.status);
  const current = () => ongoing() ? state.session.steps[state.session.index] : null;
  const hash = () => {try{return decodeURIComponent(location.hash.slice(1)) || 'guide';}catch{return 'guide';}};
  const routeMatches = () => current() && (hash() === current().target || document.getElementById(current().target)?.contains(document.getElementById(hash())));
  const skillText = skills => skills.map(s=>labels[s]||s).join(' + ');
  const errorMessage = text => { $('#ds-message').textContent=text; $('#ds-message').hidden=false; dockMessage.textContent=text; dockMessage.hidden=false; };
  const clearMessage = () => { $('#ds-message').hidden=true; dockMessage.hidden=true; };
  const dock = node('aside',undefined,'ds-dock'); dock.id='daily-study-dock'; dock.hidden=true; dock.setAttribute('aria-label','本次学习进度');
  const copy=node('div',undefined,'ds-dock-copy'), dockLabel=node('p','','ds-dock-label'), dockTitle=node('h2','','ds-dock-title'), instruction=node('p','','ds-dock-instruction'), dockMessage=node('p','','ds-message'); dockMessage.hidden=true;
  copy.append(dockLabel,dockTitle,instruction,dockMessage);
  const actions=node('div',undefined,'ds-dock-actions'), time=node('span','','ds-dock-time'); time.id='ds-clock';
  const pause=button('暂停',togglePause), note=button('随手记',openNotes), overview=node('a','查看安排'); overview.href='#guide';
  const advance=button('完成这一步 →',nextStep,'ds-primary'); advance.id='ds-next'; pause.id='ds-pause';
  actions.append(time,pause,note,overview,advance);dock.append(copy,actions);document.body.append(dock);
  const dialog=node('dialog',undefined,'ds-dialog'); dialog.setAttribute('aria-labelledby','ds-note-heading');
  const noteHeading=node('h2','随手记');noteHeading.id='ds-note-heading';
  const noteLabel=node('label','这次改了哪里，或下次想练什么（可留空）');noteLabel.htmlFor='ds-note';
  const noteInput=node('textarea');noteInput.id='ds-note';noteInput.maxLength=12000;
  const noteStatus=node('p','');noteStatus.setAttribute('role','status');
  const dialogActions=node('div',undefined,'ds-dialog-actions');dialogActions.append(button('关闭',()=>dialog.close()),button('保存笔记',saveNotes,'ds-primary'));
  dialog.append(noteHeading,noteLabel,noteInput,noteStatus,dialogActions);document.body.append(dialog);
  try {state=field.value ? M.read(field.value) : M.initial(); if(state.session?.status==='active')state=M.pause(state);} catch {state=M.initial();blocked=true;}
  document.body.classList.add('ds-enabled');
  $('#ds-date').textContent=new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'long'});

  function persist(next, redraw=true) {
    if(blocked){errorMessage('学习安排记录暂时无法读取，已保留原记录。请到学习记录页导出备份后处理。');return false;}
    const previous=field.value, raw=JSON.stringify(next); saving=true;
    field.value=raw;field.dispatchEvent(new Event('input',{bubbles:true}));
    let ok=false;
    try {ok=JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'null')?.fields?.['daily-study-state']===raw;} catch {}
    if(!ok){
      // Roll back the field AND the existing controller's in-memory value.
      field.value=previous;field.dispatchEvent(new Event('input',{bubbles:true}));saving=false;
      if(ongoing())state=M.pause(state);
      renderDock();errorMessage('本次保存未成功，进度没有前进。请先导出学习记录；恢复存储后可继续。');return false;
    }
    state=next;saving=false;clearMessage();if(redraw)render();return true;
  }
  function setPreferences(minutes, skills) {
    if(ongoing())return;
    const max=capacity[minutes], trimmed=skills.slice(0,max);
    const preferences={...state.preferences,minutes,skills:trimmed};
    const variant=catalog.find(c=>c.skill==='reading')?.variants?.find(v=>v.id===preferences.readingCase);
    if(variant&&variant.minMinutes>minutes/Math.max(1,trimmed.length))delete preferences.readingCase;
    if(persist({...state,preferences}) && skills.length>max)errorMessage('已切换为 '+minutes+' 分钟，保留前 '+max+' 个板块；其他板块可以下次选择。');
  }
  document.querySelectorAll('[data-ds-minutes]').forEach(b=>b.addEventListener('click',()=>setPreferences(Number(b.dataset.dsMinutes),state.preferences.skills)));
  function selectSkill(skill) {
    let selected=[...state.preferences.skills];
    if(skill==='auto')selected=[];
    else if(selected.includes(skill))selected=selected.filter(s=>s!==skill);
    else if(selected.length<capacity[state.preferences.minutes])selected.push(skill);
    setPreferences(state.preferences.minutes,selected);
  }
  function renderSkills() {
    const host=$('#ds-skills'), selected=state.preferences.skills;host.replaceChildren();
    const add=(key,label,isSelected,action)=>{const b=button(label,action||(()=>selectSkill(key)));b.dataset.dsSkill=key;b.setAttribute('aria-pressed',String(isSelected));b.disabled=blocked||ongoing()||(!isSelected&&key!=='auto'&&selected.length>=capacity[state.preferences.minutes]);host.append(b);};
    add('auto','帮我安排',!selected.length);
    const pair=button('阅读后写作',()=>setPreferences(Math.max(30,state.preferences.minutes),['reading','writing2']));pair.dataset.dsPair='reading-writing';pair.disabled=blocked||ongoing();host.append(pair);
    for(const [key,label] of [['listening','听力'],['reading','阅读'],['writing','写作'],['speaking','口语'],['vocabulary','词汇与短语'],['background','共用背景']]){
      if(key==='writing')add(key,label,selected.some(s=>s.startsWith('writing')),()=>{const writing=selected.find(s=>s.startsWith('writing'));if(writing)selectSkill(writing);else selectSkill('writing2');});
      else add(key,label,selected.includes(key));
    }
    const writing=selected.find(s=>s.startsWith('writing'));
    if(writing){const types=node('div',undefined,'ds-writing-types');types.setAttribute('role','group');types.setAttribute('aria-label','写作类型');
      for(const [key,label] of [['writing1','Task 1 · 图表'],['writing2','Task 2 · 议论文']]){const b=button(label,()=>setPreferences(state.preferences.minutes,selected.map(s=>s.startsWith('writing')?key:s)));b.dataset.dsWriting=key;b.setAttribute('aria-pressed',String(writing===key));b.disabled=blocked||ongoing();types.append(b);}host.append(types);}
    const variants=catalog.find(c=>c.skill==='reading')?.variants;
    if(selected.includes('reading')&&variants?.length){
      const label=node('label','阅读材料','ds-reading-picker'),picker=node('select');picker.id='ds-reading-material';
      const auto=node('option','按最近安排轮换');auto.value='';picker.append(auto);
      const budget=state.preferences.minutes/selected.length;
      for(const v of variants){const option=node('option',v.title+(v.minMinutes>budget?'（需更多时间）':''));option.value=v.id;option.disabled=v.minMinutes>budget;picker.append(option);}
      picker.value=state.preferences.readingCase||'';picker.disabled=blocked||ongoing();
      picker.addEventListener('change',()=>{const preferences={...state.preferences};if(picker.value)preferences.readingCase=picker.value;else delete preferences.readingCase;persist({...state,preferences});});
      label.append(picker);host.append(label);
    }
  }
  function renderSteps(plan) {
    const list=$('#ds-steps');list.replaceChildren();
    const grouped=plan.steps.length>4&&!expanded;
    const items=grouped?plan.skills.map(skill=>{const steps=plan.steps.filter(s=>s.skill===skill);return {title:labels[skill],instruction:steps.map(s=>s.title).join(' → '),minutes:steps.reduce((n,s)=>n+s.minutes,0),id:steps[0].id};}):plan.steps;
    items.forEach((step,index)=>{
      const li=node('li'), completed=ongoing()&&state.session.completed.includes(step.id), active=ongoing()&&(grouped?current().skill===plan.skills[index]:current().id===step.id);
      li.classList.toggle('is-done',!!completed&&!active);li.classList.toggle('is-current',!!active||(!ongoing()&&index===0));
      li.append(node('span',completed&&!active?'✓':String(index+1),'ds-step-dot'));
      const line=node('div',undefined,'ds-step-line');line.append(node('strong',grouped?step.title:(plan.skills.length>1?labels[step.skill]+' · ':'')+step.title),node('small',step.minutes+' 分钟'));li.append(line,node('p',step.instruction));list.append(li);
    });
    $('#ds-expand')?.remove();if(plan.steps.length>4){const b=button(expanded?'收起步骤':'查看全部 '+plan.steps.length+' 个步骤',()=>{expanded=!expanded;renderSteps(plan);},'ds-more');b.id='ds-expand';list.after(b);}
  }
  function renderCompletion() {
    const n=$('#ds-completed'), session=state.session;n.hidden=!['completed','ended'].includes(session?.status);n.replaceChildren();if(n.hidden)return;
    n.append(node('h2',session.status==='completed'?'这一段学习，完成了。':'这次先学到这里。'),node('p',skillText(session.skills)+' · 你已确认完成 '+session.completed.length+' / '+session.steps.length+' 步 · 记录用时 '+Math.floor(session.elapsedMs/60000)+' 分钟'),node('p','下次怎样安排？按你的实际感受选择。'));
    const feedback=node('div',undefined,'ds-feedback');for(const [value,label] of [['okay','比较顺利，换个板块'],['retry','还想再练'],['skip','暂时跳过这个板块']]){const b=button(label,()=>{let next=M.feedback(state,value,state.session.note);if(value!=='retry')next={...next,preferences:{...next.preferences,skills:[]}};persist(next);});b.dataset.dsFeedback=value;b.setAttribute('aria-pressed',String(session.feedback===value));feedback.append(b);}feedback.append(button(session.note?'查看这次笔记':'补一句笔记（可选）',openNotes));n.append(feedback);
  }
  function render() {
    renderSkills();renderCompletion();
    const s=state.session, active=ongoing();
    document.querySelectorAll('[data-ds-minutes]').forEach(b=>{b.disabled=blocked||active;b.setAttribute('aria-pressed',String(Number(b.dataset.dsMinutes)===state.preferences.minutes));});
    try {preview=active?s:M.plan(state.preferences,catalog,state.history,Date.now());}catch(e){$('#ds-start').disabled=true;errorMessage(e.message);return;}
    $('#ds-plan-title').textContent=active?'上次学到这里':'今天的安排';$('#ds-plan-total').textContent=active?'约剩 '+Math.ceil(M.remaining(state)/60)+' 分钟':'约 '+preview.minutes+' 分钟';
    $('#ds-plan-reason').textContent=active?skillText(s.skills)+' · 第 '+(s.index+1)+' / '+s.steps.length+' 步':skillText(preview.skills)+' · '+preview.reason;
    $('#ds-capacity').textContent='最多选 '+capacity[state.preferences.minutes]+' 个板块';
    $('#ds-selection-note').textContent=active?'已保留这次安排与步骤，继续即可回到当前内容。':state.preferences.skills.length?'本次只安排你选中的内容；取消全部选择后由我安排。':'先专注一个板块。完成后，可根据你的反馈继续巩固或换个内容。';
    $('#ds-start').replaceChildren(document.createTextNode(active?'继续这次学习':'直接开始学习'),node('span','→'));$('#ds-start').disabled=blocked;
    $('#ds-start-meta').textContent=preview.minutes+' 分钟 · '+preview.steps.length+' 步';
    $('#ds-start-note').textContent=active?'暂停和关闭页面都不会清空步骤；学习时间只记录当前练习。':'直接进入第一步；已经做过的材料可以作为复习。';
    $('#ds-end')?.remove();if(active){const end=button('提前结束，重新安排',()=>{if(persist(M.end(state,Date.now())))location.hash='guide';},'ds-more');end.id='ds-end';$('#ds-start-note').after(end);}
    renderSteps(preview);renderDock();
    if(blocked)errorMessage('学习安排记录暂时无法读取，原文已保留。请到学习记录页导出备份后处理。');
  }
  function goCurrent() {
    const step=current(),target=step&&document.getElementById(step.target);if(!target){errorMessage('这一步的学习材料暂时找不到，进度已保留。');return false;}
    if(hash()!==step.target)location.hash=step.target;
    else window.dispatchEvent(new HashChangeEvent('hashchange'));
    return true;
  }
  function positionCurrent() {
    const step=current(),target=step&&document.getElementById(step.target);if(!target)return;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      let focus=target;
      // The 15-minute writing route is the independent micro task, not its full sheet.
      if(/^pr-writing[12]-/.test(step.target)&&state.session.minutes/state.session.skills.length<=20&&state.session.index%4>0){
        const micro=target.querySelector('[data-save="'+step.target+'-another"]');
        if(micro){focus=micro.closest('details')||micro;for(let n=focus;n&&n!==target;n=n.parentElement)if(n.tagName==='DETAILS'&&!n.hasAttribute('data-answer-gate'))n.open=true;}
      }
      for(let n=target;n;n=n.parentElement)if(n.tagName==='DETAILS')n.open=true;
      focus.scrollIntoView({block:'start',behavior:'instant'});focus.setAttribute('tabindex','-1');focus.focus({preventScroll:true});renderDock();
    }));
  }
  $('#ds-start').addEventListener('click',()=>{
    const plan=ongoing()?state.session:preview;
    if(!plan.steps.every(s=>document.getElementById(s.target))){errorMessage('部分学习材料暂时无法打开，请选择其他板块。');return;}
    const next=ongoing()?M.resume(state):M.start(state,preview,Date.now());
    if(persist(next)){clockAt=performance.now();lastFlush=clockAt;goCurrent();}
  });
  function nextStep() {
    if(!ongoing()||state.session.status!=='active')return;
    const upcoming=state.session.steps[state.session.index+1],target=upcoming&&document.getElementById(upcoming.target);
    if(target?.closest('.gated[hidden]')){errorMessage('请先在本页留下答案并点击「保存首次作答」，再进入核对这一步。');return;}
    const next=M.advance(state,Date.now());
    if(persist(next)){clockAt=performance.now();if(ongoing())goCurrent();else{location.hash='guide';requestAnimationFrame(()=>$('#ds-completed').scrollIntoView({block:'center'}));}}
  }
  function togglePause() {if(!ongoing())return;const isPaused=state.session.status==='paused';if(persist(isPaused?M.resume(state):M.pause(state))){clockAt=performance.now();if(isPaused&&!routeMatches())goCurrent();}}
  function renderDock() {
    dock.hidden=!ongoing()||hash()==='guide';document.body.classList.toggle('ds-dock-active',!dock.hidden);if(!ongoing())return;
    const s=state.session, step=current();dockLabel.textContent=labels[step.skill]+' · 第 '+(s.index+1)+' / '+s.steps.length+' 步 · 建议 '+step.minutes+' 分钟';
    dockTitle.textContent=step.title;instruction.textContent=step.instruction;
    pause.textContent=s.status==='paused'?'继续':'暂停';advance.disabled=s.status!=='active'||blocked;renderClock();
  }
  function renderClock(){if(!ongoing())return;const s=state.session;time.textContent=s.status==='paused'?'已暂停':s.stepElapsedMs>=current().minutes*60000?'建议时间已到，可继续':'本步 '+Math.floor(s.stepElapsedMs/60000)+':'+String(Math.floor(s.stepElapsedMs/1000)%60).padStart(2,'0');}
  function openNotes(){if(!state.session)return;noteInput.value=state.session.note;noteStatus.textContent='';dialog.showModal();}
  function saveNotes(){if(!state.session)return;const s={...state.session,note:noteInput.value};const next={...state,session:s,history:state.history.map(h=>h.id===s.id?{...s}:h)};if(persist(next)){noteStatus.textContent='笔记已保存。';dialog.close();}else noteStatus.textContent='尚未保存，请先复制保留这段文字。';}
  window.addEventListener('hashchange',()=>{if(ongoing()&&state.session.status==='active'&&!routeMatches())persist(M.pause(state));renderDock();if(routeMatches())positionCurrent();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&ongoing()&&state.session.status==='active')persist(M.pause(state),false);clockAt=performance.now();renderDock();});
  window.addEventListener('pagehide',()=>{if(ongoing()&&state.session.status==='active')persist(M.pause(state),false);});
  setInterval(()=>{
    const now=performance.now(),delta=Math.max(0,Math.min(now-clockAt,3000));clockAt=now;
    if(!blocked&&!saving&&!document.hidden&&state.session?.status==='active'&&routeMatches()){
      state=M.tick(state,delta);renderClock();
      if(now-lastFlush>15000){lastFlush=now;persist(state,false);}
    }
  },1000);
  render();
})();

