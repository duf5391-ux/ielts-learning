"""Keep learner-facing pages about the material and the lesson, not provenance audits."""
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from collections import Counter
import re,json,shutil

HERE=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
MAIN=BOOK/'开始学习.html'

def clean_html(page):
    soup=BeautifulSoup(page,'html.parser'); changes=Counter()
    def drop(node):
        if node and node.parent:
            assert not node.select('[data-save]'),f'Cannot remove learner records: {node}'
            node.decompose();changes['removed_blocks']+=1
    def replace(node,text):
        if node and node.get_text()!=text:
            node.clear();node.append(text);changes['simplified_blocks']+=1
    def is_alive(node):return node.parent is not None

    # Per-word provenance records dominate the page but add no teaching content.
    for node in soup.select('.tv-source,.enrichment-origin,.lesson-notes-entry,.home-footnote'):
        drop(node)
    for summary in list(soup.select('details > summary')):
        if not is_alive(summary):continue
        text=summary.get_text(' ',strip=True)
        if text.startswith(('来源说明：','核查来源登记','本轮逐板块检查与修复结果','话题来源与核验说明','来源与整理说明')):
            drop(summary.parent)
        elif text in ['资源出处与原件','查看来源原件（可能含答案）']:
            replace(summary,'配套材料')
            # Keep usable documents and recordings by name, without repeated source notes.
            parent=summary.parent
            for node in list(parent.find_all('p',recursive=False)):
                if not node.find('a'):drop(node)

    for node in list(soup.select('.res-meta')):
        text=node.get_text(' ',strip=True)
        if node.parent and (node.find_parent(class_='res-track') or re.search('官方|核查|来源|原创|当季|本工作区|不背单词',text)):
            drop(node)
    for node in soup.select('.res-badge'):
        text=node.get_text(' ',strip=True)
        if text.startswith('2026-09-16') or text.startswith('新增｜'):replace(node,'新增')
        elif '回忆选题' in text:replace(node,'口语话题')
        elif text.startswith('新增资源 ·'):replace(node,'学习资源')

    # Each historical reading has a concise explanation of what the passage is about.
    notes=[
      'Their / the sisters 指 Gwendoline 和 Margaret Davies。这段叙述两人的成长、教育及文化活动；philanthropic 表示与慈善有关。',
      '这是一篇历史著作的书评开头，讨论糖的生产、贸易地位、补贴及影响。',
      '本段分析公共部门采用 AI 所需的条件：技术、数据管理、组织协作与人员能力。注意 typically 的限定作用。',
      '本段介绍一项保护项目及其在 2022 年的进展，涉及生态系统修复、生物多样性与跨组织合作。',
      '开头 It 指达累斯萨拉姆；DART 是文中讨论的快速公交系统。关注上车流程、无障碍设计与携婴出行。',
      '考古结合了发现、分析、想象、解释和遗产保护。注意作者如何组织并列概念。',
      'Johnson 指 Samuel Johnson。这段介绍词典编写者的工作与做法，可练习人物经历和大型任务的描述。',
      '本段解释澳大利亚的运动成绩，介绍教练、设施、培训机构及运动支持服务。',
      'temporal hours 把白昼或黑夜分别分成十二段，段长随季节变化。本段介绍两类古代计时工具及其使用限制。',
      'these monuments 指印度阶梯井。关注遗产修复、工程特点和游客活动的表达。',
      '本段回顾一种主要从身体和医疗理解健康的历史观点，后续段落继续扩展到生活环境与公共条件。',
      '这段把电影声音分成人声、音效和音乐。discussed below 指后文将展开的说明。'
    ]
    for index,content in enumerate(soup.select('.authentic-content')):
        paragraphs=content.find_all('p',recursive=False)
        if len(paragraphs)>=3 and index<len(notes):
            drop(paragraphs[0]);replace(paragraphs[1],notes[index]);drop(paragraphs[2])
    for node in soup.select('.authentic-links p'):
        if node.get_text(' ',strip=True)=='来源页面':drop(node)
    for node in soup.select('.authentic-links a'):
        text=node.get_text(' ',strip=True)
        if re.search('来源|官网|官方|公开页面',text):drop(node)
    for node in soup.select('.source-anchor .small'):
        links=node.find_all('a')
        if links:
            for a in links:a.extract()
            node.clear()
            for a in links:node.append(a)
        else:drop(node)
    for node in list(soup.select('.word-card small,.usage-card small')):
        if re.search('篇|语料|统计|词频|来源|核验',node.get_text()):drop(node)
    for node in soup.select('.word-top span'):
        if re.search('篇|册|覆盖',node.get_text()):drop(node)
    for node in soup.select('#vocabulary > .background-start'):
        # Keep its navigation; remove the methodology mini-essay.
        for child in list(node.find_all('p',recursive=False)):
            if not child.find('a'):drop(child)
    for node in soup.select('.tv-footnote'):replace(node,'收藏与熟悉度标记会自动保存；点击词典可查更多义项和发音。')
    for head in list(soup.select('main h2,main h3')):
        if head.get_text(' ',strip=True) not in ['来源与核验范围','原始来源与配对记录','近期主题来源和本题边界']:continue
        cursor=head.next_sibling
        while cursor is not None:
            nxt=cursor.next_sibling
            if getattr(cursor,'name',None) in ['h1','h2','h3']:break
            if getattr(cursor,'name',None):
                if cursor.select('[data-save]'):break
                drop(cursor)
            else:cursor.extract()
            cursor=nxt
        drop(head)

    exact={
      '材料有出处，反馈有依据。':'学习资料',
      '本册使用的原始参考与官方规则集中放在这里，可直接打开查阅。':'题目、音频、学习册和评分标准，可直接打开。',
      '随册原始参考':'配套文件',
      '本季题目与新增资源':'话题与学习资源',
      '本季话题与教学资源':'话题与教学资源',
      '本季优先话题 · 16 组教学资源':'口语话题 · 16 组教学',
      '本季口语':'口语话题',
      '先从 2026 年 9—12 月公开回忆主题进入语境与表达，再按缺口补基础背景。':'从口语话题学习语境与表达，也可选择基础背景。',
      '12 段原文，保留原句和来源。按需要阅读，词汇注释可展开；题材覆盖由原文决定。':'12 段阅读材料，附可展开的词汇注释。',
      '新增可学资源 · 4 单元':'专项练习 · 4 单元',
      '新增可学资源 · 2 单元':'专项练习 · 2 单元',
      '换一个日常语境 · 自编例句':'日常语境例句',
      '来自现有原文':'阅读例句',
      '对应原题':'相关练习',
      '原始参考':'配套材料',
      '完整词汇来源库':'完整词汇库',
      '词频与原文证据':'词频与阅读语境',
      '新增可学资源':'专项练习',
      '语境、教学和参考均可直接打开。听力使用配套原音；自编题与官方材料分别注明。':'语境、教学、练习与解析，可直接打开。',
      '这是词条参考，具体义项请结合当前句子判断。':'',
      '先读懂材料，再做题；可以直接学习，无需先做测试。':'先读材料，再按需要做练习。'
    }
    # Only learner-facing text nodes are changed, never JSON, saved data or code here.
    text_nodes=[x for x in soup.find_all(string=True) if isinstance(x,NavigableString) and x.find_parent(['main','aside','header','dialog','title']) and not x.find_parent(['script','style','textarea'])]
    for node in text_nodes:
        if not is_alive(node):continue
        old=str(node);text=old
        for a,b in exact.items():text=text.replace(a,b)
        text=re.sub(r'（[^（）]*(?:教学自编|例句自编|不是官方|非官方|非真题|原创教学|官方评分)[^（）]*）','',text)
        text=re.sub(r'\((?:original|author-created) teaching[^)]*\)','',text,flags=re.I)
        for a,b in [
            ('官方原题','练习题'),('官方样题','练习题'),('官方原音','听力音频'),('官方原声','听力音频'),
            ('官方课堂材料','课堂材料'),('官方材料','阅读材料'),('官方货运','货运'),('官方 Part','Part'),('官方 115010','115010'),
            ('完整原创示范','完整示范'),('完整原创回答','完整回答'),('原创 Task','Task'),('原创数据题面','数据题面'),
            ('原创短文','阅读短文'),('原创教学地图','地图'),('原创虚构数据','数据'),('原创教学题','练习题'),('原创练习','练习'),
            ('自编例句','例句'),('自编对照','对照'),('自编情境','情境'),('自编句','句子'),('自编题','练习题'),('自编的',''),
            ('自编新追问','新追问'),('自编活动情境','活动情境'),('自编迁移','迁移练习'),('本地原始文件：','评分标准：')]:text=text.replace(a,b)
        text=re.sub(r'本主题是自编背景导读，不是雅思原题。\s*','',text)
        text=re.sub(r'本主题为自编[^。]*。\s*','',text)
        text=re.sub(r'本地原文已逐字核对[^。]*。','',text)
        text=re.sub(r'；?(?:这些|这|本段|本文|本题)?不是 IELTS 原题(?:或完整作文)?。','。',text)
        text=re.sub(r'\s*· 原 PDF 第\s*\d+\s*页','',text)
        text=re.sub(r'：原 PDF 第\s*\d+\s*页','',text)
        if text!=old:node.replace_with(text);changes['text_changes']+=1

    # Administrative paragraphs, identified by their actual role rather than generic words
    # such as "source", which also occur in vocabulary definitions and reading explanations.
    admin_starts=(
       '依据截至 2026-09-16','本次新增教学内容','本轮新增资源与旧版PDF',
       '题面、中文讲解、词块例句','2026-09-16 核查','参考“不背单词”',
       '本地原文已逐字核对','所有场景与流程为原创','地名、人物与方案均为原创',
       'Bellford、项目与数据均为','本文观点与例子为原创','语境、示范与练习均为',
       'Kimi 本地资料列出','参考：Kimi 本地','下列词汇来源','词形与本地',
       '本卡明确结构在当前','表面形式见','表面结构见','合并模式见','排除 as a result',
       '见2篇，另一篇','本条中文义项','本卡入选','原题来自用户提供',
       '本轮新增资源与旧版PDF','本轮资源','已有 26 个补充学习单元',
       '本轮新增用法','本次新增用法',
       '8 个话题按当前学习需要编排','教学自编短文 ·','教学自编语境与搭配 ·',
       '补充资料中题名带','本卡暂不展示原句','本章尚未逐句试听',
       '本章已查看原题图','新录音同样仅完成','官方同组关系与音频原件',
       '本章尚未逐句','原样题片段的标题',
       'How to do IELTS','下面数据为工作区自编','来源核验中的一处不一致',
    )
    for node in list(soup.select('main p, main small')):
        if not is_alive(node) or node.find_parent(['script','style']):continue
        text=node.get_text(' ',strip=True)
        if text.startswith(admin_starts) and not node.select('[data-save]'):drop(node)
    # Specific mixed paragraphs retain the useful directions and shed authorship remarks.
    for node in list(soup.select('main p')):
        if not is_alive(node):continue
        text=node.get_text(' ',strip=True)
        if text.startswith('32 个教学单元 · 136 组用法。'):
            replace(node,'32 个教学单元 · 136 组用法，包含语境、示范、练习与解析。')
        elif text.startswith('detergent＝洗涤剂。'):replace(node,'detergent＝洗涤剂。')
        elif text.startswith('下表为虚构城市 Cedarford'):replace(node,'下表显示 Cedarford 成年居民主要通勤方式的比例，每年总计 100%。')
        elif text.startswith('下面两张为原创教学地图'):replace(node,'下面两张地图北在上，入口都在南边中央。每格表示相对位置，不代表面积比例。')
        elif text.startswith('可用开头：The maps show'):replace(node,'可用开头：The maps show how a small library changed between 2010 and 2025.')
        elif text.startswith('随册原始文件'):replace(node,'配套文件可直接打开。')
        elif text.startswith('已核查的本轮扩展资源'):replace(node,'此页用于添加你自己的学习资料。')
        elif text.startswith('这里会显示标题、正文和导入条数'):replace(node,'预览标题、正文和导入条数。')
        elif text.startswith('新库 Office party planning'):replace(node,'Office party planning 展示了同样的讨论方法：方案在预算内，仍可能有执行困难。食物选择也需要同时考虑费用和实际条件。')
        elif text.startswith('答案以') and '不冒充' in text:
            for child in list(node.contents):
                if getattr(child,'name',None)!='a':child.extract()
        elif text.startswith('以下均为工作区自编表达'):replace(node,'原稿中的取件问答使用 picked up from；下面练习两个常用句子。')
        elif text.startswith('先保留') and '英文教学例句是工作区自编' in text:replace(node,'先保留自己的首答，再看例句和示范。')
        elif text.startswith('这是参考 IELTS 官方教师文章'):replace(node,'先缩短准备与讲话时间，练习把一件事说清楚，再逐步扩展到题卡中的其他要点。')
        elif text.startswith('这是官方公开 Part 2 示例录音'):replace(node,'这段 Part 2 示例录音回答重要物品题。听听考生怎样交代物品、经历和个人意义。')
        elif text.startswith('可打开 Meeting an old friend'):
            replace(node,'Meeting an old friend 中的两个人谈到搬家、工作和家庭近况。挑一个支撑近况的细节，再练习介绍自己的近况。')
        elif text.startswith('已对照') and '核验措辞' in text:replace(node,'本题既要讨论网络娱乐使实体场所不再重要的看法，也要讨论其仍有经济、文化价值的看法，并提出自己的判断。')
        elif text.startswith('样本有关影院收入用于公共设施'):replace(node,'样本有关影院收入用于公共设施的论述，可以用来练习：因果的中间环节是否解释清楚。')
    # Strip remaining authorship labels from headings/instructions, while leaving
    # actual vocabulary definitions (e.g. source, original, official) untouched.
    for node in list(soup.find_all(string=True)):
        if not is_alive(node) or not node.find_parent('main') or node.find_parent(['script','style','textarea']):continue
        if node.find_parent(class_=['tv-card','res-usage','word-card','usage-card']):continue
        old=str(node);text=old
        text=re.sub(r'（[^（）]*(?:自编|原创|官方)[^（）]*）','',text)
        text=re.sub(r'教学自编，不是完整范文','局部示范',text)
        text=re.sub(r'教学可接受短示范，非官方唯一范文','短示范',text)
        text=re.sub(r'教学产出参考[^：]*：','表达参考：',text)
        text=re.sub(r'英语人名为原创虚构示例；','',text)
        text=re.sub(r'这里是虚构教学情境，不是运动计划或官方范文。','',text)
        text=re.sub(r'带评分答卷保留来源报告分数，不由某一处相似错误推定你的分数。','',text)
        text=re.sub(r'下列数据为教学自编[^。]*。','',text)
        text=re.sub(r'以下表格数据为教学自编[^。]*。','',text)
        text=re.sub(r'本单元的[^。]*(?:原创|自编)[^。]*。','',text)
        text=re.sub(r'下面 4 题为本学习册自编，依据听力音频，非原课程题号。','完成下面四道听力理解题。',text)
        text=re.sub(r'答案均依据原课程文字稿核对，题目是本学习册自编。','',text)
        text=re.sub(r'这些都是工作区自编用法练习。','',text)
        text=re.sub(r'下面是自编教学任务，不是原卷问题，也没有答案分数。','完成下面的表达练习。',text)
        text=re.sub(r'教学自编(?:观点题)?，非 IELTS 原题：','练习：',text)
        text=re.sub(r'原创改编题（不是回忆原句）：','练习题：',text)
        text=text.replace('自编语境示范（非原音文字稿）','对话示范').replace('原创展开示范','展开示范').replace('原创小链条','理由展开').replace('原创情境题','情境练习')
        text=text.replace('自编短示范','短示范').replace('自编示范','示范').replace('自编示例','示例').replace('自编输出','输出练习').replace('自编开口任务','开口练习').replace('教学自编开口任务','开口练习').replace('自编新问','新问题').replace('自编追问','追问').replace('自编语义迁移','换情境练习').replace('官方','')
        text=text.replace('自编错误句','错误句').replace('自编错误','错误').replace('自编通知','通知').replace('自编预报','预报').replace('自编段落片段','段落片段').replace('自编信息表','信息表').replace('自编理解题','理解题').replace('本学习册自编匹配','人物匹配').replace('核查背景给detail','检查画面背景给 detail')
        text=text.replace('练习题来源','练习题').replace('来源稿件','文字稿')
        if text!=old:node.replace_with(text);changes['text_changes']+=1
        elif text.startswith('基线材料状态已修正：'):replace(node,'如果看过题目、原文或答案，请选另一份材料做初测。熟悉的材料可继续用于学习和复盘。')
        elif '不构成诊断或治疗建议' in text and '本段回顾' in text:replace(node,'本段回顾健康概念从身体与医疗扩展到生活环境的过程。')
    # Brief labels for source document links; the file itself is still available.
    for node in soup.select('details.enrichment-sources a,.res-body>details a'):
        text=node.get_text(' ',strip=True)
        for prefix in ['IELTS 官方 ','British Council 官方 ','British Council ','Cambridge English 官方 ','Cambridge 官方 ','官方 ']:text=text.replace(prefix,'')
        text=text.replace(' · 本地文件','').replace('来源页面','配套材料')
        replace(node,text)
    for node in soup.select('label'):
        if node.find(id=re.compile('material.*source')):
            node['hidden']=''

    # Provenance is kept in data for maintenance; the lookup/import UI displays just content.
    for script in soup.find_all('script'):
        if script.get('type')=='application/json':continue
        js=script.string or ''
        if not js:continue
        old=js
        js=js.replace(" · ${row.source || '来源待补充'}",'')
        js=js.replace("block.append(node('small', e.source || '工作区已有注释')); result.append(block);","result.append(block);")
        js=js.replace("result.append(node('p', '这是词条参考，具体义项请结合当前句子判断。', 'lookup-muted'));",'')
        js=js.replace('在线词义参考 · MyMemory（机器翻译，非当前句子的人工注释）','中文释义')
        js=js.replace('`${cached.source} · 上次查询缓存`',"'上次查询'")
        js=js.replace("+' · 来源：'+(item.source||'尚未注明')",'')
        js=js.replace("+' · '+(item.source||'来源未注明')",'')
        js=js.replace(",text('p','这是自行添加的资料，内容与来源标签未经工作区核验；未计入原有词频统计。','material-read-note')",'')
        js=js.replace('本季题目与新增资源','话题与学习资源')
        if old!=js:script.string=js;changes['scripts_simplified']+=1
    # Preserve every saved input and lesson ID across a text-only cleanup.
    return str(soup),dict(changes)

def main():
    original=MAIN.read_text(encoding='utf8');before=BeautifulSoup(original,'html.parser')
    backup=HERE/'backups'/'开始学习-before-copy-cleanup.html';backup.parent.mkdir(exist_ok=True)
    if not backup.exists():shutil.copy2(MAIN,backup)
    html,stats=clean_html(original);after=BeautifulSoup(html,'html.parser')
    fields=lambda s:sorted(x['data-save'] for x in s.select('[data-save]'))
    assert fields(before)==fields(after),'Saved fields changed'
    assert len(before.select('.res-unit'))==len(after.select('.res-unit'))
    assert len(before.select('audio'))==len(after.select('audio'))
    MAIN.write_text(html,encoding='utf8')
    (HERE/'cleanup-result.json').write_text(json.dumps({**stats,'saved_fields':len(fields(after)),'lesson_units':len(after.select('.res-unit')),'audio_elements':len(after.select('audio'))},ensure_ascii=False,indent=2),encoding='utf8')
    print(stats)
if __name__=='__main__':main()
