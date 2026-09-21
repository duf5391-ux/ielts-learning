# 公网页面的渐进启动构建

唯一实现接口是 `tools/progressive_web.py::apply_progressive_loading(stage_dir) -> dict`。输入是发布器已经复制依赖、改写相对链接、补好 head/icon/webmanifest 的 `stage_dir/index.html`；不要传本地正式册。函数增量生成资源并替换该 stage 的首页，不修改内容维护源、学习记录或发布仓库。对已经转换的输入会明确报错，避免二次启动层。

## 运行约定

- 先显示独立的暖白/绿色轻量首屏。入口按钮只记录想去的位置；所有正文准备好之前不能作答。
- 正文按原父子结构分成 24 KiB / 150 元素左右的小操作，用 JSON 包承载。原有大 JSON 数据脚本保持单个文本节点，其体积不代表等量 DOM 元素。
- 两个正文包与一个控制器包预取；每次插入都让出主线程，累计约 8 ms 后让出绘制帧。组装期间正文 `display:none`，避免反复全量排版。
- 3353 字段及 JSON 数据 ID 完整后，将正文切到仅 `visibility:hidden` 的 `initializing` 状态，再逐个运行原控制器。保留原代码、严格顺序、元素位置和 ID；不卸载再建字段，不重做恢复。
- 原始深链保持；首屏选择的新入口在初始化之前写入 URL，业务控制器按原方式路由。
- 所有启动资源文件名绑定内容哈希；读取正文和控制器包校验 SHA-256/字节数。外部词典控制器复制为**同一目录**的哈希文件，并使用 SRI，保留 `document.currentScript.src` 推导词典目录的语义。
- 包缺失、内容哈希不匹配、inline 控制器抛错或外部控制器加载失败时停止初始化，保留可读错误与刷新重试按钮。不会清理 localStorage。

当前实现是合作式完整 DOM 启动，后续仍由原模块显示所需内容。它**没有**实现隐藏学习面板的卸载/重建；原字段缓存和直接绑定事件要求启动完成前完整组装。媒体按需加载属于上游移动优化变换。

## 发布器必须保留的验证

1. 函数内部用注入操作及脚本占位符反向重组，验证**输入 HTML 字节完全相同**，再对保存字段顺序、所有 ID、链接、JSON 脚本 ID 做独立指纹比较。
2. 生成的 `progressive-build.json` 和函数返回值相同，包含 source/entry SHA、`exact_reassembly`、字段/脚本计数和顺序 SHA、`generated_assets` 的路径/字节/SHA。
3. `original_references` 是延迟正文包含的原始引用。发布器须继续以 **index.html 所在目录** 为基准验证这些路径；不能把 JSON 文件所在的 `progressive/` 当作基准，也不能只扫描轻量首页。
4. `manifest` 指向的 JSON 中，`controllers` 指向原控制器数组；内联脚本在数组 `[].code`。发布器必须在变换前检查原 inline JS 语法，或在变换后检查这个数组里的代码。仅遍历 `.html` / `.js` 会漏掉内联控制器。
5. 完整发布 manifest 继续包含实际所有文件与哈希。该功能不替代发布器依赖/预算/跨文件恢复检查。

## 冻结候选及证据

- 合并输入：`source.html`，SHA `7ea735c348907a20b6b808ee403423aea263c29811071067ddca41fa85bfce44`。
- 隔离输出：`site/index.html`，SHA `f5eedbc537283fd4edb1a36782e98559ed776e62ba38d87eeec833ad932761c7`。
- 输入 3,978,782 字节，首页 138,993 字节；31 个正文 JSON 包，396 个小操作，27 个原控制器，3353 保存字段。
- `qa.json`：6/6，通过实际 loader 在 Node/linkedom 中的 DOM 组装、所有原正文结构与内容比较、深链/早期选择、重复启动保护、破损包阻断、inline 异常阻断和外部词典失败阻断。
- QA 的脚本插入钩子**记录且模拟业务控制器执行事件**，不冒充所有业务控制器的真实浏览器运行。页面初始化、SRI、词典目录、音频、菜单及手机可交互由 root 使用 CUA 在完整发布预览中验证。
- 此 `site/` 是隔离测试输出，只准备了两个外部控制器；没有复制完整音频、图片或词典数据，不能直接当成完整发布包。

复跑示例：

```powershell
python tools/progressive_web.py <完整stage目录>
node content-pipeline/progressive-boot-20260921/qa-progressive.cjs <stage目录> <变换前的index.html快照> <报告路径>
```

QA 依赖项目现有隔离测试目录中的 `linkedom`，不访问真实用户浏览器或学习记录。
