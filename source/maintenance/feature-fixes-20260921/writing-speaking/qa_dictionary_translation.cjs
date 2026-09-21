const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{pathToFileURL}=require('url');
const BOOK='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const candidate=path.resolve(process.argv[2]||'feature-fixes-20260921/candidate.html');
const output=path.join(__dirname,'dictionary-translation');fs.mkdirSync(output,{recursive:true});
const bytes=fs.readFileSync(candidate),sourceSha256=crypto.createHash('sha256').update(bytes).digest('hex');
const fixture=path.join(output,'isolated-fixture.html');
fs.writeFileSync(fixture,bytes.toString('utf8').replace('<head>','<head><base href="'+pathToFileURL(BOOK+path.sep).href+'">'));
const checks=[],errors=[],network=[],lookups=[],liveTranslations=[];
let browser;
async function check(name,fn){try{const evidence=await fn();checks.push({name,pass:true,evidence});}catch(error){checks.push({name,pass:false,error:error.message});}}
async function main(){
  browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const offline=await browser.newContext({offline:true,viewport:{width:1365,height:900}}),p=await offline.newPage();
  p.setDefaultTimeout(18000);p.on('pageerror',e=>errors.push({phase:'offline',message:e.message}));
  p.on('request',r=>{if(/^https?:/.test(r.url()))network.push({phase:'offline',type:'request',url:r.url()})});
  await p.goto(pathToFileURL(fixture).href+'#vocabulary',{waitUntil:'domcontentloaded'});
  await check('file protocol dictionary engine loads while browser is offline',async()=>{
    assert.equal(await p.evaluate(()=>navigator.onLine),false);
    return p.evaluate(async()=>{await IELTSLocalDictionary.ready();return {online:navigator.onLine,info:IELTSLocalDictionary.info,protocol:location.protocol}});
  });
  await check('20 consecutive offline UI queries include repeats without stale results',async()=>{
    await p.locator('#lookup-open').click();
    for(const term of ['environment','sustainable','important','evidence','government','transport','knowledge','opportunity','analysis','children','went','running','studies','better','mice','geese','teeth','environment','children','opportunity']){
      await p.locator('#lookup-input').fill(term);await p.locator('#lookup-input').press('Enter');
      await p.waitForFunction(term=>document.querySelector('#lookup-result h3')?.textContent===term&&document.querySelectorAll('#lookup-result .dictionary-entry').length>0,term);
      const row=await p.evaluate(term=>({term,heading:document.querySelector('#lookup-result h3').textContent,entries:[...document.querySelectorAll('#lookup-result .dictionary-entry h4')].map(x=>x.textContent),meaning:document.querySelector('#lookup-result .dictionary-meaning')?.textContent||'',history:IELTSLookup.getHistory().find(x=>x.term===term)}),term);
      assert.equal(row.heading,term);assert(row.meaning);assert(row.history?.meaning);lookups.push(row);
    }
    return {queries:lookups.length,uniqueTerms:new Set(lookups.map(x=>x.term)).size,repeatCount:lookups.at(-1).history.count};
  });
  await check('offline irregular and regular inflections resolve to their base forms',async()=>{
    const expected={children:'child',went:'go',running:'run',studies:'study',mice:'mouse',geese:'goose',teeth:'tooth'};
    const result=[];
    for(const [term,base] of Object.entries(expected)){
      const found=await p.evaluate(async term=>{const x=await IELTSLocalDictionary.lookup(term);return {term,entries:x.entries.map(e=>e.word),bases:x.bases}},term);
      assert(found.bases.includes(base)||found.entries.includes(base),JSON.stringify(found));result.push(found);
    }
    return result;
  });
  await check('overlapping dictionary queries leave the most recent word visible',async()=>{
    await p.evaluate(async()=>Promise.all([IELTSLookup.open('photosynthesis'),IELTSLookup.open('resilient'),IELTSLookup.open('opportunity')]));
    assert.equal(await p.locator('#lookup-result h3').textContent(),'opportunity');
    assert((await p.locator('#lookup-result .dictionary-entry h4').allTextContents()).includes('opportunity'));
    return {heading:await p.locator('#lookup-result h3').textContent()};
  });
  await check('offline missing word reports no match and next valid lookup recovers',async()=>{
    await p.evaluate(()=>IELTSLookup.open('zzqvnotarealword'));
    assert((await p.locator('#lookup-result').textContent()).includes('未收录'));
    await p.evaluate(()=>IELTSLookup.open('sustainable'));
    assert(await p.locator('#lookup-result .dictionary-entry').count()>0);
    return {missingWordMessage:true,nextWord:'sustainable'};
  });
  await check('bundled exact sentence translation works without a network',async()=>{
    const result=await p.evaluate(async()=>{const pair=JSON.parse(document.querySelector('#sentence-local-pairs').textContent)[0];IELTSSentences.open(pair.en);await IELTSSentences.translate();return {source:pair.en,expected:pair.zh,translation:document.querySelector('#sentence-result').value,status:document.querySelector('#sentence-status').textContent}});
    assert.equal(result.translation,result.expected);assert(result.status.includes('无需联网'));return result;
  });
  await check('uncached sentence offline failure is explicit and preserves input',async()=>{
    const result=await p.evaluate(async()=>{const text='The small library closes at six every evening.';IELTSSentences.open(text);await IELTSSentences.translate();return {source:document.querySelector('#sentence-source').value,translation:document.querySelector('#sentence-result').value,status:document.querySelector('#sentence-status').textContent,buttonDisabled:document.querySelector('#sentence-translate').disabled}});
    assert.equal(result.source,'The small library closes at six every evening.');assert.equal(result.translation,'');assert(result.status.includes('暂时无法连接'));assert.equal(result.buttonDisabled,false);return result;
  });
  await offline.close();
  const online=await browser.newContext({viewport:{width:390,height:844}}),q=await online.newPage();
  q.setDefaultTimeout(24000);q.on('pageerror',e=>errors.push({phase:'online',message:e.message}));
  q.on('requestfailed',r=>{if(r.url().includes('api.mymemory.translated.net'))network.push({phase:'online',type:'requestfailed',url:r.url(),failure:r.failure()})});
  q.on('response',async r=>{if(r.url().includes('api.mymemory.translated.net')){const row={phase:'online',type:'response',url:r.url(),status:r.status()};try{row.body=await r.json()}catch{}network.push(row)}});
  await q.goto(pathToFileURL(fixture).href+'#sentence-learning',{waitUntil:'domcontentloaded'});
  for(const text of ['The small library closes at six every evening.','这座小图书馆每天晚上六点关门。']){
    await check('live MyMemory translation '+(/[\u3400-\u9fff]/.test(text)?'Chinese to English':'English to Chinese'),async()=>{
      await q.evaluate(text=>IELTSSentences.open(text),text);
      await q.locator('#sentence-translate').click();await q.waitForFunction(()=>!document.querySelector('#sentence-translate').disabled,null,{timeout:23000});
      const row=await q.evaluate(()=>({source:document.querySelector('#sentence-source').value,direction:document.querySelector('#sentence-direction').value,translation:document.querySelector('#sentence-result').value,status:document.querySelector('#sentence-status').textContent,online:navigator.onLine}));
      liveTranslations.push(row);await q.screenshot({path:path.join(output,row.direction.startsWith('en')?'live-en-zh.png':'live-zh-en.png')});
      assert(row.translation,row.status);assert(row.status.includes('译文已就绪'));return row;
    });
  }
  await online.close();await browser.close();
  const result={source:candidate,sourceSha256,fixtureChange:'Only add a file:// base pointing to the existing local assets; browser contexts are isolated.',checkedAt:new Date().toISOString(),checks,errors,lookups,liveTranslations,network};
  fs.writeFileSync(path.join(output,'test-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({sourceSha256,checks,errors,liveTranslations,network},null,2));
  if(checks.some(x=>!x.pass)||errors.length)process.exitCode=1;
}
main().catch(async e=>{console.error(e);if(browser)await browser.close();process.exitCode=1});
