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

window.IELTSRecordStore={commit(values, options = {}){
 if(loadBlocked)return false;
 const controls=Object.entries(values).map(([k,v])=>[$(`[data-save="${k}"]`),v]);
 if(controls.some(([n,v])=>!n||!['string','boolean'].includes(typeof v)))return false;
 const previous=state;
 state={...state,fields:{...state.fields,...values}};
 if(!save({fields:Object.keys(values),expectedFields:options.expectedFields||{}},false)){state=previous;return false}
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
/*SPEAKING-RECORDER-FIX:START*/
/* SPEAKING-RECORDER-20260921. Audio stays in this tab until downloaded. */
(() => {
  'use strict';
  const starts = [...document.querySelectorAll('[data-record]')];
  if (!starts.length) return;
  const control = (name, id) => document.querySelector(`[data-${name}="${id}"]`);
  const urls = new Map(), awaitingDownload = new Set();
  let active = null;
  const status = (id, text) => {
    const node = control('rec-status', id);
    if (node) { node.textContent = text; node.setAttribute('role', 'status'); node.setAttribute('aria-live', 'polite'); }
  };
  const release = stream => stream?.getTracks().forEach(track => track.stop());
  function buttons(id, busy) {
    control('record', id).disabled = busy;
    control('stop', id).disabled = !busy;
  }
  function finish(session) {
    release(session.stream);
    if (active === session) { buttons(session.id, false); active = null; }
  }
  function showAudio(id, blob, name) {
    if (!blob.size) { status(id, '未收到有效音频；原有录音仍保留，请重新录制或载入音频。'); return; }
    const previous = urls.get(id), url = URL.createObjectURL(blob);
    const player = control('preview', id);
    player.pause(); player.src = url; player.hidden = false;
    const link = control('download', id);
    link.href = url; link.download = name; link.hidden = false; link.textContent = '下载录音';
    urls.set(id, url); awaitingDownload.add(id);
    if (previous) URL.revokeObjectURL(previous);
    status(id, `已载入 ${name}；请下载保存。刷新后需重新载入音频，文字备份不包含声音。`);
    const note = document.querySelector(`[data-save="${id}-record-note"]`) || (id === 'speaking-review' ? document.querySelector('[data-save="speaking-review-answer"]') : null);
    // Never replace a learner's observations or transcript with a filename.
    if (note && !note.readOnly && !note.value.trim()) {
      note.value = name; note.dispatchEvent(new Event('input', {bubbles: true}));
    }
  }
  function recordingName(id, type) {
    const mime = type.split(';')[0].toLowerCase();
    const extension = ({'audio/mp4':'m4a', 'video/mp4':'mp4', 'audio/ogg':'ogg', 'video/ogg':'ogg', 'audio/webm':'webm', 'video/webm':'webm', 'audio/wav':'wav', 'audio/mpeg':'mp3'})[mime] || 'audio';
    return `IELTS-${id}-${new Date().toISOString().replace(/[:.]/g, '-')}.${extension}`;
  }
  function stop(session) {
    if (!session || session.stopping) return;
    session.stopping = true;
    if (!session.rec) {
      session.cancelled = true; finish(session);
      status(session.id, '已取消麦克风请求；即使稍后授权，也不会开始这次录音。');
      return;
    }
    status(session.id, '正在结束录音，请稍候；音频准备好后可试听并下载。');
    try {
      if (session.rec.state !== 'inactive') session.rec.stop();
    } catch {
      finish(session); status(session.id, '未能结束这次录音；原有音频仍保留，请重试。');
    }
  }
  async function start(id) {
    if (active) {
      status(id, '已有录音或麦克风请求正在进行。请先在原题结束录音，再开始本题。'); return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      status(id, '当前浏览器不能录音。请使用 HTTPS 网站并允许麦克风，或用自己的录音器后载入音频。'); return;
    }
    const session = {id, stream: null, rec: null, chunks: [], cancelled: false, stopping: false};
    active = session; buttons(id, true);
    status(id, '正在请求麦克风权限；点“结束并保留”可取消本次请求。');
    try {
      session.stream = await navigator.mediaDevices.getUserMedia({audio: true});
      if (session.cancelled || active !== session) { release(session.stream); return; }
      const type = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus'].find(value => MediaRecorder.isTypeSupported?.(value));
      const recorder = type ? new MediaRecorder(session.stream, {mimeType: type}) : new MediaRecorder(session.stream);
      session.rec = recorder;
      recorder.ondataavailable = event => { if (event.data?.size) session.chunks.push(event.data); };
      recorder.onstop = () => {
        const blob = new Blob(session.chunks, {type: recorder.mimeType || session.chunks[0]?.type || 'application/octet-stream'});
        finish(session);
        showAudio(id, blob, recordingName(id, blob.type));
        if (session.failed && blob.size) status(id, '录音因设备问题中断；已保留收到的部分音频，请试听并下载。');
      };
      recorder.onerror = () => {
        session.failed = true;
        status(id, '录音设备发生错误，正在保留已经收到的音频。');
        stop(session);
      };
      recorder.start();
      status(id, '正在录音；完成后点击结束并保留，再下载声音。');
    } catch (error) {
      finish(session);
      if (session.cancelled) return;
      const message = error?.name === 'NotAllowedError' ? '麦克风权限未获允许。请在浏览器网站权限中允许后重试，或载入已有音频。'
        : error?.name === 'NotFoundError' ? '没有找到麦克风。请连接麦克风后重试，或载入已有音频。'
        : '未能开启录音，麦克风已释放。请检查设备是否被其他应用占用，或载入已有音频。';
      status(id, message);
    }
  }
  document.addEventListener('click', event => {
    const startButton = event.target.closest('[data-record]');
    if (startButton) { start(startButton.dataset.record); return; }
    const stopButton = event.target.closest('[data-stop]');
    if (stopButton) { if (active?.id === stopButton.dataset.stop) stop(active); return; }
    const download = event.target.closest('[data-download]');
    if (download && urls.has(download.dataset.download)) {
      awaitingDownload.delete(download.dataset.download);
      status(download.dataset.download, '已发起录音下载；请确认文件已保存。刷新后可重新载入该文件。');
    }
  });
  document.querySelectorAll('[data-upload]').forEach(input => input.addEventListener('change', event => {
    const file = event.target.files[0], id = input.dataset.upload;
    if (!file) return;
    if (active) { status(id, '请先结束当前录音，再载入已有音频。'); input.value = ''; return; }
    if (!(file.type.startsWith('audio/') || /\.(webm|ogg|m4a|mp4|wav|mp3|aac|flac|opus)$/i.test(file.name))) {
      status(id, '请选择音频文件；原有录音仍保留。'); input.value = ''; return;
    }
    showAudio(id, file, file.name); input.value = '';
  }));
  window.addEventListener('beforeunload', event => {
    if (active || awaitingDownload.size) { event.preventDefault(); event.returnValue = ''; }
  });
  window.addEventListener('pagehide', event => {
    if (active) { active.cancelled = true; release(active.stream); }
    if (!event.persisted) for (const url of urls.values()) URL.revokeObjectURL(url);
  });
})();

/*SPEAKING-RECORDER-FIX:END*/
$$('.review-stage details').forEach(d=>{if(/完成后|核对|参考/.test(d.querySelector('summary')?.textContent||''))d.classList.add('answer-note')});
const dialog=document.createElement('dialog');dialog.className='zoom-dialog';dialog.innerHTML='<button type="button">关闭原页大图</button><img alt="放大的原始题页">';document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();$$('.original img').forEach(img=>{img.tabIndex=0;img.setAttribute('role','button');img.setAttribute('aria-label',img.alt+'；打开大图');const open=()=>{dialog.querySelector('img').src=img.src;dialog.showModal()};img.onclick=open;img.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}}});
window.preparePrint=kind=>{$$('.work-area').forEach(area=>area.prepend(area.querySelector('.response')));document.body.classList.add(kind==='reference'?'print-reference':'print-student');$$('details').forEach(d=>d.open=true);$$('main>.panel').forEach(p=>p.hidden=false);$$('.gated').forEach(p=>p.hidden=false);$$('img').forEach(p=>p.loading='eager');const cover=document.createElement('section');cover.className='print-cover';cover.innerHTML='<p class="eyebrow">IELTS / ACADEMIC · 第一册</p><h1>'+(kind==='reference'?'参考册<br>完成后，再看。':'把理解变成<br>会用的英语。')+'</h1><p>'+(kind==='reference'?'答案、证据解释、可接受表达与新情境核对。<br>先保留自己的首答，再拿其中一处和参考比较。':'四科学习册 · 原题、作答页、教学练习与隔日检查。<br>阅读与写作分别完成；听力与口语使用随附原音。')+'</p><div class="cover-list">01　阅读：找到判断的证据<br>02　Task 1：把图表讲清楚<br>03　Task 2：让理由站得住<br>04　听力：听清最终要填什么<br>05　口语：说清一件物品的意义</div><p class="small">音频与可填写版本：解压后打开“开始学习.html”。<br>原题来自用户提供的 Cambridge 21 Academic 及 Cambridge 官方公开样题。<br>中文教学与部分迁移任务为工作区编写，考生样本保留原有错误。<br>本册用于首轮学习；完成一本或局部练习不直接换算 IELTS 分数。</p>';$('main').prepend(cover)};
})();
