#!/usr/bin/env node
'use strict';
// Actual candidate controllers in isolated Node/linkedom. No user browser/profile.
const fs=require('fs'),path=require('path'),assert=require('assert'),vm=require('vm'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..');
const source=path.resolve(process.argv[2]||path.join(__dirname,'开始学习.html'));
const baseline=path.resolve(process.argv[3]||path.join(root,'content-pipeline/mobile-media-20260921/开始学习.html'));
const output=path.resolve(process.argv[4]||path.join(__dirname,'qa.json'));
let harness=fs.readFileSync(path.join(root,'qa_navigation_ui_final.cjs'),'utf8').split('const f=boot();')[0];
harness=harness.replace(/const sourcePath='[^']+';/,'const sourcePath='+JSON.stringify(source)+';')
 .replace('return{callbacks,document','return{rafs,timers,setStorage(value){storage=value},callbacks,document')
 .replace('const f=fixture(options);f.run(0);f.run(1);f.run(2);f.run(12);',`const f=fixture(options);
 const selected=[...f.document.querySelectorAll('script')];
 const runMatch=predicate=>{const found=selected.map((s,i)=>({s,i})).filter(({s})=>predicate(s));assert.equal(found.length,1,'Unique script required');f.run(found[0].i);};
 runMatch(s=>s.id==='record-concurrency-model-script');
 runMatch(s=>s.textContent.includes('/* RECORD-SAFETY-20260919 */'));
 runMatch(s=>s.textContent.includes('function recordCount()'));
 runMatch(s=>s.textContent.includes('function updateProgress(){const s=stored()'));
 runMatch(s=>s.textContent.includes('// RUNTIME-PERFORMANCE-V1:'));
 runMatch(s=>s.id==='authentic-case-script');`);
const {boot,parseHTML,raw}=new Function('require',harness+'\nreturn {boot,parseHTML,raw};')(require);
const baseRaw=fs.readFileSync(baseline),beforeDoc=parseHTML(baseRaw.toString('utf8')).document;
const candidateDoc=parseHTML(raw.toString('utf8')).document,checks=[];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const check=(name,fn)=>{try{checks.push({name,status:'pass',detail:fn()});}catch(e){checks.push({name,status:'needs_fix',error:e.stack});}console.log(checks.at(-1).status+' '+name);};
const json=value=>JSON.parse(JSON.stringify(value));
const change=(f,node)=>node.dispatchEvent(new f.ctx.Event('change',{bubbles:true}));
const set=(f,selector,value)=>{const n=f.q(selector);n.value=value;n.dispatchEvent(new f.ctx.Event('input',{bubbles:true}));return n;};

check('All 3353 save controls, content IDs and fixed daily/health/concurrency blocks survive',()=>{
 for(const [selector,attr] of [['[data-save]','data-save'],['[id]','id']]){
  const a=[...beforeDoc.querySelectorAll(selector)].map(n=>n.getAttribute(attr)),b=[...candidateDoc.querySelectorAll(selector)].map(n=>n.getAttribute(attr));
  for(const value of a)assert.equal(b.filter(v=>v===value).length,1,'Lost or duplicated '+attr+' '+value);
  assert.equal(new Set(b).size,b.length,'Duplicate '+attr);if(attr==='data-save')assert.equal(b.length,3353);
 }
 const normalized=n=>n.outerHTML.replace(/\r\n/g,'\n');
 for(const id of ['daily-study-catalog','daily-study-model-script','daily-study-script','record-concurrency-model-script','health-study-bridge-script','health-study-ui-script','energy-control-script'])assert.equal(normalized(candidateDoc.querySelector('#'+id)),normalized(beforeDoc.querySelector('#'+id)),id+' changed');
 assert.deepStrictEqual(JSON.parse(candidateDoc.querySelector('#learning-adjust-data').textContent),JSON.parse(beforeDoc.querySelector('#learning-adjust-data').textContent));
 return {saveFields:3353};
});
check('Every inline executable script parses',()=>{
 let count=0;for(const s of candidateDoc.querySelectorAll('script'))if(!s.src&&s.type!=='application/json'){new vm.Script(s.textContent);count++;}return{scripts:count};
});

const f=boot();
check('Startup paints the active catalog once and leaves hidden unit progress unbuilt',()=>{
 assert.equal(f.q('main>.panel:not([hidden])').id,'study');
 assert.equal(f.qa('#la-study-cards [data-subject]').length,4);
 assert.equal(f.qa('#la-practice-cards [data-subject]').length,0);
 assert.equal(f.qa('[data-unit-progress] progress').length,0);
 assert.equal(f.q('#topical-vocabulary').getAttribute('aria-busy'),'true');
 assert.equal(f.q('#topical-vocabulary').dataset.tvReady,undefined);
});
check('Input is persisted synchronously and updates only the related word/score counter',()=>{
 const outputs=f.qa('[data-wordcount]'),first=outputs[0],other=outputs.find(x=>x.dataset.wordcount!==first.dataset.wordcount);
 other.textContent='untouched counter sentinel';f.input(first.dataset.wordcount,'two words');
 assert.equal(JSON.parse(f.storage).fields[first.dataset.wordcount],'two words');
 assert.equal(first.textContent,'2 词（空白分隔计数）');assert.equal(other.textContent,'untouched counter sentinel');
 const score=f.q('[data-score]');f.input(score.dataset.save,true);assert(f.q('#'+score.dataset.score+'-score').textContent.startsWith('1 / '));
 f.flush();
});
check('One input burst schedules one frame per progress controller and retains every test part',()=>{
 f.route('#test-reading');f.rafs.splice(0);
 f.input('full-test-reading-q1','answer 1');f.input('full-test-reading-q15','answer 15');f.input('full-test-listening-q1','answer listening');
 for(let i=0;i<30;i++)f.input('full-test-reading-q2','burst '+i);
 assert.equal(f.rafs.length,2,'Expected one legacy and one learning-adjust paint');
 f.flush();
 assert(f.q('#test-reading [data-test-progress]').textContent.includes('3 / 40'));
 assert(f.q('#test-listening [data-test-progress]').textContent.includes('1 / 40'));
 const parts=f.qa('#test-reading [data-test-part-progress]');assert(parts[0].textContent.includes('2 /'));assert(parts[1].textContent.includes('1 /'));
 assert.equal(JSON.parse(f.storage).fields['full-test-reading-q2'],'burst 29');
});
check('Unit deep links, visible progress and category return reflect saved values',()=>{
 const u=f.data.units.find(u=>u.id==='pr-jijing-202609-listening-01-v1');assert(u);
 f.route('#'+u.id);const out=f.q('[data-unit-progress="'+u.id+'"]');assert(f.visible(out));assert(out.querySelector('progress'));
 const key=u.steps.find(s=>s.kind!=='checked'&&s.kind!=='check').key;f.input(key,'attempt');f.flush();assert(out.textContent.includes('1 /'));
 f.route('#study-reading-list');assert(f.qa('#la-study-cards [data-catalog-unit]').length>0);
 f.input(key,'');f.flush();f.route('#'+u.id);assert(out.textContent.includes('0 /'));
 for(const id of ['pr-jijing-202609-reading-01-v1','listening-new-new-listening-campus-notes','usage-04']){f.route('#'+id);assert(f.visible(f.document.getElementById(id)),id);}
});
let checkedStorage;
check('Answer gates preserve required answers, saved first attempts, revisions and save-failure lock',()=>{
 const g=boot(),id='pr-jijing-202609-reading-01-v1';g.route('#'+id);
 const gate=g.q('#'+id+' [data-answer-gate]'),content=gate.querySelector('.la-gate-content'),keys=JSON.parse(gate.dataset.answerGate);
 g.click(gate.querySelector('summary'));assert(content.hidden);
 for(const key of keys)g.input(key,'first '+key);g.flush();assert(!gate.classList.contains('la-gate-locked'));
 g.setQuota(true);g.click(gate.querySelector('summary'));assert(content.hidden);g.setQuota(false);
 g.click(gate.querySelector('summary'));assert(!content.hidden);g.flush();
 const snapshot=json(g.state().checked[gate.id]);assert(snapshot.at);
 g.input(keys[0],'revised answer');g.click(gate.querySelector('summary'));g.flush();
 assert.deepStrictEqual(json(g.state().checked[gate.id]),snapshot);
 checkedStorage=g.storage;const restored=boot({initial:checkedStorage});restored.route('#'+id);
 assert.equal(restored.q('[data-save="'+keys[0]+'"]').value,'revised answer');assert.deepStrictEqual(json(restored.state().checked[gate.id]),snapshot);
 return{requiredAnswers:keys.length};
});
check('Vocabulary index yields between batches, direct route waits, pagination mutates at most two pages',()=>{
 const g=boot();g.ctx.location.hash='#topical-vocabulary';for(const fn of g.callbacks.hashchange||[])fn();
 let frames=0,intermediate=false;while(g.rafs.length&&frames++<100){g.rafs.shift()();const done=g.qa('.tv-card[hidden]').length;if(done>0&&done<975)intermediate=true;}
 assert(intermediate,'No partial index state observed');assert.equal(g.q('#topical-vocabulary').dataset.tvReady,'true');
 assert.equal(g.qa('.tv-card:not([hidden])').length,25);assert.equal(g.q('#tv-page').textContent,'1 / 40');assert(g.q('#tv-count').textContent.includes('1000 条匹配'));
 let writes=0;for(const card of g.qa('.tv-card'))Object.defineProperty(card,'hidden',{configurable:true,get(){return this.hasAttribute('hidden')},set(value){writes++;if(value)this.setAttribute('hidden','');else this.removeAttribute('hidden')}});
 g.q('#tv-next').onclick();assert.equal(g.q('#tv-page').textContent,'2 / 40');assert.equal(writes,50);assert.equal(g.qa('.tv-card:not([hidden])').length,25);
 const originalNode=g.q('[data-save="topic-vocab-star-education-curriculum"]');g.q('#tv-prev').onclick();assert.strictEqual(g.q('[data-save="topic-vocab-star-education-curriculum"]'),originalNode);
 set(g,'#tv-search','no match 873234');assert.equal(g.qa('.tv-card:not([hidden])').length,0);assert(!g.q('#tv-empty').hidden);assert.equal(g.q('#tv-page').textContent,'1 / 1');
 set(g,'#tv-search','');set(g,'#tv-topic','work');assert(g.q('#tv-count').textContent.includes('50 条匹配'));assert(g.qa('.tv-card:not([hidden])').every(n=>n.dataset.tvTopic==='work'));
 set(g,'#tv-topic','all');set(g,'#tv-status','saved');assert(g.q('#tv-count').textContent.startsWith('0 '));
 const star=g.input('topic-vocab-star-education-curriculum',true);change(g,star);assert.equal(g.qa('.tv-card:not([hidden])').length,1);
 g.input(star.dataset.save,false);change(g,star);assert.equal(g.qa('.tv-card:not([hidden])').length,0);
 set(g,'#tv-status','N');const level=g.input('topic-vocab-level-education-curriculum','N');change(g,level);assert.equal(g.qa('.tv-card:not([hidden])').length,1);
 g.input(level.dataset.save,'K');change(g,level);assert.equal(g.qa('.tv-card:not([hidden])').length,0);
 return{indexFrames:frames,pageSize:25,nextPageHiddenWrites:50};
});
check('Independent remote fields are merged; conflicting same-field writes retain the remote value',()=>{
 const g=boot();g.input('reading-q1','local first');
 let remote=JSON.parse(g.storage);remote.fields['reading-q2']='remote other';g.setStorage(JSON.stringify(remote));g.input('reading-q1','local second');
 assert.equal(JSON.parse(g.storage).fields['reading-q2'],'remote other');
 remote=JSON.parse(g.storage);remote.fields['reading-q1']='remote changed';g.setStorage(JSON.stringify(remote));g.input('reading-q1','conflicting local draft');
 assert.equal(JSON.parse(g.storage).fields['reading-q1'],'remote changed');assert(g.q('#save-status').textContent.includes('另一页面'));
});
check('Daily route start, pause and reload retain their original saved record',()=>{
 const g=boot();g.named('daily-study-model-script');g.named('daily-study-script');g.flush();g.route('#guide');g.click(g.q('#ds-start'));
 const state=()=>JSON.parse(g.q('#daily-study-state').value);assert.equal(state().session.status,'active');
 const target=state().session.steps[0].target;g.route('#'+target);assert(g.visible(g.document.getElementById(target)));
 g.click(g.q('#ds-pause'));assert.equal(state().session.status,'paused');
 const saved=g.q('#daily-study-state').value,again=boot({initial:g.storage});assert.equal(again.q('#daily-study-state').value,saved);
});
check('Input files are unchanged by isolated validation',()=>{assert.equal(sha(fs.readFileSync(source)),sha(raw));assert.equal(sha(fs.readFileSync(baseline)),sha(baseRaw));});
const report={source,baseline,sha256:sha(raw),method:'Actual candidate core, navigation, vocabulary, learning and selected daily controllers in Node/linkedom. Synthetic records, controlled rAF and idle fallback queues; no real browser, layout, timing claim or user data.',checks,passed:checks.filter(c=>c.status==='pass').length,total:checks.length};
fs.writeFileSync(output,JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,total:report.total,output},null,2));if(report.passed!==report.total)process.exitCode=1;
