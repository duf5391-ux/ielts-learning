(() => {
  'use strict';
  const $=s=>document.querySelector(s), root=$('#word-learn-app'), stateField=$('#word-learning-state');
  if(!root||!stateField||!window.IELTSLookup)return;
  const lookup=window.IELTSLookup, historyField=$('#lookup-history-store');
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  const cards=[...document.querySelectorAll('.tv-card')].map(n=>({id:n.dataset.tvId,topic:n.dataset.tvTopic,topicLabel:n.querySelector('.tv-topic')?.textContent.trim(),term:n.querySelector('[data-local-dictionary]')?.dataset.localDictionary||'',pos:n.querySelector('h3 small')?.textContent.trim()||'',meaning:n.querySelector('.tv-meaning')?.textContent.trim()||'',chunk:n.querySelector('.tv-chunk [lang=en]')?.textContent.trim()||'',translation:n.querySelector('.tv-chunk p:not([lang])')?.textContent.trim()||'',level:n.querySelector('[data-save^="topic-vocab-level-"]')})).filter(c=>c.term&&c.level);
  let current=null,revealed=false;
  function rows(){const r=JSON.parse(historyField.value||'[]');if(!Array.isArray(r)||r.some(x=>!x||typeof x.term!=='string'))throw Error('单词记录暂时无法读取，原记录已保留。请先导出记录。');return r;}
  function read(){const s=JSON.parse(stateField.value||'{}');if(!s||typeof s!=='object'||Array.isArray(s))throw Error('背词进度暂时无法读取，原记录已保留。');return {version:1,topic:'all',currentId:null,...s};}
  const status=el('p','','ui-word-status');status.id='word-learn-status';status.setAttribute('role','status');
  const heading=el('div','','ui-word-heading');heading.append(el('div','VOCABULARY / DAILY PRACTICE','ui-word-eyebrow'),el('h1','背单词'),el('p','从一个词开始，积累自己的表达。','ui-subtitle'));root.append(heading);
  const toolbar=el('div','','ui-word-toolbar'),label=el('label','话题'),topic=el('select');topic.id='word-learn-topic';topic.setAttribute('aria-label','背词话题');
  const topics=new Map(cards.map(c=>[c.topic,c.topicLabel]));for(const [id,name] of [['all','全部话题'],...topics]){const o=el('option',name);o.value=id;topic.append(o)}label.append(topic);
  const count=el('p','','ui-word-count');count.id='word-learn-count';toolbar.append(label,count);root.append(toolbar);
  const surface=el('article','','ui-learn-card');surface.id='word-learn-card';root.append(surface,status);
  function learned(c,r){return !!c.level.value||r.some(x=>lookup.normalize(x.term)===lookup.normalize(c.term)&&(x.learning?.lastAt||x.learning?.legacyMarked||x.reviews?.length));}
  function candidate(s,r){const pool=cards.filter(c=>s.topic==='all'||c.topic===s.topic);return {pool,next:pool.find(c=>c.id===s.currentId&&!learned(c,r))||pool.find(c=>!learned(c,r))};}
  function render(){
    let s,r;try{s=read();r=rows()}catch(e){status.textContent=e.message;return;}
    topic.value=topics.has(s.topic)||s.topic==='all'?s.topic:'all';const {pool,next}=candidate({...s,topic:topic.value},r);current=next;revealed=false;surface.replaceChildren();
    const done=pool.filter(c=>learned(c,r)).length;count.textContent=`已学 ${done} / ${pool.length} 个`;count.setAttribute('aria-label',count.textContent+'，已学不等于掌握');
    if(!current){surface.classList.add('ui-learn-empty');surface.append(el('span','✓','ui-learn-complete'),el('h2','这个话题已经学过一遍'),el('p','复习会接着用你查过和学过的词。'));const a=el('a','开始复习 →','ui-solid-link');a.href='#word-review';surface.append(a);return;}
    surface.classList.remove('ui-learn-empty');surface.append(el('div',current.topicLabel,'ui-topic-pill'));
    const word=el('h2',current.term,'ui-learn-term');word.lang='en';surface.append(word,el('span',current.pos,'ui-learn-pos'));
    const prompt=el('p','先回忆它的意思，再看释义与搭配。','ui-learn-prompt');surface.append(prompt);
    const details=el('div','','ui-learn-definition');details.id='word-learn-definition';details.hidden=true;details.append(el('p',current.meaning,'ui-learn-meaning'));
    if(current.chunk){const quote=el('blockquote');const english=el('p',current.chunk);english.lang='en';quote.append(english,el('p',current.translation));details.append(quote)}
    const reveal=el('button','查看释义与搭配','ui-reveal');reveal.type='button';reveal.id='word-learn-reveal';reveal.addEventListener('click',()=>{revealed=true;details.hidden=false;reveal.hidden=true;prompt.hidden=true;const s=read();window.IELTSRecordStore.commit({[stateField.dataset.save]:JSON.stringify({...s,exposed:{...s.exposed,[current.id]:Date.now()}})},{expectedFields:{[stateField.dataset.save]:stateField.value}});});surface.append(reveal,details);
    const grades=el('div','','ui-learn-grades');for(const [grade,text,hint] of [['forgot','不会','再认识一次'],['hard','模糊','有些印象'],['known','会','继续下一个']]){const b=el('button');b.type='button';b.dataset.learnGrade=grade;b.append(el('strong',text),el('span',hint));b.addEventListener('click',()=>record(grade));grades.append(b)}surface.append(grades);
    surface.append(el('p','标记后进入下一个词，复习会按本次记录接续。','ui-learn-note'));
  }
  function record(grade){if(!current)return;let s,r;try{s=read();r=rows()}catch(e){status.textContent=e.message;return;}
    const c=current,key=lookup.normalize(c.term),old=r.find(x=>lookup.normalize(x.key||x.term)===key)||{},at=new Date().toISOString();
    const independent=!revealed&&!(Date.now()-Number(s.exposed?.[c.id]||0)<600000)&&!(Date.now()-(Date.parse(old.lastAt)||0)<600000);
    const row={...old,key,term:c.term,meaning:old.meaning||c.meaning,chunk:old.chunk||c.chunk,lookupVersion:2,count:old.count||0,source:old.source||'话题词汇',sourceRoute:old.sourceRoute||'topical-vocabulary',topicCardId:old.topicCardId||c.id,
      learning:{...old.learning,lastAt:at,lastGrade:grade,topic:c.topic},learningEvents:[...(Array.isArray(old.learningEvents)?old.learningEvents:[]),{at,grade,answerRevealed:!independent,independentAttempt:independent,topic:c.topic}],
      review:window.IELTSVocabularyReview.plan(old,grade,Date.parse(at),independent)};
    const nextRows=[row,...r.filter(x=>lookup.normalize(x.key||x.term)!==key)],next={...s,currentId:null};
    // N means newly studied. A self-reported recall does not assert the old
    // topic-card K level ("can use it"). Existing topic marks are never downgraded.
    const changes={[historyField.dataset.save]:JSON.stringify(nextRows),[stateField.dataset.save]:JSON.stringify(next),[c.level.dataset.save]:c.level.value||'N'};
    const expectedFields={[historyField.dataset.save]:historyField.value,[stateField.dataset.save]:stateField.value,[c.level.dataset.save]:c.level.value};
    if(!window.IELTSRecordStore.commit(changes,{expectedFields})){status.textContent='这次没能保存，当前单词仍在这里。请先导出记录后重试。';return;}
    status.textContent=`已记录 ${c.term}，继续下一个。`;window.dispatchEvent(new CustomEvent('ielts-lookup-changed'));$('#lookup-history-search')?.dispatchEvent(new Event('input',{bubbles:true}));render();
  }
  topic.addEventListener('change',()=>{let s;try{s=read()}catch(e){status.textContent=e.message;return}const next={...s,topic:topic.value,currentId:null};if(!window.IELTSRecordStore.commit({[stateField.dataset.save]:JSON.stringify(next)},{expectedFields:{[stateField.dataset.save]:stateField.value}})){topic.value=s.topic;status.textContent='话题选择未能保存，请重试。';return}status.textContent='';render();});
  // Existing explicit topic marks count as studied material, but their unknown
  // historical date or answer events are never fabricated.
  function syncMarked(){try{const r=rows(),byKey=new Map(r.map(x=>[lookup.normalize(x.key||x.term),x]));let changed=false;for(const c of cards.filter(x=>x.level.value)){const key=lookup.normalize(c.term),old=byKey.get(key);if(old?.learning||old?.reviews?.length)continue;byKey.set(key,{...old,key,term:c.term,meaning:old?.meaning||c.meaning,chunk:old?.chunk||c.chunk,count:old?.count||0,lookupVersion:2,source:old?.source||'话题词汇',sourceRoute:'topical-vocabulary',topicCardId:c.id,learning:{legacyMarked:true,topic:c.topic}});changed=true}if(changed&&window.IELTSRecordStore.commit({[historyField.dataset.save]:JSON.stringify([...byKey.values()])},{expectedFields:{[historyField.dataset.save]:historyField.value}}))window.dispatchEvent(new CustomEvent('ielts-lookup-changed'));}catch(e){status.textContent=e.message;}}
  window.addEventListener('hashchange',()=>{if(['#vocabulary-review','#word-review','#word-library','#lookup-learning'].includes(location.hash))syncMarked();if(location.hash==='#vocabulary-review')render()});document.addEventListener('ielts-record-restored',()=>{syncMarked();render()});window.addEventListener('storage',()=>{if(!root.closest('.panel').hidden)render()});syncMarked();render();
})();
