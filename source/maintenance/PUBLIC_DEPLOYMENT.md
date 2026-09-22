最新已发布：3ba0baa5正式册，4092字段、236单元，Actions 35680317051；首页SHA4e3d8f43。本轮单词整合、双端UI和大陆探测见 research/product-word-workspace-delivery-20260922.md。下方旧数字为历史。

当前最新已发布：e2b9e12e 正式册，4091字段、236单元，Actions 35670336528；首页SHA 0bab2fa1。发布包、HTTPS与本轮大陆证据见 research/product-redesign-delivery-20260922.md。下方旧数字为历史。

当前最新已发布：83346245 正式册，3371字段、227单元，Actions 35611402372；首页SHA 8c77a35f。验证边界见 research/architecture-content-delivery-20260921.md。以下旧数字以此为准。

# 公网版与本地内容同步（GitHub Pages 已上线）

最新方向：用户要求中国大陆至少能直接访问，网址不含 AI 平台品牌。原 Sites 地址在北京节点返回403，已停止继续发布；下方 Sites 流程仅保留为历史恢复资料。

当前发布项目位于独立 `github-publication/` 仓库，固定远程仓库 `duf5391-ux/ielts-learning`，网址 `https://duf5391-ux.github.io/ielts-learning/`，已成功部署并强制HTTPS。2026-09-21本轮已发布2f870d2c正式版，1085文件、261299690字节、3368保存字段，首页约140 KB并渐进恢复完整正文。成功状态及当前访问限制见 `research/github-pages-migration-status.json`，不把历史全节点成功当作长期保证。

## 当前构建与更新流程

1. 先核实 README 的最新正式册，增量修改并通过对应内容/交互检查。
2. 运行 `./prepare_github_publication.ps1 -Progressive`：复用 `web-publication/prepare.py` 构建并检查依赖闭包、媒体副本、保存字段和语法，再生成轻量首页、按原顺序恢复控件的渐进加载包，复制到独立 `github-publication/site/`。复制前后逐文件核对SHA和大小；失败保留上次完整候选。
3. 专用公开仓库与 GitHub Actions Pages 已创建，不重复创建。用户已通过官方设备流授权 `duf5391-ux`，凭据存储在系统keyring；不能因为连接器显示另一个账号而切换发布归属。不把 token 放入代码、远程URL或聊天，用户无关的仓库不修改。
4. 首次建站之后，运行 `./publish_github.ps1`：默认启用 `-Progressive` 重新构建本地正式版、校验独立仓库/远程目标、提交并推送到同一个 `main`。GitHub Actions 再次校验指纹，只上传 `site/` 并发布；网页运行不依赖本机在线。
5. 核实 Actions 成功，核对 HTTPS 首页指纹和关键资源。失败保留上次成功信息；生成成功或 Git 推送成功均不等于网站更新成功。
6. 首次迁移需实际浏览器检查，以及 `python research/probe_github_publication.py --base-url https://duf5391-ux.github.io/ielts-learning/` 的同组大陆多节点首页和两条关键音频检查。平台404初筛不计为本站验收；音频Range探测不等于完整播放。用户所在大陆设备仍需复验。

用户让助手修改正式册时，同一任务完成同步发布，除非明确要求只改本地。用户自行修改后可以运行同步脚本或说“同步发布雅思”。本地每次保存不会自行上传；推送 `main` 后由云端自动部署，部署完成后电脑关机不影响网站服务。

本次 GitHub CLI 直连曾超时，登录任务确认用户已有 Windows 系统代理 `127.0.0.1:10808`。需要时仅让相关 CLI 进程沿用该代理，不修改系统设置、不关闭TLS校验；这与大陆远程节点的直接访问验收是不同条件。

学习记录仍保存在各浏览器本地，无账号云同步。新网址与旧网址/本地文件存储隔离，使用现有整册、课程、新增资料导出/导入，录音单独下载。内容/功能同步和个人记录同步必须明确区分。

## 以下为原 Sites 发布历史

原站的源仓库、静态包和成功状态用于追溯，不继续执行本节步骤。新流程以上文为准。

