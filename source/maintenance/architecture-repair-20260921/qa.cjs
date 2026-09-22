const fs=require('fs'),path=require('path'),http=require('http'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const here=__dirname,book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const target=process.argv[2]||'candidate',combined=target==='combined',candidateFile=combined?'combined.html':'candidate.html',assetRoot=path.resolve(here,'../content-pipeline/batches/jiufen-jijing-20260921/reviewed-assets'),live=target.startsWith('https:'),checks=[],errors=[],routes=[];let browser,server;
const add=(name,detail)=>{checks.push({name,detail,status:'pass'});console.log(name)};
async function ready(page){await page.waitForFunction(()=>window.IELTSCourseWindow&&window.IELTSRecordStore&&!document.body.hasAttribute('data-progressive-state'),null,{timeout:120000});}
async function go(page,id){await page.evaluate(id=>location.hash=id,id);await page.waitForTimeout(90);await page.waitForFunction(()=>[...document.querySelectorAll('main>.panel')].filter(n=>!n.hidden).length===1);}
async function active(page){return page.locator('main>.panel:not([hidden])').getAttribute('id')}
async function main(){
 let base=target;
 if(!live){const root=(target==='candidate'||combined)?null:path.resolve(target);server=http.createServer((req,res)=>{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1)||'index.html';const file=root?path.resolve(root,rel):rel==='index.html'?path.join(here,candidateFile):fs.existsSync(path.join(assetRoot,rel))?path.join(assetRoot,rel):path.resolve(book,rel);const allowed=root||book;if(!(file===path.join(here,candidateFile)||file.startsWith(allowed+path.sep)||file.startsWith(allowed+'/')||file.startsWith(assetRoot+path.sep))||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':({'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.mp3':'audio/mpeg'})[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(file).pipe(res)});await new Promise(r=>server.listen(0,'127.0.0.1',r));base='http://127.0.0.1:'+server.address().port+'/';}
 browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 if(!live)await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
 await context.addInitScript(()=>{if(!localStorage.getItem('architecture-fixture')){localStorage.setItem('architecture-fixture','1');localStorage.setItem('ielts-finished-book-v1',JSON.stringify({version:1,fields:{'lookup-history-v1':JSON.stringify([{term:'sustainable',key:'sustainable',meaning:'可持续的',favorite:true,lookupVersion:2}]),'sentence-collection-v1':JSON.stringify([{text:'Education creates opportunities.',translation:'教育创造机会。',direction:'en|zh-CN',title:'原材料',createdAt:'2026-09-19T00:00:00Z'}]),'workspace-reflection':'architecture isolated pre-existing record'},snapshots:{}}));}});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'#study',{waitUntil:'domcontentloaded',timeout:120000});await ready(page);
 assert.equal(await page.locator('[data-save]').count(),target==='candidate'?3368:3371);add('旧字段3368个全部保留');
 assert.equal(await page.locator('#learning-tools a').count(),3);assert.equal(await page.locator('#workspace .la-card').count(),4);
 for(const id of ['vocabulary-review','sentence-learning','writing-workbench']){await go(page,'study');await page.locator('#learning-tools a[href="#'+id+'"]').click();await page.waitForTimeout(120);assert.equal(await active(page),id);assert.equal(await page.locator('#workspace-navigation [aria-current="page"]').getAttribute('data-go'),'study');assert(await page.locator('#'+id+' .la-section-links a[href="#study"]').isVisible());await go(page,'study');assert.equal(await page.locator('#la-resume a').getAttribute('href'),'#'+id)}add('三个已有学习工具归学习，独立页头、返回与续学一致');
 await go(page,'vocabulary-review');assert.equal(await page.locator('#vr-list .vr-list-card').count(),1);await page.locator('[data-vr-quick-grade="known"]').click();assert.match(await page.locator('#vr-status').innerText(),/已标记/);assert(await page.locator('#records').isHidden());add('旧单词收藏恢复，直接标记仍可用');
 await go(page,'sentence-learning');assert.equal(await page.locator('#sentence-list .st-sentence').count(),1);assert.match(await page.locator('#sentence-list').innerText(),/Education creates/);add('旧句子记录在独立学习页恢复');
 await go(page,'records');assert.equal(await page.locator('[data-save="workspace-reflection"]').inputValue(),'architecture isolated pre-existing record');assert(await page.locator('#sentence-learning').isHidden());add('记录页保留旧答案，词句本不再内嵌');
 for(const [id,want] of [['writing1','study-writing1-list'],['writing2','study-writing2-list'],['practice-writing1','practice-writing1-list'],['practice-writing2','practice-writing2-list']]){await go(page,id);assert.equal(new URL(page.url()).hash,'#'+want)}add('Task 1和Task 2旧地址分别进入正确分类');
 await go(page,'pr-vocabulary-tourism');assert.equal(await page.locator('#workspace-navigation [aria-current="page"]').getAttribute('data-go'),'practice');assert.equal(await page.locator('.la-focus-nav a').getAttribute('href'),'#practice-vocabulary-list');await go(page,'practice');await page.locator('#architecture-practice-extras a').click();await page.locator('[data-catalog-unit="pr-vocabulary-tourism"]').waitFor();add('旅游词汇统一到练习/词汇，分类可实际进入');
 await go(page,'topic-education');assert.equal(await active(page),'background');assert.equal(await page.locator('.la-focus-nav a').getAttribute('href'),'#study-shared-list');add('每日教育背景目标的页面与返回均属共用背景');
 await go(page,'library');assert.equal(await page.locator('#library h1').innerText(),'原始资料');assert.equal(await page.locator('#library #text-question-directory').count(),0);await go(page,'resource-update');assert.equal(await active(page),'resource-update');assert(await page.locator('#res-search').isVisible());assert(await page.locator('#text-question-directory').isVisible());add('原始资料与学习资源索引分离，原目标ID保留');
 await go(page,'pp-reading');assert(await page.locator('#pp-reading').isVisible());assert.equal(await page.locator('main>.panel:not([hidden]) > .la-focus-nav').count(),1);add('题组包装入口聚焦集合');
 await go(page,'plan');assert.match(await page.locator('#plan > header').innerText(),/自选清单[\s\S]*手动移除/);assert.equal(await page.locator('#plan').getAttribute('data-la-owner'),'study');add('持久自选清单与每日安排分清');
 await go(page,'course-window');assert.equal(await page.locator('#cw-intake-save').isVisible(),false);assert.equal(await page.locator('#cw-import-file').isVisible(),false);assert.match(await page.locator('#course-window').innerText(),/待开放/);assert.equal(await page.locator('#workspace-navigation [aria-current="page"]').getAttribute('data-go'),'workspace');add('定制课程只留待开放窗口，制课导入试学均隐藏');
 await go(page,'course-design');assert.equal(await page.locator('#cw-intake-save').isVisible(),false);assert.match(await page.locator('#content-intake-status').innerText(),/资料接入进度/);add('资料接入进度与定制课程占位分开');
 await page.reload({waitUntil:'domcontentloaded'});await ready(page);await go(page,'vocabulary-review');assert.equal(await page.locator('[data-vr-quick-grade="known"]').getAttribute('aria-pressed'),'true');add('刷新恢复词汇自评');
 // Check every previously inventoried address, sequentially, without claiming
 // that DOM reachability is equivalent to completing every learning operation.
 const ledger=JSON.parse(fs.readFileSync(path.join(here,'../research/interface-map-20260921/interface-map.json'),'utf8')).ledger;
 for(const row of (process.argv.includes('--smoke')?[]:ledger)){await go(page,row.requested);const result=await page.evaluate(id=>{const target=document.getElementById(id),shown=[...document.querySelectorAll('main>.panel')].filter(n=>!n.hidden);return{requested:id,actual:location.hash,targetExists:!!target,active:shown.map(n=>n.id),title:document.title}},row.requested);assert(result.targetExists,row.requested);assert.equal(result.active.length,1,row.requested);routes.push(result)}add('本轮逐地址重开完成（数量见记录；smoke不重复全量）',{count:routes.length});
 for(const width of [1440,390]){await page.setViewportSize({width,height:width===390?844:1000});for(const id of ['study','workspace','vocabulary-review','sentence-learning','course-window','course-design','library','resource-update','plan']){await go(page,id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),id+' overflow');await page.screenshot({path:path.join(here,`${live?'live':combined?'combined':target==='candidate'?'candidate':'packed'}-${width}-${id}.png`)});}add('桌面与手机九个架构界面布局无横向溢出');}
 if(combined||live||target!=='candidate'){
 const pkg=JSON.parse(fs.readFileSync(path.join(assetRoot,'../cleaned-luna-20260921/reviewed-package.json'),'utf8'));
 for(const u of pkg.units){
  for(const skill of ['reading','shared']){
   await go(page,'study-'+skill+'-list');const card=page.locator('[data-catalog-unit="'+u.id+'"]');
   assert(await card.isVisible());assert.match(await card.locator('.content-entry-metadata').innerText(),/4\/5.*置信度低.*九分学长/);
   await card.locator('a[href="#'+u.id+'"]').first().click();await page.waitForTimeout(100);
   assert.equal(await page.locator('.la-focus-nav a').getAttribute('href'),'#study-'+skill+'-list');
  }
  const unit=page.locator('#'+u.id);assert.equal(await unit.locator('.content-entry-metadata').count(),0);
  assert.match(await unit.innerText(),/读懂这一段/);await unit.locator('details summary').click();
  const href=await unit.locator('details a').getAttribute('href');const response=await context.request.get(new URL(href,base).href);assert.equal(response.status(),200);
  const original=await response.text();assert(original.includes(u.sourceTitle));assert(original.includes(u.id));
  await unit.locator('input[type=checkbox]').check();await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert(await page.locator('#'+u.id+' input[type=checkbox]').isChecked());
 }
 add('三份精读从阅读和背景共用同一单元，入口标注、上下文、全文和保存恢复通过');
 await go(page,pkg.units[0].id);await page.screenshot({path:path.join(here,'combined-reading-mobile.png'),fullPage:true});
}
assert.deepEqual(errors,[]);await context.close();
}
main().then(()=>fs.writeFileSync(path.join(here,'qa-'+(live?'live':combined?'combined':target==='candidate'?'candidate':'packed')+'.json'),JSON.stringify({pass:true,target,checkedAt:new Date().toISOString(),checks,errors,routes},null,2))).catch(e=>{console.error(e);fs.writeFileSync(path.join(here,'qa-failure.json'),JSON.stringify({target,checks,errors,error:e.stack,routes},null,2));process.exitCode=1}).finally(async()=>{if(browser)await browser.close();server?.close()});
