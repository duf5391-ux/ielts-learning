const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const qa=path.join(__dirname,'worked-answers-qa');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:950}}),page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
 const route=async id=>{await page.evaluate(id=>location.hash=id,id);await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));};
 const check=async(name,fn)=>{try{checks.push({name,pass:true,detail:await fn()});}catch(e){checks.push({name,pass:false,error:e.message});}};
 try{
  await page.goto(pathToFileURL(book).href+'#library');
  await check('one directory in lower navigation, no top duplicate',async()=>{
   assert.equal(await page.locator('.sidebar [data-go="resource-update"]').count(),0);
   assert.equal(await page.locator('.sidebar [data-go="library"]').count(),1);
   assert.equal(await page.locator('#library #resource-update .res-card').count(),44);
   assert.equal(await page.locator('.technique-entry').count(),0);
   assert(!(await page.locator('#resource-update').evaluate(e=>e.classList.contains('panel'))));
   assert(await page.locator('#library').isVisible());
   await page.screenshot({path:path.join(qa,'desktop-merged-directory.png'),animations:'disabled'});
  });
  await check('legacy catalogue hashes route into merged library',async()=>{
   for(const id of ['resource-update','resource-new-list']){await route('guide');await route(id);assert(await page.locator('#library').isVisible(),id);assert(await page.locator('#resource-update').isVisible(),id);}
   return ['resource-update','resource-new-list'];
  });
  await check('all original record fields and IDs remain',async()=>{
   const before=JSON.parse(fs.readFileSync(path.join(qa,'baseline.json'),'utf8'));
   const now=await page.evaluate(()=>({fields:[...document.querySelectorAll('[data-save]')].map(x=>x.dataset.save),ids:[...document.querySelectorAll('[id]')].map(x=>x.id)}));
   assert(before.fields.every(x=>now.fields.includes(x)));assert(before.ids.every(x=>now.ids.includes(x)));assert.equal(new Set(now.ids).size,now.ids.length);
   return {preservedFields:before.fields.length,preservedIds:before.ids.length};
  });
  await check('12 worked answers with concrete evidence are visible without another reveal',async()=>{
   const samples=JSON.parse(fs.readFileSync(path.join(__dirname,'learning-techniques.json'),'utf8')).units;
   for(const u of samples){await route(u.anchor);const node=page.locator('#'+u.anchor);assert(await node.locator('.worked-answer').isVisible(),u.id);assert.equal(await node.locator('.worked-reason').count(),u.worked_example.explanations.length);assert((await node.locator('.worked-answer-text').innerText()).trim().length>20);}
   return samples.length;
  });
  await check('three complete Task 1 model essays meet the requested length',async()=>{
   const samples=JSON.parse(fs.readFileSync(path.join(__dirname,'writing-worked-answers.json'),'utf8'));const counts={};
   for(const id of ['tech-read-chart','tech-process','tech-maps']){const text=samples[id].answer_md;counts[id]=text.trim().split(/\s+/).length;assert(counts[id]>=150&&counts[id]<=190,id);assert(text.split(/\n\n/).length>=3);}
   return counts;
  });
  await check('worked answers and merged catalogue fit mobile viewport',async()=>{
   await page.setViewportSize({width:390,height:844});
   for(const id of ['library','reading-tech-judgement','reading-tech-diagram','writing1-tech-read-chart','writing1-tech-process','writing1-tech-maps']){
    await route(id);if(id!=='library')await page.locator('#'+id+' .worked-answer').scrollIntoViewIfNeeded();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),id);
    await page.screenshot({path:path.join(qa,'mobile-'+id+'.png'),animations:'disabled'});
   }
  });
  await check('no script errors',async()=>assert.deepEqual(errors,[]));
 }finally{
  const result={checks,errors,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length,isolatedContext:true};
  fs.writeFileSync(path.join(qa,'browser-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await context.close();await browser.close();if(result.failed)process.exitCode=1;
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
