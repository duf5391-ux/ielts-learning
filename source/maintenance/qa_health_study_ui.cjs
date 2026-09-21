// Actual candidate controllers; no browser profile, microphone, layout or formal-file writes.
const fs=require('fs'),assert=require('assert'),crypto=require('crypto'),path=require('path');
const source=path.resolve(process.argv[2]||'health-interaction-qa/candidate.html').replace(/\\/g,'/');
const harness=fs.readFileSync('qa_navigation_ui_final.cjs','utf8').split('function boot(')[0]
 .replace('D:/IELTS-Work/learning-adjust-20260920/开始学习-ui-final.html',source);
const {fixture,raw}=new Function('require',harness+'\nreturn {fixture,raw};')(require);
const settle=async()=>{for(let i=0;i<6;i++)await Promise.resolve()};
async function boot(){
 const f=fixture(),scripts=[...f.document.querySelectorAll('script')];
 f.q=s=>f.document.querySelector(s);
 f.named=id=>{const index=scripts.findIndex(n=>n.id===id);assert(index>=0,'Missing script '+id);f.run(index)};
 // Mutation observers and layout are irrelevant to explicit button actions in this test.
 f.ctx.MutationObserver=class{observe(){}disconnect(){}};
 if(scripts.some(n=>n.id==='record-concurrency-model-script'))f.named('record-concurrency-model-script');
 const core=scripts.findIndex(n=>n.textContent.includes('/* RECORD-SAFETY-20260919 */'));
 assert(core>=0,'Missing real record controller');f.run(core);
 for(const id of ['energy-control-model-script','energy-control-script','daily-study-model-script','daily-study-script','health-study-bridge-script','health-study-ui-script'])f.named(id);
 assert(scripts.find(n=>n.id==='health-study-ui-script').textContent.includes('再收工。'),'Candidate lacks recording guard');
 f.daily=()=>JSON.parse(f.q('#daily-study-state').value).session;
 f.energy=()=>f.window.IELTSEnergyControl.read();
 f.route('#guide');f.click(f.q('#ds-start'));f.route('#'+f.daily().steps[0].target);f.flush();
 f.q('#energy-start').onclick();await settle();assert.equal(f.daily().status,'active');assert.equal(f.energy().mode,'running');
 return f;
}
(async()=>{
 const checks=[],f=await boot();
 const stop=f.q('[data-stop]');assert(stop);stop.disabled=false;
 const before={daily:f.q('#daily-study-state').value,energy:JSON.stringify(f.energy()),route:f.ctx.location.hash,storage:f.storage};
 f.click(f.q('#hs-finish'));await settle();
 assert.equal(f.q('#daily-study-state').value,before.daily);assert.equal(JSON.stringify(f.energy()),before.energy);assert.equal(f.ctx.location.hash,before.route);assert.equal(f.storage,before.storage);
 const status=f.q('.hs-rest-status');assert(!status.hidden);assert.match(status.textContent,/先结束并下载录音，再收工/);
 checks.push('Active recording blocks finish without changing daily, route, reminder or persisted record; status is visible');
 stop.disabled=true;f.click(f.q('#hs-finish'));await settle();assert.equal(f.daily().status,'ended');assert.equal(f.ctx.location.hash.replace(/^#/,''),'guide');assert.equal(f.energy().mode,'idle');
 checks.push('After recording stops, finish commits ended and returns to Guide with Energy idle');
 const g=await boot(),events=[];g.window.addEventListener('ielts-energy-change',e=>events.push(e.detail));
 const unchanged={route:g.ctx.location.hash,storage:g.storage,remaining:g.energy().remaining};g.setQuota(true);g.click(g.q('#hs-finish'));await settle();
 assert.notEqual(g.daily().status,'ended');assert.equal(g.ctx.location.hash,unchanged.route);assert.equal(g.storage,unchanged.storage);
 assert.equal(g.energy().mode,'paused');assert(g.energy().remaining>0&&g.energy().remaining<=unchanged.remaining);assert(!events.some(e=>e.action==='stop'));
 assert.equal(g.q('#ds-pause').textContent,'继续');assert(!g.q('#daily-study-dock .ds-message').hidden);assert.match(g.q('#daily-study-dock .ds-message').textContent,/未成功/);
 checks.push('Failed daily commit stays on material, preserves stored record, exposes failure and only pauses the linked reminder; no stop/reset');
 const result={source,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'Actual candidate core/daily/Energy/bridge/UI in Node/linkedom with isolated storage; recording simulated by real enabled stop control; no microphone or layout engine',passed:checks.length,checks};
 fs.writeFileSync('research/health-study-ui-tests-20260920.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(error=>{console.error(error);process.exitCode=1});
