(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const field = $('#lookup-history-store');
  const glossary = JSON.parse($('#lookup-glossary').textContent);
  const popup = $('#word-lookup');
  const result = $('#lookup-result');
  const input = $('#lookup-input');
  if (!field || !popup || !result || !input) return;
  let serial = 0, openedFrom = null, activeTerm = '', lastPersisted = true;
  const normalize = t => t.trim().toLowerCase().replace(/[’]/g, "'").replace(/\s+/g, ' ');
  function node(tag, text, cls) {
    const el = document.createElement(tag); if (text) el.textContent = text;
    if (cls) el.className = cls; return el;
  }
  const keyOf = row => normalize(row.key || row.term);
  function readRows() {
    const rows = JSON.parse(field.value || '[]');
    if (!Array.isArray(rows) || rows.some(r => !r || typeof r.term !== 'string')) throw Error('查词记录格式无法读取，已保留原始记录。请先备份学习记录，再恢复有效备份。');
    return rows;
  }
  function history() { try { return readRows(); } catch { return []; } }
  function save(rows, options = {}) {
    readRows(); // Never overwrite malformed stored data with an empty list.
    const next = JSON.stringify(rows);
    if (options.requirePersistence) {
      lastPersisted = window.IELTSRecordStore?.commit({[field.dataset.save]:next,...options.additionalFields}) === true;
    } else {
      field.value = next; field.dispatchEvent(new Event('input', {bubbles:true}));
      try { lastPersisted = JSON.parse(localStorage.getItem('ielts-finished-book-v1') || '{}').fields?.[field.dataset.save] === field.value; } catch { lastPersisted = false; }
    }
    renderHistory(); refreshFavorite(); window.dispatchEvent(new CustomEvent('ielts-lookup-changed'));
    let warning=$('#lookup-save-warning');
    if(!warning){warning=node('p','','lookup-muted');warning.id='lookup-save-warning';warning.setAttribute('role','status');field.before(warning);}
    warning.textContent=lastPersisted?'':options.requirePersistence?'本次标记未保存，原来的记录保持不变。请处理页面保存提示后重试。':'本次修改仅留在当前页面，尚未保存到浏览器。请先“导出查词记录”保留，再刷新。';
    let popupWarning=$('#lookup-popup-save-warning');
    if(!popupWarning){popupWarning=node('p','','lookup-muted');popupWarning.id='lookup-popup-save-warning';popupWarning.setAttribute('role','status');popup.append(popupWarning);}
    popupWarning.textContent=warning.textContent;
    return !options.requirePersistence || lastPersisted;
  }
  function updateEntry(term, patch, options = {}) {
    const rows = readRows(), row = rows.find(r => keyOf(r) === normalize(term));
    if (!row) return null;
    Object.assign(row, typeof patch === 'function' ? patch({...row}) : patch);
    return save(rows, options) ? row : null;
  }
  function setFavorite(term, value = true) {
    const additionalFields = {};
    for (const card of topicCards) if (card.key === normalize(term)) additionalFields[card.field.dataset.save] = !!value;
    return updateEntry(term, row => ({favorite:!!value, favoriteAt:value ? (row.favoriteAt || new Date().toISOString()) : row.favoriteAt}), {requirePersistence:true,additionalFields});
  }
  const topicCards = [...document.querySelectorAll('.tv-card')].map(card => {
    const term = card.querySelector('[data-local-dictionary]')?.dataset.localDictionary;
    return {card,term,key:term?normalize(term):'',field:card.querySelector('input[data-save^="topic-vocab-star-"]')};
  }).filter(x=>x.term&&x.field);
  function collectTopic(card, favorite) {
    const rows=readRows(), old=rows.find(r=>keyOf(r)===card.key), now=new Date().toISOString();
    const row={...old,key:card.key,term:card.term,favorite:!!favorite,favoriteAt:old?.favoriteAt||now,firstAt:old?.firstAt||now,lastAt:old?.lastAt||now,lookupVersion:2,count:old?.count||0,
      meaning:old?.meaning||card.card.querySelector('.tv-meaning')?.textContent.trim()||'',chunk:old?.chunk||card.card.querySelector('.tv-chunk [lang="en"]')?.textContent.trim()||'',source:old?.source||'话题词卡',sourceRoute:old?.sourceRoute||'topical-vocabulary',topicCardId:old?.topicCardId||card.card.dataset.tvId};
    const additionalFields=Object.fromEntries(topicCards.filter(x=>x.key===card.key).map(x=>[x.field.dataset.save,!!favorite]));
    const ok=save([row,...rows.filter(r=>keyOf(r)!==card.key)],{requirePersistence:true,additionalFields});
    if(!ok)card.field.checked=!!old?.favorite;
    return ok;
  }
  // The existing checkbox keeps its saved key. Commit its change with the word list.
  document.addEventListener('input',event=>{
    const card=topicCards.find(x=>x.field===event.target);if(!card)return;
    event.stopImmediatePropagation();
    try{collectTopic(card,card.field.checked);}catch(error){card.field.checked=!card.field.checked;const notice=document.querySelector('.vq-notice');if(notice)notice.textContent=error.message;}
  },true);
  function refreshFavorite() {
    const button = $('#lookup-favorite'); if (!button) return;
    const row = history().find(r => keyOf(r) === normalize(activeTerm));
    button.disabled = !row; button.textContent = row?.favorite ? '★ 已收藏 · 取消收藏' : '☆ 收藏到单词表';
    button.setAttribute('aria-pressed', String(!!row?.favorite));
  }
  function remember(term, context, data) {
    const rows = readRows(); const key = normalize(term); const index = rows.findIndex(r => keyOf(r) === key), old = rows[index];
    const now = new Date().toISOString();
    const entry = {...old, key, term, lookupVersion:2, legacyReviewMark:old?.legacyReviewMark ?? (old && !old.lookupVersion ? old.status : null), firstAt:old?.firstAt || now, lastAt:now,
      count:(Number(old?.count) || 0) + 1, status:old?.status || 'pending', context:context || old?.context || '',
      meaning:data.meaning || old?.meaning || '', chunk:data.chunk || old?.chunk || '',
      example:data.example || old?.example || '', source:data.source || old?.source || '', lookupState:data.meaning || old?.meaning ? 'found' : 'unresolved',
      lookups:[...(Array.isArray(old?.lookups) ? old.lookups : (old ? [{at:old.lastAt || old.firstAt || now,context:old.context || '',legacy:true}] : [])),{at:now,context:context || ''}]};
    save([entry, ...rows.filter((_, i) => i !== index)]);
  }
  function supplement(term, data) {
    const rows = readRows(); const row = rows.find(r => keyOf(r) === normalize(term));
    if (row) { Object.assign(row, data); save(rows); }
  }
  function renderHistory() {
    let rows;
    try { rows = readRows(); } catch (error) { $('#lookup-history-count').textContent = error.message; return; }
    const filter = $('#lookup-filter').value;
    const q = normalize($('#lookup-history-search').value);
    const shown = rows.filter(r => (filter === 'all' || (filter === 'favorite' ? r.favorite : r.status === filter)) &&
      normalize([r.term,r.meaning,r.context].join(' ')).includes(q));
    $('#lookup-history-count').textContent = `${rows.length} 个查询词或词组 · ${rows.filter(r => r.favorite).length} 个已收藏`;
    const list = $('#lookup-history-list'); list.replaceChildren();
    if (!shown.length) { list.append(node('p', rows.length ? '没有匹配的记录。' : '点击正文中的英文词，释义和原句会自动留在这里。', 'lookup-muted')); return; }
    for (const row of shown.slice(0, 60)) {
      const card = node('article', '', 'lookup-record');
      const head = node('div', '', 'lookup-record-head');
      const reopen = node('button', row.term, 'lookup-term'); reopen.type = 'button';
      reopen.addEventListener('click', event => { event.stopPropagation(); lookup(row.term, row.context, reopen); });
      head.append(reopen, node('span', row.favorite ? '已收藏' : '查询记录', 'lookup-tag'));
      card.append(head, node('p', row.meaning || '暂未查到释义，可点击词语重试。'));
      if (row.chunk) card.append(node('p', row.chunk, 'lookup-chunk'));
      if (row.context) card.append(node('blockquote', row.context));
      card.append(node('p', row.count===0?'从话题词卡收藏':`查询 ${row.count || 1} 次 · 最近 ${new Date(row.lastAt).toLocaleString('zh-CN')}`, 'lookup-muted'));
      const favorite = node('button', row.favorite ? '取消收藏' : '☆ 收藏到单词表', 'lookup-review'); favorite.type = 'button';
      favorite.setAttribute('aria-pressed', String(!!row.favorite)); favorite.addEventListener('click', () => setFavorite(row.term, !row.favorite)); card.append(favorite);
      const action = node('button', row.status === 'reviewed' ? '旧标记：已复习 → 待复习' : '旧标记：待复习 → 已复习', 'lookup-review'); action.type = 'button';
      action.addEventListener('click', () => { const all = readRows(); const r = all.find(x => keyOf(x) === keyOf(row));
        if (r) { r.status = r.status === 'reviewed' ? 'pending' : 'reviewed'; r.reviewedAt = r.status === 'reviewed' ? new Date().toISOString() : null; save(all); }
      });
      card.append(action); list.append(card);
    }
    if (shown.length > 60) list.append(node('p', `显示最近 60 条；另有 ${shown.length - 60} 条，可用搜索查看。全部记录仍保存在备份中。`, 'lookup-muted'));
  }
  function entries(term, bases=[]) {
    for (const base of [term, ...bases]) {
      const found = glossary[normalize(base)];
      if (found) return {base, entries:found};
    }
    return null;
  }
  function title(term) {
    result.replaceChildren(node('h3', term));
    const actions=node('div','','lookup-favorite-actions'), favorite=node('button','☆ 收藏到单词表','lookup-review');
    favorite.type='button'; favorite.id='lookup-favorite'; favorite.addEventListener('click',()=>{
      try { setFavorite(term, !history().find(r=>keyOf(r)===normalize(term))?.favorite); }
      catch(error) { result.append(node('p',error.message,'lookup-muted')); }
    });
    const link=node('a','去单词表复习 →'); link.href='#vocabulary-review'; link.addEventListener('click',close);
    actions.append(favorite,link); result.append(actions); refreshFavorite();
  }
  function showCourse(match) {
    if (!match) return;
    result.append(node('h4', '本页用法'));
    if (normalize(input.value) !== normalize(match.base)) result.append(node('p', `对应词条：${match.base}`, 'lookup-muted'));
    for (const e of match.entries.slice(0,3)) {
      const block = node('div', '', 'lookup-sense');
      block.append(node('p', (e.pos ? e.pos+' ' : '')+e.meaning));
      if (e.chunk) block.append(node('p', e.chunk, 'lookup-chunk'));
      if (e.example) block.append(node('p', e.example, 'lookup-example'));
      result.append(block);
    }
  }
  async function lookup(raw, context='', from=null) {
    const request = ++serial;
    const term = raw.trim().replace(/^["“”‘’.,!?;:()[\]{}]+|["“”‘’.,!?;:()[\]{}]+$/g, '').replace(/\s+/g,' ');
    popup.hidden=false; openedFrom=from;
    if (!/^[A-Za-z][A-Za-z0-9'’ -]{0,79}$/.test(term) || term.split(' ').length > 6) {
      result.replaceChildren(node('p','请输入一个英文词或短词组（最多六个词）。')); return {ok:false};
    }
    input.value=term; activeTerm=term;
    let match=entries(term);
    const cached=history().find(r => keyOf(r)===normalize(term) && r.meaning && r.lookupState==='found');
    title(term); showCourse(match);
    const loading=node('p','正在读取本地词典…','lookup-muted'); result.append(loading);
    try { remember(term,context,match ? match.entries[0] : (cached || {source:'本地词典'})); }
    catch(error) { loading.textContent=error.message; return {ok:false,error:error.message}; }
    try {
      if (!window.IELTSLocalDictionary || !window.IELTSDictionaryUI) throw new Error('dictionary unavailable');
      const found=await window.IELTSLocalDictionary.lookup(term);
      const priorMatch=match;
      if (!match) match=entries(term,found.bases);
      const e=match?.entries[0], d=found.entries[0];
      if (e || d) supplement(term,{meaning:e?.meaning || d.translation || d.definition,chunk:e?.chunk || cached?.chunk || '',example:e?.example || cached?.example || '',source:e?.source || 'ECDICT 本地英汉词典',lookupState:'found',dictionaryWord:d?.word || '',phonetic:d?.phonetic || cached?.phonetic || ''});
      if (serial!==request) return {ok:true,term,key:normalize(term)};
      loading.remove();
      if (!priorMatch && match) showCourse(match);
      if (found.entries.length) {
        result.append(node('h4','本地英汉词典'));
        window.IELTSDictionaryUI.renderEntries(result,found);
      } else result.append(node('p',match?'本地词典暂未收录这个完整词组；上方可查看本页用法。':'本地词典未收录这个词或完整词组。可以检查拼写，或分开查其中的词。','lookup-muted'));
      if (!e && !d && cached) result.append(node('h4','上次保存的释义'),node('p',cached.meaning),node('p','保留原有记录，本次本地词典未命中。','lookup-muted'));
      window.IELTSDictionaryUI.appendOnlineOption(result,term);
    } catch (error) {
      if (serial!==request) return {ok:true,term,key:normalize(term)};
      loading.textContent='本地词典文件未能读取。请保留学习册旁的 local-dictionary 文件夹，再重试。';
      if (cached && !match) result.append(node('p',cached.meaning),node('p','上次保存的释义','lookup-muted'));
      const retry=node('button','重试本地查询','lookup-review'); retry.type='button';
      retry.addEventListener('click',event=>{event.stopPropagation();lookup(term,context,from);});result.append(retry);
    }
    return {ok:true,term,key:normalize(term),row:history().find(r=>keyOf(r)===normalize(term))};
  }
  function close() { popup.hidden=true; serial++; }
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
    if (sel && !sel.isCollapsed) return; // Selection actions are offered by selection-tools.js.
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
  document.addEventListener('click', e=>{const local=e.target.closest('a[data-local-dictionary]');if(local){e.preventDefault();lookup(local.dataset.localDictionary,'',local);return;}if(!popup.hidden&&!popup.contains(e.target)&&!e.target.closest('#lookup-open,[data-open-local-lookup]')&&!openedFrom?.contains?.(e.target))close();clickedWord(e);});
  document.querySelectorAll('[data-open-local-lookup]').forEach(b=>b.addEventListener('click',()=>{openedFrom=b;popup.hidden=false;input.focus();}));
  $('#lookup-open').addEventListener('click',e=>{openedFrom=e.currentTarget;popup.hidden=false;input.focus();});
  $('#lookup-close').addEventListener('click',()=>{close();openedFrom?.focus?.();});
  $('#lookup-form').addEventListener('submit',e=>{e.preventDefault();lookup(input.value,'',input);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!popup.hidden){close();openedFrom?.focus?.();}});
  window.addEventListener('hashchange',()=>{close();renderHistory();});
  $('#lookup-filter').addEventListener('input',renderHistory);
  $('#lookup-history-search').addEventListener('input',renderHistory);
  $('#lookup-export').addEventListener('click',()=>{
    let data; try { data=JSON.stringify({format:'ielts-lookup-history',version:2,exportedAt:new Date().toISOString(),items:readRows()},null,2); } catch { data=field.value; }
    const blob=new Blob([data],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=node('a');a.href=url;a.download='IELTS-查词记录.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const favoriteOption = node('option','已收藏'); favoriteOption.value='favorite'; $('#lookup-filter').append(favoriteOption); $('#lookup-filter').value='all';
  window.IELTSLookup = Object.freeze({
    open:lookup, close, normalize, getHistory:history, updateEntry, setFavorite, isPersisted:()=>lastPersisted,
    collect:async(term,context='',from=null)=>{
      const pending=lookup(term,context,from);
      // Lookup creates the history item synchronously before its dictionary read.
      if (activeTerm && normalize(activeTerm)===normalize(term.trim().replace(/^["“”‘’.,!?;:()[\]{}]+|["“”‘’.,!?;:()[\]{}]+$/g,''))) {
        try { setFavorite(activeTerm,true); } catch(error) { return {ok:false,error:error.message}; }
      }
      const status=await pending; if(!status?.ok)return status;
      return {...status,row:setFavorite(status.term,true)};
    }
  });
  // Bring old checked topic cards into the same list once; cancellation also clears those checks.
  try {
    const rows=readRows(), additions=new Map();
    for(const card of topicCards.filter(x=>x.field.checked)) {
      const old=rows.find(r=>keyOf(r)===card.key);if(old?.favorite)continue;
      const now=new Date().toISOString();
      additions.set(card.key,{...old,key:card.key,term:card.term,favorite:true,favoriteAt:old?.favoriteAt||now,firstAt:old?.firstAt||now,lastAt:old?.lastAt||now,count:old?.count||0,lookupVersion:2,meaning:old?.meaning||card.card.querySelector('.tv-meaning')?.textContent.trim()||'',chunk:old?.chunk||card.card.querySelector('.tv-chunk [lang="en"]')?.textContent.trim()||'',source:old?.source||'话题词卡',sourceRoute:'topical-vocabulary',topicCardId:card.card.dataset.tvId});
    }
    if(additions.size)save([...additions.values(),...rows.filter(r=>!additions.has(keyOf(r)))],{requirePersistence:true});
  }catch(error){$('#lookup-history-count').textContent=error.message;}
  renderHistory();
})();
