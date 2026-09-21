// Run the real daily and Energy controllers from a candidate in isolated storage.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const path=require('path');
const source=path.resolve(process.argv[2]||'research/health-study-bridge-candidate-20260920.html').replace(/\\/g,'/');
const harness=fs.readFileSync('qa_navigation_ui_final.cjs','utf8').split('const f=boot();')[0]
 .replace('D:/IELTS-Work/learning-adjust-20260920/开始学习-ui-final.html',source)
 .replace('return{callbacks,document','return{timers,callbacks,document');
const {boot,raw}=new Function('require',harness+'\nreturn {boot,raw};')(require);
(async()=>{
 const f=boot(),checks=[];let clock=1000;f.ctx.performance.now=()=>clock;
 f.named('energy-control-model-script');f.named('energy-control-script');
 f.named('daily-study-model-script');f.named('daily-study-script');f.named('health-study-bridge-script');f.flush();
 const settle=async()=>{for(let i=0;i<6;i++)await Promise.resolve()};
 const daily=()=>JSON.parse(f.q('#daily-study-state').value).session;
 const energy=()=>f.window.IELTSEnergyControl.read();
 f.route('#guide');f.click(f.q('#ds-start'));f.route('#'+daily().steps[0].target);await settle();
 assert.equal(daily().status,'active');assert(f.window.IELTSHealthStudyBridge.requestRest());await settle();
 assert.equal(daily().status,'paused');assert.equal(energy().mode,'break');
 const pausedClock=f.q('#ds-clock').textContent;clock+=2000;f.timers.at(-1)();assert.equal(f.q('#ds-clock').textContent,pausedClock);
 checks.push('Direct rest pauses real daily controller and stops its clock');
 f.click(f.q('#ds-pause'));await settle();assert.equal(daily().status,'active');assert.equal(energy().mode,'idle');
 checks.push('Explicit real daily continuation ends break without starting a new Energy block');
 f.q('#energy-start').onclick();await settle();f.click(f.q('#ds-pause'));await settle();assert.equal(energy().mode,'paused');
 f.click(f.q('#ds-pause'));await settle();assert.equal(energy().mode,'running');
 checks.push('Real daily pause and explicit continuation control only their linked reminder');
 const stored=JSON.parse(f.storage).fields;assert.equal(JSON.parse(stored['daily-study-state']).session.status,'active');assert.equal(JSON.parse(stored['energy-control-state']).mode,'running');
 checks.push('Both controllers keep using the original record fields');
 const result={source,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'Candidate actual controllers in Node/linkedom; isolated storage, no browser profile, layout, microphone or exam session',passed:checks.length,checks};
 fs.writeFileSync('research/health-study-integrated-tests-20260920.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(error=>{console.error(error);process.exitCode=1});
