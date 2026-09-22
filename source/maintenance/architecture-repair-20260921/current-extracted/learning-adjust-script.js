(function () {
  'use strict';
  const M = window.IELTSLearning, $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const data = JSON.parse($('#learning-adjust-data').textContent), field = $('#learning-adjust-state');
  const units = new Map(data.units.map(u => [u.id,u]));
  const groups = {listening:'听力',reading:'阅读',writing:'写作',speaking:'口语'};
  const scope = {study:'',practice:''};let lastCategory=null;
  const learningTools = {'word-review':'单词复习','vocabulary-review':'我的单词表','sentence-learning':'我的句子本','writing-workbench':'写作工作台'};
  const groupOf = skill => /^writing/.test(skill) ? 'writing' : skill;
  const scopeMatches = (u, group) => !group || u.skill===group || groupOf(u.skill)===group || (u.relatedSkills||[]).includes(group);
  const labelOf = group => ({writing1:'Task 1',writing2:'Task 2'}[group]||groups[group]||data.skills[group]);
  let state, blocked = false, notificationTimer, drawing = false;
  try { state = M.read(field.value); } catch (e) { state = M.initial(); blocked = true; }
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n; };
  function notify(text) { const n = $('#la-notice'); n.textContent = text; n.hidden = false; clearTimeout(notificationTimer); notificationTimer = setTimeout(()=>n.hidden=true,5500); }
  function save(next) {
    if (blocked) { notify('安排记录无法读取，原文已保留。请先到工作台导出记录。'); return false; }
    const previous=field.value,raw=JSON.stringify(next);field.value=raw;field.dispatchEvent(new Event('input',{bubbles:true}));
    try{const persisted=JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'null');if(persisted?.fields?.['learning-adjust-state']!==raw)throw Error();}catch{
      // Restore the core recorder's in-memory draft as well as this control.
      // Otherwise a later, unrelated input can persist the rejected operation.
      field.value=previous;field.dispatchEvent(new Event('input',{bubbles:true}));
      notify('当前未能保存，请到记录页导出本次文字。答案尚未解锁，本次操作未完成。');return false;
    }
    state = next; progressCache.clear(); return true;
  }
  function control(key) { return $$('[data-save]').find(n => n.dataset.save === key); }
  // Build once; the original book restores all static fields before this controller runs.
  const fields = new Map($$('[data-save]').map(n=>[n.dataset.save,n]));
  const value = key => { const n = fields.get(key); return n?.type === 'checkbox' ? n.checked : String(n?.value || ''); };
  // Business visibility only: the startup shell may temporarily hide the whole app.
  const visible = n => !!n && !n.closest('[hidden],[data-la-focus-hidden],.ui-filtered,.la-hidden-legacy');
  const progressCache = new Map();
  function savedFirst(key){try{return !!JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'{}').snapshots?.[key]?.at;}catch{return false;}}
  function savedAnswer(key){try{return M.filled(JSON.parse(localStorage.getItem('ielts-finished-book-v1')||'{}').fields?.[key]);}catch{return false;}}
  function unitProgress(u) {if(!progressCache.has(u.id))progressCache.set(u.id,M.progress(u.steps.map(s => s.kind === 'saved-first' ? savedFirst(s.key) : s.kind === 'any-answer' ? s.keys.some(k=>savedAnswer(k)) : s.kind === 'checked' ? !!state.checked[s.key] : s.kind === 'check' ? value(s.key) === true : M.filled(value(s.key)))));return progressCache.get(u.id);}
  const unitProgressNodes=$$('[data-unit-progress]').map(n=>({n,u:units.get(n.dataset.unitProgress)}));
  const collectionProgressNodes=$$('[data-collection-progress]').map(n=>({n,ids:JSON.parse(n.dataset.collectionProgress).filter(id=>units.has(id))}));
  const gates=$$('[data-answer-gate]'),gateKeys=new Map(gates.map(n=>[n,JSON.parse(n.dataset.answerGate)]));
  const todaySurfaces=[$('#la-today-list'),$('#la-plan-list'),$('#la-resume'),$('#la-today-progress'),...$$('[data-project-progress]')];

  function bar(p, noun='完成') { const n=el('div','','la-progress'), b=el('progress'); b.max=100;b.value=p.percent;b.setAttribute('aria-label',noun+' '+p.percent+'%');n.append(b,el('span',p.percent+'% · '+p.done+' / '+p.total+' '+noun));return n; }
  function button(text, action, cls='') { const n=el('button',text,cls); n.type='button';n.addEventListener('click',action);return n; }
  const link = (id,text) => {const n=el('a',text);n.href='#'+id;return n;};
  function toggleToday(id) { const next=state.today.includes(id)?state.today.filter(x=>x!==id):[...state.today,id];if(save({...state,today:next})){renderCards();renderToday();} }
  // Every content row opens the material itself. The index never opens another index card.
  const browseState = {study:new Map(),practice:new Map()};
  const filterNames = ['skill','topic','type','part','search','difficulty','confidence','status'];
  const listPositions = new Map();
  const entryOrigins = new Map();
  const folded = text => String(text||'').normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
  const corpus = new Map(data.units.map(u=>[u.id,folded([u.title,u.topic,u.type,u.description,u.source,document.getElementById(u.id)?.textContent].join(' '))]));
  const sections = [['listening','听力'],['reading','阅读'],['writing1','写作 · Task 1'],['writing2','写作 · Task 2'],['speaking','口语'],['vocabulary','词汇'],['phrases','短语'],['shared','背景与话题']];
  function rememberFilters(mode){browseState[mode].set(scope[mode]||'',Object.fromEntries(filterNames.map(k=>[k,$('#la-'+mode+'-'+k)?.value||''])));}
  function restoreFilters(mode,group){
    scope[mode]=group;const prior=browseState[mode].get(group)||{};
    for(const [suffix,key] of [['topic','topic'],['type','category'],['part','part']]){
      const picker=$('#la-'+mode+'-'+suffix);if(!picker)continue;picker.replaceChildren();const any=el('option','全部');any.value='';picker.append(any);
      for(const choice of [...new Set(data.units.filter(u=>(!group||scopeMatches(u,group))&&(mode==='study'||u.mode==='practice')).map(u=>u[key]).filter(Boolean))].sort()){
        const opt=el('option',choice);opt.value=choice;picker.append(opt);
      }
    }
    for(const key of filterNames){const node=$('#la-'+mode+'-'+key);if(node)node.value=prior[key]||'';}
  }
  document.addEventListener('click',event=>{
    const a=event.target.closest('a[href^="#"]');if(!a)return;
    for(const mode of ['study','practice'])if(!$('#'+mode).hidden){
      rememberFilters(mode);listPositions.set(mode+':'+scope[mode],window.scrollY);
      const target=a.getAttribute('href').slice(1);
      if(units.has(target))entryOrigins.set(target,{hash:location.hash.slice(1)||mode,mode,search:$('#la-'+mode+'-search').value});
    }
  },true);
  function unitCard(u) {
    const n=el('article','','product-content-row');n.dataset.catalogUnit=u.id;
    const content=el('div','','product-row-content'),title=link(u.id,u.title);title.className='product-content-title';content.append(title);
    if(u.id==='topical-vocabulary'&&!$('#study').hidden&&$('#la-study-search').value.trim())title.textContent='在话题词卡中查找：'+$('#la-study-search').value.trim();
    const p=unitProgress(u),meta=[u.mode==='practice'?'练习':'学习',u.skillLabel,u.topic];
    if(u.difficulty?.level)meta.push('难度 '+u.difficulty.level+'/5');
    if(u.referenceConfidence)meta.push('参考置信度'+u.referenceConfidence);
    if(u.source)meta.push(u.source);
    const info=el('p',[...new Set(meta.filter(Boolean))].join(' · '),'product-row-meta');
    if(u.referenceConfidence)info.classList.add('content-entry-metadata');
    info.title=u.difficulty?.reason||u.difficulty?.rationale||'';content.append(info);
    const actions=el('div','','product-row-actions');
    if(p.total)actions.append(el('span',p.done===p.total?'本项已完成':p.done?'已完成 '+p.done+'/'+p.total:'未开始','product-row-state'));
    const add=button(state.today.includes(u.id)?'已选':'＋ 自选',()=>toggleToday(u.id));
    add.setAttribute('aria-label',(state.today.includes(u.id)?'移出自选：':'加入自选：')+u.title);add.setAttribute('aria-pressed',String(state.today.includes(u.id)));actions.append(add);
    n.append(content,actions);return n;
  }
  function renderCards() {
    for(const mode of ['study','practice']) {
      const root=$('#'+mode);if(root.hidden)continue;
      const group=scope[mode],pick=k=>$('#la-'+mode+'-'+k)?.value||'';
      const q=folded(pick('search')),topic=pick('topic'),type=pick('type'),part=pick('part'),difficulty=pick('difficulty'),confidence=pick('confidence'),status=pick('status');
      const filtering=!!(q||topic||type||part||difficulty||confidence||status);
      rememberFilters(mode);
      const all=data.units.filter(u=>(mode==='study'&&q?true:u.mode===mode)&&scopeMatches(u,group));
      const found=all.filter(u=>{
        const p=unitProgress(u),activity=p.done===p.total&&p.total?'done':p.done?'started':'new';
        return(!topic||u.topic===topic)&&(!type||u.category===type)&&(!part||u.part===part)&&(!difficulty||String(u.difficulty?.level||'')===difficulty)&&(!confidence||u.referenceConfidence===confidence)&&(!status||status===activity)&&(!q||q.split(' ').every(term=>(corpus.get(u.id)||'').includes(term)));
      });
      root.querySelector('.la-heading h1').textContent=mode==='study'?'学习':'练习';
      root.querySelector('.la-heading > p:last-child').textContent='';
      $('#la-'+mode+'-progress').hidden=true;
      const search=$('#la-'+mode+'-search');search.placeholder=mode==='study'?'搜索全部内容、题型或话题':'搜索练习题目、题型或话题';
      const crumb=$('#la-'+mode+'-location');crumb.replaceChildren();
      for(const [code,label] of [['','全部'],...sections]){
        if(code&&!data.units.some(u=>u.mode===mode&&scopeMatches(u,code)))continue;
        const a=link(code?mode+'-'+code+'-list':mode,label);a.className='product-scope';if(group===code)a.setAttribute('aria-current','page');crumb.append(a);
      }
      const toolbar=root.querySelector('.la-toolbar');toolbar.hidden=false;
      $('#la-'+mode+'-skill').closest('label').hidden=true;
      const partNode=$('#la-'+mode+'-part');partNode.closest('label').hidden=!!group&&!['listening','speaking'].includes(group);
      const count=$('#la-'+mode+'-count');count.hidden=false;count.textContent=found.length+' 项'+(group?' · '+labelOf(group):'');
      const summary=root.querySelector('.product-filters > summary');summary.textContent='筛选'+([topic,type,part,difficulty,confidence,status].filter(Boolean).length?' · 已选 '+[topic,type,part,difficulty,confidence,status].filter(Boolean).length+' 项':'');
      const cards=$('#la-'+mode+'-cards');cards.replaceChildren();
      function groupRows(label,items,key){if(!items.length)return;const block=el('section','','product-content-group'),h=el('h2',label+' · '+items.length);block.dataset.productGroup=key;block.append(h,...items.map(unitCard));cards.append(block);}
      if(filtering||group)groupRows(q?'搜索结果':group?labelOf(group):'筛选结果',found,'results');
      else {
        const recent=found.filter(u=>/^(jiufen-close-|pr-jiufen-|pr-jijing-)/.test(u.id)).reverse();
        groupRows('新到内容',recent,'recent');
        for(const [code,label] of sections)groupRows(label,found.filter(u=>u.skill===code&&!recent.includes(u)),code);
      }
      if(!found.length){const empty=el('div','','product-empty');empty.append(el('p','没有找到匹配内容。'));empty.append(button('清除筛选与搜索',()=>{for(const k of filterNames){const n=$('#la-'+mode+'-'+k);if(n)n.value='';}renderCards();}));cards.append(empty);}
      for(const id of ['la-'+mode+'-extras','architecture-practice-extras']){const n=$('#'+id);if(n)n.hidden=true;}
      const quick=$('#la-'+mode+'-quick');if(quick)quick.hidden=!!group;
    }
  }

  function renderToday() {
    if(!todaySurfaces.some(visible))return;
    const list=$('#la-today-list');list.replaceChildren();
    const selected=state.today.map(id=>units.get(id)).filter(Boolean);
    if(!selected.length)list.append(el('p','从学习或练习中挑几项，加入自选；也可以直接开始。','la-empty'));
    for(const u of selected){const item=el('li');item.append(link(u.id,u.title),bar(unitProgress(u),u.progressLabel||'完成'),button('移出自选',()=>toggleToday(u.id)));list.append(item);}
    const plan=$('#la-plan-list');plan.replaceChildren();for(const u of selected){const item=el('li');item.append(link(u.id,u.title),bar(unitProgress(u),u.progressLabel||'完成'),button('移出自选',()=>toggleToday(u.id)));plan.append(item);}if(!selected.length)plan.append(el('li','还没选内容，直接去学习或练习中挑选即可。'));
    const resume=$('#la-resume'),last=units.get(state.last)||(learningTools[state.last]?{id:state.last,title:learningTools[state.last],isTool:true}:null);resume.replaceChildren(last?link(last.id,'继续：'+last.title):el('span','选一项内容开始，之后可以从这里继续。'));if(last&&!last.isTool)resume.append(bar(unitProgress(last),last.progressLabel||'完成'));
    $('#la-today-progress').replaceChildren(bar(M.progress(selected.map(u=>unitProgress(u).percent===100)),'项'));
    for(const p of data.projects){const area=$('[data-project="'+p.id+'"]');if(!area)continue;const ids=[...new Set(p.units)].filter(id=>units.has(id));const progress=M.progress(ids.map(id=>unitProgress(units.get(id)).percent===100));area.querySelector('[data-project-progress]').replaceChildren(bar(progress,'项'));}
  }
  function renderParts() {
    for(const {n,u} of unitProgressNodes)if(u&&visible(n))n.replaceChildren(bar(unitProgress(u),u.progressLabel||'完成'));
    for(const {n,ids} of collectionProgressNodes)if(visible(n))n.replaceChildren(bar(M.progress(ids.map(id=>unitProgress(units.get(id)).percent===100)),'单元'));
  }
  function gateValues(keys) {return Object.fromEntries(keys.map(k=>[k,String(value(k)||'')]))}
  function canOpen(gate) { const keys=gateKeys.get(gate); return M.canCheck(keys,gateValues(keys)); }
  function reveal(gate, requested) {
    if (!canOpen(gate)) {gate.open=false;gate.querySelector('.la-gate-content').hidden=true;if(requested){notify('先留下这组题的答案，再核对。不会的题可以写“暂时不会”。');const key=gateKeys.get(gate).find(k=>!M.filled(String(value(k)||'')));fields.get(key)?.focus();}return false;}
    if(requested && !state.checked[gate.id]) {const keys=gateKeys.get(gate);if(!save(M.check(state,gate.id,keys,gateValues(keys),new Date().toISOString()))){gate.open=false;return false;}}
    gate.querySelector('.la-gate-content').hidden=false;return true;
  }
  for(const gate of gates) {
    gate.open=false;gate.querySelector('.la-gate-content').hidden=true;
    gate.querySelector('summary').addEventListener('click',e=>{if(!gate.open&&!reveal(gate,true))e.preventDefault();});
    gate.addEventListener('toggle',()=>{if(gate.open)reveal(gate,true);});
  }
  function refreshGates(){for(const gate of gates)if(visible(gate))gate.classList.toggle('la-gate-locked',!canOpen(gate));}
  document.addEventListener('click',e=>{const b=e.target.closest('[data-la-unknown]');if(b){const n=fields.get(b.dataset.laUnknown);if(n&&!n.readOnly&&!n.disabled){n.value='暂时不会';n.dispatchEvent(new Event('input',{bubbles:true}));n.focus();}}});
  function focusActivity(panel,u){
    $$('[data-la-focus-hidden]').forEach(n=>n.removeAttribute('data-la-focus-hidden'));$$('.la-focus-nav').forEach(n=>n.remove());
    if(!u)return;
    const unit=document.getElementById(u.id),family=[unit];
    if(/^(reading|listening|writing1|writing2|speaking)-first$/.test(u.id))for(const suffix of ['learn','feedback','review']){const next=document.getElementById(u.id.replace(/-first$/,'-'+suffix));if(next)family.push(next);}
    function focusWithin(node){for(const child of node.children){if(family.includes(child))continue;if(family.some(target=>child.contains(target)))focusWithin(child);else child.setAttribute('data-la-focus-hidden','');}}
    focusWithin(panel);const nav=el('nav','','la-focus-nav');nav.setAttribute('aria-label','当前位置');const returnSkill=lastCategory?.mode===u.mode&&(u.relatedSkills||[]).includes(lastCategory.skill)?lastCategory.skill:u.skill;nav.append(link(u.mode+'-'+(data.navigationVersion>=3?returnSkill:groupOf(returnSkill))+'-list','← '+(u.mode==='study'?'学习':'练习')+' / '+(returnSkill===u.skill?u.skillLabel:labelOf(returnSkill))),el('span','','product-crumb-detail'));const origin=entryOrigins.get(u.id);if(origin){const back=nav.querySelector('a');back.href='#'+origin.hash;back.textContent=origin.search?'← 返回搜索结果':'← 返回'+(origin.mode==='study'?'学习内容':'练习列表');}else if(u.id==='topical-vocabulary'){const back=nav.querySelector('a');back.href='#vocabulary-review';back.textContent='← 单词';}panel.prepend(nav);
  }
  function panelRoute(){let h;try{h=decodeURIComponent(location.hash.slice(1))||(data.navigationVersion>=3?'study':'guide');}catch{return;}const n=document.getElementById(h),panel=n?.closest('main > .panel');if(!panel)return;
    let u=units.get(h)||units.get(n.closest('[data-learning-unit]')?.id);
    if(data.navigationVersion){
      const category=h.match(/^(study|practice)-(listening|reading|writing[12]?|speaking|vocabulary|phrases|shared)-list$/);
      const legacy={reading:'study-reading-list',listening:'study-listening-list',writing1:'study-writing1-list',writing2:'study-writing2-list',speaking:'study-speaking-list','practice-reading':'practice-reading-list','practice-listening':'practice-listening-list','practice-writing1':'practice-writing1-list','practice-writing2':'practice-writing2-list','practice-speaking':'practice-speaking-list','practice-phrases':'study-phrases-list',vocabulary:'study-vocabulary-list',phrases:'study-phrases-list'};
      if(legacy[h]){location.hash=legacy[h];return;}
      if(category){lastCategory={mode:category[1],skill:category[2]};restoreFilters(category[1],category[2]);}
      else if(h==='study'||h==='practice')restoreFilters(h,'');
      if(!u&&/^(reading|listening|writing1|writing2|speaking)-(learn|feedback|review)$/.test(h))u=units.get(panel.id+'-first');
      const collectionRoutes={'pp-reading':['reading','阅读练习'],'pp-listening':['listening','听力练习'],'pp-writing1':['writing1','Task 1 练习'],'pp-writing2':['writing2','Task 2 练习'],'pp-speaking':['speaking','口语练习'],'pp-vocabulary':['vocabulary','词汇练习'],'reading-case-bank':['reading','阅读原题片段'],'writing1-case-bank':['writing1','Task 1 原题片段'],'writing2-case-bank':['writing2','Task 2 原题片段']};
      const collection=collectionRoutes[h];
      if(collection&&!u){const focus={id:h,mode:'practice',skill:collection[0],skillLabel:labelOf(collection[0]),title:collection[1]};focusActivity(panel,focus);panel.dataset.laCollectionTitle=focus.title;}else{delete panel.dataset.laCollectionTitle;focusActivity(panel,u);}
      renderCards();
    }
    const owner=u?.id==='topical-vocabulary'?'vocabulary-review':panel.dataset.laCollectionTitle?'practice':data.navigationVersion&&u?u.mode:panel.dataset.laOwner||panel.id;document.body.classList.toggle('ws-wide',owner==='workspace'||owner==='development');for(const b of $$('#workspace-navigation [data-go]')){if(b.dataset.go===owner)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');}
    const sectionName={'word-review':'复习','vocabulary-review':'单词','sentence-learning':'句子','writing-workbench':'写作工作台',guide:'今天',study:'学习',practice:'练习',tests:'测试',workspace:'工作台',development:'开发工作台'}[owner]||'学习';
    $('#current-page-label').textContent=u?sectionName+' / '+u.skillLabel:((panel.id==='study'||panel.id==='practice')&&scope[panel.id]?sectionName+' / '+(groups[scope[panel.id]]||data.skills[scope[panel.id]]):panel.dataset.laCollectionTitle||panel.dataset.laTitle||sectionName);
    document.title=$('#current-page-label').textContent+' · IELTS';
    const resumeId=u?.id||(learningTools[panel.id]?panel.id:'');
    if(resumeId&&state.last!==resumeId)save({...state,last:resumeId});
    renderToday();renderParts();refreshGates();
    if(panel.id==='study'||panel.id==='practice'){const y=listPositions.get(panel.id+':'+scope[panel.id])||0;requestAnimationFrame(()=>requestAnimationFrame(()=>window.scrollTo(0,y)));}
    document.dispatchEvent(new CustomEvent('product-route-ready'));
  }
  const answerValues = id => Object.fromEntries($$('[data-test-answer="'+id+'"]').map(n=>[n.dataset.question,n.value]));
  const testFields = id => $$('[data-test-answer="'+id+'"]');
  function start(id, fresh=false){const meta=data.tests[id];if(!meta)return;
    if(fresh && !window.confirm('开始新一轮会清空当前答题框；本轮提交或草稿会保留在测试历史中。继续？'))return;
    let base=state;const previous=state.tests[id];if(fresh&&previous?.status==='running')base={...state,tests:{...state.tests,[id]:{...previous,answers:answerValues(id)}}};
    const next=M.startTest(base,id,Date.now(),meta.minutes*60000,fresh);if(!save(next))return;
    if(fresh)for(const f of testFields(id)){f.value='';f.readOnly=false;f.dispatchEvent(new Event('input',{bubbles:true}));}
    renderTests();location.hash='test-'+id;
  }
  function submit(id){if([...$('#test-'+id).querySelectorAll('[data-stop]')].some(b=>!b.disabled)){notify('请先结束并保存录音，再提交本次测试。');return;}const answers=answerValues(id),blank=Object.values(answers).filter(v=>!M.filled(v)).length;
    if(blank&&!window.confirm('还有 '+blank+' 处未作答。提交后保留空白并结束本次测试，确定提交？'))return;
    if(save(M.submitTest(state,id,answers,Date.now())))renderTests();
  }
  for(const b of $$('[data-test-start]'))b.addEventListener('click',()=>start(b.dataset.testStart));
  for(const b of $$('[data-test-submit]'))b.addEventListener('click',()=>submit(b.dataset.testSubmit));
  for(const b of $$('[data-test-retry]'))b.addEventListener('click',()=>start(b.dataset.testRetry,true));
  $('#la-start-mock').addEventListener('click',()=>{
    const ids=Object.keys(data.tests);if(ids.some(id=>state.tests[id])&&!window.confirm('开始新的四科组合练习？现有各科提交和草稿会进入历史，答题框将清空。'))return;
    const next=M.queueMock(state,Object.fromEntries(ids.map(id=>[id,answerValues(id)])),Date.now());
    // Start each section's timer only when that section is entered.
    if(!save(next))return;
    for(const id of ids)for(const f of testFields(id)){f.value='';f.readOnly=false;f.dispatchEvent(new Event('input',{bubbles:true}));}
    start('listening');
  });
  function renderTests(){
    const active=state.mock;const completed=Object.keys(data.tests).filter(id=>{const t=state.tests[id];return t?.status==='submitted'&&(!active||t.start>=active.start);});
    $('#la-mock-progress').replaceChildren(bar({done:completed.length,total:4,percent:completed.length*25},'科已提交'));
    for(const [id,meta] of Object.entries(data.tests)){
      const t=state.tests[id],panel=$('#test-'+id),body=panel.querySelector('.la-test-body'),result=panel.querySelector('.la-test-result');
      const freshForMock=active&&(!t||t.start<active.start)&&t?.status!=='running';
      const submitted=t?.status==='submitted'&&!freshForMock,running=t?.status==='running';body.hidden=!(running||submitted);result.hidden=!submitted;
      panel.querySelector('[data-test-start]').textContent=running?'继续本次':submitted?'查看本次结果':'开始本次测试';panel.querySelector('[data-test-start]').hidden=submitted;
      panel.querySelector('[data-test-submit]').hidden=!running;panel.querySelector('[data-test-retry]').hidden=!submitted;
      const answered=M.progress(Object.values(submitted?t.answers:answerValues(id)).map(M.filled));panel.querySelector('[data-test-progress]').replaceChildren(bar( answered,'已作答'));
      for(const f of testFields(id)){f.readOnly=submitted;if(submitted)f.value=t.answers[f.dataset.question]||'';}
      for(const b of panel.querySelectorAll('[data-record],[data-upload]'))b.disabled=submitted;
      for(const part of panel.querySelectorAll('[data-test-part]'))part.querySelector('[data-test-part-progress]').replaceChildren(bar(M.progress([...part.querySelectorAll('[data-test-answer]')].map(f=>M.filled(f.value))),'已作答'));
      for(const ref of panel.querySelectorAll('[data-test-reference]'))ref.hidden=!submitted;
      if(submitted){result.replaceChildren(el('h2','本次已提交'),el('p','作答 '+answered.done+' / '+answered.total+'。用时 '+Math.ceil((t.submittedAt-t.start)/60000)+' 分钟；题目完成比例与成绩分别记录。'));
        if(meta.key){const score=M.score(t.answers,meta.key);result.append(el('p',score.correct+' / '+score.verified+' 个有参考答案的题号与参考一致。'+(score.verified<40?'其余 '+(40-score.verified)+' 题暂无已核实答案，本页不生成听力总分。':'填空如有其他正确写法，请结合原文核对；不自动换算 Band。')));const table=el('table');const head=el('tr');for(const h of ['题号','我的答案','参考','核对'])head.append(el('th',h));table.append(head);for(const r of score.rows){const row=el('tr');for(const text of [r.q,r.answer||'未作答',r.expected,r.correct?'一致':'待复核'])row.append(el('td',text));table.append(row);}result.append(table);}
        else result.append(el('p',id==='writing'?'Task 1 与 Task 2 原稿均已保留。可打开参考标准检查回应题意、组织、词汇与语法。':'三个 Part 的录音文件记录均已保留。下载声音后，可按流利与连贯、词汇、语法、发音回听。'));
        const nextId=Object.keys(data.tests)[Object.keys(data.tests).indexOf(id)+1];if(active&&nextId)result.append(button('继续下一科：'+data.tests[nextId].label,()=>{location.hash='test-'+nextId;renderTests();}));
      }
      const hist=panel.querySelector('[data-test-history]');hist.replaceChildren(el('summary','以往作答 · '+(t?.history.length||0)+' 次'));for(const h of [...(t?.history||[])].reverse()){const p=el('pre',new Date(h.start).toLocaleString()+' · '+(h.status==='submitted'?'已提交':'保留的草稿')+'\n'+Object.entries(h.answers).map(([q,a])=>q+': '+a).join('\n'));hist.append(p);}
    }
    renderClocks();
  }
  function renderClocks(){for(const id of Object.keys(data.tests)){const t=state.tests[id],out=$('#test-'+id+' [data-test-clock]');if(!t||t.status!=='running'){out.textContent=t?.status==='submitted'?'已提交':'尚未开始';continue;}const left=Math.max(0,Math.ceil((t.start+t.duration-Date.now())/1000));out.textContent=left?Math.floor(left/60)+':'+String(left%60).padStart(2,'0'):'建议时间已到';out.title='计时不中断输入；完成后请提交。';}}
  // Coalesce paint work, not persistence. Keep every changed test/part in the batch.
  const dirtyTests=new Set(),dirtyTestParts=new Set();
  function queueViews(target){
    progressCache.clear();
    if(target?.dataset.testAnswer){dirtyTests.add(target.dataset.testAnswer);const part=target.closest('[data-test-part]');if(part)dirtyTestParts.add(part);}
    if(drawing)return;drawing=true;
    requestAnimationFrame(()=>{drawing=false;
      renderParts();refreshGates();renderToday();renderCards();
      const tests=[...dirtyTests],parts=[...dirtyTestParts];dirtyTests.clear();dirtyTestParts.clear();
      for(const id of tests){const out=$('#test-'+id+' [data-test-progress]');if(out)out.replaceChildren(bar(M.progress(Object.values(answerValues(id)).map(M.filled)),'已作答'));}
      for(const part of parts)part.querySelector('[data-test-part-progress]').replaceChildren(bar(M.progress([...part.querySelectorAll('[data-test-answer]')].map(f=>M.filled(f.value))),'已作答'));
    });
  }
  document.addEventListener('input',e=>{if(e.target?.dataset.save)queueViews(e.target);});
  for(const mode of ['study','practice'])for(const kind of ['search','skill','topic','type','part','difficulty','confidence','status'])$('#la-'+mode+'-'+kind)?.addEventListener('input',renderCards);
  window.addEventListener('hashchange',panelRoute);
  document.addEventListener('ielts-record-committed',()=>queueViews());
  document.addEventListener('click',event=>{if(event.target.closest('[data-freeze]'))queueViews();});
  renderTests();panelRoute();setInterval(renderClocks,1000);
  if(blocked)notify('已有安排记录无法读取，原文已保留；普通学习与原有记录入口仍可使用。');
})();