用户已授权：将雅思学习册持续托管到公网，并在本地正式内容更新后同步发布。平台由助手选择，暂不处理 App Store。

当前发布项目：`web-publication/`，独立 Git 仓库。站点身份只认 `.openai/hosting.json` 中的 `project_id`，不得重复创建站点。
当前站点 ID：`appgprj_6aafe4aba57c8191bb7584968912183b`。访问范围为 public。
固定网址：https://ielts-study-book-0920.harry-oditbap.chatgpt.site
正式网址及最近成功状态以 `research/public-deployment-status.json` 为准；文件未显示 succeeded 时不得声称上线。

## 更新约定

用户让助手修改正式学习册时，完成本地修改和相关验证后，同步更新现有公网版，除非用户明确说只改本地。
用户自行改了本地文件后，可以让助手“同步发布雅思”。这是一套按更新任务发布的流程，不是后台文件监听器；本地每次保存不会自行触发上传。

1. 先读 README 顶部，核实当前正式 HTML，而不是旧候选稿。不要运行旧整页重建器。
2. 运行 `./prepare_web_publication.ps1`，生成 `web-publication/dist/`。它复制当前依赖，验证保存字段、语法、媒体大小并生成指纹清单，不读取浏览器记录。构建期间全部源文件指纹必须保持一致；新增动态媒体、外部 JS/JSON 中的资源路径或 srcset 时，必须先扩展收集器并核对新增资源，不能仅以首页通过当作依赖完整。
3. 如果更换了转换过的音频、C21 PDF 或 `extra-resources.json` 中登记的源文件，构建器会因指纹不匹配而停止。先重新生成并验证网页副本，保留完整时长/页码/文字层，再更新资源映射和显式依赖清单，不能让旧副本覆盖新原件。
4. 在 `web-publication/` 中提交确切文件。通过 Sites 原生 `create_source_repository_write_credential` 为已有站点获得短期权限，以单次 HTTP Authorization header 推送 `HEAD:main`。凭据不得写入文件、远程 URL 或 Git 配置。
5. 推送成功后运行 `git rev-parse --verify HEAD`，复制完整 SHA。源码直到打包/保存完成不得改变。
6. 优先用当前 Sites 发布技能的打包脚本。本次插件安装目录在处理中消失且 Windows 无 Bash，因此保留 `web-publication/package.py` 作可移植替代，严格输出 `dist/` 和 `dist/.openai/hosting.json` 的静态包结构。打包命令：`python package.py ../web-publication.tar.gz`。打包器要求发布仓库已全部提交，逐个核对 dist 文件清单、长度和 SHA-256；任何漏文件或构建后的修改都停止打包。单文件上限 25 MiB，展开包上限 256 MiB。
7. 通过 Sites 原生 `save_site_version` 保存该 SHA 和绝对本地压缩包路径，再对返回的 version ID 执行 `deploy_site_version`。这是已授权的 public 站点，不改回 private，也不重复询问是否发布。
8. 用返回的 deployment ID 查询到 succeeded。保存成功网址/版本/提交/正式册指纹到 `research/public-deployment-status.json`，失败保留上次成功信息，不声称新版已上线。

本次实际恢复路径：原生 archive 上传在两个不同存储端点均于 60 秒超时，完整源码推送已成功。无法通过本机文件传输交付发布包时，改由 `save_site_version` 的源码构建回退保存相同提交（不提供 archive），再让平台部署这个已保存版本。本地包和资源校验仍保留，不能绕过 Sites 原生工具自行调用发布 HTTP 接口。

## 范围

发布后由云端持续提供 HTTPS 服务，电脑关机或关闭本地预览不影响已经发布的网站。
更新保持同一网站身份和网址，保留原有 `data-save`、`DAILY-STUDY-V1`、`daily-study-state` 和材料身份。
这是内容/功能发布同步，尚无账号及学习记录云同步。从本地文件首次迁移需要分别导出/导入整册、定制课程和新增资料；录音单独下载。详情见 `web-publication/README.md`。
维护报告、构建工具、备份及凭据不进入公开静态包。实际发布文件由引用闭包决定，不能仅按目录名称排除原始参考或扩展资料。
