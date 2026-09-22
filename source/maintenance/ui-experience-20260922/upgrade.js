(() => {
  'use strict';
  const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n};
  const value=k=>$('[data-save="'+k+'"]')?.value||'';
  function tests(){let state;try{state=JSON.parse($('#learning-adjust-state').value||'{}')}catch{return}
    let running=0,submitted=0,historical=0;
    for(const card of $$('[data-ux-test]')){
      const id=card.dataset.uxTest,t=state.tests?.[id],fields=$$('[data-test-answer="'+id+'"]'),count=fields.filter(f=>f.value.trim()).length,history=t?.history||[];
      if(t?.status==='running')running++;if(t?.status==='submitted')submitted++;historical+=history.length+(t?.status==='submitted'?1:0);
      card.dataset.state=t?.status||'new';const label=card.querySelector('.ux-test-status');
      label.textContent=t?.status==='submitted'?'已提交 · '+count+' / '+fields.length+' 项作答':t?.status==='running'?'进行中 · '+count+' / '+fields.length+' 项作答':'尚未开始';
      card.querySelector('.ux-test-start').textContent=t?.status==='submitted'?'查看本次结果 →':t?.status==='running'?'继续作答 →':'开始'+card.querySelector('h2').textContent+' →';
      card.querySelector('.ux-test-history span').textContent=(history.length+(t?.status==='submitted'?1:0))+' 次';
    }
    const summary=$('#ux-test-summary');summary.replaceChildren();for(const [n,text]of[[running,'科进行中'],[submitted,'科已提交'],[historical,'份历次作答']]){const item=el('div');item.append(el('strong',String(n)),el('span',text));summary.append(item)}
    for(const panel of $$('.la-test-panel'))panel.querySelector('.ux-part-nav').hidden=panel.querySelector('.la-test-body').hidden;
  }
  const questions=JSON.parse($('#writing-question-map').textContent);
  function writing(){let started=0,revised=0;for(const q of questions){const draft=value(q.id+'-first').trim(),frozen=value(q.id+'-first-at'),revision=value(q.id+'-revision').trim();const status=revision?'revised':draft||frozen?'draft':'new';if(status!=='new')started++;if(revision)revised++;
      const row=$('[data-ww-pick="'+q.id+'"]');row.dataset.uxState=status;
      let badge=row.querySelector('.ux-writing-badge');if(!badge){badge=el('b','','ux-writing-badge');row.prepend(badge)}badge.textContent=revision?'有修订稿':frozen?'首稿已保留':draft?'首稿写作中':'尚未开始';
    }
    const out=$('#ux-writing-summary');out.replaceChildren();for(const [n,label]of[[questions.length,'道完整题目'],[started,'道已开始'],[revised,'份修订稿']]){const span=el('span');span.append(el('strong',String(n)),document.createTextNode(' '+label));out.append(span)}
  }
  function review(){const start=$('#vr-start'),extra=$('#vr-practice-all'),stage=$('#vr-stage');
    let hint=$('#ux-review-empty');if(!hint){hint=el('p','','ux-review-empty');hint.id='ux-review-empty';start.closest('.vr-controls').before(hint)}
    hint.hidden=!start.disabled||!stage.hidden;
    if(!hint.hidden){const rows=window.IELTSLookup.getHistory(),next=rows.map(r=>Date.parse(r.review?.dueAt)).filter(t=>Number.isFinite(t)&&t>Date.now()).sort((a,b)=>a-b)[0];hint.textContent=rows.length?(next?'下一次到期：'+new Date(next).toLocaleString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})+'。现在也可以加练。':'暂时没有到期词，可以加练或继续背新词。'):'先背一个词，或查一个词，复习会自动接上。';if(!rows.length){const link=el('a','开始背单词 →');link.href='#vocabulary-review';hint.append(link)}}extra.classList.toggle('ux-primary',start.disabled&&!extra.disabled);
  }
  let scheduled=false;function refresh(){if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;tests();writing();review()})}
  document.addEventListener('input',refresh);document.addEventListener('ielts-record-committed',refresh);document.addEventListener('ielts-record-restored',refresh);window.addEventListener('hashchange',refresh);window.addEventListener('ielts-lookup-changed',refresh);
  document.addEventListener('click',event=>{
    const hist=event.target.closest('[data-ux-history]');if(hist){event.preventDefault();const skill=hist.dataset.uxHistory;location.hash='test-'+skill;requestAnimationFrame(()=>requestAnimationFrame(()=>{const h=$('#ux-test-history-'+skill);h.open=true;h.scrollIntoView({block:'start',behavior:'instant'});h.querySelector('summary').focus({preventScroll:true})}));}
    const part=event.target.closest('[data-ux-part]');if(part){const p=document.getElementById(part.dataset.uxPart);p.scrollIntoView({block:'start',behavior:'instant'});p.querySelector('h2').tabIndex=-1;p.querySelector('h2').focus({preventScroll:true})}
    const view=event.target.closest('button[data-ux-view]');if(view){const p=view.closest('.la-test-part');p.dataset.uxView=view.dataset.uxView;for(const b of p.querySelectorAll('[data-ux-view]'))b.setAttribute('aria-pressed',String(b===view));if(view.dataset.uxView==='answers')p.querySelector('.la-test-sheet input,.la-test-sheet textarea')?.focus({preventScroll:true});}
    // Review stage changes do not all write data (e.g. pause), so inspect after click.
    if(event.target.closest('#word-review'))requestAnimationFrame(review);
  });
  // Keep status feedback readable without inventing a successful save.
  const feedback=['#vr-status','#word-learn-status','#ww-notice','#sentence-status','#lookup-save-warning'];
  for(const selector of feedback){const n=$(selector);if(!n)continue;const paint=()=>{const text=n.textContent.trim();n.classList.toggle('ux-feedback',!!text);n.dataset.uxFeedback=/未能|没能|失败|未保存|无法|未成功/.test(text)?'error':'info'};new MutationObserver(paint).observe(n,{childList:true,subtree:true,characterData:true});paint()}
  // Keyboard grading only when the learner is the active surface and no popup/input owns focus.
  document.addEventListener('keydown',e=>{if(e.repeat||e.ctrlKey||e.metaKey||e.altKey||e.shiftKey||!['1','2','3'].includes(e.key)||$('#vocabulary-review').hidden||e.target.closest('input,textarea,select,[contenteditable=true]')||$$('[role=dialog]').some(n=>!n.hidden))return;const b=$('#vocabulary-review [data-learn-grade="'+['forgot','hard','known'][Number(e.key)-1]+'"]');if(b){e.preventDefault();b.click()}});
  const learner=$('#word-learn-card');function keys(){for(const [i,b]of[...learner.querySelectorAll('[data-learn-grade]')].entries())b.setAttribute('aria-keyshortcuts',String(i+1))}new MutationObserver(keys).observe(learner,{childList:true});keys();
  const helper=el('p','键盘 1 / 2 / 3 也可标记不会、模糊、会。','ux-keyboard-note');$('#word-learn-app').append(helper);
  // Existing popups remain non-modal. Preserve Escape/return-focus behavior.
  for(const id of ['word-lookup','sentence-popup']){const popup=document.getElementById(id);new MutationObserver(()=>document.body.classList.toggle('ux-popup-open',$$('[role=dialog]').some(n=>!n.hidden))).observe(popup,{attributes:true,attributeFilter:['hidden']})}
  refresh();
})();
