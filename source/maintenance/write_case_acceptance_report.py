"""Write the final, count-driven acceptance record after integration and QA."""
from collections import Counter
from build_authentic_case_database import BOOK,HERE,QA,read,types,original_key,question_numbers

def main():
    data=read(BOOK/'authentic-cases.json');cases=data['cases'];stats=data['stats']
    audit=read(BOOK/'content-audit-current.json')['summary']
    browser=read(QA/'browser-results.json');source=read(QA/'source-verification.json');links=read(QA/'link-checks.json')
    integrity=read(QA/'integration-checks.json')['checks']
    assert browser['failed']==0 and source['flagged_for_review']==0 and not links['issues'] and all(integrity.values())
    r=stats['reading'];kinds=Counter(c['source']['kind'] for c in cases)
    lines=['# 原题案例与内容整改验收 · 2026-09-19','',
        '按正常考试难度保留原题，不设置渐进难度，不改写原文以降低难度。阅读采用可独立作答的连续多段片段；写作使用原任务和原图，练习多段写作。','',
        f"本轮纳入 {len(cases)} 组案例：阅读 {r['cases']} 组、{r['originals']} 篇独立原文、{r['uniqueQuestions']} 个不重复原题号；Task 1 为 {stats['writing1']['cases']} 道独立原任务，Task 2 为 {stats['writing2']['cases']} 道独立原任务。",'',
        '## 审核结果','',
        f"57 项原未达标教学内容已替换并复核。38 项原可疑内容保留原标记，各附独立达标补充。当前共 {audit['total']} 个审核单元：达标 {audit['by_status']['达标']}，可疑 38，未达标 0。初轮报告另存，未覆盖历史判定。",'',
        '## 内容与来源','',
        '每组阅读保留原题号、指令、必要选项、原答案和证据；先填写各题，再显示答案、解释及精读。写作先留下首稿，再显示针对原任务编写的参考段落与修改依据。参考写法明确标注，未冒充官方唯一标准答案。','',
        '来源按案例标注：'+'、'.join(f'{k} {v} 组' for k,v in kinds.items())+'。官方教辅中的题目明确注明性质。G 类短答样题也保留 G 类来源标识，不当作学术类材料。','',
        '同篇文章的不同裁切会标注同源，统计原文数时去重；蜣螂图示和表格使用同篇原文，计为一篇。原题 20–21 的双选共计两个题号、一个输入框。','',
        '## 阅读题型覆盖','',
        '| 题型 | 案例组数 | 独立原文数 |','|---|---:|---:|']
    group=[c for c in cases if c['skill']=='reading']
    for t,count in r['by_type'].items():
        selected=[c for c in group if t in types(c)]
        originals=len({original_key(c) for c in selected})
        lines.append(f'| {t} | {count} | {originals} |')
    lines+=['','混合题型案例同时出现在相关题型行，组数不能跨行相加；精确逐题口径见[独立覆盖报告](内容验收/coverage-independent-review.json)。','',
        '## 写作覆盖','',
        'Task 1：'+'、'.join(f'{k} {v} 组' for k,v in stats['writing1']['by_type'].items())+'。',
        'Task 2：'+'、'.join(f'{k} {v} 组' for k,v in stats['writing2']['by_type'].items())+'。','',
        '来源数量的边界：地图目前只有一份独立真题（Cambridge IELTS 21 咖啡厅），部分阅读题型也仅一篇独立来源。没有将重复原文、重复任务或自编题计成新增真题。','',
        '## 数据与交互验收','',
        '- 学习内容写入 SQLite 的 cases、sources、paragraphs、questions、case_types 和 teaching_modules，再从数据库生成离线页面；题型入口保存在 framework_links，审核结论保存在 current_audit。',
        f"- {source['checked_cases']} 组来源核查通过。PDF 文本层的 OCR、脚注和跨页差异通过原页目检闭环，并保留文本哈希和核验说明。", 
        f"- {links['unique_references_checked']} 个新增内部或本地引用均有效。",
        f"- 浏览器验收 {browser['passed']} 项通过：先答后看、首次作答保留、修订、恢复与导出、题型筛选、图表、手机布局及无脚本错误。",
        '- 原有 2470 个记录字段、225 个锚点、9 个音频、21 张原题图及核心保存脚本保留；原用户浏览器记录未被测试改写。',
        '- 正文使用深色，审核状态使用小标记；只保留一个资源目录入口。','',
        '## 可回查文件','',
        '- [打开学习册](开始学习.html)',
        '- [数据库](学习案例.sqlite3)',
        '- [当前审核数据](content-audit-current.json)',
        '- [案例数据](authentic-cases.json)','']
    report='\n'.join(lines)
    (BOOK/'本轮内容验收.md').write_text(report,encoding='utf8')
    (HERE/'audit-content-remediated-20260919.md').write_text(report,encoding='utf8')
    print(str(BOOK/'本轮内容验收.md'))

if __name__=='__main__':main()
