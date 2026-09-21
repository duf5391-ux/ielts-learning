const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const main='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const qa=path.join(__dirname,'authentic-case-qa');
(async()=>{
 const data=JSON.parse(fs.readFileSync(path.join(path.dirname(main),'authentic-cases.json'),'utf8'));
 const audit=JSON.parse(fs.readFileSync(path.join(__dirname,'audit-content-remediated-20260919.json'),'utf8'));
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:1000},acceptDownloads:true}),page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(15000);
 const frame=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const route=async id=>{await page.evaluate(id=>location.hash=id,id);await frame();};
 const check=async(name,fn)=>{try{checks.push({name,pass:true,detail:await fn()});}catch(e){checks.push({name,pass:false,error:e.message});}};
 try{
  await page.goto(pathToFileURL(main).href+'#reading-case-bank');await frame();
  await check('three database banks render all cases and audit labels',async()=>{
   assert.equal(await page.locator('.case-bank').count(),3);assert.equal(await page.locator('.exam-case').count(),data.cases.length);
   for(const item of audit.items){const target=page.locator(`[data-audit-target="${item.id}"]`);assert.equal(await target.count(),1,item.id);assert.equal(await target.locator(`[data-content-audit="${item.id}"].content-audit-badge`).textContent(),item.status);}
   assert.equal(await page.locator('.authentic-supplement').count(),38);
   const mappings=JSON.parse(fs.readFileSync(path.join(__dirname,'case-framework-links.json'),'utf8'));
   for(const mapping of mappings){
    const unit=page.locator(mapping.targetSelector);assert.equal(await unit.count(),1,mapping.targetSelector);
    for(const cid of mapping.caseIds){const c=data.cases.find(c=>c.id===cid),id=cid.startsWith(c.skill+'-')?cid:c.skill+'-case-'+cid;assert.equal(await unit.locator(`.framework-case-links a[href="#${id}"]`).count(),1,cid);}
   }
   return {...audit.summary,frameworksWithAdditionalCaseLinks:mappings.length};
  });
  const first=page.locator('#reading-case-bank .exam-case').first();const firstID=await first.getAttribute('id');
  await check('answers hidden until every question has an attempted answer',async()=>{
   await route(firstID);assert(await first.evaluate(e=>e.open));assert(await first.locator('.case-feedback').isHidden());await first.locator('[data-case-submit]').click();assert(await first.locator('.case-feedback').isHidden());
   const fields=first.locator('[data-case-answer]');for(let i=0;i<await fields.count();i++)await fields.nth(i).fill(i?'不确定，需对照限定范围':'CASE QA FIRST');
   await first.locator('[data-case-submit]').click();assert(await first.locator('.case-feedback').isVisible());assert(await first.locator('[data-case-done]').isChecked());assert(await fields.first().getAttribute('readonly')!==null);
   await first.locator('[data-save$="-revision"]').fill('QA：按真实证据修订');await frame();
   await page.screenshot({path:path.join(qa,'desktop-case-feedback.png'),animations:'disabled'});
  });
  await check('case work and original notes persist and export together',async()=>{
   await route('reading');await page.locator('[data-save="reading-q1"]').fill('ORIGINAL QA');await route('reading-tech-locate');await page.locator('[data-save="resource-note-tech-locate"]').fill('OLD NOTE QA');await frame();await page.reload();await frame();await route(firstID);
   assert.equal(await first.locator('[data-case-answer]').first().inputValue(),'CASE QA FIRST');assert.equal(await first.locator('[data-save$="-revision"]').inputValue(),'QA：按真实证据修订');assert(await first.locator('.case-feedback').isVisible());
   await route('records');const pending=page.waitForEvent('download');await page.locator('[data-export="json"]').click();const download=await pending;const dest=path.join(qa,'isolated-case-records.json');await download.saveAs(dest);const saved=JSON.parse(fs.readFileSync(dest,'utf8'));assert.equal(saved.fields['reading-q1'],'ORIGINAL QA');assert.equal(saved.fields['resource-note-tech-locate'],'OLD NOTE QA');const firstKey=await first.locator('[data-case-answer]').first().getAttribute('data-save');assert.equal(saved.fields[firstKey],'CASE QA FIRST');return {exportedFields:Object.keys(saved.fields).length};
  });
  await check('type search, progress filters and next unattempted case work',async()=>{
   await route('reading-case-bank');const bank=page.locator('#reading-case-bank');await bank.locator('[data-case-filter]').selectOption('done');assert.equal(await bank.locator('.exam-case:visible').count(),1);
   await bank.locator('[data-case-filter]').selectOption('new');assert.equal(await bank.locator('.exam-case:visible').count(),data.stats.reading.cases-1);
   await bank.locator('[data-case-next]').click();assert(await bank.locator('.exam-case:not([hidden])[open]').count()>0);
   await bank.locator('[data-case-search]').fill('NO_RESULTS_48943');assert(await bank.locator('[data-case-empty]').isVisible());await bank.locator('[data-case-search]').fill('');await bank.locator('[data-case-filter]').selectOption('all');
   const t=bank.locator('[data-case-type]').nth(1);const type=await t.getAttribute('data-case-type');await t.click();assert.equal(await bank.locator('.exam-case:visible').count(),data.stats.reading.by_type[type]);await bank.locator('[data-case-type="全部"]').click();
  });
  await check('writing original figures and draft before model work',async()=>{
   await route('writing1-case-bank');const unit=page.locator('#writing1-case-bank .exam-case').first();await unit.locator('summary').first().click();assert(await unit.locator('.case-feedback').isHidden());await unit.locator('[data-case-answer]').fill('The main feature is supported by the original chart. This is my own initial draft.');await unit.locator('[data-case-submit]').click();assert(await unit.locator('.case-model').isVisible());
   const imgs=page.locator('.case-figure');for(let i=0;i<await imgs.count();i++){await imgs.nth(i).evaluate(e=>{e.loading='eager';});}await page.waitForFunction(()=>[...document.querySelectorAll('.case-figure')].every(i=>i.complete&&i.naturalWidth>0));
   await page.screenshot({path:path.join(qa,'desktop-writing-case.png'),animations:'disabled'});
  });
  await check('one resource directory and original questions preserved',async()=>{
   await route('library');assert.equal(await page.locator('.sidebar [data-go="resource-update"]').count(),0);assert.equal(await page.locator('.sidebar [data-go="library"]').count(),1);assert.equal(await page.locator('.res-card').count(),44);assert.equal(await page.locator('.qt-unit').count(),14);assert.equal(await page.locator('.qt-originals img').count(),21);assert.equal(await page.locator('.qt-body [data-save]').count(),25);
   await page.locator('#res-search').fill('原题');await page.locator('#res-search').fill('');await page.locator('#qt-search').fill('cash flow');assert.equal(await page.locator('.qt-results li:not([hidden])').count(),1);await page.locator('#qt-search').fill('');
  });
  await check('normal color and mobile layout across cases and replacements',async()=>{
   await page.setViewportSize({width:390,height:844});
   for(const id of ['reading-case-bank',firstID,'writing1-case-bank','writing2-case-bank','speaking-new-sep26-journeys','topic-crime','library']){await route(id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),id);}
   await route(firstID);await page.screenshot({path:path.join(qa,'mobile-reading-case.png'),animations:'disabled'});
   const p=first.locator('.case-passage p').first();const color=await p.evaluate(e=>getComputedStyle(e).color);const [r,g,b]=color.match(/[\d.]+/g).map(Number);assert(!(r>g*1.4&&r>b*1.4));
  });
  await check('no browser errors',async()=>assert.deepEqual(errors,[]));
 }finally{
  const result={checks,errors,passed:checks.filter(x=>x.pass).length,failed:checks.filter(x=>!x.pass).length,isolatedContext:true};fs.writeFileSync(path.join(qa,'browser-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await context.close();await browser.close();if(result.failed)process.exitCode=1;
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
