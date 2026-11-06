# 墨记文档 · MkDocs 版

用 **MkDocs + Material 主题**复刻原站（`E:\123\craft\app`）：内容与目录结构照搬，地址改成 MkDocs 默认的目录式，外观交给 Material。

原站是手写静态生成器（`build.mjs` + 固定外壳），这次不再自己拼 HTML，改由 MkDocs 负责页面装配，只保留原站真正独有的那一步——**扫目录生成列表**，用一个 hook 补回来。

---

## 快速开始

```bash
# 1. 环境（已经建好 .venv，Python 3.12）
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. 本地预览（改文件会自动刷新）
.venv\Scripts\python.exe -m mkdocs serve

# 3. 构建到 site/
.venv\Scripts\python.exe -m mkdocs build

# 4. 站内链接自检（构建之后跑）
.venv\Scripts\python.exe tools\check_links.py
```

当前状态：`mkdocs build` 通过（0.8 秒），`check_links.py` 检查 **200 条**站内链接与图片，全部可达。

---

## 自动构建与部署（GitHub Actions）

`.github/workflows/deploy.yml`：**每次 push 到 `main` / `master` 就自动构建并发布到 GitHub Pages**，也可以在 Actions 页面手动触发。

流水线分两段：

| 阶段 | 做什么 | 失败会怎样 |
| --- | --- | --- |
| `build` | 装依赖 → `mkdocs build --strict` → `tools/check_links.py` → 上传 `site/` | 站点不会发布，旧版本继续在线 |
| `deploy` | `actions/deploy-pages@v4` 发布构建产物 | 同上 |

`--strict` 会把 MkDocs 的 WARNING 当成错误（断链、锚点不存在、页面没有标题等），所以坏站点发不出去，而不是等读者发现。

**首次要做的两件事**：

1. 仓库 `Settings → Pages → Build and deployment → Source` 选 **GitHub Actions**（不需要 `gh-pages` 分支）。
2. 建议在 `mkdocs.yml` 里补一行站点地址，让 canonical / og 链接指向正确域名：

   ```yaml
   site_url: https://<用户名>.github.io/<仓库名>/
   ```

**换成别的托管**（对象存储、VPS 上的 Nginx）：把 `deploy` 那个 job 换成一次上传即可，`build` 段不用动——产物就是 `site/` 这一整个目录。也可以只保留 `build`，在 Actions 页下载 `github-pages` 这个 artifact。

**本地没法直接跑这个工作流**：它依赖 GitHub 的 Pages 环境。想在本机复现它的检查部分，就是 README 开头那两行 `mkdocs build --strict` 和 `python tools/check_links.py`。

---

## 目录结构

```
.
├── mkdocs.yml              站点配置：nav、主题、Markdown 扩展、hook
├── requirements.txt        mkdocs-material==9.8.0
├── .github/workflows/
│   └── deploy.yml          push 后自动构建 + 发布到 GitHub Pages
├── hooks/
│   └── lists.py            列表注入钩子（原 build.mjs 里那一步）
├── tools/
│   └── check_links.py      产物链接自检
├── docs/                   ← 内容源（MkDocs 的 docs_dir，整个目录会被发布）
│   ├── index.md            使用引导：11 个折叠问答 + 最新 3 篇博客
│   ├── favicon.svg
│   ├── assets/brand.svg    侧栏 logo（来自原站内联 SVG 的 brandMark）
│   ├── images/             4 张插图，原样拷贝
│   ├── docs/               软件手册
│   │   ├── index.md        手册列表页
│   │   ├── getting-started.md
│   │   ├── images-and-embeds.md
│   │   └── publishing-a-post.md
│   ├── blog/               技术博客
│   │   ├── index.md        博客列表页（按日期从新到旧）
│   │   ├── building-docs-site.md
│   │   ├── daily-notes.md
│   │   └── reading-code.md
│   ├── changelog.md        更新日志
│   └── about.md            关于本站
└── site/                   构建产物（不要手改）
```

`docs/docs/` 这个双层名字是刻意的：`docs_dir` 是 `docs/`，而站点地址要保留原站的 `/docs/<篇名>/` 前缀，所以手册类文章的源文件就放在 `docs/docs/` 下。

---

## 与原站的对照

### 地址

| 原站 | 这里 |
| --- | --- |
| `/index.html` | `/` |
| `/docs/getting-started.html` | `/docs/getting-started/` |
| `/blog/reading-code.html` | `/blog/reading-code/` |
| `/changelog.html` | `/changelog/` |
| `/about.html` | `/about/` |

这是 `use_directory_urls: true` 的结果。相对链接全部由 MkDocs 生成，所以整个 `site/` 仍然可以放在任意子目录下运行。

### 内容字段

原站的自制 front matter 字段名基本保留，只有两处为了 MkDocs 语义改了名：

| 原站 | 这里 | 说明 |
| --- | --- | --- |
| `summary` | `description` | Material 会把它写进 `<meta description>` 和搜索结果 |
| `cover` / `coverAlt` | 保留，键名不变 | 但不再由构建脚本渲染成封面大图，改为正文里的第一张图 |
| `date` / `tag` / `footer` / `title` | 保留 | `date` 由 MkDocs 解析成 `date` 对象，钩子里做了类型归一 |

