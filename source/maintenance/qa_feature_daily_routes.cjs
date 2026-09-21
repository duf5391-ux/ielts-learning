const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const live='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const harness=fs.readFileSync('qa_navigation_ui_final.cjs','utf8').split('const f=boot();')[0].replace("D:/IELTS-Work/learning-adjust-20260920/开始学习-ui-final.html",live);
const {boot,raw}=new Function('require',harness+'\nreturn {boot,raw};')(require);
const checks=[];
for(const minutes of [15,30,60])for(const skill of ['listening','reading','writing1','writing2','speaking','vocabulary','background']){
 const item={minutes,skill,status:'pass'};
 try{
  const f=boot({hash:'#guide'});f.named('daily-study-model-script');f.named('daily-study-script');f.flush();
  const read=()=>JSON.parse(JSON.parse(f.storage).fields['daily-study-state']);
  f.click(f.q('[data-ds-minutes="'+minutes+'"]'));f.click(f.q('[data-ds-skill="'+(skill.startsWith('writing')?'writing':skill)+'"]'));
  if(skill.startsWith('writing'))f.click(f.q('[data-ds-writing="'+skill+'"]'));
  const navigate=()=>f.route('#'+f.ctx.location.hash.replace(/^#/,''));
  f.click(f.q('#ds-start'));navigate();
  assert.equal(read().session.status,'active');assert.equal(read().session.minutes,minutes);assert.deepEqual(read().session.skills,[skill]);
  item.targets=[];item.firstAnswerGateChecked=false;
  while(read().session.status==='active'){
   const current=read().session,step=current.steps[current.index],target=f.document.getElementById(step.target);
   assert(f.visible(target),'Hidden daily content '+step.target);item.targets.push(step.target);
   f.click(f.q('#ds-next'));
   if(read().session.index===current.index&&read().session.status==='active'){
    // Full first-attempt chapters must refuse to advance into hidden explanations.
    assert(f.q('#ds-message').textContent.includes('保存首次作答'));
    const chapter=target.closest('main>.panel');const freeze=chapter.querySelector('[data-freeze]');assert(freeze);
    for(const n of chapter.querySelectorAll('.first-stage [data-save]'))f.input(n.dataset.save,n.type==='checkbox'?true:'synthetic answer');
    f.click(freeze);assert(freeze.disabled);f.click(f.q('#ds-next'));item.firstAnswerGateChecked=true;
   }
   if(read().session.status==='active')assert.equal(read().session.index,current.index+1);
   navigate();
  }
  assert.equal(read().session.status,'completed');assert.equal(read().session.completed.length,4);
  assert(f.visible(f.q('#ds-completed')));f.click(f.q('[data-ds-feedback="retry"]'));assert.equal(read().session.feedback,'retry');
  assert.equal(read().history.at(-1).feedback,'retry');
 }catch(e){item.status='needs_fix';item.error=e.stack;}
 checks.push(item);console.log(JSON.stringify(item));
}
const out={source:live,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'Actual daily, core, UI and navigation scripts in Node/linkedom with isolated storage. User-confirmed step completion, no media capture or real browser.',checks,passed:checks.filter(c=>c.status==='pass').length,total:checks.length};
fs.writeFileSync('research/feature-daily-routes-20260920.json',JSON.stringify(out,null,2));console.log(JSON.stringify({passed:out.passed,total:out.total}));if(out.passed!==out.total)process.exitCode=1;
