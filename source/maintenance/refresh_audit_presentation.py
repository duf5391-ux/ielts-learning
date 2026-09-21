"""Keep the presentation explicit about snapshot and implementation boundaries."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    p=ROOT/'build_learning_audit.py';text=p.read_text(encoding='utf8')
    swaps=[
      ('<main>\n<section','<main>\n<div id="version-notice" class="notice warn"></div>\n<section'),
      ('教学卡片显示「发现时判定」，修复进展另列；不把历史不合格数量当作当前未修数量。本页独立于旧 147 项综合审查（含来源要求）；抽查边界以具体报告为准。',
       '教学卡片显示固定快照判定；正文后来有更新的单元单独提示，修复进展另列。未抽查内容不自动获得结论，也不把旧不合格数量当作当前未修数量。'),
      ('<strong>设计提案 · 尚未实施。</strong>本页展示的是建议架构与待验收流程，不能当成主学习册已具备的功能。已完成的可靠性修改在“证据与边界”单独列出。',
       '<strong>设计提案 · 逐项看进展。</strong>六入口和复习决策仍是提案；补充题目入口、局部写作反馈已有部分落地，见各动作的快照进展。可靠性修复另列，不把方案当成已实现功能。'),
      ('旧 147 项综合审查（含来源要求）、当前教学审核与学习架构审核是不同尺度；目录总量不作为质量评分。',
       '147条标题是历史目录基线，不覆盖后续新增的所有内容。不同范围的内容审核与学习架构审核分别保留，目录总量不作为质量评分。'),
      ('改善方案 · 尚未实施','后续改善 / 保留方式'),
      ("cat.length+' 条内容标题 · 目录口径'","cat.length+' 条历史标题 · 不含后续全部新增内容'"),
      ("'发现时需改善'","'该快照需改善'"),
      ("发现时判断的用途：","快照审查用途："),
      ("function teachingCard(x){const fixed=x.repair_status==='本轮已修复';return", "function teachingCard(x){const fixed=x.repair_status==='本轮已修复',changed=(D.freshness?.items||[]).find(v=>v.id===x.id)?.matchesReviewedSnapshot===false;return"),
      ("(fixed?'<div class=\"notice\">'+esc(x.repair_description||x.repair_status)+'</div>':'')", "(changed?'<div class=\"notice warn\">此条正文或关联材料在审后已更新；下方保留受审版本结论，修复核验另列。</div>':'')+(x.repair_description?'<div class=\"notice\">'+esc(x.repair_description)+'</div>':'')"),
      ("snapshotCheckUnused:'unused'", "snapshotCheckUnused:'unused'"),
      ("const labels={'implementation_boundary'", "const labels={'snapshot_update':'最终快照更新','snapshot_progress':'快照进展','componentAssessment':'按子部分分别判断','previousJudgmentAssessment':'旧判定复核说明','previousJudgmentOutdated':'旧判定是否过期','review_boundary':'版本与审查边界','snapshotSha256':'受审快照校验','implementation_boundary'"),
      ("tree({测试:D.reliability,修改记录:D.reliabilityPatch})", "tree({测试:D.reliability,修改记录:D.reliabilityPatch,重建后核验:D.reliabilityReapplied})"),
      ("[('reliability', 'reliability-tests.json'), ('reliabilityPatch', 'reliability-patch.json')]", "[('reliability', 'reliability-tests.json'), ('reliabilityPatch', 'reliability-patch.json'), ('reliabilityReapplied', 'reliability-reapplied.json')]"),
    ]
    for old,new in swaps:
        if old==new: continue
        if old in text: text=text.replace(old,new)
        elif new not in text: raise AssertionError('Expected presentation text missing: '+old[:80])
    js="""const F=D.freshness||{};$('version-notice').textContent='版本范围：复核基于 2026-09-19 固定内容快照（'+String(F.snapshotSha256||'').slice(0,12)+'）。接入时 '+(F.matched??'待核对')+'/24 项教学正文及关联材料仍一致，'+(F.changed??'待核对')+' 项有审后更新；有更新的条目不自动沿用旧判定。最后比较：'+(F.checkedAt||'未提供')+'。';
"""
    if js not in text:
        marker="const items=A.items||[]"
        assert marker in text;text=text.replace(marker,js+marker,1)
    p.write_text(text,encoding='utf8')
    p=ROOT/'publish_learning_audit.py';text=p.read_text(encoding='utf8')
    text=text.replace("'reliability-tests.json','reliability-patch.json',", "'reliability-tests.json','reliability-patch.json','reliability-reapplied.json',") if "'reliability-reapplied.json'" not in text else text
    p.write_text(text,encoding='utf8')

if __name__=='__main__': main()
