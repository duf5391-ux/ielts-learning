"""Build an independent writing workspace from the existing, sourced practice bank."""
from pathlib import Path
from html import escape
import json

HERE = Path(__file__).resolve().parent
e = lambda s: escape(str(s), quote=True)

GUIDANCE = {
    'jobs': {
        'focus': '选出主要变化，再用成组比较支持概览',
        'plan': ['图表范围、单位与时间：我在比较什么？', 'Overview：两条最重要的总体变化是什么？', '细节组 A：哪些趋势适合放在一起？写出数据证据。', '细节组 B：相同终点、不同增量，怎样比较？'],
        'teach': '先分清净变化与中途峰值：制造业从 15 到 13 million，净减少 2 million；不能把 1980 年峰值 20 到终点 13 的差当作全期净变化。零售和医疗都在 16 million 结束，但分别从 6 与 2 起步。概览突出主导行业改变与农业整体下降，细节段再用数字支持。',
        'example': 'Retail and healthcare both employed sixteen million people in 2020, although healthcare had started from a much lower base.',
        'why': '这句把共同终点与不同起点放在同一个比较里。它不能替代整篇概览，也不解释图中未给出的社会原因。',
        'micro': '用两句写 overview：一条写最大行业的变化，一条写农业的整体走势。先不列逐年数字。',
        'answer': 'Manufacturing was the largest employer at the beginning, but retail and healthcare had both overtaken it by 2020. Agricultural employment declined overall and was the lowest at the end of the period.',
        'transfer': '换到砖块流程图，只写两句总览；检查你能否根据图的类型改变概览方式。',
        'next': 'ww-bricks',
    },
    'bricks': {
        'focus': '区分顺序与分支，准确描述工序',
        'plan': ['起点、终点与整体性质：原料怎样变成成品？', 'Overview：如何概括主要阶段，而不逐个抄标签？', '前半程：两种成形方式是什么关系？', '后半程：温度与时长分别属于哪一步？'],
        'teach': '先沿箭头走一遍：成形有 wire cutter 与 mould 两条路径，随后都进入干燥，并非每块砖先切再压。温度属于两段 kiln，24–48 hours 属于干燥，48–72 hours 属于冷却。总览可以概括从取土到配送的工业过程，不必机械数出可能有歧义的步骤总数。',
        'example': 'The clay mixture is shaped into bricks either with a wire cutter or in moulds before being dried for 24 to 48 hours.',
        'why': 'either ... or ... 表达备选成形路径，before 表达共同后续步骤。被动语态把砖与原料放在信息中心，但不要求每一句都用被动。',
        'micro': '写两句，描述干燥之后、包装之前的流程。保留两段温度与冷却时间，不推算完整工期。',
        'answer': 'The dried bricks pass through a kiln at a moderate temperature of 200–980°C and then at a higher temperature of 870–1300°C. They are subsequently cooled in a chamber for 48–72 hours.',
        'transfer': '换到咖啡厅平面图，只写总览和两条位置变化；不要沿用制造过程的时间顺序。',
        'next': 'ww-cafe',
    },
    'cafe': {
        'focus': '用空间分组呈现变化，避免逐项罗列',
        'plan': ['两张图的时间关系与场所用途是什么？', 'Overview：最显著的整体布局变化有哪些？', '细节组 A：选一个区域，记录新增、移除或搬迁的设施。', '细节组 B：另一地区怎样变化？哪些设施保持原位？'],
        'teach': '先在原图核对每个设施的旧位置和新位置，再选择按区域或按功能分段。只有旧设施消失、同处出现新设施，才使用 replaced by；设施仍在但改到别处，用 relocated 或 moved。图未给出方位标时，用 to the left of、near the entrance 等实际可见参照，不自行指定东西南北。',
        'example': 'The seating area has been relocated closer to the entrance.',
        'why': '这只是“设施搬迁”的表达示范，并非对本题图面的事实断言。写进作文前，必须核对图中是否真的同时显示搬迁与靠近入口。',
        'micro': '从原图找一处确定的改动，分别记录旧位置、新位置，再写一句比较；另写一句总览。',
        'answer': '核对标准：两个位置都有原图依据；变化动词与图相符；总览概括整体变化，不只重复某一个设施名称。本题没有唯一写法，返回原图逐项核对。',
        'transfer': '换到就业折线图，只写一条静态比较和一条动态变化，检查是否能正确切换表达。',
        'next': 'ww-jobs',
    },
    'primary': {
        'focus': '回应两个问题，并把游戏的价值写成因果链',
        'plan': ['题目有几个问题？分别要求我判断什么？', '我的完整立场：对 formal learning 的程度判断 + 游戏的重要性。', '主体段 A：一个理由 → 为什么成立 → 课堂例子。', '主体段 B：如何补足另一问？可接受的边界是什么？'],
        'teach': '“游戏有用”没有直接回答学校是否过分重视正式学习。先写清赞同程度，再解释游戏在课堂里承担什么功能。发展理由时，把抽象结果拆成可观察过程：儿童轮流参与游戏 → 必须倾听同伴并协商规则 → 有机会练习协作。例子应支持这个过程，不必编造调查比例。',
        'example': 'Structured games can complement formal lessons because children have to listen to one another and agree on rules. For example, a small-group shop game gives pupils a reason to practise numbers while taking turns as customers and sellers.',
        'why': '这是自编假设课堂例子：它连接活动、机制与学习结果，没有把“有趣”直接等同“有效”。完整文章仍需明确回答两问并维持立场。',
        'micro': '写 2–3 句立场与理由，同时回答两问；随后用一句说明什么情况下游戏不能替代直接讲授。',
        'answer': '一种可行方向：部分学校过度依赖正式训练；有结构的游戏对语言与合作练习重要，但新概念仍需要清楚讲授。核对你的句子是否明确包含程度、重要性和边界，而不只说 play is useful。',
        'transfer': '换到高层住宅题，先圈定 best，再用一句比较性立场回应；不要只说高层有优点。',
        'next': 'ww-housing',
    },
    'tourism': {
        'focus': '比较利弊的分量，说明为什么一方更重要',
        'plan': ['outweigh 要求什么判断？涉及哪些受影响对象？', '我的结论：哪一方更重？比较依据是什么？', '优势段：收益 → 作用机制 → 对谁有利？', '不利段与权衡：持续时间、影响范围或可缓解程度如何比较？'],
        'teach': '两边各列两个点不等于完成 outweigh。选择一条比较尺度，例如影响持续多久、影响谁、能否缓解，并在结论中解释为何这使一方更重。承认旅游创造收入后，可进一步问：收入是否留在当地、住房压力是否持续。政策例子是论证中的假设条件，不能当作题目已给出的事实。',
        'example': 'Tourism can support local shops, but this benefit may be seasonal. If homes are converted into holiday rentals throughout the year, residents may face a more persistent cost than the temporary jobs can offset.',
        'why': '这是自编假设情境。seasonal 与 persistent 提供同一比较尺度；if 和 may 保留条件，避免把所有旅游城市说成同一种情况。',
        'micro': '用 60–80 词写一个权衡段：承认一项收益，说明一项居民成本，再明确为何其中一项更重。',
        'answer': '自核：有一项明确收益、一项明确成本、一条共同比较尺度，以及权衡结论。若只写 However tourism also causes pollution，再罗列另一点，还需要补上为何更重。',
        'transfer': '换到小学课堂题，用同样的“条件—机制—结果”写一个游戏例子；这次必须回应两问。',
        'next': 'ww-primary',
    },
    'housing': {
        'focus': '辨清 best 的比较要求，补足条件与因果',
        'plan': ['题目核心判断是“有用”还是“最佳”？范围是什么？', '我的程度立场：在哪些条件下成立，哪些不成立？', '主体段 A：高层怎样增加供给？这一机制需要什么条件？', '主体段 B：另一办法或约束如何影响“最佳”的判断？'],
        'teach': '“一栋楼能容纳更多住户”支持用地效率，却不能单独证明所有城市都应建高层，也不能保证房价下降。先区分供给数量与可负担性，再比较土地、基础设施与成本等条件。选少量相关条件展开，比列出许多没有解释的城市问题更有用。',
        'example': 'Tall apartment blocks can accommodate more households on a limited site, which makes them useful in areas where land is scarce. However, this does not automatically make housing affordable, because construction and maintenance costs may still be high.',
        'why': '自编教学例句先说明机制，再限定推论。which 指向前句的空间效率；however 转向可负担性。文章还需解释这些条件如何影响最佳方案的判断。',
        'micro': '改写 Tall buildings contain more homes, so they are the best solution everywhere and will make housing affordable. 保留合理优点，删除无依据的绝对推论，补一个条件。',
        'answer': 'Tall apartment blocks can help cities provide more homes where land is scarce, although their affordability depends partly on construction costs and the type of housing supplied.',
        'transfer': '换到旅游题，写一句明确的利弊权衡，再为结论补一条比较依据。',
        'next': 'ww-tourism',
    },
}

