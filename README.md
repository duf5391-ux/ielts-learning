# IELTS 学习册网页发布仓库

**当前为 GitHub Pages 迁移候选，尚未上线。** 预期仓库为 `gvgokok/ielts-learning`；启用 Pages 并完成首次成功部署后，预期网址为 [IELTS 学习册](https://gvgokok.github.io/ielts-learning/)。实际发布结果以 GitHub Actions 的部署输出为准。

本仓库保存从本地正式学习册生成的静态发布副本。内容维护在原学习工作区完成，再生成到隔离的 `site/` 目录；本仓库不承担账号服务或学习记录云同步。

## 文件与发布流程

- `site/`：网页和播放所需的静态资源，也是唯一上传到 Pages 的目录。
- `manifest.json`：本次发布文件的公开指纹清单。
- `validate.py`：发布前校验脚本。
- `.github/workflows/pages.yml`：校验并发布到 GitHub Pages 的工作流。

日常更新顺序为：**更新本地正式学习册 → 生成隔离发布副本和指纹清单 → 本地校验 → 提交并推送到 `main` → GitHub Actions 再次校验并更新网站**。请通过生成流程更新 `site/`，避免手工修改生成文件后在下一次发布中被覆盖。

仓库根目录的本地校验命令：

```sh
python3 validate.py
```

Windows 中也可使用已安装的 Python 运行 `python validate.py`。校验失败时应修复发布副本并重新生成清单，再提交更新。

首次发布需要在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。工作流随后会在推送到 `main` 时自动运行，也可在 Actions 页面通过 **Run workflow** 手动运行。工作流先运行 `validate.py`，通过后只上传 `site/`，再发布到 `github-pages` 环境。配置方式见 [GitHub 官方 Pages 工作流文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 网址与学习记录

成功部署后，电脑和手机可通过同一个网址访问学习册。网站由 GitHub Pages 托管，完成发布后，本地电脑关机不影响已发布网站的访问；本地修改仍需完成下一次推送和部署才会出现在网上。

学习记录保存在当前浏览器本地，没有账号登录或云端同步。电脑、手机以及不同浏览器的记录各自独立；新网址不会自动读取原本地文件或旧网址保存的记录。更换浏览器、清除网站数据或迁移网址前，应使用学习册已有的记录备份功能保留自己的记录。

## 部署配置依据

工作流按 GitHub 官方静态 Pages 方案配置，使用 `actions/checkout@v6`、`actions/configure-pages@v5`、`actions/upload-pages-artifact@v4` 和 `actions/deploy-pages@v4`。`contents: read` 用于读取仓库，`pages: write` 与 `id-token: write` 用于 Pages 部署；部署网址取自 `deployment` 步骤的 `page_url` 输出。[官方工作流与权限说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

发布任务共用 `pages` 并发组，`cancel-in-progress: false` 保留已经运行中的部署。[GitHub 官方并发配置说明](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
