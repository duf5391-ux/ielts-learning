const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL}=require('url');
const main='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const qa=path.join(__dirname,'text-conversion-qa'),data=JSON.parse(fs.readFileSync(path.join(__dirname,'text-questions.json'),'utf8'));
(async()=>{
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
const context=await browser.newContext({viewport:{width:1365,height:950}}),page=await context.newPage(),errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
page.setDefaultTimeout(12000);
const check=async(name,f)=>{try{checks.push({name,pass:true,detail:await f()})}catch(e){checks.push({name,pass:false,error:e.stack})}};
const route=async id=>{await page.evaluate(id=>{location.hash=id},id);await page.waitForFunction(id=>!document.getElementById(id).closest('main>.panel').hidden,id);await page.locator('#'+id).scrollIntoViewIfNeeded();await page.evaluate(()=>{document.documentElement.style.scrollBehavior='auto'});};
try{
await page.goto(pathToFileURL(main).href+'#library');
await check('all prior fields, IDs and audio survive; no duplicate keys',async()=>{
 const before=JSON.parse(fs.readFileSync(path.join(qa,'baseline.json'),'utf8'));
 const now=await page.evaluate(()=>({fields:[...document.querySelectorAll('[data-save]')].map(x=>x.dataset.save),ids:[...document.querySelectorAll('[id]')].map(x=>x.id),audio:[...document.querySelectorAll('audio source,audio[src]')].map(x=>x.getAttribute('src'))}));
 assert.deepEqual([...now.fields].sort(),[...before.fields].sort());assert.equal(now.fields.length,new Set(now.fields).size);assert(before.ids.every(id=>now.ids.includes(id)));assert.equal(now.ids.length,new Set(now.ids).size);assert.deepEqual(now.audio,before.audio);return {fields:now.fields.length,ids:now.ids.length,audio:now.audio.length};
});
await check('all 21 original pages accessible inside 14 closed disclosures',async()=>{
 assert.equal(await page.locator('.qt-unit').count(),14);assert.equal(await page.locator('.qt-originals img').count(),21);assert.equal(await page.locator('.qt-originals[open]').count(),0);assert.equal(await page.locator('.qt-body [data-save]').count(),25);assert.equal(await page.locator('.qt-diagram img').count(),3);
 for(const u of data.units){const id=u.chapter+'-text-'+u.id;await route(id);assert(await page.locator('#'+id+' .qt-body').isVisible(),id);assert((await page.locator('#'+id+' .qt-body').innerText()).length>100);}
 return {pages:21,units:14,inlineAnswers:25,retainedDiagrams:3};
});
await check('full question text search and cross-section routing',async()=>{
 await route('text-question-directory');await page.locator('#qt-search').fill('cash flow');assert.equal(await page.locator('.qt-results li:not([hidden])').count(),1);await page.locator('.qt-results li:not([hidden]) a').click();assert(await page.locator('#listening-text-customer-call').isVisible());
 await route('text-question-directory');await page.locator('#qt-search').fill('zzzzNOmatch');assert(await page.locator('#qt-empty').isVisible());await page.locator('#qt-search').fill('');assert.equal(await page.locator('.qt-results li:not([hidden])').count(),14);
 await page.screenshot({path:path.join(qa,'desktop-directory.png'),animations:'disabled'});
});
await check('source image disclosure and image zoom remain usable',async()=>{
 await route('speaking-text-important-object');await page.locator('#speaking-text-important-object .qt-originals summary').click();const img=page.locator('#speaking-text-important-object .qt-originals img');await img.scrollIntoViewIfNeeded();await img.click();assert(await page.locator('.zoom-dialog').isVisible());await page.locator('.zoom-dialog button').click();await page.locator('#speaking-text-important-object .qt-originals summary').click();
});
await check('selecting new passage text opens existing word lookup',async()=>{
 await route('reading-text-davies');
 const paragraph=page.locator('#reading-text-davies .qt-passage p').first();await paragraph.scrollIntoViewIfNeeded();
 await paragraph.evaluate(el=>{const t=el.firstChild,at=t.textContent.indexOf('inheritance');const r=document.createRange();r.setStart(t,at);r.setEnd(t,at+'inheritance'.length);const sel=getSelection();sel.removeAllRanges();sel.addRange(r);el.dispatchEvent(new MouseEvent('click',{bubbles:true,button:0}));});
 assert(await page.locator('#word-lookup').isVisible());assert.equal(await page.locator('#lookup-form input').inputValue(),'inheritance');await page.locator('#lookup-close').click();await page.evaluate(()=>getSelection().removeAllRanges());
});
await check('old answers restore into inline fields; edits persist and export correctly',async()=>{
 await page.evaluate(()=>localStorage.setItem('ielts-finished-book-v1',JSON.stringify({version:1,fields:{'reading-q1':'old answer','listening-q1':'Jacobs','listening-review-q1':'motivation','writing2-essay':'Existing essay kept.'},snapshots:{}})));
 await page.reload();await route('reading-text-davies');assert.equal(await page.locator('[data-save="reading-q1"]').inputValue(),'old answer');await page.locator('[data-save="reading-q1"]').fill('mining');await page.reload();assert.equal(await page.locator('[data-save="reading-q1"]').inputValue(),'mining');assert.equal(await page.locator('[data-save="writing2-essay"]').inputValue(),'Existing essay kept.');assert.equal(await page.locator('[data-save="listening-review-q1"]').inputValue(),'motivation');
 const state=await page.evaluate(()=>JSON.parse(localStorage.getItem('ielts-finished-book-v1')));assert.equal(state.fields['reading-q1'],'mining');
 await route('records');const downloadPromise=page.waitForEvent('download');await page.locator('[data-export="json"]').first().click();const download=await downloadPromise;const saved=path.join(qa,'test-export.json');await download.saveAs(saved);const exported=JSON.parse(fs.readFileSync(saved,'utf8'));assert.equal(exported.fields['reading-q1'],'mining');assert.equal(exported.fields['writing2-essay'],'Existing essay kept.');
 return 'isolated test browser only';
});
await check('freeze includes moved answers and restores read-only state',async()=>{
 await route('reading-first');await page.locator('[data-freeze="reading"]').click();await page.waitForFunction(()=>JSON.parse(localStorage.getItem('ielts-finished-book-v1')).snapshots.reading);const snap=await page.evaluate(()=>JSON.parse(localStorage.getItem('ielts-finished-book-v1')).snapshots.reading);assert.equal(snap.fields['reading-q1'],'mining');assert.equal(Object.keys(snap.fields).filter(k=>/^reading-q/.test(k)).length,13);await page.reload();assert(await page.locator('[data-save="reading-q1"]').evaluate(x=>x.readOnly));
 await route('listening-first');await page.locator('[data-save="listening-q8"]').fill('1500');await page.locator('[data-freeze="listening"]').click();const ls=await page.evaluate(()=>JSON.parse(localStorage.getItem('ielts-finished-book-v1')).snapshots.listening);assert.equal(ls.fields['listening-q8'],'1500');assert.equal(Object.keys(ls.fields).filter(k=>/^listening-q/.test(k)).length,8);
});
await check('desktop and mobile layout, images, text size',async()=>{
 for(const width of [1365,390]){
  await page.setViewportSize({width,height:width===390?844:950});
  for(const u of data.units){const id=u.chapter+'-text-'+u.id;await route(id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),width+' '+id);assert(await page.locator('#'+id+' .qt-body').evaluate(x=>parseFloat(getComputedStyle(x).fontSize)>=16));
   if(u.crop){const img=page.locator('#'+id+' .qt-diagram img');await img.scrollIntoViewIfNeeded();await img.evaluate(x=>x.decode());assert(await img.evaluate(x=>x.naturalWidth>300));}
  }
  for(const id of ['reading-text-davies','listening-text-shipping','writing1-text-us-jobs','writing2-text-theatres','speaking-text-important-object','text-question-directory']){
   await route(id);await page.evaluate(id=>{document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'})},id);await page.screenshot({path:path.join(qa,width+'-'+id+'.png'),animations:'disabled'});
  }
 }
});
await check('no browser script errors',async()=>assert.deepEqual(errors,[]));
}finally{const result={checks,errors,passed:checks.filter(x=>x.pass).length,failed:checks.filter(x=>!x.pass).length,isolatedContext:true};fs.writeFileSync(path.join(qa,'browser-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await browser.close();if(result.failed)process.exitCode=1;}
})().catch(e=>{console.error(e);process.exitCode=1});
