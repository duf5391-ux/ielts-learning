(() => {
  'use strict';
  const root = document.getElementById('writing-workbench');
  if (!root || root.dataset.wwReady) return;
  root.dataset.wwReady = 'true';
  const KEY = 'ielts-finished-book-v1';
  const picker = root.querySelector('#ww-task-picker');
  const units = [...root.querySelectorAll('[data-ww-unit]')];
  const timers = new Map();
  const byKey = key => root.querySelector(`[data-save="${key}"]`);
  const field = (unit, suffix) => byKey(`${unit.id}-${suffix}`);
  function setStage(unit, requested, save = false) {
    const stage = ['plan','draft','review','next'].includes(requested) ? requested : 'draft';
    for (const node of unit.querySelectorAll('[data-ww-step]')) node.hidden = node.dataset.wwStep !== stage;
    for (const link of unit.querySelectorAll('.ww-progress a')) {
      if (link.hash === '#'+unit.id+'-'+stage) link.setAttribute('aria-current','step');
      else link.removeAttribute('aria-current');
    }
    unit.dataset.wwCurrentStage=stage;
    if (save && field(unit,'stage').value !== stage && !put(field(unit,'stage'), stage)) fail();
    return stage;
  }

  const notice = message => {
    const el = root.querySelector('#ww-notice');
    el.textContent = message;
    el.hidden = false;
  };
  function persisted(el) {
    try {
      const record = JSON.parse(localStorage.getItem(KEY));
      return record?.version === 1 && record.fields?.[el.dataset.save] === (el.type === 'checkbox' ? el.checked : el.value);
    } catch { return false; }
  }
  function put(el, value) {
    if (el.type === 'checkbox') el.checked = value;
    else el.value = String(value);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    return persisted(el);
  }
  // Workflow transitions use the common record store, so a failed write does
  // not leave hidden metadata ahead of the visible editor or clock.
  function commit(values, expectedFields = values) {
    return !!window.IELTSRecordStore?.commit(values, {expectedFields});
  }
  const fail = () => notice('当前浏览器未能保存。这次输入仍在页面中；请先导出本题作答，再处理学习记录的保存提示。');
  function words(text) {
    return (text.match(/[A-Za-z0-9]+(?:['’.-][A-Za-z0-9]+)*/g) || []).length;
  }
  function wordCounts(unit) {
    for (const suffix of ['first', 'revision']) {
      const count = words(field(unit, suffix).value);
      const minimum = Number(unit.dataset.wwMinimum);
      unit.querySelector(`[data-ww-count="${unit.id}-${suffix}"]`).textContent = `${count} 词（估算） · ${count < minimum ? `距建议最低字数还差 ${minimum-count} 词` : `已达到 ${minimum} 词最低要求`}`;
    }
  }
  function readTimer(unit) {
    const minutes = Number(unit.dataset.wwMinutes);
    const fallback = {status: 'idle', remaining: minutes*60, deadline: 0};
    const raw = field(unit, 'timer').value;
    if (!raw) return fallback;
    try {
      const v = JSON.parse(raw);
      if (!['idle','running','paused','ended'].includes(v.status) || !Number.isFinite(v.remaining) || v.remaining < 0 || v.remaining > minutes*60 || !Number.isFinite(v.deadline) || v.deadline < 0) throw Error();
      return v;
    } catch { return {...fallback, invalid: true}; }
  }
  function remaining(timer) {
    return timer.status === 'running' ? Math.max(0, Math.ceil((timer.deadline-Date.now())/1000)) : timer.remaining;
  }
  function timerLabel(unit) {
    const timer = timers.get(unit.id);
    const left = remaining(timer);
    unit.querySelector('[data-ww-clock]').textContent = `${Math.floor(left/60)}:${String(left%60).padStart(2, '0')}`;
    const button = unit.querySelector('[data-ww-action="timer"]');
    button.disabled = !!timer.invalid || !!field(unit, 'first-at').value;
    button.textContent = timer.invalid ? '计时记录待修复' : timer.status === 'running' ? '暂停计时' : timer.status === 'paused' ? '继续计时' : timer.status === 'ended' ? '重新计时' : `开始 ${unit.dataset.wwMinutes} 分钟`;
  }
  function setTimer(unit, next) {
    const timerField = field(unit, 'timer');
    if (!commit({[timerField.dataset.save]: JSON.stringify(next)}, {[timerField.dataset.save]: timerField.value})) { fail(); return false; }
    timers.set(unit.id, next);
    timerLabel(unit);
    return true;
  }
  function timerAction(unit) {
    const timer = timers.get(unit.id);
    if (timer.invalid) { notice('计时记录无法读取。可导出本题保留原记录，然后重置计时。'); return; }
    const next = timer.status === 'running'
      ? {status: 'paused', remaining: remaining(timer), deadline: 0}
      : {status: 'running', remaining: timer.status === 'paused' ? timer.remaining : Number(unit.dataset.wwMinutes)*60, deadline: 0};
    if (next.status === 'running') next.deadline = Date.now()+next.remaining*1000;
    setTimer(unit, next);
  }
  function updateFrozen(unit) {
    const at = field(unit, 'first-at').value;
    field(unit, 'first').readOnly = !!at;
    const button = unit.querySelector('[data-ww-action="freeze"]');
    button.disabled = !!at;
    button.textContent = at ? '首稿已独立保留' : '保留首稿，开始修订';
    const date = new Date(at);
    unit.querySelector('[data-ww-frozen]').textContent = at ? `保留于 ${Number.isNaN(date.getTime()) ? at : date.toLocaleString()}` : '';
    unit.querySelector('[data-ww-action="reset-timer"]').disabled = !!at;
    timerLabel(unit);
  }
  function freeze(unit) {
    const draft = field(unit, 'first');
    if (!draft.value.trim()) { notice('先写下首稿，再保留。'); draft.focus(); return; }
    const at = field(unit, 'first-at');
    if (at.value) { updateFrozen(unit); return; }
    const revision = field(unit, 'revision');
    const timer = timers.get(unit.id);
    const paused = timer.status === 'running' ? {status: 'paused', remaining: remaining(timer), deadline: 0} : timer;
    const values = {[draft.dataset.save]: draft.value, [at.dataset.save]: new Date().toISOString(), [revision.dataset.save]: revision.value || draft.value};
    const expected = {[draft.dataset.save]: draft.value, [at.dataset.save]: at.value, [revision.dataset.save]: revision.value};
    if (!timer.invalid) {
      const timerField = field(unit, 'timer');
      values[timerField.dataset.save] = JSON.stringify(paused);
      expected[timerField.dataset.save] = timerField.value;
    }
    if (!commit(values, expected)) { fail(); return; }
    timers.set(unit.id, paused);
    updateFrozen(unit);
    wordCounts(unit);
    notice('首稿已保留；在「检查与修订」中继续修改，首稿保持原样。');
    setStage(unit,'review',true);
    location.hash=unit.id+'-review';
    unit.querySelector(`#${unit.id}-review`).scrollIntoView({behavior:'smooth',block:'start'});
  }
  function versions(unit) {
    const raw = field(unit, 'versions').value;
    if (!raw) return [];
    const list = JSON.parse(raw);
    if (!Array.isArray(list) || list.length > 1000 || list.some(v => !v || typeof v.at !== 'string' || typeof v.text !== 'string' || typeof v.reason !== 'string')) throw Error('无法读取修订记录');
    return list;
  }
  function renderHistory(unit) {
    const holder = unit.querySelector('[data-ww-history]');
    holder.replaceChildren();
    try {
      const list = versions(unit);
      if (!list.length) { holder.textContent = '尚未另存修订版本。当前修订稿仍会自动保存。'; return; }
      [...list].reverse().forEach((version, index) => {
        const detail = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = `修订 ${list.length-index} · ${new Date(version.at).toLocaleString()} · ${words(version.text)} 词`;
        const pre = document.createElement('pre');
        pre.textContent = version.text;
        const reason = document.createElement('p');
        reason.textContent = version.reason ? `修改理由：${version.reason}` : '未记录修改理由。';
        detail.append(summary, pre, reason);
        holder.append(detail);
      });
    } catch { holder.textContent = '已有修订记录无法读取，已保留原文。请先导出本题，再恢复有效的学习记录备份。'; }
  }
  function saveVersion(unit) {
    const text = field(unit, 'revision').value;
    if (!text.trim()) { notice('先写修订稿，再另存版本。'); return; }
    if (!field(unit, 'first-at').value) { notice('请先保留首稿，再另存修订版本。当前修订输入会保留。'); return; }
    try {
      const list = versions(unit);
      const reason = field(unit, 'reason').value;
      if (list.length && list[list.length-1].text === text && list[list.length-1].reason === reason) {
        if (!persisted(field(unit, 'versions'))) { fail(); return; }
        renderHistory(unit);
        notice('这一版已经保留；修改后再另存即可。'); return;
      }
      if (list.length >= 1000) { notice('修订版本已达 1000 份，请先导出保留。当前修订稿仍可编辑。'); return; }
      list.push({at: new Date().toISOString(), text, reason});
      const history = field(unit, 'versions');
      const revision = field(unit, 'revision');
      const reasonField = field(unit, 'reason');
      const values = {[history.dataset.save]: JSON.stringify(list), [revision.dataset.save]: text, [reasonField.dataset.save]: reason};
      const expected = {[history.dataset.save]: history.value, [revision.dataset.save]: text, [reasonField.dataset.save]: reason, [field(unit, 'first-at').dataset.save]: field(unit, 'first-at').value};
      if (!commit(values, expected)) { fail(); return; }
      renderHistory(unit);
      notice(`已保留修订 ${list.length}，可以继续修改当前修订稿。`);
    } catch { notice('已有修订记录无法读取，未覆盖。请导出本题保留原始内容。'); }
  }
  function nextAction(unit) {
    const choice = field(unit, 'next-focus').value;
    const task1 = Number(unit.dataset.wwMinimum) === 150;
    const suggestions = {
      task: task1 ? '重看原图，在不列细节数字的情况下写两句概览，再逐项核对是否概括主要特征。' : '把题目每个问句单独列出；为每一问写一句明确回答，再核对首稿有没有漏答。',
      coherence: task1 ? '给每段标一个功能，并重新分组同类特征；检查是否把一组比较拆散到几个段落。' : '从一个主体段里标出观点、解释、例子；若只有观点和例子，补一句解释为什么例子支持观点。',
      lexical: '从自己的稿中取三个不确定的搭配，结合原句查词并收藏；核对词义后，各写一句与本题相关的新句。',
      grammar: '从稿中选一条复杂句，找出主句主语和谓语、从句关系与标点；修好后，再独立写一句表达同类关系的新句。',
      transfer: '按本页下方入口换一道题。先记录是否见过题目，关闭提示独立完成目标动作，再与原来的问题对照。',
    };
    unit.querySelector('[data-ww-next]').textContent = suggestions[choice] || suggestions.task;
  }
  function resumeStatus(unit) {
    const draft = field(unit, 'first').value;
    const revised = field(unit, 'revision').value;
    const next = field(unit, 'next-date').value;
    root.querySelector('#ww-resume').textContent = `${unit.querySelector('h2').textContent} · ${field(unit,'first-at').value ? '首稿已保留' : draft.trim() ? '首稿写作中' : '尚未开始'}${revised.trim() ? ' · 有修订稿' : ''}${next ? ' · 计划复查 '+next : ''}`;
  }
  function selectUnit(id, saveSelection = false) {
    const selected = units.find(u => u.id === id) || units[0];
    for (const unit of units) unit.hidden = unit !== selected;
    picker.value = selected.id;
    if (saveSelection && !put(picker, selected.id)) fail();
    setStage(selected, field(selected,'stage').value || (field(selected,'first-at').value ? 'review' : 'draft'));
    resumeStatus(selected);
    return selected;
  }
  function onHash() {
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(hash);
    const unit = target?.closest('[data-ww-unit]');
    if (unit) {
      selectUnit(unit.id, true);
      const step = target.closest('[data-ww-step]');
      setStage(unit, step?.dataset.wwStep || field(unit,'stage').value || unit.dataset.wwCurrentStage || 'draft', !!step);
      requestAnimationFrame(() => unit.querySelector('[data-ww-step]:not([hidden])').scrollIntoView({block:'start'}));
    } else if (hash === 'writing-workbench') {
      const selected=selectUnit(picker.value);
      if (field(selected,'first').value.trim() || field(selected,'first-at').value) requestAnimationFrame(()=>selected.querySelector('[data-ww-step]:not([hidden])').scrollIntoView({block:'start'}));
    }
    if (!root.hidden) {
      const title = document.getElementById('current-page-label');
      if (title) title.textContent = '写作工作台';
      document.title = '写作工作台 · IELTS Work';
    }
  }
  function exportUnit(unit) {
    const rows = [`IELTS 写作工作台 · ${unit.querySelector('h2').textContent}`, `导出时间：${new Date().toLocaleString()}`, '', '【题目与来源】', unit.querySelector('.ww-prompt').textContent, unit.querySelector('.ww-source-detail').textContent, ''];
    for (const input of unit.querySelectorAll('[data-save]')) {
      const label = input.closest('label')?.querySelector('span')?.textContent || input.closest('label')?.textContent?.trim() || input.dataset.save;
      const value = input.type === 'checkbox' ? (input.checked ? '是' : '否') : input.tagName === 'SELECT' ? input.options[input.selectedIndex]?.textContent : input.value;
      rows.push(`【${label}】`, value || '（未填写）', '');
    }
    rows.push('【可发给助手或老师的反馈请求】', '请结合题目、首稿、修订稿和作答条件，按 TA/TR、CC、LR、GRA 检查。每项给出具体作品证据，只优先选 1–2 个问题，解释修改理由，如确有需要，再建议一个可选的局部练习。不要仅凭字数、复杂词数量或勾选结果给分。');
    const blob = new Blob([rows.join('\n')], {type:'text/plain;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `IELTS-写作-${unit.dataset.wwUnit}-${new Date().toISOString().slice(0,10)}.txt`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }
  for (const unit of units) {
    timers.set(unit.id, readTimer(unit));
    wordCounts(unit); updateFrozen(unit); renderHistory(unit); nextAction(unit);
  }
  selectUnit(picker.value);
  picker.addEventListener('change', () => { selectUnit(picker.value, true); location.hash = picker.value; });
  root.addEventListener('input', event => {
    const unit = event.target.closest('[data-ww-unit]');
    if (!unit) return;
    if (event.target.matches('textarea')) wordCounts(unit);
    if (event.target === field(unit,'next-focus')) nextAction(unit);
    resumeStatus(unit);
  });
  root.addEventListener('toggle', event => {
    if (event.target.matches('details[data-ww-support]') && event.target.open) {
      const unit = event.target.closest('[data-ww-unit]');
      if (!put(field(unit,'used-help'), true)) fail();
    }
  }, true);
  root.addEventListener('click', event => {
    const button = event.target.closest('[data-ww-action]');
    if (!button) return;
    const unit = button.closest('[data-ww-unit]');
    switch (button.dataset.wwAction) {
      case 'timer': timerAction(unit); break;
      case 'reset-timer': setTimer(unit, {status:'idle',remaining:Number(unit.dataset.wwMinutes)*60,deadline:0}); break;
      case 'freeze': freeze(unit); break;
      case 'version': saveVersion(unit); break;
      case 'export': exportUnit(unit); break;
    }
    resumeStatus(unit);
  });
  window.addEventListener('hashchange', onHash);
  onHash();
  setInterval(() => {
    for (const unit of units) {
      const timer = timers.get(unit.id);
      if (timer.status !== 'running') continue;
      if (remaining(timer) === 0) {
        // Stop the in-memory clock even if storage is unavailable, avoiding repeated writes.
        const ended = {status:'ended',remaining:0,deadline:0};
        timers.set(unit.id, ended);
        const timerField = field(unit, 'timer');
        if (!commit({[timerField.dataset.save]: JSON.stringify(ended)}, {[timerField.dataset.save]: timerField.value})) fail();
        else notice(`${unit.querySelector('h2').textContent}：时间到了。输入仍保留，可将此刻首稿独立保存后修订。`);
      }
      timerLabel(unit);
    }
  }, 500);
})();
