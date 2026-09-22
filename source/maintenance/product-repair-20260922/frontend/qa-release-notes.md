# 发布包与线上轻量验收

共享脚本：`qa-release.cjs packed` / `qa-release.cjs https://duf5391-ux.github.io/ielts-learning/`。使用隔离浏览器记录，不读取用户数据，不修改产品。

本次正式源 `e2b9e12e58c8f03de4b43b8ec6bdb1b81a15130ddceb6b80ea5fff6a3d742075`，发布转换源 `0da42024b053a8da6c07caad7075c8c492f5ffa1269014c693127f1fc99bb4fe`，首页 `0bab2fa197699cb83087528a3769e4be81035420b70933eedcf56b1707a95336`。各报告绑定本地发布 manifest 和实际 HTTP 首页／渐进 manifest 的 SHA。

`qa-packed.json`：6 组轻量流程全部通过，0 个页面脚本异常。覆盖手机 5 个常用导航控制、更多 4 项、词卡检索和收藏刷新、学习全局搜索跨写作返回原结果、32 题目录到独居题首稿及刷新、学习／休息／继续／收工及刷新。学习栏和休息栏底部都为 780px，底导航顶部 790px，没有重叠。

首轮测试夹具曾误要求整张词卡完全落入 844px 首屏：实际卡片 top 544.16、height 358.19，词卡末尾次要内容超出屏幕。主任务确认应按“搜索及主要动作首屏可见”验收，因此修改测试断言，没有修改产品。

补充实测 `qa-packed-word-geometry.json`：词卡搜索框高度 44.09px；首条 curriculum 标题 top 623.16／bottom 654.20；收藏动作 top 563.16／bottom 607.16；均在底栏顶部 790px 以上。补充几何证据亦已写入 `qa-packed.json`，且与同一首页 SHA 绑定。

线上结果 `qa-live.json`：Actions 35670336528 成功后，对原 HTTPS 地址以独立浏览器直连完成相同 6 组流程，全部通过，0 个页面脚本异常。实际首页 SHA 与上文 `0bab2fa1…` 一致，远端 progressive manifest 指纹亦匹配。未使用额外代理或更改 TLS。搜索框及收藏动作几何、32 题目录／独居首稿刷新恢复、每日休息与收工刷新均在真实线上完成。

这是本机 HTTPS 行为验收，不是大陆多节点可达性结论，也不包含真机麦克风。
