"""墨记文档 · 列表注入钩子

原站的 build.mjs 会在构建时扫一遍 content/blog 和 content/documentation，
生成「软件手册」列表、「技术博客」列表，以及首页的「最新博客」三条。
MkDocs 只负责单页转换，没有这一步，所以这里用 hook 补上。

页面里可以写这四种占位符：

    <!--META-->         本页的元信息行：日期 · 分类 · 阅读时长
    <!--LIST:DOCS-->    content/documentation 里所有文章
    <!--LIST:BLOG-->    content/blog 里所有文章，按日期从新到旧
    <!--LATEST:3-->     最新 n 篇博客（首页用）

设计上有两条刻意的约束：

1. 直接读 docs 目录里的 .md 文件，不依赖 MkDocs 的 Page / FileCollection —— 
   构建顺序变了也不会拿到半成品。
2. 生成的链接一律指向 .md 源文件，交给 MkDocs 自己的相对链接重写，
   这样不管站点部署在根路径还是子目录都能用。
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Any

FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
PLACEHOLDER = re.compile(r"<!--\s*(META|LIST|LATEST)(?::([A-Za-z0-9_]+))?\s*-->")

# 中文阅读速度，与原站 build.mjs 的 380 字/分钟一致
CHARS_PER_MINUTE = 380


def _split(raw: str) -> tuple[dict[str, str], str]:
    """把文件切成 (顶部登记信息, 正文)。"""
    match = FRONT_MATTER.match(raw)
    meta: dict[str, str] = {}
    body = raw
    if match:
        body = raw[match.end() :]
        for line in match.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
    return meta, body


def _reading_time(body: str) -> str:
    chars = len(re.sub(r"\s+", "", body))
    minutes = max(2, math.floor(chars / CHARS_PER_MINUTE + 0.5))
    return f"{minutes} 分钟阅读"


def _load(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    meta, body = _split(raw)
    meta["_path"] = path
    meta["_body"] = body
    return meta


def _collect(folder: Path) -> list[dict[str, Any]]:
    """扫一个目录里的所有 .md（跳过 index.md，它是列表页本身）。"""
    if not folder.is_dir():
        return []
    return [_load(p) for p in sorted(folder.glob("*.md")) if p.name != "index.md"]


def _by_date(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # 日期写成 YYYY-MM-DD 时，字符串比较就是正确的时间顺序
    return sorted(items, key=lambda item: str(item.get("date", "")), reverse=True)


def _row(post: dict[str, Any], page_dir: Path) -> str:
    """一条列表项：标题一行，元信息一行小字。"""
    href = os.path.relpath(post["_path"], page_dir).replace(os.sep, "/")
    title = post.get("title") or post["_path"].stem
    sub = " · ".join(
        part for part in (post.get("date", ""), post.get("tag", ""), _reading_time(post["_body"])) if part
    )
    return f"- [{title}]({href})  \n  <small>{sub}</small>"


def _rows(items: list[dict[str, Any]], page_dir: Path) -> str:
    return "\n".join(_row(item, page_dir) for item in items) or "_（暂无文章）_"


def _text(value: Any) -> str:
    """登记信息里的值可能是 YAML 解析出来的 date，统一成字符串。"""
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _meta_line(meta: dict[str, Any], body: str) -> str:
    parts = [_text(meta.get("date")), _text(meta.get("tag")), _reading_time(body)]
    return " · ".join(part for part in parts if part)


def on_page_markdown(markdown: str, page, config, files):
    docs_dir = Path(config["docs_dir"]).resolve()
    src = Path(page.file.abs_src_path or os.path.join(docs_dir, page.file.src_path))
    page_dir = src.parent
    # MkDocs 在触发 on_page_markdown 之前就把顶部登记信息收走了，
    # 所以本页的 meta 从 page.meta 取；取不到再回退到手动解析。
    page_meta: dict[str, Any] = dict(getattr(page, "meta", None) or {})
    page_body = markdown
    if not page_meta:
        page_meta, page_body = _split(markdown)

    def expand(match: re.Match[str]) -> str:
        kind = match.group(1)
        arg = (match.group(2) or "").upper()

        if kind == "META":
            return f"<small>{_meta_line(page_meta, page_body)}</small>"

        if kind == "LATEST":
            count = int(arg) if arg.isdigit() else 3
            return _rows(_by_date(_collect(docs_dir / "blog"))[:count], page_dir)

        if arg == "DOCS":
            return _rows(_collect(docs_dir / "docs"), page_dir)

        return _rows(_by_date(_collect(docs_dir / "blog")), page_dir)

    return PLACEHOLDER.sub(expand, markdown)
