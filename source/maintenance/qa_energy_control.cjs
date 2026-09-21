const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const M=require('./energy-control-model.js');

test('explicit start, pause and resume preserve remaining time',()=>{
 let s=M.initial();assert.equal(s.mode,'idle');
 s=M.reduce(s,{type:'start'},1000);assert.equal(s.dueAt,901000);
 s=M.reduce(s,{type:'pause'},121000);assert.equal(s.remaining,780000);
 s=M.reduce(s,{type:'start'},500000);assert.equal(s.dueAt,1280000);
 assert.equal(M.left(s,560000),720000);
});
test('refresh after the deadline reminds without starting another block',()=>{
 let s=M.reduce(M.initial(),{type:'start'},1000);
 s=M.read(JSON.stringify(s),9999999);assert.equal(s.mode,'due');
 assert.equal(M.reduce(s,{type:'start'},10000000).mode,'due');
 s=M.reduce(s,{type:'rest'},10000000);assert.equal(s.mode,'break');
 s=M.read(JSON.stringify(s),11000000);assert.equal(s.mode,'ready');
 assert.equal(s.dueAt,0);assert.equal(M.tick(s,12000000).mode,'ready');
});
test('snooze is one explicit three-minute extension, stop retains position',()=>{
 let s=M.reduce(M.initial(),{type:'start'},0);s=M.tick(s,900000);
 s=M.reduce(s,{type:'snooze'},1000000);assert.equal(s.dueAt,1180000);
 s=M.reduce(s,{type:'bookmark',bookmark:{hash:'#reading',anchor:'reading-unit',y:123}},1010000);
 s=M.reduce(s,{type:'stop'},1020000);assert.equal(s.mode,'idle');assert.equal(s.bookmark.anchor,'reading-unit');
});
test('settings only change between blocks; invalid persisted state is rejected',()=>{
 let s=M.reduce(M.initial(),{type:'settings',minutes:5,rest:2},0);s=M.reduce(s,{type:'start'},0);
 s=M.reduce(s,{type:'settings',minutes:25,rest:5},1000);assert.equal(s.minutes,5);assert.equal(s.rest,2);
 for (const raw of ['{','null','[]',JSON.stringify({...s,minutes:999}),JSON.stringify({...s,remaining:-1}),JSON.stringify({...s,bookmark:{hash:'x',anchor:'x',y:'bad'}})]) assert.throws(()=>M.read(raw,0));
});

// An isolated synthetic DOM fixture tests the adapter, without opening the blocked learning page.
function fixture(raw='',activeRecording=false){
 const events={},nodes={},timers=[];let writes=0;
 class El{
   constructor(id=''){this.id=id;this.value='';this.textContent='';this.hidden=false;this.disabled=false;this.children=[];this.listeners={};this.dataset={};this.parentElement=null;}
   append(n){this.children.push(n);} replaceChildren(){this.children=[];}
   addEventListener(k,fn){this.listeners[k]=fn;} dispatchEvent(){writes++;}
   querySelector(){return this.detail||null;} contains(){return false;} getClientRects(){return [1];} getBoundingClientRect(){return {top:20};}
   querySelectorAll(){return [];} scrollIntoView(){} closest(){return this.panel;}
 }
 const names=['control','control-state','summary','minutes','rest','start','pause','take-rest','snooze','stop','return','message','storage','reminder'];
 for(const n of names)nodes['energy-'+n]=new El('energy-'+n);
 nodes['energy-control'].detail=new El();nodes['energy-control-state'].value=raw;
 const stop=new El();stop.disabled=!activeRecording;
 const panel=new El('reading');panel.hidden=false;panel.tagName='SECTION';panel.panel=panel;
 nodes.reading=panel;nodes['save-status']=new El();nodes['save-status'].textContent='文字已保存在当前浏览器';
 const document={getElementById:id=>nodes[id],createElement:()=>new El(),querySelectorAll:sel=>sel==='[data-stop]'?[stop]:sel==='main>.panel'?[panel]:[],addEventListener:(k,fn)=>events[k]=fn};
 const window={IELTSEnergyModel:M,scrollY:20,addEventListener:(k,fn)=>events[k]=fn};
 const context={window,document,location:{hash:'#reading'},Date,Event:class{},setInterval:fn=>timers.push(fn),setTimeout:fn=>fn(),clearTimeout(){},requestAnimationFrame:fn=>fn()};
 vm.runInNewContext(fs.readFileSync('energy-control.js','utf8'),context);
 return {nodes,stop,events,timers,get writes(){return writes;},state(){return JSON.parse(nodes['energy-control-state'].value);}};
}
test('active recording blocks rest; finishing it allows rest without manipulating media',()=>{
 const f=fixture('',true);f.nodes['energy-start'].onclick();assert.equal(f.state().mode,'running');
 f.nodes['energy-take-rest'].onclick();assert.equal(f.state().mode,'running');assert.match(f.nodes['energy-message'].textContent,/先结束/);
 f.stop.disabled=true;f.nodes['energy-take-rest'].onclick();assert.equal(f.state().mode,'break');assert.equal(f.state().bookmark.anchor,'reading');
});
test('corrupt reminder record remains untouched while a temporary timer can run',()=>{
 const f=fixture('{broken');f.nodes['energy-start'].onclick();
 assert.equal(f.nodes['energy-control-state'].value,'{broken');assert.equal(f.writes,0);assert.equal(f.nodes['energy-storage'].hidden,false);
});
test('restored paused session and global backup input',()=>{
 let s=M.reduce(M.initial(),{type:'start'},Date.now());s=M.reduce(s,{type:'pause'},Date.now());
 const f=fixture(JSON.stringify(s));assert.equal(f.nodes['energy-start'].textContent,'继续这段学习');
 f.nodes['energy-start'].onclick();assert.equal(f.state().mode,'running');assert.ok(f.writes>0);
});
test('storage failure is visible; reminder does not automatically repeat',()=>{
 const f=fixture();f.nodes['save-status'].textContent='当前未能保存';f.nodes['energy-start'].onclick();
 assert.equal(f.nodes['energy-storage'].hidden,false);
});
