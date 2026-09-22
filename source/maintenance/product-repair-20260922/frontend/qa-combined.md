# 组合候选可靠性验收

冻结源：`combined-frozen-8650db.html`，SHA-256 `8650db419b3ce44f821cc3444152a05afe668bca939d6dfb91c99aa2d402c075`，4091 保存字段。来自主任务已生成的 `product-repair-20260922/candidate.html`，本次没有修改产品文件。

执行 `node product-repair-20260922/frontend/qa-combined.cjs`，13 项通过，0 个页面脚本异常。具体结果见 `qa-combined.json`，其中 `candidate_sha256` 绑定冻结输入。此前可靠性基线的 `qa.json`、`qa.cjs` 和截图未覆盖。

原 11 项已适配组合导航：词表次要详情手动展开后核对来源及取消收藏；新旧句子和来源返回、保存失败保留草稿、真实首答进度及刷新、逐题录音版本与下载、权限/存储失败均通过。

新增组合检查：

- 独立 `word-review` 显示复习而隐藏词表；注入保存失败不推进当前词，恢复保存后同一词可完成并返回单词页，只计一次真实复习。
- 390px 启动每日安排后进入新口语材料，在浏览器合成麦克风正在录音时点击健康“收工”，保留当前学习状态并明确拒绝收工；麦克风结束、录音第 3 版存入 IndexedDB 后，收工成功；刷新后每日仍为 ended，3 版录音仍在，调用播放器播放成功。

每日安排与当前口语材料不同，进入材料时每日自动暂停；验收确认“收工被拒后状态保持”，不把系统已暂停误报为应当继续运行。初次检查夹具中的 active-only 断言已修正，历史失败保留在 `qa-combined-failure.json`。

关键截图：`combined-mobile-recording-finish-blocked.png`（录音中收工提示、健康栏与底部导航），`combined-mobile-finished-recording-restored.png`（收工刷新后录音恢复）。`combined-synthetic-recording.webm` 为本次合成下载证据，4272 字节。

本轮是隔离 Edge 浏览器和合成麦克风验收，没有真机麦克风或网络可达性结论。若后续仅变更写作目录视觉且不触及这些组件，无需重复本轮全套；最终发布仍需主任务确认组合指纹与线上版本。
