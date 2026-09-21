from pathlib import Path
from bs4 import BeautifulSoup
import hashlib,json
ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
p=BOOK/'词频与原文证据.html';raw=p.read_text(encoding='utf8')
backup=ROOT/'backups/词频与原文证据-before-deep-audit-20260919.html'
if not backup.exists():backup.write_text(raw,encoding='utf8')
s=BeautifulSoup(raw,'html.parser');before=[hashlib.sha256(x.get_text().encode()).hexdigest() for x in s.select('script')]
for n in s.select('[data-frequency-audit]'):n.decompose()
n=s.new_tag('aside',attrs={'data-frequency-audit':'scope','style':'margin:18px 0;padding:16px 20px;background:#f2f6ed;border:1px solid #ccd9c9;border-radius:8px;color:#294234;font-size:14px;line-height:1.8'})
n.append(BeautifulSoup('<strong>统计核验：达标；原件回查与高频外推：存疑</strong><p>本轮复算全部 8,774 条词形记录，计数一致。三个语料组分开计算：23篇阅读／8,879词，24篇听力／9,486词，27篇考试文本／22,670词。重复来源未当成独立考场样本。</p><p>这里的高频仅指所选样本。TF是出现次数，DF是出现篇数；数值来自清洗后的统计视图，不是考试出现概率，也不能直接推出高分写作或口语优先级。27篇考试组仍需补齐从此视图到原题PDF的直接映射。</p><a href="词条逐项审核.html">查看1000个话题词的逐项语言审核与样本证据 →</a>','html.parser'))
s.main.insert(0,n)
after=[hashlib.sha256(x.get_text().encode()).hexdigest() for x in s.select('script')];assert before==after
p.write_text(str(s),encoding='utf8')
(ROOT/'deep-audit-qa/frequency-scope.json').write_text(json.dumps({'scripts_and_count_data_preserved':True,'scope_added':True}),encoding='utf8')
print('Frequency scope added; counting data and scripts preserved.')
