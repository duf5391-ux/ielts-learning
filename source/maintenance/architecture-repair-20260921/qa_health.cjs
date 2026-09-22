const fs=require('fs'),path=require('path'),http=require('http'),assert=require('node:assert/strict'),crypto=require('crypto');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const here=__dirname,book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const target=process.argv[2]||'candidate',live=/^https:/.test(target),checks=[],errors=[];let browser,server;
const add=(name,detail)=>checks.push({name,status:'pass',detail});
const daily=page=>page.evaluate(()=>JSON.parse(document.getElementById('daily-study-state').value));
async function ready(page){await page.waitForFunction(()=>window.IELTSRecordStore&&document.getElementById('hs-finish')&&(!document.body.hasAttribute('data-progressive-state')),{},{timeout:120000});}
async function main(){
 let base=target;
 if(!live){
  const stage=target==='candidate'?null:path.resolve(target);
  server=http.createServer((req,res)=>{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1)||'index.html';const file=stage?path.resolve(stage,rel):rel==='index.html'?path.join(here,'combined.html'):fs.existsSync(path.join(here,'jijing/assets',rel))?path.join(here,'jijing/assets',rel):path.resolve(book,rel);if(![stage||book,here].some(root=>file.startsWith(root))||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}const types={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.mp3':'audio/mpeg','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'};res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(file).pipe(res);});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));base='http://127.0.0.1:'+server.address().port+'/';
 }
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844}});
 if(!live)await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 const response=await page.goto(base+'#guide',{waitUntil:'domcontentloaded',timeout:120000});assert.equal(response.status(),200);await ready(page);
 const html=await response.body();add('Homepage and full control initialization',{bytes:html.length,sha256:crypto.createHash('sha256').update(html).digest('hex'),progressive:await page.evaluate(()=>document.documentElement.dataset.progressiveReady==='true')});
 assert.equal(await page.locator('[data-save]').count(),3371);assert.equal(await page.locator('[data-learning-unit]').count(),227);add('All 3371 saved fields and 227 learning units assembled');
 assert.equal(await page.locator('script#vocabulary-quick-marks-script').count(),1);assert(await page.evaluate(()=>!!window.IELTSRecordStore));
 await page.locator('[data-ds-minutes="15"]').click();await page.locator('[data-ds-skill="vocabulary"]').click();await page.locator('#ds-start').click();await page.locator('#hs-rest').waitFor();assert.equal((await daily(page)).session.status,'active');
 await page.locator('#hs-rest').click();await page.waitForFunction(()=>JSON.parse(document.getElementById('daily-study-state').value).session.status==='paused');assert.equal(await page.evaluate(()=>window.IELTSEnergyControl.read().mode),'break');assert(await page.locator('#ds-next').isDisabled());add('Rest pauses daily study and prevents advancement');
 await page.locator('#ds-pause').click();assert.equal((await daily(page)).session.status,'active');assert.notEqual(await page.evaluate(()=>window.IELTSEnergyControl.read().mode),'break');add('Continue ends rest and resumes study');
 await page.locator('#hs-finish').click();await page.locator('#ds-completed').waitFor();assert.equal((await daily(page)).session.status,'ended');assert(await page.locator('#daily-study-dock').isHidden());
 await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert.equal((await daily(page)).session.status,'ended');assert(await page.locator('#ds-completed').isVisible());add('Finish completes and restores after reload');
 await page.evaluate(()=>location.hash='topical-vocabulary');await page.locator('.tv-card[data-tv-id="education-curriculum"] [data-vq-value="K"]').click();assert.equal(await page.locator('[data-save="topic-vocab-level-education-curriculum"]').inputValue(),'K');add('Published direct vocabulary mark is usable on mobile');
 const unit='pr-jiufen-20260921-origin-language-v1';await page.evaluate(id=>location.hash=id,unit);await page.locator('#'+unit).waitFor();assert.match(await page.locator('#'+unit+' .jj-update-meta').innerText(),/新内容[\s\S]*4\/5/);await page.locator('#'+unit+' details[data-answer-gate] summary').click();assert(await page.locator('#'+unit+' .la-gate-content').isHidden());
 const answer=page.locator('#'+unit+' [data-save]').first();await answer.fill('B - isolated release check');await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert.equal(await answer.inputValue(),'B - isolated release check');add('New reading deep link, difficulty, empty-answer gate and saved response');
 await page.locator('#'+unit+' h2').scrollIntoViewIfNeeded();assert(await page.locator('#'+unit).isVisible());
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(here,'release-'+(live?'live':target==='candidate'?'candidate':'packed')+'.png')});assert.deepEqual(errors,[]);
 if(live){
   const urls=await page.locator('audio[src],audio source[src]').evaluateAll(nodes=>nodes.map(n=>n.src).filter(u=>/^https:/.test(u)&&new URL(u).origin===location.origin));
   for(const url of [...new Set(urls)].slice(0,2)){const r=await context.request.get(url,{headers:{Range:'bytes=0-1023'},timeout:60000});assert([200,206].includes(r.status()));assert((await r.body()).length>0);add('Live audio bytes accessible',{url,status:r.status()});}
 }
 await context.close();
}
main().then(()=>{const report={pass:true,target,checkedAt:new Date().toISOString(),checks,errors};fs.writeFileSync(path.join(here,'release-'+(live?'live':target==='candidate'?'candidate':'packed')+'.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));}).catch(e=>{console.error(e);fs.writeFileSync(path.join(here,'release-failure.json'),JSON.stringify({target,checks,errors,error:e.stack},null,2));process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server?.close();});
