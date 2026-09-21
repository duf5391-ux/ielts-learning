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
