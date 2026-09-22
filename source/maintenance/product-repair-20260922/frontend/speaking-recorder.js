/* SPEAKING-RECORDER-20260922. Each take is retained by task in this browser. */
(() => {
  'use strict';
  const starts = [...document.querySelectorAll('[data-record]')];
  if (!starts.length) return;
  const control = (name, id) => document.querySelector(`[data-${name}="${id}"]`);
  const urls = new Map(), awaitingDownload = new Set();
  let active = null;
  const takes=new Map(),pendingSaves=new Set();let databasePromise;
  function database(){
    if(!databasePromise)databasePromise=new Promise((resolve,reject)=>{
      if(!window.indexedDB){reject(Error('音频存储不可用'));return;}
      const request=indexedDB.open('ielts-speaking-audio-v1',1);
      request.onupgradeneeded=()=>{const db=request.result;const store=db.createObjectStore('takes',{keyPath:'key'});store.createIndex('unit','unit');};
      request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);request.onblocked=()=>reject(Error('音频存储正被另一页面占用'));
    }).catch(error=>{databasePromise=null;throw error;});
    return databasePromise;
  }
  async function stored(id){const db=await database();return new Promise((resolve,reject)=>{const q=db.transaction('takes').objectStore('takes').index('unit').getAll(id);q.onsuccess=()=>resolve(q.result.sort((a,b)=>a.at.localeCompare(b.at)));q.onerror=()=>reject(q.error);});}
  async function retain(take){const db=await database();return new Promise((resolve,reject)=>{const tx=db.transaction('takes','readwrite');tx.objectStore('takes').put(take);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||Error('录音未保存'));});}
  function markSaved(id,take){const field=document.querySelector(`[data-save="${id}-audio-saved"]`);if(!field)return;const value=take?JSON.stringify({key:take.key,at:take.at,name:take.name}):'';if(field.value!==value)window.IELTSRecordStore?.commit({[field.dataset.save]:value},{expectedFields:{[field.dataset.save]:field.value}});}
  function history(id){
    const holder=control('record',id)?.closest('.recorder');if(!holder)return;
    let list=holder.querySelector('[data-audio-history]');if(!list){const label=document.createElement('label');label.textContent='本题已保存的录音 ';list=document.createElement('select');list.dataset.audioHistory=id;list.setAttribute('aria-label','本题已保存的录音');label.append(list);holder.append(label);list.addEventListener('change',()=>{const take=takes.get(id)?.find(t=>t.key===list.value);if(take){displayAudio(id,take.blob,take.name);status(id,'已切换到保存的录音；可回听或下载备份。');}});}
    const rows=takes.get(id)||[];list.replaceChildren();rows.forEach((take,i)=>{const option=document.createElement('option');option.value=take.key;option.textContent=(i===0?'首录':'录音 '+(i+1))+' · '+new Date(take.at).toLocaleString();list.append(option);});list.value=rows.at(-1)?.key||'';list.parentElement.hidden=!rows.length;
    control('record',id).textContent=rows.length?'再录一版（保留已有录音）':'开始录音';
  }
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
  function displayAudio(id, blob, name) {
    if (!blob.size) { status(id, '未收到有效音频；原有录音仍保留，请重新录制或载入音频。'); return; }
    const previous = urls.get(id), url = URL.createObjectURL(blob);
    const player = control('preview', id);
    player.pause(); player.src = url; player.hidden = false;
    const link = control('download', id);
    link.href = url; link.download = name; link.hidden = false; link.textContent = '下载录音';
    urls.set(id, url);
    if (previous) URL.revokeObjectURL(previous);
  }
  async function showAudio(id, blob, name) {
    if(!blob.size){status(id,'未收到有效音频；原有录音仍保留，请重试。');return;}
    displayAudio(id,blob,name);awaitingDownload.add(id);pendingSaves.add(id);
    status(id,'音频可回听，正在保存到本浏览器…');
    const at=new Date().toISOString(),take={key:id+':'+(crypto.randomUUID?.()||at+Math.random()),unit:id,at,blob,name};
    try{await retain(take);const rows=await stored(id);takes.set(id,rows);history(id);markSaved(id,take);awaitingDownload.delete(id);status(id,'录音已保存在本浏览器，刷新后可回听；首录和每次重录分别保留。换设备请下载音频，文字备份不包含声音。');}
    catch{status(id,'录音未保存成功，目前仅在此页可回听。请立即下载保留，刷新后这次录音会丢失；此前已保存的录音不受影响。');}
    finally{pendingSaves.delete(id);}
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
    if (active || pendingSaves.size) {
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
      status(download.dataset.download, '已发起录音下载，请确认文件已保存；可以载入下载的音频。');
    }
  });
  document.querySelectorAll('[data-upload]').forEach(input => input.addEventListener('change', event => {
    const file = event.target.files[0], id = input.dataset.upload;
    if (!file) return;
    if (active || pendingSaves.size) { status(id, '请先结束并保存当前录音，再载入已有音频。'); input.value = ''; return; }
    if (!(file.type.startsWith('audio/') || /\.(webm|ogg|m4a|mp4|wav|mp3|aac|flac|opus)$/i.test(file.name))) {
      status(id, '请选择音频文件；原有录音仍保留。'); input.value = ''; return;
    }
    showAudio(id, file, file.name); input.value = '';
  }));
  window.addEventListener('beforeunload', event => {
    if (active || pendingSaves.size || awaitingDownload.size) { event.preventDefault(); event.returnValue = ''; }
  });
  window.addEventListener('pagehide', event => {
    if (active) { active.cancelled = true; release(active.stream); }
    if (!event.persisted) for (const url of urls.values()) URL.revokeObjectURL(url);
  });
  for(const button of starts){const id=button.dataset.record;stored(id).then(rows=>{takes.set(id,rows);history(id);if(rows.length){const take=rows.at(-1);displayAudio(id,take.blob,take.name);markSaved(id,take);status(id,'已有 '+rows.length+' 份录音保存在本浏览器，可回听、下载或再录一版。');}else markSaved(id,null);}).catch(()=>status(id,'本浏览器暂时无法读取已保存的音频；可稍后重试，或载入已下载音频。文字草稿仍可使用。'));}
})();
