const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {snapshot,settle,jump,base,out}=require('./probe_ui_routes_20260921.cjs');
let browser;const findings=[],snapshots=[],errors=[];
async function main(){
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1280,height:900}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
 await page.goto(base+'#topical-vocabulary',{waitUntil:'domcontentloaded',timeout:120000});await page.waitForFunction(()=>document.documentElement.dataset.progressiveReady==='true'&&window.IELTSLookup,{},{timeout:120000});
 const card=page.locator('.tv-card[data-tv-id="education-curriculum"]');await card.locator('input[type=checkbox]').check();
 const saved=await card.locator('input[type=checkbox]').evaluate(e=>({key:e.dataset.save,value:e.checked}));await jump(page,'workspace');await page.locator('#workspace a[href="#vocabulary-review"]').click();await settle(page);
 findings.push({case:'1000词卡收藏后打开我的单词表',topicSaved:saved,myVocabularyCount:await page.locator('#vr-list .vr-list-card').count(),lookupFavorites:await page.evaluate(()=>window.IELTSLookup.getHistory().filter(x=>x.favorite===true).length),text:await page.locator('#vocabulary-review').innerText()});
 await page.locator('#vocabulary-review').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'favorite-does-not-enter-word-list.png')});
 await jump(page,'study-reading-list');const first=page.locator('#la-study-cards [data-catalog-unit]').first();const chosen=await first.getAttribute('data-catalog-unit');await first.getByRole('button',{name:'加入今天',exact:true}).click();await jump(page,'plan');const planText=await page.locator('#la-plan-list').innerText();await jump(page,'guide');
 findings.push({case:'加入今天与直接开始安排关系',chosen,planText,dailyPlanTitle:await page.locator('#ds-plan-title').innerText(),dailyPlanReason:await page.locator('#ds-plan-reason').innerText(),dailySteps:await page.locator('#ds-steps').innerText(),selectedKeys:await page.evaluate(()=>JSON.parse(document.querySelector('[data-save="learning-adjust-state"]').value).today)});
 for(const mode of ['study','practice'])for(const task of ['writing1','writing2']){await jump(page,mode+'-writing-list');await page.locator('#'+mode+' a[href="#'+mode+'-'+task+'-list"]').click();await settle(page);snapshots.push(await snapshot(page,mode+'-'+task+'-list','clicked-task-list'));}
 await jump(page,'writing-workbench');const workbench=await page.locator('#ww-task-picker option').evaluateAll(items=>items.map(e=>({id:e.value,title:e.textContent})));
 findings.push({case:'写作题目与写作工作台覆盖范围',workbench,catalogWriting:await page.evaluate(()=>JSON.parse(document.getElementById('learning-adjust-data').textContent).units.filter(x=>/^writing/.test(x.skill)).map(x=>({id:x.id,title:x.title,mode:x.mode}))),newJijingAvailable:workbench.some(x=>/jiufen|识字|灭绝|工作.*平衡/.test(x.id+' '+x.title))});
 for(const id of ['pp-background','pr-background-fisheries','pp-vocabulary','pr-vocabulary-tourism']){if(await page.locator('[id="'+id+'"]').count()){await jump(page,id);snapshots.push(await snapshot(page,id,'classification-conflict'));}}
 await page.setViewportSize({width:390,height:844});
 for(const id of ['study-reading-list','study-writing1-list','practice-writing2-list','library','course-window']){await jump(page,id);await page.evaluate(()=>scrollTo(0,0));await settle(page);snapshots.push(await snapshot(page,id,'mobile-flow'));await page.screenshot({path:path.join(out,'mobile-flow-'+id+'.png')});}
 fs.writeFileSync(path.join(out,'flows.json'),JSON.stringify({scope:'Isolated synthetic browser records only; production files and user data unchanged',findings,snapshots,errors},null,2));console.log(JSON.stringify({findings:findings.map(x=>({case:x.case,chosen:x.chosen,myVocabularyCount:x.myVocabularyCount,newJijingAvailable:x.newJijingAvailable})),snapshots:snapshots.length,errors,output:out}));await context.close();
}
main().catch(e=>{fs.writeFileSync(path.join(out,'flow-failure.json'),JSON.stringify({error:e.stack,findings,snapshots,errors},null,2));console.error(e);process.exitCode=1}).finally(async()=>browser&&await browser.close());
