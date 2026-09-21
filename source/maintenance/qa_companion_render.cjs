const vm = require('vm');
const fs = require('fs');
const path = require('path');
const work = 'C:/Users/Admin1/Documents/ChatGPT/ielts';
function run(index) {
 const nodes = {};
 function node(id) { return nodes[id] ||= {value: ['#source','#unit'].includes(id)?'all':id==='#rank'?'df':'', options:[], innerHTML:'', textContent:'', events:{}, append(o){this.options.push(o);if(!this.value)this.value=o.value;},addEventListener(k,f){this.events[k]=f;},replaceChildren(){this.innerHTML='';},scrollIntoView(){}}; }
 const context = {document:{querySelector:node,createElement:()=>({value:'',textContent:''})},scrollTo(){}};
 vm.createContext(context);
 const script=fs.readFileSync(path.join(work,`cleanup-companion-script-${index}-0.js`),'utf8');
 vm.runInContext(script,context);
 const result={index,initialCount:node('#count').textContent};
 if(index===0){
  if((node('#out').innerHTML.match(/<article>/g)||[]).length!==80)throw new Error('Expected 80 word cards');
  node('#q').value='education';node('#q').events.input();
  if(!node('#out').innerHTML.includes('<h2>education</h2>'))throw new Error('Search missing education');
  for(const o of node('#source').options){node('#source').value=o.value;node('#q').value='';node('#q').events.input();if(!node('#out').innerHTML.includes('<article>'))throw new Error('Empty source '+o.value);}
  result.sourceFilters=node('#source').options.length;
  result.unitFilters=node('#unit').options.length;
  if(/来源|核验|出处|原始单位/.test(node('#out').innerHTML))throw new Error('Metadata visible');
 } else {
  let snippets=0;
  for(const o of node('#scope').options){node('#scope').value=o.value;node('#scope').events.input();const word=node('#rows').innerHTML.match(/data-word="([^"]+)"/)[1];node('#rows').onclick({target:{dataset:{word}}});if(!node('#evidence').innerHTML.includes('原文例句'))throw new Error('No snippets');snippets+=(node('#evidence').innerHTML.match(/class="quote"/g)||[]).length;}
  result.groups=node('#scope').options.map(o=>o.textContent);result.snippets=snippets;
  if(/来源|核验|出处|原 PDF 页/.test(node('#evidence').innerHTML))throw new Error('Metadata visible');
 }
 return result;
}
const results=[run(0),run(1)];
const reportPath=path.join(work,'cleanup-audit.json');
const report=JSON.parse(fs.readFileSync(reportPath,'utf8'));
report.render_qa=results;
fs.writeFileSync(reportPath,JSON.stringify(report,null,2),'utf8');
process.stdout.write(JSON.stringify(results,null,2));
