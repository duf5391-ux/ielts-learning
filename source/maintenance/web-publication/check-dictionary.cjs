// Exercise the actual hosted dictionary engine with isolated Node state and files.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {pathToFileURL, fileURLToPath} = require('node:url');
const root = path.join(__dirname, 'dist/local-dictionary');
const enginePath = path.join(root, 'dictionary-engine.js');
let ctx;
const head = {appendChild(element) {
  try {vm.runInContext(fs.readFileSync(fileURLToPath(element.src),'utf8'),ctx); queueMicrotask(()=>element.onload());}
  catch(e) {queueMicrotask(()=>element.onerror?.(e));}
}};
const context = {window:{}, document:{currentScript:{src:pathToFileURL(enginePath).href}, head,
  createElement:()=>({remove(){}})}, URL, Response, Blob, DecompressionStream, AbortController,
  setTimeout, clearTimeout, console,
  fetch: async(url)=>{
    const bytes=fs.readFileSync(fileURLToPath(url));
    return new Response(process.argv.includes('--decoded-response') ? require('node:zlib').gunzipSync(bytes) : bytes);
  }};
ctx=vm.createContext(context);
vm.runInContext(fs.readFileSync(enginePath,'utf8'),ctx);
(async()=>{
  const api=ctx.window.IELTSLocalDictionary;
  const manifest=await api.ready();
  assert.equal(manifest.entryCount,770611);
  for(const term of ['sustainable','children','serendipity','associated','IELTS']){
    const result=await api.lookup(term);
    assert(result.entries.length>0,term);
    assert(result.entries.some(x=>x.translation||x.definition),term);
  }
  const a=await api.lookup('children');
  assert(a.entries.some(x=>/child/i.test(x.word)));
  console.log(JSON.stringify({passed:6,entryCount:manifest.entryCount,checks:['manifest','sustainable','children + base forms','serendipity','associated','IELTS']}));
})().catch(error=>{console.error(error);process.exitCode=1});
