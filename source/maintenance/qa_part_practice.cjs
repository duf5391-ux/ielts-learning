/* Isolated acceptance checks for the added per-part practice. */
const {chromium} = require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const {pathToFileURL, fileURLToPath} = require('url');
const root = __dirname;
const out = path.join(root, 'part-practice-qa');
const book = 'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const main = path.join(book, '开始学习.html');
const sections = ['reading','listening','writing1','writing2','speaking','vocabulary','background'];
const checks = [];
const facts = {};
fs.mkdirSync(out, {recursive:true});
const norm = s => String(s).replace(/\s+/g,' ').trim();
const wav = () => {
  const samples=8000, b=Buffer.alloc(44+samples*2);
  b.write('RIFF'); b.writeUInt32LE(b.length-8,4); b.write('WAVEfmt ',8); b.writeUInt32LE(16,16);
  b.writeUInt16LE(1,20); b.writeUInt16LE(1,22); b.writeUInt32LE(8000,24); b.writeUInt32LE(16000,28);
  b.writeUInt16LE(2,32); b.writeUInt16LE(16,34); b.write('data',36); b.writeUInt32LE(samples*2,40);
  return b;
};
async function check(name, fn, page) {
  if(process.argv.includes('--persistence-only')&&!name.includes('responses survive')&&!name.includes('page errors'))return;
  try { await fn(); checks.push({name, pass:true}); }
  catch(error) {
    checks.push({name,pass:false,error:error.stack});
    if(page) await page.screenshot({path:path.join(out,name.replace(/[^a-z0-9]+/gi,'-')+'-failure.png'),fullPage:false}).catch(()=>{});
  }
}
async function route(page, id) {
  await page.evaluate(id => { location.hash=id; },id);
  await page.waitForFunction(id => {const e=document.getElementById(id);return e && !e.closest('main > .panel').hidden;},id);
}
async function openUnit(page,u) {
  await route(page,u.id);
  assert(await page.locator('#'+u.id).isVisible());
  assert(await page.locator('#'+u.id).evaluate(e=>e.open));
}
async function mainQA() {
  const report=JSON.parse(fs.readFileSync(path.join(out,'integration.json'),'utf8'));
  const bank=JSON.parse(fs.readFileSync(path.join(root,'part-practice-bank.json'),'utf8'));
  const units=bank.units;
  const html=fs.readFileSync(main,'utf8');
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const page=await context.newPage();
  page.setDefaultTimeout(8000);
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('dialog',d=>d.accept());
  try {
    await page.goto(pathToFileURL(main).href,{waitUntil:'domcontentloaded'});
    await page.waitForSelector('.pp-practice',{state:'attached'});
    await check('all seven chapter links route to their new practice',async()=>{
      for(const section of sections) {
        await route(page,'library');
        const link=page.locator('#library a[href="#pp-'+section+'"]').first();
        assert(await link.isVisible(),section+' directory link visible');
        await link.click();
        await page.waitForFunction(section=>!document.getElementById(section).hidden,section);
        assert(await page.locator('#pp-'+section).isVisible(),section+' target visible');
        assert.equal(await page.locator('#pp-'+section+' > .pp-unit').count(),units.filter(u=>u.section===section).length);
      }
    },page);
    await check('original static ids fields and content preserved',async()=>{
      const inventory=await page.evaluate(html=>{
        const stripped=html.replace(/<!--PART-PRACTICE-V1:[^>]+-->[\s\S]*?<!--\/PART-PRACTICE-V1-->/g,'');
        const before=new DOMParser().parseFromString(stripped,'text/html'),after=new DOMParser().parseFromString(html,'text/html');
        const ids=d=>Array.from(d.querySelectorAll('[id]'),e=>e.id);
        const fields=d=>Array.from(d.querySelectorAll('[data-save]'),e=>e.dataset.save);
        return {oldIds:ids(before),newIds:ids(after),oldFields:fields(before),newFields:fields(after)};
      },html);
      assert.deepEqual(inventory.newIds.filter(id=>!id.startsWith('pp-')&&!id.startsWith('pr-')),inventory.oldIds);
      assert.deepEqual(inventory.newFields.filter(id=>!id.startsWith('pr-')),inventory.oldFields);
      assert.equal(inventory.newIds.length,new Set(inventory.newIds).size);
      assert.equal(inventory.newFields.length,new Set(inventory.newFields).size);
      assert.equal(inventory.oldFields.length,report.original_fields_preserved);
      assert.equal(inventory.newFields.length-inventory.oldFields.length,report.new_fields);
      assert(report.original_content_preserved_exactly&&report.idempotent);
      facts.inventory={oldFields:inventory.oldFields.length,newFields:report.new_fields,units:units.length};
    },page);
    await check('all exercises show exact contexts and prompts with answers initially hidden',async()=>{
      for(const u of units) {
        await openUnit(page,u);
        const card=page.locator('#'+u.id);
        const keys=card.locator('.pp-key');
        for(const key of await keys.all()) {
          assert.equal(await key.evaluate(e=>e.open),false,u.id+' key initially closed');
          const nonSummary=key.locator(':scope > p').first();
          if(await nonSummary.count())assert.equal(await nonSummary.isVisible(),false,u.id+' answer not visible');
        }
        const text=norm(await card.innerText());
        for(const p of u.context||[])assert(text.includes(norm(p)),u.id+' context retained');
        for(const q of u.questions)assert(text.includes(norm(q.prompt)),u.id+' prompt retained');
        assert(text.includes(norm(u.source.title)),u.id+' source shown');
        for(const line of [...u.reasoning||[],...u.pitfalls||[]])if(line&&norm(line)!==norm(u.reference))assert(!text.includes(norm(line)),u.id+' reasoning not shown');
        if(u.challengeMechanism)assert(!text.includes(norm(u.challengeMechanism)),u.id+' mechanism not shown');
        assert(!/高难|难度|挑战|陷阱|难点解析|解题技巧/.test(await card.locator(':scope > summary').innerText()));
        assert.equal(await card.locator('.pp-body .intensive,.pp-body .pitfalls,.pp-body .reasoning').count(),0);
        if(u.section!=='speaking') {
          const key=card.locator(':scope > .pp-body > .pp-key');
          await key.locator(':scope > summary').click();
          assert(norm(await key.innerText()).includes(norm(u.reference)),u.id+' answer toggle displays full key');
          await key.locator(':scope > summary').click();
        }
      }
    },page);
    await check('original and added responses survive reload and main backup export',async()=>{
      await route(page,'reading');
      const old=page.locator('#reading textarea[data-save]:not([data-save^="pr-"])').first();
      const oldKey=await old.getAttribute('data-save');
      await old.evaluate(e=>{let p=e.parentElement;while(p){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement;}});
      await old.fill('QA original field survives 20260919');
      const u=units.find(u=>u.section==='reading');
      await openUnit(page,u);
      const added=page.locator('#'+u.id+' textarea[data-save]').first();
      const newKey=await added.getAttribute('data-save');
      await added.fill('QA added field survives 20260919');
      await page.reload({waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('[data-save="'+newKey+'"]').inputValue(),'QA added field survives 20260919');
      assert.equal(await page.locator('[data-save="'+oldKey+'"]').inputValue(),'QA original field survives 20260919');
      await route(page,'records');
      const selector=page.locator('[data-export="json"]');
      let button=null;
      for(const b of await selector.all())if(await b.isVisible()){button=b;break;}
      assert(button,'visible main backup control');
      const [download]=await Promise.all([page.waitForEvent('download'),button.click()]);
      const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
      assert.equal(exported.fields[oldKey],'QA original field survives 20260919');
      assert.equal(exported.fields[newKey],'QA added field survives 20260919');
      facts.savedFields=[oldKey,newKey];
      fs.writeFileSync(path.join(out,'isolated-progress-export.json'),JSON.stringify(exported,null,2));
    },page);
    await check('all new images decode and all four listening audio parts load metadata',async()=>{
      const images=[],audio=[];
      for(const u of units) {
        await openUnit(page,u);
        if(u.image) {
          const result=await page.locator('#'+u.id+' .pp-figure img').evaluate(async e=>{e.loading='eager';await e.decode();return {src:e.getAttribute('src'),width:e.naturalWidth,height:e.naturalHeight};});
          assert(result.width>0&&result.height>0);images.push(result);
        }
        if(u.audio) {
          const result=await page.locator('#'+u.id+' .pp-audio').evaluate(e=>new Promise((resolve,reject)=>{
            const timer=setTimeout(()=>reject(Error('audio metadata timeout: '+e.src)),15000);
            const done=()=>{clearTimeout(timer);resolve({src:e.getAttribute('src'),duration:e.duration,readyState:e.readyState,error:e.error?.message||null});};
            e.addEventListener('loadedmetadata',done,{once:true});e.addEventListener('error',()=>{clearTimeout(timer);reject(Error(e.error?.message||'audio load error'));},{once:true});
            if(e.readyState>=1)done();else e.load();
          }));
          assert(Number.isFinite(result.duration)&&result.duration>0);assert.equal(result.error,null);
          if(u.audio.start!=null)assert(u.audio.start<result.duration);
          if(u.audio.end!=null)assert(u.audio.end<=result.duration+0.5);
          audio.push({id:u.id,...result});
        }
        for(const a of await page.locator('#'+u.id+' .pp-source a').all()){
          const href=await a.getAttribute('href');
          if(!/^https?:/.test(href)){const url=new URL(href,pathToFileURL(main));url.hash='';assert(fs.existsSync(fileURLToPath(url)),href);}
        }
      }
      assert(audio.length>=4,'at least one audio source for each listening part');
      facts.media={images,audio};
    },page);
    await check('speaking controls load fixture recording without real microphone access',async()=>{
      const speaking=units.filter(u=>u.section==='speaking');
      assert(speaking.length>=3);
      for(const u of speaking){await openUnit(page,u);assert.equal(await page.locator('#'+u.id+' [data-record]').count(),1);assert.equal(await page.locator('#'+u.id+' [data-stop]').count(),1);assert.equal(await page.locator('#'+u.id+' [data-upload]').count(),1);}
      const u=speaking[0];await openUnit(page,u);
      await page.locator('#'+u.id+' [data-upload]').setInputFiles({name:'qa-silent-fixture.wav',mimeType:'audio/wav',buffer:wav()});
      const player=page.locator('#'+u.id+' [data-preview]');
      assert(await player.isVisible());
      await page.waitForFunction(id=>document.querySelector('#'+id+' [data-preview]').readyState>=1,u.id);
      assert.equal(await page.locator('#'+u.id+' [data-download]').getAttribute('download'),'qa-silent-fixture.wav');
      assert.equal(await page.locator('#'+u.id+' [data-save$="-record-note"]').inputValue(),'qa-silent-fixture.wav');
    },page);
    await check('desktop and 390px mobile new practice layout without overflow',async()=>{
      const widths=[];
      for(const width of [1440,390]){
        await page.setViewportSize({width,height:width===390?844:1000});
        for(const section of sections){
          const u=units.find(u=>u.section===section);await openUnit(page,u);
          const measure=await page.evaluate(id=>{const el=document.getElementById(id);return {viewport:innerWidth,document:document.documentElement.scrollWidth,practice:el.scrollWidth,box:el.clientWidth};},'pp-'+section);
          assert(measure.document<=measure.viewport+1,section+' document overflow '+JSON.stringify(measure));
          assert(measure.practice<=measure.box+1,section+' practice overflow '+JSON.stringify(measure));
          widths.push({width,section,...measure});
          await page.locator('#'+u.id).scrollIntoViewIfNeeded();
          await page.screenshot({path:path.join(out,(width===390?'mobile-':'desktop-')+section+'.png'),fullPage:false,animations:'disabled'});
        }
      }
      facts.layouts=widths;
    },page);
    await check('no uncaught page errors',async()=>assert.deepEqual(errors,[]),page);
  } finally {await context.close();await browser.close();}
  const result={scope:'Isolated temporary Edge context; no real browser profile or microphone used',generatedAt:new Date().toISOString(),checks,facts};
  fs.writeFileSync(path.join(out,process.argv.includes('--persistence-only')?'persistence-results.json':'browser-results.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({checks,facts},null,2));
  if(checks.some(c=>!c.pass))process.exitCode=1;
}
mainQA().catch(error=>{console.error(error);process.exitCode=1;});
