# 源码与逐接口检查快照 · 2026-09-21

本分支保存当前正式源码及维护、探针材料。`site/` 仍是提交 `46bc80bc1d77638f019f58a2c39bfed65a99c19e` 的原发布文件；本次源码推送没有改变网站。

## 从这里开始

- [正式整页源码](production/开始学习.html)：SHA-256 `2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85`，3368 个保存字段。
- [正式页提取的控制器与片段](production/extracted/)：与正式整页绑定，优先于历史维护目录中的同名文件。
- [42 个功能区总览](maintenance/research/interface-map-20260921/功能总览.md)、[429 个目标入口与 9 个独立页面](maintenance/research/interface-map-20260921/全量入口表.md)。入口数量不等于独立页面数量。
- [当前二维入口树](maintenance/research/interface-map-20260921/现状入口树.html)、[已证实问题](maintenance/research/ui-experience-audit-20260921.md)。分级立体关系图仍在继续制作。
- [逐目标探针账本](maintenance/research/ui-route-probe-20260921/full-content/ledger.json)、[动态界面检查](maintenance/research/ui-route-probe-20260921/dynamic-interfaces.json)。打开和读取内容不代表所有操作已经通过。
- [逐文件 SHA-256 清单](manifest.json)。

## 运行和维护边界

在仓库根目录运行 `python -m http.server 8000 --directory site`，用浏览器打开 `http://localhost:8000/`，可预览完整已发布版本。根目录 `python validate.py` 校验发布文件。

`production/开始学习.html` 是未经路径重写的正式原件；其媒体、词典等依赖可在仓库 `site/` 查阅。独立打开这个原件不保证所有本地相对路径可用，预览请用上述 `site/`。

`maintenance/` 保留原维护脚本、内容数据、构建工具和检查程序，部分是历史实现，部分仍引用原本地路径或运行库。它是维护快照，不是已迁移完成的一键重建环境。不要批量运行旧整页重建器；当前正式整页及指纹是增量修改的基线。

`drafts/` 仅含尚未集成、尚未通过验证的词汇收藏/复习改动，不能当作已修复或发布。维护目录中的候选文件同样不自动成为正式源码。

本快照不包括凭据、浏览器档案、用户学习记录、工具下载仓库、签名材料、大型备份压缩包及重复媒体；不是整台电脑的备份。已有静态媒体保留在 `site/`。未为既有第三方材料附加开源授权。
