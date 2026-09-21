const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=path.join(__dirname,'ui-route-probe-20260921');fs.mkdirSync(out,{recursive:true});
const base='https://duf5391-ux.github.io/ielts-learning/';
const errors=[],snapshots=[],journeys=[];let browser;
async function settle(page){await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.waitForTimeout(100);}
async function snapshot(page,requested,kind){return page.evaluate(({requested,kind})=>{
 const visible=e=>!!e&&!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
 const rect=e=>{const b=e.getBoundingClientRect();return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)}};
 const panels=[...document.querySelectorAll('main > .panel')].filter(visible);
 const headings=panels.flatMap(p=>[...p.querySelectorAll('h1,h2,h3')].filter(visible).map(e=>({tag:e.tagName,text:e.textContent.trim(),...rect(e)})));
 const controls=panels.flatMap(p=>[...p.querySelectorAll('a,button,input,textarea,select,summary')].filter(visible).map(e=>({tag:e.tagName,id:e.id,text:(e.innerText||e.getAttribute('aria-label')||e.placeholder||'').trim().slice(0,140),href:e.getAttribute('href'),go:e.dataset.go,disabled:!!e.disabled,...rect(e)})));
 const hiddenVisible=[...document.querySelectorAll('[hidden]')].filter(visible).slice(0,15).map(e=>({tag:e.tagName,id:e.id,class:e.className,text:e.textContent.trim().slice(0,140),...rect(e)}));
 return {requested,kind,actual:location.hash,title:document.title,topLabel:document.getElementById('current-page-label')?.textContent,activeNav:[...document.querySelectorAll('#workspace-navigation [aria-current]')].map(e=>({go:e.dataset.go,label:e.textContent.trim()})),panels:panels.map(p=>({id:p.id,owner:p.dataset.laOwner,title:p.dataset.laTitle,...rect(p)})),headings,controls,hiddenVisible,bodyWidth:document.documentElement.scrollWidth,viewport:innerWidth,scrollY,visibleText:panels.map(p=>p.innerText).join('\n').slice(0,50000),overflow:controls.filter(e=>e.x<-2||e.x+e.w>innerWidth+2).slice(0,15)};
 },{requested,kind});}
