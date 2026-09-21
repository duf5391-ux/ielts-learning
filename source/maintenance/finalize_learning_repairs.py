"""Restore the verified record protection and precise weather question after rebuilds."""
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib, json
from fix_record_reliability import apply, MAIN, HERE

OLD_Q='雨将在周六什么时段抵达 south coast？'
NEW_Q='按预报，雨最迟到什么时候会抵达 south coast？请写出星期及上午／下午。'
OLD_A='4＝下午。不要只记 Saturday 而漏掉时段。'
NEW_A='4＝截至周六下午／不晚于周六下午。原音说 by Saturday afternoon，说明最迟到达时间，没有给出精确抵达时刻；不能改述为只在周六下午抵达。'
TESTED_CORE='6fa9277c9b8069282fdf6b604c69b3db975ee1fde5fae406c7d77971957a4ffd'

def main():
    raw=MAIN.read_bytes();text=raw.decode('utf8')
    for old,new,accepted in [(OLD_Q,NEW_Q,'雨最迟会在什么时候抵达 south coast？'),
                             (OLD_A,NEW_A,'4＝最迟周六下午。原文 by Saturday afternoon 给出截止时间；不能据此断定恰好在下午抵达。')]:
        assert old in text or new in text or accepted in text, 'Weather text differs; inspect before editing'
    updated=apply(text).replace(OLD_Q,NEW_Q).replace(OLD_A,NEW_A)
    s=BeautifulSoup(updated,'html.parser')
    cores=[n.get_text() for n in s.select('script') if "const key='ielts-finished-book-v1'" in n.get_text()]
    assert len(cores)==1
    # HTML may be reserialized with Windows newlines; normalize only line endings.
    digest=hashlib.sha256(cores[0].replace('\r\n','\n').encode()).hexdigest()
    assert digest==TESTED_CORE,'Core differs from the version covered by eight tests'
    backup=HERE/'backups/开始学习-before-final-learning-repairs-20260919.html'
    if not backup.exists(): backup.write_bytes(raw)
    assert MAIN.read_bytes()==raw,'Concurrent update detected'
    tmp=MAIN.with_suffix('.final-repairs.tmp');tmp.write_text(updated,encoding='utf8',newline='');tmp.replace(MAIN)
    source_updates=[]
    for rel in ['skills-resources.json','build-skills-resources.py']:
        p=HERE/rel;original=p.read_text(encoding='utf8');new=original.replace(OLD_Q,NEW_Q).replace(OLD_A,NEW_A)
        if new!=original:
            assert p.read_text(encoding='utf8')==original
            p.write_text(new,encoding='utf8');source_updates.append(rel)
    result={'record_protection_reapplied_after_rebuild':True,'core_script_identical_to_8_tested_version':True,
            'core_sha256':digest,'core_hash_normalizes_line_endings':True,'weather_deadline_semantics_fixed':True,'source_updates':source_updates,
            'save_fields':len(s.select('[data-save]')),'scripts':len(s.select('script')),
            'audio':len(s.select('audio source,audio[src]')),'images':len(s.select('img')),
            'main_sha256':hashlib.sha256(updated.encode()).hexdigest(),
            'boundary':'主册末轮为静态检查；未绕过浏览器对该文件URL的访问限制。八项运行测试对应相同核心脚本。'}
    (HERE/'architecture-audit-qa/reliability-reapplied.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
