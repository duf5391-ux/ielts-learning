/* Answers stay in IndexedDB when hosted, or in the private loopback file store. */
(async () => {
  'use strict';
  const $=id=>document.getElementById(id),root=$('speaking-answerbook');
  const browserMode=document.documentElement.dataset.storage==='browser';
  let database;
  async function localDatabase(){
    if(!database)database=new Promise((resolve,reject)=>{const request=indexedDB.open('ielts-speaking-answerbook',1);request.onupgradeneeded=()=>request.result.createObjectStore('records');request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(Error('浏览器无法打开本机存储：'+request.error.message));request.onblocked=()=>reject(Error('请关闭其他答案本窗口后重试。'));});
    return database;
  }
  async function browserStore(url,body){
    const db=await localDatabase();
    return new Promise((resolve,reject)=>{
      const transaction=db.transaction('records',body?'readwrite':'readonly'),store=transaction.objectStore('records');let result,error;
      transaction.oncomplete=()=>resolve(result);transaction.onabort=transaction.onerror=()=>reject(error||Error('浏览器保存失败：'+(transaction.error?.message||'存储不可用')));
      if(url==='api/book'){result={version:1,records:{}};const cursor=store.openCursor();cursor.onsuccess=()=>{const row=cursor.result;if(row){result.records[row.key]=row.value;row.continue();}};}
      else if(url==='api/record'){
        const request=store.get(body.id);request.onsuccess=()=>{const old=request.result||'';if(old!==body.expected&&old!==body.raw){error=Error('另一窗口已修改同一道题。本页输入仍保留，请导出后刷新核对。');transaction.abort();return;}store.put(body.raw,body.id);result={ok:true};};
      }else if(url==='api/import'){
        result={added:0,identical:0,conflicts:0};for(const [id,raw]of Object.entries(body.records)){const request=store.get(id);request.onsuccess=()=>{if(!request.result){store.put(raw,id);result.added++;}else if(request.result===raw)result.identical++;else result.conflicts++;};}
      }else{error=Error('未知本机操作');transaction.abort();}
    });
  }
  async function api(url,body){if(browserMode&&url.startsWith('api/'))return browserStore(url,body);const response=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{cache:'no-store'});let data;try{data=await response.json();}catch{throw Error('页面没有返回有效内容，请刷新后重试。');}if(!response.ok)throw Error(data.error||'服务暂不可用。');return data;}
  const [bank,book]=await Promise.all([api('question-bank.json'),api('api/book')]);
  const questions=bank.questions,byId=new Map(questions.map(q=>[q.id,q])),cache=new Map();
  // A topic is a display unit; each examiner question keeps its original record ID.
  const groupMap=new Map(),groupForQuestion=new Map(),rows=new Map();let activeGroup=null;
  for(const q of questions){const key=q.part===1?'part1:'+q.topic:q.part===2?q.id:q.related;let group=groupMap.get(key);if(!group){group={id:q.id,topic:q.topic,questions:[]};groupMap.set(key,group);}group.questions.push(q);groupForQuestion.set(q.id,group);}
  const groups=[...groupMap.values()];
  const controls={idea:$('sp-idea'),first:$('sp-first'),revision:$('sp-revision'),keywords:$('sp-keywords')};
  let current=null,timer=null,actionBusy=false,practiceStart=0,elapsed=0,tick=null,practiceDirty=false;
  const blank=()=>({version:1,idea:'',first:'',revision:'',keywords:'',versions:[],preferredId:'',rehearsals:[],referenceSeen:false});
  const clone=x=>JSON.parse(JSON.stringify(x)),now=()=>new Date().toISOString();
  const node=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
  function validate(s){
    if(s?.draftField!==undefined&&!['first','revision'].includes(s.draftField))throw Error('这道题的当前稿件标记无效，不能覆盖原数据。');
    if(!s||s.version!==1||!['idea','first','revision','keywords','preferredId'].every(k=>typeof s[k]==='string')||!Array.isArray(s.versions)||!Array.isArray(s.rehearsals)||typeof s.referenceSeen!=='boolean')throw Error('这道题的本机记录格式异常，原文件保留。请先导出并检查。');
    if(s.versions.some(v=>!v||typeof v.id!=='string'||!Number.isFinite(Date.parse(v.at))||!['first','revision'].includes(v.kind)||typeof v.answer!=='string'||typeof v.referenceSeen!=='boolean')||new Set(s.versions.map(v=>v.id)).size!==s.versions.length||(s.preferredId&&!s.versions.some(v=>v.id===s.preferredId)))throw Error('这道题的版本记录无法读取，不能覆盖原数据。');
    if(s.rehearsals.some(v=>!v||typeof v.id!=='string'||!Number.isFinite(Date.parse(v.at))||typeof v.reflection!=='string'||!Number.isFinite(v.seconds)||typeof v.preferredId!=='string'))throw Error('这道题的自练记录无法读取，不能覆盖原数据。');
    return s;
  }
  function record(id){
    if(!cache.has(id)){const basis=book.records[id]||'';try{cache.set(id,{basis,data:basis?validate(JSON.parse(basis)):blank(),dirty:false,generation:0,pending:null});}catch(error){cache.set(id,{basis,data:blank(),dirty:false,generation:0,error:error.message});}}
    return cache.get(id);
  }
  const state=id=>record(id).data,preferred=s=>s.versions.find(v=>v.id===s.preferredId);
  const draftField=s=>s.draftField||(s.revision?'revision':'first');
  const category=s=>s.preferredId?'final':s.first.trim()||s.revision.trim()||s.idea.trim()?'draft':'empty';
  function status(message,error=false){$('sp-save-status').textContent=message;$('sp-save-status').dataset.error=String(error);$('sp-retry').hidden=!error;}
  async function save(id){
    const rec=record(id);if(rec.pending)await rec.pending;if(!rec.dirty)return !rec.error;
    if(rec.error){status(rec.error,true);return false;}
    const snapshot=clone(rec.data),generation=rec.generation;
    rec.pending=(async()=>{try{
      validate(snapshot);const raw=JSON.stringify(snapshot);if(raw.length>250000)throw Error('这道题的记录较大。请先导出保留全部内容，本次没有截断记录。');
      if(raw!==rec.basis)await api('api/record',{id,expected:rec.basis,raw});
      rec.basis=raw;rec.dirty=rec.generation!==generation;
      rec.saveError='';const failed=[...cache.values()].some(r=>r.saveError);
      if(!failed)status(rec.dirty?'还有新输入，正在继续保存…':browserMode?'已保存到当前浏览器。作答没有上传。':'已保存到本机文件。没有上传到云端或第三方 AI。');
      updateCounts();refreshRows();renderList();return true;
    }catch(error){rec.saveError=error.message;status('尚未保存：'+error.message+' 当前文字仍在本页，可以导出保留。',true);refreshRows();return false;}})();
    const ok=await rec.pending;rec.pending=null;if(ok&&rec.dirty)schedule();return ok;
  }
  async function flush(){clearTimeout(timer);timer=null;let ok=true;for(const [id,rec]of cache){if(rec.pending)await rec.pending;if(rec.dirty&&!await save(id))ok=false;}return ok;}
  function schedule(){clearTimeout(timer);timer=setTimeout(()=>void flush(),350);}
  function dirty(id){const rec=record(id);rec.dirty=true;rec.generation++;}
  async function change(next,message){
    const id=current,rec=record(id);if(rec.error){status(rec.error,true);return false;}
    if(!await flush())return false;
    const prior=clone(rec.data);rec.data=next;dirty(id);
    if(!await save(id)){
      // Keep typed words while rolling back an unaccepted version/selection action.
      const live=rec.data;rec.data={...prior,...Object.fromEntries(Object.keys(controls).map(k=>[k,live[k]]))};if(live.draftField)rec.data.draftField=live.draftField;rec.dirty=true;rec.generation++;return false;
    }
    status(message);paintState();return true;
  }
  async function command(fn){if(actionBusy)return;actionBusy=true;root.setAttribute('aria-busy','true');try{await fn();}catch(error){status(error.message,true);}finally{actionBusy=false;root.removeAttribute('aria-busy');}}
  function updateCounts(){let started=0,final=0;for(const q of questions){const s=state(q.id);if(category(s)!=='empty')started++;if(s.preferredId)final++;}$('sp-progress').textContent=`${groups.length} 个话题 · ${started} / ${questions.length} 题已填写 · ${final} 题已选定答案`;$('sp-question-state').textContent=current?({empty:'还未填写',draft:'正在准备',final:'已有个人答案'}[category(state(current))]):'';if(activeGroup){const a=activeGroup.questions;$('sp-group-progress').textContent=`本话题 ${a.length} 题 · ${a.filter(q=>category(state(q.id))!=='empty').length} 题已填写 · ${a.filter(q=>state(q.id).preferredId).length} 题已选定答案`;}}
  function groupCategory(g){return g.questions.every(q=>state(q.id).preferredId)?'final':g.questions.some(q=>category(state(q.id))!=='empty')?'draft':'empty';}
  function filtered(){const query=$('sp-search').value.trim().toLowerCase(),part=$('sp-part').value,topic=$('sp-topic').value,kind=$('sp-state').value;return groups.filter(g=>(!part||g.questions.some(q=>String(q.part)===part))&&(!topic||g.topic===topic)&&(!query||(g.topic+' '+g.questions.map(q=>q.prompt).join(' ')).toLowerCase().includes(query))&&(!kind||groupCategory(g)===kind));}
  function renderList(){
    const list=$('sp-question-list');list.replaceChildren();const found=filtered();$('sp-filter-count').textContent=`找到 ${found.length} 个话题`;
    for(const g of found){const li=node('li',''),button=node('button','');button.type='button';button.setAttribute('aria-current',String(g===activeGroup));button.dataset.spGroup=g.id;button.append(node('small',`${g.questions[0].part===1?'Part 1':'Part 2 & 3'} · ${g.questions.length} 题 · ${g.questions.filter(q=>category(state(q.id))!=='empty').length} 已填`),node('span',g.topic));button.onclick=()=>command(()=>select(g.id));li.append(button);list.append(li);}
    if(!found.length)list.append(node('li','没有符合条件的话题，试试清除筛选。'));
    const i=found.findIndex(g=>g===activeGroup);$('sp-previous').disabled=i<=0;$('sp-next').disabled=i<0||i===found.length-1;
  }
  function refreshRows(){for(const [id,row]of rows){const rec=record(id),s=rec.data;if(document.activeElement!==row.input)row.input.value=s[draftField(s)];row.input.disabled=!!rec.error;const final=preferred(s);row.label.textContent=rec.error||rec.saveError||(rec.dirty?'正在保存…':final?(final.answer===s[draftField(s)]?'已选为我的答案':'草稿已保存 · 另有选定版本'):(category(s)==='empty'?'':'草稿已保存'));row.label.dataset.error=String(!!(rec.error||rec.saveError));}}
  function parkTools(){for(const row of rows.values())row.card.classList.remove('is-practicing');const panel=$('sp-question-tools');panel.hidden=true;$('sp-tools-parking').append(panel);}
  function renderGroup(group){
    parkTools();activeGroup=group;rows.clear();const host=$('sp-group-questions');host.replaceChildren();$('sp-group-title').textContent=group.topic;$('sp-group-part').textContent=group.questions[0].part===1?'PART 1':'PART 2 & 3';root.dataset.currentGroup=group.id;
    let lastPart=0,number=0;
    for(const q of group.questions){
      if(q.part!==lastPart){lastPart=q.part;number=0;if(q.part!==1){const heading=node('h3',q.part===2?'Part 2 · 题卡':'Part 3 · 追问');heading.className='sp-part-heading';host.append(heading);}}
      number++;const card=node('article','');card.className='sp-stage sp-question-card';card.dataset.questionId=q.id;card.id='card-'+q.id;
      const title=node('h3',`${number}. ${q.prompt}`);title.lang='en';title.id='prompt-'+q.id;card.append(title);
      if(q.cuePoints){card.append(node('p','You should say:'));const cues=node('ul','');cues.className='sp-cues';cues.lang='en';cues.append(...q.cuePoints.map(x=>node('li',x)));card.append(cues);}
      if(q.editorNote){const note=node('p',q.editorNote);note.className='sp-note';card.append(note);}
      const label=node('label','我的回答'),input=node('textarea','');input.rows=q.part===2?7:3;input.maxLength=20000;input.dataset.answerFor=q.id;input.setAttribute('aria-labelledby',title.id);input.placeholder='';label.append(input);card.append(label);
      const actions=node('div','');actions.className='sp-actions';const choose=node('button','选为我的答案');choose.type='button';choose.onclick=()=>command(async()=>{if(await select(q.id))await keep(draftField(state(q.id)),true);});
      const tools=node('button','版本、练习与参考');tools.type='button';tools.dataset.toolsFor=q.id;tools.onclick=()=>command(async()=>{if(!await select(q.id))return;const panel=$('sp-question-tools');card.append(panel);panel.hidden=false;});
      const saved=node('span','');saved.className='sp-help sp-row-status';saved.setAttribute('role','status');actions.append(choose,tools,saved);card.append(actions);host.append(card);rows.set(q.id,{card,input,label:saved});
      input.oninput=()=>{const rec=record(q.id);if(rec.error)return;let field=draftField(rec.data);if(field==='first'&&rec.data.versions.some(v=>v.kind==='first'))field='revision';rec.data[field]=input.value;rec.data.draftField=field;dirty(q.id);if(q.id===current){controls[field].value=input.value;wordCount();}status('正在保存到本机…');refreshRows();schedule();};
    }
    refreshRows();updateCounts();
  }
  function topics(){const chosen=$('sp-topic').value,part=$('sp-part').value,names=[...new Set(questions.filter(q=>!part||String(q.part)===part).map(q=>q.topic))];$('sp-topic').replaceChildren(new Option('全部话题',''),...names.map(n=>new Option(n,n)));if(names.includes(chosen))$('sp-topic').value=chosen;}
  function wordCount(){for(const kind of ['first','revision'])$('sp-'+kind+'-count').textContent=`${(controls[kind].value.match(/[A-Za-z]+(?:['’-][A-Za-z]+)*/g)||[]).length} 个英文词 · 仅供检查篇幅`;}
  async function keep(kind,choose){
    if(!state(current)[kind].trim()){status('先填写这份'+(kind==='first'?'初稿':'修改稿')+'，再保存版本。',true);return false;}
    if(!await flush())return false;const next=clone(state(current));let version=next.versions.slice().reverse().find(v=>v.kind===kind&&v.answer===next[kind]);
    if(!version){if(kind==='first'&&next.versions.some(v=>v.kind==='first')){status('初稿已经保留，请在修改区继续。',true);return false;}version={id:crypto.randomUUID(),at:now(),kind,answer:next[kind],referenceSeen:next.referenceSeen};next.versions.push(version);}
    if(choose)next.preferredId=version.id;
    const ok=await change(next,choose?'已选为我的答案。原稿和其他版本仍保留。':'这个版本已保存，后续修改不会覆盖它。');if(ok&&kind==='first')$('sp-revision-section').open=true;return ok;
  }
  function history(){
    const s=state(current),host=$('sp-history');host.replaceChildren();$('sp-history-summary').textContent=`原稿与修订记录（${s.versions.length}）`;
    for(const v of s.versions.slice().reverse()){
      const entry=node('details','');entry.className='sp-history-row';entry.append(node('summary',`${v.kind==='first'?'初稿':'修改稿'} · ${new Date(v.at).toLocaleString()}${v.id===s.preferredId?' · 我的答案':''}`),node('pre',v.answer));
      const choose=node('button','选为我的答案');choose.type='button';choose.onclick=()=>command(async()=>{const next=clone(state(current));next.preferredId=v.id;await change(next,'已选定这个版本；其他版本仍保留。');});
      const use=node('button','复制到修改区');use.type='button';use.onclick=()=>command(async()=>{if(controls.revision.value.trim()&&controls.revision.value!==v.answer){if(!confirm('修改区已有文字。先保留为一个修订版本，再载入这份历史稿？'))return;if(!await keep('revision',false))return;}controls.revision.value=v.answer;edit('revision');$('sp-revision-section').open=true;controls.revision.focus();});entry.append(choose,use);host.append(entry);
    }
    if(!s.versions.length)host.append(node('p','保留初稿或修订版本后，可以在这里回看。自动保存的草稿仍可继续编辑。'));
    if(s.rehearsals.length){const d=node('details','');d.append(node('summary',`自练记录（${s.rehearsals.length}）`));for(const p of s.rehearsals.slice().reverse())d.append(node('p',`${new Date(p.at).toLocaleString()} · ${p.seconds} 秒`),node('blockquote',p.reflection));host.append(d);}
  }
  function paintState(){const s=state(current),final=preferred(s),hasFirst=s.versions.some(v=>v.kind==='first');controls.first.readOnly=hasFirst;$('sp-keep-first').disabled=hasFirst;$('sp-keep-first').textContent=hasFirst?'初稿已保留':'保留这份初稿';$('sp-final-text').textContent=final?.answer||'尚未选定答案。';$('sp-practice-open').disabled=!final;$('sp-unset').hidden=!final;$('sp-practice-answer').textContent=final?.answer||'';$('sp-practice-keywords').textContent=s.keywords||'未设置关键词。';$('sp-practice-count').textContent=`已记录 ${s.rehearsals.length} 次自练。`;updateCounts();refreshRows();history();renderList();wordCount();}
  async function select(id){
    if(!byId.has(id)||!await flush())return false;
    if(practiceDirty){status('本次自练反思尚未记录，请先记录自练，或复制保留后清空反思再切题。',true);return false;}
    stopTimer();$('sp-practice').hidden=true;$('sp-editing').hidden=false;current=id;const q=byId.get(id),rec=record(id),s=rec.data;const group=groupForQuestion.get(id);if(group!==activeGroup){const hadGroup=!!activeGroup;renderGroup(group);if(hadGroup)$('sp-group-title').scrollIntoView({block:'start'});}else parkTools();
    root.dataset.currentQuestion=id;$('sp-topic-title').textContent=q.topic;$('sp-part-label').textContent='PART '+q.part;$('sp-prompt').textContent=q.prompt;
    const cues=$('sp-cues');cues.replaceChildren(...(q.cuePoints||[]).map(x=>node('li',x)));cues.hidden=!q.cuePoints;$('sp-editor-note').hidden=!q.editorNote;$('sp-editor-note').textContent=q.editorNote||'';
    for(const [kind,c]of Object.entries(controls)){c.value=s[kind];c.disabled=!!rec.error;}
    $('sp-source').href='speaking-personal-reference/questions.pdf#page='+q.source.pages[0];$('sp-source').textContent='原题参考 · PDF 第 '+q.source.pages.join('、')+' 页';$('sp-reference').hidden=!q.referencePage;$('sp-reference').href='speaking-personal-reference/samples.pdf#page='+(q.referencePage||1);$('sp-method').hidden=q.part!==1;$('sp-method').href='speaking-personal-reference/method.pdf#page='+(q.methodPage||1);$('sp-reference-details').open=false;$('sp-copy-fallback').hidden=true;$('sp-notes').open=!!s.idea;$('sp-copy-status').textContent='';$('sp-copy-text').value='';$('sp-revision-section').open=!!s.revision||s.versions.some(v=>v.kind==='first');
    paintState();window.history.replaceState(null,'','#'+id);const active=$('sp-question-list').querySelector('[aria-current="true"]');if(active){const list=$('sp-question-list');list.scrollTop+=active.getBoundingClientRect().top-list.getBoundingClientRect().top-list.clientHeight/3;}status(rec.error||(rec.basis?'已载入这道题的本机记录。':'本题尚未填写。'),!!rec.error);return true;
  }
  function edit(kind){const rec=record(current);if(rec.error)return;rec.data[kind]=controls[kind].value;if(kind==='first'||kind==='revision')rec.data.draftField=kind;dirty(current);status('正在保存到本机…');wordCount();refreshRows();schedule();}
  function download(name,body){const url=URL.createObjectURL(new Blob([body],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);}
  function exportBook(){
    const lines=['我的口语答案本','导出于 '+new Date().toLocaleString(),'包含本页尚未保存的文字；个人选定稿不是官方标准答案。',''];
    for(const q of questions){const rec=record(q.id),s=rec.data;if(category(s)==='empty'&&!rec.error)continue;lines.push(`Part ${q.part} · ${q.topic}`,q.prompt,...(q.cuePoints||[]).map(x=>'• '+x),'');if(rec.error)lines.push('原始记录（无法解析，原样保留）：',rec.basis);for(const [title,key]of [['我的素材','idea'],['当前初稿','first'],['当前修改稿','revision'],['关键词','keywords']])if(s[key])lines.push(title,s[key],'');const final=preferred(s);if(final)lines.push('我的选定答案',final.answer,'');for(const v of s.versions)lines.push(`${v.kind==='first'?'初稿':'修改稿'}版本 · ${v.at}`,v.answer,'');for(const p of s.rehearsals)lines.push('自练 · '+p.at+' · '+p.seconds+'秒',p.reflection,'');if(q.id===current&&practiceDirty)lines.push('本次尚未记录的自练反思',$('sp-reflection').value,'');lines.push('--------------------','');}
    download('我的口语答案本.txt',lines.join('\n'));const unsaved=[...cache.values()].some(r=>r.dirty);status(unsaved?'已导出答案本，包含尚未保存的文字。请继续重试保存，或保留导出文件后刷新核对。':'已导出答案本。',unsaved);
  }
  async function exportBackup(){
    const fresh=await api('api/book');for(const [id,rec]of cache)if(rec.dirty&&!rec.error)fresh.records[id]=JSON.stringify(rec.data);
    fresh.exportedAt=now();download('口语答案备份-'+now().slice(0,10)+'.json',JSON.stringify(fresh,null,2));
    status('已导出可导入的备份文件。'+(practiceDirty?'本次自练反思尚未记录，请先点击“记录这次自练”。':''),[...cache.values()].some(r=>r.dirty));
  }
  async function importBackup(file){
    if(!file)return;if(practiceDirty)throw Error('请先记录本次自练，再导入备份。');if(!await flush())return;
    if(file.size>50000000)throw Error('备份文件过大，请检查文件。');
    const incoming=JSON.parse(await file.text());if(incoming.version!==1||!incoming.records||typeof incoming.records!=='object'||Array.isArray(incoming.records))throw Error('这不是有效的口语答案备份。');
    for(const [id,raw]of Object.entries(incoming.records)){if(!byId.has(id)||typeof raw!=='string'||raw.length>250000)throw Error('备份含未知题目或无效记录，本次未导入。');validate(JSON.parse(raw));}
    const result=await api('api/import',{records:incoming.records}),fresh=await api('api/book');book.records=fresh.records;cache.clear();activeGroup=null;await select(current);
    status(`已导入 ${result.added} 题，${result.identical} 题相同。${result.conflicts?result.conflicts+' 题与当前答案不同，已保留当前答案；备份文件中的稿件未覆盖它们。':''}`);
  }
  function stopTimer(){if(tick){elapsed+=Date.now()-practiceStart;clearInterval(tick);tick=null;}$('sp-timer-start').textContent='继续计时';}
  function clockText(){const seconds=Math.floor((elapsed+(tick?Date.now()-practiceStart:0))/1000);$('sp-timer').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');}
  for(const [kind,c]of Object.entries(controls))c.oninput=()=>edit(kind);
  $('sp-part').onchange=()=>{topics();renderList();};for(const id of ['sp-topic','sp-state'])$(id).onchange=renderList;$('sp-search').oninput=renderList;
  $('sp-clear').onclick=()=>{$('sp-search').value='';$('sp-part').value='';$('sp-state').value='';topics();$('sp-topic').value='';renderList();};
  $('sp-previous').onclick=()=>command(async()=>{const a=filtered(),i=a.indexOf(activeGroup);if(i>0)await select(a[i-1].id);});$('sp-next').onclick=()=>command(async()=>{const a=filtered(),i=a.indexOf(activeGroup);if(i>=0&&i<a.length-1)await select(a[i+1].id);});
  $('sp-close-tools').onclick=()=>command(async()=>{if(practiceDirty){status('本次自练反思尚未记录，请先记录自练。',true);return;}if(!await flush())return;stopTimer();parkTools();});
  $('sp-retry').onclick=()=>command(flush);$('sp-export').onclick=exportBook;$('sp-export-bottom').onclick=exportBook;
  $('sp-backup').onclick=()=>command(exportBackup);$('sp-import').hidden=!browserMode;$('sp-import-help').hidden=!browserMode;
  $('sp-import').onclick=()=>$('sp-import-file').click();$('sp-import-file').onchange=()=>command(async()=>{try{await importBackup($('sp-import-file').files[0]);}finally{$('sp-import-file').value='';}});
  $('sp-keep-first').onclick=()=>command(()=>keep('first',false));$('sp-save-revision').onclick=()=>command(()=>keep('revision',false));$('sp-choose-first').onclick=()=>command(()=>keep('first',true));$('sp-choose-revision').onclick=()=>command(()=>keep('revision',true));
  $('sp-copy-first').onclick=()=>{if(actionBusy)return;if(controls.revision.value.trim()){status('修改区已有内容。请先保存版本，再从历史中载入初稿。',true);return;}controls.revision.value=controls.first.value;edit('revision');controls.revision.focus();};
  $('sp-unset').onclick=()=>command(async()=>{const next=clone(state(current));next.preferredId='';await change(next,'已取消选定；全部稿件仍保留。');});
  for(const id of ['sp-source','sp-reference','sp-method'])$(id).addEventListener('click',()=>{const rec=record(current);if(!rec.error&&!rec.data.referenceSeen){rec.data.referenceSeen=true;dirty(current);schedule();}});
  $('sp-copy-coaching').onclick=async()=>{const q=byId.get(current),s=state(current),content=`请根据这道题检查我的回答是否回应题意，并修改不清楚或不自然的表达。保留我的真实意思；题目没有要求的理由、经历或结构，不作为必须补充的内容。\nPart ${q.part}：${q.prompt}\n${(q.cuePoints||[]).join('\n')}\n本题笔记：${s.idea}\n我的作答：${s[$('sp-feedback-version').value]}\n仅评价文字内容，不能评价发音或实际流利度。`;$('sp-copy-text').value=content;$('sp-copy-fallback').hidden=false;try{await navigator.clipboard.writeText(content);$('sp-copy-status').textContent='已复制。你可以贴回当前聊天，让我继续带你修改。';}catch{$('sp-copy-status').textContent='请从下面的文字框手动复制。';$('sp-copy-text').select();}};
  $('sp-practice-open').onclick=()=>command(async()=>{if(!await flush()||!preferred(state(current)))return;const s=state(current);$('sp-practice-keywords').textContent=s.keywords||'未设置关键词。';$('sp-practice-answer').textContent=preferred(s).answer;$('sp-editing').hidden=true;$('sp-practice').hidden=false;rows.get(current)?.card.classList.add('is-practicing');$('sp-practice-answer').hidden=true;$('sp-reveal').textContent='看我的答案';$('sp-practice-status').textContent='';elapsed=0;clockText();$('sp-timer-start').textContent='开始计时';$('sp-practice').scrollIntoView({block:'start'});});
  $('sp-practice-close').onclick=()=>{stopTimer();$('sp-practice').hidden=true;$('sp-editing').hidden=false;rows.get(current)?.card.classList.remove('is-practicing');};
  $('sp-reveal').onclick=()=>{const n=$('sp-practice-answer');n.hidden=!n.hidden;$('sp-reveal').textContent=n.hidden?'看我的答案':'隐藏答案';};
  $('sp-timer-start').onclick=()=>{if(tick){stopTimer();clockText();return;}practiceStart=Date.now();tick=setInterval(clockText,250);$('sp-timer-start').textContent='暂停计时';};
  $('sp-reflection').oninput=()=>{practiceDirty=!!$('sp-reflection').value.trim();};
  $('sp-practice-save').onclick=()=>command(async()=>{stopTimer();clockText();const reflection=$('sp-reflection').value.trim();if(!reflection){$('sp-practice-status').textContent='请填写本次练习记录。';return;}const next=clone(state(current));next.rehearsals.push({id:crypto.randomUUID(),at:now(),seconds:Math.floor(elapsed/1000),preferredId:next.preferredId,reflection});if(await change(next,'本次自练记录已保存。')){$('sp-practice-status').textContent='本次自练已记录。';$('sp-reflection').value='';practiceDirty=false;elapsed=0;clockText();}});
  window.addEventListener('beforeunload',event=>{if(practiceDirty||[...cache.values()].some(r=>r.dirty||r.pending)){event.preventDefault();event.returnValue='';}});
  window.addEventListener('pagehide',stopTimer);
  topics();await select(byId.has(location.hash.slice(1))?location.hash.slice(1):questions.find(q=>q.part===1&&q.topic.startsWith('学习'))?.id||questions[0].id);
  window.IELTSSpeakingAnswerBook=Object.freeze({select,flush,exportBook,getCurrent:()=>current,read:id=>clone(state(id)),questionCount:questions.length});
})().catch(error=>{const box=document.getElementById('sp-load-error');box.hidden=false;box.textContent='答案本未能载入：'+error.message+(document.documentElement.dataset.storage==='browser'?' 请检查浏览器是否允许本机存储，再刷新重试。':' 请使用“打开口语答案本”启动本机服务。原文件不会被覆盖。');document.querySelectorAll('textarea,button,select,input').forEach(n=>n.disabled=true);});
