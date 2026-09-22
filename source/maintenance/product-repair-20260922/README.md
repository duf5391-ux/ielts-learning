# 2026-09-22 产品入口与学习流程修复

本目录保存这一轮的增量源、组合候选、独立验收与恢复证据。用户优先级为常用工具独立、学习内容平铺可查；产品设计与截图复审由 Kimi K3 完成，主任务校正现况并集成，frontend / writing 分工开发，journey_qa 独立验收。

- 入口设计与用户原话：`../research/product-entry-design-kimi-20260922.md`、`../research/product-entry-user-evidence-20260922.md`。
- 最终决策与交付：`../research/product-entry-decisions-20260922.md`、`../research/product-redesign-delivery-20260922.md`。
- 组合源顺序：`frontend/integrate.py` → `writing/integrate.py` → `navigation/integrate.py`；`build.py` 只接受本轮原正式册 SHA `83346245…`，不得对后续正式册重复执行。
- `candidate.html` 是验收后的全页；`static.json` 检查字段、标识、媒体、内部地址、受保护脚本与语法。原3371字段全部保留，共4091字段、236目录单元、32道完整工作台写作题。
- `accept.py` 将独立验收报告及组件连续性证据绑定为 `release-acceptance.json`。前一组合的可靠性/旧地址检查只按报告明确的未改组件继承，最终入口与写作另有直接检查。
- `install.py` 验证正式册未被他人改动、候选与验收文件指纹一致，保存 `formal-backup/` 后替换正式主HTML。执行记录在 `installation.json`。再次运行会停止，不覆盖恢复点。
- 公网仍由工作区 `publish_github.ps1` 构建并更新原 GitHub Pages。`frontend/qa-packed.json`、`frontend/qa-live.json` 分别记录渐进包和HTTPS站点验收；源验收不等于线上验收。

回退前先确认现正式文件仍等于 `installation.json.after`，仅恢复本轮备份的主HTML，随后重新构建验证并同步同一站点。若之后已有新改动，应对照增量处理，不能直接覆盖。恢复HTML不会恢复浏览器个人记录；本轮测试均使用隔离合成记录，没有改动用户浏览器资料。

录音保存在当前浏览器的 IndexedDB，逐次录音分别保留；整册JSON不含声音，跨设备仍需下载音频。合成麦克风和手机视口验证不等于真人手机或四端安装验证。429个旧地址可达性不等于所有题目内容质量已逐题审完。
