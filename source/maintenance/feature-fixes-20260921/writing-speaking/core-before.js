(()=>{'use strict';
/* RECORD-SAFETY-20260919 */
const key='ielts-finished-book-v1';let state={version:1,fields:{},snapshots:{}},storageOK=true,recoveryRaw=null,loadBlocked=false,recordSaveIssue='';
const recordObject=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const recordFields=x=>recordObject(x)&&Object.values(x).every(v=>typeof v==='string'||typeof v==='boolean'||(typeof v==='number'&&Number.isFinite(v)));
function validateRecord(x){
 if(!recordObject(x)||x.version!==1||!recordFields(x.fields)||!recordObject(x.snapshots))throw Error('学习记录结构不完整');
 const chapters=['reading','writing1','writing2','listening','speaking'];
 for(const [id,snapshot] of Object.entries(x.snapshots))if(!chapters.includes(id)||!recordObject(snapshot)||typeof snapshot.at!=='string'||!recordFields(snapshot.fields))throw Error('首次作答记录格式不符');
 return x;
}
function recordWarning(){return loadBlocked?'已有记录无法读取，已暂停自动保存。请导出文字保留本次输入，并备份原始记录后恢复有效备份。':recordSaveIssue||'当前未能保存，请导出文字或备份学习记录后再刷新。';}
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
try{const raw=localStorage.getItem(key);if(raw!==null){recoveryRaw=raw;state=validateRecord(JSON.parse(raw));recoveryRaw=null}}catch(e){storageOK=false;loadBlocked=true}
let toastTimeout;function notice(s){$('#toast').textContent=s;$('#toast').hidden=false;clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>$('#toast').hidden=true,3500)}
const recordConcurrency=window.IELTSRecordConcurrency.create({initial:state,read:()=>localStorage.getItem(key),write:raw=>localStorage.setItem(key,raw),validate:validateRecord});
function concurrencyWarning(reason){return reason==='conflict'?'另一页面修改了同一项，本页新输入未能保存。请先导出文字或备份本页草稿，再刷新核对；其他页面的记录未被覆盖。':reason==='changed-again'?'另一页面刚更新了记录，本次未能保存且没有覆盖它。请先导出本页草稿，再重试或刷新核对。':reason==='external-invalid'?'其他页面的记录已变更且无法读取，本页没有覆盖它。请先导出本页草稿，再检查学习记录备份。':'当前未能保存，请导出文字或备份学习记录后再刷新。';}
function save(changes,retainOnFailure=true){
 if(loadBlocked){$('#save-status').textContent=recordWarning();return false}
 const result=recordConcurrency.save(state,changes,retainOnFailure);
 if(!result.ok){storageOK=false;recordSaveIssue=concurrencyWarning(result.reason);$('#save-status').textContent=recordWarning();return false}
 state=result.state;storageOK=true;recordSaveIssue='';$('#save-status').textContent=result.remoteUpdates?'本次文字已保存；另一页面的更新已保留，刷新可载入。':'文字已保存在当前浏览器';return true;
}

window.IELTSRecordStore={commit(values){
 if(loadBlocked)return false;
 const controls=Object.entries(values).map(([k,v])=>[$(`[data-save="${k}"]`),v]);
 if(controls.some(([n,v])=>!n||!['string','boolean'].includes(typeof v)))return false;
 const previous=state;
 state={...state,fields:{...state.fields,...values}};
 if(!save({fields:Object.keys(values)},false)){state=previous;return false}
 controls.forEach(([n,v])=>{if(n.type==='checkbox')n.checked=v;else n.value=v});
 document.dispatchEvent(new Event('ielts-record-committed'));return true;
}};

// Cached static controls; synchronous record saving below is unchanged.
const wordCountIndex=new Map(),scoreIndex=new Map();
for(const output of $$('[data-wordcount]')){const k=output.dataset.wordcount;if(!wordCountIndex.has(k))wordCountIndex.set(k,[]);wordCountIndex.get(k).push({output,field:$(`[data-save="${k}"]`)});}
for(const control of $$('[data-score]')){const id=control.dataset.score;if(!scoreIndex.has(id))scoreIndex.set(id,{controls:[],output:$('#'+id+'-score'),total:control.dataset.total});scoreIndex.get(id).controls.push(control);}
function wordCounts(key){const groups=key===undefined?wordCountIndex.values():[wordCountIndex.get(key)||[]];for(const rows of groups)for(const {output,field} of rows)output.textContent=((field.value.trim().match(/\S+/g)||[]).length)+' 词（空白分隔计数）';}
function scores(id){const groups=id===undefined?scoreIndex.values():[scoreIndex.get(id)];for(const group of groups)if(group)group.output.textContent=group.controls.filter(n=>n.checked).length+' / '+group.total;}
function unlock(id){$$('#'+id+' .gated').forEach(el=>el.hidden=false);$$(`#${id} .first-stage [data-save]`).forEach(el=>{if(el.tagName==='SELECT')el.disabled=true;else el.readOnly=true});const b=$(`[data-freeze="${id}"]`);b.textContent='首次作答已保留';b.disabled=true;$(`[data-snapshot-status="${id}"]`).textContent='原稿已独立保存。请在下方练习区修订，重要答案及时导出。'}
function restore(){for(const el of $$('[data-save]')){const v=state.fields[el.dataset.save];if(v!==undefined){if(el.type==='checkbox')el.checked=!!v;else el.value=String(v)}}for(const id of Object.keys(state.snapshots)){if($('#'+id))unlock(id)}wordCounts();scores()}
restore();if(!storageOK)$('#save-status').textContent=recordWarning();
document.addEventListener('input',e=>{const el=e.target;if(el.dataset.save){state.fields[el.dataset.save]=el.type==='checkbox'?el.checked:el.value;save({fields:[el.dataset.save]});wordCounts(el.dataset.save);if(el.dataset.score)scores(el.dataset.score)}});
function show(id,anchor){if(!$('#'+id)?.classList.contains('panel'))id='guide';$$('main>.panel').forEach(el=>el.hidden=el.id!==id);$$('[data-go]').forEach(el=>{if(el.dataset.go===id)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current')});$$('audio').forEach(a=>a.pause());if(anchor){const target=$('#'+anchor);if(target){let p=target;while(p){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement}target.scrollIntoView({behavior:'smooth',block:'start'})}}else window.scrollTo(0,0)}
function route(){const h=decodeURIComponent(location.hash.slice(1))||'study';let id=document.getElementById(h)?.closest('main>.panel')?.id||h;show(id,h!==id?h:null)}
window.addEventListener('hashchange',route);route();
window.prepareBackgroundPrint=()=>{document.body.classList.add('print-background');$$('details').forEach(d=>d.open=true);$$('main>.panel').forEach(p=>p.hidden=false);$$('img').forEach(p=>p.loading='eager')};
document.addEventListener('click',e=>{const go=e.target.closest('[data-go]');if(go){if(location.hash==='#'+go.dataset.go)show(go.dataset.go);else location.hash=go.dataset.go}const freeze=e.target.closest('[data-freeze]');if(freeze){const id=freeze.dataset.freeze;if(state.snapshots[id]&&!freeze.disabled){recordSaveIssue='另一页面已保留这组首答，本页未能重新提交。请先导出本页草稿，再刷新核对原稿。';$('#save-status').textContent=recordSaveIssue;notice(recordSaveIssue);return}const fields={};$$(`#${id} .first-stage [data-save]`).forEach(el=>fields[el.dataset.save]=el.value);const answerKeys=Object.keys(fields).filter(k=>/-q\d+$|-essay$|-record-note$/.test(k));if(!answerKeys.length||!answerKeys.every(k=>String(fields[k]).trim())){notice('先完成各题的作答；不会的题可写“暂时不会”，再核对。');return}if(!state.snapshots[id]){state.snapshots[id]={at:new Date().toISOString(),fields};if(!save({snapshots:[id],expectedFields:fields},false)){delete state.snapshots[id];notice(recordWarning());return}}unlock(id);$('#'+id+'-learn').scrollIntoView({behavior:'smooth'});notice('首次作答已保留，下面开始学习。')}});
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}
document.addEventListener('click',e=>{const btn=e.target.closest('[data-export]');if(!btn)return;const kind=btn.dataset.export;let content;if(kind==='json'&&recoveryRaw!==null){download(new Blob([recoveryRaw],{type:'application/json'}),'IELTS-异常原始学习记录.json');notice('已导出异常原始记录；本次新输入请另用“导出文字作答”保留。');return}if(kind==='json')content=JSON.stringify(state,null,2);else{content='IELTS 四科学习册 · 我的作答\n导出时间：'+new Date().toLocaleString()+'\n\n';for(const [id,first] of Object.entries(state.snapshots)){content+='【'+id+' 首次原稿 · '+first.at+'】\n';for(const [k,v] of Object.entries(first.fields))content+=k+'：'+v+'\n';content+='\n'}content+='【练习、修订与复习记录】\n';for(const [k,v] of Object.entries(state.fields))content+=k+'：'+v+'\n';content+='\n录音需单独保存；本文件不包含音频。\n'}download(new Blob([content],{type:kind==='json'?'application/json':'text/plain;charset=utf-8'}),'IELTS-我的学习记录.'+(kind==='json'?'json':'txt'))});
$('#import-state').addEventListener('change',async e=>{
 const file=e.target.files[0];if(!file)return;
 try{
  const candidate=validateRecord(JSON.parse(await file.text()));
  let observed;try{observed=localStorage.getItem(key)}catch(err){notice('当前无法读取浏览器记录，未恢复备份。请先保留本页草稿和备份文件。');return}
  if((Object.keys(state.fields).length||Object.keys(state.snapshots).length||loadBlocked||observed!==null)&&!confirm('恢复备份会替换此浏览器的当前文字记录，包括其他页面刚保存的内容。请先导出本页草稿及当前记录，确定继续？'))return;
  const restored=recordConcurrency.restore(candidate,observed);
  if(!restored.ok){recordSaveIssue=concurrencyWarning(restored.reason);$('#save-status').textContent=recordWarning();notice(recordSaveIssue);return}
  state=candidate;storageOK=true;loadBlocked=false;recoveryRaw=null;recordSaveIssue='';location.reload();
 }catch(err){notice('未能恢复：备份格式不完整或含无效字段，当前记录未替换。')}
 finally{e.target.value=''}
});
const timers={};document.addEventListener('click',e=>{const b=e.target.closest('[data-timer]');if(!b)return;const id=b.dataset.timer;if(timers[id]){clearInterval(timers[id].interval);delete timers[id];b.textContent='重新开始 '+b.dataset.minutes+' 分钟计时';return}const end=Date.now()+Number(b.dataset.minutes)*60000;b.textContent='停止计时';timers[id]={interval:setInterval(()=>{const left=Math.max(0,Math.ceil((end-Date.now())/1000));$('#timer-'+id).textContent=Math.floor(left/60)+':'+String(left%60).padStart(2,'0');if(!left){clearInterval(timers[id].interval);delete timers[id];b.textContent='本次计时结束';notice('时间到了，请保留此刻的答案。')}},250)}});
const recorders={},urls={};function showAudio(id,blob,name){if(urls[id])URL.revokeObjectURL(urls[id]);const u=URL.createObjectURL(blob);urls[id]=u;const player=$(`[data-preview="${id}"]`);player.src=u;player.hidden=false;const a=$(`[data-download="${id}"]`);a.href=u;a.download=name;a.hidden=false;a.textContent='下载录音';$(`[data-rec-status="${id}"]`).textContent='已载入 '+name+'；请下载保存，刷新页面不会保留声音。';const note=$(`[data-save="${id}-record-note"]`)||(id==='speaking-review'?$(`[data-save="speaking-review-answer"]`):null);if(note&&!note.readOnly){note.value=name;note.dispatchEvent(new Event('input',{bubbles:true}))}}
document.addEventListener('click',async e=>{const start=e.target.closest('[data-record]'),stop=e.target.closest('[data-stop]');if(stop){recorders[stop.dataset.stop]?.rec.stop();return}if(!start)return;const id=start.dataset.record;if(!navigator.mediaDevices||!window.MediaRecorder){notice('当前浏览器不能录音，请用自己的录音器后载入文件。');return}try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});const rec=new MediaRecorder(stream),chunks=[];recorders[id]={rec,stream};rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};rec.onstop=()=>{stream.getTracks().forEach(t=>t.stop());const blob=new Blob(chunks,{type:rec.mimeType});showAudio(id,blob,'IELTS-'+id+'-'+new Date().toISOString().replace(/[:.]/g,'-')+'.webm');start.disabled=false;$(`[data-stop="${id}"]`).disabled=true};rec.start();start.disabled=true;$(`[data-stop="${id}"]`).disabled=false;$(`[data-rec-status="${id}"]`).textContent='正在录音；完成后点击结束并保留。'}catch(err){notice('未能开启麦克风。可用自己的录音器，再载入音频。')}});
$$('[data-upload]').forEach(el=>el.addEventListener('change',e=>{const f=e.target.files[0];if(f)showAudio(el.dataset.upload,f,f.name)}));
$$('.review-stage details').forEach(d=>{if(/完成后|核对|参考/.test(d.querySelector('summary')?.textContent||''))d.classList.add('answer-note')});
const dialog=document.createElement('dialog');dialog.className='zoom-dialog';dialog.innerHTML='<button type="button">关闭原页大图</button><img alt="放大的原始题页">';document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();$$('.original img').forEach(img=>{img.tabIndex=0;img.setAttribute('role','button');img.setAttribute('aria-label',img.alt+'；打开大图');const open=()=>{dialog.querySelector('img').src=img.src;dialog.showModal()};img.onclick=open;img.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}}});
window.preparePrint=kind=>{$$('.work-area').forEach(area=>area.prepend(area.querySelector('.response')));document.body.classList.add(kind==='reference'?'print-reference':'print-student');$$('details').forEach(d=>d.open=true);$$('main>.panel').forEach(p=>p.hidden=false);$$('.gated').forEach(p=>p.hidden=false);$$('img').forEach(p=>p.loading='eager');const cover=document.createElement('section');cover.className='print-cover';cover.innerHTML='<p class="eyebrow">IELTS / ACADEMIC · 第一册</p><h1>'+(kind==='reference'?'参考册<br>完成后，再看。':'把理解变成<br>会用的英语。')+'</h1><p>'+(kind==='reference'?'答案、证据解释、可接受表达与新情境核对。<br>先保留自己的首答，再拿其中一处和参考比较。':'四科学习册 · 原题、作答页、教学练习与隔日检查。<br>阅读与写作分别完成；听力与口语使用随附原音。')+'</p><div class="cover-list">01　阅读：找到判断的证据<br>02　Task 1：把图表讲清楚<br>03　Task 2：让理由站得住<br>04　听力：听清最终要填什么<br>05　口语：说清一件物品的意义</div><p class="small">音频与可填写版本：解压后打开“开始学习.html”。<br>原题来自用户提供的 Cambridge 21 Academic 及 Cambridge 官方公开样题。<br>中文教学与部分迁移任务为工作区编写，考生样本保留原有错误。<br>本册用于首轮学习；完成一本或局部练习不直接换算 IELTS 分数。</p>';$('main').prepend(cover)};
})();
