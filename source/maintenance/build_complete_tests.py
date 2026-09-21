"""Assemble complete question sets from the existing, local source material.

Renders original PDF question pages; never edits their content or the learner's records.
The Inspera listening key uses all 40 entries from the official familiarisation key.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
from html import escape as E
import json,re,shutil
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parent
PROJECT=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an')
BOOK=PROJECT/'outputs/IELTS-四科学习册'
STAGE=Path('D:/IELTS-Work/learning-adjust-20260920')
ASSETS=STAGE/'learning-assets'
LISTEN=PROJECT/'outputs/materials-library/listening-audit-2026-09-14/batch-03'

def listening_answers():
    evidence=json.loads((ROOT/'research/listening-full-answer-evidence-20260920.json').read_text(encoding='utf8'))
    key={str(x['question']):x['answer_options_for_existing_text_input'] for x in evidence['items']}
    assert set(key)=={str(q) for q in range(1,41)} and all(key.values())
    assert 'D' in key['15'] and {'tutor','tutors'}<=set(key['37'])
    return key

LISTENING_NOTE='官方机考体验完整题面，40题均有官方参考答案；选择题可填字母。提交后逐题核对，不自动换算 Band。'

def source_pages():
    ASSETS.mkdir(parents=True,exist_ok=True)
    src=BOOK/'原始参考/8ee8170c-Cambridge IELTS 21 - Academic.pdf'
    doc=pdfium.PdfDocument(str(src))
    for page in range(17,32):
        target=ASSETS/f'c21-page-{page}.png'
        if not target.exists():
            p=doc[page-1];bitmap=p.render(scale=1.75);bitmap.to_pil().save(target);bitmap.close();p.close()
    doc.close()

def sheet(skill,lo,hi):
    return '<div class="la-test-sheet">'+''.join(f'<label><span>Q{q}</span><input autocomplete="off" spellcheck="false" data-save="full-test-{skill}-q{q}" data-test-answer="{skill}" data-question="{q}" aria-label="{skill} Q{q}"></label>' for q in range(lo,hi+1))+'</div>'

def pages(nums):
    return ''.join(f'<img class="la-test-page" loading="lazy" src="learning-assets/c21-page-{p}.png" alt="Cambridge IELTS 21 Test 1 原始题页，PDF 第 {p} 页">' for p in nums)

def recorder(part):
    uid=f'full-test-speaking-{part}'
    return f'''<div class="recorder"><button type="button" data-record="{uid}">开始录音</button><button type="button" data-stop="{uid}" disabled>结束录音</button><a data-download="{uid}" hidden>下载录音</a><audio controls data-preview="{uid}" hidden></audio><label>载入录音 <input type="file" accept="audio/*" data-upload="{uid}"></label><p data-rec-status="{uid}" class="small">结束后请下载录音；文字备份不包含声音。</p></div><label class="field"><span>Part {part} 录音文件名（或记录未能作答的位置）</span><input data-save="{uid}-record-note" data-test-answer="speaking" data-question="{part}"></label>'''

def build():
    source_pages()
    reading_key=['mining','education','notes','journals','Venice','canteen','friends','TRUE','NOT GIVEN','FALSE','NOT GIVEN','TRUE','TRUE','C','B','A','G','breath','questionnaire','wellbeing','depression','C','A','B','D','C','B','A','C','A','H','E','I','A','G','C','YES','NOT GIVEN','NO','YES']
    reading=''.join(f'<section class="la-test-part" data-test-part="reading"><h2>Passage {i} · Q{lo}–{hi}</h2><div data-test-part-progress></div>{pages(nums)}{sheet("reading",lo,hi)}</section>' for i,(lo,hi,nums) in enumerate([(1,13,range(17,21)),(14,26,range(21,26)),(27,40,range(26,30))],1))
    listening='<audio controls preload="none" src="原始参考/precise-official-listening-full.mp3" aria-label="官方机考体验完整听力录音"></audio><p>按录音指示完成四个 Part。此处使用官方机考体验题，计时为本地练习计时。</p>'
    for part in range(1,5):
        raw=BeautifulSoup((LISTEN/f'questions/part-{part}.html').read_text(encoding='utf8'),'html.parser')
        articles=raw.find_all('article')
        for art in articles:
            for bad in art.select('script,iframe'):bad.decompose()
            for tag in art.find_all():
                for key in list(tag.attrs):
                    if key.lower().startswith('on'):del tag[key]
                if tag.get('src'):
                    filename=Path(tag['src']).name
                    src=LISTEN/'figures'/filename
                    assert src.is_file(),src
                    shutil.copy2(src,ASSETS/filename);tag['src']='learning-assets/'+filename
        lo,hi=(part-1)*10+1,part*10
        listening+=f'<section class="la-test-part" data-test-part="listening"><h2>Part {part} · Q{lo}–{hi}</h2><div data-test-part-progress></div><div class="la-full-questions">'+''.join(map(str,articles))+f'</div>{sheet("listening",lo,hi)}</section>'
    listening_key=listening_answers()
    writing=''
    for part,p in [(1,30),(2,31)]:
        writing+=f'<section class="la-test-part" data-test-part="writing"><h2>Task {part}</h2><div data-test-part-progress></div>{pages([p])}<label class="field"><span>Task {part} 作文</span><textarea rows="18" data-save="full-test-writing-task{part}" data-test-answer="writing" data-question="{part}"></textarea></label><p data-wordcount="full-test-writing-task{part}">0 词</p></section>'
    speaking=''
    for part,filename in [(1,'support-1627493a-cambridge-zip-115041_Speaking_sample_task_-_Part_1.pdf'),(2,'support-2e9c2a8e-cambridge-zip-115047_Speaking_sample_task_-_Part_2.pdf'),(3,'support-45086163-cambridge-zip-115053_Speaking_sample_task_-_Part_3.pdf')]:
        reader=PdfReader(BOOK/'原始参考'/filename)
        text='\n'.join(p.extract_text() for p in reader.pages)
        speaking+=f'<section class="la-test-part" data-test-part="speaking"><h2>Part {part}</h2><div data-test-part-progress></div><div class="english" style="white-space:pre-line">{E(text)}</div>{recorder(part)}</section>'
    tests={
      'listening':{'label':'听力','minutes':32,'scope':'4 Parts · 40 题 · 完整原音','note':LISTENING_NOTE,'key':listening_key},
      'reading':{'label':'阅读','minutes':60,'scope':'3 篇文章 · 40 题','note':'Cambridge IELTS 21 Academic · Test 1。题目、图表和字数要求均保留原页。','key':{str(i):[a] for i,a in enumerate(reading_key,1)}},
      'writing':{'label':'写作','minutes':60,'scope':'Task 1 + Task 2','note':'Cambridge IELTS 21 Academic · Test 1。建议分别用 20 / 40 分钟，至少 150 / 250 词。'},
      'speaking':{'label':'口语','minutes':14,'scope':'Part 1 + Part 2 + Part 3','note':'Cambridge 官方公开样题组合。Part 2 准备 1 分钟、说 1–2 分钟；本地自练按 11–14 分钟安排。'}
    }
    panels=[]
    for skill,body in [('listening',listening),('reading',reading),('writing',writing),('speaking',speaking)]:
        m=tests[skill]
        reference=''
        if skill=='writing':reference='<p>检查 Task 1 是否选出主要特征并比较数据；Task 2 是否直接回应观点并展开理由。两项都检查段落衔接、词汇搭配、语法与拼写。</p><p><a href="https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail" target="_blank" rel="noopener">官方评分标准</a> · <a href="#writing-workbench">把需要修改的片段带到写作工作台</a></p>'
        elif skill=='speaking':reference='<p>回听时选一处停顿、一处重复表达和一处不清楚的发音来改进。完成录音不代表达到某个分数。</p><p><a href="https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail" target="_blank" rel="noopener">官方评分标准</a></p>'
        panels.append(f'''<section id="test-{skill}" class="panel la-test-panel" hidden data-la-owner="tests" data-la-title="{m['label']}整科测试"><header class="la-heading"><a href="#tests">← 全部测试</a><h1>{m['label']}整科测试</h1><p>{m['scope']}</p><p>{m['note']}</p></header><div class="la-test-controls"><output class="la-test-clock" data-test-clock>尚未开始</output><button type="button" data-test-start="{skill}" class="la-primary">开始本次测试</button><button type="button" data-test-submit="{skill}" hidden>提交本次作答</button><button type="button" data-test-retry="{skill}" hidden>再做一轮</button><div data-test-progress></div></div><div class="la-test-body" hidden>{body}</div><section class="la-test-result" hidden></section><div data-test-reference hidden>{reference}</div><details data-test-history><summary>以往作答</summary></details></section>''')
    (STAGE/'complete-tests.html').write_text('\n'.join(panels),encoding='utf8')
    (STAGE/'complete-tests-data.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2),encoding='utf8')
    return tests

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf8')
    build();print('Complete question sets staged; 40 reading keys and 40 verified listening keys; no automatic Band conversion.')
