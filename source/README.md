# 源码与逐接口检查快照 · 2026-09-21

本分支保存正式源码及维护、探针材料。2026-09-22源码已同步最新正式册 `e2b9e12e…`，对应已成功部署的主分支提交 `c84dab611f943c9e24b9a595321462392c96ef4a`。本源码分支的 `site/` 保留旧版；预览最新完整站点请使用 `main` 分支。

## 从这里开始

- [正式整页源码](production/开始学习.html)：SHA-256 `e2b9e12e58c8f03de4b43b8ec6bdb1b81a15130ddceb6b80ea5fff6a3d742075`，4091个保存字段、236个目录单元。
- [当前正式页提取的控制器与片段](production/current-extracted/)：与本次正式整页绑定。`production/extracted/` 是上一版2f870基线，留作历史对照。
- [42 个功能区总览](maintenance/research/interface-map-20260921/功能总览.md)、[429 个目标入口与 9 个独立页面](maintenance/research/interface-map-20260921/全量入口表.md)。入口数量不等于独立页面数量。
- [改版前二维入口树](maintenance/research/interface-map-20260921/现状入口树.html)、[原审计问题](maintenance/research/ui-experience-audit-20260921.md)、[三维内容关系图](maintenance/research/content-tensor-20260921/内容分级张量图.html)。图中准备/候选状态不代表已完成教学加工或已经发布。
- [最新入口与流程实现](maintenance/product-repair-20260922/README.md)、[最新线上独立复验](maintenance/word-review-separation-20260921/latest-live-verification.json)、[Kimi审查与处理](maintenance/research/kimi-review-resolution-20260921.md)。
- [逐目标探针账本](maintenance/research/ui-route-probe-20260921/full-content/ledger.json)、[动态界面检查](maintenance/research/ui-route-probe-20260921/dynamic-interfaces.json)。打开和读取内容不代表所有操作已经通过。
- [逐文件 SHA-256 清单](manifest.json)。

## 运行和维护边界

切换到 `main` 后，在仓库根目录运行 `python -m http.server 8000 --directory site`，用浏览器打开 `http://localhost:8000/`，可预览最新完整已发布版本。根目录 `python validate.py` 校验发布文件。

`production/开始学习.html` 是未经路径重写的正式原件；其媒体、词典等依赖可在仓库 `site/` 查阅。独立打开这个原件不保证所有本地相对路径可用，预览请用上述 `site/`。

`maintenance/` 保留原维护脚本、内容数据、构建工具和检查程序，部分是历史实现，部分仍引用原本地路径或运行库。它是维护快照，不是已迁移完成的一键重建环境。不要批量运行旧整页重建器；当前正式整页及指纹是增量修改的基线。

`drafts/` 保留早期词汇收藏/复习草稿，最新版已通过后续产品整合发布；这些旧草稿仍不能直接部署。维护目录中的候选文件同样不自动成为正式源码。

本快照不包括凭据、浏览器档案、用户学习记录、工具下载仓库、签名材料、大型备份压缩包及重复媒体；不是整台电脑的备份。已有静态媒体保留在 `site/`。未为既有第三方材料附加开源授权。
