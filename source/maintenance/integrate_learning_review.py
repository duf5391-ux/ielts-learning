"""Attach versioned judgements; preserve lessons, records and other reviews."""
from pathlib import Path
import argparse
from collections import Counter
from datetime import datetime
from bs4 import BeautifulSoup
import hashlib, json
from review_snapshot_utils import item_fingerprints, find_node

ROOT = Path(__file__).resolve().parent
MAIN = Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
SNAPSHOT = ROOT / 'architecture-audit-qa/delivery-content-snapshot.html'

def sig(s):
    return {
        'fields': [n['data-save'] for n in s.select('[data-save]')],
        'scripts': [hashlib.sha256(n.get_text().encode()).hexdigest() for n in s.select('script')],
        'audio': [n.get('src') for n in s.select('audio source,audio[src]')],
        'images': [hashlib.sha256(n.get('src','').encode()).hexdigest() for n in s.select('img')],
        'other_reviews': [str(n) for n in s.select('[data-content-audit]')],
    }

def run(report_only=False):
    raw = MAIN.read_bytes()
    s = BeautifulSoup(raw.decode('utf-8'), 'html.parser')
    before = sig(s)
    for n in list(s.select('[data-learning-audit]')): n.decompose()
    snapshot = BeautifulSoup(SNAPSHOT.read_text(encoding='utf-8'), 'html.parser')
    data = json.loads((ROOT/'research/teaching-current-review.json').read_text(encoding='utf-8'))
    arch_path = ROOT/'research/current-learning-architecture.json'
    architecture = json.loads(arch_path.read_text(encoding='utf-8'))
    for item in architecture.get('content_catalog', []):
        target = find_node(s,item['selector'])
        if target is not None:
            located=target if target.get('id') else target.find_parent(id=True)
            if located: item['reviewAnchor'] = '#' + located['id']
    results = []
    for item in data['items']:
        old, now = item_fingerprints(snapshot, item), item_fingerprints(s, item)
        changes = sorted(k for k in set(old)|set(now) if old.get(k) != now.get(k))
        target = find_node(s,item['selector'])
        matches = not changes and target is not None
        results.append({'id':item['id'], 'matchesReviewedSnapshot':matches, 'changedSelectors':changes,
                        'snapshotFingerprints':old, 'currentFingerprints':now})
        if target is None: continue
        note = s.new_tag('details', attrs={'id':'learning-review-'+item['id'], 'class':'learning-audit-note',
                     'data-learning-audit':item['id'], 'data-verdict':item['status'] if matches else '待复核'})
        summary = s.new_tag('summary')
        summary.string = ('学习审查（09-19 快照）：'+item['status'] if matches else '学习审查：正文已更新，见复核与修复记录')
        note.append(summary)
        p=s.new_tag('p')
        p.string=('接入时，正文及直接关联材料与审查台所列固定版本一致；后续改动需重新核验。' if matches else
                  '以下是固定快照的判定。正文或关联材料在审查后已有变动，不能自动沿用该结论；已核实的修复另列。')
        note.append(p)
        for label,key in [('用途','scope'),('快照判定依据','why'),('改善方案','improvement'),('验收','acceptance'),('修复核验','repair_description')]:
            value=item.get(key)
            if value:
                p=s.new_tag('p');p.string=label+'：'+('；'.join(value) if isinstance(value,list) else str(value));note.append(p)
        a=s.new_tag('a',href='学习架构审查台.html#teaching',target='_blank',rel='noopener');a.string='查看完整证据、版本与教学抽查';note.append(a)
        if target.name=='details' and target.select_one(':scope > summary'): target.select_one(':scope > summary').insert_after(note)
        else:
            heading=target.find(['h1','h2','h3','h4'],recursive=False)
            if heading: heading.insert_after(note)
            else: target.insert(0,note)
    style=s.new_tag('style',attrs={'data-learning-audit':'style'})
    style.string='''.learning-audit-note{border:1px solid #b7cec6;border-radius:8px;padding:12px 16px;margin:12px 0;background:#f0f6f2;color:#243a33}.learning-audit-note>summary{font-size:14px;font-weight:600;cursor:pointer}.learning-audit-note p{font-size:14px;line-height:1.8;margin:9px 0}.learning-audit-note[data-verdict="不合格"]{border-left:4px solid #a55935}.learning-audit-note[data-verdict="合格"]{border-left:4px solid #367457}.learning-audit-note[data-verdict="待复核"]{border-left:4px solid #9d8529}.learning-audit-entry{border:1px solid #b7cec6;background:#f0f6f2;padding:18px;border-radius:10px;margin:0 0 24px}.learning-audit-entry p{font-size:14px;line-height:1.8}.learning-audit-entry a{font-weight:600}.learning-audit-note a{color:#28594b}'''
    s.head.append(style)
    counts=Counter(x['status'] for x in data['items']);matched=sum(x['matchesReviewedSnapshot'] for x in results)
    entry=s.new_tag('aside',attrs={'class':'learning-audit-entry','data-learning-audit':'entry'})
    for tag,text in [('strong','学习架构与产品调查 · 2026-09-19'),
                     ('p',f'固定快照复核24项架构与24项教学；教学为{counts["合格"]}项合格、{counts["不合格"]}项不合格，仅针对所标用途。接入时{matched}/24项正文及关联材料与受审版本一致；审后修复与变更另列。'),
                     ('p','含雅思课程、背词与模考产品的模块拆解、页面证据，以及逐项改善和验收方案。不同范围、不同轮次的审核分别保留。')]:
        n=s.new_tag(tag);n.string=text;entry.append(n)
    a=s.new_tag('a',href='学习架构审查台.html',target='_blank',rel='noopener');a.string='打开学习架构审查台 →';entry.append(a)
    s.select_one('#library').insert(0,entry)
    assert before==sig(s),'Learning fields, scripts, media or other reviews changed'
    ids=[n['id'] for n in s.select('[id]')];assert len(ids)==len(set(ids)),'Duplicate ids'
    updated=str(s)
    unchanged=MAIN.read_bytes()==raw
    version={'checkedAt':datetime.now().astimezone().isoformat(timespec='seconds'),'snapshot':str(SNAPSHOT),
             'snapshotSha256':hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
             'scope':'24项正文及直接关联材料的接入时比较；后续更新不自动获得相同判定',
             'matched':matched,'changed':24-matched,'items':results,
             'concurrentUpdateDuringCheck':not unchanged,'mainAnnotationsWritten':unchanged and not report_only}
    (ROOT/'research/review-version-check.json').write_text(json.dumps(version,ensure_ascii=False,indent=2),encoding='utf-8')
    arch_path.write_text(json.dumps(architecture,ensure_ascii=False,indent=2),encoding='utf-8')
    if not report_only:
        assert unchanged,'Concurrent content update detected; version comparison saved; workbook not overwritten'
        temp=MAIN.with_suffix('.learning-review.tmp');temp.write_text(updated,encoding='utf-8',newline='');temp.replace(MAIN)
    result={'main':str(MAIN),'teaching_annotations':len(data['items']),'matched_snapshot':matched,
            'pending_rereview':24-matched,'preserved':{k:len(v) for k,v in before.items()},'duplicate_ids':0,
            'sha256':hashlib.sha256(updated.encode()).hexdigest()}
    (ROOT/'architecture-audit-qa/learning-review-integration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report-only',action='store_true');run(parser.parse_args().report_only)
