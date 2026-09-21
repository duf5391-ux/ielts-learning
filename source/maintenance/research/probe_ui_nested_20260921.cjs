const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {snapshot,settle,jump,shot,base,out}=require('./probe_ui_routes_20260921.cjs');
let browser;const results=[],errors=[],journeys=[];
async function main(){
 const inventory=JSON.parse(fs.readFileSync(path.join(out,'inventory.json')));
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(5000);
 await page.goto(base+'#workspace',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true'&&window.IELTSRecordStore,{},{timeout:120000});
 const already=new Set([...inventory.units.map(u=>u.id),...inventory.panels.map(p=>p.id)]);
 const nested=[...new Set(inventory.links.filter(x=>x.exists&&!already.has(x.href.slice(1))&&!/^(study|practice)-.+-list$/.test(x.href.slice(1))).map(x=>x.href.slice(1)))];
 for(const id of nested){await jump(page,id);results.push(await snapshot(page,id,'nested-route'));}
 const priority=['vocabulary-review','sentence-learning','topical-vocabulary','lookup-history','resource-update','study-vocabulary-list','study-phrases-list','study-shared-list','study-reading-list','study-writing-list','practice-writing-list'];
 for(const id of priority){if(!await page.locator('[id="'+id+'"]').count())continue;await jump(page,id);results.push(await snapshot(page,id,'desktop-target'));await shot(page,id,'desktop');}
 for(const to of ['vocabulary-review','sentence-learning','writing-workbench','library','course-window','plan']){
  await jump(page,'workspace');await page.locator('#workspace a[href="#'+to+'"]').click();await settle(page);const s=await snapshot(page,to,'workspace-click');journeys.push({from:'workspace',to,actual:s.actual,label:s.topLabel,active:s.activeNav,visibleHeadings:s.headings.map(h=>h.text),scrollY:s.scrollY});
  await page.screenshot({path:path.join(out,'click-'+to+'.png')});
 }
 await page.setViewportSize({width:390,height:844});
 for(const id of ['vocabulary-review','sentence-learning','writing-workbench','library','study-vocabulary-list','study-writing-list','practice-writing-list','topical-vocabulary']){
  await jump(page,id);results.push(await snapshot(page,id,'mobile-target'));await shot(page,id,'mobile');
  if(id==='vocabulary-review'||id==='sentence-learning'){await page.locator('#'+id).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'mobile-focused-'+id+'.png')});}
 }
 // A realistic populated word list, in a separate synthetic-only browser context.
 const seeded=await browser.newContext({viewport:{width:390,height:844}});
 await seeded.addInitScript(()=>localStorage.setItem('ielts-finished-book-v1',JSON.stringify({version:1,fields:{'lookup-history-v1':JSON.stringify([{key:'sustainable',term:'sustainable',meaning:'可持续的；能够持续的',favorite:true,lastAt:'2020-01-01T00:00:00Z',context:'We need a sustainable approach to learning.'},{key:'curriculum',term:'curriculum',meaning:'课程体系',favorite:true,lastAt:'2020-01-01T00:00:00Z'}])},snapshots:{}})));
 const second=await seeded.newPage();await second.goto(base+'#vocabulary-review',{waitUntil:'domcontentloaded',timeout:120000});await second.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true',{},{timeout:120000});await settle(second);results.push(await snapshot(second,'vocabulary-review','mobile-synthetic-list'));await second.locator('#vocabulary-review').scrollIntoViewIfNeeded();await second.screenshot({path:path.join(out,'mobile-vocabulary-populated.png')});
 await second.locator('#vr-start').click();await settle(second);results.push(await snapshot(second,'vocabulary-review','mobile-synthetic-review'));await second.locator('#vr-stage').scrollIntoViewIfNeeded();await second.screenshot({path:path.join(out,'mobile-vocabulary-reviewing.png')});
 fs.writeFileSync(path.join(out,'nested.json'),JSON.stringify({nestedCount:nested.length,errors,journeys,results},null,2));console.log(JSON.stringify({nestedCount:nested.length,snapshots:results.length,errors,journeys,output:out}));await context.close();await seeded.close();
}
main().catch(e=>{fs.writeFileSync(path.join(out,'nested-failure.json'),JSON.stringify({error:e.stack,results,journeys,errors},null,2));console.error(e);process.exitCode=1}).finally(async()=>browser&&await browser.close());