async function jump(page,id){await page.evaluate(id=>{location.hash=id;},id);await settle(page);}
async function shot(page,id,prefix){await page.evaluate(()=>scrollTo(0,0));await settle(page);await page.screenshot({path:path.join(out,prefix+'-'+id+'.png')});}
async function clickJourney(page,from,selector,label){await jump(page,from);const locator=page.locator(selector).first();await locator.scrollIntoViewIfNeeded();await locator.click();await settle(page);const s=await snapshot(page,label,'clicked-journey');snapshots.push(s);journeys.push({from,selector,to:s.actual,label,topLabel:s.topLabel,activeNav:s.activeNav,visiblePanels:s.panels.map(p=>p.id)});return s;}
async function main(){
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 const response=await page.goto(base+'#study',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true'&&window.IELTSRecordStore,{},{timeout:120000});
 const inventory=await page.evaluate(()=>{
  const data=JSON.parse(document.getElementById('learning-adjust-data').textContent);
  return {topNav:[...document.querySelectorAll('#workspace-navigation [data-go]')].map(e=>({go:e.dataset.go,label:e.textContent.trim()})),panels:[...document.querySelectorAll('main>.panel')].map(e=>({id:e.id,owner:e.dataset.laOwner,title:e.dataset.laTitle,h1:e.querySelector('h1')?.textContent,h2:e.querySelector('h2')?.textContent})),units:data.units.map(u=>({id:u.id,mode:u.mode,skill:u.skill,title:u.title,part:u.part})),links:[...document.querySelectorAll('a[href^="#"]')].map(a=>({href:a.getAttribute('href'),text:a.textContent.trim().slice(0,120),panel:a.closest('main>.panel')?.id,exists:!!document.getElementById(a.getAttribute('href').slice(1))})),saveFields:document.querySelectorAll('[data-save]').length};
 });
 fs.writeFileSync(path.join(out,'inventory.json'),JSON.stringify({url:base,checkedAt:new Date().toISOString(),homepage_sha256:crypto.createHash('sha256').update(await response.body()).digest('hex'),...inventory},null,2));
 const priority=['study','practice','tests','workspace','development','vocabulary-review','sentence-workbench','writing-workbench','library','guide','plan','learning-projects','course-window','topical-vocabulary','review','records'];
 const ids=new Set(inventory.panels.map(p=>p.id));
 for(const id of priority.filter(x=>ids.has(x))){await jump(page,id);snapshots.push(await snapshot(page,id,'desktop-entry'));await shot(page,id,'desktop');}
 const categories=[...new Set(inventory.links.map(x=>x.href.slice(1)).filter(x=>/^(study|practice)-.+-list$/.test(x)))];
 for(const id of [...new Set([...inventory.panels.map(p=>p.id),...categories])]){await jump(page,id);snapshots.push(await snapshot(page,id,'desktop-route'));}
 for(const u of inventory.units){await jump(page,u.id);const s=await snapshot(page,u.id,'learning-unit');snapshots.push({...s,visibleText:s.visibleText.slice(0,1300),controls:s.controls.filter(c=>c.href).slice(0,12),headings:s.headings.slice(0,8)});}
 for(const item of [
 ['workspace','a[href="#vocabulary-review"]','工作台 → 单词表'],
 ['workspace','a[href="#sentence-workbench"]','工作台 → 句子本'],
 ['workspace','a[href="#writing-workbench"]','工作台 → 写作工作台'],
 ['study','a[href="#study-reading-list"]','学习 → 阅读'],
 ['study','a[href="#study-writing-list"]','学习 → 写作'],
 ['practice','a[href="#practice-writing-list"]','练习 → 写作']
 ]){try{await clickJourney(page,...item);}catch(e){journeys.push({from:item[0],selector:item[1],label:item[2],error:e.message.slice(0,350)});}}
 await page.setViewportSize({width:390,height:844});
 for(const id of priority.filter(x=>ids.has(x))){await jump(page,id);snapshots.push(await snapshot(page,id,'mobile-entry'));await shot(page,id,'mobile');}
 fs.writeFileSync(path.join(out,'routes.json'),JSON.stringify({errors,journeys,snapshots},null,2));
 const summary={url:base,checkedAt:new Date().toISOString(),panels:inventory.panels.length,categories:categories.length,learningUnits:inventory.units.length,routesProbed:snapshots.length,deadAnchors:inventory.links.filter(x=>!x.exists),pageErrors:errors,journeys,overflows:snapshots.filter(s=>s.bodyWidth>s.viewport+2).map(s=>({route:s.requested,kind:s.kind,width:s.bodyWidth,viewport:s.viewport,controls:s.overflow})),hiddenVisible:snapshots.filter(s=>s.hiddenVisible.length).map(s=>({route:s.requested,kind:s.kind,nodes:s.hiddenVisible})),multipleVisiblePanels:snapshots.filter(s=>s.panels.length!==1).map(s=>({route:s.requested,kind:s.kind,panels:s.panels})),ownerAnomalies:snapshots.filter(s=>s.activeNav.length!==1).map(s=>({route:s.requested,kind:s.kind,active:s.activeNav}))};
 fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2));console.log(JSON.stringify({panels:summary.panels,categories:summary.categories,learningUnits:summary.learningUnits,routesProbed:summary.routesProbed,deadAnchors:summary.deadAnchors.length,pageErrors:errors.length,overflows:summary.overflows.length,hiddenVisible:summary.hiddenVisible.length,multipleVisiblePanels:summary.multipleVisiblePanels.length,ownerAnomalies:summary.ownerAnomalies.length,output:out}));await context.close();
}
module.exports={snapshot,settle,jump,shot,base,out};
if(require.main===module)main().catch(e=>{fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:e.stack,errors,snapshots,journeys},null,2));console.error(e);process.exitCode=1}).finally(async()=>{if(browser)await browser.close()});