### 渲染方式

| 原站 | 这里 |
| --- | --- |
| 自制的 130 行 Markdown 子集解析器 | `python-markdown` + Material 的扩展（`admonition`、`pymdownx.details`、`superfences`、`tables`…） |
| 首页问答：`## 问题` + 自制折叠行 | `??? note "问题"` 折叠块（`pymdownx.details`） |
| 正文标题由 front matter 提供，`#` 被降级成 `h2` | 正文里的 `# 标题` 就是页面 `h1`，`##` / `###` 正常分级 |
| 图片说明靠 `![](... "注释")` 渲染成 `<figcaption>` | 注释改成图片下方的一行斜体 |
| 没有搜索 | Material 自带全文搜索（与原站首页说的 `Ctrl+K` 现在真的可用） |
| 左下角浮动「意见反馈」对话框 | 没有搬：它是原站 `app.js` 里的演示交互，Material 没有对应位置 |
| 无第三方依赖 | 依赖 1 个包（`mkdocs-material`，带 26 个传递依赖） |

### 唯一被改写的既有正文

只有两篇「操作说明」按新工具改写，其余文章逐字保留：

- `docs/docs/publishing-a-post.md`：`content/blog/` → `docs/blog/`，`npm run build` → `mkdocs build` / `mkdocs serve`，front matter 字段说明同步更新；
- `docs/index.md` 第 11 条问答：`content/blog/` → `docs/blog/`，「重新生成一次站点」保留。

`docs/blog/building-docs-site.md` 是一月写的旧文，讲的是当时那套 `build.mjs`，作为文章原样保留，没有改写成 MkDocs 版。

---

## 列表是怎么生成的

原站 `build.mjs` 在构建时扫目录、算阅读时长、拼列表。MkDocs 只管单页转换，所以 `hooks/lists.py` 把这一步补回来，页面里用占位符触发：

| 占位符 | 用在 | 展开成 |
| --- | --- | --- |
| `<!--LIST:DOCS-->` | `docs/docs/index.md` | 手册列表 |
| `<!--LIST:BLOG-->` | `docs/blog/index.md` | 博客列表，按 `date` 从新到旧 |
| `<!--LATEST:3-->` | `docs/index.md` | 最新 3 篇博客 |
| `<!--META-->` | 每篇文章 | `日期 · 分类 · N 分钟阅读` |

两条实现约定：

1. **直接读 `docs/` 里的 `.md` 源文件**，不依赖 MkDocs 的 `Page` 对象——构建顺序变化也不会拿到半成品；
2. **生成的链接指向 `.md` 源文件**，交给 MkDocs 自己的相对链接重写，部署到子目录也不会断。

阅读时长沿用原站的算法：正文去掉空白后的字符数 ÷ 380，四舍五入，最少 2 分钟。

> 踩过的一个坑记在这里：`on_page_markdown` 拿到 markdown 时，顶部 `---` 之间的登记信息**已经被 MkDocs 收走了**，所以本页 meta 必须从 `page.meta` 取；而且 `page.meta['date']` 是 YAML 解析出的 `date` 对象，不是字符串。

---

## 加内容

**加一篇博客**：在 `docs/blog/` 新建 `.md`，写顶部登记信息（`title` / `date` / `tag` / `description`，可选 `cover` / `coverAlt` / `footer`），正文第一行写 `# 标题`，图片用 `../images/文件名`。构建后自动出现在首页「最新博客」和博客列表。

**加一篇手册**：同样的写法，放 `docs/docs/`。

**改首页问答**：在 `docs/index.md` 里增删 `??? note "问题"` 块，块内容缩进 4 个空格；要加「阅读全文」，就在块里写 `[阅读全文](docs/某篇.md)`。

**改配色**：`mkdocs.yml` 的 `theme.palette`。

> 注意：`docs/` 下每个 `.md` 都会被发布，写给自己看的草稿不要放进这个目录（原站把给作者看的 `README.md` 放在 `content/`，这里没有对应位置）。

---

## 还没做的

- **视觉没有逐像素对齐**：这一版走的是 Material 默认外观 + 原站配色（白底、`#3964fe` 链接色），侧栏、正文栏宽度、一屏高外壳这些原站特征都没有复刻。要对齐需要自建主题，把原 `styles.css` 和 `shell()` 搬成 Jinja 模板。
- **没有搬「意见反馈」对话框**：需要的话可以在 Material 里加一个浮动按钮 + `dialog`，把原 `src/app.js` 那两段直接拿过来。
- **nav 之外的页面会打 INFO 提示**：手册正文和博客正文故意不列进 `nav`（原站侧栏就是一个扁平五项列表），构建日志里的「not included in the nav configuration」是预期行为。
- **`date` 排序仍是字符串比较**：写成 `2026-3-5` 会排错位置，约定统一用 `YYYY-MM-DD`。
