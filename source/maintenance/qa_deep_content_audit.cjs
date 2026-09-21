const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const qa=path.join(__dirname,'deep-audit-qa'),audit=JSON.parse(fs.readFileSync(path.join(__dirname,'audit-content-deep-20260919.json'),'utf8'));
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:1000}}),page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 const frame=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const route=async id=>{await page.evaluate(id=>location.hash=id,id);await frame()};
 async function check(name,fn){try{checks.push({name,pass:true,detail:await fn()})}catch(e){checks.push({name,pass:false,error:e.message})}}
 try{
  await page.goto(pathToFileURL(path.join(book,'开始学习.html')).href+'#library');await frame();
  await check('all reviewed units have one current badge and historical reviews are explicit',async()=>{
   for(const i of audit.items.filter(x=>x.audit_round==='current')){
    const n=page.locator(`[data-audit-target="${i.id}"]`);assert.equal(await n.count(),1,i.id);
    const badge=n.locator(`[data-content-audit="${i.id}"].content-audit-badge`);assert.equal(await badge.textContent(),i.status,i.id);
   }
   assert.equal(await page.locator('.learning-audit-note > summary').filter({hasText:'学习审查：'}).count(),0);
   assert.equal(await page.locator('.deep-unit-summary').count(),7);
   return audit.summary;
  });
  await check('supplementary unit links open the unit, notes still save in isolated context',async()=>{
   const item=audit.items.find(x=>x.id==='audit-075');await route(item.review_anchor);
   const unit=page.locator('[data-audit-target="audit-075"]');assert(await unit.isVisible());
   if(!await unit.evaluate(e=>e.open))await unit.locator(':scope > summary').click();
   await unit.locator(':scope > .content-audit-note > summary').click();
   assert(await unit.locator(':scope > .content-audit-note').evaluate(e=>e.open));
   await route('reading-tech-locate');await page.locator('[data-save="resource-note-tech-locate"]').fill('DEEP AUDIT isolated preservation check');
   await frame();await page.reload();await frame();assert.equal(await page.locator('[data-save="resource-note-tech-locate"]').inputValue(),'DEEP AUDIT isolated preservation check');
  });
  await check('known teaching errors are corrected without revealing test answers',async()=>{
   const weather=await page.locator('#listening-new-new-listening-weather-table').textContent();assert(weather.includes('最迟周六下午'));assert(!weather.includes('4＝下午。'));
   const lecture=await page.locator('#listening-new-new-listening-lecture-outline .res-body').textContent();assert(!lecture.includes('you can do it anywhere'));assert(lecture.includes('you do not need any tools or devices'));
   const garden=await page.locator('#speaking-new-sep26-energy .remediated-teaching').textContent();assert(garden.includes('trade-off'));assert(!garden.includes('换成自己的真实经历'));
  });
  await check('same-task official benchmarks link to existing local source pages',async()=>{
   const boxes=page.locator('[data-deep-audit-ui="benchmark"]');assert(await boxes.count()>=7);
   const hrefs=await boxes.locator('a').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
   for(const href of hrefs){if(!/^https?:/.test(href))assert(fs.existsSync(path.join(book,decodeURIComponent(href.split('#')[0]))),href)}
   assert(hrefs.some(x=>x.endsWith('#page=17')));assert(hrefs.some(x=>x.endsWith('#page=22')));assert(hrefs.some(x=>x.endsWith('#page=26')));
  });
  await check('desktop and phone layouts keep audit and lessons readable',async()=>{
   await route('vocabulary');await page.screenshot({path:path.join(qa,'desktop-vocabulary.png'),animations:'disabled'});
   await page.setViewportSize({width:390,height:844});
   for(const id of ['library','topic-education','vocabulary',audit.items.find(x=>x.id==='audit-078').review_anchor]){
    await route(id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),id);
   }
   await page.screenshot({path:path.join(qa,'mobile-unit.png'),animations:'disabled'});
  });
  await check('standalone audit search and status filters work',async()=>{
   await page.goto(pathToFileURL(path.join(book,'学习单元与词汇深审.html')).href);assert.equal(await page.locator('article').count(),audit.summary.current_total);
   await page.locator('#status').selectOption('不达标');assert.equal(await page.locator('article:visible').count(),audit.summary.current_by_status['不达标']);
   await page.locator('#q').fill('教育');assert(await page.locator('article:visible').count()>0);await page.locator('#q').fill('NO_MATCH__AUDIT');assert.equal(await page.locator('article:visible').count(),0);
   await page.locator('#q').fill('');await page.locator('#status').selectOption('');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await page.screenshot({path:path.join(qa,'mobile-report.png'),animations:'disabled'});
  });
  await check('word audit supports search, repairs and exact-wordform evidence',async()=>{
   await page.goto(pathToFileURL(path.join(book,'词条逐项审核.html')).href);
   assert.equal(await page.locator('article').count(),40);
   await page.locator('#q').fill('respectively');assert.equal(await page.locator('article').count(),1);assert((await page.locator('article').textContent()).includes('Classes A and B'));
   await page.locator('#q').fill('');await page.locator('#status').selectOption('repaired');assert.equal(await page.locator('article').count(),5);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await page.screenshot({path:path.join(qa,'mobile-word-audit.png'),animations:'disabled'});
  });
  await check('no browser script errors',async()=>assert.deepEqual(errors,[]));
 }finally{
  const result={checks,errors,passed:checks.filter(x=>x.pass).length,failed:checks.filter(x=>!x.pass).length,isolatedContext:true};
  fs.writeFileSync(path.join(qa,'browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await context.close();await browser.close();if(result.failed)process.exitCode=1;
 }
})().catch(e=>{console.error(e);process.exitCode=1});
