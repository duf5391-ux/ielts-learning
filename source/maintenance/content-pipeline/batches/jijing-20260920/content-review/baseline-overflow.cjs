const fs=require('fs'),path=require('path'),http=require('http'),crypto=require('crypto');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../../..'),stage=path.resolve(__dirname,'../stage');
const book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
function resolve(base,rel){const p=path.resolve(base,rel);return p.startsWith(path.resolve(base)+path.sep)&&fs.existsSync(p)&&fs.statSync(p).isFile()?p:null;}
const mime={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.mp3':'audio/mpeg','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1);const file=resolve(stage,rel)||resolve(book,rel);if(!file){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).pipe(res);});
(async()=>{
 let browser;
 try{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
  const page=await context.newPage(),results=[];
  for(const hash of ['study','pr-reading-davies-statements']){
   await page.goto(base+'/baseline.html#'+hash);await page.waitForTimeout(650);
   const layout=await page.evaluate(()=>{
    const rect=n=>{if(!n)return null;const r=n.getBoundingClientRect(),s=getComputedStyle(n);return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,display:s.display,visibility:s.visibility,transform:s.transform,zIndex:s.zIndex}};
    return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,bodyClass:document.body.className,topbar:rect(document.querySelector('.workspace-topbar')),actions:rect(document.querySelector('.topbar-actions')),saveIndicator:rect(document.querySelector('.save-indicator')),sidebar:rect(document.querySelector('.sidebar')),wide:[...document.querySelectorAll('body *')].filter(n=>{const r=n.getBoundingClientRect();return r.width&&r.right>innerWidth+2&&!n.closest('[hidden]')}).slice(0,20).map(n=>({tag:n.tagName,id:n.id,cl:n.className,...rect(n)})),buttons:[...document.querySelectorAll('button')].filter(n=>n.getBoundingClientRect().width&&getComputedStyle(n).display!=='none').slice(0,15).map(n=>({id:n.id,label:n.textContent.trim(),aria:n.getAttribute('aria-label')}))};
   });
   await page.screenshot({path:path.join(__dirname,'baseline-'+hash+'-390.png')});results.push({hash,...layout});
  }
  const menu=page.locator('#mobile-menu');
  if(await menu.count()){
   await menu.click();await page.waitForTimeout(350);await page.screenshot({path:path.join(__dirname,'baseline-drawer-open-390.png')});
   results.push({drawerOpen:await page.evaluate(()=>({bodyClass:document.body.className,sidebar:(()=>{const n=document.querySelector('.sidebar'),r=n.getBoundingClientRect(),s=getComputedStyle(n);return {left:r.left,right:r.right,width:r.width,transform:s.transform}})()}))});
  }
  const out={baselineSHA256:crypto.createHash('sha256').update(fs.readFileSync(path.join(stage,'baseline.html'))).digest('hex'),browser:'Headless Edge '+browser.version(),viewport:{width:390,height:844},userProfileUsed:false,remoteNetworkBlocked:true,results};
  fs.writeFileSync(path.join(__dirname,'baseline-overflow.json'),JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));
 }finally{if(browser)await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
