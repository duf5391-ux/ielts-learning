(() => {
  'use strict';
  const lookup = window.IELTSLookup, host = document.querySelector('#vocabulary-review');
  const reviewHost=document.getElementById('word-review');if (!lookup || !host || !reviewHost) return;
  const DAY = 86400000, steps = [1, 3, 7, 14, 30, 60];
  let session = null, current = null, revealed = false, spelling = '', spellingCorrect = null;
  const viewedMeanings = new Set();
  const gradeLabels = {forgot:'不会',hard:'模糊',known:'会'};
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n; };
  const button = (text, fn, cls) => { const b=el('button',text,cls); b.type='button'; b.addEventListener('click',fn); return b; };
  const key = row => lookup.normalize(row.key || row.term);
  const favorites = () => lookup.getHistory().filter(row => row.favorite === true);
  const dueAt = row => { const n=Date.parse(row.review?.dueAt); return Number.isFinite(n) ? n : 0; };
  const due = row => dueAt(row) <= Date.now();
  const ordered = rows => [...rows].sort((a,b)=>dueAt(a)-dueAt(b) || (Date.parse(a.favoriteAt)||0)-(Date.parse(b.favoriteAt)||0));
  const dateLabel = value => { const n=Date.parse(value); return Number.isFinite(n) ? new Date(n).toLocaleString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '现在'; };
  function announce(text) { status.textContent=text;const n=document.getElementById('word-list-status');if(n)n.textContent=text; }
  function safe(fn) { try { return fn(); } catch(error) { announce(error.message || '记录未能更新，请先备份学习记录。'); return null; } }
  function scheduling(row, grade, at=Date.now(), independent=true) {
    const prior=row.review || {}, repetitions=Number(prior.repetitions)||0, successful=Number(prior.successfulStreak)||0;
    const scheduleGrade=grade==='known'&&!independent?'hard':grade;
    const interval = scheduleGrade==='forgot' ? 10*60000 : scheduleGrade==='hard' ? DAY : steps[Math.min(successful,steps.length-1)]*DAY;
    return {...prior,version:1,dueAt:new Date(at+interval).toISOString(),lastAt:new Date(at).toISOString(),lastGrade:grade,scheduleGrade,
      intervalMinutes:interval/60000,repetitions:repetitions+1,successfulStreak:scheduleGrade==='known'?successful+1:0,
      lapses:(Number(prior.lapses)||0)+(grade==='forgot'?1:0)};
  }
  host.replaceChildren();const links=el('nav','','word-tool-links');const reviewLink=el('a','开始复习 →');reviewLink.href='#word-review';const sentenceLink=el('a','我的句子 →');sentenceLink.href='#sentence-learning';links.append(reviewLink,sentenceLink);host.append(links);
  const heading=el('div','','vr-heading');
  const title=el('div'); title.append(el('h1','我的单词表'),el('p','查词和话题词卡的收藏都在这里，可直接标记会不会。','vr-muted'));
  heading.append(title); host.append(heading);const listStatus=el('p','','vr-muted');listStatus.id='word-list-status';listStatus.setAttribute('role','status');host.append(listStatus);
  const stats=el('div','','vr-stats'); stats.id='vr-stats'; reviewHost.append(stats);
  const controls=el('div','','vr-controls'), mode=el('select'); mode.id='vr-mode'; mode.setAttribute('aria-label','复习方式');
  [['recall','看英文 · 回忆意思'],['spelling','看释义 · 拼写词语']].forEach(([value,label])=>{ const o=el('option',label); o.value=value; mode.append(o); });
  const start=button('开始今日复习',()=>begin('due'),'vr-primary'); start.id='vr-start';
  const extra=button('加练全部收藏',()=>begin('all')); extra.id='vr-practice-all';
  controls.append(mode,start,extra); reviewHost.append(controls);
  const status=el('p','','vr-status'); status.id='vr-status'; status.setAttribute('role','status'); reviewHost.append(status);
  const stage=el('div','','vr-stage'); stage.id='vr-stage'; stage.hidden=true; reviewHost.append(stage);
  const library=el('details','','vr-library'); library.open=true;
  const summary=el('summary','查看单词表'); library.append(summary);
  const filters=el('div','','vr-controls'), search=el('input'), filter=el('select');
  search.type='search'; search.id='vr-search'; search.placeholder='搜索单词、释义或原句'; search.setAttribute('aria-label','搜索收藏的词语');
  filter.id='vr-filter'; filter.setAttribute('aria-label','单词表范围');
  [['all','全部收藏'],['due','现在该复习'],['new','还未复习'],['later','稍后复习']].forEach(([value,label])=>{ const o=el('option',label); o.value=value; filter.append(o); });
  filters.append(search,filter); library.append(filters);
  const list=el('div','','vr-list'); list.id='vr-list'; library.append(list); host.append(library);
  const legacy=el('div','','vr-legacy'); host.append(legacy);
  const note=el('details','','vr-help'); note.append(el('summary','复习如何安排？'),el('p','看英文回忆时，可以直接点“不会／模糊／会”，释义和原句按需查看。独立回忆后的“会”：下次在 1、3、7、14、30、60 天后逐步安排；模糊：1 天后；不会：10 分钟后。看过提示后的自评仍会记录，但不会增加独立回忆连续次数。'),el('p','单词表上的快捷自评只标记现在的感觉，不算完成复习，也不改到期时间。拼写仍需先尝试，拼错或查看答案后不能记为独立拼对。单次自评不代表已经掌握。'),el('p','收藏、原句、自填释义、每次复习和拼写答案均包含在“备份学习记录”及“导出查词记录”中。取消收藏只移出复习队列，查询和复习历史继续保留。'));
  reviewHost.append(note);
  function renderStats() {
    const rows=favorites(), now=rows.filter(due).length, fresh=rows.filter(r=>!r.review?.lastAt).length;
    stats.replaceChildren();
    for (const [count,label] of [[rows.length,'已收藏'],[now,'现在可复习'],[fresh,'未开始']]) { const n=el('div'); n.append(el('strong',String(count)),el('span',label)); stats.append(n); }
    start.disabled=!now; extra.disabled=!rows.length;
    summary.textContent=`查看单词表 · ${rows.length} 个词与词组`;
  }
  function renderList() {
    const q=lookup.normalize(search.value), rows=ordered(favorites()).filter(row=>
      (filter.value==='all'||filter.value==='due'&&due(row)||filter.value==='new'&&!row.review?.lastAt||filter.value==='later'&&!due(row)) &&
      lookup.normalize([row.term,row.userMeaning||row.meaning,row.context,row.chunk,row.notes].join(' ')).includes(q));
    list.replaceChildren();
    if (!rows.length) { list.append(el('p',favorites().length?'没有符合条件的词语。':'还没有收藏。查词或在话题词卡中点“收藏”，就能在这里复习。','vr-empty'));if(!favorites().length){const a=el('a','去话题词卡挑选 →');a.href='#topical-vocabulary';list.append(a);} return; }
    let shown=0;
    const more=button('显示更多',renderMore,'vr-more');
    function renderMore() {
      more.remove(); rows.slice(shown,shown+30).forEach(row=>list.append(listCard(row))); shown+=30;
      if (shown<rows.length) { more.textContent=`显示更多（还有 ${rows.length-shown} 个）`; list.append(more); }
    }
    renderMore();
  }
  function listCard(row) {
    const card=el('article','','vr-list-card'), head=el('div','','vr-card-heading'); head.append(el('h3',row.term),el('span',!row.review?.lastAt?'新收藏':due(row)?'可以复习':`下次 ${dateLabel(row.review.dueAt)}`,'vr-tag'));
    card.dataset.vrKey=key(row);card.append(head);
    const quick=el('div','','vr-quick-marks');quick.setAttribute('role','group');quick.setAttribute('aria-label',row.term+' 的快捷自评');
    for(const grade of ['forgot','hard','known']){const b=button(gradeLabels[grade],()=>quickMark(row.term,grade));b.dataset.vrQuickGrade=grade;b.setAttribute('aria-pressed',String(row.selfAssessment?.grade===grade));quick.append(b);}
    card.append(quick,el('p',row.selfAssessment?`当前自评：${gradeLabels[row.selfAssessment.grade]||'未标记'} · 不计为完成复习`:'直接标记现在会不会；要检验回忆，再开始复习。','vr-muted'));
    const meaningDetails=el('details','','vr-meaning-details');meaningDetails.append(el('summary','释义与原句'),el('p',row.userMeaning||row.meaning||'尚无释义，可在下方补充。','vr-meaning'));
    if(row.chunk)meaningDetails.append(el('p',row.chunk,'vr-chunk'));
    if(row.context)meaningDetails.append(el('blockquote',row.context));
    if(row.sourceRoute&&document.getElementById(row.sourceRoute)){const source=el('a','回到原材料 →');source.href='#'+row.sourceRoute;if(row.topicCardId)source.dataset.uiTopicCard=row.topicCardId;meaningDetails.append(source);}
    meaningDetails.addEventListener('toggle',()=>{if(meaningDetails.open)viewedMeanings.add(key(row));});card.append(meaningDetails);
    const actions=el('div','','vr-controls'); actions.append(button('复习这个词',()=>begin('one',row)),button('查详细用法',event=>lookup.open(row.term,row.context,event.currentTarget)),button('取消收藏',()=>safe(()=>lookup.setFavorite(row.term,false)))); card.append(actions);
    const details=el('details','','vr-edit'); details.append(el('summary','补充释义与我的例句'));
    const meaning=el('textarea'), note=el('textarea'); meaning.rows=2; meaning.value=row.userMeaning||''; meaning.placeholder=row.meaning?'留空使用词典释义':'填入已核对的释义'; note.rows=2; note.value=row.notes||'';
    const meaningLabel=el('label','我的释义（优先用于复习）'); meaningLabel.append(meaning); const noteLabel=el('label','我的例句／记忆笔记'); noteLabel.append(note);
    details.append(meaningLabel,noteLabel,button('保存补充',()=>safe(()=>{lookup.updateEntry(row.term,{userMeaning:meaning.value.trim(),notes:note.value.trim()});announce('释义与笔记已记录。');}))); card.append(details);
    return card;
  }
  function quickMark(term,grade){
    const result=safe(()=>lookup.updateEntry(term,{selfAssessment:{grade,at:new Date().toISOString(),source:'word-list'}},{requirePersistence:true}));
    announce(result?`${term}：已标记“${gradeLabels[grade]}”。复习时间保持不变。`:'本次标记未保存，原记录未改动，请处理页面保存提示后重试。');
  }
  function renderLegacy() {
    const pending=lookup.getHistory().filter(r=>r.favorite!==true&&r.status==='pending'&&(r.lookupVersion!==2||r.legacyReviewMark==='pending')); legacy.replaceChildren();
    if(!pending.length)return;
    legacy.append(el('p',`查询记录里另有 ${pending.length} 个“待复习”旧标记。可逐个收藏，也可以一起加入。`,'vr-muted'),button('把旧待复习词加入单词表',()=>safe(()=>{
      pending.forEach(row=>lookup.setFavorite(row.term,true)); announce(`已加入 ${pending.length} 个词，旧查询记录与复习标记保留。`);
    })));
  }
  function refresh() { host.dataset.vrSession=String(!!session);renderStats(); renderList(); renderLegacy(); }
  function begin(scope, row) {
    const rows=scope==='one'?[row]:ordered(favorites()).filter(r=>scope==='all'||due(r));
    if(!rows.length){announce('现在没有待复习词，可以继续收藏或稍后回来。');return;}
    session={keys:rows.map(key),index:0,done:0,mode:mode.value,scope,practice:scope==='all'||scope==='one'&&!due(row)};host.dataset.vrSession='true'; stage.hidden=false; library.open=true;location.hash='word-review'; nextCard();
  }
  function nextCard() {
    const all=favorites(); current=null;
    while(session.index<session.keys.length&&!current){current=all.find(r=>key(r)===session.keys[session.index]);if(!current)session.index++;}
    revealed=false; spelling=''; spellingCorrect=null;
    if(!current){stage.replaceChildren(el('h3',session.practice?'这一轮加练完成':'这一轮复习完成'),el('p',`已完成 ${session.done} 个词。`+(session.practice?'加练答案已记录，下次复习时间保持不变。':'每个词的下次时间已安排好。')),button('返回单词表',()=>{stage.hidden=true;library.open=true;session=null;refresh();location.hash='vocabulary-review';}));announce(`本轮完成 ${session.done} 个词。`);return;}
    renderStage(); stage.scrollIntoView({behavior:'smooth',block:'nearest'});
  }
  function renderStage() {
    stage.replaceChildren();
    const progress=el('div','','vr-card-heading'); progress.append(el('p',`本轮 ${session.index+1} / ${session.keys.length} · 已完成 ${session.done}`+(session.practice?' · 加练不改变复习时间':''),'vr-muted'),button('暂停本轮',()=>{stage.hidden=true;library.open=true;session=null;refresh();announce('已完成的复习保留，其余词语仍在单词表中。');})); stage.append(progress);
    const card=el('article','','vr-flashcard');
    if(session.mode==='spelling'&&!revealed){
      const meaning=current.userMeaning||current.meaning;
      card.append(el('p','根据释义写出收藏的英文词或词组。','vr-kicker'));
      if(meaning){
        // Do not leak the answer if a dictionary definition contains its headword.
        const escaped=current.term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
        card.append(el('p',meaning.replace(new RegExp('\\b'+escaped+'\\b','gi'),'______'),'vr-prompt'));
      }else card.append(el('p','这个词尚无释义。本次先查看词语，补充释义后再练拼写。','vr-prompt'));
      const form=el('form'), answer=el('input'); answer.id='vr-spelling'; answer.type='text'; answer.autocomplete='off'; answer.spellcheck=false; answer.setAttribute('aria-label','拼写收藏的英文词语'); answer.placeholder='输入英文词或词组'; answer.value=spelling;
      const submit=el('button','核对拼写','vr-primary');submit.type='submit'; form.append(answer,submit); form.addEventListener('submit',event=>{event.preventDefault();spelling=answer.value.trim();if(!spelling){announce('先尝试输入，再核对；也可以点“想不起来，查看答案”。');return;}spellingCorrect=lookup.normalize(spelling)===lookup.normalize(current.term);reveal();});
      if(meaning)card.append(form);
      card.append(button('想不起来，查看答案',()=>{spelling=answer.value.trim();spellingCorrect=false;reveal();})); stage.append(card); answer.focus();
    }else{
      card.append(el('p',session.mode==='spelling'?'核对词语与用法':'先想一想：这个词是什么意思？怎么用？','vr-kicker'),el('h3',current.term,'vr-word'));
      if(current.phonetic)card.append(el('p','/'+current.phonetic.replace(/^\/+|\/+$/g,'')+'/','vr-muted'));
      if(!revealed){card.append(el('p','直接选择这次是否记得；需要时再查看释义。','vr-muted'),gradeButtons(),button('查看释义与原句',reveal)); stage.append(card);return;}
      if(session.mode==='spelling')card.append(el('p',spellingCorrect?'拼写一致。再检查意思和用法是否也记得。':spelling?`你的拼写：${spelling}。对照上方正确词语，再决定复习间隔。`:'本次查看了答案，下次再试拼写。','vr-spelling-result'));
      card.append(el('p',current.userMeaning||current.meaning||'尚无释义。请在单词表中补充，或重新查词。','vr-meaning'));
      if(current.chunk)card.append(el('h4','常用搭配'),el('p',current.chunk,'vr-chunk'));
      if(current.context)card.append(el('h4','当时读到的原句'),el('blockquote',current.context));
      if(current.example&&current.example!==current.context)card.append(el('h4','用法例句'),el('p',current.example));
      if(current.notes)card.append(el('h4','我的例句／笔记'),el('p',current.notes));
      card.append(el('p','试着用这个词说一个新句子，再选择这次记得怎样。','vr-muted'));
      card.append(gradeButtons()); stage.append(card);
    }
  }
  function independentAttempt(){
    if(session.mode==='spelling')return spellingCorrect===true;
    const justLookedUp=Date.now()-(Date.parse(current.lastAt)||0)<10*60000;
    return !revealed&&!viewedMeanings.has(key(current))&&!justLookedUp;
  }
  function gradeButtons(){
      const grades=el('div','','vr-grades');
      const independent=independentAttempt();
      for(const [grade,label] of [['forgot','忘记'],['hard','模糊'],['known','认识']]){
        const planned=scheduling(current,grade,Date.now(),independent), minutes=planned.intervalMinutes, when=session.practice?'记录加练':minutes<60?`${minutes} 分钟后`:`${minutes/1440} 天后`;
        const b=button(`${gradeLabels[grade]} · ${when}`,()=>gradeCard(grade),grade==='known'?'vr-primary':'');b.dataset.vrGrade=grade;
        // A revealed/mismatched spelling answer cannot earn a successful recall streak.
        if(session.mode==='spelling'&&spellingCorrect!==true&&grade==='known'){b.disabled=true;b.title='拼写未独立答对，可选“模糊”或“忘记”。';} grades.append(b);
      }
      if(!independent&&session.mode==='recall')grades.append(el('p','本次看过提示，选择“会”也不会增加独立回忆连续次数。','vr-grade-note'));
      return grades;
  }
  function reveal(){revealed=true;renderStage();stage.querySelector('[data-vr-grade]')?.focus();}
  function gradeCard(grade) {
    if(!session||!current||(!revealed&&session.mode!=='recall'))return;
    if(session.mode==='spelling'&&grade==='known'&&spellingCorrect!==true)return;
    const target=current, now=Date.now(),independent=independentAttempt();
    const result=safe(()=>lookup.updateEntry(target.term,row=>({...(!session.practice?{review:scheduling(row,grade,now,independent),status:'reviewed',reviewedAt:new Date(now).toISOString()}:{}),
      reviews:[...(Array.isArray(row.reviews)?row.reviews:[]),{at:new Date(now).toISOString(),grade,mode:session.mode,practice:session.practice,answerRevealed:revealed,independentAttempt:independent,answer:session.mode==='spelling'?spelling:null,spellingCorrect:session.mode==='spelling'?spellingCorrect:null,priorDueAt:row.review?.dueAt||null}]}),{requirePersistence:true}));
    if(!result){announce('这次复习未保存，当前词语保留在这里。请处理页面保存提示后重试。');return;}
    session.done++;session.index++;announce(`${target.term}：`+(session.practice?'加练已记录，复习时间保持不变':`下次 ${dateLabel(result.review.dueAt)}`));nextCard();
  }
  search.addEventListener('input',renderList);filter.addEventListener('change',renderList);
  window.addEventListener('ielts-lookup-changed',refresh);
  window.addEventListener('hashchange',refresh);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)renderStats();});
  // Refresh due counts after a ten-minute relearning interval while this page stays open.
  setInterval(()=>{if(!document.hidden)renderStats();},30000);
  window.IELTSVocabularyReview=Object.freeze({refresh,begin:()=>begin('due'),plan:scheduling});
  refresh();
})();
