(() => {
  'use strict';
  const $=s=>document.querySelector(s), root=$('#ui-review-history');if(!root)return;
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  const stats=el('div','','ui-history-summary'),filters=el('div','','ui-history-filters'),search=el('input'),mode=el('select'),list=el('div');
  search.type='search';search.id='ui-history-search';search.placeholder='搜索学过、查过的词';search.setAttribute('aria-label','搜索学习记录');mode.id='ui-history-mode';mode.setAttribute('aria-label','记录类型');
  for(const [value,label] of [['all','全部学习记录'],['study','背词'],['recall','回忆复习'],['spelling','拼写练习']]){const o=el('option',label);o.value=value;mode.append(o)}filters.append(search,mode);root.append(stats,filters,list);
  const gradeNames={forgot:'不会',hard:'模糊',known:'会'};let limit=40;
  function render(){let rows;try{rows=JSON.parse($('#lookup-history-store').value||'[]');if(!Array.isArray(rows))throw Error()}catch{list.replaceChildren(el('p','记录暂时无法读取，原记录已保留，请先导出备份。'));return;}
    const events=[];for(const row of rows){for(const event of row.learningEvents||[])events.push({...event,term:row.term,mode:'study'});for(const event of row.reviews||[])events.push({...event,term:row.term,mode:event.mode||'recall'});}
    events.sort((a,b)=>(Date.parse(b.at)||0)-(Date.parse(a.at)||0));stats.replaceChildren();
    const spelling=events.filter(x=>x.mode==='spelling'&&typeof x.spellingCorrect==='boolean'),correct=spelling.filter(x=>x.spellingCorrect&&x.independentAttempt===true).length;
    for(const [value,label] of [[events.length,'逐词作答记录'],[new Set(events.map(x=>x.term)).size,'涉及词语'],[spelling.length?correct+' / '+spelling.length:'—','独立拼对 / 拼写作答']]){const n=el('div','','ui-history-stat');n.append(el('strong',String(value)),el('span',label));stats.append(n)}
    const query=search.value.trim().toLowerCase(),found=events.filter(x=>(mode.value==='all'||x.mode===mode.value)&&String(x.term).toLowerCase().includes(query));list.replaceChildren();
    if(!found.length){const empty=el('div','','ui-history-empty');empty.append(el('h2',events.length?'没有匹配的记录':'下一次练习，就从这里接续'),el('p',events.length?'换个关键词或记录类型试试。':'背词、回忆和拼写的真实作答会保存在这里。旧记录没有日期时，不会补造一条历史。'));const a=el('a','开始背单词 →');a.href='#vocabulary-review';empty.append(a);list.append(empty);return;}
    for(const e of found.slice(0,limit)){const n=el('article','','ui-history-row'),content=el('div');content.append(el('h3',e.term));const time=Number.isFinite(Date.parse(e.at))?new Date(e.at).toLocaleString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'日期未记录';
      content.append(el('p',time+' · '+({study:'背单词',spelling:'拼写练习',recall:'回忆复习'}[e.mode]||'复习')+(e.practice?' · 加练':'')+(e.answerRevealed&&e.independentAttempt!==true?' · 核对或查看过答案':'')));
      if(e.mode==='spelling'&&e.answer)content.append(el('p','当时输入：'+e.answer));
      const result=el('span',e.mode==='spelling'?(e.spellingCorrect?'拼写一致':'需再练'):(gradeNames[e.grade]||'已记录'),'ui-history-result');result.dataset.grade=e.grade||'';n.append(content,result);list.append(n);}
    if(found.length>limit){const more=el('button','再看 40 条');more.type='button';more.addEventListener('click',()=>{limit+=40;render()});list.append(more)}
  }
  search.addEventListener('input',()=>{limit=40;render()});mode.addEventListener('change',()=>{limit=40;render()});window.addEventListener('hashchange',()=>{if(location.hash==='#review-history')render()});window.addEventListener('ielts-lookup-changed',render);document.addEventListener('ielts-record-restored',render);render();
})();
