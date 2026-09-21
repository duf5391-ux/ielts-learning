const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {snapshot,settle,jump,base,out}=require('./probe_ui_routes_20260921.cjs');
let browser;const results=[],flows=[],errors=[];
async function main(){
 const seen=new Set([...JSON.parse(fs.readFileSync(path.join(out,'routes.json'))).snapshots,...JSON.parse(fs.readFileSync(path.join(out,'nested.json'))).results,...JSON.parse(fs.readFileSync(path.join(out,'flows.json'))).snapshots].map(s=>s.requested));
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(6000);
 await page.goto(base+'#study',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true'&&window.IELTSRecordStore,{},{timeout:120000});
 const cats=await page.locator('[id]').evaluateAll(items=>items.map(x=>x.id).filter(x=>/^(study|practice)-(listening|reading|writing[12]?|speaking|vocabulary|phrases|shared)-list$/.test(x)));
 for(const id of cats.filter(x=>!seen.has(x))){await jump(page,id);results.push(await snapshot(page,id,'remaining-category'));}
 await jump(page,'guide');await page.locator('[data-ds-minutes="15"]').click();await page.locator('[data-ds-skill="background"]').click();const selected=await page.locator('#ds-plan-reason').innerText();await page.locator('#ds-start').click();await settle(page);const s=await snapshot(page,'background-daily-start','daily-route-conflict');results.push(s);flows.push({name:'直接开始共用背景后的页面归属',selected,actual:s.actual,label:s.topLabel,active:s.activeNav,back:s.controls.filter(x=>x.href&&x.text.startsWith('←')),headings:s.headings.map(x=>x.text)});
 await page.locator('#hs-finish').click();await settle(page);
 await jump(page,'materials');await page.evaluate(()=>scrollTo(0,0));results.push(await snapshot(page,'materials','materials-hidden-check'));await page.screenshot({path:path.join(out,'mobile-materials.png')});
 await page.setViewportSize({width:1440,height:1000});await jump(page,'records');
 for(const legacy of ['writing1','writing2']){await jump(page,'records');const link=page.locator('#records a[href="#'+legacy+'"]').first();if(await link.isVisible()){await link.click();await settle(page);const r=await snapshot(page,legacy,'record-chapter-return');results.push(r);flows.push({name:'学习记录进入'+legacy,actual:r.actual,label:r.topLabel});}}
 fs.writeFileSync(path.join(out,'remaining.json'),JSON.stringify({allCategoryRoutes:cats,results,flows,errors},null,2));console.log(JSON.stringify({allCategoryRoutes:cats.length,remainingProbed:results.length,flows,errors}));await context.close();
}
main().catch(e=>{fs.writeFileSync(path.join(out,'remaining-failure.json'),JSON.stringify({error:e.stack,results,flows,errors},null,2));console.error(e);process.exitCode=1}).finally(async()=>browser&&await browser.close());
