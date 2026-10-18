import {initializeMotion} from './motion.js?v=509356376181';
import {installHostBridge} from './host-bridge.js?v=509356376181';
import {currentMixedQuestion} from './mixed-practice.js?v=509356376181';
import {importMarkedBank} from './engine.js?v=509356376181';
import {loadEnglishDictionary,englishMeaning} from './english-dictionary.js?v=509356376181';
import {appearanceControl,initializeAppearance,refreshAppearance} from './appearance.js?v=509356376181';
import {createTranslations,createTranslationView} from './translations.js?v=509356376181';
import {ensureDailyPlan,createState,startSession,startGroupedSession,newWords,dueWords,unfinishedWords,getBankPending,prioritizeBankWords,compareBankWords,mergeStudyWords,importWordBank,act,getStats,getCurrentView,getSessionStatus} from './engine.js?v=509356376181';
import {createStore} from './storage.js?v=509356376181';
import {createAccount} from './account.js?v=509356376181';
import {config} from './config.js?v=509356376181';
import {createCorpus,corpusWithBank,rotateMemoryPassages,memorySnippet} from './corpus.js?v=509356376181';
import {createLookup,wordTokens,normalizeLookupTerm} from './lookup.js?v=509356376181';
import {importListening,listeningSelection,dictationQueue,createPronunciation,withListeningAudio} from './listening.js?v=509356376181';
import {listeningEntry,listeningPage,listeningLearning,listeningResults} from './listening-view.js?v=509356376181';

