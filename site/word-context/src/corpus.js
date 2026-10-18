import {sentenceSpans, wordTokens} from './lookup.js?v=509356376181';

// Exact source slices only. Long sentences use an explicitly labelled fragment;
// paragraph identity remains available for rotation, provenance and saved grades.
export function memorySnippet(p, wordId, maxWords=48) {
  const target=p.matches?.find(m=>m.wordId===wordId)?.highlight||p.highlight||[];
  if(!target.length)return null;
  const sentences=sentenceSpans(p.text);
  const spans=sentences.filter(s=>target.some(h=>h.start>=s.start&&h.end<=s.end));
  const size=s=>wordTokens(s.text).length;
  // Keep enough context: when the target sentence is short, include its adjacent
  // original sentence. Never stitch unrelated parts or generate filler.
  const pairs=sentences.slice(0,-1).map((s,i)=>({start:s.start,end:sentences[i+1].end,text:p.text.slice(s.start,sentences[i+1].end)}))
    .filter(s=>spans.some(t=>t.start>=s.start&&t.end<=s.end&&size(t)<20));
  const candidates=[...spans,...pairs].filter(s=>size(s)<=maxWords).sort((a,b)=>Math.abs(size(a)-30)-Math.abs(size(b)-30));
  let chosen=candidates[0]||spans.sort((a,b)=>size(a)-size(b))[0]||{start:0,end:p.text.length,text:p.text};
  let fragment=!candidates.length;
  if(size(chosen)>maxWords){
    const tokens=wordTokens(chosen.text),hit=target.find(h=>h.start>=chosen.start&&h.end<=chosen.end);
    const index=Math.max(0,tokens.findIndex(t=>t.start+chosen.start<=hit.start&&t.end+chosen.start>=hit.end));
    const from=Math.max(0,Math.min(index-20,tokens.length-maxWords)),to=Math.min(tokens.length,from+maxWords);
    chosen={start:chosen.start+tokens[from].start,end:chosen.start+tokens[to-1].end};
  }
  const start=chosen.start,end=chosen.end,text=p.text.slice(start,end);
  const matches=(p.matches||[{wordId,highlight:target}]).map(m=>({...m,highlight:m.highlight.filter(h=>h.start>=start&&h.end<=end).map(h=>({...h,start:h.start-start,end:h.end-start}))})).filter(m=>m.highlight.length);
  return {...p,id:`mem-${p.id}-${start}-${end}`,memoryParentId:p.id,parentParagraphId:p.parentParagraphId||p.id,
    sentenceStart:(p.sentenceStart||0)+start,sentenceEnd:(p.sentenceStart||0)+end,text,
    wordCount:wordTokens(text).length,matches,highlight:matches.find(m=>m.wordId===wordId)?.highlight||[],
    isSentence:!fragment,isFragment:fragment,translation:start===0&&end===p.text.length?p.translation:''};
}

// Advance only on a committed memory answer; rendering and restoration never consume a sample.
export function rotateMemoryPassages(passages, history, wordId, beforeEventId = null) {
  if (passages.length < 2) return passages;
  const end = beforeEventId ? history.findIndex(e => e.id === beforeEventId) : -1;
  const answers = (end >= 0 ? history.slice(0, end) : history)
    .filter(e => e.type === 'memory' && e.wordId === wordId && !e.undone);
  const previous = passages.findIndex(p => p.id === answers.at(-1)?.passageId);
  const offset = previous >= 0 ? (previous + 1) % passages.length : answers.length % passages.length;
  return [...passages.slice(offset), ...passages.slice(0, offset)];
}

