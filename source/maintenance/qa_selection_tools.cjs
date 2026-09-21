const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),assert=require('assert'),path=require('path'),{pathToFileURL}=require('url');
const book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const out=path.join(__dirname,'learning-upgrade-qa');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const checks=[];
 const run=async(name,fn)=>{const context=await browser.newContext(),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));try{await page.goto(pathToFileURL(book).href+'#sentence-learning',{waitUntil:'load'});await fn(page,context);assert.deepEqual(errors,[]);checks.push({name,pass:true});}catch(e){checks.push({name,pass:false,error:e.stack});}finally{await context.close();}};
 const open=async p=>{await p.locator('[data-open-sentence]').click();};
 const getRows=p=>p.locator('#sentence-store').evaluate(e=>JSON.parse(e.value||'[]'));
 await run('translate selected text, preserve exact request, save and restore',async p=>{
   let requests=[];await p.route('https://api.mymemory.translated.net/**',async route=>{requests.push(new URL(route.request().url()));await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({responseStatus:200,responseData:{translatedText:'公共交通可以减少交通拥堵。'}})});});
   await p.evaluate(()=>{location.hash='reading';const p=document.createElement('p');p.id='qa-selection-text';p.textContent='Public transport can reduce traffic congestion.';document.querySelector('#reading').prepend(p);});
   await p.locator('#qa-selection-text').scrollIntoViewIfNeeded();
   await p.evaluate(()=>{const p=document.querySelector('#qa-selection-text'),range=document.createRange();range.selectNodeContents(p);const s=getSelection();s.removeAllRanges();s.addRange(range);p.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));});
   await p.locator('#selection-translate').click();await p.waitForFunction(()=>document.querySelector('#sentence-result').value.length>0);
   assert.equal(requests.length,1);assert.equal(requests[0].searchParams.get('q'),'Public transport can reduce traffic congestion.');assert.equal(requests[0].searchParams.get('langpair'),'en|zh-CN');
   await p.locator('#sentence-save').click();assert.equal((await getRows(p)).length,1);
   await p.reload({waitUntil:'load'});await p.evaluate(()=>location.hash='sentence-learning');assert.equal((await getRows(p))[0].translation,'公共交通可以减少交通拥堵。');
   await p.locator('#sentence-list button').first().click();await p.locator('#sentence-result').fill('公共交通有助于缓解拥堵。');await p.locator('#sentence-save').click();assert.equal((await getRows(p)).length,1);assert.equal((await getRows(p))[0].provenance,'手动修订译文');
   await p.locator('#sentence-translate').click();assert.equal(requests.length,1);assert.match(await p.locator('#sentence-status').textContent(),/无需联网/);
 });
 await run('manual Chinese to English translation and long sentence handling',async p=>{
   let count=0;await p.route('https://api.mymemory.translated.net/**',route=>{count++;return route.abort();});
   await open(p);await p.locator('#sentence-source').fill('公共交通应该得到更多投入。');await p.locator('#sentence-direction').selectOption('zh-CN|en');await p.locator('#sentence-result').fill('Public transport should receive more investment.');await p.locator('#sentence-save').click();assert.equal((await getRows(p))[0].direction,'zh-CN|en');assert.equal(count,0);
   await p.locator('#sentence-source').fill('a'.repeat(501));await p.locator('#sentence-translate').click();assert.match(await p.locator('#sentence-status').textContent(),/较长/);assert.equal(count,0);
 });
 await run('network failure and quota never become saved translations',async p=>{
   await p.route('https://api.mymemory.translated.net/**',route=>route.abort());await open(p);await p.locator('#sentence-source').fill('This is a test sentence.');await p.locator('#sentence-translate').click();await p.waitForFunction(()=>document.querySelector('#sentence-status').textContent.includes('无法连接'));assert.equal(await p.locator('#sentence-result').inputValue(),'');
   await p.unroute('https://api.mymemory.translated.net/**');await p.route('https://api.mymemory.translated.net/**',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({quotaFinished:true,responseStatus:200,responseData:{translatedText:'MYMEMORY WARNING'}})}));await p.locator('#sentence-translate').click();await p.waitForFunction(()=>document.querySelector('#sentence-status').textContent.includes('额度'));assert.equal(await p.locator('#sentence-result').inputValue(),'');assert.equal((await getRows(p)).length,0);
 });
 await run('corrupt sentence field preserved',async p=>{
   await p.evaluate(()=>{const f=document.querySelector('#sentence-store');f.value='{bad';f.dispatchEvent(new Event('input',{bubbles:true}));});await open(p);await p.locator('#sentence-source').fill('Example');await p.locator('#sentence-result').fill('示例');await p.locator('#sentence-save').click();assert.equal(await p.locator('#sentence-store').inputValue(),'{bad');assert.match(await p.locator('#sentence-status').textContent(),/异常/);
 });
 await run('manual translation survives a pending response and an oversized retry',async p=>{
   let held=null;await p.route('https://api.mymemory.translated.net/**',route=>{held=route;});await open(p);await p.locator('#sentence-source').fill('Parks make cities pleasant.');await p.locator('#sentence-translate').click();
   await p.locator('#sentence-result').fill('手动填写的译文');if(held)await held.fulfill({status:200,contentType:'application/json',body:JSON.stringify({responseStatus:200,responseData:{translatedText:'不该覆盖'}})}).catch(()=>{});assert.equal(await p.locator('#sentence-result').inputValue(),'手动填写的译文');
   await p.locator('#sentence-source').fill('a'.repeat(501));await p.locator('#sentence-result').fill('保留我的译文');await p.locator('#sentence-translate').click();assert.equal(await p.locator('#sentence-result').inputValue(),'保留我的译文');
 });
 await run('storage failure remains a current-page draft and reports unsaved state',async p=>{
   await open(p);await p.locator('#sentence-source').fill('A safe backup matters.');await p.locator('#sentence-result').fill('可靠的备份很重要。');await p.evaluate(()=>{Storage.prototype.setItem=function(){throw new DOMException('Quota','QuotaExceededError');};});await p.locator('#sentence-save').click();assert.match(await p.locator('#sentence-status').textContent(),/未能写入/);assert.equal((await getRows(p)).length,1);
 });
 await run('known bilingual example resolves offline with exact match',async p=>{
   let count=0;await p.route('https://api.mymemory.translated.net/**',route=>{count++;return route.abort();});await open(p);await p.locator('#sentence-source').fill('There is little evidence that the new rule has solved the problem.');await p.locator('#sentence-translate').click();assert.equal(await p.locator('#sentence-result').inputValue(),'很少有证据表明新规定已解决问题。');assert.equal(count,0);assert.match(await p.locator('#sentence-status').textContent(),/配套译文/);
 });
 await run('mobile notebook and popup fit the viewport',async p=>{
   await p.setViewportSize({width:390,height:844});await open(p);await p.locator('#sentence-source').fill('Education gives children more opportunities.');await p.locator('#sentence-result').fill('教育为儿童提供更多机会。');await p.screenshot({path:path.join(out,'sentence-mobile.png'),fullPage:false});
   const box=await p.locator('#sentence-popup').boundingBox();assert(box.x>=0&&box.x+box.width<=391);assert(box.y>=0&&box.y+box.height<=845);
 });
 await browser.close();fs.writeFileSync(path.join(out,'sentence-tests.json'),JSON.stringify(checks,null,2));console.log(JSON.stringify(checks,null,2));if(checks.some(x=>!x.pass))process.exitCode=1;
})();
