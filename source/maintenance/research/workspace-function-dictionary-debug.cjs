const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const {parseHTML}=require('D:/IELTS-Work/learning-adjust-20260920/synthetic-tests/node_modules/linkedom');
const sourcePath='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const raw=fs.readFileSync(sourcePath),html=raw.toString('utf8');
const checks=[];function check(name,fn){try{const detail=fn();checks.push({name,status:'pass',detail});}catch(e){checks.push({name,status:'needs_fix',error:e.stack,actual:e.actual,expected:e.expected});}}
function fixture({initial=null,allStorage=null,quota=false,hash='#study'}={}){
 const {document,window:w}=parseHTML(html),callbacks={},timers=[],rafs=[];let storage=initial,reloads=0,downloads=[];const stores=allStorage?{...allStorage}:{'ielts-finished-book-v1':initial}; for(const n of document.querySelectorAll('[type="checkbox"]'))n.checked=n.hasAttribute('checked');
 Object.defineProperty(w.HTMLSelectElement.prototype,'value',{configurable:true,get(){if(this.__syntheticValue!==undefined)return this.__syntheticValue;const o=[...this.querySelectorAll('option')];return o.find(x=>x.selected)?.getAttribute('value')??o[0]?.getAttribute('value')??o[0]?.textContent??''},set(v){this.__syntheticValue=String(v)}});
 w.HTMLElement.prototype.scrollIntoView=function(){};w.HTMLElement.prototype.focus=function(){};w.HTMLElement.prototype.getClientRects=function(){return[{}]};w.HTMLElement.prototype.getBoundingClientRect=function(){return {top:1,bottom:2,left:1,right:2}};w.HTMLElement.prototype.pause=function(){};
 const loc={hash,reload(){reloads++}},win={addEventListener(t,fn){(callbacks[t]??=[]).push(fn)},scrollTo(){},confirm:()=>true,scrollY:0,innerHeight:900,innerWidth:1200};
 const localStorage={getItem(k){return stores[k]??null},setItem(k,v){if(quota)throw Error('QuotaExceededError');stores[k]=String(v);if(k==='ielts-finished-book-v1')storage=v}};
 const ctx={window:win,document,location:loc,localStorage,navigator:{},Blob,URL,Event:w.Event,CustomEvent:w.CustomEvent,DOMParser:w.DOMParser,crypto,alert(){},Date,JSON,console,confirm:()=>true,setTimeout:fn=>{timers.push(fn);return timers.length},clearTimeout(){},setInterval:fn=>{timers.push(fn);return timers.length},clearInterval(){},requestAnimationFrame:fn=>rafs.push(fn),TextEncoder,AbortController};
 ctx.URL=class extends URL{};ctx.URL.createObjectURL=b=>{downloads.push(b);return 'blob:synthetic'};ctx.URL.revokeObjectURL=()=>{};ctx.performance={now:()=>1000};ctx.fetch=async()=>{throw Error('network-disabled-in-test')};win.getSelection=()=>({isCollapsed:true,toString:()=>''});ctx.HashChangeEvent=w.Event;win.dispatchEvent=e=>{for(const fn of callbacks[e.type]||[])fn(e)};win.location=loc;win.localStorage=localStorage;vm.createContext(ctx);
 const importer=document.querySelector('#import-state'); const oldAdd=importer.addEventListener.bind(importer); importer.addEventListener=(type,fn)=>{if(type==='change')importer.syntheticChange=fn;else oldAdd(type,fn)};
 const scripts=[...document.querySelectorAll('script')];
 const exec=(text,name)=>vm.runInContext(text,ctx,{filename:name});
 const append=document.head.appendChild.bind(document.head);document.head.appendChild=n=>{const out=append(n);if(n.tagName==='SCRIPT'&&n.src){const p=require('url').fileURLToPath(n.src);try{exec(fs.readFileSync(p,'utf8'),p);n.onload?.();}catch(e){n.onerror?.(e);}}return out};
 const run=i=>{const n=scripts[i];document.currentScript=n;if(n.hasAttribute('src')){const p=require('path').resolve(require('path').dirname(sourcePath),n.getAttribute('src'));n.src=require('url').pathToFileURL(p).href;return exec(fs.readFileSync(p,'utf8'),p)}return exec(n.textContent,'actual-script-'+i+'.js')};
 const click=n=>{if(!n)throw Error('Missing click target');if(n.disabled)throw Error('Disabled click target');return n.dispatchEvent(new w.Event('click',{bubbles:true}));};
 const input=(key,value)=>{const n=document.querySelector(`[data-save="${key}"]`);if(n.type==='checkbox')n.checked=value;else n.value=value;n.dispatchEvent(new w.Event('input',{bubbles:true}));return n};
 const flush=()=>{let c=0;while(rafs.length&&c++<100)rafs.shift()()};
 const route=hash=>{loc.hash=hash;for(const fn of callbacks.hashchange||[])fn();flush()};
 return{callbacks,document,window:win,ctx,run,click,input,flush,route,get storage(){return stores['ielts-finished-book-v1']},get allStorage(){return {...stores}},get reloads(){return reloads},downloads,setQuota(v){quota=v}};
}
function boot(options={}){
 const f=fixture(options);for(const [i,n] of [...f.document.querySelectorAll('script')].entries())if(n.type!=='application/json')f.run(i);
 const scripts=[...f.document.querySelectorAll('script')];f.named=id=>f.run(scripts.findIndex(n=>n.id===id));
 f.flush();
 f.q=s=>f.document.querySelector(s);f.qa=s=>[...f.document.querySelectorAll(s)];f.data=JSON.parse(f.q('#learning-adjust-data').textContent);
 f.state=()=>JSON.parse(JSON.parse(f.storage).fields['learning-adjust-state']);
 f.visible=n=>{for(let p=n;p;p=p.parentElement)if(p.hidden||p.hasAttribute('data-la-focus-hidden')||p.classList?.contains('ui-filtered')||p.classList?.contains('la-hidden-legacy'))return false;return true};
 return f;
}

async function test(name,fn){try{const detail=await fn();checks.push({name,status:'pass',detail});}catch(e){checks.push({name,status:'needs_fix',error:e.stack});} console.log(name,checks.at(-1).status);}
(async()=>{const f=boot();const status=await f.window.IELTSLookup.collect('sustainable','The city needs sustainable transport.');console.log(JSON.stringify({status,result:f.q('#lookup-result').textContent,engine:Object.keys(f.window.IELTSLocalDictionary),history:f.window.IELTSLookup.getHistory()},null,2));try{console.log(await f.window.IELTSLocalDictionary.lookup('sustainable'))}catch(e){console.log(e.stack)}})();