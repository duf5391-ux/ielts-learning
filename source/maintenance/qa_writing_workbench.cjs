/* Meaningful writing lifecycle checks in an isolated browser context. */
const {chromium} = require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const http = require('http');
const assert = require('assert/strict');
const book = 'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const out = path.join(__dirname,'writing-workbench-qa');
const preview = fs.readFileSync(path.join(out,'preview.html'),'utf8').replace(/<base href="[^"]+">/,'');
const checks = [];
const key = 'ielts-finished-book-v1';
const server = http.createServer((req,res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  if (url === '/' || url === '/开始学习.html') {res.setHeader('Content-Type','text/html;charset=utf-8');res.end(preview);return;}
  const file = path.resolve(book,'.'+url);
  if (!file.startsWith(path.resolve(book)+path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {res.statusCode=404;res.end();return;}
  const types={'.js':'text/javascript','.css':'text/css','.png':'image/png','.json':'application/json','.svg':'image/svg+xml'};
  res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
const field = (page,name) => page.locator(`[data-save="${name}"]`);
async function main() {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const page=await context.newPage();
  page.setDefaultTimeout(8000);
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  async function check(name,fn) {
    try {await fn();checks.push({name,pass:true});}
    catch(e){checks.push({name,pass:false,error:e.stack});}
  }
  async function route(id) {await page.evaluate(id=>location.hash=id,id);await page.waitForFunction(id=>!document.getElementById(id).closest('[data-ww-unit]').hidden,id);}
  try {
    await page.goto(origin+'/开始学习.html#ww-primary',{waitUntil:'domcontentloaded'});
    await check('deep task route reveals the writing panel and selected task',async()=>{
      assert(await page.locator('#writing-workbench').isVisible());
      assert(await page.locator('#ww-primary').isVisible());
      assert.equal(await page.locator('#ww-task-picker').inputValue(),'ww-primary');
    });
    const draft='Structured classroom games help children practise taking turns. Direct instruction remains necessary when pupils encounter a new concept.';
    await check('separate tasks keep plans and drafts without mixing',async()=>{
      await field(page,'ww-primary-plan-1').fill('Two questions: degree of agreement and importance of play.');
      await field(page,'ww-primary-first').fill(draft);
      await route('ww-housing');
      await field(page,'ww-housing-first').fill('Tall buildings can increase the number of homes on a small site.');
      await route('ww-primary');
      assert.equal(await field(page,'ww-primary-first').inputValue(),draft);
      assert((await page.locator('#ww-primary [data-ww-count="ww-primary-first"]').textContent()).includes('18 词'));
    });
    await check('timer survives reload with original deadline',async()=>{
      await page.locator('#ww-primary [data-ww-action="timer"]').click();
      const first=JSON.parse(await field(page,'ww-primary-timer').inputValue());
      assert.equal(first.status,'running');
      await page.reload({waitUntil:'domcontentloaded'});
      const after=JSON.parse(await field(page,'ww-primary-timer').inputValue());
      assert.equal(after.deadline,first.deadline);
      assert.equal(await page.locator('#ww-primary [data-ww-action="timer"]').textContent(),'暂停计时');
    });
    await check('freezing preserves original and creates independent revision',async()=>{
      await page.locator('#ww-primary [data-ww-action="freeze"]').click();
      assert(await field(page,'ww-primary-first').evaluate(e=>e.readOnly));
      assert.equal(await field(page,'ww-primary-revision').inputValue(),draft);
      await field(page,'ww-primary-revision').fill(draft+' For example, a shop game can provide a reason to use numbers.');
      await field(page,'ww-primary-reason').fill('Added an example that shows the mechanism.');
      await field(page,'ww-primary-check-task').selectOption('checked');
      await field(page,'ww-primary-evidence-task').fill('Both questions now have explicit answers.');
      await page.locator('#ww-primary [data-ww-action="version"]').click();
      await field(page,'ww-primary-revision').fill(draft+' A second independently edited revision.');
      await page.locator('#ww-primary [data-ww-action="version"]').click();
      assert.equal(JSON.parse(await field(page,'ww-primary-versions').inputValue()).length,2);
      await page.reload({waitUntil:'domcontentloaded'});
      assert.equal(await field(page,'ww-primary-first').inputValue(),draft);
      assert(await field(page,'ww-primary-first').evaluate(e=>e.readOnly));
      assert.equal(await field(page,'ww-primary-check-task').inputValue(),'checked');
      assert.equal(JSON.parse(await field(page,'ww-primary-versions').inputValue()).length,2);
    });
    await check('hints mark support and next action follows the chosen dimension',async()=>{
      await page.locator('#ww-primary details[data-ww-support] > summary').first().click();
      assert(await field(page,'ww-primary-used-help').isChecked());
      await field(page,'ww-primary-next-focus').selectOption('lexical');
      assert((await page.locator('#ww-primary [data-ww-next]').textContent()).includes('搭配'));
      await field(page,'ww-primary-next-date').fill('2026-09-22');
      await page.reload({waitUntil:'domcontentloaded'});
      assert(await field(page,'ww-primary-used-help').isChecked());
      assert.equal(await field(page,'ww-primary-next-date').inputValue(),'2026-09-22');
    });
    await check('export contains original, revisions and a specific feedback request',async()=>{
      const downloadEvent=page.waitForEvent('download');
      await page.locator('#ww-primary [data-ww-action="export"]').click();
      const download=await downloadEvent;
      const file=path.join(out,'isolated-test-export.txt');
      await download.saveAs(file);
      const text=fs.readFileSync(file,'utf8');
      assert(text.includes(draft));assert(text.includes('second independently'));assert(text.includes('TA/TR'));
    });
    await check('nested hashes choose correct task; mobile layout has no overflow',async()=>{
      await route('ww-bricks-plan');
      assert.equal(await page.locator('#ww-task-picker').inputValue(),'ww-bricks');
      assert(await page.locator('#ww-bricks').isVisible());
      await page.setViewportSize({width:390,height:844});
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.waitForTimeout(500); // Allow the existing sidebar's CSS resize transition to finish.
      const sizes=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
      assert(sizes.scroll<=sizes.client+1,JSON.stringify(sizes));
      await page.screenshot({path:path.join(out,'mobile.png'),fullPage:false});
      await page.setViewportSize({width:1440,height:1000});
      await page.waitForTimeout(500);
      await page.screenshot({path:path.join(out,'desktop.png'),fullPage:false});
    });
    await check('blocked storage does not lock an unsaved first draft',async()=>{
      await route('ww-housing');
      await page.evaluate(()=>{Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError')};});
      await field(page,'ww-housing-first').fill('A changed draft that cannot be persisted.');
      await page.locator('#ww-housing [data-ww-action="freeze"]').click();
      assert.equal(await field(page,'ww-housing-first').evaluate(e=>e.readOnly),false);
      assert.equal(await field(page,'ww-housing-first-at').inputValue(),'');
      assert((await page.locator('#ww-notice').textContent()).includes('未能保存'));
      await page.reload({waitUntil:'domcontentloaded'});
    });
    await check('malformed version history is preserved and not overwritten',async()=>{
      await page.evaluate(key=>{const x=JSON.parse(localStorage.getItem(key));x.fields['ww-primary-versions']='broken prior record';localStorage.setItem(key,JSON.stringify(x));},key);
      await page.reload({waitUntil:'domcontentloaded'});
      await route('ww-primary');
      await page.locator('#ww-primary [data-ww-action="version"]').click();
      assert.equal(await field(page,'ww-primary-versions').inputValue(),'broken prior record');
      assert((await page.locator('#ww-notice').textContent()).includes('未覆盖'));
    });
    await check('no JavaScript page errors',async()=>assert.deepEqual(errors,[]));
  } finally {
    fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify({checks,errors},null,2));
    await browser.close();server.close();
  }
  console.log(JSON.stringify(checks));
  if(checks.some(c=>!c.pass))process.exitCode=1;
}
main().catch(e=>{console.error(e);server.close();process.exitCode=1;});
