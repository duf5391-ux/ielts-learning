// Read-only audit: run the fixed formal-page snapshot with synthetic storage.
const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const root='C:/Users/Admin1/Documents/ChatGPT/ielts/';
const snapshot=root+'research/health-ui-local-snapshot-3b4ee9cdce99.html';
let harness=fs.readFileSync(root+'qa_navigation_ui_final.cjs','utf8').split('const f=boot();')[0]
 .replace('D:/IELTS-Work/learning-adjust-20260920/开始学习-ui-final.html',snapshot)
 .replace('return{callbacks,document','return{timers,callbacks,document');
const {boot,raw}=new Function('require',harness+'\nreturn {boot,raw};')(require);
const checks=[];
function check(name,fn){try{checks.push({name,status:'confirmed',detail:fn()});}catch(e){checks.push({name,status:'inconclusive',error:e.stack});}}
const f=boot();
let clock=1000;f.ctx.performance.now=()=>clock;
f.named('energy-control-model-script');f.named('energy-control-script');
f.named('daily-study-model-script');f.named('daily-study-script');f.flush();
const energy=()=>JSON.parse(f.q('#energy-control-state').value);
const daily=()=>JSON.parse(f.q('#daily-study-state').value);
check('Healthy-study control exists globally and has accessible native controls',()=>{
 const host=f.q('#energy-control');assert.equal(host.parentElement.tagName,'MAIN');
 assert.equal(host.getAttribute('aria-label'),'学习与休息提醒');
 for(const id of ['energy-start','energy-pause','energy-take-rest','energy-stop','energy-return'])assert.equal(f.q('#'+id).tagName,'BUTTON');
 assert.equal(f.q('#energy-message').getAttribute('aria-live'),'polite');
 return {parent:'main',outsideIndividualPanels:true};
});
check('Energy rest does not pause an active daily session',()=>{
 f.q('#energy-start').onclick();f.route('#guide');f.click(f.q('#ds-start'));f.route('#'+daily().session.steps[0].target);
 assert.equal(daily().session.status,'active');
 f.q('#energy-take-rest').onclick();assert.equal(energy().mode,'break');
 const before=f.q('#ds-clock').textContent;clock+=1000;f.timers.at(-1)();
 assert.equal(daily().session.status,'active');assert.notEqual(f.q('#ds-clock').textContent,before);
 assert.equal(f.q('#ds-pause').textContent,'暂停');
 return {energy:energy().mode,daily:daily().session.status,clockBefore:before,clockAfter:f.q('#ds-clock').textContent,dailyAction:f.q('#ds-pause').textContent};
});
check('Daily pause leaves an independently started Energy timer running',()=>{
 f.q('#energy-stop').onclick();f.q('#energy-start').onclick();assert.equal(energy().mode,'running');
 f.click(f.q('#ds-pause'));assert.equal(daily().session.status,'paused');assert.equal(energy().mode,'running');
 return {energy:energy().mode,daily:daily().session.status};
});
check('Formal reading plan still ends with method recall rather than concrete material close reading',()=>{
 const catalog=JSON.parse(f.q('#daily-study-catalog').textContent),r=catalog.find(c=>c.skill==='reading');
 assert.equal(r.stages.length,4);assert.equal(r.stages.at(-1).title,'回顾今天的判断方法');
 return {title:r.stages.at(-1).title,instruction:r.stages.at(-1).instruction,targets:r.stages.at(-1).target};
});
check('Existing AI close reading and later vocabulary/sentence review remain distinct',()=>{
 const material=f.q('#reading-case-rd-c21-ai-1');
 assert(material.textContent.includes('答后精读'));assert(material.textContent.includes('no shortage of'));assert(material.textContent.includes('While'));
 for(const id of ['vocabulary-review','sentence-learning'])assert(f.q('[data-workspace-shortcut="'+id+'"] a'));
 return {closeReadingMaterial:'reading-case-rd-c21-ai-1',laterReview:['vocabulary-review','sentence-learning']};
});
check('Four primary routes expose the matching panel and current-page state',()=>{
 assert.deepEqual(f.qa('#workspace-navigation nav [data-go]').map(n=>n.textContent.trim()),['学习','练习','测试','工作区']);
 for(const id of ['study','practice','tests','workspace']){f.route('#'+id);assert.equal(f.q('main>.panel:not([hidden])').id,id);assert.equal(f.q('[data-go="'+id+'"]').getAttribute('aria-current'),'page');}
 return {routes:4};
});
check('Writing picker keeps Task 1 and Task 2 inside Writing',()=>{
 f.route('#study-writing-list');assert.deepEqual(f.qa('#la-study-cards h2').map(n=>n.textContent),['Task 1','Task 2']);
 f.route('#study-writing1-list');assert(f.qa('#la-study-cards [data-catalog-unit]').every(n=>f.data.units.find(u=>u.id===n.dataset.catalogUnit).skill==='writing1'));
 assert(f.q('#la-study-location a[href="#study-writing-list"]'));return {picker:['Task 1','Task 2']};
});
check('AI material opens alone and returns to the matching practice category',()=>{
 const id='reading-case-rd-c21-ai-1';f.route('#'+id);assert(f.visible(f.q('#'+id)));
 const back=f.q('.la-focus-nav a');assert.equal(back.getAttribute('href'),'#practice-reading-list');f.route(back.getAttribute('href'));
 assert(f.q('#la-practice-cards [data-catalog-unit="'+id+'"]'));return {material:id,back:'#practice-reading-list'};
});
check('Workspace vocabulary and sentence shortcuts return through their owning Records panel',()=>{
 for(const id of ['vocabulary-review','sentence-learning']){f.route('#workspace');const a=f.q('[data-workspace-shortcut="'+id+'"] a');assert(f.visible(a));f.route(a.getAttribute('href'));
 const target=f.q('#'+id),panel=target.closest('main>.panel');assert(f.visible(target));assert.equal(panel.id,'records');assert.equal(f.q('[data-go="workspace"]').getAttribute('aria-current'),'page');
 const back=panel.querySelector('a[href="#workspace"]');assert(f.visible(back));f.route(back.getAttribute('href'));assert(f.visible(f.q('#workspace')));}
 return {shortcuts:['vocabulary-review','sentence-learning'],returnOwner:'records'};
});
const result={sourcePath:snapshot,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'Actual formal-page scripts in Node/linkedom, synthetic storage and clock; no browser profile, user records or layout engine.',checks};
fs.writeFileSync(root+'research/health-ui-local-extra-checks-20260920.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
if(checks.some(c=>c.status==='inconclusive'))process.exitCode=1;