// Shared original paragraphs are indexed once, then retrieved for any matching word.
export function createCorpus(data) {
  const articles=new Map((data.articles||[]).map(a=>[a.id,a]));
  const shared=new Map((data.paragraphs||[]).map(p=>[p.id,{...p,article:articles.get(p.articleId),matches:[]}]));
  const words=data.words.map(word=>{
    const matches=(word.matches||[]).filter(m=>(m.semanticStatus==='accepted'||word.personal&&m.semanticStatus==='lexical')&&shared.has(m.paragraphId));
    const passages=matches.map(m=>{
      const p=shared.get(m.paragraphId),a=p.article;
      p.matches.push({wordId:word.id,highlight:m.highlight});
      return {...p,id:p.id,highlight:m.highlight,source:{...a.source,title:a.title,paragraph:`第${p.index}段`},sourceLabel:sourceLabel(a),topics:a.topics||[],translation:p.translation||''};
    });
    return {...word,originalMeaning:word.meaning,meaning:word.meaning.replace(/^(?:adj\.|adv\.|n\.|v\.|vt\.|vi\.|prep\.)\s*/,''),passages,acceptedSpellings:word.acceptedSpellings||word.spellingVariants||[]};
  });
  for(const p of shared.values()){
    p.source={...p.article.source,title:p.article.title,paragraph:`第${p.index}段`};
    p.sourceLabel=sourceLabel(p.article);p.topics=p.article.topics||[];
  }
  const wordMap=new Map(words.map(w=>[w.id,w]));
  const topics=[...new Set([...articles.values()].flatMap(a=>a.topics||[]))].sort((a,b)=>a.localeCompare(b,'zh-CN'));
  function ranked(topic='',scope=words,sort='topic'){
    // Topic concentration, not global frequency: generic words should not head every topic.
    const relevance=w=>w.passages.length?w.passages.filter(p=>p.topics.includes(topic)).length/w.passages.length:0;
    return scope.filter(w=>!topic||w.passages.some(p=>p.topics.includes(topic))).slice().sort((a,b)=>
      sort==='topic'?(topic?relevance(b)-relevance(a):0)||(a.originalOrder-b.originalOrder):
      sort==='original'?(a.originalOrder-b.originalOrder):
      (b.semanticFrequency?.acceptedArticleCount||0)-(a.semanticFrequency?.acceptedArticleCount||0)||
      (b.semanticFrequency?.acceptedOccurrenceCount||0)-(a.semanticFrequency?.acceptedOccurrenceCount||0)||a.originalOrder-b.originalOrder);
  }
  function retrieve(ids,topic='',limit=10){
    const wanted=new Set(ids),count=new Map(ids.map(id=>[id,0]));
    const candidates=[...shared.values()].filter(p=>(!topic||p.topics.includes(topic))&&p.matches.some(m=>wanted.has(m.wordId)));
    const selected=[],used=new Set();
    // Retrieve useful coverage before adding repeated hits of the most common word.
    while(selected.length<limit&&selected.length<candidates.length){
      let best=null,bestScore=-1;
      for(const p of candidates){
        if(used.has(p.id))continue;
        const hit=p.matches.filter(m=>wanted.has(m.wordId));
        const score=hit.reduce((n,m)=>n+(count.get(m.wordId)<2?12:1),0)+(p.wordCount>=35&&p.wordCount<=180?2:0)+
          (p.article.source.sourceQuality==='cambridge_original_book_local_transcription'?1:0);
        if(score>bestScore){best=p;bestScore=score;}
      }
      if(!best)break;used.add(best.id);selected.push(best);
      for(const m of best.matches)if(wanted.has(m.wordId))count.set(m.wordId,count.get(m.wordId)+1);
    }
    return selected;
  }
  function forWord(id,topic='',limit=12){
    const w=wordMap.get(id);if(!w)return[];
    return w.passages.filter(p=>!topic||p.topics.includes(topic)).slice().sort((a,b)=>
      Number(b.source.sourceQuality==='cambridge_original_book_local_transcription')-Number(a.source.sourceQuality==='cambridge_original_book_local_transcription')||
      Math.abs(a.wordCount-85)-Math.abs(b.wordCount-85)).slice(0,limit);
  }
  return {words,articles,paragraphs:shared,topics,ranked,retrieve,forWord,wordMap};
}
export function sourceLabel(article){
  const s=article.source;
  if(s.kind==='user-selection')return s.label||'阅读与写作标记';
  if(s.book&&(s.section==='listening'||String(s.sourceQuality).includes('listening')))return `剑桥雅思 ${s.book} · Test ${s.test} · 听力 Part ${s.part||s.passage||3}`;
  return s.book?`剑桥雅思 ${s.book} · Test ${s.test} · Passage ${s.passage}`:'补充雅思阅读资料';
}

// Account entries only store the word and the encounter. Original sentences are
// retrieved from the shared file corpus and reconstructed, never copied into a
// separate per-account material database.
export function corpusWithBank(baseData,bank,lookup){
  if(!lookup||!Object.keys(bank||{}).length)return createCorpus(baseData);
  const articles=new Map(baseData.articles.map(a=>[a.id,a]));
  const paragraphs=new Map(baseData.paragraphs.map(p=>[p.id,p]));
  const words=new Map(baseData.words.map(w=>[w.id,w]));
  let order=baseData.words.length;
  for(const entry of Object.values(bank||{})){
    const found=lookup.search(entry,{limit:12}),original=words.get(entry.id);
    const matches=[];
    for(const origin of entry.origins || []){
      if(!origin.context)continue;
      const highlights=wordTokens(origin.context).filter(token=>token.form===entry.term).map(token=>({start:token.start,end:token.end}));
      if(!highlights.length)continue;
      const articleId=`marked-${origin.paragraphId}`,id=`${articleId}-${entry.id}`;
      articles.set(articleId,{id:articleId,title:origin.sourceLabel||'阅读与写作标记',topics:[],source:{kind:'user-selection',label:origin.sourceLabel,route:origin.sourceRoute||''}});
      paragraphs.set(id,{id,articleId,index:1,text:origin.context,translation:'',wordCount:wordTokens(origin.context).length});
      matches.push({paragraphId:id,articleId,highlight:highlights,occurrences:highlights.length,semanticStatus:'lexical'});
    }
    for(const sentence of found.sentences){
      if(!articles.has(sentence.articleId))articles.set(sentence.articleId,lookup.getArticle(sentence.articleId));
      if(!paragraphs.has(sentence.id))paragraphs.set(sentence.id,{...sentence,isSentence:true,matches:undefined});
      matches.push({paragraphId:sentence.id,articleId:sentence.articleId,highlight:sentence.highlight,occurrences:sentence.occurrences,semanticStatus:'lexical'});
    }
    words.set(entry.id,{...(original||entry),originalOrder:original?.originalOrder||++order,
      // The original 303-word definitions and frequencies remain authoritative.
      meaning:original?.meaning||entry.meaning||'',personal:true,bankEntry:entry,
      lexicalFrequency:found,matches:[...(original?.matches||[]),...matches]});
  }
  return createCorpus({...baseData,articles:[...articles.values()],paragraphs:[...paragraphs.values()],words:[...words.values()]});
}
