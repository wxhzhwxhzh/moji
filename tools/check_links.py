"""站点自检：确认 site/ 里所有站内链接和图片都指向真实文件。

用法（在项目根目录）：

    .venv\\Scripts\\python.exe tools\\check_links.py

有断裂时逐条打印并返回退出码 1，可以直接放进 CI 或提交前的检查。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE = Path(__file__).resolve().parent.parent / "site"
LINK = re.compile(r'(?:href|src)="([^"]+)"')
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:", "//")


def resolve(page: Path, url: str) -> Path:
    """把页面里的相对地址还原成磁盘上的路径。"""
    path = unquote(urlsplit(url).path)
    target = (page.parent / path).resolve()
    if path == "" or path.endswith("/"):
        return target / "index.html"
    if target.is_dir():
        return target / "index.html"
    if target.suffix == "":
        return target / "index.html"
    return target


def main() -> int:
    if not SITE.is_dir():
        print("site/ 不存在，先跑一次 mkdocs build。")
        return 2

    checked = 0
    broken: list[str] = []

    for page in sorted(SITE.rglob("*.html")):
        html = page.read_text(encoding="utf-8", errors="ignore")
        for url in LINK.findall(html):
            if url.startswith(SKIP_PREFIXES):
                continue
            checked += 1
            target = resolve(page, url)
            # 只关心站点自己的文件，越界到系统目录的不算
            if SITE not in target.parents and target != SITE:
                continue
            if not target.exists():
                broken.append(f"{page.relative_to(SITE).as_posix()} -> {url}")

    if broken:
        print(f"断裂 {len(broken)} 条：")
        for line in broken:
            print("  " + line)
        return 1

    print(f"检查 {checked} 条站内链接和图片：全部可达。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