const app=document.querySelector('#app'),dialog=document.querySelector('#dialog');
const icons={back:'<path d="m14 5-7 7 7 7"/>',next:'<path d="m10 5 7 7-7 7"/>',close:'<path d="m6 6 12 12M18 6 6 18"/>',star:'<path d="m12 3 2.8 5.7 6.3.9-4.5 4.4 1.1 6.2L12 17.3l-5.7 2.9 1.1-6.2-4.5-4.4 6.3-.9Z"/>',note:'<path d="M14 4H5v16h14v-9M9 14l1-4 8-8 4 4-8 8Z"/>',sound:'<path d="M4 9v6h4l5 4V5L8 9ZM17 8c3 2 3 6 0 8m3-11c5 4 5 10 0 14"/>',pause:'<path d="M8 5v14M16 5v14"/>',more:'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',check:'<path d="m5 12 4 4L19 6"/>',light:'<path d="M8 16c0-2-3-3-3-7a7 7 0 0 1 14 0c0 4-3 5-3 7ZM9 20h6M10 23h4"/>'};
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=(name,label,action,extra='')=>`<button type="button" class="icon-button ${extra}" aria-label="${esc(label)}" title="${esc(label)}" data-action="${action}"><svg viewBox="0 0 24 24" aria-hidden="true">${icons[name]||icons.more}</svg></button>`;
const button=(label,action,cls='',extra='')=>`<button type="button" class="button ${cls}" data-action="${action}" ${extra}>${label}</button>`;
const names={learn:'新词学习',review:'到期复习',practice:'速刷',spelling:'拼写练习',dictation:'听力听写'};
let collection,baseData,baseWords=[],baseIds=new Set(),lookupEngine=null,lookupPromise=null,bankFingerprint=null,encounter=null,encounterRequest=0,bankFilter='unknown',bankSearch='',corpus,words=[],legacyWords=[],queryTopic='',wordSort='topic',store,account,accountSession={status:'checking'},route=location.hash.slice(1).split('?')[0]||'home',filter='all',search='',toastTimer,modalWordId=null,selectedScope=null,quietPending=0,scrollTimer;
let listeningWords=[],listeningLoadError='',listeningSeed=null,seedImportRun=null;
try{const raw=new URLSearchParams(location.hash.split('?')[1]||'').get('import');if(raw)listeningSeed=JSON.parse(atob(raw.replace(/-/g,'+').replace(/_/g,'/')));}catch{listeningLoadError='本次勾选链接不完整，请重新打开对话中的入口。';}
let bankSeed=null,bankSeedError='',bankSeedRun=null,bankSeedCount=0;
const decodeBankSeed=raw=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(atob(raw.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0))));
try{const raw=new URLSearchParams(location.hash.split('?')[1]||'').get('words');if(raw)bankSeed=decodeBankSeed(raw);}catch{bankSeedError='勾选链接不完整，请重新打开保存的入口。';}
const encodeSeed=value=>btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(value)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
const seedFragment=()=>{const params=new URLSearchParams();if(listeningSeed)params.set('import',encodeSeed(listeningSeed));if(bankSeed)params.set('words',encodeSeed(bankSeed));return params.size?'?'+params.toString():'';};
const allStudyWords=()=>[...words,...listeningWords];
let bridge;
const wordById=id=>words.find(w=>w.id===id)||listeningWords.find(w=>w.id===id)||legacyWords.find(w=>w.id===id);
const pronunciation=createPronunciation();let listeningAudio={busy:false,error:''},audioEpoch=0;
function stopListeningAudio(){audioEpoch++;pronunciation.cancel();listeningAudio={busy:false,error:''};}
function listeningState(){try{return listeningSeed?importListening(state(),listeningSeed,listeningWords):state();}catch{return state();}}
async function applyListeningSeed(){
 if(!listeningSeed)return;if(seedImportRun)return seedImportRun;
 const seed=listeningSeed,owner=identityEpoch;
 seedImportRun=(async()=>{await store.update(s=>importListening(s,seed,listeningWords));
  if(owner!==identityEpoch)return;
  if(store.identity?.uid){listeningSeed=null;history.replaceState(null,'','#'+route+seedFragment());}
  render();})();
 try{await seedImportRun;}finally{seedImportRun=null;}
}
async function applyBankSeed(){
 if(!bankSeed||!['guest','signed-in'].includes(accountSession.status))return;
 if(bankSeedRun)return bankSeedRun;
 const seed=bankSeed,owner=identityEpoch;
 bankSeedRun=(async()=>{
  await ensureLookup();if(owner!==identityEpoch)return;
  const rows=lookupEngine.prepareBankImport(seed);
  await store.update(s=>importWordBank(s,rows,words));
  if(owner!==identityEpoch)return;
  bankSeedCount=rows.length;bankSeedError='';
  if(store.identity?.uid){bankSeed=null;history.replaceState(null,'','#'+route+seedFragment());}
  syncBank();render();
 })();
 try{await bankSeedRun;}catch(error){if(owner===identityEpoch){bankSeedError=error.message;render();}}
 finally{bankSeedRun=null;if(owner!==identityEpoch&&bankSeed)queueMicrotask(()=>applyBankSeed());}
}
function bankImportNotice(){
 if(bankSeedError)return `<p class="info-block" role="status">${esc(bankSeedError)} ${bankSeed?button('重试加入','bank-import'):''}</p>`;
 if(!bankSeed&&!bankSeedCount)return '';
 return `<p class="info-block" role="status">${bankSeedCount?`已载入 ${bankSeedCount} 个勾选词。${store.identity?.uid?'已合并到生词本，已有学习进度保留。':'登录后保存到你的账号；这个入口可重新打开。'}`:'正在载入勾选词…'}</p>`;
}
async function playListening(){
 const s=state().session,w=view().word;if(!s||s.mode!=='dictation'||s.paused||!w||!['memory','spelling'].includes(s.phase))return;
 const owner=identityEpoch,token=++audioEpoch,guard={type:'DICTATION_HEARD',sessionId:s.id,wordId:w.id,round:s.spellingRound,spellingIndex:s.spellingIndex};
 listeningAudio={busy:true,error:''};render();
 try{if(!w.audio)throw Error('听力音源信息暂未加载，请刷新重试。');
  const audioURL=new URL('../data/listening-audio/'+w.id+'.wav',import.meta.url);audioURL.searchParams.set('v',w.audio.sha256.slice(0,16));
  await pronunciation.play(w.term,w.audio.locale,audioURL.href);if(owner!==identityEpoch||token!==audioEpoch)return;
  listeningAudio={busy:false,error:''};if(s.phase==='spelling')await update(guard);else render();
 }catch(e){if(owner===identityEpoch&&token===audioEpoch){listeningAudio={busy:false,error:e.message};render();}}
}
async function beginListening(kind='new'){
 await applyListeningSeed();
 const selected=dictationQueue(state(),listeningWords,Date.now(),undefined,kind);
 if(!selected.length){toast(kind==='review'?'现在没有到期的听力词。':'已选新词已学完，可以复习或再挑一小页。');return;}
 await begin('dictation',selected,kind);
}
async function handleListening(action,el){
 switch(action){
 case'listening':closeDialog();goto('listening');return true;
 case'listen-start':await beginListening();return true;
 case'listen-review':await beginListening('review');return true;
 case'listen-screen':await applyListeningSeed();await store.update(s=>listeningSelection(s,listeningWords,{type:'open'}));render();document.querySelector('[data-listen-choice]')?.focus();return true;
 case'listen-selection-later':{const selection=document.querySelector('.listen-selection');if(selection){selection.open=false;selection.querySelector('summary')?.focus();}return true;}
 case'listen-confirm-next':
 case'listen-confirm':{
  const ids=JSON.parse(el.dataset.ids),keepSelecting=action==='listen-confirm-next';let count=0,confirmed=false;
  await store.update(s=>{
   const next=listeningSelection(s,listeningWords,{type:'confirm',ids,continue:keepSelecting});
   if(next!==s){count=s.listening.draft.selectedIds.length;confirmed=true;}return next;
  });
  if(!confirmed)return true;
  render();
  const selection=document.querySelector('.listen-selection');
  if(keepSelecting&&selection){
   selection.open=true;selection.scrollIntoView({block:'start'});
   selection.querySelector('[data-listen-choice]')?.focus({preventScroll:true});
  }else (document.querySelector('[data-action="listen-screen"]')||document.querySelector('.listen-list summary'))?.focus();
  toast(`${count?`已加入 ${count} 项`:'已跳过本页'}${keepSelecting&&selection?'，继续挑下一页':'，本页已筛完'}`);
  return true;
 }
 case'listen-back':stopListeningAudio();await update({type:'PAUSE'});goto('listening');return true;
 case'listen-play':await playListening();return true;
 case'listen-learn-next':stopListeningAudio();await update({type:'DICTATION_LEARN_NEXT',wordId:el.dataset.word,sessionId:el.dataset.session});if(state().session?.phase==='spelling')void playListening();return true;
 case'listen-history':{const attempts=state().history.filter(e=>e.type==='spelling'&&e.mode==='dictation'&&e.sessionId===el.dataset.id);openDialog('听写结果',listeningResults(attempts,listeningWords));return true;}
 default:return false;
 }
}
const state=()=>store.state;
const sentenceTranslation=createTranslationView(createTranslations(),()=>render());
function translationKey(p){return `${identityEpoch}:${store?.identity?.uid||'guest'}:${state().session?.id||''}:${view().wordId||''}:${p.id}`;}
function translationState(p){return sentenceTranslation.select(translationKey(p),p.text);}
async function toggleTranslation(){const list=activeParagraphs(),p=list[passagePage(list)];if(p)await sentenceTranslation.toggle(translationKey(p),p.text);}
function translationMarkup(p){const t=translationState(p);return `<div class="sentence-meaning"><button class="text-btn" data-action="sentence-meaning" aria-expanded="${t.open}" aria-controls="sentence-translation">${t.open?'收起句意':'显示句意'}</button>${t.open?`<div id="sentence-translation" class="sentence-translation" aria-live="polite">${t.status==='ready'?`<p>${esc(t.entry.zh)}</p><small>${t.entry.kind==='reviewed'?'参考译文':'机器参考译文'}</small>`:t.status==='loading'?'正在加载句意…':t.status==='missing'?'这条语料的译文待补。':`${esc(t.error)}，收起后可重新点击。`}</div>`:''}</div>`;}
let identityEpoch=0,identityRenderPending=false;
const stats=()=>getStats(state(),words);
const view=()=>getCurrentView(state(),allStudyWords());
function toast(text){const t=document.querySelector('#toast');t.textContent=text;t.classList.add('toast-show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('toast-show'),3600);}
function goto(value){route=value;location.hash=value+seedFragment();render();window.scrollTo(0,0);}
function openDialog(title,body,actions=''){dialog.innerHTML=`<div class="dialog-head"><h2 id="dialog-title">${esc(title)}</h2>${icon('close','关闭','close-dialog')}</div><div class="dialog-body">${body}</div>${actions?`<div class="dialog-actions">${actions}</div>`:''}`;if(!dialog.open)dialog.showModal();}
function closeDialog(){dialog.close();modalWordId=null;encounter=null;encounterRequest++;}
function syncLabel(){return ({synced:'已自动同步',syncing:'正在自动同步',pending:'正在保存',offline:'已存本机 · 自动重试中','download-available':'云端已更新 · 结束编辑后接续',conflict:'记录有冲突'})[store?.syncStatus?.phase]||'同步记录';}
function syncButton(){return accountSession.status==='signed-in'?`<button class="text-btn sync-status" data-action="sync">${esc(syncLabel())}</button>`:'';}
function syncDialog(){openDialog('两台设备都有新记录','<p>本机和云端都有修改，已暂停覆盖。选择继续使用哪一份；另一份会作为副本保留在当前账号的导出记录中。</p>',button('导出全部记录','export')+button('继续用本机这份','sync-local')+button('使用云端这份','sync-cloud','primary'));}
function accountLabel(){return accountSession.status==='signed-in'?'我的账号':accountSession.status==='checking'?'正在恢复账号…':accountSession.status==='unavailable'?'账号连接中…':'登录保存';}
const navIcons={home:'<path d="m3 10 9-7 9 7v10H3Z"/><path d="M9 20v-7h6v7"/>',book:'<path d="M12 5v16M3 4c4-1 7 0 9 2 2-2 5-3 9-2v15c-4-1-7 0-9 2-2-2-5-3-9-2Z"/>',listening:'<path d="M4 14v-3a8 8 0 0 1 16 0v3M4 12h3v8H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2Zm16 0h-3v8h3a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2Z"/>',bank:'<path d="M5 3h14v18l-7-4-7 4Z"/><path d="M9 9h6m-3-3v6"/>',stats:'<path d="M4 4v16h17M8 15v-4m5 4V7m5 8v-6"/>',settings:'<circle cx="12" cy="12" r="3"/><path d="M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1Z"/>'};
const navSvg=name=>`<svg viewBox="0 0 24 24" aria-hidden="true">${navIcons[name]}</svg>`;
function shell(body){
 const signed=accountSession.status==='signed-in',labels={home:'学习',book:'语境词本',listening:'听力必会单词',bank:'我的生词',stats:'学习记录',settings:'设置'};
 return `<div class="shell"><aside class="sidebar"><a class="brand" href="#home"><span class="brand-icon">a</span><span>语境</span></a><nav class="nav-links" aria-label="主导航">${['home','listening','book','bank','stats'].map(r=>`<a class="nav-link ${route===r?'active':''}" href="#${r}" ${route===r?'aria-current="page"':''}>${navSvg(r)}<span>${labels[r]}</span></a>`).join('')}</nav><div class="sidebar-bottom"><a class="nav-link ${route==='settings'?'active':''}" href="#settings" aria-label="设置">${navSvg('settings')}<span>设置</span></a>${config.hostEntry?`<a class="host-link" target="_top" href="${esc(globalThis.parent&&globalThis.parent!==globalThis?'/#study':config.hostEntry)}">← 返回学习网站</a>`:''}</div></aside><div class="workspace"><header class="nav"><div class="workspace-location"><span>我的学习空间</span><b>/</b>${labels[route]||'学习'}</div><div class="workspace-tools">${syncButton()}${appearanceControl()}<button class="account" data-action="account"><span class="account-avatar" aria-hidden="true">${signed?'我':'访'}</span>${accountLabel()}</button></div></header>${body}</div></div>`;
}
function countMetric(label,num,hint=''){return `<div class="metric"><small>${label}</small><div class="number">${num}</div>${hint?`<div class="hint">${hint}</div>`:''}</div>`;}
function resumeProgress(s){
 if(s.mode==='dictation')return s.phase==='spelling'?`听写第 ${s.spellingIndex+1} / ${s.spellingQueue.length} 项`:`记忆第 ${s.index+1} / ${s.queue.length} 项`;
 return `${s.mode==='spelling'?s.spellingIndex:s.index} / ${s.queue.length}`;
}
function home(){
 const s=stats(),originalStats=getStats(state(),baseWords.length?baseWords:words),scopedStats=getStats(state(),corpus.ranked(queryTopic).filter(w=>w.passages.length)),pending=getSessionStatus(state())==='pending';
 return shell(`<main class="home"><div class="home-head"><div><h1>今天，学一点。</h1><p class="subtle">${new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'long'})}</p></div><button class="text-btn" data-action="about">词本说明</button></div>${pending?`<div class="resume-strip"><div><strong>接着上次学</strong><span>${names[state().session.mode]} · ${resumeProgress(state().session)}</span></div><button class="button primary" data-action="resume">继续这一轮</button></div>`:''}<div class="study-paths">${listeningEntry(listeningState())}<section class="context-entry"><div class="path-heading"><span class="path-icon">${navSvg('book')}</span><div><h2>语境记忆</h2><p>在原文里理解词义，再检验拼写。</p></div><button class="text-btn" data-action="book" aria-label="打开语境词本">↗</button></div><div class="path-metrics"><div><strong>${Math.min(scopedStats.newRemaining,s.dailyNewRemaining)+scopedStats.unfinished}</strong><span>今日待学</span></div><div><strong>${scopedStats.due}</strong><span>到期复习</span></div><button class="text-btn" data-action="settings">调整计划</button></div><div class="path-actions">${button('开始学习','start-learn',pending?'':'primary')}${button(scopedStats.due?`复习全部到期 · ${scopedStats.due} 词`:'暂无到期复习','start-review','',scopedStats.due?'':'disabled')}</div><div class="path-foot" data-daily-plan><span>每日新增 ${s.dailyPlan.target} 词 · 未完成内容持续结转</span><span>今日完成 ${s.todayCompleted} / ${s.dailyPlan.total} 词</span><span>复习按到期数量，可随时暂停</span></div><div class="collection-progress" title="${esc(collection.title)}"><span>原词表 ${originalStats.total} 词</span><div class="progress-track"><span style="width:${originalStats.completionPercent}%"></span></div><span>已学 ${originalStats.learned} / ${originalStats.total}</span></div></section></div>${frequencyPanel()}<div class="home-bottom">${bankSummary()}<div class="overview"><div><strong>${s.familiar}</strong><span>熟词</span></div><div><strong>${s.favorites}</strong><span>收藏</span></div><div><strong>${s.completedSessions}</strong><span>完成轮次</span></div></div></div><p class="home-save-note">${accountSession.status==='signed-in'?'学习记录自动保存到当前账号。':'当前为试学，登录后可保存学习记录。'}</p></main>`);
}
function highlight(p){let out='',at=0;for(const span of [...(p.highlight||[])].sort((a,b)=>a.start-b.start)){if(span.start<at)continue;out+=esc(p.text.slice(at,span.start))+`<mark>${esc(p.text.slice(span.start,span.end))}</mark>`;at=span.end;}return out+esc(p.text.slice(at));}
function learningTop(s,current){const mixed=s.phase==='mixed';return `<header class="learning-top">${icon('back','返回首页并暂停','leave')}<div class="session-progress"><span>${names[s.mode]}</span><span class="thin-line"><span style="width:${mixed?s.mixedRound.progress.reduce((total,p)=>total+p.step/s.mixedRound.recipe.length,0)/s.mixedRound.wordIds.length*100:s.queue.length?((s.mode==='spelling'?s.spellingIndex:current.memoryCompleted??s.index)/s.queue.length*100):100}%"></span></span><span>${mixed?`组内练习 · ${s.mixedRound.progress.filter(p=>p.completed).length} / ${s.mixedRound.wordIds.length} 词`:current.isRetry?`本轮再记 · 还剩 ${current.memoryRemaining} 词`:`${s.phase==='memory'?current.index+1:s.phase==='spelling'?s.spellingIndex+1:s.index} / ${s.phase==='spelling'?s.spellingQueue.length:s.queue.length}`}</span></div><div class="learning-tools">${appearanceControl()}${syncButton()}${current?.word && s.phase==='memory'?icon('star','收藏当前词','favorite',state().favorites.includes(current.wordId)?'selected':'')+icon('note','写笔记','note'):''}${s.phase!=='complete'?icon('pause','暂停','pause'):''}${icon('more','更多选项','session-more')}</div></header>`;}
function meaning(word){return `<div class="meaning-panel"><div class="term-row"><span class="term">${esc(word.term)}</span>${icon('sound','朗读单词','speak-word')}<span class="phonetic">${esc(word.phonetic||'')}</span></div><p class="definition"><span class="pos">${esc(word.pos)}</span>${esc(word.meaning)}</p>${englishMeaning(word)}${word.collocations?.length?`<div class="collocations">${word.collocations.map(c=>`<span><strong>${esc(c.text)}</strong>${esc(c.meaning)}</span>`).join('')}</div>`:''}${state().notes[word.id]?`<p class="reader-note">${esc(state().notes[word.id])}</p>`:''}</div>`;}
function activeWordIds(){const s=state().session;if(!s)return[];const n=s.plan.groupSize,start=Math.floor((view().index||0)/n)*n;const ids=s.queue.slice(start,start+n),current=view().wordId;if(current&&!ids.includes(current))ids.push(current);return ids;}
function activeParagraphs(){
 const s=state().session,w=view().word;if(!w)return[];
 const topic=s.context?.topic??(corpus.topics.includes(s.context?.title)?s.context.title:'');
 const shared=(s.context?.paragraphIds||[]).map(id=>corpus.paragraphs.get(id)).filter(p=>p?.matches?.some(m=>m.wordId===w.id)&&(!topic||p.topics.includes(topic)));
 const own=corpus.forWord(w.id,topic,12),found=new Set(shared.map(p=>p.id));
 for(const p of own)if(!found.has(p.id)){shared.push(corpus.paragraphs.get(p.id)||p);found.add(p.id);}
 const result=shared.slice(0,12);
 return rotateMemoryPassages(result,state().history,w.id,view().isBrowsing?view().answer?.eventId:null).map(p=>memorySnippet(p,w.id)).filter(Boolean);
}
function passagePage(list){
 const s=state().session,v=view(),anchor=s?.context?.scroll;
 const saved=anchor?.wordId===v.wordId&&anchor?.revealed===v.revealed?list.findIndex(p=>p.id===anchor.paragraphId):-1;
 return Math.max(0,Math.min(list.length-1,saved>=0?saved:s.passageIndex||0));
}
function paragraphMarkup(p,focusId,selectedIds=[]){
 const selected=new Set(selectedIds),spans=(p.matches||[]).filter(m=>m.wordId===focusId||selected.has(m.wordId)).flatMap(m=>m.highlight.map(h=>({...h,wordId:m.wordId})));
 const labels=new Map();for(const entry of Object.values(state().wordBank||{}))for(const form of new Set([entry.term,...(entry.forms||[]),...(entry.acceptedSpellings||[])].map(normalizeLookupTerm))){const candidates=labels.get(form)||[];candidates.push(entry);labels.set(form,candidates);}
 let at=0,out='';for(const token of wordTokens(p.text)){
  out+=esc(p.text.slice(at,token.start));const hit=spans.find(h=>h.start<=token.start&&h.end>=token.end);
  const candidates=labels.get(token.form)||[],exactBank=candidates.find(w=>w.origins?.some(o=>o.paragraphId===(p.parentParagraphId||p.id)&&o.start===(p.sentenceStart||0)+token.start&&o.end===(p.sentenceStart||0)+token.end))||candidates.find(w=>normalizeLookupTerm(w.term)===token.form)||(candidates.length===1?candidates[0]:null);
  const label=exactBank?.label==='known'?'known-token':exactBank?.label==='unknown'?'unknown-token':'';
  let text=esc(token.text);if(hit)text=`<mark class="${hit.wordId===focusId?'focus-word':'shared-word'}" data-term="${esc(wordById(hit.wordId)?.term)}">${text}</mark>`;
  out+=`<span class="word-token ${label}" data-action="lookup-word" data-token="${esc(token.text)}" data-pid="${esc(p.id)}" data-start="${token.start}" data-end="${token.end}" title="标记 ${esc(token.text)}：会 / 不会">${text}</span>`;at=token.end;
 }
 return out+esc(p.text.slice(at));
}
function passageCard(p,v,s,index){
 const selected=activeWordIds(),hits=(p.matches||[]).filter(m=>selected.includes(m.wordId)),hasFocus=hits.some(m=>m.wordId===v.wordId);
 return `<article class="corpus-card ${hasFocus?'has-focus':''}" data-pid="${esc(p.id)}"><div class="corpus-card-heading"><span>${String(index+1).padStart(2,'0')} · ${esc(p.topics?.join(' / ')||'文章正文')}</span><span>${hasFocus?(p.isFragment?'原文片段':'原文例句'):'本组交叉语料'}</span></div><p class="passage" lang="en" data-pid="${esc(p.id)}">${paragraphMarkup(p,v.wordId,selected)}</p><div class="source-line"><button class="source-button" data-action="source" data-pid="${esc(p.memoryParentId||p.id)}">查看上下文 · ${esc(p.sourceLabel)} ↗</button><button class="icon-button" aria-label="朗读这段语料" data-action="speak-passage" data-pid="${esc(p.id)}"><svg viewBox="0 0 24 24">${icons.sound}</svg></button></div>${translationMarkup(p)}<p class="shared-terms">${hits.map(m=>`<span class="${m.wordId===v.wordId?'current':''}">${esc(wordById(m.wordId).term)}${v.revealed?' · '+esc(wordById(m.wordId).meaning):''}</span>`).join('')}</p></article>`;
}
function learning(){
 const s=state().session;if(!s)return home();if(s.mode==='dictation')return listeningLearning(state(),listeningWords,listeningAudio);const v=view();let content='';
 if(!lookupEngine&&s.queue.some(id=>state().wordBank?.[id]))content='<main class="loading">正在恢复个人词库的原文句子…</main>';
 else if(s.paused)content=`<main class="paused"><span class="eyebrow">TAKE A BREATH</span><h1>休息一下</h1><p>继续时，回到刚才的语料。</p>${button('继续学习','resume','primary')}</main>`;
 else if(s.phase==='complete')content=complete(s);
 else if(s.phase==='spelling-result')content=spellingResult(s);
 else if(s.phase==='spelling')content=spelling(s,v);
 else if(s.phase==='mixed')content=mixedPractice(s);
 else if(v.word){const list=activeParagraphs(),w=v.word,page=passagePage(list),p=list[page],pending=s.pendingGrade;
 const controls=v.isBrowsing?button('回到当前词','return-current','primary'):button('不认识','grade-forgot',pending==='forgot'?'primary choice-picked':'',`data-word="${esc(w.id)}" data-session="${esc(s.id)}" data-prompt="${esc(v.promptToken)}" title="本轮继续出现，直到认识"`)+button('认识','grade-known',pending==='known'?'primary choice-picked':pending?'':'primary',`data-word="${esc(w.id)}" data-session="${esc(s.id)}" data-prompt="${esc(v.promptToken)}" title="认识了，拉长后续复习间隔"`)+button('会（双击）','dismiss-current','skip-known',`data-word="${esc(w.id)}" data-session="${esc(s.id)}" data-prompt="${esc(v.promptToken)}" title="双击确认：跳过这个词，以后不再安排学习和复习"`);
 content=`<main class="reader memory-stage"><div class="reader-heading"><div><div class="context-title">${esc(s.context?.title||'真实文章语料')}</div><p class="memory-target">${v.isBrowsing?'回看上一词':v.isRetry?'本轮再记':'当前记忆'} <strong class="focus-label">${esc(w.term)}</strong></p></div><button class="text-btn" data-action="lookup-input">选词 / 查词</button></div><section class="memory-card" aria-label="当前词的语料记忆卡"><div class="corpus-reader card-reading" data-reader-key="${esc(readerKey())}:${page}">${p?passageCard(p,v,s,page):'<p class="empty">这个词暂未检索到可核实的原文语料。</p>'}</div><nav class="passage-navigation" aria-label="切换当前词的语料"><button data-action="passage-prev" ${page<=0?'disabled':''}>← 上一句</button><span class="passage-counter">语料 ${list.length?page+1:0} / ${list.length}</span><button data-action="passage-next" ${page>=list.length-1?'disabled':''}>下一句 →</button></nav>${v.revealed?`<div class="recall-answer">${meaning(w)}${pending?`<p class="choice-message">${pending==='forgot'?'先记住词义，继续后会在本轮再次遇到这个词。':'核对词义后继续，之后会隔更久再复习。'}</p>`:''}</div>`:`<div class="recall-prompt"><span>读语料，判断自己是否认识标出的词。</span><button class="text-btn" data-action="reveal">查看词义</button></div>`}</section></main><footer class="learning-footer memory-footer"><div class="footer-side"><button data-action="previous" ${s.index?'':'disabled'}>上一词</button></div><div class="footer-actions">${controls}</div><div class="footer-side">${pending&&!v.isBrowsing?button('继续 →','grade-continue','primary',`data-word="${esc(w.id)}" data-session="${esc(s.id)}" data-prompt="${esc(v.promptToken)}"`):'<span class="keyboard">← 不认识　→ 认识</span>'}</div></footer>`;}
 return `<div class="learning ${s.phase==='mixed'?'mixed-learning':''}">${learningTop(s,v)}${content}</div>`;
}
function readerKey(){const s=state().session;return s?`${store.identity?.uid||'guest'}:${s.id}:${view().wordId}:${Number(view().revealed)}`:'';}
async function saveAnchor(){
 clearTimeout(scrollTimer);
 const s=state().session,reader=document.querySelector('.corpus-reader');if(!s?.context||!reader||s.paused||view().isBrowsing)return;
 const top=reader.getBoundingClientRect().top;
 const cards=[...reader.querySelectorAll('.corpus-card')],active=cards.find(el=>el.getBoundingClientRect().bottom>top+70)||cards.at(-1);
 if(!active)return;
 const index=s.context.paragraphIds.indexOf(active.dataset.pid),offset=Math.round(top-active.getBoundingClientRect().top);
 const previous=s.context.scroll;
 if(previous?.wordId===view().wordId&&previous.paragraphId===active.dataset.pid&&previous.offset===offset&&previous.revealed===s.revealed)return;
 await update({type:'CONTEXT_PASSAGE',...(index>=0?{index}:{}),wordId:view().wordId,sessionId:s.id,scroll:{wordId:view().wordId,paragraphId:active.dataset.pid,offset}},true);
}
function restoreAnchor(){requestAnimationFrame(()=>{
 const s=state().session,reader=document.querySelector('.corpus-reader'),saved=s?.context?.scroll;
 if(!reader||!saved||saved.wordId!==view().wordId||saved.revealed!==view().revealed)return;
 const card=reader.querySelector(`[data-pid="${CSS.escape(saved.paragraphId)}"]`);
 if(card)reader.scrollTop+=card.getBoundingClientRect().top-reader.getBoundingClientRect().top+saved.offset;
});}

const mixedNames={meaning:'英文选中文',word:'中文选英文',spelling:'独立拼写',recall:'无提示回忆'};
function mixedPractice(s){
 const r=s.mixedRound,q=currentMixedQuestion(r),f=r.feedback,completed=r.progress.filter(p=>p.completed).length;
 const answer=q.type==='meaning'?q.meaning:q.term;
 let body='';
 if(['meaning','word'].includes(q.type))body=`<div class="mixed-options">${q.options.map((o,i)=>`<button class="mixed-option ${f?(o.id===q.correctAnswer?'is-correct':o.id===f.selectedAnswer?'is-wrong':''):''}" data-action="mixed-answer" data-answer="${esc(o.id)}" data-question="${esc(q.id)}" ${f?'disabled':''}><span>${i+1}</span>${esc(o.label)}</button>`).join('')}</div>${f?'':button('暂时想不起','mixed-forgot','text-btn',`data-question="${esc(q.id)}"`)}`;
 else if(q.type==='spelling')body=`<label class="sr-only" for="mixed-input">输入英文单词</label><input id="mixed-input" class="spell-input" value="${esc(s.mixedInput)}" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" ${f?'readonly':''} aria-label="输入英文单词">${s.mixedRevealed&&!f?`<p class="mixed-answer">${esc(q.term)}</p>`:''}${f?'':`<div class="inline-actions">${button('检查拼写','mixed-submit','primary',`data-question="${esc(q.id)}"`)}${button('查看答案，再练一次','mixed-spell-skip','',`data-question="${esc(q.id)}"`)}</div>`}`;
 else body=`${s.mixedRevealed||f?`<p class="mixed-answer">${esc(q.meaning)}</p>${f?'':`<div class="inline-actions">${button('还需再记','mixed-answer','',`data-answer="forgot" data-question="${esc(q.id)}"`)}${button('独立想起了','mixed-answer','primary',`data-answer="known" data-question="${esc(q.id)}"`)}</div>`}`:button('显示释义，核对回忆','mixed-reveal','primary')}`;
 return `<main class="mixed-stage"><p class="eyebrow">${esc(mixedNames[q.type])} · 本词第 ${q.step+1} 步</p><h1 class="mixed-prompt">${esc(q.prompt)}</h1>${body}${f?`<div class="mixed-feedback ${f.correct?'':'retry'}" role="status"><strong>${f.correct?'本步完成':'本词从第一步重新练习，稍后再次出现'}</strong><p>${esc(answer)}${q.type==='meaning'?'':` · ${esc(q.meaning)}`}</p></div>`:''}<p class="subtle mixed-status">本组 ${completed} / ${r.wordIds.length} 词完成 · 连续通过 ${r.recipe.length} 步完成一个词</p></main><footer class="learning-footer"><div class="footer-side">${button('暂停','pause','text-btn')}</div><div class="footer-actions">${f?button('继续 →','mixed-next','primary',`data-question="${esc(q.id)}"`):''}</div><div class="footer-side"></div></footer>`;
}
function spelling(s,v){const w=v.word,r=v.spellingResult;const feedback=r?(r.correct?'拼对了':r.hinted&&r.matched?'借助提示拼对了':'再记一下这个词'):'';return `<main class="spell"><span class="eyebrow">${s.spellingRound?'RECALL AGAIN':'SPELL THE WORD'}</span><p class="spell-meaning">${esc(w.meaning)}</p><label class="sr-only" for="spelling-input">输入英文单词</label><input id="spelling-input" class="spell-input" value="${esc(s.spellingInput)}" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" ${s.spellingRevealed?'readonly':''} placeholder="" aria-label="输入英文单词">${s.spellingHinted&&!r?`<div class="spell-hint">${esc(w.term.slice(0,s.hintLevel))}${'·'.repeat(Math.max(0,w.term.length-s.hintLevel))}</div>`:''}<div class="spell-feedback ${r&&!r.correct?'wrong':''}" role="status">${feedback}${r?`<span class="correct-answer">${esc(w.term)}</span>`:''}</div></main><footer class="learning-footer"><div class="footer-side">${icon('light','提示一个字母','spell-hint')}${s.spellingRevealed?'':'<button data-action="spell-skip">不会拼</button>'}</div><div class="footer-actions">${s.spellingRevealed?button('下一词 →','spell-next','primary'):button('检查拼写','spell-submit','primary')}</div><div class="footer-side"><span class="keyboard">Enter ${s.spellingRevealed?'下一词':'检查'}</span></div></footer>`;}
function spellingResult(s){const wrong=s.spellResults.filter(r=>!r.correct);return `<main class="result"><div class="result-symbol">✓</div><h1>这一组，拼写完成</h1><div class="result-summary">${countMetric('独立拼对',s.spellResults.length-wrong.length)}${countMetric('再记一遍',wrong.length)}</div><div class="result-list">${s.spellResults.map(r=>`<div class="result-word"><strong>${esc(wordById(r.wordId).term)}</strong><span>${esc(wordById(r.wordId).meaning)}</span><span class="word-result">${r.correct?'✓':r.hinted?'用过提示':'再练'}</span></div>`).join('')}</div><div class="inline-actions" style="justify-content:center">${wrong.length?button(`只练错词（${wrong.length}）`,'retry-wrong'):''}${button(s.index>=s.queue.length||s.mode==='spelling'?'查看本轮结果':'继续下一组 →','continue','primary')}</div></main>`;}
function dueText(p){if(!p)return '未学习';if(p.status==='familiar')return '已标熟';if(!p.dueAt)return '未安排复习';const mins=Math.ceil((p.dueAt-Date.now())/60000);return mins<=0?'待复习':mins<60?`${mins} 分钟后复习`:mins<1440?`${Math.ceil(mins/60)} 小时后复习`:`${Math.ceil(mins/1440)} 天后复习`;}
function complete(s){if(s.emptyReason)return `<main class="result"><div class="result-symbol">✓</div><h1>${s.emptyReason==='nothing-due'?'现在没有到期单词':'本次计划已完成'}</h1><p class="info-block">${s.emptyReason==='nothing-due'?'可以先学新词，或从词本里选词速刷。':'可以调整每日数量，或去词本里选词练习。'}</p>${button('返回学习首页','home','primary')}${button('打开词本','book')}</main>`;const sum=s.summary;return `<main class="result"><div class="result-symbol">✓</div><h1>记忆又加深了一点</h1><div class="result-summary">${sum.mode==='spelling'?countMetric('本轮单词',s.queue.length)+countMetric('拼写次数',sum.spellingAttempts)+countMetric('独立拼对',sum.spellingCorrect):countMetric('本轮学习',sum.studied)+countMetric('记住了',sum.known)+countMetric('再复习',sum.forgot)}</div><div class="result-list">${s.queue.map(id=>`<div class="result-word"><strong>${esc(wordById(id).term)}</strong><span>${esc(wordById(id).meaning)}</span><button class="word-result text-btn" data-action="familiar" data-word="${esc(id)}">${dueText(state().progress[id])}${state().progress[id]?.status==='familiar'?'':' · 标熟'}</button></div>`).join('')}</div><div class="inline-actions" style="justify-content:center">${button('返回首页','home','primary')}${button('再练这一组','practice-session')}${s.mode==='learn'?button('继续学新词 →','start-learn'):''}</div></main>`;}
function topicSelect(){return `<label class="topic-select"><span>文章话题</span><select data-topic aria-label="按文章话题检索"><option value="">全部话题</option>${corpus.topics.map(t=>`<option value="${esc(t)}" ${queryTopic===t?'selected':''}>${esc(t)}</option>`).join('')}</select></label>`;}
function filteredWords(){const list=(baseWords.length?baseWords:words).filter(w=>(!search||`${w.term} ${w.meaning}`.toLowerCase().includes(search.toLowerCase()))&&(filter==='all'||filter==='favorites'&&state().favorites.includes(w.id)||filter==='notes'&&state().notes[w.id]||filter==='new'&&newWords(state(),[w]).length||filter==='familiar'&&state().progress[w.id]?.status==='familiar'||filter==='learned'&&Number.isFinite(state().progress[w.id]?.introducedAt)));return corpus.ranked(queryTopic,list,wordSort);}
function frequencyPanel(){const available=corpus.ranked(queryTopic,baseWords.length?baseWords:words,wordSort).filter(w=>w.passages.length),list=newWords(state(),available).slice(0,6);return `<section class="frequency-panel"><div class="section-heading"><div><h2>语境词本 · ${esc(queryTopic||'接下来学习的词')}</h2><p class="subtle">${queryTopic?'按文章话题相关性选词':'按原词表顺序学习'} · ${newWords(state(),available).length} 个可学新词</p></div>${topicSelect()}</div><div class="frequency-preview">${list.length?list.map(w=>`<button data-action="word-detail" data-word="${esc(w.id)}"><strong>${esc(w.term)}</strong><span>${w.passages.filter(p=>!queryTopic||p.topics.includes(queryTopic)).length} 段${queryTopic?'本话题':''}语料</span><small>${esc(w.meaning)}</small></button>`).join(''):'<p class="empty">这个话题已没有可学新词，可以换个话题。</p>'}</div><div class="frequency-footer"><span class="subtle">“会”直接跳过并补入新词，不占每日名额。</span><button class="text-btn" data-action="book">查看${queryTopic?'本话题单词':'全部 303 词'} →</button></div></section>`;}

function book(){const list=filteredWords();return shell(`<main class="content"><div class="page-title"><div><h1>${esc(collection.title)}</h1></div><button class="text-btn" data-action="print">导出词表 ↗</button></div><div class="toolbar"><input class="search" type="search" placeholder="搜索单词或词义" aria-label="搜索单词或词义" value="${esc(search)}">${topicSelect()}<select class="sort-select" data-sort aria-label="词表排序"><option value="topic" ${wordSort==='topic'?'selected':''}>话题相关</option><option value="original" ${wordSort==='original'?'selected':''}>原词表顺序</option></select></div><div class="filters">${[['all','全部'],['new','未学'],['learned','已学'],['familiar','熟词'],['favorites','收藏'],['notes','笔记']].map(([id,title])=>`<button class="chip ${filter===id?'active':''}" data-action="filter" data-filter="${id}">${title}</button>`).join('')}</div><div class="section-heading" style="margin-top:24px"><p class="subtle">检索到 ${list.length} 词</p><div class="inline-actions">${button('速刷这些词','practice-filter')}${button('拼写这些词','spelling-filter')}</div></div><div class="word-list">${list.length?list.map(w=>`<div class="word-row"><button class="word-open" data-action="word-detail" data-word="${esc(w.id)}">${esc(w.term)}</button><span class="word-meaning">${esc(w.meaning)}</span><span class="word-status">${w.semanticFrequency?.acceptedArticleCount||0} / 132 篇<br>${w.passages.length?`${w.passages.length} 段语料`:'语料待补'}</span><button class="icon-button ${state().favorites.includes(w.id)?'selected':''}" data-action="favorite" data-word="${esc(w.id)}" aria-label="${state().favorites.includes(w.id)?'取消收藏':'收藏'} ${esc(w.term)}"><svg viewBox="0 0 24 24">${icons.star}</svg></button></div>`).join(''):'<p class="empty">没有符合当前筛选的词。<br>可以换个话题或搜索条件。</p>'}</div><p class="sample-note">原词表完整保留 303 词。频次来自已检索的 132 篇剑雅正文；补充资料中的命中另列，不加入这个分母。</p></main>`);}
function frequencyInfo(){openDialog('高频的依据',`<p>统计范围是剑桥雅思 11–21 Academic 的 44 套、132 篇阅读正文，排除题干、答案和讲解。按<strong>命中的不同文章数</strong>优先，再按出现次数排序。</p><p>只计算完整词和明确的屈折、英美拼写变体；已核对检索片段与词表基本含义的关系。同一文章出现多次，只计一篇。</p><p>这是当前材料范围内的实际频次，不是官方发布的历年考频。补充雅思阅读资料提供更多上下文，单独标来源，不抬高剑雅频次。</p>`);}

function recordWordIds(run){return [...new Set(state().history.filter(e=>e.sessionId===run.sessionId&&e.type===(run.mode==='spelling'?'spelling':'memory')&&!e.undone).map(e=>e.wordId))];}
function recordStatus(run){return ({complete:'已完成',archived:'已保留旧词本轮次',active:'进行中',paused:'已暂停'})[run.outcome]||'提前结束';}
function recordRuns(){
 const runs=state().history.filter(e=>e.type==='session').slice().reverse(),s=state().session;
 if(s&&s.phase!=='complete'&&!runs.some(r=>r.sessionId===s.id)){
  const run={id:s.id,sessionId:s.id,mode:s.mode,at:s.lastActionAt,outcome:s.paused?'paused':'active'};
  run.studied=recordWordIds(run).length;
  if(run.studied)runs.unshift(run);
 }
 return runs;
}
function records(){const s=stats(),runs=recordRuns();return shell(`<main class="content"><div class="page-title"><div><div class="eyebrow">YOUR PROGRESS</div><h1>一点点，记得更多</h1></div>${button('导出记录','export')}</div><div class="stats-grid">${[['累计学词',s.learned],['今日新学',s.todayLearned],['今日复习',s.todayReviewed],['收藏单词',s.favorites]].map(([l,n])=>`<div class="stat-card"><small>${l}</small><strong>${n}</strong></div>`).join('')}</div><div class="section-heading"><h2>学习记录</h2><span class="subtle">${runs.length} 轮</span></div>${runs.length?runs.map(r=>`<div class="history-row"><div><strong>${names[r.mode]}</strong><p class="subtle">${new Date(r.at).toLocaleString('zh-CN')}</p></div><span>${recordWordIds(r).length} 词 · ${recordStatus(r)}</span><button class="text-btn" data-action="history-detail" data-id="${esc(r.id)}">查看 →</button></div>`).join(''):'<p class="empty">还没有提交过学习判断。<br>每学一个词都会记录，无需完成整组或当天计划。</p>'}<p class="sample-note">${accountSession.status==='signed-in'?'每次判断立即保存，单个词完成循环或拼写后加入复习，无需学满25词。云端同步结果见右上角。':'当前是试学，刷新后进度不会保留。'}</p></main>`);}
function settings(){const s=state().settings;return shell(`<main class="content" style="max-width:790px"><div class="page-title"><div><h1>学习设置</h1></div></div><div class="settings-section"><div class="setting-row"><div>每日新词<small>需要记忆的新词数，熟词跳过后自动补位</small></div><select data-setting="newPerDay" aria-label="每日新词">${[5,10,15,20,25,30,50,100,300].map(n=>`<option value="${n}" ${s.newPerDay===n?'selected':''}>${n} 词</option>`).join('')}</select></div><div class="setting-row"><div>每组词数<small>新词按组完成组合练习；复习按全部到期数量进行</small></div><select data-setting="groupSize" aria-label="每组词数">${[1,5,6,10,15,20].map(n=>`<option value="${n}" ${s.groupSize===n?'selected':''}>${n} 词</option>`).join('')}</select></div>${[['mixedPractice','组内组合练习','语境初记 → 英文选中文 → 中文选英文 → 拼写（可选）→ 无提示回忆；答错后重练该词'],['spellAfterLearn','新词学后拼写','每组语料记忆完成后，检验拼写'],['spellAfterReview','复习后拼写','全部到期词复习后，检验拼写'],['autoSpeak','自动朗读语料','浏览器语音朗读，跟随语料切换']].map(([id,title,hint])=>`<label class="setting-row"><span>${title}<small>${hint}</small></span><input class="switch" type="checkbox" data-setting="${id}" ${s[id]?'checked':''} aria-label="${title}"></label>`).join('')}<div class="setting-row"><span>发音</span><select data-setting="voice" aria-label="发音"><option value="en-GB" ${s.voice==='en-GB'?'selected':''}>英式</option><option value="en-US" ${s.voice==='en-US'?'selected':''}>美式</option></select></div></div><div class="setting-row"><div>网站账号<small>账号沿用网站，词本进度独立</small></div>${button(accountSession.status==='signed-in'?'账号信息':'登录','account')}</div><div class="info-block"><p>已接入原来的 ${baseWords.length||303} 词。按文章话题选择单词与正文，熟词自动跳过补位；学习和复习仍以词为单位。</p><p>组合练习逐词累计连续通过的步骤，答错后从该词第一步重练。首次复习在记忆完成后安排，后续按作答表现调整。</p></div><div class="inline-actions">${button('导出记录','export')}${button('语料与版本说明','about')}</div></main>`);}
let dailyPlanRun=null,dailyPlanRetryAt=0;
function saveDailyPlan(){
 if(!store || route!=='home' || !['signed-in','guest'].includes(accountSession.status) || dailyPlanRun || Date.now()<dailyPlanRetryAt)return;
 const ids=words.map(w=>w.id);
 if(ensureDailyPlan(state(),Date.now(),ids)===state())return;
 dailyPlanRun=Promise.resolve().then(()=>store.update(s=>ensureDailyPlan(s,Date.now(),ids)))
  .catch(error=>{dailyPlanRetryAt=Date.now()+30000;toast(error.message);})
  .finally(()=>{dailyPlanRun=null;});
}
function render(){
 if(!store||quietPending>0&&!identityRenderPending)return;
 const canPreserveInput=!identityRenderPending,previousInput=document.querySelector('#spelling-input, #mixed-input');
 identityRenderPending=false;
 const focused=document.activeElement,choiceId=focused?.dataset?.listenChoice,selectionOpen=document.querySelector('.listen-selection')?.open;
 const menuOpen=!!document.querySelector('.appearance[open]'),scene=document.querySelector('[data-listen-scene]')?.dataset.listenScene;
 const themeFocus=focused?.closest?.('.appearance')?(focused.dataset.styleChoice?`[data-style-choice="${focused.dataset.styleChoice}"]`:focused.dataset.themeChoice?`[data-theme-choice="${focused.dataset.themeChoice}"]`:focused.matches('[data-theme-auto]')?'[data-theme-auto]':'.appearance>summary'):null;
 refreshAppearance(route==='learn'&&!!state().session&&state().session.phase!=='complete');
 const previous=document.querySelector('.corpus-reader'),oldKey=previous?.dataset.readerKey,top=previous?.scrollTop||0;
 syncBank();queryTopic=state().settings.studyTopic||'';const active=route==='learn';if(!active||state().session?.phase!=='memory'||state().session?.paused)sentenceTranslation.select(null,'');app.innerHTML=active?learning():route==='book'?book():route==='bank'?bankPage():route==='listening'?shell(listeningPage(listeningState(),listeningWords,{importPending:!!listeningSeed,loadError:listeningLoadError,persistent:!!store.identity?.uid})):route==='stats'?records():route==='settings'?settings():home();
 saveDailyPlan();
 const reader=document.querySelector('.corpus-reader');
 if(reader){if(oldKey===reader.dataset.readerKey)reader.scrollTop=top;else restoreAnchor();reader.addEventListener('scroll',()=>{clearTimeout(scrollTimer);scrollTimer=setTimeout(saveAnchor,220);},{passive:true});}
 const selection=document.querySelector('.listen-selection');if(selection&&selectionOpen!==undefined)selection.open=selectionOpen;
 const sameScene=scene===document.querySelector('[data-listen-scene]')?.dataset.listenScene;
 const nextInput=document.querySelector('#spelling-input, #mixed-input');
 // A sync acknowledgement may replace the state object without changing the prompt.
 // Retain the live editor (including selection) only when its saved value agrees.
 if(canPreserveInput&&(scene||state().session?.phase==='mixed')&&sameScene&&previousInput&&nextInput&&previousInput.id===nextInput.id&&(previousInput.value===nextInput.value||focused===previousInput)&&previousInput.readOnly===nextInput.readOnly)nextInput.replaceWith(previousInput);
 if(menuOpen&&sameScene){const menu=document.querySelector('.appearance');if(menu)menu.open=true;}
 const restoreFocus=choiceId?document.querySelector(`[data-listen-choice="${choiceId}"]`):menuOpen&&sameScene&&themeFocus?document.querySelector(themeFocus):null;
 if(restoreFocus)restoreFocus.focus({preventScroll:true});
 else if(active&&state().session?.phase==='mixed'&&!state().session?.paused)requestAnimationFrame(()=>{if(!dialog.open)document.querySelector('#mixed-input')?.focus();});
 else if(active&&state().session?.phase==='spelling'&&!state().session?.paused&&!menuOpen)requestAnimationFrame(()=>{if(!dialog.open&&!document.querySelector('.appearance[open]'))document.querySelector('#spelling-input')?.focus();});
}
async function update(action,quiet=false){if(action.type==='GRADE'){const list=activeParagraphs();action={...action,passageId:list[passagePage(list)]?.memoryParentId||list[passagePage(list)]?.id};}const beforeId=view().wordId,beforeIndex=state().session?.passageIndex;if(quiet)quietPending++;try{await store.update(s=>act(s,action,['MARK_UNKNOWN','MARK_KNOWN'].includes(action.type)?words:allStudyWords()));if(quiet)return;render();const current=view();if(state().session?.mode!=='dictation'&&state().settings.autoSpeak&&route==='learn'&&state().session?.phase==='memory'&&(beforeId!==current.wordId||beforeIndex!==state().session.passageIndex))speakCurrent(false);if(action.type==='REVEAL')requestAnimationFrame(()=>{const reader=document.querySelector('.reader');if(reader)reader.scrollTop=0;});}catch(error){toast(error.message);}finally{if(quiet)quietPending--;}}
async function begin(mode,scope=null,listeningKind='new'){
 const ownerEpoch=identityEpoch;
 if(Object.keys(state().wordBank||{}).length){await ensureLookup();syncBank();if(scope)scope=scope.map(w=>wordById(w.id)).filter(Boolean);}
 if(ownerEpoch!==identityEpoch)throw new Error('账号已切换，请在当前账号重新开始。');
 if(!scope?.length&&scope!==null){toast('没有可练习的单词');return;}
 if(getSessionStatus(state())==='pending'){
  const previous=state().session;
  const sameScope=mode==='dictation'||scope===null||(scope.length===previous.queue.length&&scope.every(w=>previous.queue.includes(w.id)));
  const sameTask=previous.mode===mode&&sameScope&&(mode==='dictation'?previous.plan.listeningKind===listeningKind:(previous.context?.topic||'')===queryTopic);
  if(sameTask){await handle('resume');return;}
  selectedScope={mode,words:scope,listeningKind};
  openDialog('还有一轮未完成',`<p>上次：${esc(names[previous.mode])} · ${esc(resumeProgress(previous))}。本次选择：${esc(names[mode])} · ${esc(mode==='dictation'?'听力必会单词':queryTopic||'全部话题')}。已完成的词会保留。</p>`,button('继续上次','resume')+button('结束上次并开始','replace-session','primary'));return;
 }
 if(mode==='dictation'){await store.update(s=>startSession(s,scope||[],mode,Date.now(),{listeningKind}));if(ownerEpoch===identityEpoch)goto('learn');return;}
 let ranked=corpus.ranked(queryTopic,scope||words,wordSort).filter(w=>state().progress[w.id]?.status!=='familiar'&&(!w.bankEntry||w.bankEntry.ready));
 if(mode!=='spelling')ranked=ranked.filter(w=>w.passages.some(p=>!queryTopic||p.topics.includes(queryTopic)));
 if(mode==='learn'){const pendingIds=new Set(getBankPending(state()).map(e=>e.id));const newIds=new Set([...unfinishedWords(state(),ranked),...newWords(state(),ranked)].map(w=>w.id));ranked=prioritizeBankWords(state(),ranked.filter(w=>pendingIds.has(w.id)||newIds.has(w.id)));}
 if(mode==='practice')ranked=prioritizeBankWords(state(),ranked);
 if(mode==='review')ranked=dueWords(state(),ranked);
 const selected=ranked.map(w=>w.id);
 if(!selected.length&&mode!=='spelling'){
  const title=mode==='review'?'当前范围没有到期单词':mode==='learn'&&!stats().dailyNewRemaining?'今日新词计划已完成':'当前范围没有可开始的语料新词';
  const message=mode==='review'?'可以换个话题复习，或从词本里选词速刷。':stats().dailyNewRemaining?'已学过的词保留在词本；尚未检索到语料的词标为“语料待补”。可以换个话题或查看全部词。':'可以调整每日数量，或从词本里选词练习。';
  openDialog(title,`<p>${message}</p>`,button('关闭','close-dialog')+button('打开词本','book','primary'));return;
 }
 const paragraphs=corpus.retrieve(selected.slice(0,state().settings.groupSize),queryTopic,10);
 if(mode==='spelling')await store.update(s=>startSession(s,ranked,mode));
 else await store.update(s=>startGroupedSession(s,words,{id:`retrieval-${Date.now().toString(36)}`,title:queryTopic||'全部话题',topic:queryTopic,refillSkipped:mode==='learn',mixedRecipe:mode==='learn'&&s.settings.mixedPractice?['meaning','word',...(s.settings.spellAfterLearn?['spelling']:[]),'recall']:undefined,wordIds:selected,paragraphIds:paragraphs.map(p=>p.id)},mode));
 if(ownerEpoch!==identityEpoch)return;goto('learn');if(state().settings.autoSpeak&&state().session?.phase==='memory')speakCurrent(false);
}

async function ensureLookup(){
 if(lookupEngine)return lookupEngine;
 if(!lookupPromise)lookupPromise=(async()=>{
  const resources=await Promise.all(['lookup.json','search-corpus.json'].map(async name=>{const r=await fetch(new URL('../data/'+name,import.meta.url));if(!r.ok)throw new Error('原文检索库暂未载入，请稍后重试');return r.json();}));
  lookupEngine=createLookup({...baseData,words:baseWords},resources[0],resources[1]);bankFingerprint=null;syncBank();return lookupEngine;
 })().catch(error=>{lookupPromise=null;throw error;});
 return lookupPromise;
}
function syncBank(){
 if(!baseData||!store)return;
 const bank=state().wordBank||{};
 if(!lookupEngine){
  words=mergeStudyWords(corpus.words,state());
  if(Object.keys(bank).length)ensureLookup().then(()=>render()).catch(e=>toast(e.message));
  return;
 }
 const fingerprint=JSON.stringify([store.identity?.uid||null,bank]);
 if(fingerprint===bankFingerprint)return;
 corpus=corpusWithBank(baseData,bank,lookupEngine);words=corpus.words;baseWords=words.filter(w=>baseIds.has(w.id));bankFingerprint=fingerprint;
}
function bankSummary(){
 const bank=Object.values(state().wordBank||{}),unknown=bank.filter(e=>e.label==='unknown'),known=bank.length-unknown.length;
 return `<section class="bank-summary"><div><strong>我的生词</strong><span>${unknown.length} 个不会 · ${known} 个会</span><small>${unknown.some(e=>e.pending&&e.ready)?'高频生词优先进入下一组，其他词不插队':'在原文点词或选词，标记会 / 不会'}</small></div><button class="text-btn" data-action="bank">打开生词库 →</button></section>`;
}
function bankList(which=bankFilter){
 return Object.values(state().wordBank||{}).filter(e=>(which==='all'||e.label===which)&&(!bankSearch||`${e.term} ${e.meaning}`.toLowerCase().includes(bankSearch.toLowerCase()))).map(e=>wordById(e.id)||{...e,passages:[],bankEntry:e}).sort(compareBankWords);
}
function bankPage(){
 const all=Object.values(state().wordBank||{}),list=bankList();
 return shell(`<main class="content bank-content">${bankImportNotice()}<div class="page-title"><div><h1>我的生词</h1><p class="subtle">从读到的原文中选词，用更多真实句子记住它。</p></div>${button('开始下一组','start-learn','primary')}</div><div class="toolbar"><input class="bank-search input" type="search" placeholder="搜索我的词或词义" aria-label="搜索我的生词" value="${esc(bankSearch)}">${button('检索一个词','lookup-input')}</div><div class="filters">${[['unknown','不会，需记忆'],['known','会，不需记忆'],['all','全部']].map(([value,label])=>`<button class="chip ${bankFilter===value?'active':''}" data-action="bank-filter" data-filter="${value}">${label} · ${value==='all'?all.length:all.filter(e=>e.label===value).length}</button>`).join('')}</div><div class="section-heading" style="margin-top:22px"><p class="subtle">${list.length} 个词</p>${list.some(w=>w.bankEntry?.label==='unknown'&&w.bankEntry?.ready)?button('速刷不会的词','bank-practice'):''}</div><div class="word-list">${list.length?list.map(w=>{const e=w.bankEntry||state().wordBank[w.id];return `<div class="word-row bank-row" data-bank-id="${esc(w.id)}" data-label="${e.label}"><button class="word-open" data-action="bank-word" data-word="${esc(w.id)}">${esc(w.term)}</button><span class="word-meaning">${esc(w.meaning||'释义待补')}</span><span class="word-status">${w.lexicalFrequency?`${w.lexicalFrequency.articleCount} 篇 · ${w.lexicalFrequency.totalOccurrences} 次`:lookupEngine?'暂无完整例句':'正在检索原文…'}<br><span class="knowledge-tag ${e.label}">${e.label==='known'?'会，不需记忆':!e.meaning?'不会 · 释义待补':!e.ready?'不会 · 样本待补':e.pending?'不会 · 按词频分批安排':'不会 · 正常复习'}</span></span><button class="text-btn" data-action="bank-word" data-word="${esc(w.id)}">管理 →</button></div>`;}).join(''):'<p class="empty">这里还没有符合条件的词。<br>阅读时点一个词，选择“不会”或“会”。</p>'}</div><p class="sample-note">${lookupEngine?`检索范围：${lookupEngine.articles.size} 篇来源正文、${lookupEngine.indexedSentenceCount.toLocaleString()} 个完整原句。按完整词形统计全库出现次数，非官方考频。你标记不会的待学词按次数从高到低安排，从下一组开始生效；次数相同时优先覆盖更多文章的词。已学词正常复习。`:'选词后自动检索完整原文文件库。'}<br>${accountSession.status==='signed-in'?'标记随当前账号保存并同步。':'当前为试用，标记在刷新后不会保留；登录后可保存。'}</p></main>`);
}
function displayParagraph(id){return (String(id).startsWith('mem-')?activeParagraphs().find(p=>p.id===id):null)||corpus.paragraphs.get(id)||encounter?.results?.sentences.find(p=>p.id===id)||lookupEngine?.getParagraph(id)||null;}
function originFor(p,start,end){
 const offset=p.sentenceStart||0;
 return {paragraphId:p.parentParagraphId||p.id,articleId:p.articleId,start:offset+start,end:offset+end,text:p.text.slice(start,end),sourceLabel:p.sourceLabel||''};
}
async function pickToken(el){
 const p=displayParagraph(el?.dataset.pid);if(!p)return;
 const start=Number(el.dataset.start),end=Number(el.dataset.end),text=p.text.slice(start,end);
 if(!text||wordTokens(text).length!==1)return;
 await openEncounter(text,originFor(p,start,end));
}
async function openEncounter(form,origin,existingEntry=null){
 const owner=store.identity?.uid||null,ownerEpoch=identityEpoch,request=++encounterRequest;await saveAnchor();
 if(request!==encounterRequest||ownerEpoch!==identityEpoch)return;
 openDialog(`选词 · ${form}`,'<p class="info-block">正在从原文文件库检索句子…</p>');
 try{
  await ensureLookup();
  if(request!==encounterRequest||ownerEpoch!==identityEpoch||(store.identity?.uid||null)!==owner)return;
  const result=lookupEngine.lookup(form);
  if(result.error){openDialog('请选择一个英文单词','<p>支持单个词及带连字符的词。选中多个词时，请重新选择。</p>');return;}
  encounter={request,owner,ownerEpoch,form,origin,candidates:result.candidates,entry:existingEntry||result.entry,results:null};
  if(encounter.entry){const prior=state().wordBank?.[encounter.entry.id];if(prior)encounter.entry={...encounter.entry,...prior};}
  renderEncounter();
 }catch(error){if(request===encounterRequest)openDialog('原文检索暂不可用',`<p>${esc(error.message)}</p>`,button('关闭','close-dialog'));}
}
function chooseEncounter(index){
 if(!encounter||!encounter.candidates[index])return;
 const selected=encounter.candidates[index],prior=state().wordBank?.[selected.id];encounter.entry=prior?{...selected,...prior}:selected;renderEncounter();
}
function renderEncounter(){
 const e=encounter;if(!e)return;
 if(!e.entry){openDialog(`选词 · ${e.form}`,`<p class="subtle">这个词形可对应以下词条，选择你要记的词。</p><div class="lookup-candidates">${e.candidates.map((w,i)=>`<button data-action="lookup-candidate" data-index="${i}"><strong>${esc(w.term)}</strong><span>${esc(w.meaning||'释义待补')}</span></button>`).join('')}</div>`);return;}
 const w=e.entry,result=lookupEngine.search(w,{limit:12});e.results=result;
 const previous=state().wordBank?.[w.id],label=previous?.label||(state().progress[w.id]?.status==='familiar'?'known':'');
 const sourceName=w.dictionarySource==='target303'?'原词表释义':w.dictionarySource==='local-dictionary'?'本地词典释义':w.dictionarySource==='user'?'你填写的词义':'暂未查到词典释义';
 openDialog(w.term,`<div class="lookup-topline"><span class="knowledge-tag ${label}">${label==='known'?'会，不需记忆':label==='unknown'?'不会，需记忆':'尚未标记'}</span><span class="subtle">选中的词形：${esc(e.form)}</span></div><label class="field-label" for="bank-meaning">${sourceName}${w.baseWordId?'':' · 可补充自己的记忆提示'}</label><textarea id="bank-meaning" class="bank-meaning input" rows="3" maxlength="8000" ${w.baseWordId?'readonly':''} placeholder="词义暂缺，可填中文词义或自己的记忆提示">${esc(w.meaning)}</textarea>${englishMeaning(w)}${previous?.origins.filter(o=>o.context).map(o=>`<article class="lookup-sentence"><small>${esc(o.sourceLabel||'阅读与写作标记')}</small><p lang="en">${esc(o.context)}</p></article>`).join('')||''}<div class="lookup-stats"><strong>${result.sentenceCount} 个不同原句</strong><span>来自 ${result.articleCount} 篇文章</span><small>完整检索库 ${lookupEngine.articles.size} 篇 · 当前显示 ${result.sentences.length} 句</small></div>${result.insufficient?`<p class="sample-shortage">${result.sentenceCount?'目前样本较少，已展示全部检索结果。':'暂未找到完整句子，可先收录为待补。'}</p>`:''}${!w.meaning?'<p class="sample-shortage">可以先收录；补充词义后再混入下一组学习。</p>':''}<p class="subtle">原文自动检索，优先不同文章；释义是词典释义，不是每句的逐句翻译。</p><div class="lookup-sentences">${result.sentences.map((p,i)=>`<article class="lookup-sentence" data-sentence-id="${esc(p.id)}" data-article-id="${esc(p.articleId)}"><div class="lookup-sentence-no">${String(i+1).padStart(2,'0')} · ${esc(p.topics.join(' / ')||'原文资料')}</div><p lang="en">${highlight(p)}</p><button class="source-button" data-action="source" data-pid="${esc(p.id)}">${esc(p.sourceLabel)} · ${esc(p.source.title)} ↗</button></article>`).join('')}</div>`,button('会，不需记忆','mark-known',label==='known'?'soft':'')+button('不会，加入学习','mark-unknown','primary'));
}
async function saveEncounter(label){
 const e=encounter;if(!e?.entry)return;
 if(identityEpoch!==e.ownerEpoch||(store.identity?.uid||null)!==e.owner)throw new Error('账号已切换，请在当前账号重新选择这个词。');
 const meaningInput=document.querySelector('#bank-meaning'),text=(meaningInput?.value??e.entry.meaning).trim();
 const entry={...e.entry,meaning:text,unresolved:!text,ready:!!text&&(e.results.sentenceCount>0||state().wordBank?.[e.entry.id]?.origins.some(o=>o.context))};
 if(!entry.baseWordId&&text!==e.entry.meaning)entry.dictionarySource='user';
 let origin=e.origin;
 if(!origin){const first=e.results.sentences[0],hit=first?.highlight[0];origin=first&&hit?originFor(first,hit.start,hit.end):{paragraphId:'manual-lookup',start:0,end:e.form.length,text:e.form,sourceLabel:'手动输入'};}
 await store.update(s=>act(s,{type:label==='known'?'MARK_KNOWN':'MARK_UNKNOWN',entry,origin},words));
 if(identityEpoch!==e.ownerEpoch)return;
 const saved=state().wordBank?.[entry.id];if(!saved||saved.label!==label)throw new Error('本次标记未保存，请重新选择这个词。');
 const active=view().wordId;closeDialog();syncBank();
 if(label==='known'&&active===entry.id)await update({type:'SKIP_KNOWN',wordId:entry.id,sessionId:state().session?.id});else render();
 toast(label==='known'?'已标记为会，后续不再安排记忆':entry.ready?'已加入生词库，按出现频率分批安排':text?'已收录，完整原句待补':'已收录，补充词义后加入学习');
}
async function bankDetail(id){
 const e=state().wordBank?.[id];if(!e)return;
 await openEncounter(e.term,e.origins[0],e);
}
function openLookupInput(){
 encounter=null;encounterRequest++;
 openDialog('检索一个词','<label class="field-label" for="lookup-input">英文单词</label><input id="lookup-input" class="input" autocomplete="off" spellcheck="false" placeholder="输入单词，在完整原文库里检索"><p class="subtle">也可以在语料中直接点词或拖动选词。</p>',button('检索原文','lookup-submit','primary'));
 document.querySelector('#lookup-input')?.focus();
}
async function lookupInput(){const value=document.querySelector('#lookup-input')?.value?.trim();if(!value)return;await openEncounter(value,null);}

function speak(text){if(!('speechSynthesis'in window)){toast('当前浏览器暂不支持朗读');return;}speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.lang=state().settings.voice;utterance.rate=.88;const voice=speechSynthesis.getVoices().find(v=>v.lang===utterance.lang);if(voice)utterance.voice=voice;utterance.onerror=()=>toast('语音暂不可用，请检查浏览器语音设置');speechSynthesis.speak(utterance);}
function speakCurrent(wordOnly){const w=wordById(modalWordId)||view().word;if(w)speak(wordOnly?w.term:(activeParagraphs()[0]?.text||w.passages[0]?.text||w.term));}
function sourceDialog(id){const input=document.querySelector('#bank-meaning');if(encounter?.entry&&input&&!encounter.entry.baseWordId&&input.value.trim()!==encounter.entry.meaning){encounter.entry={...encounter.entry,meaning:input.value.trim(),dictionarySource:'user'};}let p=displayParagraph(id)||activeParagraphs()[0];if(!p)return;if(p.parentParagraphId){const raw=lookupEngine?.getParagraph(p.parentParagraphId);if(raw)p={...p,...raw,source:p.source,id:raw.id,matches:[]};}const s=p.source;openDialog('查看上下文',`<h3>${esc(s.title)}</h3><p class="subtle">${esc(p.topics?.join(' / ')||'')}</p><p class="source-text" data-pid="${esc(p.id)}">${paragraphMarkup(p,view().wordId,state().session?.queue||[])}</p><div class="source-meta"><span>来源</span><span>${esc(p.sourceLabel)}</span><span>段落</span><span>${esc(s.paragraph)}</span><span>类型</span><span>${s.sourceQuality==='cambridge_original_book_local_transcription'?'剑雅原书阅读正文':s.section==='listening'||String(s.sourceQuality).includes('listening')?'剑雅原书听力对话':'补充雅思阅读资料正文'}</span>${p.isSentence||p.parentParagraphId?'<span>检索</span><span>从原文提取的句子；词形自动匹配，释义来自词典。</span>':''}<span>核对</span><span>${s.originalPageCheck==='visually_checked_this_batch'?'本段已对照原书扫描页核对。':'原文文本与来源文件对应；本批未对每段重新看原书扫描页。'}</span></div>`,encounter?button('返回选词','lookup-back','primary'):'');}
async function detail(id){
 const w=wordById(id);if(!w)return;modalWordId=id;if(w.bankEntry&&!baseIds.has(id)){await bankDetail(id);return;}const list=corpus.forWord(id,'',12);
 openDialog(w.term,`<p>${esc(w.pos)} ${esc(w.meaning)}</p>${englishMeaning(w)}<p class="subtle">${w.semanticFrequency?.acceptedArticleCount||0} / 132 篇剑雅阅读正文 · ${w.passages?.length||0} 段可用语料${w.passages?.length>12?' · 展示其中 12 段':''}</p>${state().notes[id]?`<p class="reader-note">${esc(state().notes[id])}</p>`:''}${list.length?list.map(p=>`<p class="source-text">${highlight(p)}</p>${p.translation?`<p>${esc(p.translation)}</p>`:''}<p class="subtle">${esc(p.topics.join(' / '))}</p><button class="source-button" data-action="source" data-pid="${esc(p.id)}">${esc(p.sourceLabel)} · ${esc(p.source.title)} ↗</button>`).join(''):'<p class="empty">正文语料待补。原词和释义已保留，可先练习拼写。</p>'}`,button('写笔记','note','',`data-word="${esc(id)}"`)+button(state().progress[id]?.status==='familiar'?'取消标熟':'标为熟词','familiar','',`data-word="${esc(id)}"`)+(list.length?button('练习这个词','practice-word','primary',`data-word="${esc(id)}"`):button('练习拼写','spelling-word','primary',`data-word="${esc(id)}"`)));
}
function note(id){const w=wordById(id);modalWordId=id;openDialog(`笔记 · ${w.term}`,`<label class="sr-only" for="note-text">单词笔记</label><textarea id="note-text" class="note-input" maxlength="8000" placeholder="记下自己的理解、联想或搭配…">${esc(state().notes[id]||'')}</textarea>`,button('取消','close-dialog')+button('保存笔记','save-note','primary',`data-word="${esc(id)}"`));document.querySelector('#note-text').focus();}
function about(){openDialog('语境 · 303词',`<p>完整词表是你在 10 月 2 日上传到不背单词的<strong>阅读538精筛303词</strong>，保留原词和释义。选话题后按文章语料相关性安排单词；全部话题按原词表顺序。每日默认 25 个需记忆的新词，熟词跳过并自动补位。</p><p>语料直接检索自文章正文，按文章话题筛选，短原句切换记忆，完整段落可点查看上下文；同一段可供多个目标词共用。新学、回忆词义、复习与拼写仍按单词推进，没有额外理解关卡。</p><p>原书正文与补充资料分别标来源。没有检索结果的词保留在词本，暂不进入语料新学；未编写假原文补数。</p><p>沿用网站同一个账号，语境进度独立保存并自动同步。原有账号本机记录保留；未登录试学不保存。原主站入口和原版逐页一比一核验仍待完成。</p>`);}

function download(filename,content,type='application/json'){const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([content],{type}));link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);}
function exportRecords(){download(`语境记录-${new Date().toISOString().slice(0,10)}.json`,store.exportRaw()||JSON.stringify({state:state()},null,2));toast('记录已导出');}
function printWords(){const list=filteredWords();document.querySelector('.print-only')?.remove();const area=document.createElement('section');area.className='print-only';area.innerHTML=`<h1>${esc(collection.title)} · ${list.length} 词</h1>${list.map(w=>`<article><h2>${esc(w.term)}</h2><p>${esc(w.pos)} ${esc(w.meaning)}</p>${englishMeaning(w)}${w.passages.map(p=>`<p>${esc(p.text)}</p><small>${esc(p.sourceLabel)}</small>`).join('')}${state().notes[w.id]?`<p>笔记：${esc(state().notes[w.id])}</p>`:''}</article>`).join('')}`;document.body.append(area);window.print();}
function accountDialog(){const s=account.getSession();if(['checking','unavailable'].includes(s.status)){openDialog('恢复设备登录',`<p>正在恢复此设备的登录状态，连接恢复后会自动接续账号进度。</p><p class="subtle">${s.status==='unavailable'?'暂时未连上账号服务，正在自动重试。':''}</p>`,button('重试连接','refresh-account'));return;}if(s.status==='signed-in'){openDialog('我的账号',`<p>已登录：${esc(s.user.phone||s.user.displayName||'网站账号')}</p><p class="subtle">与网站共用账号身份。语境记录独立保存并同步到同一账号。${esc(syncLabel())}。</p>`,button('导出记录','export')+button('退出账号','logout'));return;}openDialog('登录网站账号',`<p class="subtle">使用网站的同一个手机号。在新地址登录后自动恢复该账号的语境记录。</p><label class="field-label" for="phone">手机号</label><input id="phone" class="input" type="tel" autocomplete="tel" placeholder="请输入手机号"><p id="auth-message" class="subtle">${s.status==='unavailable'?esc(s.error||'登录服务暂不可用'):''}</p>`,button('发送验证码','send-code','primary'));}
let skipConfirmation=null,skipConfirmTimer;
function clearSkipConfirmation(){clearTimeout(skipConfirmTimer);skipConfirmation=null;}
function confirmFamiliarSkip(){
 const s=state().session;
 if(!s||s.paused||s.mode==='dictation'||s.phase!=='memory'||view().isBrowsing){clearSkipConfirmation();return false;}
 const key=`${identityEpoch}:${s.id}:${view().promptToken}:${view().wordId}`;
 if(skipConfirmation?.key===key&&Date.now()<skipConfirmation.until){clearSkipConfirmation();return true;}
 clearSkipConfirmation();skipConfirmation={key,until:Date.now()+3000};
 skipConfirmTimer=setTimeout(clearSkipConfirmation,3000);
 toast('再点一次「会」才会跳过并标为熟词（3 秒内）。');return false;
}
async function handle(action,el){const actionEpoch=identityEpoch;if(action==='dismiss-current'){if(!confirmFamiliarSkip())return;}else clearSkipConfirmation();const id=el?.dataset.word||modalWordId||view().wordId;if(await handleListening(action,el))return;switch(action){
 case'home':closeDialog();goto('home');break;case'bank':closeDialog();goto('bank');break;case'book':closeDialog();goto('book');break;case'frequency-info':frequencyInfo();break;case'settings':goto('settings');break;case'about':about();break;case'close-dialog':closeDialog();break;
 case'start-learn':await begin('learn');break;
 case'bank-import':await applyBankSeed();break;
 case'lookup-back':renderEncounter();break;case'lookup-word':await pickToken(el);break;case'lookup-input':openLookupInput();break;case'lookup-submit':await lookupInput();break;case'lookup-candidate':chooseEncounter(Number(el.dataset.index));break;case'mark-unknown':await saveEncounter('unknown');break;case'mark-known':await saveEncounter('known');break;case'bank-word':await bankDetail(id);break;case'bank-filter':bankFilter=el.dataset.filter;render();break;case'bank-learn':await begin('learn',bankList('unknown'));break;case'bank-practice':await begin('practice',bankList('unknown').filter(w=>w.bankEntry?.ready));break;case'start-review':await begin('review');break;
 case'replace-session':{const scope=selectedScope;if(!scope)break;closeDialog();await update({type:'CLOSE_SESSION'});if(actionEpoch!==identityEpoch)break;await begin(scope.mode,scope.words,scope.listeningKind);if(actionEpoch===identityEpoch)selectedScope=null;break;}
 case'leave':await saveAnchor();if(actionEpoch!==identityEpoch)break;await update({type:'PAUSE'});if(actionEpoch!==identityEpoch)break;stopListeningAudio();goto(state().session?.mode==='dictation'?'listening':'home');break;
 case'pause':await saveAnchor();if(actionEpoch!==identityEpoch)break;await update({type:'PAUSE'});if(actionEpoch===identityEpoch)stopListeningAudio();break;
 case'resume':closeDialog();await update({type:'RESUME'});if(actionEpoch!==identityEpoch)break;goto('learn');restoreAnchor();if(state().session?.mode==='dictation'&&state().session?.phase==='spelling'&&!state().session?.spellingRevealed)void playListening();break;
 case'reveal':await update({type:'REVEAL'});break;
 case'dismiss-current':await update({type:'DISMISS_CURRENT',wordId:id,promptToken:el?.dataset.prompt||view().promptToken,sessionId:el?.dataset.session||state().session?.id});if(actionEpoch===identityEpoch&&state().progress[id]?.status==='familiar')toast('已标为会，跳过这个词，以后不再安排学习和复习');break;
 case'sentence-meaning':await toggleTranslation();break;
 case'grade-known':case'grade-forgot':if(state().session?.pendingGrade===(action==='grade-known'?'known':'forgot')&&(!el?.dataset.prompt||el.dataset.prompt===view().promptToken)){await toggleTranslation();break;}await update({type:!view().revealed||state().session?.pendingGrade?'MEMORY_CHOICE':'GRADE',grade:action==='grade-known'?'known':'forgot',wordId:id,promptToken:el?.dataset.prompt||view().promptToken,sessionId:el?.dataset.session||state().session?.id});break;
 case'grade-continue':if(state().session?.pendingGrade)await update({type:'GRADE',grade:state().session.pendingGrade,wordId:id,promptToken:el?.dataset.prompt||view().promptToken,sessionId:el?.dataset.session||state().session?.id});break;
 case'passage':await update({type:'PASSAGE',index:Number(el.dataset.index)});break;
 case'passage-prev':case'passage-next':{const list=activeParagraphs(),index=passagePage(list),next=index+(action==='passage-next'?1:-1);if(next>=0&&next<list.length)await update({type:'PASSAGE',index:next,wordId:id,sessionId:state().session?.id});break;}
 case'previous':await update({type:'PREVIOUS'});break;case'return-current':await update({type:'RETURN_CURRENT'});break;
 case'correct':await update({type:'CORRECT_LAST'});toast('已回到上一词，请重新选择');break;
 case'favorite':await update({type:'FAVORITE',wordId:id});toast(state().favorites.includes(id)?'已收藏':'已取消收藏');break;
 case'note':note(id);break;case'save-note':await update({type:'NOTE',wordId:id,text:document.querySelector('#note-text').value});closeDialog();toast('笔记已记录');break;
 case'familiar':await update({type:'FAMILIAR',wordId:id,value:state().progress[id]?.status!=='familiar'});if(dialog.open)await detail(id);else toast(state().progress[id]?.status==='familiar'?'已标为熟词':'已恢复到原学习状态');break;
 case'source':sourceDialog(el?.dataset.pid);break;case'speak-word':speakCurrent(true);break;case'speak-passage':el?.dataset.pid?speak(displayParagraph(el.dataset.pid)?.text||''):speakCurrent(false);break;
 case'spell-hint':await update({type:'SPELL_HINT'});break;
 case'mixed-answer':await update({type:'MIXED_ANSWER',questionId:el.dataset.question,answer:el.dataset.answer,wordId:id});break;
 case'mixed-forgot':await update({type:'MIXED_ANSWER',questionId:el.dataset.question,answer:null,wordId:id});break;
 case'mixed-reveal':await update({type:'MIXED_REVEAL',wordId:id});break;
 case'mixed-spell-skip':await update({type:'MIXED_REVEAL',wordId:id});if(actionEpoch===identityEpoch)await update({type:'MIXED_ANSWER',questionId:el.dataset.question,wordId:id});break;
 case'mixed-submit':{const input=document.querySelector('#mixed-input');if(!input?.value.trim()){toast('输入拼写后检查，或查看答案再练一次。');break;}await update({type:'MIXED_INPUT',value:input.value},true);if(actionEpoch===identityEpoch)await update({type:'MIXED_ANSWER',questionId:el.dataset.question,wordId:id});break;}
 case'mixed-next':await update({type:'MIXED_NEXT',questionId:el.dataset.question,wordId:id});break;
 case'spell-submit':{const input=document.querySelector('#spelling-input');if(state().session?.phase==='spelling'&&!state().session.spellingRevealed&&!(input?.value??state().session.spellingInput).trim()){const message='先输入你听到的词；不会拼可以点「不会拼，查看答案」。';const hint=document.querySelector('#listen-input-feedback');if(hint){hint.textContent=message;input?.setAttribute('aria-invalid','true');}else toast('先输入拼写；也可以点击「不会拼」。');input?.focus();break;}if(input)await update({type:'SPELL_INPUT',value:input.value},true);if(actionEpoch!==identityEpoch)break;await update({type:'SPELL_SUBMIT',wordId:id});break;}case'spell-skip':await update({type:'SPELL_SKIP',wordId:id});break;
 case'spell-next':stopListeningAudio();await update({type:'SPELL_NEXT',wordId:id});if(state().session?.mode==='dictation'&&state().session?.phase==='spelling')void playListening();break;case'retry-wrong':await update({type:'RETRY_WRONG'});break;case'continue':await update({type:'CONTINUE'});break;
 case'filter':filter=el.dataset.filter;render();break;
 case'spelling-word':closeDialog();await begin('spelling',[wordById(id)]);break;
 case'word-detail':await detail(id);break;case'practice-word':closeDialog();await begin('practice',[wordById(id)]);break;
 case'practice-filter':await begin('practice',filteredWords());break;case'spelling-filter':await begin('spelling',filteredWords());break;
 case'practice-session':{const mode=state().session.mode==='spelling'?'spelling':'practice',list=state().session.queue.map(wordById);await begin(mode,list);break;}
 case'session-more':openDialog('本轮学习','<p>暂停可以保留当前位置。提前结束会保留已经学过的词。</p>',button('我的生词','bank')+button('学习设置','session-settings')+button('提前结束','end-session','danger'));break;
 case'session-settings':closeDialog();await saveAnchor();if(actionEpoch!==identityEpoch)break;await update({type:'PAUSE'});if(actionEpoch===identityEpoch)goto('settings');break;
 case'end-session':{const back=state().session?.mode==='dictation'?'listening':'home';stopListeningAudio();closeDialog();await update({type:'CLOSE_SESSION'});goto(back);break;}
 case'history-detail':{const r=recordRuns().find(e=>e.id===el.dataset.id);if(!r)break;openDialog(names[r.mode],`<p class="subtle">${new Date(r.at).toLocaleString('zh-CN')} · ${recordStatus(r)}</p>${recordWordIds(r).map(wid=>`<p><strong>${esc(wordById(wid)?.term||wid)}</strong>　${esc(wordById(wid)?.meaning||'')}</p>`).join('')}`);break;}
 case'sync':if(store.syncStatus?.phase==='conflict'){syncDialog();break;}await store.sync();if(store.syncStatus?.phase==='conflict')syncDialog();else toast(syncLabel());break;case'sync-local':case'sync-cloud':{const expectedRevision=store.syncStatus?.revision;closeDialog();await store.sync({choice:action==='sync-local'?'local':'cloud',expectedRevision});if(store.syncStatus?.phase==='conflict')syncDialog();else toast(syncLabel());break;}case'export':exportRecords();break;case'print':printWords();break;case'account':accountDialog();break;
 case'send-code':{const msg=document.querySelector('#auth-message');el.disabled=true;try{const r=await account.sendCode(document.querySelector('#phone').value);openDialog('输入验证码',`<p class="subtle">验证码已发送至 ${esc(r.maskedPhone||r.phone)}</p><label class="field-label" for="code">短信验证码</label><input id="code" class="input" inputmode="numeric" autocomplete="one-time-code" placeholder="请输入验证码"><p id="auth-message" class="subtle"></p>`,button('返回','account')+button('登录','verify-code','primary'));}catch(e){msg.textContent=e.message;el.disabled=false;}break;}
 case'verify-code':el.disabled=true;try{await account.verifyCode(document.querySelector('#code').value);closeDialog();goto('home');toast('已登录，已切换到此账号的独立进度');}catch(e){document.querySelector('#auth-message').textContent=e.message;el.disabled=false;}break;
 case'refresh-account':await account.refresh();accountDialog();break;
 case'logout':await account.logout();closeDialog();goto('home');toast('已退出，账号进度保留');break;
}}
document.addEventListener('click',event=>{const el=event.target.closest('[data-action]');if(el?.dataset.action==='lookup-word'&&window.getSelection()?.toString().trim())return;if(el&&!el.disabled)handle(el.dataset.action,el).catch(e=>toast(e.message));});
document.addEventListener('input',event=>{if(event.target.id==='mixed-input')update({type:'MIXED_INPUT',value:event.target.value},true);});
document.addEventListener('keydown',event=>{if(event.target.id==='mixed-input'&&event.key==='Enter'){event.preventDefault();const el=document.querySelector('[data-action="mixed-submit"],[data-action="mixed-next"]');if(el)handle(el.dataset.action,el).catch(e=>toast(e.message));}});
document.addEventListener('pointerup',event=>{
 if(dialog.open||event.button!==0)return;
 const selection=window.getSelection();if(!selection||selection.isCollapsed||!selection.rangeCount)return;
 const range=selection.getRangeAt(0),node=range.commonAncestorContainer;
 const element=node.nodeType===Node.ELEMENT_NODE?node:node.parentElement,p=element?.closest('.passage[data-pid]');
 if(!p||!p.contains(range.startContainer)||!p.contains(range.endContainer))return;
 const raw=range.toString(),trimmed=raw.trim();if(!trimmed||wordTokens(trimmed).length!==1||normalizeLookupTerm(wordTokens(trimmed)[0].text)!==normalizeLookupTerm(trimmed))return;
 const prefix=document.createRange();prefix.selectNodeContents(p);prefix.setEnd(range.startContainer,range.startOffset);
 const start=prefix.toString().length+(raw.length-raw.trimStart().length),end=start+trimmed.length,paragraph=displayParagraph(p.dataset.pid);
 if(!paragraph||paragraph.text.slice(start,end)!==trimmed)return;
 // Let the drag's click finish before clearing selection; it must not open twice.
 setTimeout(()=>{selection.removeAllRanges();openEncounter(trimmed,originFor(paragraph,start,end)).catch(e=>toast(e.message));},0);
});
document.addEventListener('input',event=>{if(event.target.matches('.bank-search')){bankSearch=event.target.value;const start=event.target.selectionStart;render();const input=document.querySelector('.bank-search');input.focus();input.setSelectionRange?.(start,start);}if(event.target.matches('.search')){search=event.target.value;const start=event.target.selectionStart;render();const input=document.querySelector('.search');input.focus();input.setSelectionRange?.(start,start);}if(event.target.id==='spelling-input'){clearSkipConfirmation();event.target.removeAttribute('aria-invalid');const hint=document.querySelector('#listen-input-feedback');if(hint)hint.textContent='';update({type:'SPELL_INPUT',value:event.target.value},true);}});
document.addEventListener('change',event=>{if(event.target.dataset.listenChoice){const id=event.target.dataset.listenChoice,checked=event.target.checked;store.update(s=>listeningSelection(s,listeningWords,{type:'toggle',id,checked})).then(()=>render()).catch(e=>toast(e.message));return;}if(event.target.matches('[data-lookup-choice]')){chooseEncounter(Number(event.target.value));return;}if(event.target.matches('[data-topic]')){update({type:'SETTINGS',patch:{studyTopic:event.target.value}});return;}if(event.target.matches('[data-sort]')){wordSort=event.target.value;render();return;}const key=event.target.dataset.setting;if(key)update({type:'SETTINGS',patch:{[key]:event.target.type==='checkbox'?event.target.checked:['newPerDay','groupSize'].includes(key)?Number(event.target.value):event.target.value}});});
document.addEventListener('keydown',event=>{if(event.target.id==='lookup-input'&&event.key==='Enter'){event.preventDefault();lookupInput();return;}if(dialog.open||route!=='learn'||!state().session||state().session.paused)return;const s=state().session;if(event.target.id==='spelling-input'){if(event.key==='Enter'&&!event.repeat){event.preventDefault();handle(s.spellingRevealed?'spell-next':'spell-submit',null).catch(e=>toast(e.message));}return;}if(['INPUT','TEXTAREA','SELECT','BUTTON'].includes(event.target.tagName))return;if(s.mode==='dictation')return;if(s.phase==='memory'){if(event.key==='Enter'&&s.pendingGrade){event.preventDefault();handle('grade-continue');}else if(event.code==='Space'&&!view().revealed){event.preventDefault();handle('reveal');}else if(!view().isBrowsing&&['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();handle(event.key==='ArrowRight'?'grade-known':'grade-forgot');}}});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveAnchor();else if(route==='home')render();});
setInterval(()=>{if(store && route==='home' && document.visibilityState==='visible' && ensureDailyPlan(state(),Date.now(),words.map(w=>w.id))!==state())render();},30000);
addEventListener('hashchange',()=>{
 const previousRoute=route,next=location.hash.slice(1).split('?')[0]||'home';if(next!==route)stopListeningAudio();route=next;
 const raw=new URLSearchParams(location.hash.split('?')[1]||'').get('words');
 if(raw&&(!bankSeed||encodeSeed(bankSeed)!==raw)){
  try{bankSeed=decodeBankSeed(raw);bankSeedCount=0;bankSeedError='';}catch{bankSeedError='勾选链接不完整，请重新打开保存的入口。';}
 }
 if(listeningSeed||bankSeed)history.replaceState(null,'','#'+route+seedFragment());
 render();if(bankSeed)void applyBankSeed();if(next!==previousRoute)window.scrollTo(0,0);
});
dialog.addEventListener('click',event=>{if(event.target===dialog){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)closeDialog();}});
initializeAppearance();
initializeMotion();
bridge=installHostBridge({getOwner:()=>accountSession.status==='signed-in'?accountSession.user.owner:null,
 async importSeed(seed,owner,markUnknown){
  await ensureLookup();
  const rows=lookupEngine.prepareBankImport(seed);
  await store.update(s=>{
   if(accountSession.status!=='signed-in' || accountSession.user.owner!==owner)throw Error('账号已切换，请重新同步收词。');
   return markUnknown?importMarkedBank(s,rows,words):importWordBank(s,rows,words);
  });
  syncBank();render();return rows.length;
 }});

try{
 const response=await fetch(config.collectionPath);if(!response.ok)throw new Error('词本加载失败');const data=await response.json();baseData=data;collection=data.collection;corpus=createCorpus(data);baseIds=new Set(data.words.map(w=>w.id));words=corpus.words;baseWords=words;try{legacyWords=(await (await fetch(new URL('../data/legacy-sample-18.json',import.meta.url))).json()).words;}catch{}
 try{const response=await fetch(new URL('../data/listening-words.json',import.meta.url));if(!response.ok)throw Error();listeningWords=(await response.json()).words;}catch{listeningLoadError='听力词表暂未加载，请刷新重试。';}
 if(listeningWords.length)try{const response=await fetch(new URL('../data/listening-audio/manifest.json',import.meta.url),{cache:'no-cache'});if(!response.ok)throw Error('听力音源信息暂未加载，请刷新重试。');listeningWords=withListeningAudio(listeningWords,await response.json());}catch(error){listeningLoadError=error.message;}
 await loadEnglishDictionary();
 let renderedState=null;
 store=createStore(allStudyWords(),(next,error)=>{if(error)toast(error.message);if(next!==renderedState){renderedState=next;render();}else{const label=document.querySelector('.sync-status');if(label)label.textContent=syncLabel();}},uid=>account.assertIdentity(uid),globalThis,(uid,action,operation)=>account.wordCloud(uid,action,operation),{canUseGuest:()=>accountSession.status==='guest',canRestore:()=>!dialog.open&&!['spelling-input','mixed-input'].includes(document.activeElement?.id)});
 account=createAccount();account.subscribe(snapshot=>{accountSession=snapshot;bridge?.ready();if(['signed-in','guest'].includes(snapshot.status)){const newUid=snapshot.status==='signed-in'?snapshot.user.uid:null;if((store.identity?.uid||null)!==newUid){identityEpoch++;bankSeedCount=0;stopListeningAudio();identityRenderPending=true;closeDialog();selectedScope=null;bankSearch='';store.setIdentity(newUid?{verified:true,uid:newUid}:null);}if(newUid){store.sync();if(listeningSeed)queueMicrotask(()=>applyListeningSeed().catch(e=>toast(e.message)));}if(bankSeed)queueMicrotask(()=>applyBankSeed());}if(store.identity&&['checking','unavailable','signed-in'].includes(snapshot.status)){const entry=document.querySelector('.account');if(entry)entry.textContent=accountLabel();}else render();if(dialog.open&&document.querySelector('#dialog-title')?.textContent==='恢复设备登录'&&snapshot.status==='signed-in')accountDialog();});
 render();await account.ready;if(bankSeed)await applyBankSeed();if(listeningSeed&&accountSession.status==='signed-in')await applyListeningSeed();if(Object.keys(state().wordBank||{}).length)ensureLookup().then(()=>render()).catch(e=>toast(e.message));
}catch(error){app.innerHTML=`<div class="loading"><h1>暂时无法打开词本</h1><p>${esc(error.message)}</p><p>请通过本地启动器打开，或刷新重试。</p></div>`;}
