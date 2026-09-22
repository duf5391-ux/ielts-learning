# 首轮入口候选审查（非发布候选）

冻结副本：`navigation-initial-candidate.html`，SHA-256 `7df8bf478f5605192504d15863fed289daf4a063c4557dff86ba4b8a5eeb7605`。仅前端与入口组合，写作改版尚未合入。独立 context，桌面 1440×1000／手机 390×844，三个合成收藏词。

## 确定需修

**NAV-01 / P2，全局搜索跨分类返回丢失来源结果。**

学习 → 搜索「成人读写困难」→ 唯一结果直接进入对应 Task 2 → 页内返回。

实际回 `#practice-writing2-list` 的 20 项，学习搜索词虽保留但学习结果页不在眼前。期望回到刚使用的学习搜索结果与原位置，同时保持题目实际归属为练习。桌面和手机均复现。截图 `nav-initial-desktop-search-return.png`／`nav-initial-mobile-search-return.png`，详细动作在对应 JSON。

## 已检查通过

- 桌面 8 个主导航逐项点击；手机 4 个底栏直达，以及更多里的练习／测试／写作工作台／工作台全部实际进入。稳态抽屉截图 `nav-initial-mobile-more-stable.png`。
- 手机三条单词完整显示：行范围 296–422、422–548、548–675；底栏从 790px 开始。三行均可标记，标记刷新保留。截图 `nav-initial-mobile-vocabulary-review.png`。
- 复习在独立 `#word-review` 面板开始：标记第一词 → 转第二词 → 暂停 → 刷新，剩余到期词从 3 变 2。没有把直接自评当作完成复习。
- 手机每日 dock 底 780px、底栏顶 790px，不相交；休息、继续、收工都能点击并正确改变会话状态。截图 `nav-initial-mobile-daily-start.png`／`nav-initial-mobile-daily-rest.png`。
- JQ-01：练习阅读的同分类筛选+搜索返回保留，仍为 1 条。`nav-initial-targeted.json`。
- JQ-02：个人资料自动制课误导主标题已移除。
- 各主面板无横向溢出，以上操作无页面脚本错误。

JQ-03 归顶由 root 正在修，未在这份旧冻结稿上重复全量判断。首轮截图中的复习顶栏偶现「学习」没有在延长等待的独立重试中稳定复现，因此未列为确定缺陷。首张 more 截图是抽屉动画中途，使用 `more-stable` 作为验收图。

下一步应在包含 writing 的最终组合候选回归导航来源、归顶与返回位置，以及原每日／独立测试／个人资料保存链路；当前结果不能作为完整发布通过。
