const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url'),assert=require('assert');
(async()=>{
  const root='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册',qa=path.join(__dirname,'resource-expansion-qa');
  const main=path.join(root,'开始学习.html'),manifest=JSON.parse(fs.readFileSync(path.join(root,'resource-expansion-manifest.json'),'utf8'));
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true}),context=await browser.newContext({viewport:{width:1365,height:950},acceptDownloads:true}),page=await context.newPage();
  const errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
  await page.goto(pathToFileURL(main).href+'#resource-update');
  assert.equal(await page.locator('#resource-update h1').textContent(),'本季话题与教学资源');
  assert.equal(await page.locator('.res-card').count(),32);assert.equal(await page.locator('.res-card').first().getAttribute('data-res-current'),'true');
  checks.push({name:'final title and current-first catalog',pass:true});
  const palette=await page.locator('.sidebar [data-go="resource-update"]').evaluate(el=>{
    const c=getComputedStyle(el),rgb=x=>x.match(/[\d.]+/g).slice(0,3).map(Number);
    const luminance=x=>rgb(x).map(v=>{v/=255;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4)}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
    const a=luminance(c.color),b=luminance(c.backgroundColor);return {color:c.color,background:c.backgroundColor,border:c.borderColor,contrast:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
  });
  assert(palette.contrast>=4.5,JSON.stringify(palette));checks.push({name:'selected navigation readable red text',pass:true,detail:palette});
  await page.screenshot({path:path.join(qa,'desktop-catalog-final.png')});
  const figureScreens=[];
  for(const c of manifest.catalog.filter(c=>c.section==='writing1')){
    await page.evaluate(h=>location.hash=h,c.anchor);await page.waitForFunction(h=>document.getElementById(h)?.open,c.anchor);
    const figures=page.locator('#'+c.anchor+' .res-figure');
    for(let i=0;i<await figures.count();i++){const out=path.join(qa,'figure-'+c.id+'-'+i+'.png');await figures.nth(i).screenshot({path:out});figureScreens.push(out);}
  }
  await page.evaluate(()=>location.hash='resource-update');await page.waitForFunction(()=>!document.getElementById('resource-update').hidden);
  const query=async phrase=>{await page.locator('#lookup-open').click();await page.locator('#lookup-input').fill(phrase);await page.locator('#lookup-form').evaluate(f=>f.requestSubmit());await page.waitForFunction(p=>document.querySelector('#lookup-result').textContent.toLowerCase().includes(p),phrase);const text=await page.locator('#lookup-result').innerText();await page.locator('#lookup-close').click();return text;};
  const original=await query('curriculum');assert(original.includes('课程'));
  const phrase=await query('cover running costs');assert(/运营|运行|日常|成本|费用/.test(phrase));assert(!phrase.includes('正在查询'));
  checks.push({name:'new phrase and existing word resolve locally',pass:true,detail:{phrase_result:phrase,existing_word_retained:original.includes('课程')}});
  await page.evaluate(()=>location.hash='records');await page.waitForFunction(()=>!document.getElementById('records').hidden);
  let text=await page.locator('#lookup-history-list').innerText();assert(text.includes('cover running costs'));assert(text.toLowerCase().includes('curriculum'));
  await page.reload();await page.waitForFunction(()=>document.getElementById('lookup-history-list').textContent.includes('cover running costs'));
  text=await page.locator('#lookup-history-list').innerText();assert(text.toLowerCase().includes('curriculum'));
  const pending=page.waitForEvent('download');await page.locator('[data-export="json"]').click();const d=await pending,backup=path.join(qa,'final-lookup-backup.json');await d.saveAs(backup);
  const data=JSON.parse(fs.readFileSync(backup,'utf8'));assert(data.fields['lookup-history-v1'].includes('cover running costs'));assert(data.fields['lookup-history-v1'].toLowerCase().includes('curriculum'));
  checks.push({name:'lookup history refresh and original JSON export',pass:true});
  const lookupPending=page.waitForEvent('download');await page.locator('#lookup-export').click();const ld=await lookupPending,lookupBackup=path.join(qa,'final-lookup-specific-export.json');await ld.saveAs(lookupBackup);
  const ltext=fs.readFileSync(lookupBackup,'utf8');assert(ltext.includes('cover running costs'));assert(ltext.toLowerCase().includes('curriculum'));
  checks.push({name:'lookup-specific export includes new and old terms',pass:true});
  await page.setViewportSize({width:390,height:844});await page.evaluate(()=>location.hash='resource-update');await page.waitForFunction(()=>!document.getElementById('resource-update').hidden);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:path.join(qa,'mobile-catalog-final.png')});
  checks.push({name:'final collapsed-source catalog at mobile width',pass:true});
  assert.deepEqual(errors,[]);
  const result={main_sha256:crypto.createHash('sha256').update(fs.readFileSync(main)).digest('hex'),manifest_main_sha256:manifest.main_sha256,isolated_browser_context:true,checks,browser_errors:errors,screenshots:[path.join(qa,'desktop-catalog-final.png'),path.join(qa,'mobile-catalog-final.png'),...figureScreens]};
  fs.writeFileSync(path.join(qa,'final-delta.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));await context.close();await browser.close();
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
