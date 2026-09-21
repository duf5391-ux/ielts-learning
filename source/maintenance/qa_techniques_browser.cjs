const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const root='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const qa=path.join(__dirname,'techniques-qa');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:950},acceptDownloads:true});
 const page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
 const frame=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const route=async id=>{await page.evaluate(h=>location.hash=h,id);await frame();};
 const check=async(name,fn)=>{try{checks.push({name,pass:true,detail:await fn()});}catch(e){checks.push({name,pass:false,error:e.message});}};
 try{
  await page.goto(pathToFileURL(path.join(root,'开始学习.html')).href+'#reading');
  const units=await page.locator('.technique-unit').evaluateAll(es=>es.map(e=>({id:e.id,title:e.querySelector('summary')?.textContent,fields:[...e.querySelectorAll('[data-save]')].map(x=>({key:x.dataset.save,type:x.type,tag:x.tagName}))})));
  await check('12 technique units and 44 resource cards',async()=>{assert.equal(units.length,12);assert.equal(await page.locator('.res-card').count(),44);return units.map(u=>u.id);});
  await check('all technique deep links expand within correct chapter',async()=>{for(const u of units){await route(u.id);assert(await page.locator('#'+u.id).isVisible(),u.id);assert(await page.locator('#'+u.id).evaluate(e=>e.open),u.id);assert(await page.locator('#'+u.id.split('-')[0]).isVisible(),u.id);}return units.length;});
  await check('catalog filters, search, and click-through',async()=>{
   await route('resource-update');
   for(const type of ['reading','writing1']){await page.locator(`[data-res-filter="${type}"]`).click();const visible=page.locator('.res-card:visible');assert((await visible.count())>0);assert((await visible.evaluateAll(es=>es.every(e=>e.dataset.resSection===es[0].dataset.resSection))));}
   await page.locator('[data-res-filter="all"]').click();
   const first=units[0];const card=page.locator(`.res-card[href="#${first.id}"]`);assert.equal(await card.count(),1);
   const title=await card.locator('h3,h2').first().textContent();await page.locator('#res-search').fill(title.trim());assert(await card.isVisible());
   await card.click();await frame();assert(await page.locator('#'+first.id).isVisible());
   return {searched:title.trim(),opened:first.id};
  });
  await check('new and original records survive reload and JSON export',async()=>{
   await route('reading');await page.locator('[data-save="reading-q1"]').fill('Technique QA original answer');
   const u=units[0];await route(u.id);const area=page.locator('#'+u.id);
   const note=area.locator('textarea[data-save]').first();await note.fill('Technique QA saved note');const noteKey=await note.getAttribute('data-save');
   const checkboxes=area.locator('input[type="checkbox"][data-save]');assert((await checkboxes.count())>=2);
   const keys=[];for(let i=0;i<await checkboxes.count();i++){keys.push(await checkboxes.nth(i).getAttribute('data-save'));await checkboxes.nth(i).check();}
   await frame();await page.reload();await frame();assert.equal(await page.locator(`[data-save="${noteKey}"]`).inputValue(),'Technique QA saved note');for(const key of keys)assert(await page.locator(`[data-save="${key}"]`).isChecked());
   await route('reading');assert.equal(await page.locator('[data-save="reading-q1"]').inputValue(),'Technique QA original answer');
   await route('records');assert(await page.locator(`#res-review-list a[href="#${u.id}"]`).isVisible());assert(await page.locator(`#res-learned-list a[href="#${u.id}"]`).isVisible());
   const pending=page.waitForEvent('download');await page.locator('[data-export="json"]').click();const download=await pending;const dest=path.join(qa,'isolated-records-export.json');await download.saveAs(dest);const record=JSON.parse(fs.readFileSync(dest,'utf8'));
   assert.equal(record.fields[noteKey],'Technique QA saved note');assert.equal(record.fields['reading-q1'],'Technique QA original answer');for(const key of keys)assert(record.fields[key]);
   return {noteKey,checkboxes:keys,isolatedContext:true};
  });
  await check('practice answers open and all five figure placements load',async()=>{
   const images=[];
   for(const u of units){await route(u.id);const unit=page.locator('#'+u.id);await unit.locator('.technique-practice>summary').click();await unit.locator('.technique-answer>summary').click();assert(await unit.locator('.technique-answer').evaluate(e=>e.open));
    const figure=unit.locator('.technique-figure');if(await figure.count()){await figure.scrollIntoViewIfNeeded();await figure.locator('img').evaluate(el=>el.decode());assert(await figure.locator('img').evaluate(el=>el.naturalWidth>0));await figure.screenshot({path:path.join(qa,u.id+'-figure.png'),animations:'disabled'});images.push(u.id);}}
   assert.equal(images.length,5);return images;
  });
  await check('desktop and mobile chapter and expanded lesson layouts',async()=>{
   const widths=[];
   for(const width of [1365,390]){await page.setViewportSize({width,height:width===390?844:950});for(const section of ['reading','writing1']){
    await route(section);await page.screenshot({path:path.join(qa,`${width}-${section}-entry.png`),animations:'disabled'});
    const u=units.find(u=>u.id.startsWith(section+'-'));await route(u.id);await page.screenshot({path:path.join(qa,`${width}-${section}-lesson.png`),animations:'disabled'});
   }
   for(const u of units){await route(u.id);const metrics=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));assert(metrics.scroll<=metrics.viewport+1,u.id+' '+JSON.stringify(metrics));widths.push({id:u.id,...metrics});}}
   return widths;
  });
  await check('no browser script errors',async()=>assert.deepEqual(errors,[]));
 }finally{
  const result={isolated_browser_context:true,checks,errors,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length};
  fs.writeFileSync(path.join(qa,'browser-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await context.close();await browser.close();if(result.failed)process.exitCode=1;
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
