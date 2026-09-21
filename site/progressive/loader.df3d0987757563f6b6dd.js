/* Cooperative bootstrap. The original controllers run once, after all saved fields exist. */
(() => {
  'use strict';
  const prefix = 'ielts-progressive-';
  const boot = document.getElementById(prefix + 'boot');
  if (!boot || boot.dataset.started) return;
  boot.dataset.started = 'true';
  const status = document.getElementById(prefix + 'status');
  const progress = document.getElementById(prefix + 'progress');
  const retry = document.getElementById(prefix + 'retry');
  const buttons = [...boot.querySelectorAll('[data-pb-route]')];
  let pendingHash = location.hash || '#study';
  let initializing = false;
  let chosenLabel = '';
  for (const button of buttons) button.addEventListener('click', event => {
    event.preventDefault();
    if (initializing) return;
    pendingHash = button.dataset.pbRoute;
    chosenLabel = button.textContent.trim();
    for (const option of buttons) option.setAttribute('aria-pressed', String(option === button));
    status.textContent = '准备好后打开「' + chosenLabel + '」。';
  });
  retry.addEventListener('click', () => location.reload());
  let lastPaintYield = 0;
  const taskQueue = [];
  const channel = new MessageChannel();
  channel.port1.onmessage = () => taskQueue.shift()?.();
  const yieldTask = () => {
    if (globalThis.scheduler?.yield) return scheduler.yield();
    return new Promise(resolve => { taskQueue.push(resolve); channel.port2.postMessage(null); });
  };
  async function yieldFrame() {
    // Yield after every small insertion. Give paint a full frame after ~8 ms of work,
    // rather than imposing one whole display frame per fragment on a fast device.
    if (!document.hidden && performance.now() - lastPaintYield >= 8) {
      await new Promise(resolve => requestAnimationFrame(resolve));
      lastPaintYield = performance.now();
    }
    await yieldTask();
  }
  const commentMap = new Map();
  function collectComments(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
    let node;
    while ((node = walker.nextNode())) if (node.data.startsWith(prefix)) {
      if (commentMap.has(node.data)) throw new Error('Duplicate content anchor');
      commentMap.set(node.data, node);
    }
  }
  async function fetchVerified(asset) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await fetch(new URL(asset.path, document.baseURI), {
        signal: controller.signal, credentials: 'same-origin', cache: 'default'
      });
      if (!response.ok) throw new Error('Content HTTP ' + response.status);
      const bytes = await response.arrayBuffer();
      if (bytes.byteLength !== asset.bytes) throw new Error('Content size mismatch');
      if (!globalThis.crypto?.subtle) throw new Error('A secure connection is required');
      const digest = await crypto.subtle.digest('SHA-256', bytes);
      const actual = [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, '0')).join('');
      if (actual !== asset.sha256) throw new Error('Content version mismatch');
      return JSON.parse(new TextDecoder().decode(bytes));
    } finally {
      clearTimeout(timeout);
    }
  }
  async function runController(descriptor) {
    const anchor = commentMap.get(descriptor.marker);
    if (!anchor?.parentNode) throw new Error('Missing controller position');
    const script = document.createElement('script');
    for (const [name, value] of descriptor.attrs) script.setAttribute(name, value ?? '');
    script.async = false;
    if (descriptor.runtime_src) {
      script.src = descriptor.runtime_src;
      script.integrity = descriptor.integrity;
    } else script.textContent = descriptor.code;
    let executionError = null;
    const capture = event => { executionError = event.error || new Error(event.message || 'Controller failed'); };
    window.addEventListener('error', capture);
    try {
      if (descriptor.runtime_src) {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('Controller download timeout')), 30000);
          script.onload = () => { clearTimeout(timer); resolve(); };
          script.onerror = () => { clearTimeout(timer); reject(new Error('Controller could not load')); };
          anchor.replaceWith(script);
        });
      } else anchor.replaceWith(script);
      await yieldFrame();
      if (executionError) throw executionError;
    } finally {
      window.removeEventListener('error', capture);
      script.onload = script.onerror = null;
    }
  }
  async function start() {
    performance.mark('ielts-progressive-start');
    collectComments(document.body);
    const config = JSON.parse(document.getElementById(prefix + 'config').textContent);
    const manifest = await fetchVerified(config.manifest);
    if (manifest.version !== 1) throw new Error('Unsupported content version');
    const controllersPromise = fetchVerified(manifest.controllers);
    // Attach handlers immediately so a failed prefetched resource never becomes an unhandled rejection.
    const settledControllers = controllersPromise.then(value => ({value}), error => ({error}));
    const pending = new Map();
    const prefetch = index => {
      if (index < manifest.packs.length && !pending.has(index)) {
        pending.set(index, fetchVerified(manifest.packs[index]).then(value => ({value}), error => ({error})));
      }
    };
    prefetch(0); prefetch(1);
    let completed = 0;
    for (let index = 0; index < manifest.packs.length; index++) {
      const result = await pending.get(index);
      pending.delete(index);
      if (result.error) throw result.error;
      prefetch(index + 2);
      for (const operation of result.value) {
        const target = commentMap.get(operation.target);
        if (!target?.parentNode) throw new Error('Missing content position');
        const range = document.createRange();
        range.selectNode(target);
        const fragment = range.createContextualFragment(operation.html);
        // Executable scripts are absent from all content packs; only original JSON data remains.
        for (const script of fragment.querySelectorAll('script')) {
          if (!['application/json', 'application/ld+json'].includes(script.type)) throw new Error('Unexpected content script');
        }
        collectComments(fragment);
        target.parentNode.insertBefore(fragment, target);
        completed++;
        progress.value = Math.round(completed / manifest.operation_count * 82);
        await yieldFrame();
      }
    }
    if (completed !== manifest.operation_count || document.querySelectorAll('[data-save]').length !== manifest.field_count) {
      throw new Error('Learning content is incomplete');
    }
    for (const id of manifest.json_script_ids) if (id && !document.getElementById(id)) throw new Error('Missing course data');
    for (const name of manifest.anchors) {
      const anchor = commentMap.get(name);
      if (!anchor) throw new Error('Missing content anchor');
      anchor.remove();
    }
    initializing = true;
    document.body.dataset.progressiveState = 'initializing';
    for (const button of buttons) button.setAttribute('disabled', '');
    status.textContent = '正在恢复学习进度…';
    if (location.hash !== pendingHash) history.replaceState(history.state, '', location.pathname + location.search + pendingHash);
    const controllersResult = await settledControllers;
    if (controllersResult.error) throw controllersResult.error;
    const controllers = controllersResult.value;
    if (controllers.length !== manifest.script_count) throw new Error('Incomplete learning controls');
    for (let index = 0; index < controllers.length; index++) {
      await runController(controllers[index]);
      progress.value = 82 + Math.round((index + 1) / controllers.length * 18);
    }
    performance.mark('ielts-progressive-ready');
    performance.measure('ielts-progressive-bootstrap', 'ielts-progressive-start', 'ielts-progressive-ready');
    document.body.removeAttribute('data-progressive-state');
    document.documentElement.dataset.progressiveReady = 'true';
    boot.remove();
    document.getElementById(prefix + 'style').remove();
    document.getElementById(prefix + 'config').remove();
    document.getElementById(prefix + 'loader').remove();
    channel.port1.close(); channel.port2.close();
    document.dispatchEvent(new CustomEvent('ielts:progressive-ready'));
  }
  start().catch(error => {
    document.body.dataset.progressiveState = 'error';
    status.textContent = '内容暂时没有准备完整。请检查网络，再重新打开。';
    progress.hidden = true;
    retry.hidden = false;
    for (const button of buttons) button.setAttribute('disabled', '');
    boot.dataset.error = error.name || 'Error';
    channel.port1.close(); channel.port2.close();
    console.error('Learning page preparation failed:', error);
  });
})();
