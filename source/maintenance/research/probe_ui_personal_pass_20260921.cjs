// Sequential, isolated browser inspection. No runtime files or user browser records are modified.
const fs = require('fs'), path = require('path');
const {chromium} = require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {snapshot, settle, jump, base, out} = require('./probe_ui_routes_20260921.cjs');
const results = [], checks = [], errors = [];
let browser;
async function main() {
  browser = await chromium.launch({channel:'msedge', headless:true});
  const context = await browser.newContext({viewport:{width:390,height:844}});
  await context.addInitScript(() => localStorage.setItem('ielts-finished-book-v1', JSON.stringify({version:1,fields:{'lookup-history-v1':JSON.stringify([{key:'sustainable',term:'sustainable',meaning:'可持续的',favorite:true,lastAt:'2020-01-01T00:00:00Z'}])},snapshots:{}})));
  const page = await context.newPage(); page.setDefaultTimeout(10000); page.on('pageerror', e => errors.push(e.message));
  await page.goto(base+'#vocabulary-review', {waitUntil:'domcontentloaded',timeout:120000});
  await page.waitForFunction(() => document.documentElement.dataset.progressiveReady==='true' && window.IELTSLookup, null, {timeout:120000});
  const word = page.locator('#vr-list .vr-list-card').first();
  await word.getByRole('button',{name:'会',exact:true}).click(); await settle(page);
  checks.push({name:'单词表直接标记会',text:await word.innerText(),saved:await page.evaluate(()=>IELTSLookup.getHistory()[0])});
  await jump(page,'sentence-learning');
  await page.locator('#sentence-learning [data-open-sentence]').click();
  await page.locator('#sentence-source').fill('Public transport can reduce traffic congestion.');
  await page.locator('#sentence-result').fill('公共交通能够缓解交通拥堵。');
  await page.locator('#sentence-save').click(); await settle(page);
  if (await page.locator('#sentence-popup').isVisible()) await page.locator('#sentence-close').click();
  await page.locator('#sentence-learning').scrollIntoViewIfNeeded();
  results.push(await snapshot(page,'sentence-learning','mobile-personal-pass'));
  checks.push({name:'句子本保存后的学习与返回控件',text:await page.locator('#sentence-list').innerText(),links:await page.locator('#sentence-list a').evaluateAll(es=>es.map(e=>({text:e.textContent,href:e.getAttribute('href')})))});
  await page.screenshot({path:path.join(out,'personal-sentence-populated.png')});
  await jump(page,'writing-workbench'); await page.locator('#ww-task-picker').selectOption('ww-tourism');
  await page.evaluate(()=>scrollTo(0,0)); await settle(page);
  results.push(await snapshot(page,'writing-workbench','mobile-personal-pass'));
  const steps=await page.locator('#ww-tourism a[href^="#"]').evaluateAll(es=>es.map(e=>({text:e.innerText,href:e.getAttribute('href')})));
  checks.push({name:'写作工作台阶段导航',steps});
  const draftLink=steps.find(x=>/首稿/.test(x.text));
  if(draftLink){await page.locator('#ww-tourism a[href="'+draftLink.href+'"]').click();await settle(page);results.push(await snapshot(page,draftLink.href.slice(1),'writing-draft-click'));}
  for (const id of ['study-speaking-list','speaking-first','speaking-new-sep26-journeys','pr-speaking-p1','pr-speaking-p2','pr-speaking-p3','test-speaking']) {
    await jump(page,id);await page.evaluate(()=>scrollTo(0,0));await settle(page);
    results.push(await snapshot(page,id,'mobile-personal-pass'));
    checks.push({name:'口语页面动作检查',route:id,controls:await page.locator('main > .panel:visible [data-record], main > .panel:visible [data-stop], main > .panel:visible input[type="file"], main > .panel:visible audio').evaluateAll(es=>es.filter(e=>e.getClientRects().length).map(e=>({tag:e.tagName,record:e.dataset.record,stop:e.dataset.stop,id:e.id,text:e.innerText,accept:e.accept,src:e.getAttribute('src'),y:Math.round(e.getBoundingClientRect().y+scrollY)})))});
    await page.screenshot({path:path.join(out,'personal-'+id+'.png')});
  }
  fs.writeFileSync(path.join(out,'personal-pass.json'),JSON.stringify({scope:'Sequential inspection in a fresh synthetic browser context',results,checks,errors},null,2));
  console.log(JSON.stringify({snapshots:results.length,checks:checks.length,errors}));
  await context.close();
}
main().catch(e=>{fs.writeFileSync(path.join(out,'personal-failure.json'),JSON.stringify({error:e.stack,results,checks,errors},null,2));console.error(e);process.exitCode=1;}).finally(async()=>browser&&await browser.close());
