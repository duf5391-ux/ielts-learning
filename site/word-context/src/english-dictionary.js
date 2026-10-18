// Source text is loaded once, independently of account state and study grading.
let dictionary=null;
const normalize=value=>String(value??'').toLowerCase().replace(/’/g,"'").trim().replace(/\s+/g,' ');
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function setEnglishDictionary(data){dictionary=data;}
export async function loadEnglishDictionary(){
 try{const response=await fetch(new URL('../data/english-definitions.json',import.meta.url));if(response.ok)setEnglishDictionary(await response.json());}catch{}
}
export function englishEntry(word){
 if(!dictionary)return null;
 for(const term of [word.term,...(word.acceptedSpellings||[]),...(word.forms||[])]){
  const key=normalize(term),head=dictionary.entries[key]?key:dictionary.aliases[key]?.[0];
  if(head&&dictionary.entries[head]?.length)return {head,senses:dictionary.entries[head]};
 }
 return null;
}
export function englishMeaning(word){
 const entry=englishEntry(word);
 if(!entry)return `<div class="english-definition missing"><span>英文词典释义</span><p>${dictionary?'本词典暂未收录这个词语的英文释义。':'英文释义暂未加载，请稍后重新打开页面。'}</p></div>`;
 const senses=entry.senses;
 const text=list=>list.map(x=>`<p lang="en">${esc(x)}</p>`).join('');
 return `<section class="english-definition"><div class="english-definition-heading"><span>英文词典释义${entry.head!==normalize(word.term)?` · ${esc(entry.head)}`:''}</span><a href="https://github.com/skywind3000/ECDICT" target="_blank" rel="noopener noreferrer">ECDICT ↗</a></div>${text(senses.slice(0,3))}${senses.length>3?`<details><summary>其他 ${senses.length-3} 条词典义项</summary>${text(senses.slice(3))}</details>`:''}</section>`;
}
