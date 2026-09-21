const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {base,out,jump,settle}=require('./probe_ui_routes_20260921.cjs');
const folder=path.join(out,'full-content');fs.mkdirSync(folder,{recursive:true});
const ledger=[],errors=[];let browser;
async function main(){
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
 page.on('pageerror',e=>errors.push({url:page.url(),message:e.message}));page.setDefaultTimeout(10000);
 await page.goto(base+'#study',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true',null,{timeout:120000});
 const targets=await page.evaluate(()=>{
   const all=new Map();const add=(id,from)=>{if(!id||!document.getElementById(id))return;if(!all.has(id))all.set(id,{id,from:[]});if(!all.get(id).from.includes(from))all.get(id).from.push(from);};
   document.querySelectorAll('main>.panel').forEach(n=>add(n.id,'主面板'));
   document.querySelectorAll('[id]').forEach(n=>{if(/^(study|practice)-.+-list$/.test(n.id))add(n.id,'分类页');});
   JSON.parse(document.querySelector('#learning-adjust-data').textContent).units.forEach(u=>add(u.id,'内容单元'));
   document.querySelectorAll('a[href^="#"]').forEach(a=>add(a.getAttribute('href').slice(1),'页面链接'));
   document.querySelectorAll('[data-go]').forEach(n=>add(n.dataset.go,'导航按钮'));
   const walk=x=>{if(!x||typeof x!=='object')return;for(const[k,v]of Object.entries(x)){if(['target','primerTarget','anchor'].includes(k)&&typeof v==='string')add(v,'每日安排目标');else if(typeof v==='object')walk(v);}};
   walk(JSON.parse(document.querySelector('#daily-study-catalog').textContent));return [...all.values()];
 });
 fs.writeFileSync(path.join(folder,'targets.json'),JSON.stringify(targets,null,2));
 for(const [i,t]of targets.entries()){
   await jump(page,t.id);
   const record=await page.evaluate(({id,from})=>{
     const n=document.getElementById(id),panel=[...document.querySelectorAll('main>.panel')].find(p=>!p.hidden),unit=n?.closest('[data-learning-unit],.ww-unit');
     const root=unit||((n?.matches('section,article,details,aside')&&!n.matches('main>.panel'))?n:panel);
     const visible=e=>e.checkVisibility?e.checkVisibility({checkVisibilityCSS:true,contentVisibilityAuto:true}):!!e.getClientRects().length;
     const label=e=>e.getAttribute('aria-label')||[...(e.labels||[])].map(x=>x.innerText.trim()).join(' / ')||e.placeholder||e.getAttribute('title')||'';
     const controls=[...(root?.querySelectorAll('a,button,input,select,textarea,summary,audio,video')||[])].map(e=>({tag:e.tagName,id:e.id,type:e.type,text:e.innerText?.trim()||'',label:label(e),href:e.getAttribute('href'),save:e.dataset.save,record:e.dataset.record,stop:e.dataset.stop,test:e.dataset.testAnswer,visible:visible(e),disabled:!!e.disabled,required:!!e.required,options:e.tagName==='SELECT'?[...e.options].map(o=>({value:o.value,label:o.label})):undefined}));
     const headings=[...(root?.querySelectorAll('h1,h2,h3,h4')||[])].map(e=>({tag:e.tagName,text:e.textContent.trim(),visible:visible(e)}));
     return {requested:id,from,actual:location.hash,checkedAt:new Date().toISOString(),title:document.title,label:document.querySelector('#current-page-label')?.textContent,panel:panel?.id,contentRoot:root?.id,headings,controls,visibleText:root?.innerText||'',allContent:root?.textContent||'',links:[...(root?.querySelectorAll('a[href]')||[])].map(a=>({text:a.textContent.trim(),href:a.getAttribute('href')})),details:[...(root?.querySelectorAll('details')||[])].map(d=>({id:d.id,title:d.querySelector('summary')?.textContent.trim(),open:d.open,answerGate:d.dataset.answerGate,visible:visible(d)})),saveFields:[...(root?.querySelectorAll('[data-save]')||[])].map(e=>e.dataset.save),images:[...(root?.querySelectorAll('img')||[])].map(e=>({src:e.getAttribute('src'),alt:e.alt,visible:visible(e),complete:e.complete,width:e.naturalWidth})),audio:[...(root?.querySelectorAll('audio')||[])].map(e=>({src:e.getAttribute('src'),sources:[...e.querySelectorAll('source')].map(x=>x.getAttribute('src')),visible:visible(e),controls:e.controls})),viewport:innerWidth,documentWidth:document.documentElement.scrollWidth};
   },t);
   const file=String(i+1).padStart(3,'0')+'-'+t.id.replace(/[^a-zA-Z0-9_-]/g,'_')+'.json';
   fs.writeFileSync(path.join(folder,file),JSON.stringify(record,null,2));
   ledger.push({number:i+1,requested:t.id,from:t.from,actual:record.actual,title:record.label,panel:record.panel,controls:record.controls.length,visibleControls:record.controls.filter(x=>x.visible).length,savedFields:record.saveFields.length,characters:record.allContent.length,file,checkedAt:record.checkedAt,status:'已逐页打开并读取完整DOM内容；未代表所有操作通过'});
   if((i+1)%25===0||i===targets.length-1){fs.writeFileSync(path.join(folder,'ledger.json'),JSON.stringify({expected:targets.length,visited:ledger.length,ledger,errors},null,2));console.log(JSON.stringify({visited:ledger.length,total:targets.length,current:t.id,errors:errors.length}));}
 }
 await context.close();
}
main().catch(e=>{fs.writeFileSync(path.join(folder,'failure.json'),JSON.stringify({error:e.stack,ledger,errors},null,2));console.error(e);process.exitCode=1}).finally(async()=>browser&&await browser.close());
