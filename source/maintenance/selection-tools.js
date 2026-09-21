(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const store = $('#sentence-store'), popup = $('#sentence-popup'), bar = $('#selection-toolbar');
  if (!store || !popup || !bar) return;
  const source = $('#sentence-source'), result = $('#sentence-result'), direction = $('#sentence-direction'), status = $('#sentence-status');
  let chosen = null, serial = 0, pending = null, origin = null, provenance = '手动译文', translated = null;
  const clean = s => String(s || '').replace(/\s+/g, ' ').trim();
  const wordLike = s => /^[A-Za-z][A-Za-z0-9'’ -]{0,79}$/.test(s) && s.split(/\s+/).length <= 6;
  const el = (tag, text, cls) => { const n = document.createElement(tag); n.textContent = text || ''; if (cls) n.className = cls; return n; };
  function rows() {
    try {
      const data = JSON.parse(store.value || '[]');
      if (!Array.isArray(data) || !data.every(x => x && typeof x.text === 'string' && typeof x.translation === 'string' && ['en|zh-CN','zh-CN|en'].includes(x.direction))) throw Error();
      return data;
    } catch { return null; }
  }
  function save(data) {
    if (rows() === null) { status.textContent = '句子记录格式异常，原始内容已保留。请先在学习记录中导出备份。'; return false; }
    const raw=JSON.stringify(data);
    if(raw.length>1500000){status.textContent='句子本内容较多，请先导出学习记录并整理已有收藏。';return false;}
    store.value = raw; store.dispatchEvent(new Event('input', {bubbles:true})); render();
    try {if(JSON.parse(localStorage.getItem('ielts-finished-book-v1'))?.fields?.['sentence-collection-v1']===raw)return true;}catch{}
    status.textContent='内容保留在当前页面，但未能写入浏览器。请先到学习记录导出文字作答，避免刷新丢失。';return false;
  }
  function render() {
    const list = $('#sentence-list'); list.replaceChildren(); const data = rows();
    if (!data) { $('#sentence-count').textContent = '句子记录格式异常，已保留原始内容，请先备份。'; return; }
    const q = clean($('#sentence-search').value).toLowerCase();
    const filtered = data.filter(x => (x.text + ' ' + x.translation).toLowerCase().includes(q));
    $('#sentence-count').textContent = `${data.length} 个收藏句子 · 与学习记录一起备份`;
    if (!filtered.length) list.append(el('p', q ? '没有匹配的句子。' : '选中一句有用的表达，翻译后收藏到这里。', 'st-muted'));
    for (const row of filtered.slice(0,60)) {
      const card = el('article', '', 'st-sentence');
      card.append(el('blockquote', row.text), el('p', row.translation));
      card.append(el('p', `${row.direction === 'en|zh-CN' ? '英 → 中' : '中 → 英'} · ${row.provenance || '收藏译文'}${row.title ? ' · '+row.title : ''}`, 'st-muted'));
      const actions = el('div', '', 'st-actions'), edit = el('button','查看 / 修改'), remove = el('button','取消收藏');
      edit.type = remove.type = 'button';
      edit.onclick = () => { open(row.text, edit, row); };
      remove.onclick = () => save((rows() || []).filter(x => !(x.text === row.text && x.direction === row.direction)));
      actions.append(edit,remove);card.append(actions);list.append(card);
    }
    if(filtered.length > 60) list.append(el('p','显示前 60 条，可搜索其余收藏。','st-muted'));
  }
  function updateExternal() {
    const [from,to] = direction.value.split('|');
    $('#sentence-bing').href = 'https://www.bing.com/translator?from='+encodeURIComponent(from)+'&to='+encodeURIComponent(to)+'&text='+encodeURIComponent(source.value);
  }
  function cancel() { serial++; pending?.abort(); pending=null; $('#sentence-translate').disabled=false; }
  function open(text='', from=null, saved=null) {
    cancel(); bar.hidden=true; const lookup=$('#word-lookup'); if(lookup)lookup.hidden=true;
    popup.hidden=false;origin=from;source.value=text;result.value=saved?.translation || '';
    direction.value=saved?.direction || (/[\u3400-\u9fff]/.test(text) ? 'zh-CN|en' : 'en|zh-CN');
    provenance=saved?.provenance || '手动译文'; translated=saved ? {text:saved.text,direction:saved.direction,translation:saved.translation} : null;
    status.textContent='';updateExternal();source.focus();
  }
  function close() { cancel();popup.hidden=true;origin?.focus?.(); }
  function decode(text) { const doc = new DOMParser().parseFromString(text, 'text/html'); return doc.body.textContent || ''; }
  async function translate() {
    cancel(); const text = clean(source.value), pair = direction.value;
    if (!text) {status.textContent='先选中或输入一句话。';return;}
    if (new TextEncoder().encode(text).length > 500) {status.textContent='选中的内容较长。请缩短为一句话，或用下方的必应翻译打开完整内容。';return;}
    const cached=(rows() || []).find(x=>x.text===text&&x.direction===pair);
    if(cached){result.value=cached.translation;provenance=cached.provenance;translated={text,direction:pair,translation:cached.translation};status.textContent='已取回收藏的译文，无需联网。';return;}
    const local=localPairs.find(x => pair==='en|zh-CN' ? clean(x.en)===text : clean(x.zh)===text);
    if(local){result.value=pair==='en|zh-CN'?local.zh:local.en;provenance='本册配套译文';translated={text,direction:pair,translation:result.value};status.textContent='已找到本册配套译文，无需联网。';return;}
    const ticket = serial, controller = new AbortController();pending=controller;
    const timeout = setTimeout(()=>controller.abort(),18000);
    $('#sentence-translate').disabled=true; status.textContent='正在翻译选中的句子…';
    try {
      const url='https://api.mymemory.translated.net/get?q='+encodeURIComponent(text)+'&langpair='+encodeURIComponent(pair);
      const response=await fetch(url,{signal:controller.signal,credentials:'omit',referrerPolicy:'no-referrer'});
      if(!response.ok)throw Error('network');
      const data=await response.json();
      if(ticket!==serial)return;
      if(data.quotaFinished || Number(data.responseStatus)===429 || /NEXT AVAILABLE IN|USED ALL AVAILABLE FREE/i.test(data.responseData?.translatedText || ''))throw Error('quota');
      if(Number(data.responseStatus)!==200 || typeof data.responseData?.translatedText!=='string' || !data.responseData.translatedText.trim())throw Error('empty');
      result.value=decode(data.responseData.translatedText);provenance='MyMemory 在线译文';translated={text,direction:pair,translation:result.value};
      status.textContent='译文已就绪。可以修改，再收藏。';
    } catch(error) {
      if(ticket!==serial)return;
      status.textContent=error.message==='quota' ? '翻译服务今日额度已用完。可以使用下方的必应翻译，或输入自己的译文。' : '暂时无法连接翻译服务。请重试，或使用下方的必应翻译。';
    } finally {clearTimeout(timeout);if(ticket===serial){pending=null;$('#sentence-translate').disabled=false;}}
  }
  function capture() {
    if(!popup.hidden)return;
    const active=document.activeElement;let text='',container=null,rect=null;
    if(active?.matches('textarea:not([hidden]),input[type="text"]') && active.closest('main') && active.selectionEnd>active.selectionStart){
      text=active.value.slice(active.selectionStart,active.selectionEnd);container=active;rect=active.getBoundingClientRect();
    } else {
      const selection=window.getSelection();
      if(!selection || selection.isCollapsed || !selection.rangeCount){bar.hidden=true;return;}
      const range=selection.getRangeAt(0);container=range.commonAncestorContainer.nodeType===1?range.commonAncestorContainer:range.commonAncestorContainer.parentElement;
      if(!container?.closest('main') || container.closest('button,nav,script,style,#sentence-learning,#vocabulary-review,#lookup-history-list')){bar.hidden=true;return;}
      text=selection.toString();rect=range.getBoundingClientRect();
    }
    text=clean(text);if(!text || text.length>3000 || !rect || rect.bottom<0 || rect.top>window.innerHeight){bar.hidden=true;return;}
    const context=clean((container.closest('p,li,td,blockquote') || container).textContent || text).slice(0,700);
    chosen={text,context,from:container};$('#selection-preview').textContent=text;
    $('#selection-lookup').hidden=$('#selection-collect').hidden=!wordLike(text);
    $('#selection-collect').textContent='☆ 收藏单词';$('#selection-collect').disabled=false;
    bar.hidden=false;bar.style.left=Math.max(12,Math.min(rect.left,window.innerWidth-bar.offsetWidth-12))+'px';
    bar.style.top=Math.max(12,Math.min(rect.bottom+9,window.innerHeight-bar.offsetHeight-12))+'px';
  }
  bar.addEventListener('pointerdown',e=>e.preventDefault());
  document.addEventListener('pointerup',e=>{if(!bar.contains(e.target)&&!popup.contains(e.target))setTimeout(capture,0);});
  document.addEventListener('keyup',e=>{if(e.key==='Shift'||e.key.startsWith('Arrow'))capture();});
  document.addEventListener('selectionchange',()=>{if(!window.getSelection()?.isCollapsed && !bar.contains(document.activeElement))return;if(!document.activeElement?.matches('textarea,input'))bar.hidden=true;});
  $('#selection-lookup').onclick=()=>{if(chosen){bar.hidden=true;window.IELTSLookup?.open(chosen.text,chosen.context,$('#selection-lookup'));}};
  $('#selection-collect').onclick=async()=>{if(!chosen)return;const b=$('#selection-collect');b.disabled=true;try{if(!window.IELTSLookup?.collect)throw Error('unavailable');const answer=await window.IELTSLookup.collect(chosen.text,chosen.context,b);b.textContent=!answer?.ok?'未能收藏，请查看查词提示':window.IELTSLookup.isPersisted()?'✓ 已收藏':'本页已收藏，请导出保留';}catch{b.textContent='请通过查词窗口收藏';}finally{b.disabled=false;}};
  $('#selection-translate').onclick=()=>{if(chosen){const selection=chosen;open(selection.text,selection.from);translate();}};
  $('#selection-dismiss').onclick=()=>{bar.hidden=true;};
  $('#sentence-close').onclick=close;$('#sentence-translate').onclick=translate;
  $('#sentence-notebook-link').onclick=close;
  document.querySelectorAll('[data-open-sentence]').forEach(b=>b.addEventListener('click',()=>open('',b)));
  for(const input of [source,direction])input.addEventListener('input',()=>{cancel();translated=null;result.value='';status.textContent='';provenance='手动译文';updateExternal();});
  result.addEventListener('input',()=>{if(pending){cancel();status.textContent='已停止在线翻译，保留你正在填写的译文。';}});
  $('#sentence-save').onclick=()=>{
    const text=clean(source.value), translation=result.value.trim(), pair=direction.value;
    if(!text||!translation){status.textContent='原句和译文都填写后即可收藏。';return;}
    const data=rows();if(!data){save([]);return;}
    const old=data.find(x=>x.text===text&&x.direction===pair);
    if(!old&&data.length>=1000){status.textContent='句子本已有 1000 条，请先备份并整理已有收藏。';return;}
    if(text.length>3000||translation.length>6000){status.textContent='请缩短为一个句子再收藏。';return;}
    const row={...old,text,translation,direction:pair,provenance:translated?.translation===translation?provenance:'手动修订译文',title:chosen?.text===text?clean(chosen.from?.closest('.panel')?.querySelector('h1,h2')?.textContent):old?.title||'',createdAt:old?.createdAt||new Date().toISOString(),updatedAt:new Date().toISOString()};
    if(save([row,...data.filter(x=>!(x.text===text&&x.direction===pair))]))status.textContent='已收藏到句子本。';
  };
  $('#sentence-search').addEventListener('input',render);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){bar.hidden=true;if(!popup.hidden)close();}});
  window.addEventListener('hashchange',()=>{bar.hidden=true;close();render();});
  window.addEventListener('resize',()=>{bar.hidden=true;});
  let scrollTimer;
  window.addEventListener('scroll',()=>{bar.hidden=true;clearTimeout(scrollTimer);if(popup.hidden)scrollTimer=setTimeout(capture,120);},true);
  let localPairs=[];try{localPairs=JSON.parse($('#sentence-local-pairs')?.textContent || '[]');}catch{}
  window.IELTSSentences={open,translate,render};render();
})();
