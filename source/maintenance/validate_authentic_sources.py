"""Check source locations and literal reading excerpts independently of authoring."""
from pathlib import Path
from collections import Counter
import json,re,unicodedata,hashlib
from pypdf import PdfReader
from bs4 import BeautifulSoup
from build_authentic_case_database import BOOK,HERE,QA,read,items,types,original_key,CASE_FILES

def norm(t):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',t.lower()))
def page_text(page,printed=None):
    lines=(page.extract_text() or '').strip().splitlines()
    if lines and re.fullmatch(r'\s*\d{1,3}\s*',lines[-1]):lines=lines[:-1]
    if printed is not None:lines=[line for line in lines if line.strip()!=str(printed)]
    lines=[line for line in lines if not re.fullmatch(r'(?:Reading|READING|Test\s+\d)',line.strip())]
    return '\n'.join(lines)

def main():
    cache={};result=[];issues=[]
    manual_file=QA/'manual-source-verifications.json'
    manual=read(manual_file) if manual_file.exists() else {}
    for name in CASE_FILES:
        if not (HERE/name).exists():continue
        for c in items(read(HERE/name)):
            src=c['source'];p=BOOK/src['path'];suffix=p.suffix.lower()
            if suffix=='.pdf':
                if str(p) not in cache:cache[str(p)]=PdfReader(p)
                doc=cache[str(p)]
                requested=src.get('pages') or src.get('page')
                requested=requested if isinstance(requested,list) else [requested]
                source_text='\n'.join(page_text(doc.pages[int(n)-1],int(n)-1 if 'Cambridge IELTS 21' in src.get('title','') else None) for n in requested if n)
                if not source_text:source_text='\n'.join(x.extract_text() or '' for x in doc.pages)
            else:
                source_text=p.read_text(encoding='utf-8-sig')
                if suffix in ['.html','.htm']:source_text=BeautifulSoup(source_text,'html.parser').get_text(' ',strip=True)
            record={'id':c['id'],'source':src['path'],'source_pages':src.get('page'),'questions':len(c.get('questions',[])),'checks':{}}
            if c['skill']=='reading':
                paras=c.get('paragraphs',[]);texts=[x['text'] if isinstance(x,dict) else x for x in paras]
                matched=[norm(t) in norm(source_text) for t in texts]
                record['checks']['paragraphs_match_cited_pages']=all(matched)
                record['paragraph_matches']=matched
                record['word_count']=sum(len(re.findall(r"\b[\w'-]+\b",t)) for t in texts)
                record['checks']['multiple_paragraphs']=len(paras)>=2
                record['checks']['medium_length']=record['word_count']>=180
                record['checks']['answers_and_explanations']=all(q.get('answer') is not None and q.get('explanation') and q.get('evidence') for q in c.get('questions',[]))
                record['checks']['has_intensive']=bool(c.get('intensive'))
                if 'Cambridge IELTS 21' in src.get('title','') and src.get('answerPage'):
                    raw_key=doc.pages[int(src['answerPage'])-1].extract_text()
                    key={m.group(1):m.group(2).strip() for m in re.finditer(r'(?m)^\s*(\d{1,2})\s+([^\n]+)$',raw_key)}
                    mismatches=[];verified=0
                    for q in c['questions']:
                        num=str(q['number'])
                        if num not in key:continue
                        expected=norm(key[num]);actual=q['answer'];actual=' '.join(actual) if isinstance(actual,list) else str(actual)
                        alternatives=[norm(x) for x in re.split(r'\s+(?:I|/|OR)\s+',key[num])]
                        alternatives.append(norm(re.sub(r'\([^)]*\)','',key[num])))
                        actual_alternatives=[norm(x) for x in re.split(r'\s+(?:I|/|OR)\s+',actual)]
                        option_gloss=len(expected)==1 and re.match(r'^'+re.escape(expected)+r'(?:\s|[.：:（(])',actual.lower())
                        if not (all(a and a in alternatives for a in actual_alternatives) or option_gloss):mismatches.append({'number':num,'provided':actual,'source':key[num]})
                        else:verified+=1
                    record['checks']['official_answer_key_match']=not mismatches
                    record['answer_key_matches']=verified;record['answer_key_mismatches']=mismatches
                record['paragraph_hashes']=[hashlib.sha256(norm(t).encode()).hexdigest() for t in texts]
                override=manual.get(c['id'],{})
                if override.get('paragraphTextSha256')==hashlib.sha256('\n'.join(texts).encode()).hexdigest():
                    record['checks'].update(override.get('checks',{}));record['manual_verification']=override.get('reason')
            else:
                record['checks']['prompt_matches_cited_page']=norm(c['prompt']) in norm(source_text)
                record['checks']['multiple_model_paragraphs']=len(c.get('modelAnswer',[]))>=2
                record['checks']['has_specific_explanations']=bool(c.get('explanation')) and bool(c.get('intensive'))
                if c['skill']=='writing1':record['checks']['original_figure_exists']=(BOOK/c.get('image','NONE')).is_file()
            result.append(record)
            if not all(record['checks'].values()):issues.append(record)
    out={'checked_cases':len(result),'flagged_for_review':len(issues),'cases':result,'issues':issues}
    (QA/'source-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'checked_cases':len(result),'flagged_for_review':len(issues),'issues':[{'id':x['id'],'checks':x['checks']} for x in issues]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
