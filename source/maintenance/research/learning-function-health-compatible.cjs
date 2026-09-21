// Read-only product audit. Runs the actual live scripts in isolated linkedom state.
const fs=require('fs'),assert=require('assert'),crypto=require('crypto'),path=require('path');
const root=path.resolve(__dirname,'..');
const live=process.argv[2]||'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const reportFile=process.argv[3]||path.join(__dirname,'learning-function-audit-20260920.json');
const only=process.argv[4]?new RegExp(process.argv[4]):null;
const fixtureSource=fs.readFileSync(path.join(root,'qa_navigation_ui_final.cjs'),'utf8').split('const f=boot();')[0].replace(/const sourcePath='[^']+';/,'const sourcePath='+JSON.stringify(live)+';');
const compatibleFixture=fixtureSource.replace('const f=fixture(options);f.run(0);f.run(1);f.run(2);f.run(12);','const f=fixture(options);f.run(0);f.run(1);f.run(2);f.run(3);f.run(13);');
const {boot,raw}=new Function('require',compatibleFixture+'\nreturn {boot,raw};')(require);
const results=[];
function check(name,fn){if(only&&!only.test(name))return;console.log('CHECK '+name);try{const detail=fn();results.push({name,status:'pass',detail});}catch(e){results.push({name,status:'needs_fix',error:e.message,actual:e.actual,expected:e.expected});}}
const saved=f=>JSON.parse(f.storage||'{"fields":{}}');
const la=f=>saved(f).fields['learning-adjust-state']?JSON.parse(saved(f).fields['learning-adjust-state']):f.window.IELTSLearning.initial();
const inputSelect=(f,s,v)=>{const n=f.q(s);n.value=v;n.dispatchEvent(new f.ctx.Event('input',{bubbles:true}));f.flush();};
const flushRoute=f=>f.route(f.ctx.location.hash);
const fillTest=(f,id,prefix)=>{for(const n of f.qa('[data-test-answer="'+id+'"]'))f.input(n.dataset.save,prefix+n.dataset.question);f.flush();};
const f=boot();
check('Live book fingerprint',()=>({sha256:crypto.createHash('sha256').update(raw).digest('hex')}));
for(const id of ['listening','reading','writing','speaking'])check(id+': start, answer, submit, locked reference, retry and retained history',()=>{
 f.route('#test-'+id);const panel=f.q('#test-'+id);
 assert(panel.querySelector('.la-test-body').hidden);f.click(panel.querySelector('[data-test-start]'));flushRoute(f);
 assert.equal(la(f).tests[id].status,'running');assert(!panel.querySelector('.la-test-body').hidden);
 assert([...panel.querySelectorAll('[data-test-reference]')].every(n=>n.hidden));
 fillTest(f,id,'first-');const before=Object.fromEntries(f.qa('[data-test-answer="'+id+'"]').map(n=>[n.dataset.question,n.value]));
 f.click(panel.querySelector('[data-test-submit]'));assert.equal(la(f).tests[id].status,'submitted');
 assert(f.qa('[data-test-answer="'+id+'"]').every(n=>n.readOnly));assert(!panel.querySelector('.la-test-result').hidden);
 f.click(panel.querySelector('[data-test-retry]'));assert.equal(la(f).tests[id].status,'running');assert.deepEqual(la(f).tests[id].history[0].answers,before);
 assert(f.qa('[data-test-answer="'+id+'"]').every(n=>n.value===''&&!n.readOnly));
 return {questions:Object.keys(before).length,history:la(f).tests[id].history.length};
});
check('Blank-test cancellation keeps current test running and editable',()=>{
 f.window.confirm=()=>false;f.click(f.q('[data-test-submit="reading"]'));assert.equal(la(f).tests.reading.status,'running');assert(!f.q('[data-test-answer="reading"]').readOnly);f.window.confirm=()=>true;
});
check('Speaking submission is blocked while recording is still active',()=>{
 const stop=f.q('#test-speaking [data-stop]');stop.disabled=false;f.click(f.q('[data-test-submit="speaking"]'));assert.equal(la(f).tests.speaking.status,'running');assert(f.q('#la-notice').textContent.includes('录音'));stop.disabled=true;
});
check('Four-subject combination queues then starts each subject, continues, retains histories',()=>{
 f.click(f.q('#la-start-mock'));flushRoute(f);assert.equal(la(f).tests.listening.status,'running');
 for(const id of ['reading','writing','speaking'])assert.equal(la(f).tests[id].status,'queued');
 const statuses=[];
 for(const id of ['listening','reading','writing','speaking']){
  f.route('#test-'+id);if(id!=='listening')f.click(f.q('[data-test-start="'+id+'"]'));
  fillTest(f,id,'mock-');f.click(f.q('[data-test-submit="'+id+'"]'));assert.equal(la(f).tests[id].status,'submitted');statuses.push(la(f).tests[id].status);
  const next=f.qa('#test-'+id+' .la-test-result button').find(b=>b.textContent.startsWith('继续下一科'));if(id!=='speaking'){assert(next);f.click(next);flushRoute(f);}
 }
 assert(f.q('#la-mock-progress').textContent.includes('4 / 4'));return{statuses,historyBySubject:Object.fromEntries(Object.entries(la(f).tests).map(([k,v])=>[k,v.history.length]))};
});
check('Test result/history and saved answers survive simulated reload',()=>{
 const g=boot({initial:f.storage});for(const id of ['listening','reading','writing','speaking']){assert.equal(la(g).tests[id].status,'submitted');assert(g.q('[data-test-answer="'+id+'"]').readOnly);assert.equal(g.q('[data-test-answer="'+id+'"]').value,'mock-1');assert.equal(la(g).tests[id].history.length,la(f).tests[id].history.length);}return{subjects:4};
});
check('Study project entries resolve to their exact existing learning units',()=>{
 const ids=new Set(f.data.units.map(u=>u.id));let count=0;for(const project of f.data.projects){const actual=f.qa('[data-project="'+project.id+'"] a').map(a=>a.getAttribute('href').slice(1));assert.deepEqual(actual,project.units);for(const id of actual){assert(ids.has(id));f.route('#'+id);assert(f.visible(f.document.getElementById(id)));count++;}}return{projects:f.data.projects.length,unitLinks:count};
});
check('Today list add, duplicate prevention, remove, progress, restore and resume work',()=>{
 const u=f.data.units.find(u=>u.id==='learn-189');f.route('#study-vocabulary-list');let button=f.q('[data-catalog-unit="'+u.id+'"] button');f.click(button);assert.deepEqual(la(f).today,[u.id]);
 f.route('#'+u.id);assert.equal(la(f).last,u.id);f.input(u.steps[0].key,true);f.flush();f.route('#plan');assert(f.q('#la-plan-list').textContent.includes('100%'));
 const g=boot({initial:f.storage});g.route('#study');assert.equal(g.q('#la-resume a').getAttribute('href'),'#'+u.id);assert.equal(la(g).today.length,1);g.route('#plan');g.click(g.q('#la-plan-list button'));assert.equal(la(g).today.length,0);
});
check('Topic/type/Part filters match their stated subset across skills',()=>{
 let filters=0;for(const mode of ['study','practice'])for(const skill of ['listening','reading','writing1','writing2','speaking','vocabulary','phrases','shared']){
  if(!f.data.units.some(u=>u.mode===mode&&u.skill===skill))continue;f.route('#'+mode+'-'+skill+'-list');
  for(const [suffix,key] of [['topic','topic'],['type','category'],['part','part']]){
   if(suffix==='part'&&!['listening','speaking'].includes(skill))continue;const choices=f.qa('#la-'+mode+'-'+suffix+' option').map(n=>n.value).filter(Boolean);
   for(const choice of choices){inputSelect(f,'#la-'+mode+'-'+suffix,choice);const got=f.qa('#la-'+mode+'-cards [data-catalog-unit]').map(n=>n.dataset.catalogUnit).sort();const expected=f.data.units.filter(u=>u.mode===mode&&u.skill===skill&&u[key]===choice).map(u=>u.id).sort();assert.deepEqual(got,expected,mode+'/'+skill+'/'+suffix+'/'+choice);filters++;}
   inputSelect(f,'#la-'+mode+'-'+suffix,'');
  }
 }return{filterSelections:filters};
});
check('Fresh answer gates reject blanks and record original answers before exposing references',()=>{
 const g=boot();const gates=g.qa('[data-answer-gate]').slice(0,3);for(const gate of gates){const keys=JSON.parse(gate.dataset.answerGate);g.click(gate.querySelector('summary'));assert(gate.querySelector('.la-gate-content').hidden);assert(!la(g).checked[gate.id]);for(const key of keys)g.input(key,'暂时不会');g.flush();g.click(gate.querySelector('summary'));assert(!gate.querySelector('.la-gate-content').hidden);assert.deepEqual(la(g).checked[gate.id].answers,Object.fromEntries(keys.map(k=>[k,'暂时不会'])));}return{gates:gates.map(n=>n.id)};
});
check('Failed test submit remains unsubmitted after recovery plus an unrelated successful save',()=>{
 const g=boot();g.click(g.q('[data-test-start="reading"]'));fillTest(g,'reading','draft-');g.setQuota(true);g.click(g.q('[data-test-submit="reading"]'));assert.equal(la(g).tests.reading.status,'running');assert(!g.q('[data-test-answer="reading"]').readOnly);
 g.setQuota(false);g.input('workspace-reflection','Unrelated note after storage recovery');g.flush();assert.equal(la(g).tests.reading.status,'running','A rejected submit was later written by an unrelated input');
});
check('Failed today-list change does not silently reappear after recovery and unrelated input',()=>{
 const g=boot();g.route('#study-vocabulary-list');g.setQuota(true);g.click(g.q('[data-catalog-unit="learn-189"] button'));assert.equal(la(g).today.length,0);g.setQuota(false);g.input('workspace-reflection','Another note');g.flush();assert.equal(la(g).today.length,0,'A rejected today-list edit was later written by an unrelated input');
});
check('Failed gate check stays unchecked after recovery and unrelated input',()=>{
 const g=boot();const gate=g.q('[data-answer-gate]'),keys=JSON.parse(gate.dataset.answerGate);for(const key of keys)g.input(key,'attempt');g.flush();g.setQuota(true);g.click(gate.querySelector('summary'));assert(gate.querySelector('.la-gate-content').hidden);assert(!la(g).checked[gate.id]);g.setQuota(false);g.input('workspace-reflection','A saved note');g.flush();assert(!la(g).checked[gate.id],'A rejected reference check was later written by an unrelated input');
});
check('Failed new-round restart preserves current submitted answers when storage recovers',()=>{
 const g=boot();g.click(g.q('[data-test-start="reading"]'));fillTest(g,'reading','original-');g.click(g.q('[data-test-submit="reading"]'));g.setQuota(true);g.click(g.q('[data-test-retry="reading"]'));assert.equal(la(g).tests.reading.status,'submitted');assert(g.q('[data-test-answer="reading"]').readOnly);g.setQuota(false);g.input('workspace-reflection','Still preserving submitted record');g.flush();assert.equal(la(g).tests.reading.status,'submitted','A rejected retry silently replaced the submitted record');
});
const report={source:live,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'Read-only live product source; actual core, navigation, enrichment, model and learning scripts executed in Node/linkedom with isolated in-memory storage. No real browser, real user storage, layout engine, microphone, network or playback.',passed:results.filter(x=>x.status==='pass').length,total:results.length,checks:results};
fs.writeFileSync(reportFile,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
