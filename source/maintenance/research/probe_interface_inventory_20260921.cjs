// Read-only inventory, sequential navigation; isolated browser, never personal browser state.
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {base,out,jump,settle,snapshot}=require('./probe_ui_routes_20260921.cjs');
const entries=['完整词汇来源库.html','扩展资料目录.html','本地词典.html','词频与原文证据.html','case-assets/reading-gap-origins-birds-original.html','原始参考/precise-listening-part-4-questions.html','机经资料/jijing-20260920/index.html','机经资料/jijing-20260920/writing-task2.html','机经资料/jiufen-reviewed-20260921/index.html'];
const results=[],errors=[],surfaces=[];let browser;
async function read(page,requested,kind){return page.evaluate(({requested,kind})=>{
 const visible=e=>e.checkVisibility?e.checkVisibility({checkVisibilityCSS:true,contentVisibilityAuto:true}):!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
 return {requested,kind,url:location.href,title:document.title,checkedAt:new Date().toISOString(),headings:[...document.querySelectorAll('h1,h2,h3')].filter(visible).map(e=>e.innerText).filter(Boolean),controls:[...document.querySelectorAll('a,button,input,textarea,select,summary')].filter(visible).map(e=>({tag:e.tagName,id:e.id,text:(e.innerText||e.getAttribute('aria-label')||e.placeholder||'').trim().slice(0,160),href:e.getAttribute('href'),type:e.type,disabled:e.disabled})),text:document.body.innerText.slice(0,30000),width:document.documentElement.scrollWidth,viewport:innerWidth};
 },{requested,kind});}
async function main(){
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push({url:page.url(),message:e.message}));
 for(const [i,entry] of entries.entries()){
   const response=await page.goto(base+entry,{waitUntil:'domcontentloaded',timeout:120000});await page.waitForTimeout(600);
   const r=await read(page,entry,'standalone-page');r.httpStatus=response.status();results.push(r);
   await page.screenshot({path:path.join(out,'inventory-external-'+String(i+1).padStart(2,'0')+'.png')});
   console.log(JSON.stringify({entry,status:r.httpStatus,title:r.title,controls:r.controls.length}));
 }
 await page.goto(base+'#study',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true',null,{timeout:120000});
 for(const id of ['course-window','materials','my-vocabulary-materials','my-topic-materials','learning-projects','guide','records','library','development']){
   await jump(page,id);surfaces.push(await read(page,id,'functional-page'));
   console.log(JSON.stringify({entry:'#'+id,controls:surfaces.at(-1).controls.length}));
 }
 await jump(page,'study');await page.locator('#lookup-open').click();await settle(page);surfaces.push(await read(page,'word-lookup','opened-popup'));await page.locator('#lookup-close').click();
 await jump(page,'sentence-learning');await page.locator('#sentence-learning [data-open-sentence]').click();await settle(page);surfaces.push(await read(page,'sentence-popup','opened-popup'));await page.locator('#sentence-close').click();
 surfaces.push(await page.evaluate(()=>({requested:'dynamic-dialog-inventory',kind:'available-dialogs',items:[...document.querySelectorAll('dialog,[role="dialog"],[role="alertdialog"]')].map(e=>({tag:e.tagName,id:e.id,heading:e.querySelector('h1,h2,h3')?.textContent,text:e.textContent.trim().slice(0,2500),controls:[...e.querySelectorAll('button,input,textarea,select')].map(n=>({tag:n.tagName,id:n.id,text:n.innerText||n.placeholder||n.getAttribute('aria-label'),type:n.type}))}))})));
 fs.writeFileSync(path.join(out,'interface-inventory.json'),JSON.stringify({scope:'Sequential actual browser page opens, existing production version',results,surfaces,errors},null,2));await context.close();console.log(JSON.stringify({pages:results.length,surfaces:surfaces.length,errors}));
}
main().catch(e=>{fs.writeFileSync(path.join(out,'interface-inventory-failure.json'),JSON.stringify({error:e.stack,results,surfaces,errors},null,2));console.error(e);process.exitCode=1}).finally(async()=>browser&&await browser.close());
