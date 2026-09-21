# 本地词典与联网句译补验 · 2026-09-21

结论：**9/9通过，页面错误0项，本轮没有发现需要修改运行代码的问题。** 受测完整候选SHA-256为`2f870d2c02b4ab48a0c64668aef59c19dbbdcb0d446df8a76a497723886b5d85`。检查时间为北京时间2026-09-21 16:58。

使用隔离的headless Edge上下文。测试副本只加`file://`资源base，指向本地完整素材；正式册和候选文件均未修改，没有读取用户浏览器记录。

- 浏览器设置offline，`navigator.onLine=false`，从`file://`打开候选副本并动态读取本地词典。连续20次真实查询表单操作（17个不同词，含3次重复）全部显示正确当前词和释义，历史记录正常更新。
- 七组词形通过：children→child、went→go、running→run、studies→study、mice→mouse、geese→goose、teeth→tooth。并发发起三次查询后显示最后请求的opportunity，没有旧查询盖回新结果。
- 无收录词明确提示未收录，随后正常词仍可查。配套精确句译断网可用；未缓存句子的断网请求明确提示连接失败，保留原句并恢复按钮，没有显示伪成功。
- 新在线隔离上下文通过真实MyMemory请求验证英→中、中→英各一次；两次HTTP200，接口responseStatus均200，quotaFinished均false。自编句`The small library closes at six every evening.`返回`小图书馆每天晚上六点关门。`；自编中文`这座小图书馆每天晚上六点关门。`返回`This small library is closed every night at 6pm.`。未发送真实用户作答。
- 手机390px截图已查看，译文、方向、收藏和关闭操作可见，无横向溢出。

结果与请求响应记录：`test-results.json`；截图：`live-en-zh.png`、`live-zh-en.png`；可复跑脚本为上级目录`qa_dictionary_translation.cjs`。

边界：此处“离线”证明本地完整学习册与词典资源在断网时可用，**不代表公网网页已具备完整离线缓存**。联网句译是当前机器当前网络的两次实测，不代表大陆所有运营商、所有句子或长期服务可用性；受外部服务网络与额度影响。机器译文仍供参考，不作为人工翻译质量认证。
