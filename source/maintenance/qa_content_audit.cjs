const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const main='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const qa=path.join(__dirname,'content-audit-qa');
(async()=>{
 const audit=JSON.parse(fs.readFileSync(path.join(__dirname,'audit-content-20260919.json'),'utf8'));
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:950},acceptDownloads:true}),page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
 const frame=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const route=async id=>{await page.evaluate(id=>location.hash=id,id);await frame();};
 const check=async(name,fn)=>{try{checks.push({name,pass:true,detail:await fn()});}catch(e){checks.push({name,pass:false,error:e.message});}};
 try{
  await page.goto(pathToFileURL(main).href+'#library');
  await check('all audit targets have matching text labels and reasons',async()=>{
   for(const item of audit.items){const target=page.locator(`[data-audit-target="${item.id}"]`);assert.equal(await target.count(),1,item.title);const badge=target.locator(`.content-audit-badge[data-content-audit="${item.id}"]`);assert.equal(await badge.count(),1,item.title);assert.equal(await badge.textContent(),item.status);assert.equal(await target.locator(`.content-audit-note[data-content-audit="${item.id}"]`).count(),1,item.title);}
   return {items:audit.items.length,counts:audit.items.reduce((a,x)=>(a[x.status]=(a[x.status]||0)+1,a),{})};
  });
  await check('normal lesson text uses ink rather than red',async()=>{
   const colors={};for(const id of ['reading-tech-judgement','writing1-tech-read-chart']){await route(id);for(const part of ['.res-body>p','.worked-answer-text p','.worked-reason p']){const key=id+' '+part;const color=await page.locator('#'+id+' '+part).first().evaluate(e=>getComputedStyle(e).color);const [r,g,b]=color.match(/[\d.]+/g).map(Number);assert(!(r>g*1.4&&r>b*1.4),key+' '+color);colors[key]=color;}}
   return colors;
  });
  await check('single resource directory and both searches still work',async()=>{
   await route('library');assert.equal(await page.locator('.sidebar [data-go="resource-update"]').count(),0);assert.equal(await page.locator('.sidebar [data-go="library"]').count(),1);assert.equal(await page.locator('.res-card').count(),44);
   await page.locator('#res-search').fill('Overview');assert((await page.locator('.res-card:visible').count())>0);await page.locator('#res-search').fill('');
   await page.locator('#qt-search').fill('cash flow');assert.equal(await page.locator('.qt-results li:not([hidden])').count(),1);await page.locator('#qt-search').fill('');
   await page.screenshot({path:path.join(qa,'desktop-audit-directory.png'),animations:'disabled'});
  });
  await check('review details expose the precise reason and next action',async()=>{
   const item=audit.items.find(x=>x.anchor==='writing1-tech-read-chart');assert(item);await route(item.anchor);const note=page.locator(`[data-audit-target="${item.id}"] .content-audit-note[data-content-audit="${item.id}"]`);await note.locator('summary').click();assert(await note.evaluate(e=>e.open));assert((await note.innerText()).includes(item.reason));await note.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(qa,'desktop-reviewed-lesson.png'),animations:'disabled'});
  });
  await check('notes and existing answers persist and export',async()=>{
   await route('writing1-tech-read-chart');await page.locator('[data-save="resource-note-tech-read-chart"]').fill('Audit QA note');await route('reading');await page.locator('[data-save="reading-q1"]').fill('Audit QA original answer');await frame();await page.reload();await frame();assert.equal(await page.locator('[data-save="reading-q1"]').inputValue(),'Audit QA original answer');assert.equal(await page.locator('[data-save="resource-note-tech-read-chart"]').inputValue(),'Audit QA note');
   await route('records');const pending=page.waitForEvent('download');await page.locator('[data-export="json"]').click();const file=await pending;const dest=path.join(qa,'isolated-records.json');await file.saveAs(dest);const data=JSON.parse(fs.readFileSync(dest,'utf8'));assert.equal(data.fields['reading-q1'],'Audit QA original answer');assert.equal(data.fields['resource-note-tech-read-chart'],'Audit QA note');
  });
  await check('all original text questions and images remain usable',async()=>{
   assert.equal(await page.locator('.qt-unit').count(),14);assert.equal(await page.locator('.qt-originals img').count(),21);assert.equal(await page.locator('.qt-body [data-save]').count(),25);const id=await page.locator('#reading .qt-unit').first().getAttribute('id');await route(id);
   const originals=page.locator('#'+id+' .qt-originals');await originals.locator('summary').click();assert(await originals.evaluate(e=>e.open));
  });
  await check('mobile audit badges and lessons stay within viewport',async()=>{
   await page.setViewportSize({width:390,height:844});
   for(const id of ['library','writing1-tech-read-chart','reading-tech-judgement','background']){await route(id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),id);await page.screenshot({path:path.join(qa,'mobile-'+id+'.png'),animations:'disabled'});}
  });
  await check('no browser errors',async()=>assert.deepEqual(errors,[]));
 }finally{
  const result={checks,errors,passed:checks.filter(x=>x.pass).length,failed:checks.filter(x=>!x.pass).length,isolatedContext:true};fs.writeFileSync(path.join(qa,'browser-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await context.close();await browser.close();if(result.failed)process.exitCode=1;
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