def field(key, label, rows=3, extra=''):
    return f'<label class="ww-field"><span>{e(label)}</span><textarea data-save="{e(key)}" rows="{rows}" {extra}></textarea></label>'

def hidden(key):
    return f'<input type="hidden" data-save="{e(key)}"/>'

def source_link(u):
    s = u['source']
    path = s.get('path') or s['url']
    if s.get('page') and '#' not in path:
        path += '#page=' + str(s['page'])
    return f'<a href="{e(path)}" target="_blank" rel="noopener">{e(s["title"])}</a>'

def render_unit(u):
    short = u['id'].rsplit('-', 1)[1]
    uid = 'ww-' + short
    g = GUIDANCE[short]
    task1 = u['section'] == 'writing1'
    minutes, minimum = (20, 150) if task1 else (40, 250)
    criteria = [
        ('task', '任务完成 / 回应 · TA / TR', '概览是否概括主要特征？细节是否准确且覆盖关键比较？有没有写图中没有的原因？' if task1 else '所有问句是否回应？立场是否一直清楚？理由是否解释了为什么，并有相关例子或证据？'),
        ('coherence', '组织与衔接 · CC', '每段是否承担清楚的功能？句子之间关系是否真实？代词指向是否明确？不要只统计连接词。'),
        ('lexical', '词汇使用 · LR', '关键词含义、搭配与拼写是否准确？替换词是否保留原意？优先修正用错的词。'),
        ('grammar', '语法范围与准确性 · GRA', '时态、主谓、冠词与标点是否正确？复杂句是否表达需要的关系？检查一条复杂句与一条简单句。'),
    ]
    image = ''
    if u.get('image'):
        image = f'<figure class="ww-figure"><img loading="lazy" src="{e(u["image"]["src"])}" alt="{e(u["image"]["alt"])}"/></figure>'
    checks = ''
    for code, title, prompt in criteria:
        checks += f'<div class="ww-check"><h4>{e(title)}</h4><p>{e(prompt)}</p><label class="ww-field"><span>检查结果</span><select data-save="{uid}-check-{code}"><option value="unreviewed">尚未检查</option><option value="needs-work">发现问题，待修订</option><option value="checked">已核对并处理</option><option value="uncertain">仍不确定</option></select></label>'
        checks += field(uid + '-evidence-' + code, '证据：摘一句原文 → 问题 / 判断依据 → 怎样改', 3, 'class="ww-evidence"') + '</div>'
    next_options = [('task', '回应题目 / 概览'), ('coherence', '组织与展开'), ('lexical', '词汇与搭配'), ('grammar', '句子与语法'), ('transfer', '换题独立检查')]
    return f'''<article class="ww-unit" id="{uid}" data-ww-unit="{short}" data-ww-minutes="{minutes}" data-ww-minimum="{minimum}" hidden>
<header><span class="ww-badge">{e(u['part'])}</span><h2>{e(u['title'])}</h2><p>{e(g['focus'])}</p></header>
<nav class="ww-progress" aria-label="本题写作步骤">{''.join(f'<a href="#{uid}-{step}">{label}</a>' for step,label in [('plan','01 审题'),('draft','02 首稿'),('review','03 检查与修订'),('next','04 再练')])}</nav>
<section class="ww-step" id="{uid}-plan"><h3>01 / 审题与提纲</h3><div class="ww-prompt" lang="en">{e(u['prompt'])}</div>{image}
<p class="ww-muted">题意沿用现有练习文字；正式题面、图示与完整要求以原件为准。{source_link(u)}</p>
<div class="ww-backlinks"><a href="#{e(u['id'])}">打开原有局部练习与参考</a><a href="#{e(u['section'])}">回到本科学习</a></div>
<p class="ww-rule">{'用自己的话概括与比较图示，至少 150 词，建议约 20 分钟。' if task1 else '回应题目，用理由与例子支持立场，至少 250 词，建议约 40 分钟。'} 可直接开始首稿；提纲为可选准备。</p>
<div class="ww-grid">{''.join(field(uid + '-plan-' + str(i),label,3) for i,label in enumerate(g['plan'],1))}</div>
<details class="ww-help" data-ww-support="{uid}"><summary>需要提示：看一种审题与展开方法</summary><p>{e(g['teach'])}</p><blockquote lang="en">{e(g['example'])}</blockquote><p>{e(g['why'])}</p><p class="ww-muted">以上为本地教学示范，不是官方范文或评分。</p></details>
</section>
<section class="ww-step" id="{uid}-draft"><h3>02 / 留下自己的首稿</h3><div class="ww-conditions"><label><input type="checkbox" data-save="{uid}-seen-before"/> 以前写过这题 / 看过答案</label><label><input type="checkbox" data-save="{uid}-used-help"/> 本次参考过提示、词典或范例</label></div>
<div class="ww-toolbar"><output class="ww-timer" data-ww-clock="{uid}" aria-label="剩余时间">{minutes}:00</output><button type="button" data-ww-action="timer" class="ww-primary">开始 {minutes} 分钟</button><button type="button" data-ww-action="reset-timer">重置计时</button><span class="ww-muted">到时保留输入，刷新后继续计时。</span></div>
{hidden(uid + '-timer')}{hidden(uid + '-first-at')}{field(uid + '-first', '首稿 · 保留后锁定，修改在下方进行', 14, 'class="ww-essay" lang="en" spellcheck="true"')}
<div class="ww-toolbar"><output class="ww-wordcount" data-ww-count="{uid}-first"></output><button type="button" class="ww-primary" data-ww-action="freeze">保留首稿，开始修订</button><span class="ww-muted" data-ww-frozen="{uid}"></span></div>
</section>
<section class="ww-step" id="{uid}-review"><h3>03 / 四维检查与修订</h3><p>先找一个最影响表达的问题，摘出自己的句子，再修改。检查结果是你的判断，不会换算 band。</p><div class="ww-grid">{checks}</div>
{field(uid + '-revision', '修订稿 · 与首稿分开保存', 14, 'class="ww-essay" lang="en" spellcheck="true"')}
<div class="ww-toolbar"><output class="ww-wordcount" data-ww-count="{uid}-revision"></output><button type="button" data-ww-action="version">另存本次修订版本</button><button type="button" data-ww-action="export">导出本题作答与反馈请求</button></div>
{field(uid + '-reason', '这次最重要的修改：原来是什么、为什么改、现在怎样更清楚？', 3)}{hidden(uid + '-versions')}
<details class="ww-help"><summary>查看已保留的修订版本</summary><div class="ww-history" data-ww-history="{uid}"></div></details></section>
<section class="ww-step" id="{uid}-next"><h3>04 / 只练一个动作，再换题检查</h3><p>{e(g['micro'])}</p>{field(uid + '-micro', '我的局部练习', 5, 'lang="en"')}
<details class="ww-help" data-ww-support="{uid}"><summary>展开参考与核对方法</summary><p>{e(g['answer'])}</p><p class="ww-muted">参考为编写内容；有其他准确且满足要求的表达。</p></details>
<div class="ww-grid"><label class="ww-field"><span>下次优先处理</span><select data-save="{uid}-next-focus">{''.join(f'<option value="{value}">{label}</option>' for value,label in next_options)}</select></label><label class="ww-field"><span>计划复查日期</span><input type="date" data-save="{uid}-next-date"/></label></div>
<div class="ww-next" data-ww-next="{uid}"></div>{field(uid + '-next-note', '下一次具体做什么？到什么状态算完成？', 2)}
<p>{e(g['transfer'])} <a href="#{e(g['next'])}">打开下一题 →</a></p>
<p class="ww-muted">同题修订属于熟题练习；新题是否真的未见，请按自己的接触情况记录。</p></section></article>'''

