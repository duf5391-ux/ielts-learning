// Offline lexical retrieval. Matches are source-backed, not reviewed meanings.
const TOKEN_SOURCE="(?<![\\p{L}\\p{M}\\p{N}_])[\\p{L}\\p{M}]+(?:['’‘‐‑-][\\p{L}\\p{M}]+)*(?![\\p{L}\\p{M}\\p{N}_])";
const SINGLE_WORD=/^[\p{L}\p{M}]+(?:['-][\p{L}\p{M}]+)*$/u;
export function normalizeLookupTerm(value){
  return String(value??'').normalize('NFKC').replace(/[’‘]/g,"'").replace(/[‐‑]/g,'-').trim().toLowerCase();
}
export function personalWordId(value){
  const term=normalizeLookupTerm(value);
  return SINGLE_WORD.test(term)?'pw-'+encodeURIComponent(term):null;
}
export function wordTokens(text){
  return [...String(text).matchAll(new RegExp(TOKEN_SOURCE,'gu'))].map(m=>({text:m[0],form:normalizeLookupTerm(m[0]),start:m.index,end:m.index+m[0].length}));
}

// Boundaries preserve exact substrings. Unpunctuated final fragments are omitted
// rather than completed or silently presented as grammatical sentences.
export function sentenceSpans(text){
  const result=[];let start=0;
  for(const m of text.matchAll(/[.!?]+["'”’\])]*(?=\s|$)/gu)){
    const punctuation=m[0],at=m.index,end=at+punctuation.length;
    if(punctuation.startsWith('.')){
      const before=text.slice(start,at+1),after=text.slice(end).trimStart();
      const token=before.match(/([A-Za-z][A-Za-z.]*)\.$/)?.[1]||'';
      if(after&&/^(?:mr|mrs|ms|dr|prof|rev|st|sr|jr|vs|cf|e\.g|i\.e|a\.m|p\.m)$/i.test(token))continue;
      if(/^(?:fig|no|vol|p|pp)$/i.test(token)&&/^\(?\d/.test(after))continue;
      if(/^(?:inc|ltd)$/i.test(token)&&/^[a-z]/.test(after))continue;
      if(after&&/\bet\s+al\.$/i.test(before))continue;
      if(/^[A-Z]$/.test(token)&&/^(?:[A-Z]|and\s+[A-Z]\.)/.test(after))continue;
      if(/^(?:[A-Za-z]\.)+[A-Za-z]$/.test(token)&&/^[a-z]/.test(after))continue;
      if(punctuation.startsWith('...')&&/^[a-z]/.test(after))continue;
    }
    if(/["”’']$/.test(punctuation)&&/^(?:he|she|they|it|we|I|the\s+\w+)\s+(?:said|says|asked|asks|added|adds|replied|replies|explained|explains|noted|notes)\b/.test(text.slice(end).trimStart()))continue;
    while(start<end&&/\s/u.test(text[start]))start++;
    if(end>start&&wordTokens(text.slice(start,end)).length)result.push({start,end,text:text.slice(start,end)});
    start=end;
  }
  return result;
}

function labelFor(article){
  const s=article.source||{};
  if(s.book&&(s.section==='listening'||String(s.sourceQuality).includes('listening')))
    return `剑桥雅思 ${s.book} · Test ${s.test} · 听力 Part ${s.part||s.passage||3}`;
  return s.book?`剑桥雅思 ${s.book} · Test ${s.test} · Passage ${s.passage}`:'补充雅思阅读资料';
}
function unknown(term){return {id:personalWordId(term),baseWordId:null,term,meaning:'',pos:'',phonetic:'',forms:[],acceptedSpellings:[],dictionarySource:'unavailable',unresolved:true};}

export function createLookup(baseData,lookupData,searchCorpusData=baseData){
  const dictionary=Object.assign(Object.create(null),lookupData?.entries||{}),formIndex=Object.assign(Object.create(null),lookupData?.formIndex||{});
  const originals=baseData.words||[],baseExact=new Map(),baseForms=new Map();
  for(const w of originals){
    baseExact.set(normalizeLookupTerm(w.term),w);
    for(const f of [w.term,...(w.forms||[]),...(w.acceptedSpellings||[])]){
      const key=normalizeLookupTerm(f),list=baseForms.get(key)||[];
      if(!list.some(x=>x.id===w.id))list.push(w);baseForms.set(key,list);
    }
  }
  function baseEntry(w){return {id:w.id,baseWordId:w.id,term:w.term,meaning:w.meaning,pos:w.pos||'',phonetic:w.phonetic||'',forms:[...(w.forms||[])],acceptedSpellings:[...(w.acceptedSpellings||[])],dictionarySource:'target303',unresolved:false};}
  function headEntry(head){
    const canonical=baseExact.get(head)||(baseForms.get(head)?.length===1?baseForms.get(head)[0]:null);
    if(canonical)return baseEntry(canonical);
    const row=dictionary[head];if(!row)return null;
    return {id:personalWordId(head),baseWordId:null,term:head,meaning:row[0]||'',pos:row[1]||'',phonetic:row[2]||'',forms:[...(row[3]||[])],acceptedSpellings:[],dictionarySource:'local-dictionary',unresolved:!row[0]};
  }
  function lookup(value){
    const form=normalizeLookupTerm(value);
    if(!SINGLE_WORD.test(form))return {form,entry:null,candidates:[],needsChoice:false,error:'select_one_word'};
    const byId=new Map();
    for(const w of baseForms.get(form)||[])byId.set(w.id,baseEntry(w));
    const heads=new Set(formIndex[form]||[]);
    if(dictionary[form])heads.add(form);
    // Pure inflected entries (e.g. "run的过去式", "pl. 孩子") are represented
    // by their dictionary lemmas. Independent entries such as running/saw stay.
    const direct=dictionary[form];
    if(direct&&heads.size>1&&((direct[4]?.length&&(!direct[1]||/^pl\.?$/.test(direct[1])))||(!direct[1]&&/的(?:过去式|过去分词|现在分词|第三人称|复数)/.test(direct[0]))))heads.delete(form);
    for(const head of heads){const entry=headEntry(head);if(entry)byId.set(entry.id,entry);}
    const candidates=[...byId.values()].sort((a,b)=>Number(!!b.baseWordId)-Number(!!a.baseWordId)||Number(b.term===form)-Number(a.term===form)||a.term.localeCompare(b.term,'en'));
    if(!candidates.length)candidates.push(unknown(form));
    return {form,entry:candidates.length===1?candidates[0]:null,candidates,needsChoice:candidates.length>1};
  }

  const articles=new Map((searchCorpusData.articles||[]).map(a=>[a.id,a]));
  const paragraphs=new Map(),sentences=[],postings=new Map();
  for(const p of searchCorpusData.paragraphs||[]){
    if(p.isBodyEligible!==true||!articles.has(p.articleId))continue;
    paragraphs.set(p.id,p);const article=articles.get(p.articleId);
    for(const span of sentenceSpans(p.text)){
      const sentence={id:`sent-${p.id}-${span.start}-${span.end}`,parentParagraphId:p.id,articleId:p.articleId,index:p.index,
        text:span.text,sentenceStart:span.start,sentenceEnd:span.end,wordCount:wordTokens(span.text).length,
        article,source:{...article.source,title:article.title,paragraph:`第${p.index}段`,parentParagraphId:p.id,paragraphTextSha256:p.textSha256},
        sourceLabel:labelFor(article),sourceGroup:article.sourceGroup,topics:article.topics||[],semanticStatus:'unreviewed'};
      const sentenceIndex=sentences.push(sentence)-1;
      for(const token of wordTokens(span.text)){
        const list=postings.get(token.form)||[];
        list.push({sentenceIndex,start:token.start,end:token.end,form:token.text});postings.set(token.form,list);
      }
    }
  }
  function search(entry,{limit=12}={}){
    if(!entry||!SINGLE_WORD.test(normalizeLookupTerm(entry.term)))return {entryId:entry?.id||null,totalOccurrences:0,sentenceCount:0,rawSentenceCount:0,articleCount:0,sourceCounts:{},insufficient:true,sentences:[],semanticStatus:'unreviewed'};
    const forms=new Set([entry.term,...(entry.forms||[]),...(entry.acceptedSpellings||[])].map(normalizeLookupTerm).filter(f=>SINGLE_WORD.test(f)));
    const hits=new Map();
    for(const form of forms)for(const hit of postings.get(form)||[]){
      const list=hits.get(hit.sentenceIndex)||[];list.push({start:hit.start,end:hit.end,form:hit.form});hits.set(hit.sentenceIndex,list);
    }
    const found=[...hits].sort((a,b)=>a[0]-b[0]).map(([index,highlight])=>({...sentences[index],highlight:highlight.sort((a,b)=>a.start-b.start),occurrences:highlight.length}));
    const sourceCounts={},allArticles=new Set();
    for(const s of found){
      allArticles.add(s.articleId);const key=s.source.sourceQuality||'unknown';
      const row=sourceCounts[key]||(sourceCounts[key]={occurrences:0,sentenceCount:0,articleIds:new Set()});
      row.occurrences+=s.occurrences;row.sentenceCount++;row.articleIds.add(s.articleId);
    }
    for(const row of Object.values(sourceCounts)){row.articleCount=row.articleIds.size;delete row.articleIds;}
    const seen=new Set(),unique=[];
    for(const sentence of found){
      const key=normalizeLookupTerm(sentence.text).replace(/\s+/g,' ');
      if(!seen.has(key)){seen.add(key);unique.push(sentence);}
    }
    // Round-robin source articles provides different source contexts before a
    // second sentence from the same article, without inventing extra samples.
    const buckets=new Map();for(const s of unique){const b=buckets.get(s.articleId)||[];b.push(s);buckets.set(s.articleId,b);}
    const selected=[],max=Math.max(0,Math.min(Number.isFinite(limit)?Math.floor(limit):12,100));
    for(let round=0;selected.length<max;round++){
      let advanced=false;
      for(const bucket of buckets.values())if(bucket[round]){selected.push(bucket[round]);advanced=true;if(selected.length===max)break;}
      if(!advanced)break;
    }
    return {entryId:entry.id,totalOccurrences:found.reduce((sum,s)=>sum+s.occurrences,0),sentenceCount:unique.length,rawSentenceCount:found.length,
      articleCount:allArticles.size,sourceCounts,insufficient:unique.length<3,sentences:selected,semanticStatus:'unreviewed',
      frequencyBasis:'Exact dictionary forms in eligible source sentences; all-source occurrence/article counts; duplicate sentence texts collapsed for samples.'};
  }
  function prepareBankImport(seed){
    if(!seed||typeof seed.id!=='string'||!/^[-a-zA-Z0-9_]{1,100}$/.test(seed.id)||
        typeof seed.title!=='string'||seed.title.length>300||!Array.isArray(seed.words)||!seed.words.length||seed.words.length>500)
      throw new Error('勾选词表不完整，请重新打开保存的入口。');
    const seen=new Set();
    return seed.words.map(item=>{
      const term=normalizeLookupTerm(item?.term);
      if(!SINGLE_WORD.test(term)||seen.has(term)||typeof item.meaning!=='string'||item.meaning.length>8000)
        throw new Error('勾选词表有重复词或缺少释义，尚未加入。');
      seen.add(term);
      // Import the selected spelling itself, never silently change it to a lemma.
      const exact=lookup(term).candidates.find(entry=>entry.term===term);
      const entry=exact?{...exact}:unknown(term);
      if(!entry.baseWordId && item.meaning.trim()){entry.meaning=item.meaning.trim();entry.dictionarySource='user';entry.unresolved=false;}
      const context=typeof item.context==='string'?item.context.slice(0,4000):'';
      const sourceRoute=typeof item.sourceRoute==='string'?item.sourceRoute.slice(0,300):'';
      const hasContext=wordTokens(context).some(token=>token.form===term);
      entry.ready=!!entry.meaning.trim()&&(hasContext||search(entry,{limit:0}).sentenceCount>0);
      return {entry,providedMeaning:!!item.meaning.trim(),origin:{paragraphId:`import:${seed.id}`,start:0,end:term.length,text:term,sourceLabel:seed.title,
        ...(hasContext?{context,sourceRoute}:{})}};
    });
  }
  return {lookup,search,prepareBankImport,getParagraph:id=>paragraphs.get(id)||null,getArticle:id=>articles.get(id)||null,
    articles,paragraphs,corpusCounts:searchCorpusData.counts||{},indexedSentenceCount:sentences.length};
}
