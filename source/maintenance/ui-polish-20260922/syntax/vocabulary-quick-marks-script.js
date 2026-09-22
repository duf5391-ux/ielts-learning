(() => {
  'use strict';
  const root = document.getElementById('topical-vocabulary');
  if (!root) return;
  const enhanced = new Map();
  let scheduled = false;
  const status = document.createElement('p');
  status.className = 'vq-notice';
  status.setAttribute('role', 'status');
  root.querySelector('#tv-count')?.after(status);
  function sync(select, group) {
    group.querySelectorAll('button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.vqValue !== '' && select.value === button.dataset.vqValue));
      button.disabled = select.disabled || (button.dataset.vqValue === '' && select.value === '');
    });
  }
  function enhance(card) {
    const select = card.querySelector('select[data-save^="topic-vocab-level-"]');
    if (!select || enhanced.has(select)) return;
    const group = document.createElement('div');
    const term = card.querySelector('h3')?.firstChild?.textContent?.trim() || '这个词';
    group.className = 'vq-choices';
    group.setAttribute('role', 'group');
    group.setAttribute('aria-label', term + ' 的熟悉度');
    for (const [value, label] of [['N', '新学'], ['R', '认识少用'], ['K', '已会用'], ['', '清除']]) {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = label; button.dataset.vqValue = value;
      button.addEventListener('click', () => {
        if (select.disabled || select.value === value) return;
        const ok = window.IELTSRecordStore?.commit({[select.dataset.save]: value}) === true;
        sync(select, group);
        status.textContent = ok ? term + (value ? '：已标记“' + label + '”。' : '：已清除熟悉度标记。') : '标记未保存，原状态未改动。请处理页面保存提示后重试。';
      });
      group.append(button);
    }
    // Keep the original saved select and its values; only replace its visible control.
    const label = select.closest('label');
    if (!label) return;
    label.after(group); label.hidden = true;
    enhanced.set(select, group); sync(select, group);
  }
  function render() {
    scheduled = false;
    if (root.dataset.tvReady !== 'true' || !root.getClientRects().length) return;
    for (const card of root.querySelectorAll('.tv-card:not([hidden])')) enhance(card);
    for (const [select, group] of enhanced) if (!select.closest('.tv-card').hidden) sync(select, group);
  }
  function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(render); } }
  new MutationObserver(schedule).observe(root, {subtree:true, attributes:true, attributeFilter:['hidden','data-tv-ready']});
  document.addEventListener('ielts-record-committed', () => { status.textContent = ''; schedule(); });
  root.addEventListener('change', schedule);
  window.addEventListener('hashchange', schedule);
  document.getElementById('import-state')?.addEventListener('change', () => setTimeout(schedule, 350));
  schedule();
})();
