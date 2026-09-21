const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {parseHTML}=require('D:/IELTS-Work/learning-adjust-20260920/synthetic-tests/node_modules/linkedom');
function fixture({status='active',reminder='',recording=false,restoreActive=false,saveFails=false}={}){
 const {document,window:w}=parseHTML('<html><body><main>'+fs.readFileSync('energy-control.html','utf8')+'<section class="panel" id="reading"><button data-stop'+(recording?'':' disabled')+'>stop</button></section></main><input id="daily-study-state"><button id="ds-pause"></button><button id="ds-next"></button></body></html>');
 Object.defineProperty(w.HTMLSelectElement.prototype,'value',{configurable:true,get(){return this.__value||this.querySelector('option[selected]')?.value||this.querySelector('option')?.value||''},set(value){this.__value=String(value)}});
 w.HTMLElement.prototype.getClientRects=function(){return[1]};w.HTMLElement.prototype.getBoundingClientRect=function(){return{top:20}};w.HTMLElement.prototype.scrollIntoView=function(){};
 const callbacks={},intervals=[],events=[];let now=1000,paused=restoreActive||status==='paused',toggleCalls=0;
 const field=document.getElementById('daily-study-state'),pause=document.getElementById('ds-pause');
 field.value=status?JSON.stringify({session:{id:'session-a',status}}):'';pause.textContent=paused?'继续':'暂停';
 document.getElementById('energy-control-state').value=reminder;
 const win={IELTSEnergyModel:require('./energy-control-model.js'),scrollY:0,addEventListener(t,fn){(callbacks[t]??=[]).push(fn)},dispatchEvent(e){events.push({type:e.type,detail:e.detail});for(const fn of callbacks[e.type]||[])fn(e)}};
 const ctx={window:win,document,location:{hash:'#reading'},Date:{now:()=>now},Event:w.Event,Promise,setTimeout:fn=>{fn();return 1},clearTimeout(){},setInterval:fn=>intervals.push(fn),requestAnimationFrame:fn=>fn()};
 function setDaily(next){const s=field.value?JSON.parse(field.value):{session:{id:'session-a'}};s.session.status=next;field.value=JSON.stringify(s);paused=next==='paused';pause.textContent=paused?'继续':'暂停';field.dispatchEvent(new w.Event('input',{bubbles:true}));}
 pause.addEventListener('click',()=>{toggleCalls++;if(saveFails){paused=true;pause.textContent='继续';field.dispatchEvent(new w.Event('input',{bubbles:true}));return;}setDaily(paused?'active':'paused')});
 vm.runInNewContext(fs.readFileSync('energy-control.js','utf8'),ctx);
 vm.runInNewContext(fs.readFileSync('health-study-bridge.js','utf8'),ctx);
 const settle=async()=>{for(let i=0;i<6;i++)await Promise.resolve()};
 return {document,window:win,events,field,pause,setDaily,settle,energy:()=>win.IELTSEnergyControl.read(),daily:()=>JSON.parse(field.value||'null')?.session,action:id=>document.getElementById('energy-'+id).onclick(),tick(ms){now+=ms;intervals.forEach(fn=>fn())},get toggleCalls(){return toggleCalls},get paused(){return paused}};
}
test('direct rest from idle pauses daily, keeps recording/media untouched, and does not auto-resume after break',async()=>{
 const f=fixture();assert(f.window.IELTSHealthStudyBridge.requestRest());await f.settle();assert.equal(f.energy().mode,'break');assert.equal(f.daily().status,'paused');assert(f.document.body.classList.contains('health-resting'));
 assert.equal(f.energy().bookmark.anchor,'reading');f.tick(180000);await f.settle();assert.equal(f.energy().mode,'ready');assert.equal(f.daily().status,'paused');assert(!f.document.body.classList.contains('health-resting'));assert.equal(f.toggleCalls,1);
 assert(f.window.IELTSHealthStudyBridge.requestRest());await f.settle();assert.equal(f.energy().mode,'break');assert.equal(f.toggleCalls,1);
});
test('recording guard rejects direct rest without starting either clock or pausing daily',async()=>{
 const f=fixture({recording:true});assert.equal(f.window.IELTSHealthStudyBridge.requestRest(),false);await f.settle();assert.equal(f.energy().mode,'idle');assert.equal(f.daily().status,'active');assert.equal(f.toggleCalls,0);assert.match(f.document.getElementById('energy-message').textContent,/先结束/);
});
test('explicit daily continuation ends the current break before continuing study',async()=>{
 const f=fixture();f.window.IELTSHealthStudyBridge.requestRest();await f.settle();assert.equal(f.daily().status,'paused');f.setDaily('active');await f.settle();assert.equal(f.daily().status,'active');assert.equal(f.energy().mode,'idle');assert(!f.document.body.classList.contains('health-resting'));
});
test('a linked daily pause preserves reminder time; explicit daily continuation resumes only that reminder',async()=>{
 const f=fixture();f.action('start');await f.settle();f.tick(2000);f.setDaily('paused');await f.settle();assert.equal(f.energy().mode,'paused');const remaining=f.energy().remaining;f.tick(9000);assert.equal(f.energy().remaining,remaining);f.setDaily('active');await f.settle();assert.equal(f.energy().mode,'running');assert.equal(f.energy().remaining,remaining);
});
test('a reminder started during a paused daily session remains independent',async()=>{
 const f=fixture({status:'paused'});f.action('start');await f.settle();assert.equal(f.energy().mode,'running');assert.equal(f.window.IELTSHealthStudyBridge.read().linkedSessionId,null);f.setDaily('paused');await f.settle();assert.equal(f.energy().mode,'running');
});
test('explicitly restarting Energy during daily pause releases the prior coupling',async()=>{
 const f=fixture();f.action('start');await f.settle();f.setDaily('paused');await f.settle();assert.equal(f.energy().mode,'paused');f.action('start');await f.settle();assert.equal(f.energy().mode,'running');assert.equal(f.window.IELTSHealthStudyBridge.read().linkedSessionId,null);
});
test('manually paused Energy is never resumed by unrelated daily pause/resume',async()=>{
 const f=fixture();f.action('start');await f.settle();f.action('pause');await f.settle();f.setDaily('paused');await f.settle();f.setDaily('active');await f.settle();assert.equal(f.energy().mode,'paused');
});
test('restored active daily state paused by its controller also pauses its restored running reminder',async()=>{
 const M=require('./energy-control-model.js'),reminder=JSON.stringify(M.reduce(M.initial(),{type:'start'},1000));const f=fixture({reminder,restoreActive:true});await f.settle();assert.equal(f.energy().mode,'paused');assert.equal(f.toggleCalls,0);
});
test('a failed daily save still pauses its live controller and never loops or claims a persisted pause',async()=>{
 const f=fixture({saveFails:true});f.window.IELTSHealthStudyBridge.requestRest();await f.settle();assert.equal(f.daily().status,'active');assert(f.paused);assert.equal(f.energy().mode,'break');assert.equal(f.toggleCalls,1);
});
test('ending a linked study pauses the reminder; standalone Energy still works without any daily session',async()=>{
 const f=fixture();f.action('start');await f.settle();f.setDaily('ended');await f.settle();assert.equal(f.energy().mode,'paused');const g=fixture({status:null});g.action('start');await g.settle();assert.equal(g.energy().mode,'running');
});
test('Energy exposes immutable snapshots and documented transition metadata',async()=>{
 const f=fixture();const read=f.energy();read.mode='broken';assert.equal(f.energy().mode,'idle');f.action('start');await f.settle();f.window.IELTSHealthStudyBridge.requestRest();await f.settle();const event=f.events.find(e=>e.detail?.mode==='break');assert.deepEqual({...event.detail},{previousMode:'running',mode:'break',action:'rest',origin:'health-ui'});
});
