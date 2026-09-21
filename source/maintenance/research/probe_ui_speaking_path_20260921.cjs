const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {snapshot,settle,jump,base,out}=require('./probe_ui_routes_20260921.cjs');
let browser;const results=[],checks=[],errors=[];
(async()=>{
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
 await page.goto(base+'#speaking-first',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true',null,{timeout:120000});
 const before=await snapshot(page,'speaking-first','before-first-save');results.push(before);
 const textarea=page.locator('#speaking-first textarea:visible').first();await textarea.fill('隔离探针：检查文字记录保存后的页面衔接，不是真实学习记录。');
 await page.locator('#speaking-first').getByRole('button',{name:'保存首次作答，进入学习',exact:true}).click();await settle(page);
 results.push(await snapshot(page,'speaking-first','after-first-save'));
 checks.push({name:'口语首次作答保存与进入学习',actual:await page.evaluate(()=>location.hash),visibleText:await page.locator('#speaking').innerText()});
 await jump(page,'test-speaking');await page.locator('#test-speaking').getByRole('button',{name:'开始本次测试',exact:true}).click();await settle(page);
 results.push(await snapshot(page,'test-speaking','test-started'));
 checks.push({name:'口语整科测试开始后的动作',recorders:await page.locator('#test-speaking [data-record]').count(),audioInputs:await page.locator('#test-speaking input[type="file"]').count(),text:await page.locator('#test-speaking').innerText()});
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'personal-speaking-test-started.png')});
 await context.close();fs.writeFileSync(path.join(out,'speaking-path.json'),JSON.stringify({results,checks,errors},null,2));console.log(JSON.stringify({snapshots:results.length,checks:checks.length,errors}));
})().catch(e=>{fs.writeFileSync(path.join(out,'speaking-path-failure.json'),JSON.stringify({error:e.stack,results,checks,errors},null,2));console.error(e);process.exitCode=1}).finally(async()=>browser&&await browser.close());
