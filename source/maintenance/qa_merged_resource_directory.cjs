const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const file=path.join(__dirname,'merged-resource-directory-qa.html');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1365,height:950}});
 const page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 const settle=()=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const route=async hash=>{await page.evaluate(h=>location.hash=h,hash);await settle();};
 try{
  await page.goto(pathToFileURL(file).href+'#library');
  for(const hash of ['library','resource-update','resource-new-list','library-materials','library-rules','library-files']){
   await route(hash);
   assert(await page.locator('#library').isVisible(),hash);
   assert.equal(await page.locator('main>.panel:visible').count(),1,hash);
   assert.equal(await page.locator('.sidebar [data-go="library"]').getAttribute('aria-current'),'page',hash);
   assert.equal(await page.locator('#current-page-label').textContent(),'资源目录',hash);
   assert.equal(await page.title(),'资源目录 · IELTS Work',hash);
   assert(await page.locator('#'+hash).isVisible(),hash);
  }
  checks.push('all six same-page and legacy anchors show library, correct active sidebar, heading, and title');
  assert.equal(await page.locator('.sidebar [data-go="resource-update"]').count(),0);
  assert.equal(await page.locator('#library #resource-update .res-card').count(),44);
  assert.equal(await page.locator('#library h1').count(),1);
  assert.equal(await page.locator('.technique-entry').count(),0);
  await route('resource-new-list');
  await page.locator('[data-res-filter="reading"]').click();
  assert.equal(await page.locator('.res-card:visible').count(),11);
  await page.locator('[data-res-filter="writing1"]').click();
  assert.equal(await page.locator('.res-card:visible').count(),7);
  await page.locator('[data-res-filter="all"]').click();
  await page.locator('#res-search').fill('阅读图示标注');
  assert.equal(await page.locator('.res-card:visible').count(),1);
  await page.locator('.res-card:visible').click();await settle();
  assert(await page.locator('#reading-tech-diagram').isVisible());
  assert(await page.locator('#reading-tech-diagram').evaluate(e=>e.open));
  checks.push('44 cards, reading 11/Task 1 7 filters, search and lesson deep link');
  await route('library-files');
  await page.locator('#library-search').fill('answer-key-01');
  assert.equal(await page.locator('.source-file:visible').count(),1);
  checks.push('original file search remains functional');
  for(const width of [1365,390]){
   await page.setViewportSize({width,height:950});
   await route('library');
   await page.locator('#res-search').fill('');
   const dimensions=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
   assert(dimensions.scroll<=dimensions.viewport+1,JSON.stringify(dimensions));
   await page.screenshot({path:path.join(__dirname,`merged-resource-directory-${width}.png`),animations:'disabled'});
  }
  checks.push('desktop/mobile no horizontal overflow');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({passed:checks,errors},null,2));
 }finally{await context.close();await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
