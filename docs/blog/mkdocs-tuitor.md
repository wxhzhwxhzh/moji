# MkDocs 简单入门教程

MkDocs 是一个用 Python 编写的静态网站生成器，专门用来写文档。你只需要用 Markdown 写内容，用一个 YAML 文件管理配置，它就能帮你生成一个结构清晰的文档网站。生成的站点是纯静态 HTML，可以放在 GitHub Pages、Netlify 或任何静态托管服务上。

这篇教程带你从零搭好一个能用的文档站，并配置自动部署。

## 一、准备工作

MkDocs 需要 Python 环境，建议 3.8 以上。在命令行里确认一下：

```bash
python --version
```

如果已有 Python，直接安装 MkDocs：

```bash
pip install mkdocs
```

如果你想要更现代的外观，可以顺便装上很流行的 Material 主题：

```bash
pip install mkdocs-material
```

> Windows 上如果 `mkdocs` 命令找不到，可以用 `python -m mkdocs` 代替后续所有命令。

## 二、创建项目

运行下面的命令，MkDocs 会自动生成项目骨架：

```bash
mkdocs new my-docs
cd my-docs
```

生成的目录里有两个关键内容：

- `mkdocs.yml`：配置文件
- `docs/`：放 Markdown 文章的地方，里面已经有一个 `index.md` 作为首页

## 三、本地预览

在项目目录里启动本地服务器：

```bash
mkdocs serve
```

浏览器打开 `http://127.0.0.1:8000/`，就能看到默认首页。这个服务器支持热重载——你保存 Markdown 文件或修改配置后，浏览器会自动刷新，写文档时可以一直开着。

## 四、写页面和配置导航

在 `docs/` 里新建一个文件，比如 `about.md`，写点内容：

```markdown
# 关于本站

这是一个用 MkDocs 搭建的文档网站。
```

然后编辑 `mkdocs.yml`，把页面组织进导航：

```yaml
site_name: 我的文档站
nav:
  - 首页: index.md
  - 关于: about.md
```

保存后浏览器自动更新，左侧导航栏会出现"首页"和"关于"两个链接。`site_name` 是唯一必填的配置项，`nav` 决定了页面的顺序和层级。

如果你用 Material 主题，在 `mkdocs.yml` 里加上：

```yaml
theme:
  name: material
  language: zh
```

这样界面会变成 Material 风格，中文菜单也能正常显示。

## 五、构建静态网站

写完后，运行：

```bash
mkdocs build
```

生成的 `site/` 文件夹里就是完整的 HTML/CSS/JS 文件。把这个文件夹上传到任意静态托管服务，网站就上线了。

## 六、用 GitHub Actions 自动部署

手动上传比较麻烦，更省事的做法是让 GitHub 在每次推送代码时自动构建并发布到 GitHub Pages。

在项目根目录创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy MkDocs

on:
  push:
    branches:
      - main

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: pip install mkdocs mkdocs-material

      - name: Deploy
        run: mkdocs gh-deploy --force
```

几个要点：

- `permissions: contents: write` 必须加上，否则 Action 没有权限推送 `gh-pages` 分支。
- `--force` 用于强制推送，避免历史冲突。
- 如果你的默认分支叫 `master`，把 `main` 改掉。

配置完成后，去仓库的 **Settings → Pages**，把 Source 设为 **Deploy from a branch**，分支选 `gh-pages`，保存。之后每次推送代码，GitHub 都会自动帮你构建并发布。

## 七、几个实用建议

**把依赖写进 `requirements.txt`**。如果你用了 Material 主题或其他插件，建议在项目根目录维护一个依赖文件，Action 里改用 `pip install -r requirements.txt`。这样本地和线上环境一致，不容易出现"本地能跑、线上报错"的问题。

**用 `--strict` 模式构建**。把构建命令改成 `mkdocs build --strict`，链接写错或导航配置有问题时构建会直接失败，而不是静默生成一个不完美的站点。团队协作时特别有用。

**设置 `site_url`**。在 `mkdocs.yml` 里加上 `site_url: https://你的用户名.github.io/仓库名/`，生成的站点在搜索引擎和社交分享时链接才是完整的。

**善用插件**。MkDocs 生态里有不少插件，比如 `mkdocs-minify-plugin` 可以压缩输出文件，`mkdocs-git-revision-date-localized-plugin` 可以在页面底部显示最后更新日期。按需安装，在 `mkdocs.yml` 的 `plugins` 下配置即可。

## 小结

到这里，你已经有了一个能写、能看、能自动发布的文档网站。日常的工作流就是：在 `docs/` 里写 Markdown，在 `mkdocs.yml` 里调整导航，`git push` 之后等 Action 自动部署。MkDocs 的学习成本很低，剩下的时间可以花在把文档内容写好上。