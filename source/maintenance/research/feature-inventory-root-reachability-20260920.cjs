const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const {parseHTML}=require('D:/IELTS-Work/learning-adjust-20260920/synthetic-tests/node_modules/linkedom');
const sourcePath='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const raw=fs.readFileSync(sourcePath),html=raw.toString('utf8');
const checks=[];function check(name,fn){try{const detail=fn();checks.push({name,status:'pass',detail});}catch(e){checks.push({name,status:'needs_fix',error:e.stack,actual:e.actual,expected:e.expected});}}
function fixture({initial=null,quota=false,hash='#study'}={}){
 const {document,window:w}=parseHTML(html),callbacks={},timers=[],rafs=[];let storage=initial,reloads=0,downloads=[]; for(const n of document.querySelectorAll('[type="checkbox"]'))n.checked=n.hasAttribute('checked');
 Object.defineProperty(w.HTMLSelectElement.prototype,'value',{configurable:true,get(){if(this.__syntheticValue!==undefined)return this.__syntheticValue;const o=[...this.querySelectorAll('option')];return o.find(x=>x.selected)?.getAttribute('value')??o[0]?.getAttribute('value')??o[0]?.textContent??''},set(v){this.__syntheticValue=String(v)}});
 w.HTMLElement.prototype.scrollIntoView=function(){};w.HTMLElement.prototype.focus=function(){};w.HTMLElement.prototype.getClientRects=function(){return[{}]};w.HTMLElement.prototype.getBoundingClientRect=function(){return {top:1,bottom:2,left:1,right:2}};w.HTMLElement.prototype.pause=function(){};
 const loc={_hash:hash,get hash(){return this._hash},set hash(v){this._hash=String(v)?'#'+String(v).replace(/^#/,''):''},reload(){reloads++}},win={addEventListener(t,fn){(callbacks[t]??=[]).push(fn)},scrollTo(){},confirm:()=>true,scrollY:0,innerHeight:900,innerWidth:1200};
 const localStorage={getItem(k){return k==='ielts-finished-book-v1'?storage:null},setItem(k,v){if(quota)throw Error('QuotaExceededError');if(k==='ielts-finished-book-v1')storage=v}};
 const ctx={window:win,document,location:loc,localStorage,navigator:{},Blob,URL:{createObjectURL(b){downloads.push(b);return'blob:synthetic'},revokeObjectURL(){}},Event:w.Event,Date,JSON,console,confirm:()=>true,setTimeout:fn=>{timers.push(fn);return timers.length},clearTimeout(){},setInterval:fn=>{timers.push(fn);return timers.length},clearInterval(){},requestAnimationFrame:fn=>rafs.push(fn),TextEncoder,AbortController};
 ctx.performance={now:()=>1000};ctx.HashChangeEvent=w.Event;win.dispatchEvent=e=>{for(const fn of callbacks[e.type]||[])fn(e)};win.location=loc;win.localStorage=localStorage;vm.createContext(ctx);
 const importer=document.querySelector('#import-state'); const oldAdd=importer.addEventListener.bind(importer); importer.addEventListener=(type,fn)=>{if(type==='change')importer.syntheticChange=fn;else oldAdd(type,fn)};
 const scripts=[...document.querySelectorAll('script')];
 const run=i=>vm.runInContext(scripts[i].textContent,ctx,{filename:'actual-script-'+i+'.js'});
 const click=n=>n.dispatchEvent(new w.Event('click',{bubbles:true}));
 const input=(key,value)=>{const n=document.querySelector(`[data-save="${key}"]`);if(n.type==='checkbox')n.checked=value;else n.value=value;n.dispatchEvent(new w.Event('input',{bubbles:true}));return n};
 const flush=()=>{let c=0;while(rafs.length&&c++<100)rafs.shift()()};
 const route=hash=>{loc.hash=hash;for(const fn of callbacks.hashchange||[])fn();flush()};
 return{callbacks,document,window:win,ctx,run,click,input,flush,route,get storage(){return storage},get reloads(){return reloads},downloads,setQuota(v){quota=v}};
}
function boot(options={}){
 const f=fixture(options);f.run(0);f.run(1);f.run(2);f.run(12);
 const scripts=[...f.document.querySelectorAll('script')];f.named=id=>f.run(scripts.findIndex(n=>n.id===id));
 f.named('learning-adjust-model-script');f.named('learning-adjust-script');f.flush();
 f.q=s=>f.document.querySelector(s);f.qa=s=>[...f.document.querySelectorAll(s)];f.data=JSON.parse(f.q('#learning-adjust-data').textContent);
 f.state=()=>JSON.parse(JSON.parse(f.storage).fields['learning-adjust-state']);
 f.visible=n=>{for(let p=n;p;p=p.parentElement)if(p.hidden||p.hasAttribute('data-la-focus-hidden')||p.classList?.contains('ui-filtered')||p.classList?.contains('la-hidden-legacy'))return false;return true};
 return f;
}

const f=boot();
const queue=['study','practice','tests','workspace'],visited=new Set(),unitIds=new Set(f.data.units.map(u=>u.id)),knownPanels=new Set(f.qa('main>.panel').map(n=>n.id)),paths=new Map(queue.map(x=>[x,[x]])),unitPaths={},external={},edges=[];
function visible(n){if(!f.visible(n))return false;for(let p=n;p;p=p.parentElement){if(p.style?.display==='none')return false;}return true;}
function canTraverse(id){return /^(study|practice)-.*-list$/.test(id)||knownPanels.has(id)||['vocabulary-review','sentence-learning'].includes(id);}
while(queue.length){const requested=queue.shift();if(visited.has(requested))continue;visited.add(requested);f.route('#'+requested);let actual=f.ctx.location.hash.slice(1),limit=0;while(actual!==requested&&limit++<3){f.route('#'+actual);if(f.ctx.location.hash.slice(1)===actual)break;actual=f.ctx.location.hash.slice(1);}const route=f.ctx.location.hash.slice(1);const shown=f.qa('a[href],[data-go]').filter(visible);let count=0;for(const a of shown){const href=a.getAttribute('href')||(a.dataset.go?'#'+a.dataset.go:'');if(!href)continue;count++;if(href[0]!=='#'){external[href]??=[...(paths.get(requested)||[]),href];continue;}const target=href.slice(1);edges.push({from:requested,to:target,label:a.textContent.trim().slice(0,100)});if(unitIds.has(target)){unitPaths[target]??=[...(paths.get(requested)||[]),target];continue;}if(canTraverse(target)&&!visited.has(target)){if(!paths.has(target))paths.set(target,[...(paths.get(requested)||[]),target]);queue.push(target);}}console.log('walked',requested,'actual',route,'visibleLinks',count);}
const missing=f.data.units.filter(u=>!unitPaths[u.id]);
const out={sourcePath,sha256:crypto.createHash('sha256').update(raw).digest('hex'),method:'Actual navigation controllers in Node/linkedom, BFS from four main navigation roots through visible anchors, catalogs, workspace and non-unit panels. A unit counts reachable only when a visible link is discovered by root traversal; arbitrary deep links are not supplied. CSS rendering, external pages and actual browser were not tested.',visited:[...visited],units:f.data.units.length,reachableUnits:Object.keys(unitPaths).length,missing,unitPaths,external,edges};
fs.writeFileSync('C:/Users/Admin1/Documents/ChatGPT/ielts/research/feature-inventory-root-reachability-20260920.json',JSON.stringify(out,null,2));console.log(JSON.stringify({visited:out.visited,units:out.units,reachableUnits:out.reachableUnits,missing:out.missing,sourcePath,sha256:out.sha256},null,2));
