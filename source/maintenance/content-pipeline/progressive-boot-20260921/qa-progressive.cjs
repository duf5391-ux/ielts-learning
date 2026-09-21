'use strict';
// Isolated DOM and loader lifecycle tests. This is not browser/phone performance evidence.
const fs=require('fs'),path=require('path'),assert=require('assert'),vm=require('vm'),crypto=require('crypto');
const {MessageChannel}=require('worker_threads');
const {performance}=require('perf_hooks');
const {parseHTML}=require('D:/IELTS-Work/learning-adjust-20260920/synthetic-tests/node_modules/linkedom');
const root=path.resolve(__dirname,'../..');
const stage=path.resolve(process.argv[2]||path.join(__dirname,'site'));
const sourcePath=path.resolve(process.argv[3]||path.join(__dirname,'source.html'));
const output=path.resolve(process.argv[4]||path.join(__dirname,'qa.json'));
const shell=fs.readFileSync(path.join(stage,'index.html'),'utf8');
const source=fs.readFileSync(sourcePath,'utf8');
const build=JSON.parse(fs.readFileSync(path.join(stage,'progressive-build.json'),'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(stage,build.manifest.path),'utf8'));
const loader=fs.readFileSync(path.join(root,'tools/progressive_loader.js'),'utf8');
const sourceDocument=parseHTML(source).document;
const expectedScripts=[...sourceDocument.querySelectorAll('script')].filter(s=>!['application/json','application/ld+json'].includes(s.type));
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const checks=[];
async function check(name,fn){try{checks.push({name,status:'pass',detail:await fn()});}catch(error){checks.push({name,status:'needs_fix',error:error.stack});}console.log(checks.at(-1).status+' '+name);}
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function canonical(node){
 const attributes=node.attributes?[...node.attributes].map(a=>[a.name,a.value]).sort((a,b)=>a[0].localeCompare(b[0])):[];
 const children=[];
 for(const child of node.childNodes||[]){
  if(child.nodeType===3&&children.at(-1)?.[0]===3)children.at(-1)[1]+=child.textContent;
  else children.push(child.nodeType===3?[3,child.textContent]:canonical(child));
 }
 return node.nodeType===8?[8,node.data]:[node.nodeType,node.localName||'',attributes,children];
}
async function fixture(options={}){
 const {document,window:w}=parseHTML(shell),events={},executed=[],errors=[];
 Object.defineProperty(document,'baseURI',{value:'https://fixture.invalid/ielts-learning/'});
 const location={hash:options.hash||'#pr-jijing-202609-reading-01-v1',pathname:'/ielts-learning/',search:'',reload(){this.reloaded=true}};
 const history={state:{original:true},replaceState(state,_title,url){this.state=state;location.hash=new URL(url,document.baseURI).hash;}};
 const win={addEventListener(type,fn){(events[type]??=new Set()).add(fn)},removeEventListener(type,fn){events[type]?.delete(fn)}};
 const commentProto=Object.getPrototypeOf(Object.getPrototypeOf(document.createComment('x')));
 const originalReplace=commentProto.replaceWith;
 commentProto.replaceWith=function(...nodes){
  const result=originalReplace.apply(this,nodes);
  for(const script of nodes){if(script.localName!=='script')continue;
   assert.equal(document.querySelectorAll('[data-save]').length,3353,'Controllers must see every saved field');
   for(const id of manifest.json_script_ids)assert(document.getElementById(id),'Missing JSON before controller '+id);
   executed.push({id:script.id,code:script.textContent,src:script.getAttribute('src')});
   if(options.controllerErrorAt===executed.length){for(const fn of events.error||[])fn({error:new Error('Synthetic controller exception')});}
   if(script.hasAttribute('src'))setImmediate(()=>options.externalFailure?script.onerror?.():script.onload?.());
  }
  return result;
 };
 const ctx={document,window:win,location,history,NodeFilter:{SHOW_COMMENT:128},performance,MessageChannel,
  setTimeout,clearTimeout,requestAnimationFrame:fn=>setImmediate(()=>fn(performance.now())),TextDecoder,AbortController,
  crypto:crypto.webcrypto,URL,CustomEvent:w.CustomEvent,console:{error:(...args)=>errors.push(args.map(x=>String(x)))},
  fetch:async url=>{
   const rel=decodeURIComponent(new URL(url).pathname.replace(/^\/ielts-learning\//,''));
   const file=path.join(stage,rel);
   if(!fs.existsSync(file))return{ok:false,status:404};
   let data=fs.readFileSync(file);
   if(options.corruptPack&&rel===manifest.packs[0].path)data=Buffer.concat([data,Buffer.from(' ')]);
   return{ok:true,status:200,arrayBuffer:async()=>data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength)};
  }};
 vm.createContext(ctx);
 try{
  vm.runInContext(loader,ctx,{filename:'actual-progressive-loader.js'});
  if(options.duplicateStart)vm.runInContext(loader,ctx,{filename:'duplicate-loader.js'});
  if(options.chooseRoute)document.querySelector(`[data-pb-route="${options.chooseRoute}"]`).dispatchEvent(new w.Event('click',{bubbles:true,cancelable:true}));
  const deadline=Date.now()+20000;
  while(!document.documentElement.dataset.progressiveReady&&document.body.dataset.progressiveState!=='error'){
   if(Date.now()>deadline)throw Error('Loader fixture timeout');await sleep(5);
  }
  return{document,executed,errors,location,history};
 }finally{commentProto.replaceWith=originalReplace;}
}
(async()=>{
 await check('Build is a byte-exact reassembly of the supplied source',()=>{
  assert.equal(build.source_html_sha256,sha(Buffer.from(source)));
  assert.equal(build.source_html_sha256,build.reconstructed_source_sha256);
  assert.equal(build.exact_reassembly,true);assert.equal(build.saved_field_count,3353);
  for(const asset of build.generated_assets){const bytes=fs.readFileSync(path.join(stage,asset.path));assert.equal(sha(bytes),asset.sha256);assert.equal(bytes.length,asset.bytes);}
  return{fields:3353,sourceBytes:build.source_bytes,entryBytes:build.entry_bytes,packs:manifest.packs.length,operations:manifest.operation_count};
 });
 await check('Real loader assembles identical DOM and preserves deep link before ordered one-time activation',async()=>{
  const f=await fixture({duplicateStart:true});
  assert.equal(f.executed.length,expectedScripts.length);assert.equal(f.errors.length,0);
  assert.equal(f.location.hash,'#pr-jijing-202609-reading-01-v1');
  for(let i=0;i<f.executed.length;i++){
   assert.equal(f.executed[i].id,expectedScripts[i].id);assert.equal(f.executed[i].code,expectedScripts[i].textContent);
  }
  for(const item of build.external_controllers){const script=f.document.querySelector(`script[src="${item.path}"]`);assert(script);script.setAttribute('src',item.original_src);script.removeAttribute('integrity');}
  assert.equal(sha(JSON.stringify(canonical(f.document.body))),sha(JSON.stringify(canonical(sourceDocument.body))),'DOM structure/content differs');
  assert.equal(f.document.querySelectorAll('[data-save]').length,3353);
  return{controllers:expectedScripts.length,fields:3353,deepLink:f.location.hash,allBodyContentIdentical:true};
 });
 await check('Early entry selection queues a route without early controller activation',async()=>{
  const f=await fixture({chooseRoute:'#guide'});assert.equal(f.location.hash,'#guide');assert.deepEqual(f.history.state,{original:true});assert.equal(f.executed.length,expectedScripts.length);return{route:f.location.hash};
 });
 await check('Corrupt or mixed-version content leaves a readable retry state and runs no controllers',async()=>{
  const f=await fixture({corruptPack:true});assert.equal(f.executed.length,0);assert.equal(f.document.documentElement.dataset.progressiveReady,undefined);assert.equal(f.document.body.dataset.progressiveState,'error');assert.equal(f.document.getElementById('ielts-progressive-retry').hidden,false);return{controllers:0,retryVisible:true};
 });
 await check('An inline controller exception stops initialization and does not mark the page ready',async()=>{
  const f=await fixture({controllerErrorAt:2});assert.equal(f.executed.length,2);assert.equal(f.document.documentElement.dataset.progressiveReady,undefined);assert.equal(f.document.body.dataset.progressiveState,'error');return{stoppedAfterControllers:2};
 });
 await check('An external dictionary script failure stops dependent controllers',async()=>{
  const firstExternal=expectedScripts.findIndex(s=>s.hasAttribute('src'));
  const f=await fixture({externalFailure:true});assert.equal(f.executed.length,firstExternal+1);assert.equal(f.document.documentElement.dataset.progressiveReady,undefined);assert.equal(f.document.body.dataset.progressiveState,'error');return{stoppedAfterControllers:f.executed.length};
 });
 const report={source:sourcePath,sourceSha256:sha(Buffer.from(source)),entrySha256:sha(Buffer.from(shell)),environment:'Node/linkedom, isolated synthetic execution hooks (not a real browser)',status:checks.every(c=>c.status==='pass')?'pass':'needs_fix',checks};
 fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');if(report.status!=='pass')process.exitCode=1;
})();
