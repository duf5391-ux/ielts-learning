(() => {
  'use strict';
  const node = (tag, text, cls) => {
    const el = document.createElement(tag);
    if (text) el.textContent = text;
    if (cls) el.className = cls;
    return el;
  };
  function renderEntries(container, found) {
    const words = [...new Set(found.entries.map(e => e.word))];
    if (found.bases?.length) container.append(node('p', '词形对应：' + found.bases.join(' / '), 'dictionary-meta'));
    for (const entry of found.entries) {
      const article = node('article', '', 'dictionary-entry');
      article.append(node('h4', entry.word));
      const meta = [entry.phonetic ? '/' + entry.phonetic.replace(/^\/+|\/+$/g, '') + '/' : '', entry.pos].filter(Boolean).join(' · ');
      if (meta) article.append(node('p', meta, 'dictionary-meta'));
      if (entry.translation) article.append(node('p', entry.translation.replace(/\\n/g, '\n'), 'dictionary-meaning'));
      if (entry.definition) {
        if (entry.translation) {
          const details = node('details'); details.append(node('summary', '英文释义'), node('p', entry.definition.replace(/\\n/g, '\n'), 'dictionary-meaning')); article.append(details);
        } else article.append(node('p', entry.definition.replace(/\\n/g, '\n'), 'dictionary-meaning'));
      }
      if (entry.exchange) {
        const labels = {p:'过去式',d:'过去分词',i:'现在分词',3:'第三人称单数',r:'比较级',t:'最高级',s:'复数',0:'原形'};
        const forms = entry.exchange.split('/').map(part => {
          const at = part.indexOf(':'); return at > 0 && labels[part.slice(0, at)] ? labels[part.slice(0, at)] + ' ' + part.slice(at + 1) : '';
        }).filter(Boolean);
        if (forms.length) article.append(node('p', forms.join('；'), 'dictionary-meta'));
      }
      container.append(article);
    }
    return words;
  }
  function appendOnlineOption(container, term) {
    const details = node('details', '', 'dictionary-online');
    const a = node('a', '打开 Cambridge 在线词典 ↗');
    a.href = 'https://dictionary.cambridge.org/dictionary/english-chinese-simplified/' + encodeURIComponent(term);
    a.target = '_blank'; a.rel = 'noopener noreferrer';
    details.append(node('summary', '在线词典（可选）'), a); container.append(details);
  }
  window.IELTSDictionaryUI = {renderEntries, appendOnlineOption};
  let serial = 0;
  const form = document.querySelector('#dictionary-form');
  if (!form) return;
  const input = document.querySelector('#dictionary-input'), result = document.querySelector('#dictionary-result');
  async function search(term) {
    const request = ++serial;
    term = term.trim(); input.value = term;
    if (!term || term.length > 80) { result.replaceChildren(node('p', '请输入英文单词或短词组。')); return; }
    result.replaceChildren(node('p', '正在读取本地词典…'));
    try {
      const found = await window.IELTSLocalDictionary.lookup(term);
      if (request !== serial) return;
      result.replaceChildren(node('h2', term));
      if (found.entries.length) renderEntries(result, found);
      else result.append(node('p', '本地词典未收录这个词或完整词组。请检查拼写，或分开查其中的词。'));
      appendOnlineOption(result, term);
    } catch {
      if (request !== serial) return;
      result.replaceChildren(node('p', '本地词典文件未能读取。请保留页面旁的 local-dictionary 文件夹，再重试。'));
      const retry = node('button', '重试本地查询'); retry.type = 'button'; retry.onclick = () => search(term); result.append(retry);
    }
  }
  form.addEventListener('submit', event => { event.preventDefault(); search(input.value); });
  const term = new URLSearchParams(location.search).get('word');
  if (term) search(term);
})();
