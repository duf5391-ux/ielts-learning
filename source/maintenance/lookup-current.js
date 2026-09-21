(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const field = $('#lookup-history-store');
  const glossary = JSON.parse($('#lookup-glossary').textContent);
  const popup = $('#word-lookup');
  const result = $('#lookup-result');
  const input = $('#lookup-input');
  let serial = 0, controller, current = null, openedFrom = null;
  const normalize = t => t.trim().toLowerCase().replace(/[’]/g, "'").replace(/\s+/g, ' ');
  function node(tag, text, cls) {
    const el = document.createElement(tag); if (text) el.textContent = text;
    if (cls) el.className = cls; return el;
  }
  function history() {
    try { const rows = JSON.parse(field.value || '[]'); return Array.isArray(rows) ? rows.filter(r => r && typeof r.term === 'string') : []; }
    catch { return []; }
  }
  function save(rows) { field.value = JSON.stringify(rows); field.dispatchEvent(new Event('input', {bubbles:true})); renderHistory(); }
  function remember(term, context, data) {
    const rows = history(); const key = normalize(term); const old = rows.find(r => r.key === key);
    const now = new Date().toISOString();
    const entry = {...old, key, term, firstAt:old?.firstAt || now, lastAt:now,
      count:(old?.count || 0) + 1, status:'pending', context:context || old?.context || '',
      meaning:data.meaning || old?.meaning || '', chunk:data.chunk || old?.chunk || '',
      source:data.source || '', lookupState:data.meaning ? 'found' : 'unresolved'};
    save([entry, ...rows.filter(r => r.key !== key)]);
  }
  function supplement(term, data) {
    const rows = history(); const row = rows.find(r => r.key === normalize(term));
    if (row) { Object.assign(row, data); save(rows); }
  }
  function renderHistory() {
    const rows = history(); const filter = $('#lookup-filter').value;
    const q = normalize($('#lookup-history-search').value);
    const shown = rows.filter(r => (filter === 'all' || r.status === filter) &&
      normalize([r.term,r.meaning,r.context].join(' ')).includes(q));
    $('#lookup-history-count').textContent = `${rows.length} 个词或词组 · ${rows.filter(r => r.status !== 'reviewed').length} 个待复习`;
    const list = $('#lookup-history-list'); list.replaceChildren();
    if (!shown.length) { list.append(node('p', rows.length ? '没有匹配的记录。' : '点击正文中的英文词，释义和原句会自动留在这里。', 'lookup-muted')); return; }
    for (const row of shown.slice(0, 60)) {
      const card = node('article', '', 'lookup-record');
      const head = node('div', '', 'lookup-record-head');
      const reopen = node('button', row.term, 'lookup-term'); reopen.type = 'button';
      reopen.addEventListener('click', event => { event.stopPropagation(); lookup(row.term, row.context, reopen); });
      head.append(reopen, node('span', row.status === 'reviewed' ? '已复习' : '待复习', 'lookup-tag'));
      card.append(head, node('p', row.meaning || '暂未查到释义，可点击词语重试。'));
      if (row.chunk) card.append(node('p', row.chunk, 'lookup-chunk'));
      if (row.context) card.append(node('blockquote', row.context));
      card.append(node('p', `查询 ${row.count || 1} 次 · 最近 ${new Date(row.lastAt).toLocaleString('zh-CN')}`, 'lookup-muted'));
      const action = node('button', row.status === 'reviewed' ? '放回待复习' : '标记已复习', 'lookup-review'); action.type = 'button';
      action.addEventListener('click', () => { const all = history(); const r = all.find(x => x.key === row.key);
        if (r) { r.status = r.status === 'reviewed' ? 'pending' : 'reviewed'; r.reviewedAt = r.status === 'reviewed' ? new Date().toISOString() : null; save(all); }
      });
      card.append(action); list.append(card);
    }
    if (shown.length > 60) list.append(node('p', `显示最近 60 条；另有 ${shown.length - 60} 条，可用搜索查看。全部记录仍保存在备份中。`, 'lookup-muted'));
  }
  function entries(term) {
    const exact = glossary[normalize(term)]; if (exact) return {base:term, entries:exact};
    if (term.includes(' ')) return null;
    const t = normalize(term); const candidates = [];
    if (t.endsWith('ies')) candidates.push(t.slice(0,-3)+'y');
    if (t.endsWith('s') && !t.endsWith('ss')) candidates.push(t.slice(0,-1));
    if (t.endsWith('ed')) candidates.push(t.slice(0,-1),t.slice(0,-2));
    if (t.endsWith('ing')) candidates.push(t.slice(0,-3),t.slice(0,-3)+'e');
    for (const base of candidates) if (glossary[base]) return {base, entries:glossary[base]};
    return null;
  }
  function title(term) {
    result.replaceChildren(node('h3', term));
    const a = node('a', '查看完整词典 ↗', 'lookup-dictionary');
    a.href = 'https://dictionary.cambridge.org/dictionary/english-chinese-simplified/' + encodeURIComponent(term);
    a.target = '_blank'; a.rel = 'noopener noreferrer'; result.append(a);
  }
  function showLocal(term, match) {
    title(term);
    if (normalize(term) !== normalize(match.base)) result.append(node('p', `词形参考：${match.base}`, 'lookup-muted'));
    for (const e of match.entries.slice(0,3)) {
      const block = node('div', '', 'lookup-sense');
      block.append(node('p', (e.pos ? e.pos+' ' : '')+e.meaning));
      if (e.chunk) block.append(node('p', e.chunk, 'lookup-chunk'));
      if (e.example) block.append(node('p', e.example, 'lookup-example'));
      result.append(block);
    }
    
    const more = node('button', '补查在线释义', 'lookup-review'); more.type = 'button';
    more.addEventListener('click', () => online(term, current.context, serial, true)); result.append(more);
  }
  async function online(term, context, request, supplementary = false) {
    if (controller) controller.abort(); controller = new AbortController(); const ownController = controller;
    const status = node('p', '正在在线查询…', 'lookup-muted');
    if (!supplementary) title(term); result.append(status);
    const timeout = setTimeout(() => ownController.abort(), 9000);
    try {
      const url = 'https://api.mymemory.translated.net/get?q=' + encodeURIComponent(term) + '&langpair=en%7Czh-CN';
      const response = await fetch(url, {signal:ownController.signal, credentials:'omit', referrerPolicy:'no-referrer'});
      if (!response.ok) throw new Error('network');
      const data = await response.json();
      const translation = data?.responseData?.translatedText;
      if (Number(data.responseStatus) !== 200 || data.quotaFinished || typeof translation !== 'string' || !translation.trim() || normalize(translation) === normalize(term) || !/[\u3400-\u9fff]/.test(translation) || translation.length > 600) throw new Error('no-result');
      if (serial !== request) return;
      status.textContent = '中文释义';
      result.append(node('p', translation, 'lookup-translation'));
      if (supplementary) supplement(term, {onlineMeaning:translation});
      else supplement(term, {meaning:translation,source:'MyMemory 在线翻译参考',lookupState:'found'});
    } catch (e) {
      if (serial !== request) return;
      status.textContent = '在线查询暂不可用或暂无中文结果。查询已保留，可重试或打开完整词典。';
      const retry = node('button', '重新查询', 'lookup-review'); retry.type='button';
      retry.addEventListener('click', () => { status.remove(); retry.remove(); online(term, context, request, supplementary); }); result.append(retry);
    } finally { clearTimeout(timeout); }
  }
  function lookup(raw, context='', from=null) {
    const term = raw.trim().replace(/^[^A-Za-z]+|[^A-Za-z]+$/g, '').replace(/\s+/g,' ');
    if (!/^[A-Za-z][A-Za-z'’ -]{0,79}$/.test(term) || term.split(' ').length > 6) {
      popup.hidden=false; result.replaceChildren(node('p','请输入一个英文词或短词组（最多六个词）。')); return;
    }
    if (controller) controller.abort(); serial++; const request = serial;
    current={term,context}; openedFrom=from; popup.hidden=false; input.value=term;
    const match = entries(term); const cached = history().find(r => r.key === normalize(term) && r.meaning && r.lookupState === 'found');
    if (match) {
      showLocal(term,match); const e=match.entries[0]; remember(term,context,{meaning:e.meaning,chunk:e.chunk,source:e.source});
    } else if (cached) {
      title(term); result.append(node('p',cached.meaning,'lookup-translation'),node('p','上次查询','lookup-muted'));
      remember(term,context,cached);
      const refresh=node('button','更新在线释义','lookup-review');refresh.type='button';refresh.addEventListener('click',()=>online(term,context,serial,false));result.append(refresh);
    } else { remember(term,context,{source:'待在线查询'}); online(term,context,request); }
  }
  function close() { popup.hidden=true; serial++; if(controller)controller.abort(); }
  function contextOf(textNode, term) {
    const container = textNode.parentElement.closest('p,li,td,blockquote,h1,h2,h3,h4') || textNode.parentElement;
    const text = container.textContent.replace(/\s+/g,' ').trim(); const at=text.toLowerCase().indexOf(term.toLowerCase());
    const start=Math.max(0,at-70);return (start?'…':'')+text.slice(start,start+220)+(text.length>start+220?'…':'');
  }
  function clickedWord(e) {
    if (e.button !== 0 || e.ctrlKey || e.metaKey || e.altKey) return;
    const target = e.target instanceof Element ? e.target : null;
    if (!target || !target.closest('main') || target.closest('a,button,input,textarea,select,label,summary,nav,script,style,[contenteditable],#word-lookup,#lookup-learning')) return;
    const sel = window.getSelection();
    if (sel && !sel.isCollapsed) {
      const text=sel.toString().trim();
      if (/^[A-Za-z][A-Za-z'’ -]{0,79}$/.test(text) && text.split(/\s+/).length<=6 && target.contains(sel.anchorNode)) lookup(text,contextOf(sel.anchorNode,text));
      return;
    }
    let caret;
    if (document.caretPositionFromPoint) {const p=document.caretPositionFromPoint(e.clientX,e.clientY);if(p)caret={node:p.offsetNode,offset:p.offset};}
    else if (document.caretRangeFromPoint) {const r=document.caretRangeFromPoint(e.clientX,e.clientY);if(r)caret={node:r.startContainer,offset:r.startOffset};}
    if (!caret || caret.node.nodeType!==Node.TEXT_NODE || !target.contains(caret.node)) return;
    const text=caret.node.textContent;
    for (const m of text.matchAll(/[A-Za-z]+(?:['’\-][A-Za-z]+)*/g)) {
      if(caret.offset<m.index || caret.offset>m.index+m[0].length)continue;
      const range=document.createRange();range.setStart(caret.node,m.index);range.setEnd(caret.node,m.index+m[0].length);
      const hit=[...range.getClientRects()].some(r=>e.clientX>=r.left-1&&e.clientX<=r.right+1&&e.clientY>=r.top&&e.clientY<=r.bottom);
      if(hit)lookup(m[0],contextOf(caret.node,m[0]));return;
    }
  }
  document.addEventListener('click', e=>{if(!popup.hidden&&!popup.contains(e.target)&&!e.target.closest('#lookup-open'))close();clickedWord(e);});
  $('#lookup-open').addEventListener('click',e=>{openedFrom=e.currentTarget;popup.hidden=false;input.focus();});
  $('#lookup-close').addEventListener('click',()=>{close();openedFrom?.focus?.();});
  $('#lookup-form').addEventListener('submit',e=>{e.preventDefault();lookup(input.value,'',input);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!popup.hidden){close();openedFrom?.focus?.();}});
  window.addEventListener('hashchange',()=>{close();renderHistory();});
  $('#lookup-filter').addEventListener('input',renderHistory);
  $('#lookup-history-search').addEventListener('input',renderHistory);
  $('#lookup-export').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({format:'ielts-lookup-history',version:1,exportedAt:new Date().toISOString(),items:history()},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=node('a');a.href=url;a.download='IELTS-查词记录.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  renderHistory();
})();
