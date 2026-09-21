const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const main='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
const out=path.join(__dirname,'architecture-audit-qa');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const results={scope:'Disposable browser contexts only; no user browser profile or records accessed',cases:[]};
 try {
  for(const [name,raw] of [['normal',null],['malformed_json','{broken'],['array_fields',JSON.stringify({version:1,fields:[],snapshots:{}})],['invalid_snapshot',JSON.stringify({version:1,fields:{},snapshots:{guide:{at:'test',fields:{}}}})]]) {
   const context=await browser.newContext(),page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   if(raw!==null)await page.addInitScript(raw=>{localStorage.setItem('ielts-finished-book-v1',raw)},raw);
   const start=Date.now();await page.goto(pathToFileURL(main).href+'#reading');
   const before=await page.evaluate(()=>({raw:localStorage.getItem('ielts-finished-book-v1'),status:document.querySelector('#save-status').textContent}));
   await page.locator('[data-save="reading-q1"]').evaluate(el=>{el.value='AUDIT_SENTINEL';el.dispatchEvent(new Event('input',{bubbles:true}))});
   const after=await page.evaluate(()=>({raw:localStorage.getItem('ielts-finished-book-v1'),status:document.querySelector('#save-status').textContent}));
   results.cases.push({name,elapsedMs:Date.now()-start,errors,before,after});
   await context.close();
  }
 } finally {await browser.close()}
 fs.writeFileSync(path.join(out,'runtime-probes.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results,null,2));
})();
