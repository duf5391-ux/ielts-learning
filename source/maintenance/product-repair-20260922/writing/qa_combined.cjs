const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert/strict');
const BOOK='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const candidate=path.resolve(process.argv[2]||path.join(__dirname,'candidate.html'));
const bytes=fs.readFileSync(candidate),checks=[],errors=[],KEY='ielts-finished-book-v1';
const questions=JSON.parse(fs.readFileSync(path.join(__dirname,'questions.json'),'utf8'));
const server=http.createServer((req,res)=>{
 const url=decodeURIComponent(req.url.split('?')[0]);
 if(url==='/index.html'){res.setHeader('Content-Type','text/html;charset=utf-8');res.end(bytes);return;}
 const f=path.resolve(BOOK,'.'+url);
 if(!f.startsWith(path.resolve(BOOK)+path.sep)||!fs.existsSync(f)||fs.statSync(f).isDirectory()){res.statusCode=404;res.end();return;}
 const types={'.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.svg':'image/svg+xml'};
 res.setHeader('Content-Type',types[path.extname(f)]||'application/octet-stream');fs.createReadStream(f).pipe(res);
});
const field=(p,k)=>p.locator('[data-save="'+k+'"]');
let browser,origin;
async function check(name,fn,{mobile=false,seed=null}={}){
 const c=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1440,height:1000},acceptDownloads:true});
 if(seed)await c.addInitScript(({key,fields})=>{if(!localStorage.getItem(key))localStorage.setItem(key,JSON.stringify({version:1,fields,steps:{},snapshots:{},recordings:{}}))},{key:KEY,fields:seed});
 const p=await c.newPage();p.setDefaultTimeout(9000);p.on('pageerror',e=>errors.push({name,message:e.message}));p.on('dialog',d=>d.accept());
 try{await p.goto(origin+'/index.html#writing-workbench',{waitUntil:'domcontentloaded'});await fn(p,c);checks.push({name,pass:true});}
 catch(e){checks.push({name,pass:false,error:e.stack});}
 finally{await c.close();}
}
async function route(p,id){await p.evaluate(id=>location.hash=id,id);await p.waitForFunction(id=>{const e=document.getElementById(id);return e && !e.closest('.panel')?.hidden && !e.closest('[data-ww-unit]')?.hidden},id);}
async function stage(p,id,s){await route(p,id+'-'+s);await p.locator('#'+id+'-'+s).waitFor({state:'visible'});}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));origin='http://127.0.0.1:'+server.address().port;
 browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 try{

 await check('combined mobile main navigation More → writing catalogue → search independent-living → draft and resume',async p=>{
  await route(p,'study');
  await p.locator('#product-more').click();
  await p.locator('#workspace-navigation [data-go="writing-workbench"]').click();
  await p.locator('.ww-directory').waitFor({state:'visible'});
  assert.equal(await p.locator('.ww-directory-row:visible').count(),32);
  for(const q of questions){const row=p.locator('[data-ww-pick="'+q.id+'"]');const text=await row.textContent();assert(text.includes(q.title),q.id);assert(text.includes(q.source.title),q.id);assert(text.includes('参考置信度：'+q.confidence.split('（')[0]),q.id);}
  await p.locator('#ww-directory-search').fill('独居');
  const id='ww-ieltsa-writing-202609-10-2-reference-v1';
  await p.locator('[data-ww-pick="'+id+'"]').click();
  await field(p,id+'-first').waitFor({state:'visible'});await p.waitForTimeout(150);
  const box=await field(p,id+'-first').boundingBox();assert(box.y>=0&&box.y<844,JSON.stringify(box));
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await field(p,id+'-first').fill('COMBINED MOBILE NAVIGATION DRAFT');
  await p.screenshot({path:path.join(__dirname,'combined-mobile-entry-chain.png')});
  await p.reload({waitUntil:'domcontentloaded'});
  assert.equal(await field(p,id+'-first').inputValue(),'COMBINED MOBILE NAVIGATION DRAFT');
  assert(await p.locator('#'+id+'-draft').isVisible());
 },{mobile:true});
 await check('32 task entries render the exact prompt, eight original figures and direct origins',async p=>{
   assert.equal(await p.locator('#ww-task-picker option').count(),32);
   for(const q of questions){await route(p,q.id);assert.equal(await field(p,'ww-active-task').inputValue(),q.id);assert((await p.locator('#'+q.id+' .ww-prompt').textContent()).includes(q.prompt));assert.equal(await p.locator('#'+q.id+' .ww-figure img').count(),q.image?1:0);assert(await p.locator('#'+q.id+'-draft').isVisible());}
 });
 await check('new Task 2 completes outline→first→freeze→four dimensions→revision versions→export and reload',async p=>{
  const id='ww-jiufen-20260921-adult-literacy-v1',text='Adults who cannot read may struggle to understand employment information. Governments can provide evening courses that fit around existing work.';
  await stage(p,id,'plan');await field(p,id+'-plan-1').fill('Two questions: disadvantages and government support.');
  await stage(p,id,'draft');await field(p,id+'-first').fill(text);await p.locator('#'+id+' [data-ww-action=timer]').click();
  await p.locator('#'+id+' [data-ww-action=freeze]').click();assert(await field(p,id+'-first').evaluate(e=>e.readOnly));assert(await p.locator('#'+id+'-review').isVisible());
  for(const code of ['task','coherence','lexical','grammar']){const f=field(p,id+'-check-'+code);await f.locator('xpath=ancestor::details').locator('summary').click();await f.selectOption('checked');await field(p,id+'-evidence-'+code).fill('Evidence from my own sentence, checked in context.');}
  await field(p,id+'-revision').fill(text+' Public information should also use accessible language.');await field(p,id+'-reason').fill('Added a matching measure.');await p.locator('#'+id+' [data-ww-action=version]').click();
  assert.equal(JSON.parse(await field(p,id+'-versions').inputValue()).length,1);
  const downloaded=p.waitForEvent('download');await p.locator('#'+id+' [data-ww-action=export]').click();const d=await downloaded;await d.saveAs(path.join(__dirname,'combined-export-new-task.txt'));
  const output=fs.readFileSync(path.join(__dirname,'combined-export-new-task.txt'),'utf8');assert(output.includes(text)&&output.includes('成人读写困难')&&output.includes('九分学长'));
  await p.reload({waitUntil:'domcontentloaded'});assert.equal(await field(p,id+'-first').inputValue(),text);assert(await field(p,id+'-first').evaluate(e=>e.readOnly));assert(await p.locator('#'+id+'-review').isVisible());
 });
 await check('old six records and same-source learning/practice/test drafts remain byte-for-byte independent',async p=>{
  const q=questions.find(q=>q.id==='ww-jobs');await route(p,'writing1-first');
  const b=p.locator('#writing1-first > .ww-origin-link [data-ww-open=ww-jobs]');await b.click();await p.locator('#ww-jobs-review').waitFor({state:'visible'});
  assert((await p.locator('#ww-jobs [data-ww-related]').textContent()).includes('学习'));assert((await p.locator('#ww-jobs [data-ww-related]').textContent()).includes('练习段落'));assert((await p.locator('#ww-jobs [data-ww-related]').textContent()).includes('测试'));
  assert.equal(await p.locator('#ww-jobs .ww-back-origin').getAttribute('href'),'#writing1-first');
  const record=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)).fields,KEY);
  for(const id of ['jobs','bricks','cafe','primary','tourism','housing']){assert.equal(record['ww-'+id+'-first'],'OLD-'+id);assert.equal(record['ww-'+id+'-versions'],JSON.stringify([{at:'2026-09-01T00:00:00.000Z',text:'REV-'+id,reason:'unchanged'}]));}
  assert.equal(record['writing1-essay'],'LEARNING ORIGINAL');assert.equal(record['case-wc-c21-t1-jobs-answer'],'PRACTICE ORIGINAL');assert.equal(record['full-test-writing-task1'],'TEST ORIGINAL');
 },{seed:Object.assign({'writing1-essay':'LEARNING ORIGINAL','case-wc-c21-t1-jobs-answer':'PRACTICE ORIGINAL','full-test-writing-task1':'TEST ORIGINAL'},...['jobs','bricks','cafe','primary','tourism','housing'].map(id=>({['ww-'+id+'-first']:'OLD-'+id,['ww-'+id+'-revision']:'REV-'+id,['ww-'+id+'-first-at']:'2026-09-01T00:00:00.000Z',['ww-'+id+'-versions']:JSON.stringify([{at:'2026-09-01T00:00:00.000Z',text:'REV-'+id,reason:'unchanged'}])})))});
 await check('saving failure cannot half-lock a new first draft',async p=>{
  const id='ww-ieltsa-writing-202609-1-2-reference-v1';await route(p,id);await field(p,id+'-first').fill('A draft that remains editable when storage fails.');
  await p.evaluate(({key,id})=>{const original=Storage.prototype.setItem;window.originalSet=original;Storage.prototype.setItem=function(k,v){if(k===key&&JSON.parse(v).fields[id+'-revision'])throw new DOMException('quota','QuotaExceededError');return original.call(this,k,v)}},{key:KEY,id});
  await p.locator('#'+id+' [data-ww-action=freeze]').click();assert.equal(await field(p,id+'-first').evaluate(e=>e.readOnly),false);assert.equal(await field(p,id+'-first-at').inputValue(),'');assert((await p.locator('#ww-notice').textContent()).includes('未能保存'));
 });
 await check('a failed return-location write is explicit and never changes essay or locks the draft',async p=>{
  await route(p,'ww-jobs');await field(p,'ww-jobs-first').fill('Preserved working draft.');
  await p.evaluate(key=>{const original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===key&&JSON.parse(v).fields['ww-jobs-return-route'])throw new DOMException('quota','QuotaExceededError');return original.call(this,k,v)}},KEY);
  await route(p,'writing1-first');await p.locator('#writing1-first > .ww-origin-link [data-ww-open=ww-jobs]').click();
  assert((await p.locator('#ww-notice').textContent()).includes('返回位置未能保存'));assert.equal(await field(p,'ww-jobs-first').inputValue(),'Preserved working draft.');assert.equal(await field(p,'ww-jobs-first').evaluate(n=>n.readOnly),false);assert.equal(await p.locator('#ww-jobs .ww-back-origin').getAttribute('href'),'#writing1-first');
 });
 await check('mobile choosing a task opens first draft within one screen; prompt, stages and resume remain usable',async p=>{
  assert(await p.locator('.ww-directory').isVisible());assert.equal(await p.locator('.ww-directory-row:visible').count(),32);await p.screenshot({path:path.join(__dirname,'combined-mobile-directory.png')});
  const id='ww-ieltsa-writing-202609-10-2-reference-v1';await p.locator('#ww-directory-search').fill('独居');assert.equal(await p.locator('.ww-directory-row:visible').count(),1);assert((await p.locator('.ww-directory-row:visible').textContent()).includes('难度系数 3/5'));await p.locator('[data-ww-pick="'+id+'"]').click();await p.locator('#'+id+'-draft').waitFor({state:'visible'});await p.waitForTimeout(120);
  const box=await field(p,id+'-first').boundingBox();assert(box.y>=0&&box.y<844,JSON.stringify(box));
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await field(p,id+'-first').fill('Mobile first draft survives returning.');await p.screenshot({path:path.join(__dirname,'combined-mobile-draft.png')});
  await p.locator('#'+id+' [data-ww-prompt-toggle]').click();assert(await p.locator('#'+id+' .ww-prompt').isVisible());
  await stage(p,id,'plan');await field(p,id+'-plan-1').fill('Optional mobile plan.');await route(p,'study');await route(p,'writing-workbench');assert.equal(await field(p,'ww-active-task').inputValue(),id);assert(await p.locator('#'+id+'-plan').isVisible());
  await p.reload({waitUntil:'domcontentloaded'});assert(await p.locator('#'+id+'-plan').isVisible());assert.equal(await field(p,id+'-first').inputValue(),'Mobile first draft survives returning.');
  await p.locator('#'+id+' [data-ww-catalogue]').click();assert(await p.locator('.ww-directory').isVisible());await p.locator('#ww-directory-search').fill('成人');assert.equal(await p.locator('.ww-directory-row:visible').count(),1);
 },{mobile:true});
 await check('desktop flat catalogue lists truthful metadata and search reaches a case draft',async p=>{
  await p.locator('#ww-directory-search').fill('雨影');
  assert.equal(await p.locator('.ww-directory-row:visible').count(),1);assert((await p.locator('.ww-directory-row:visible').textContent()).includes('难度未评估'));
  await p.locator('.ww-directory-row:visible').click();await p.locator('#ww-wc-c21-t3-rainshadow-v1-draft').waitFor({state:'visible'});await p.screenshot({path:path.join(__dirname,'combined-desktop-draft.png')});
 });
 await check('nine formerly external references have direct catalog routes and same shared workbench links',async p=>{
  for(const q of questions.filter(q=>q.newOrigin)){await route(p,q.origin);const node=p.locator('#'+q.origin);assert(await node.isVisible());assert.equal(await node.locator('[data-ww-open]').getAttribute('href'),'#'+q.id);assert(await p.evaluate(id=>JSON.parse(document.getElementById('learning-adjust-data').textContent).units.some(u=>u.id===id),q.origin));}
 });
 await check('reading expression preparation is exact and connects back to the same reading materials',async p=>{
  const id='ww-housing';await route(p,'writing2-case-wc-c21-t1-homes');await p.locator('#writing2-case-wc-c21-t1-homes [data-reading-source=rd-c21-t3-dart-city] > summary').click();
  await p.locator('#writing2-case-wc-c21-t1-homes [data-ww-open=ww-housing]').click();
  const prep=p.locator('#ww-housing .ww-reading-prep');assert(await prep.evaluate(n=>n.open));assert((await prep.locator('[data-reading-source=rd-c21-t3-dart-city]').textContent()).includes('on the periphery'));assert.equal(await prep.locator('[data-reading-source=rd-c21-t3-dart-city] a').getAttribute('href'),'#material-reading-rd-c21-t3-dart-city');
 });
 }finally{
 await browser.close();server.close();const report={candidate,candidate_sha256:require('crypto').createHash('sha256').update(bytes).digest('hex'),candidateSha256:require('crypto').createHash('sha256').update(bytes).digest('hex'),pass:checks.every(c=>c.pass)&&!errors.length,checks,errors};fs.writeFileSync(path.join(__dirname,'qa-combined.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
