const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {base,out,jump,settle}=require('./probe_ui_routes_20260921.cjs');
const priorFile=path.join(out,'dynamic-interfaces-failure.json');
const results=fs.existsSync(priorFile)?JSON.parse(fs.readFileSync(priorFile)).results.filter(x=>x.name.startsWith('定制课程')):[],errors=[];let browser;
async function capture(page,name,selector){
 const node=page.locator(selector);results.push({name,url:page.url(),checkedAt:new Date().toISOString(),aria:await node.ariaSnapshot(),text:await node.innerText(),controls:await node.locator('button,input,select,textarea,summary,a').evaluateAll(es=>es.filter(e=>e.checkVisibility({checkVisibilityCSS:true,contentVisibilityAuto:true})).map(e=>({tag:e.tagName,id:e.id,text:e.innerText||e.placeholder||e.getAttribute('aria-label')||'',type:e.type,href:e.getAttribute('href')})))});
 console.log(name);
}
(async()=>{
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'#course-window',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true',null,{timeout:120000});
 if(!results.length){
 for(const label of ['添加这一批原料／能力要求','学习量与继续建议（可选）']){await page.locator('#course-window summary').filter({hasText:label}).click();await capture(page,'定制课程展开：'+label,'#course-window');}
 for(const label of ['1 先做一题','2 理解用法','3 练习','4 换个情境','5 可选加练']){await page.locator('#course-window').getByRole('button',{name:label,exact:true}).click();await settle(page);await capture(page,'定制课程阶段：'+label,'#course-window');}
 }
 await page.locator('#energy-control summary').click();await capture(page,'健康学习设置与控制','#energy-control');await page.locator('#energy-control summary').click();
 await jump(page,'guide');await page.locator('[data-ds-minutes="15"]').click();await page.locator('#ds-start').click();await settle(page);if(await page.locator('#hs-details').isVisible())await page.locator('#hs-details').click();await capture(page,'进行中的学习工具栏','#daily-study-dock');
 await page.locator('#daily-study-dock').getByRole('button',{name:'随手记',exact:true}).click();await capture(page,'随手记弹窗','dialog.ds-dialog');await page.locator('dialog.ds-dialog').getByRole('button',{name:'关闭',exact:true}).click();
 await page.locator('#hs-finish').click();await settle(page);await capture(page,'结束后的反馈与续学','#ds-completed');
 for(const id of ['listening','reading','writing','speaking']){await jump(page,'test-'+id);await page.locator('#test-'+id+' [data-test-start]').click();await settle(page);await capture(page,'整科测试开始：'+id,'#test-'+id);}
 await jump(page,'materials');await page.locator('#material-title').fill('界面探针临时资料');await page.locator('#material-content').fill('This is an isolated interface inspection.');await page.locator('#material-preview-button').click();await capture(page,'新增资料预览','#materials');await page.locator('#material-commit').click();await page.locator('#material-list').getByRole('button',{name:'打开 →',exact:true}).click();await capture(page,'新增资料阅读器','#material-reader');await page.locator('#material-reader').getByRole('button',{name:'编辑',exact:true}).click();await capture(page,'新增资料编辑','#materials');
 for(const target of ['完整词汇来源库.html','词频与原文证据.html']){
   await page.goto(base+target,{waitUntil:'domcontentloaded',timeout:120000});await page.locator('#next').waitFor({state:'visible'});await page.locator('#next').click();await capture(page,target+'：下一页','body');await page.locator('#prev').click();await page.locator('#q').fill('sustainable');await settle(page);await capture(page,target+'：搜索','body');
 }
 await page.goto(base+'本地词典.html',{waitUntil:'domcontentloaded',timeout:120000});await page.locator('#dictionary-input').fill('sustainable');await page.getByRole('button',{name:'查询',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.dictionary-entry')||/未能|暂未收录/.test(document.body.innerText),null,{timeout:45000});await capture(page,'独立词典查询结果','body');
 await page.setViewportSize({width:390,height:844});await page.goto(base+'#study',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true',null,{timeout:120000});await page.locator('#mobile-menu').click();await capture(page,'手机导航抽屉','#workspace-navigation');
 await context.close();fs.writeFileSync(path.join(out,'dynamic-interfaces.json'),JSON.stringify({scope:'Sequential clicks with disposable synthetic records only',results,errors},null,2));console.log(JSON.stringify({states:results.length,errors}));
})().catch(e=>{fs.writeFileSync(path.join(out,'dynamic-interfaces-failure.json'),JSON.stringify({error:e.stack,results,errors},null,2));console.error(e);process.exitCode=1;}).finally(async()=>browser&&await browser.close());
