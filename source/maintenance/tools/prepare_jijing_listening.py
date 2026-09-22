import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.codex-tools/jijing-libs'))
from bs4 import BeautifulSoup

batch = ROOT / 'content-pipeline/batches/jijing-20260920'
raw = ROOT / 'downloads/jijing-20260920/ieltsa/raw/listening--2026-sep-hf-1.html'
soup = BeautifulSoup(raw.read_text(encoding='utf-8'), 'html.parser')
transcript = soup.select('details')[0].get_text('\n', strip=True)
transcript = transcript[transcript.index('PART 1'):transcript.index('PART 2')].strip()
keys = []
for i, li in enumerate(soup.select('details')[-1].select('ol > li')[:10], 1):
    keys.append(dict(id='q'+str(i), answer=li.select_one('span').get_text(' ',strip=True), explanation=li.select('p')[-1].get_text(' ',strip=True)))
prompts = [
    'Duties include: some responsibility for _________ from sales during the flight.',
    'Requirements: must be over age 19 and at least _________ cm tall.',
    'Requirements: basic academic requirements: English and _________.',
    'Requirements: at least one other _________ is desirable.',
    'Requirements: must be able to _________.',
    'Training will include: what to do in case of _________ during a flight.',
    'Training will include: awareness of different _________.',
    'Application: The airline is called _________.',
    'Application: mention experience of working in a _________ (voluntary work).',
    "Other information: You don't have to buy a _________.",
]
close = '''<h3>这段对话说了什么</h3><p>Ellie想申请空乘工作，向老同学Greg了解真实职责、申请条件和培训。她还没有坐过飞机，但这不影响她询问工作。对话后半段转向她已有的超市服务与志愿经历，最后确认这家航空公司提供制服。</p><h3>三组容易混淆的信息</h3><ul><li>空乘最低身高是168厘米；Ellie说自己169厘米。前者是岗位门槛，后者是个人情况。</li><li>另一门语言是优势，原文用an advantage和not essential限定；游泳则被称为another requirement。可取条件和必需条件不同。</li><li>“很多公司让你自己买制服”是一般情况，but之后才是Greg所在公司的安排：公司提供制服。</li></ul><h3>值得带走的词块</h3><ul><li><strong>be responsible for / deal with</strong>：前者强调负责，后者强调处理事务。这段中二者共同指向售卖商品后的钱款管理。</li><li><strong>apply to an airline / apply for a job</strong>：to后接申请的机构，for后接职位；同样的申请动作，介词随对象变化。</li><li><strong>count on a doctor being on board</strong>：count on表示指望、依赖；being on board说明医生恰好在飞机上，这种条件不能保证。</li><li><strong>the implications of that</strong>：不同文化带来的实际影响，而不只是记住文化名称。</li><li><strong>as part of a team</strong>：作为团队成员。Greg强调的价值是working with others，即合作经验。</li></ul><h3>读懂长句与指代</h3><p>“You'd be responsible for that”中的that回指前面的钱款处理；后面“they provide it for you”中的it回指制服，不是表格或培训。</p><p>培训内容里的“what action to take if a passenger suddenly has some sort of illness while you're in the air”可以分成三层：要采取什么行动（what action to take），在什么条件下（if乘客生病），发生在什么时候（while飞行途中）。整句重点是应急处置，不是要求空乘当医生。</p><p>“although for cabin crew it's not essential”让步说明会第二语言有好处但不是必需。把这一句与前面的an advantage连起来读，才能保留说话人的条件限制。</p><h3>回到原音</h3><p>核对后可重听介绍岗位条件到制服安排这一段，留意Greg怎样用right、of course和but确认、补充或限制Ellie的理解。原文就在下方，可边听边回读。</p>'''
unit = dict(id='pr-jijing-202609-listening-01-v1',title='空乘岗位咨询 · 9月机经 Part 1',skill='listening',part='Part 1',sourceUrl='https://ieltsactualtests.com/zh/listening/2026-sep-hf-1',sourceNature='考生回忆重建；配套为站方重录音频',minutes=18,instructions='Complete the notes below. Write ONE WORD AND/OR A NUMBER for each answer. 从音频开头听起，完成第1–10题；听到Part 2后暂停。',contextParagraphs=['Ellie向老同学询问空乘工作。笔记中已给出的其他信息：职责包括安全演示和提供食物；申请表可在公司网站下载；经历栏还包括在超市处理顾客询问。'],questions=[dict(id='q'+str(i),prompt=p) for i,p in enumerate(prompts,1)],answers=keys,transcript=transcript,closeReadingHtml=close,audio='ieltsa/assets/494b5ff8b614-2026-sep-hf-1.mp3',archive='ieltsa/pages/listening--2026-sep-hf-1.html')
(batch / 'listening-unit.json').write_text(json.dumps(unit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared',len(keys),'questions; transcript characters',len(transcript))
