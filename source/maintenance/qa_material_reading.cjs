/* Use the existing isolated DOM fixture against this exact publication candidate. */
const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const sourcePath='C:/Users/Admin1/Documents/ChatGPT/ielts/material-reading-qa/candidate.html';
const candidateBytes=fs.readFileSync(sourcePath);
let fixtureSource=fs.readFileSync('qa_navigation_ui_final.cjs','utf8').split('const f=boot();')[0];
fixtureSource=fixtureSource.replace("const sourcePath='D:/IELTS-Work/learning-adjust-20260920/开始学习-ui-final.html';",'const sourcePath='+JSON.stringify(sourcePath)+';');
fixtureSource=fixtureSource.replace('f.run(0);f.run(1);f.run(2);f.run(12);',`const present=[...f.document.querySelectorAll('script')];const concurrency=present.findIndex(n=>n.id==='record-concurrency-model-script');if(concurrency>=0)f.run(concurrency);const first=concurrency===0?1:0;f.run(first);f.run(first+1);f.run(first+2);f.run(present.findIndex(n=>n.id==='authentic-case-script'));`);
const {boot}=new Function('require',fixtureSource+'\nreturn {boot};')(require);
const M=require('./daily-study-model.js');
const integration=JSON.parse(fs.readFileSync('material-reading-qa/integration.json','utf8'));
const catalog=JSON.parse(fs.readFileSync(integration.manifest.find(x=>x.path.endsWith('daily-study-catalog.json')).staged,'utf8'));
const variants=catalog.find(x=>x.skill==='reading').variants;
const checks=[];
function check(name,fn){try{checks.push({name,status:'pass',detail:fn()});console.log('PASS '+name);}catch(e){checks.push({name,status:'fail',error:e.stack});console.log('FAIL '+name+': '+e.message);}}
function studyFixture(){const f=boot();f.named('daily-study-model-script');f.named('daily-study-script');f.named('material-reading-script');f.flush();return f;}

