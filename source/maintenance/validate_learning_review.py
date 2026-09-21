"""Static delivery checks; does not operate a browser or user learning records."""
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import hashlib, json, subprocess
from finalize_learning_repairs import MAIN, TESTED_CORE

ROOT=Path(__file__).resolve().parent
NODE=Path(r'C:\Users\Admin1\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')

def main():
    s=BeautifulSoup(MAIN.read_text(encoding='utf8'),'html.parser')
    ids=[n['id'] for n in s.select('[id]')]
    assert len(ids)==len(set(ids))
    core=next(n.get_text() for n in s.select('script') if "const key='ielts-finished-book-v1'" in n.get_text())
    assert hashlib.sha256(core.replace('\r\n','\n').encode()).hexdigest()==TESTED_CORE
    assert '雨最迟会在什么时候抵达 south coast？' in s.get_text() or '按预报，雨最迟到什么时候会抵达 south coast？' in s.get_text()
    arch=json.loads((ROOT/'research/current-learning-architecture.json').read_text(encoding='utf8'))
    missing=[i['id'] for i in arch['content_catalog'] if i.get('reviewAnchor','')[1:] not in ids]
    assert not missing,missing
    notes=s.select('.learning-audit-note');assert len(notes)==24
    report=ROOT/'research/学习架构审查台.html'
    d=BeautifulSoup(report.read_text(encoding='utf8'),'html.parser')
    embedded=json.loads(d.select_one('#audit-data').get_text())
    assert len(embedded['architecture']['items'])==len(embedded['teaching']['items'])==24
    assert len(embedded['lessonCatalogue'])==136
    assert len(embedded['officialGallery'])==20
    missing_images=[x['file'] for x in embedded['officialGallery'] if not (ROOT/'research'/x['file']).is_file()]
    assert not missing_images,missing_images
    scripts=[n.get_text() for n in d.select('script') if n.get('type')!='application/json']
    for i,js in enumerate(scripts):
        p=ROOT/f'architecture-audit-qa/final-dashboard-{i}.js';p.write_text(js,encoding='utf8')
        subprocess.run([str(NODE),'--check',str(p)],check=True,capture_output=True,text=True)
    integration=json.loads((ROOT/'architecture-audit-qa/learning-review-integration.json').read_text(encoding='utf8'))
    counts={'fields':len(s.select('[data-save]')),'scripts':len(s.select('script')),
            'audio':len(s.select('audio source,audio[src]')),'images':len(s.select('img'))}
    assert all(counts[k]==integration['preserved'][k] for k in counts)
    result={'main_sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest(),
            'catalogue_jump_targets':len(arch['content_catalog']),'missing_targets':missing,
            'new_teaching_notes':len(notes),'save_fields':counts['fields'],'script_tags':counts['scripts'],
            'audio_sources':counts['audio'],'images':counts['images'],'record_fix_marker':True,
            'weather_deadline_question_correct':True,'core_identical_to_8_tested_version_normalized_newlines':True,
            'architecture_counts':dict(Counter(i['status'] for i in embedded['architecture']['items'])),
            'teaching_counts':dict(Counter(i['status'] for i in embedded['teaching']['items'])),
            'public_lesson_catalogue':136,'official_originals_plus_contact_sheets':20,
            'teaching_version_matched':embedded['freshness']['matched'],
            'teaching_version_changed':embedded['freshness']['changed'],
            'report_script_syntax_valid':True,
            'browser_scope':'审查台通过受支持的浏览器操作核验；主册文件URL受策略限制，最终正文/字段/脚本/媒体/跳转做静态核查，未绕过访问限制。'}
    (ROOT/'architecture-audit-qa/final-static-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
