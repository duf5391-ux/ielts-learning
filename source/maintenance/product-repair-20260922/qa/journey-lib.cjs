const fs=require('fs'),path=require('path'),http=require('http');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const workspace=path.resolve(__dirname,'../..'),book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
exports.fs=fs;exports.path=path;exports.workspace=workspace;
exports.start=async function(opts={}) {
 const packed=opts.packed||false,root=opts.root?path.resolve(opts.root):packed?path.join(workspace,'web-publication/dist'):path.resolve(book);
 let failedOnce=false;const server=http.createServer((req,res)=>{
  const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1)||'index.html';
  const file=rel==='index.html'&&!packed?(opts.file||path.join(book,'开始学习.html')):path.resolve(root,rel);
  if(opts.failOnce&&rel.includes(opts.failOnce)&&!failedOnce){failedOnce=true;res.writeHead(503).end('Isolated QA network fault');return;}
  if(!(file===opts.file||file.startsWith(root+path.sep)||file.startsWith(root+'/'))||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
  const send=()=>{res.writeHead(200,{'Content-Type':({'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.mp3':'audio/mpeg'})[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});fs.createReadStream(file).pipe(res)};
  if(opts.delay&&rel.startsWith('progressive/'))setTimeout(send,opts.delay);else send();
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port+'/';
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:opts.width||1440,height:opts.width===390?844:1000},acceptDownloads:true});
 await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 async function ready(){await page.waitForFunction(()=>window.IELTSRecordStore&&!document.body.hasAttribute('data-progressive-state'),null,{timeout:120000});}
 async function go(id){await page.evaluate(id=>location.hash=id,id);await page.waitForTimeout(150);}
 async function shot(name,fullPage=false){await page.screenshot({path:path.join(__dirname,name+'.png'),fullPage});}
 async function snapshot(){return page.evaluate(()=>({hash:location.hash,active:[...document.querySelectorAll('main>.panel')].filter(n=>!n.hidden).map(n=>({id:n.id,text:n.innerText.slice(0,24000)})),controls:[...document.querySelectorAll('button,a,select,input,textarea')].filter(n=>n.checkVisibility()).map(n=>({tag:n.tagName,id:n.id,text:n.innerText.slice(0,120),type:n.type,href:n.getAttribute('href'),value:n.value,disabled:n.disabled,save:n.dataset.save})),overflow:document.documentElement.scrollWidth>innerWidth}));}
 return {page,context,browser,base,errors,ready,go,shot,snapshot,close:async()=>{await context.close();await browser.close();server.close()}};
};
