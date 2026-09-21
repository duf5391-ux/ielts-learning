const {chromium,expect}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url'),assert=require('assert');
const root='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const qa=path.join(__dirname,'resource-expansion-qa');
const stateKey='ielts-finished-book-v1';
const sleepFrame=page=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
(async()=>{
  fs.mkdirSync(qa,{recursive:true});
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'resource-expansion-manifest.json'),'utf8'));
  const catalog=manifest.catalog,url=pathToFileURL(path.join(root,'开始学习.html')).href;
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const errors=[],failedRequests=[],checks=[],screenshots=[];
  const context=await browser.newContext({viewport:{width:1365,height:950},acceptDownloads:true});
  const page=await context.newPage();page.setDefaultTimeout(12000);
  page.on('pageerror',e=>errors.push(e.message));
  page.on('requestfailed',r=>failedRequests.push({url:r.url(),failure:r.failure()?.errorText}));
  async function check(name,fn){try{const detail=await fn();checks.push({name,pass:true,...(detail===undefined?{}:{detail})});}catch(e){checks.push({name,pass:false,error:e.message});}}
  async function hash(anchor){await page.evaluate(h=>location.hash=h,anchor);await sleepFrame(page);}
  async function screen(name){const out=path.join(qa,name+'.png');await page.screenshot({path:out});screenshots.push(out);}
  await page.goto(url+'#resource-update');
  await check('catalog panel and counts',async()=>{
    assert(await page.locator('#resource-update').isVisible());
    assert.equal(await page.locator('.res-card').count(),manifest.units);
    assert.equal(await page.locator('#current-page-label').textContent(),'本季题目与新增资源');
    assert((await page.locator('#res-count').textContent()).includes(String(manifest.units)));
    assert.equal(await page.locator('[data-save^="resource-note-"]').count(),manifest.units);
    const dup=await page.evaluate(()=>{const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);return [...new Set(ids.filter((x,i)=>ids.indexOf(x)!==i))]});
    assert.deepEqual(dup,[]);
  });
  await screen('desktop-catalog');
  await check('catalog filters and search',async()=>{
    for(const filter of ['current','background','reading','listening','writing1','writing2']){
      await page.locator(`[data-res-filter="${filter}"]`).click();
      const expected=catalog.filter(c=>filter==='current'?c.current:c.section===filter).length;
      assert.equal(await page.locator('.res-card:visible').count(),expected,filter);
      assert.equal(await page.locator(`[data-res-filter="${filter}"]`).getAttribute('aria-pressed'),'true');
    }
    await page.locator('[data-res-filter="all"]').click();await page.locator('#res-search').fill('QA-no-result-xyz');
    assert.equal(await page.locator('.res-card:visible').count(),0);assert(await page.locator('#res-empty').isVisible());
    await page.locator('#res-search').fill(catalog[0].title);assert.equal(await page.locator('.res-card:visible').count(),1);
    await page.locator('#res-search').fill('');assert.equal(await page.locator('.res-card:visible').count(),manifest.units);
  });
  await check('all new resource routes open usable content',async()=>{
    const tested=[];
    for(const c of catalog){
      await hash(c.anchor);const unit=page.locator('#'+c.anchor);
      assert(await page.locator('#'+c.section).isVisible(),c.anchor+' panel');
      assert(await unit.isVisible(),c.anchor+' unit');
      if(c.section!=='background')assert(await unit.evaluate(el=>el.open),c.anchor+' details');
      assert(await unit.locator(`[data-save="resource-note-${c.id}"]`).isVisible(),c.anchor+' note is available before exercise');
      assert.equal(await unit.locator(`[data-save="resource-note-${c.id}"]`).getAttribute('readonly'),null);
      const color=await unit.evaluate(el=>getComputedStyle(el.querySelector('h2,h3,summary,p')).color);assert.equal(color,'rgb(173, 36, 48)',c.anchor+' red label');
      tested.push(c.anchor);
    }
    return tested;
  });
  await check('catalog resource click and repeat click',async()=>{
    const c=catalog.find(c=>c.current)||catalog[0];await hash('resource-update');
    await page.locator(`.res-card[href="#${c.anchor}"]`).click();await sleepFrame(page);
    assert(await page.locator('#'+c.anchor).isVisible());
    await hash('resource-update');await page.locator(`.res-card[href="#${c.anchor}"]`).click();await sleepFrame(page);
    assert(await page.locator('#'+c.anchor).isVisible());
  });
  await check('new-content in-page jump stays on catalogue',async()=>{
    await hash('resource-update');await page.locator('[data-res-scroll-new]').click();await sleepFrame(page);
    assert(await page.locator('#resource-update').isVisible());
    const rect=await page.locator('#resource-new-list').boundingBox();assert(rect&&rect.y<350,'new list scrolled into view; y='+rect?.y);
  });
  const selected=catalog.find(c=>c.current)||catalog[0];
  await check('new fields save without overwriting original chapter',async()=>{
    await hash('reading');await page.locator('[data-save="reading-q1"]').fill('QA existing original answer');
    await hash(selected.anchor);await page.locator(`[data-save="resource-note-${selected.id}"]`).fill('QA resource note 2026-09-16');
    await page.locator(`[data-save="resource-learned-${selected.id}"]`).check();
    await page.locator(`[data-save="resource-review-${selected.id}"]`).check();await sleepFrame(page);
    const state=await page.evaluate(k=>JSON.parse(localStorage.getItem(k)),stateKey);
    assert.equal(state.fields['reading-q1'],'QA existing original answer');
    assert.equal(state.fields['resource-note-'+selected.id],'QA resource note 2026-09-16');
    assert.equal(state.fields['resource-learned-'+selected.id],true);assert.equal(state.fields['resource-review-'+selected.id],true);
    assert.deepEqual(state.snapshots,{});
    await page.reload();await sleepFrame(page);
    assert.equal(await page.locator(`[data-save="resource-note-${selected.id}"]`).inputValue(),'QA resource note 2026-09-16');
    assert(await page.locator(`[data-save="resource-learned-${selected.id}"]`).isChecked());
    assert(await page.locator(`[data-save="resource-review-${selected.id}"]`).isChecked());
  });
  await check('records count learned and review independently',async()=>{
    await hash('records');assert((await page.locator('#res-progress').textContent()).includes('新增资源已学 1 / '+manifest.units+'；加入复习 1 项'));
    assert.equal(await page.locator('#res-learned-list a').count(),1);assert.equal(await page.locator('#res-review-list a').count(),1);
    await page.locator('#res-review-list a').click();await sleepFrame(page);
    assert(await page.locator('#'+selected.anchor).isVisible());await page.locator(`[data-save="resource-review-${selected.id}"]`).uncheck();
    await hash('records');assert((await page.locator('#res-progress').textContent()).includes('加入复习 0 项'));
    assert.equal(await page.locator('#res-learned-list a').count(),1);
  });
  await check('background read count uses actual denominator',async()=>{
    const bg=catalog.find(c=>c.section==='background');await hash(bg.anchor);
    await page.locator(`[data-save="topic-read-${bg.id}"]`).check();await hash('records');
    const counts=await page.locator('#record-topics').innerText();const total=await page.locator('[data-save^="topic-read-"]').count();
    assert(counts.includes('1 '));assert(counts.includes('/ '+total+' 段'),counts+' vs total '+total);
  });
  await check('export and restore retain new and original fields',async()=>{
    await hash('records');const pending=page.waitForEvent('download');await page.locator('[data-export="json"]').click();
    const download=await pending,backup=path.join(qa,'qa-only-backup.json');await download.saveAs(backup);
    const data=JSON.parse(fs.readFileSync(backup,'utf8'));assert.equal(data.fields['resource-note-'+selected.id],'QA resource note 2026-09-16');
    assert.equal(data.fields['reading-q1'],'QA existing original answer');assert.equal(data.fields['resource-review-'+selected.id],false);
    const restoreContext=await browser.newContext({viewport:{width:1365,height:950}}),restorePage=await restoreContext.newPage();
    restorePage.on('pageerror',e=>errors.push('restore: '+e.message));await restorePage.goto(url+'#records');
    await Promise.all([restorePage.waitForEvent('load'),restorePage.locator('#import-state').setInputFiles(backup)]);await sleepFrame(restorePage);
    const restored=await restorePage.evaluate(k=>JSON.parse(localStorage.getItem(k)),stateKey);assert.deepEqual(restored,data);
    assert((await restorePage.locator('#res-progress').textContent()).includes('新增资源已学 1 / '+manifest.units));
    await restoreContext.close();
  });
  await check('audio local resources load metadata',async()=>{
    const results=[];
    for(const c of catalog.filter(c=>c.section==='listening')){
      await hash(c.anchor);const player=page.locator('#'+c.anchor+' audio').first();assert.equal(await player.count(),1,c.anchor+' audio exists');
      const result=await player.evaluate(a=>new Promise(resolve=>{let done=false;const finish=x=>{if(!done){done=true;resolve(x)}};a.addEventListener('loadedmetadata',()=>finish({duration:a.duration,src:a.currentSrc}),{once:true});a.addEventListener('error',()=>finish({error:a.error?.code,src:a.currentSrc}),{once:true});setTimeout(()=>finish({error:'metadata timeout',src:a.currentSrc}),10000);a.load();}));
      assert(!result.error,c.anchor+' '+JSON.stringify(result));assert(result.duration>0);results.push(result);
    }
    return results;
  });
  await check('original lookup is usable and saves lookup record',async()=>{
    await hash('resource-update');await page.locator('#lookup-open').click();assert(await page.locator('#word-lookup').isVisible());
    await page.locator('#lookup-input').fill('curriculum');await page.locator('#lookup-form').evaluate(f=>f.requestSubmit());
    await page.waitForFunction(()=>document.querySelector('#lookup-result')?.textContent.includes('课程'));
    assert((await page.locator('#lookup-result').innerText()).toLowerCase().includes('curriculum'));
    await page.locator('#lookup-close').click();await hash('records');
    assert((await page.locator('#lookup-history-list').innerText()).toLowerCase().includes('curriculum'));
    const state=await page.evaluate(k=>JSON.parse(localStorage.getItem(k)),stateKey);assert(state.fields['lookup-history-v1']);
  });
  await check('mobile navigation and no horizontal overflow',async()=>{
    await page.setViewportSize({width:390,height:844});
    for(const anchor of ['resource-update',...['background','reading','listening','writing1','writing2','speaking'].map(s=>catalog.find(c=>c.section===s)?.anchor).filter(Boolean)]){
      await hash(anchor);await sleepFrame(page);
      const width=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));assert(width.scroll<=width.viewport+1,anchor+' '+JSON.stringify(width));
    }
    await hash('resource-update');await screen('mobile-catalog');
    await page.locator('#mobile-menu').click();assert(await page.locator('.sidebar [data-go="resource-update"]').isVisible());
    await page.locator('.sidebar [data-go="resource-update"]').click();assert(!(await page.locator('body').getAttribute('class')||'').includes('nav-open'));
    await hash(selected.anchor);await screen('mobile-speaking');
  });
  await check('original navigation still works',async()=>{
    await page.setViewportSize({width:1365,height:950});
    for(const id of ['guide','background','vocabulary','reading','listening','writing1','writing2','speaking','plan','records','library','materials']){await hash(id);assert(await page.locator('#'+id).isVisible(),id);}
    await hash('records');await screen('desktop-records');
  });
  await check('no browser script errors',async()=>assert.deepEqual(errors,[]));
  const result={date:'2026-09-16',isolated_browser_context:true,uses_user_profile:false,units:manifest.units,checks,errors,failedRequests,screenshots,passed:checks.filter(x=>x.pass).length,failed:checks.filter(x=>!x.pass).length};
  fs.writeFileSync(path.join(qa,'results.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({passed:result.passed,failed:result.failed,failures:checks.filter(x=>!x.pass),errors,report:path.join(qa,'results.json')}));
  await context.close();await browser.close();if(result.failed)process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