check('Every material has direct pure reading independent of answer submission',()=>{
 const f=studyFixture();assert.equal(variants.length,38);
 for(const v of variants){
  const id='material-reading-'+v.id;const n=f.q('#'+id);
  assert(n,id);assert(!n.closest('.case-feedback'));
  assert(!n.querySelector('[data-save],input,textarea,button'));
  assert(n.querySelectorAll('.mr-paragraph').length>0);
  assert(n.querySelectorAll('.mr-sentence').length>=2);
  assert(!/Q\s*\d+|干扰项|解题步骤|第\s*\d+\s*题/.test(n.textContent),id);
  assert.equal(f.q('#reading-case-'+v.id+' [data-case-done]').checked,false);
 }
 for(const id of [variants[0].id,'rd-c21-ai-1',variants[variants.length-1].id]){f.route('#material-reading-'+id);const n=f.q('#material-reading-'+id);assert(n.open&&f.visible(n),id);}
 const unit=f.q('#reading-case-rd-c21-ai-1'),search=unit.closest('.case-bank').querySelector('[data-case-search]');search.value='no-such-material-123';search.dispatchEvent(new f.ctx.Event('input',{bubbles:true}));assert(unit.hidden);f.route('#material-reading-rd-c21-ai-1');assert(f.visible(f.q('#material-reading-rd-c21-ai-1')));
 return {materials:variants.length};
});
check('Writing preparation precedes the actual task, and every route resolves',()=>{
 const f=studyFixture();let count=0;
 for(const n of f.qa('[data-writing-case]')){
  const body=n.parentElement,children=[...body.children];assert(children.indexOf(n)<children.indexOf(body.querySelector('.case-task')));
  for(const a of n.querySelectorAll('a[href^="#"]'))assert(f.q(a.getAttribute('href')));
  count++;
 }
 for(const n of [f.qa('[data-writing-case]')[0],f.qa('[data-writing-case]').at(-1)]){f.route('#'+n.id);assert(f.visible(n),n.id);}
 assert(count>=2);return{writingUnits:count};
});
check('All materials can be chosen; variable step counts and old snapshots stay valid',()=>{
 for(const v of variants){const plan=M.plan({minutes:60,skills:['reading'],readingCase:v.id},catalog,[]);assert.equal(plan.steps.length,2);assert.equal(plan.steps[0].materialCaseId,v.id);assert.equal(plan.steps[1].target,'material-reading-'+v.id);assert.equal(plan.steps.reduce((n,s)=>n+s.minutes,0),60);const state=M.start({...M.initial(),preferences:{minutes:60,skills:['reading'],readingCase:v.id}},plan,100);assert.deepEqual(M.read(JSON.stringify(state)),state);}
 const oldCatalog=catalog.map(c=>({...c,variants:undefined,stages:Array.from({length:4},(_,i)=>({title:'Old '+i,target:'reading-first',instruction:'Retained old session'}))}));
 const legacy=M.start(M.initial(),M.plan({minutes:30,skills:['reading']},oldCatalog,[]),100);
 assert.equal(M.read(JSON.stringify(legacy)).session.steps.length,4);
});
check('Reading completion reveals only that material’s matching expressions before writing',()=>{
 const pairedDefault=M.plan({minutes:30,skills:['reading','writing2']},catalog,[]);assert(pairedDefault.steps.some(s=>s.skill==='writing2'&&s.readingSourceId),'The paired shortcut should begin with a matching material');
 const v=variants.find(v=>v.id==='rd-c21-ai-1');assert(v.writingTargets.some(w=>w.skill==='writing2'));
 const f=studyFixture();f.route('#guide');f.click(f.q('[data-ds-pair]'));
 const picker=f.q('#ds-reading-material');picker.value=v.id;picker.dispatchEvent(new f.ctx.Event('change',{bubbles:true}));f.click(f.q('#ds-start'));f.flush();
 const state=()=>JSON.parse(JSON.parse(f.storage).fields['daily-study-state']);
 let s=state().session;assert.deepEqual(s.skills,['reading','writing2']);assert.equal(s.steps.length,4);
 f.route('#'+s.steps[0].target);f.click(f.q('#ds-next'));f.flush();s=state().session;f.route('#'+s.steps[s.index].target);assert.equal(s.steps[s.index].target,'material-reading-'+v.id);
 f.click(f.q('#ds-next'));f.flush();s=state().session;f.route('#'+s.steps[s.index].target);
 const block=f.q('#'+s.steps[s.index].target);assert(block.classList.contains('material-writing'));assert(!block.hidden);
 const shown=[...block.querySelectorAll('[data-reading-source]')].filter(n=>!n.hidden);
 assert.equal(shown.length,1);assert.equal(shown[0].dataset.readingSource,v.id);assert(shown[0].open);assert(shown[0].querySelector('blockquote[lang="en"]'));
 const oldValues=[...f.qa('[data-case-answer]')].map(n=>n.value);assert(oldValues.every(v=>!v));
 f.click(f.q('#ds-pause'));const saved=f.storage,g=boot({initial:saved});g.named('daily-study-model-script');g.named('daily-study-script');g.named('material-reading-script');g.flush();g.route('#guide');g.click(g.q('#ds-start'));g.flush();g.route('#'+s.steps[s.index].target);assert.equal(JSON.parse(JSON.parse(g.storage).fields['daily-study-state']).session.index,2);assert(!g.q('#'+block.id).hidden);
});
check('Unmatched writing tasks receive no invented source expression or forced Part change',()=>{
 const v=variants.find(v=>!v.writingTargets.some(w=>w.skill==='writing1'));assert(v);
 const plan=M.plan({minutes:60,skills:['reading','writing1'],readingCase:v.id},catalog,[]);
 assert.deepEqual(plan.skills,['reading','writing1']);assert(plan.steps.filter(s=>s.skill==='writing1').every(s=>!s.readingSourceId));
 const unmatched=variants.find(v=>!v.writingTargets.some(w=>w.skill==='writing2'));assert(unmatched);
 const f=studyFixture();f.route('#guide');f.click(f.q('[data-ds-minutes="60"]'));f.click(f.q('[data-ds-pair]'));
 const picker=f.q('#ds-reading-material');picker.value=unmatched.id;picker.dispatchEvent(new f.ctx.Event('change',{bubbles:true}));f.click(f.q('#ds-start'));f.flush();
 for(let i=0;i<2;i++){const s=JSON.parse(JSON.parse(f.storage).fields['daily-study-state']).session;f.route('#'+s.steps[s.index].target);f.click(f.q('#ds-next'));f.flush();}
 const current=JSON.parse(JSON.parse(f.storage).fields['daily-study-state']).session;f.route('#'+current.steps[current.index].target);
 assert.equal(current.steps[current.index].skill,'writing2');assert(f.qa('[data-writing-case]').every(n=>n.hidden),'Unrelated preparation exposed');
});
check('Rotation continues beyond the thirty-session history limit',()=>{
 let state=M.initial();const chosen=[];
 for(let i=0;i<variants.length;i++){
  const plan=M.plan({minutes:60,skills:['reading']},catalog,state.history);chosen.push(plan.steps[0].materialCaseId);
  state=M.start(state,plan,1000+i);while(state.session.status==='active')state=M.advance(state,2000+i);
 }
 assert.equal(new Set(chosen).size,38);assert.equal(state.history.length,30);
});
check('All source aliases resolve to maintained precision reading',()=>{
 const f=studyFixture();for(const box of f.qa('[data-material-links]'))for(const a of box.querySelectorAll('a'))assert(f.q(a.getAttribute('href')));
 const a=f.q('[data-material-links] a');f.route(a.getAttribute('href'));assert(f.visible(f.q(a.getAttribute('href'))));
});
check('Manual material-to-writing links preserve the selected source',()=>{const f=studyFixture();const a=f.q('#material-reading-rd-c21-ai-1 .mr-writing-links a');f.route(a.getAttribute('href'));const group=f.q(a.getAttribute('href')),block=group.closest('[data-writing-case]');assert(group.open&&!group.hidden&&!block.hidden);assert.equal([...block.querySelectorAll('[data-reading-source]')].filter(x=>!x.hidden).length,1);});
assert(fs.readFileSync(sourcePath).equals(candidateBytes),'Candidate changed during checks');
const out={sha256:crypto.createHash('sha256').update(candidateBytes).digest('hex'),method:'Existing isolated Node/linkedom fixture; synthetic storage, no personal browser data or layout engine. Full static content coverage plus representative deep routes and actual daily transitions.',checks,passed:checks.filter(x=>x.status==='pass').length,total:checks.length};
fs.writeFileSync('material-reading-qa/interaction-results.json',JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));if(out.passed!==out.total)process.exitCode=1;