def build():
    units = [u for u in json.loads((HERE / 'precise-writing-language.json').read_text(encoding='utf-8'))['units'] if u['section'].startswith('writing')]
    options = ''.join(f'<optgroup label="{label}">' + ''.join(f'<option value="ww-{e(u["id"].rsplit("-",1)[1])}">{e(u["part"])} · {e(u["title"])}</option>' for u in units if u['section'] == sec) + '</optgroup>' for sec, label in [('writing1','Academic Task 1'),('writing2','Task 2')])
    html = f'''<section class="panel workspace-panel" id="writing-workbench" hidden><header class="ww-heading"><p class="ww-kicker">WRITE · REVIEW · REWRITE</p><h1>写作工作台</h1><p>从一份首稿开始，找出一个具体问题，再写得更清楚。</p><p class="ww-muted">Task 1 与 Task 2 共用审题、写作、检查和修订流程。每道题的记录单独保留。</p></header>
<div class="ww-switcher"><label for="ww-task-picker">选一道题，或继续上次作答<select id="ww-task-picker" data-save="ww-active-task">{options}</select></label><a href="#records">学习记录与备份 →</a></div><p id="ww-resume" class="ww-muted"></p>
{''.join(render_unit(u) for u in units)}<p class="ww-notice" id="ww-notice" role="status" hidden></p>
<footer class="ww-footer"><p class="ww-muted">所有输入随本册「备份学习记录」保存；本题导出包含首稿、修订、检查证据与反馈请求。这里提供自检与修订工具，不自动评分。</p><details class="ww-help"><summary>考试要求与本区用法</summary><p>Academic Writing 共 60 分钟，两题都要完成。Task 1 至少 150 词、约 20 分钟；Task 2 至少 250 词、约 40 分钟。Task 2 对写作成绩的权重为 Task 1 的两倍。</p><p>这里的计时可暂停，用于练习。计数按英文单词、数字及常见缩写估算，不代表考试系统的精确计数。查看提示后请保留“参考过帮助”记录。</p><p><a href="https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-writing" target="_blank" rel="noopener">IELTS 官方考试要求</a> · <a href="https://ielts.org/cdn/ielts-guides/ielts-writing-band-descriptors.pdf" target="_blank" rel="noopener">官方四维评分描述</a></p></details></footer></section>'''
    (HERE / 'writing-workbench.html').write_text(html, encoding='utf-8')
    return units

if __name__ == '__main__':
    print('Built writing workbench:', len(build()), 'sourced tasks')
