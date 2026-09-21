'use strict';
// Isolated Node VM behavior checks; no browser, profile, or real user storage.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..'),dist=path.join(root,'web-publication','dist');
const out=path.join(__dirname,'health-ui-web-evidence-20260920');
const source=fs.readFileSync(path.join(out,'script-0.js'),'utf8');
function sandbox(shared,options={}){
 const events=new Map(),nodes=new Map();
 function node(id){if(!nodes.has(id))nodes.set(id,{id,textContent:'',hidden:false,dataset:{},type:'text',value:'',children:[],classList:{contains:()=>true,add(){}},addEventListener(type,fn){this[type]=fn},querySelector(){return node(id+'-button')},append(){},setAttribute(){},removeAttribute(){},closest(){return null}});return nodes.get(id)}
 const localStorage={getItem:k=>shared.has(k)?shared.get(k):null,setItem(k,v){if(options.quota)throw Error('QuotaExceededError');shared.set(k,String(v))}};
 const document={querySelector:s=>node(s),querySelectorAll:()=>[],getElementById:()=>null,body:{append(){},classList:{add(){}}},createElement:tag=>node('created-'+tag),addEventListener(type,fn){if(!events.has(type))events.set(type,[]);events.get(type).push(fn)},dispatchEvent(){}};
 const context={document,localStorage,location:{hash:'#study',reload(){}},navigator:{},setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,clearInterval(){},URL,Blob,Event:class{},Date,console,confirm:()=>true};
 context.window=context;context.addEventListener=()=>{};context.scrollTo=()=>{};
 vm.createContext(context);vm.runInContext(source,context);
 return {input(key,value){const target={dataset:{save:key},value,type:'text'};for(const f of events.get('input')||[])f({target})},status:()=>node('#save-status').textContent};
}
const key='ielts-finished-book-v1',shared=new Map();
const a=sandbox(shared),b=sandbox(shared);
a.input('writing1-essay','tab-A new draft');
const afterA=JSON.parse(shared.get(key));
b.input('reading-q1','tab-B answer');
const afterB=JSON.parse(shared.get(key));
const corruptRaw='{broken',corrupt=new Map([[key,corruptRaw]]),c=sandbox(corrupt);c.input('reading-q1','preserve input');
const valid=JSON.stringify({version:1,fields:{'reading-q1':'old answer'},snapshots:{}}),quota=new Map([[key,valid]]),q=sandbox(quota,{quota:true});q.input('reading-q1','new answer');
const storage={
 initial_save_persists:afterA.fields['writing1-essay']==='tab-A new draft',
 corrupt_original_preserved:corrupt.get(key)===corruptRaw,
 corrupt_save_status:c.status(),
 quota_original_preserved:quota.get(key)===valid,
 quota_save_status:q.status(),
 concurrent_tabs:{after_tab_a:afterA.fields,after_tab_b:afterB.fields,tab_a_status:a.status(),tab_b_status:b.status(),lost_tab_a_field:!Object.hasOwn(afterB.fields,'writing1-essay')}
};
async function dictionary(){
 const loaded=[],dictionaryRoot=path.join(dist,'local-dictionary');let context;
 const appendChild=element=>{queueMicrotask(()=>{try{const url=new URL(element.src),relative=decodeURIComponent(url.pathname).replace(/^\/local-dictionary\//,'');const file=path.resolve(dictionaryRoot,relative);assert(file.startsWith(dictionaryRoot+path.sep));loaded.push(relative);vm.runInContext(fs.readFileSync(file,'utf8'),context);element.onload?.();}catch(error){element.onerror?.(error)}})};
 context={URL,setTimeout,clearTimeout,document:{currentScript:{src:'https://audit.invalid/local-dictionary/dictionary-engine.js'},createElement:()=>({remove(){}}),head:{appendChild}},console};context.window=context;vm.createContext(context);
 vm.runInContext(fs.readFileSync(path.join(dictionaryRoot,'dictionary-engine.js'),'utf8'),context);
 const api=context.IELTSLocalDictionary,manifest=await api.ready();
 const missing=manifest.shards.filter(k=>!fs.existsSync(path.join(dictionaryRoot,'shards',k+'.js')));
 const terms={};for(const term of ['research','Went','children','sustainable','take into account']){const value=await api.lookup(term);terms[term]={normalized:value.term,entry_count:value.entries.length,bases:value.bases};}
 return {manifest_shards:manifest.shards.length,manifest_entry_count:manifest.entryCount,missing_shards:missing,terms,loaded_files:loaded};
}
(async()=>{const result={boundary:'Synthetic Node VM, no browser execution or user records',storage,dictionary:await dictionary()};fs.writeFileSync(path.join(out,'isolated-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));})();
