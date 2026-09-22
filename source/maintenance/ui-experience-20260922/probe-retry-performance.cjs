const {start,fs,path}=require('../product-repair-20260922/qa/journey-lib.cjs');
(async()=>{const e=await start({packed:true}),p=e.page;try{
  p.setDefaultTimeout(120000);
  p.on('dialog',d=>d.accept());
  await p.goto(e.base+'#test-reading');await e.ready();
  await p.locator('[data-test-start=reading]').click();
  await p.locator('[data-save="full-test-reading-q1"]').fill('isolated-performance-answer');
  await p.locator('[data-test-submit=reading]').click();
  await p.locator('.ux-history-jump[data-ux-history=reading]').click();
  const cdp=await e.context.newCDPSession(p);await cdp.send('Profiler.enable');await cdp.send('Profiler.start');
  const t=Date.now();console.log('Measuring retry on the isolated packed browser');
  await p.locator('[data-test-retry=reading]').click();
  await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const elapsed=Date.now()-t,{profile}=await cdp.send('Profiler.stop');
  const times=new Map();profile.samples.forEach((id,i)=>times.set(id,(times.get(id)||0)+profile.timeDeltas[i]));
  const top=profile.nodes.map(n=>({function:n.callFrame.functionName,url:n.callFrame.url,line:n.callFrame.lineNumber+1,ms:Math.round((times.get(n.id)||0)/1000)})).sort((a,b)=>b.ms-a.ms).slice(0,25);
  const out={elapsedMs:elapsed,errors:e.errors,top};fs.writeFileSync(path.join(__dirname,'retry-performance.json'),JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));
}finally{await e.close()}})().catch(e=>{console.error(e);process.exitCode=1});
