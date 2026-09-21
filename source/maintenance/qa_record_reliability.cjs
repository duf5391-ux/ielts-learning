const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const main='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html',key='ielts-finished-book-v1';
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const checks=[];
 const run=async(name,fn)=>{const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());try{await page.goto(pathToFileURL(main).href+'#reading',{waitUntil:'domcontentloaded'});await fn(page);assert.deepEqual(errors,[]);checks.push({name,pass:true})}catch(e){checks.push({name,pass:false,error:e.message})}finally{await context.close()}};
 const raw=p=>p.evaluate(k=>localStorage.getItem(k),key);
 const type=p=>p.locator('[data-save="reading-q1"]').fill('mining');
 const seed=async(p,s)=>{await p.evaluate(([k,v])=>localStorage.setItem(k,v),[key,s]);await p.reload({waitUntil:'domcontentloaded'})};
 const upload=(p,data)=>p.locator('#import-state').setInputFiles({name:'backup.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
 const valid={version:1,fields:{'reading-q1':'education'},snapshots:{}};
 const invalid=['{broken',JSON.stringify({version:1,fields:[],snapshots:{}}),JSON.stringify({version:1,fields:{},snapshots:{guide:{at:'test',fields:{}}}})];
 try{
  await run('normal input, frozen first attempt and reload',async p=>{await type(p);await p.locator('[data-freeze="reading"]').click();assert.equal(JSON.parse(await raw(p)).snapshots.reading.fields['reading-q1'],'mining');await p.reload({waitUntil:'domcontentloaded'});assert.equal(await p.locator('[data-save="reading-q1"]').inputValue(),'mining');assert(await p.locator('[data-save="reading-q1"]').evaluate(e=>e.readOnly))});
  for(const s of invalid)await run('invalid stored data preserved: '+s.slice(0,65),async p=>{await seed(p,s);await type(p);assert.equal(await raw(p),s);assert((await p.locator('#save-status').textContent()).includes('暂停自动保存'));await p.locator('[data-freeze="reading"]').click();assert.equal(await raw(p),s);assert.equal(await p.locator('[data-freeze="reading"]').isDisabled(),false)});
  await run('invalid backup rejected without replacing valid data',async p=>{await type(p);const before=await raw(p);await upload(p,{version:1,fields:[],snapshots:{}});await p.waitForFunction(()=>document.querySelector('#toast').textContent.includes('格式不完整'));assert.equal(await raw(p),before)});
  await run('valid restore from corrupt record',async p=>{await seed(p,'{broken');await upload(p,valid);await p.waitForFunction(()=>document.querySelector('[data-save="reading-q1"]')?.value==='education');assert.deepEqual(JSON.parse(await raw(p)),valid)});
  await run('failed restore write preserves current state and allows retry',async p=>{await type(p);const before=await raw(p);await p.evaluate(()=>{window.originalAuditSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException('Quota','QuotaExceededError')}});await upload(p,valid);await p.waitForFunction(()=>document.querySelector('#toast').textContent.includes('未能写入'));assert.equal(await raw(p),before);assert.equal(await p.locator('[data-save="reading-q1"]').inputValue(),'mining');await p.evaluate(()=>Storage.prototype.setItem=window.originalAuditSetItem);await upload(p,valid);await p.waitForFunction(()=>document.querySelector('[data-save="reading-q1"]')?.value==='education')});
  await run('corrupt raw export and current draft text both recoverable',async p=>{await seed(p,'{broken');await type(p);await p.evaluate(()=>location.hash='records');let [d]=await Promise.all([p.waitForEvent('download'),p.locator('[data-export="json"]').click()]);assert.equal(fs.readFileSync(await d.path(),'utf8'),'{broken');[d]=await Promise.all([p.waitForEvent('download'),p.locator('#records [data-export="text"]').click()]);assert(fs.readFileSync(await d.path(),'utf8').includes('mining'));assert.equal(await raw(p),'{broken')});
 }finally{await browser.close()}
 fs.writeFileSync(path.join(__dirname,'architecture-audit-qa','reliability-tests.json'),JSON.stringify({scope:'isolated temporary browser profiles',checks},null,2));console.log(JSON.stringify(checks,null,2));if(checks.some(x=>!x.pass))process.exitCode=1;
})();


