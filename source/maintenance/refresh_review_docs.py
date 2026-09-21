from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    p=ROOT/'research/调查结论与使用建议.md';old=p.read_text(encoding='utf8')
    tail=old[old.index('## 哪些产品值得参考'):]
    tail=tail.replace('(local-learning-architecture.md)','(current-learning-architecture.md)').replace('(teaching-content-review.md)','(teaching-current-review.md)')
    intro='''# 学习架构审查与产品调查结论

核验日期：2026-09-19。主交付是 [学习架构审查台](学习架构审查台.html)：逐项判定、原文位置、问题、改善、验收、产品模块、课程目录和界面证据可查。

## 学习架构与教学

固定快照的24项架构审查：14项合格、10项不合格。另有24项具体教学抽查：17项合格、7项不合格。两组检查对象不同，不能换算为整册质量百分比。当前主册在并行更新；审查台显示接入时的逐项版本比较，有变动的条目不自动继承旧结论。

- 保留：核心五章的首答与修订分离、证据定位、可执行练习入口、旅游写作的局部反馈。多个阅读技巧课已补上具体材料，旧的“只有泛指、未交付材料”理由已撤销。
- 优先改善：入口选一个学习目标；各科最短路径与跳过条件；示范、带提示练习与真正未见题分开标识；复习队列的优先顺序与结束条件。
- 具体教学问题：四个听力样本的新增正式题缺本单元内的对应录音入口。原有British Council有声微课和新增材料的文字分析可保留，但不能把读稿分析记作听音理解。
- 两个口语导读可作为语言输入，作为独立口语训练仍缺录答、回听和修订；词库的主动表达路径仍需补齐。具体范围见每条卡片，不能把一个局部问题外推整章不合格。
- 教材来源与教学质量分别判断：原创微课可以合格，官方材料仍要核对题面、答案、配套输入和反馈。

六个学习入口、八项改善动作和30/45分钟路径作为设计提案交付。新版已经补入的材料与局部写作反馈单独标进展，不再重复列成尚未提供的内容。

天气题中“by Saturday afternoon”应是最迟周六下午，收尾核验时题干与解析已修正。记录保护在课程重建后重新应用；规范化换行后的核心代码与已通过8项运行测试的版本相同。主册最终集成做静态检查，浏览器文件访问限制未被绕过。

'''
    assert p.read_text(encoding='utf8')==old
    p.write_text(intro+tail,encoding='utf8')
    p=ROOT/'README.md';old=p.read_text(encoding='utf8')
    marker='页面文案约定：';assert marker in old
    tail=old[old.index(marker):]
    intro='''# IELTS 学习工作区

2026-09-19 学习架构与产品调查：入口为 [学习架构审查台](research/学习架构审查台.html)，短版导读见 [调查结论与使用建议](research/调查结论与使用建议.md)。固定内容快照的24项学习架构为14合格、10不合格；24项具体教学为17合格、7不合格。每项都有用途边界、原文、改善和验收；两种数量不代表整册合格率。主册若并行更新，报告按指纹提示审后变更，不能用旧判定覆盖新内容。

研究含7组雅思学习体系、8款词汇产品、4组模考产品（品牌有交叉，不合计为19款独立产品），以及分场景选型。保留136课公开课程目录、17张官方原图、3张对照拼图、3张现场截图和来源链接。官方Inspera阅读实际输入两题、切换Part并核对计数；BC/GEL注册与IOT登录后的深层流程未完成。目录、官方截图和宣传均不冒充完整账号实测。

新版已补入具体阅读题和局部写作反馈；仍需改善入口选路、示范与独立题的区分、听力配套录音、补充口语声音反馈、复习决策和词块主动表达。6入口／8动作的设计方案与已完成的局部改动分别标明。

可靠性修复使用 `fix_record_reliability.py`；`finalize_learning_repairs.py` 在重建后恢复并核验核心代码，同时核对天气题的截止时间含义。8项运行验证见 `architecture-audit-qa/reliability-tests.json`，重建后代码一致性见 `reliability-reapplied.json`。不读取或改写用户浏览器内的实际记录。主册最终文件URL受浏览器策略限制，只做静态集成核对。

当前复核数据是 `research/current-learning-architecture.json` 与 `research/teaching-current-review.json`；原 `local-learning-architecture` 和 `teaching-content-review` 文件保留为历史，不能作为新正文的结论。147条目录亦为历史定位基线，不覆盖后续全部新增内容。

重建后先运行 `finalize_learning_repairs.py`，再运行 `integrate_learning_review.py`，最后 `publish_learning_audit.py`。集成器保留现有正文、保存字段、脚本、媒体和其他审核，按受审快照比较正文及关联材料；检测到并行写入时拒绝覆盖并保留比较报告。不要从旧备份覆盖主册。报告及证据发布在学习册旁，使用相对链接；记录字段数量等末轮数据以 `architecture-audit-qa/final-static-validation.json` 为准。

'''
    assert p.read_text(encoding='utf8')==old
    p.write_text(intro+tail,encoding='utf8')

if __name__=='__main__': main()
