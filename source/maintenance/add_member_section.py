"""Add the deeper member-area research to the existing local audit."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent

SECTION='''<section class="panel" id="members" hidden><div class="hero"><div class="eyebrow">Member areas · 07</div><h1>进入之后，到底怎么学</h1><p class="lead">免费内部体验、会员操作手册、公开批改样本和官方界面逐项拆开；把课程内容、用户路径、反馈和权限说具体。</p></div><div class="notice" id="member-stats"></div><div class="notice warn">Road to IELTS 的部分免费练习由本次实际完成；其他产品按官方资料还原。个人记录、完整付费课与评分效果仍有核验边界。本节用中文注明证据类型，不将子报告的字母编码与旧调查混用。</div><div class="two-grid" id="member-findings"></div><div class="toolbar"><input id="member-search" type="search" aria-label="搜索会员区内容" placeholder="搜索产品、单课、报告字段、会员权限…"><select id="member-category" aria-label="会员区类别"><option value="">全部类别</option></select><button id="member-reset">清空筛选</button></div><div id="member-count" class="count" role="status"></div><div id="member-cards" class="cards"></div><details><summary>实际操作截图与官方内部页面样本</summary><div id="member-gallery" class="gallery"></div></details><h2>对学习设计的具体补充</h2><div class="notice warn">以下是设计提案，尚未作为新功能实现。本轮增加调查与设计依据，不重建学习册正文。</div><div id="member-design"></div><details><summary>研究范围与尚未验证的事项</summary><div id="member-limits"></div></details></section>
'''

SCRIPT='''
const M=D.members||{},memberProducts=M.products||[];
$('member-stats').textContent=M.counts?M.counts.products+' 个产品与版本 · '+M.counts.uniqueSourceUrls+' 个来源链接 · '+M.counts.liveWalkthroughProducts+' 项实际内部练习体验 · '+M.counts.galleryImages+' 张现场或官方内部图':'';
$('member-findings').innerHTML=(M.findings||[]).map(x=>'<article class="card"><h3>'+esc(x.title)+'</h3><p>'+esc(x.text)+'</p><details><summary>对应来源</summary>'+tree(x.sources||[],{},1,'sources')+'</details></article>').join('');
[...new Set(memberProducts.map(x=>x.category))].forEach(x=>$('member-category').add(new Option(x,x)));
function renderMembers(){const q=$('member-search').value,c=$('member-category').value,list=memberProducts.filter(x=>(!c||x.category===c)&&matches(x,q)).sort((a,b)=>(a.id==='road-live'?-1:0)-(b.id==='road-live'?-1:0));$('member-count').textContent='显示 '+list.length+' / '+memberProducts.length+' 个产品与版本';$('member-cards').innerHTML=list.map(p=>'<article class="card"><div class="card-top"><div><div class="card-id">'+esc(p.category)+'</div><h3>'+esc(p.name)+'</h3></div><span class="badge '+(p.id==='road-live'?'good':'warn')+'">'+(p.id==='road-live'?'含实际操作':'官方资料还原')+'</span></div><p>'+esc(p.coverage||p.depth||p.evidenceLevel||p.proofSummary)+'</p><details '+(q?'open':'')+'><summary>展开导航、单课、反馈、权限和证据</summary>'+tree(p,{...sourceMap(p),...sourceMap({sources:p.sourceIndex||[]})})+'</details><p class="meta">'+anchor('阅读独立报告',p.reportFile)+'</p></article>').join('')||'<div class="empty">没有匹配的内部流程。</div>'}
$('member-search').oninput=renderMembers;$('member-category').onchange=renderMembers;$('member-reset').onclick=()=>{$('member-search').value='';$('member-category').value='';renderMembers()};renderMembers();
$('member-gallery').innerHTML=(M.gallery||[]).map(x=>'<figure><a href="'+esc(linkURL(x.file))+'" target="_blank" rel="noopener"><img loading="lazy" src="'+esc(linkURL(x.file))+'" alt="'+esc(x.title)+'"></a><figcaption><strong>'+esc(x.title)+'</strong><div>'+esc(x.note||'')+'</div>'+(x.sourcePage?anchor('官方图片来源',x.sourcePage):'')+'</figcaption></figure>').join('');
$('member-design').innerHTML=tree(M.designUpdates||[]);$('member-limits').innerHTML=tree({研究方法:M.method,边界:M.limitations});
'''

def main():
    p=ROOT/'build_learning_audit.py';text=p.read_text(encoding='utf8')
    if 'id="members"' not in text:
        text=text.replace('<button data-panel="evidence">06　证据与边界</button>','<button data-panel="evidence">06　证据与边界</button><button data-panel="members">07　会员区补查</button>')
        text=text.replace('<footer class="footer">',SECTION+'<footer class="footer">')
        text=text.replace("const labels={", "const labels={'sourceIndex':'本产品来源索引','proofSummary':'验证方式','reportFile':'独立报告','coverage':'核验覆盖','dashboard':'内部首页','module_tree':'模块结构','lesson_content':'单课内容','content_samples':'实际内容样本','practice_feedback':'练习与反馈','progress_next':'记录与下一步','membership':'会员解锁与限制','concrete_paths':'具体用户路径','observed_in_account':'是否在本人账户操作','research_method':'研究方法','evidence_legend':'证据说明','evidenceType':'证据类型','classification':'事实或推断','cardContents':'单词卡内容','completeSession':'完整一次学习','errorBranches':'答错后的分支','reviewAndProgress':'复习与进度','demoTakeaways':'可采用的设计','visualEvidence':'界面证据','depth':'调查深度','investigation_priority':'采用优先级','identity':'产品范围','journey':'用户路径','facts':'具体功能事实','stage':'阶段','detail':'细节','verification':'验证方式','limitation':'限制','report_schema':'报告字段','unknowns':'未核实项','learning_takeaway':'学习设计启示','source_id':'来源编号','evidence_type':'证据类型','urls':'直接来源链接','maps_to':'对应学习入口','proposal':'设计建议（未实施）',",1)
    if 'function renderMembers()' not in text:
        marker='const inv=A.page_inventory||[],cat=A.content_catalog||[];'
        assert marker in text, 'Member script insertion point missing'
        text=text.replace(marker,SCRIPT+'\n'+marker,1)
    if "'member_followup':" not in text:
        text=text.replace('const labels={',"const labels={'member_followup':'会员区后续补查','member_research_update':'会员研究带来的设计补充',",1)
    assert text.count('function renderMembers()')==1
    p.write_text(text,encoding='utf8')

if __name__=='__main__': main()
