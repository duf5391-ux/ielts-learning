const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const live='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const candidate='D:/IELTS-Work/learning-adjust-20260920/开始学习-feature-checked.html';
let harness=fs.readFileSync('research/workspace-function-audit.cjs','utf8').split('async function test(')[0];
harness=harness.replace("const sourcePath='"+live+"'","const sourcePath='"+candidate+"'")
 .replace('require(\'path\').dirname(sourcePath)','require(\'path\').dirname('+JSON.stringify(live)+')');
const {boot,raw}=new Function('require',harness+'\nreturn {boot,raw};')(require);
const checks=[];
function check(name,fn){try{checks.push({name,status:'pass',detail:fn()});}catch(e){checks.push({name,status:'needs_fix',error:e.stack});}console.log(name,checks.at(-1).status);}
const f=boot();
const set=(sel,value)=>{const n=f.q(sel);n.value=value;n.dispatchEvent(new f.ctx.Event('input',{bubbles:true}));};
const navigate=()=>f.route('#'+f.ctx.location.hash.replace(/^#/,''));
check('All current controllers initialize together after the three-script patch',()=>{
 for(const key of ['IELTSLookup','IELTSVocabularyReview','IELTSCourseWindow','IELTSEnergyModel','IELTSLearning','IELTSDailyStudy'])assert(f.window[key],key);
 assert.equal(f.q('#writing-workbench').dataset.wwReady,'true');
});
check('Imported vocabulary and topic material can be saved, found from classification, opened and returned',()=>{
 const result=[];
 for(const [type,category,panel,list] of [['vocabulary','vocabulary','my-vocabulary-materials','vocabulary-additions'],['topic','shared','my-topic-materials','topic-additions']]){
  f.route('#materials');set('#material-kind',type);set('#material-mode','single');set('#material-title','QA custom '+type);set('#material-content','Original imported '+type+' content.');
  f.click(f.q('#material-preview-button'));f.click(f.q('#material-commit'));
  f.route('#study-'+category+'-list');const link=f.q('#la-study-location a[href="#'+panel+'"]');assert(f.visible(link));
  f.route(link.getAttribute('href'));assert(f.visible(f.q('#'+list)));assert.equal(f.qa('main>.panel:not([hidden])').length,1);
  assert.equal(f.q('[data-go="study"]').getAttribute('aria-current'),'page');
  const card=f.qa('#'+list+' .added-material-card').find(n=>n.textContent.includes('QA custom '+type));assert(card);f.click(card.querySelector('button'));navigate();
  assert(f.visible(f.q('#material-reader')));assert(f.q('#material-reader').textContent.includes('Original imported '+type+' content.'));
  f.route('#'+list);assert(f.visible(f.q('#'+list)));const back=f.q('#'+panel+' a[href="#study-'+category+'-list"]');assert(f.visible(back));f.route(back.getAttribute('href'));assert(f.visible(f.q('#study')));
  result.push({type,panel,list});
 }
 return result;
});
check('Dedicated vocabulary material list resets old usage/search filters and does not expose other panels',()=>{
 f.route('#usage-cards');set('#vocab-search','no matches anywhere');f.route('#my-vocabulary-materials');
 assert(f.visible(f.q('#vocabulary-additions')));assert(f.q('#vocabulary-addition-list').textContent.includes('QA custom vocabulary'));
 assert.equal(f.qa('main>.panel:not([hidden])').length,1);assert(!f.visible(f.q('#learn-189')));
});
check('Optional course time controls persist 5/10/15 minutes without hiding or blocking tasks',()=>{
 f.route('#course-window');assert(!f.q('[data-cw-optional]').open);assert(f.visible(f.q('[data-cw-answer]')));
 f.q('[data-cw-optional]').open=true;const count=f.qa('[data-cw-task]').length;
 for(const minutes of [5,10,15]){f.click(f.q('[data-cw-budget="'+minutes+'"]'));assert.equal(f.window.IELTSCourseWindow.getState().progress[0].minutes,minutes);assert.equal(f.q('[data-cw-budget="'+minutes+'"]').getAttribute('aria-pressed'),'true');assert(f.q('[data-cw-optional]').open);assert.equal(f.qa('[data-cw-task]').length,count);}
 return {budgets:[5,10,15],taskCount:count};
});
check('Course recommendation remains optional, follows a saved attempt and opens its suggested content',()=>{
 const c=f.window.IELTSCourseWindow.getCourses()[0],answer=f.q('[data-cw-answer]'),id=answer.dataset.cwAnswer,t=c.stages.flatMap(s=>s.tasks).find(t=>t.id===id);
 set('[data-cw-answer="'+id+'"]',t.type==='choice'?(t.options.find(o=>o.id!==t.answer)||t.options[0]).id:'Independent answer');f.click(f.q('[data-cw-submit="'+id+'"]'));
 assert(f.q('.cw-reference'));const b=f.q('[data-cw-recommendation]');assert(b);const stage=b.dataset.cwRecommendation;f.click(b);
 assert.equal(f.q('[data-cw-stage="'+stage+'"]').getAttribute('aria-current'),'step');assert.equal(f.window.IELTSCourseWindow.getState().progress[0].stageId,stage);
 return {suggestedStage:stage};
});
check('Fresh isolated reload preserves imported material lists and the chosen course budget',()=>{
 const g=boot({allStorage:f.allStorage});for(const list of ['vocabulary-additions','topic-additions']){g.route('#'+list);assert(g.visible(g.q('#'+list)));assert(g.q('#'+list).textContent.includes('QA custom'));}
 g.route('#course-window');assert.equal(g.window.IELTSCourseWindow.getState().progress[0].minutes,15);assert.equal(g.q('[data-cw-budget="15"]').getAttribute('aria-pressed'),'true');assert.equal(g.window.IELTSCourseWindow.getState().attempts.length,1);
});
const out={source:candidate,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'All actual controllers in isolated Node/linkedom, including local dictionary scripts; no real browser, user storage or microphone.',checks,passed:checks.filter(c=>c.status==='pass').length,total:checks.length};
fs.writeFileSync('research/feature-repairs-tests-20260920.json',JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));if(out.passed!==out.total)process.exitCode=1;
