const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const BOOK='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const KEY='ielts-finished-book-v1',checks=[],errors=[];
const explicitCandidate=process.argv[2]?path.resolve(process.argv[2]):null;
const candidatePath=explicitCandidate||path.join(__dirname,'preview.html');
const output=explicitCandidate?path.join(__dirname,'combined'):__dirname;
fs.mkdirSync(output,{recursive:true});
const candidateBytes=fs.readFileSync(candidatePath);
const candidateSha256=require('crypto').createHash('sha256').update(candidateBytes).digest('hex');
const pages={before:fs.readFileSync(path.join(BOOK,'开始学习.html'),'utf8'),after:candidateBytes.toString('utf8')};
const server=http.createServer((req,res)=>{
  const url=decodeURIComponent(req.url.split('?')[0]);
  const version=url.startsWith('/before/')?'before':'after';
  if(url.endsWith('/index.html')){res.setHeader('Content-Type','text/html;charset=utf-8');res.end(pages[version]);return;}
  const file=path.resolve(BOOK,'.'+url.replace(/^\/(before|after)/,''));
  if(!file.startsWith(path.resolve(BOOK)+path.sep)||!fs.existsSync(file)||fs.statSync(file).isDirectory()){res.statusCode=404;res.end();return;}
  const mime={'.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.mp3':'audio/mpeg'};
  res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
const field=(p,key)=>p.locator(`[data-save="${key}"]`);
const button=(p,action)=>p.locator(`#ww-housing [data-ww-action="${action}"]`);
let browser,origin;
async function run(name,fn,{baseline=false,mobile=false}={}){
  for(const version of baseline&&!explicitCandidate?['before','after']:['after']){
    const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1365,height:900},acceptDownloads:true});
    const p=await context.newPage();p.setDefaultTimeout(7000);p.on('pageerror',e=>errors.push({name,version,message:e.message}));
    p.on('dialog',d=>d.accept());
    try{await p.goto(origin+`/${version}/index.html#ww-housing`,{waitUntil:'domcontentloaded'});await fn(p,context,version);checks.push({name,version,pass:true});}
    catch(e){checks.push({name,version,pass:false,error:e.message});}
    finally{await context.close();}
  }
}
async function prepareSpeech(p){
  const info=await p.locator('[data-record]').first().evaluate(el=>({id:el.dataset.record,route:el.closest('[data-learning-unit]').id}));
  const id=info.id;
  await p.evaluate(route=>location.hash=route,info.route);
  await p.locator(`[data-record="${id}"]`).waitFor({state:'visible'});
  await p.locator(`[data-record="${id}"]`).scrollIntoViewIfNeeded();
  return id;
}
async function injectRecorder(p,mode='manual'){
  await p.evaluate(mode=>{
    window.qa={requests:0,tracks:[],recorders:[],mode};
    Object.defineProperty(navigator.mediaDevices,'getUserMedia',{value:()=>{
      qa.requests++;return new Promise((resolve,reject)=>{qa.resolve=()=>{
        const track={stopped:false,stop(){this.stopped=true}};qa.tracks.push(track);resolve({getTracks:()=>[track]});
      };qa.reject=reject;if(mode==='auto'||mode==='construct-fail')qa.resolve();});
    }});
    window.MediaRecorder=class{
      static isTypeSupported(type){return type==='audio/mp4'}
      constructor(stream){if(mode==='construct-fail')throw new Error('constructor failed');this.mimeType='audio/mp4';this.state='inactive';qa.recorders.push(this)}
      start(){this.state='recording'}
      stop(){if(this.state==='inactive')throw new Error('double stop');this.state='inactive';setTimeout(()=>{this.ondataavailable?.({data:new Blob(['synthetic test'],{type:this.mimeType})});this.onstop?.()},10)}
    };
  },mode);
}
async function main(){
  await new Promise(r=>server.listen(0,'127.0.0.1',r));origin=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']});
  await run('freeze save failure leaves editable first draft and no partial lock',async p=>{
    await field(p,'ww-housing-first').fill('A first draft that must not become locked when the revision cannot be saved.');
    await button(p,'timer').click();
    await p.evaluate(key=>{const original=Storage.prototype.setItem;window.qaSet=original;Storage.prototype.setItem=function(k,v){if(k===key&&JSON.parse(v).fields['ww-housing-revision'])throw new DOMException('quota','QuotaExceededError');return original.call(this,k,v)}},KEY);
    await button(p,'freeze').click();
    assert.equal(await field(p,'ww-housing-first').evaluate(e=>e.readOnly),false);
    assert.equal(await field(p,'ww-housing-first-at').inputValue(),'');
    assert.equal(await p.evaluate(key=>JSON.parse(localStorage.getItem(key)).fields['ww-housing-first-at']||'',KEY),'');
    await p.evaluate(()=>Storage.prototype.setItem=window.qaSet);await button(p,'freeze').click();
    assert.equal(await field(p,'ww-housing-first').evaluate(e=>e.readOnly),true);
    assert((await field(p,'ww-housing-revision').inputValue()).includes('must not become locked'));
  },{baseline:true});
  await run('failed timer start does not leave a hidden running clock after recovery',async p=>{
    await p.evaluate(()=>{window.qaSet=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new Error('blocked')}});
    await button(p,'timer').click();
    assert.equal(await field(p,'ww-housing-timer').inputValue(),'');
    await p.evaluate(()=>Storage.prototype.setItem=window.qaSet);
    await field(p,'ww-housing-first').fill('Storage can now save this draft.');
    await p.reload({waitUntil:'domcontentloaded'});
    assert.equal(await button(p,'timer').textContent(),'开始 40 分钟');
  },{baseline:true});
  await run('failed revision snapshot is not silently saved by an unrelated input',async p=>{
    await field(p,'ww-housing-first').fill('First draft.');await button(p,'freeze').click();
    await field(p,'ww-housing-revision').fill('An independent revised draft.');
    await p.evaluate(()=>{window.qaSet=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new Error('blocked')}});
    await button(p,'version').click();assert.equal(await field(p,'ww-housing-versions').inputValue(),'');
    await p.evaluate(()=>Storage.prototype.setItem=window.qaSet);
    await field(p,'ww-housing-plan-1').fill('Recovered storage.');
    assert.equal(await p.evaluate(key=>JSON.parse(localStorage.getItem(key)).fields['ww-housing-versions']||'',KEY),'');
    await button(p,'version').click();assert.equal(JSON.parse(await field(p,'ww-housing-versions').inputValue()).length,1);
  },{baseline:true});
  await run('remote revision is protected before first-draft freeze',async(p,context)=>{
    await field(p,'ww-housing-first').fill('Shared first draft.');
    const other=await context.newPage();await other.goto(p.url(),{waitUntil:'domcontentloaded'});
    await field(other,'ww-housing-revision').fill('Revision from the other tab.');
    await button(p,'freeze').click();
    assert.equal(await field(p,'ww-housing-first').evaluate(e=>e.readOnly),false);
    assert.equal(await p.evaluate(key=>JSON.parse(localStorage.getItem(key)).fields['ww-housing-first-at']||'',KEY),'');
    assert.equal(await p.evaluate(key=>JSON.parse(localStorage.getItem(key)).fields['ww-housing-revision'],KEY),'Revision from the other tab.');
  },{baseline:true});
  await run('writing draft revision history export and refresh on phone width',async p=>{
    const draft='Tall buildings can provide more homes close to public transport.';
    await field(p,'ww-housing-first').fill(draft);await button(p,'timer').click();await button(p,'freeze').click();
    assert.equal(await field(p,'ww-housing-first').evaluate(e=>e.readOnly),true);
    assert.equal(await field(p,'ww-housing-revision').inputValue(),draft);
    assert.equal(JSON.parse(await field(p,'ww-housing-timer').inputValue()).status,'paused');
    await field(p,'ww-housing-revision').fill(draft+' This can reduce journey times.');await button(p,'version').click();
    const download=p.waitForEvent('download');await button(p,'export').click();const file=await download;
    await file.saveAs(path.join(output,'isolated-writing-export.txt'));assert(fs.readFileSync(path.join(output,'isolated-writing-export.txt'),'utf8').includes(draft));
    await p.reload({waitUntil:'domcontentloaded'});assert.equal(JSON.parse(await field(p,'ww-housing-versions').inputValue()).length,1);
    assert.equal(await field(p,'ww-housing-first').inputValue(),draft);
    assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await field(p,'ww-housing-revision').scrollIntoViewIfNeeded();await p.screenshot({path:path.join(output,'writing-mobile.png')});
  },{mobile:true});
  await run('permission request blocks duplicate start and activates finish guard',async p=>{
    const id=await prepareSpeech(p);await injectRecorder(p);
    await p.evaluate(id=>{const b=document.querySelector(`[data-record="${id}"]`);b.click();b.click()},id);
    assert.equal(await p.evaluate(()=>qa.requests),1);
    assert.equal(await p.locator(`[data-stop="${id}"]`).isDisabled(),false);
    await p.locator(`[data-stop="${id}"]`).click();await p.evaluate(()=>qa.resolve());
    assert.equal(await p.evaluate(()=>qa.tracks[0].stopped),true);assert.equal(await p.evaluate(()=>qa.recorders.length),0);
  },{baseline:true});
  await run('recorder construction failure releases the microphone',async p=>{
    const id=await prepareSpeech(p);await injectRecorder(p,'construct-fail');await p.locator(`[data-record="${id}"]`).click();
    assert.equal(await p.evaluate(()=>qa.tracks[0].stopped),true);assert.equal(await p.locator(`[data-record="${id}"]`).isDisabled(),false);
    assert.equal(await p.locator(`[data-stop="${id}"]`).isDisabled(),true);
  },{baseline:true});
  await run('permission denial recovers controls and reports permission guidance',async p=>{
    const id=await prepareSpeech(p);await injectRecorder(p);await p.locator(`[data-record="${id}"]`).click();
    await p.evaluate(()=>qa.reject(new DOMException('denied','NotAllowedError')));
    assert.equal(await p.locator(`[data-record="${id}"]`).isDisabled(),false);
    assert((await p.locator(`[data-rec-status="${id}"]`).textContent()).includes('权限'));
  });
  await run('MPEG4 recording uses matching extension and preserves learner notes',async p=>{
    const id=await prepareSpeech(p);await injectRecorder(p,'auto');
    const note=field(p,`${id}-record-note`);await note.fill('My own observations and transcript.');
    await p.locator(`[data-record="${id}"]`).click();
    await p.evaluate(id=>{const b=document.querySelector(`[data-stop="${id}"]`);b.click();b.click()},id);
    await p.locator(`[data-download="${id}"]`).waitFor({state:'visible'});
    assert((await p.locator(`[data-download="${id}"]`).getAttribute('download')).endsWith('.m4a'));
    assert.equal(await note.inputValue(),'My own observations and transcript.');
    assert.equal(await p.evaluate(()=>qa.tracks[0].stopped),true);
  },{baseline:true});
  await run('native MediaRecorder with browser synthetic microphone creates playable downloadable audio',async p=>{
    const id=await prepareSpeech(p);await p.locator(`[data-record="${id}"]`).click();
    await p.waitForFunction(id=>document.querySelector(`[data-rec-status="${id}"]`).textContent.startsWith('正在录音'),id);
    await p.waitForTimeout(450);await p.locator(`[data-stop="${id}"]`).click();
    const link=p.locator(`[data-download="${id}"]`);await link.waitFor({state:'visible'});
    const result=await p.locator(`[data-preview="${id}"]`).evaluate(async el=>{
      await new Promise((resolve,reject)=>{if(el.readyState>=1)return resolve();el.onloadedmetadata=resolve;el.onerror=()=>reject(new Error('audio decode error'))});
      return {size:(await(await fetch(el.src)).blob()).size,mime:(await(await fetch(el.src)).blob()).type,readyState:el.readyState};
    });assert(result.size>100);assert(result.readyState>=1);
    const download=p.waitForEvent('download');await link.click();await(await download).saveAs(path.join(output,'browser-synthetic-recording.webm'));
    await p.reload({waitUntil:'domcontentloaded'});assert.equal(await p.locator(`[data-preview="${id}"]`).isVisible(),false);
  },{mobile:true});
  await run('audio upload preserves handwritten notes and rejects non-audio',async p=>{
    const id=await prepareSpeech(p);await field(p,`${id}-record-note`).fill('Keep my notes.');
    await p.locator(`[data-upload="${id}"]`).setInputFiles({name:'sample.wav',mimeType:'audio/wav',buffer:Buffer.from('RIFFsynthetic')});
    assert.equal(await field(p,`${id}-record-note`).inputValue(),'Keep my notes.');
    const previous=await p.locator(`[data-download="${id}"]`).getAttribute('href');
    await p.locator(`[data-upload="${id}"]`).setInputFiles({name:'not-audio.txt',mimeType:'text/plain',buffer:Buffer.from('text')});
    assert.equal(await p.locator(`[data-download="${id}"]`).getAttribute('href'),previous);
  },{baseline:true});
  await browser.close();server.close();
  const result={candidatePath,candidateSha256,checks,errors,boundary:'Fresh isolated browser contexts. Native MediaRecorder check uses Chromium synthetic microphone. No physical microphone/device recording claimed.'};
  fs.writeFileSync(path.join(output,'test-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
  if(checks.some(c=>c.version==='after'&&!c.pass)||errors.some(e=>e.version==='after'))process.exitCode=1;
}
main().catch(async e=>{console.error(e);if(browser)await browser.close();server.close();process.exitCode=1});
