(() => {
  const routes=['vocabulary-review','word-review','sentence-learning','lookup-learning','review-history','word-library'];
  const tabs=[['vocabulary-review','背单词'],['word-review','复习'],['sentence-learning','句子'],['lookup-learning','查词与历史']];
  for(const id of routes){
    const panel=document.getElementById(id);if(!panel)continue;
    const nav=document.createElement('nav');nav.className='word-tool-links ui-word-tabs';nav.setAttribute('aria-label','单词栏目');
    for(const [route,label] of tabs){const a=document.createElement('a');a.href='#'+route;a.textContent=label;
      if(route===id||route==='lookup-learning'&&['review-history','word-library'].includes(id))a.setAttribute('aria-current','page');nav.append(a)}
    panel.prepend(nav);
    if(['lookup-learning','review-history','word-library'].includes(id)){
      const links=document.createElement('nav');links.className='ui-history-tabs';links.setAttribute('aria-label','单词记录');
      for(const [route,label] of [['lookup-learning','查词记录'],['review-history','学习记录'],['word-library','已收录词语']]){const a=document.createElement('a');a.href='#'+route;a.textContent=label;if(route===id)a.setAttribute('aria-current','page');links.append(a)}nav.after(links);
    }
  }
  const review=document.getElementById('word-review'),subtitle=document.createElement('p');subtitle.className='ui-subtitle';subtitle.textContent='查过、学过的词，按进度接着复习。';review.querySelector('header').after(subtitle);
  const history=document.createElement('a');history.href='#review-history';history.className='ui-review-history-link';history.textContent='查看学习与拼写记录 →';review.querySelector('#vr-stats').after(history);
  const quick=document.createElement('button');quick.type='button';quick.id='ui-spelling-check';quick.className='ui-diagnostic-link';quick.textContent='拼写自测  →';quick.addEventListener('click',()=>{document.getElementById('vr-mode').value='spelling';document.getElementById('vr-practice-all').click()});review.querySelector('.vr-controls').after(quick);
  function update(){quick.disabled=document.getElementById('vr-practice-all').disabled;}
  window.addEventListener('ielts-lookup-changed',update);document.addEventListener('ielts-record-restored',update);update();
  document.getElementById('ui-query-word').addEventListener('click',()=>document.getElementById('lookup-open').click());
})();
