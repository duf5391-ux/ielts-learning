"""Separate the learning tools and development workbenches without rebuilding the book.

The public integration API is transform(html: str) -> str.  This module only
patches its own navigation/presentation boundary.  It never writes the formal
book; the CLI requires a distinct candidate output path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


STYLE_ID = "workspace-split-style"
STYLE = """<style id="workspace-split-style">
/* Learning tools and development are separate top-level destinations. */
body.ws-wide main{max-width:none;padding-left:32px;padding-right:32px}
#workspace,#development{width:100%;max-width:none}
#workspace .la-workspace-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
#workspace .la-card{padding:26px;display:flex;flex-direction:column;align-items:flex-start;min-height:184px}
#workspace .la-card>a{margin-top:auto;padding-top:16px}
#workspace-navigation .ws-nav-divider{display:block;margin:16px 18px 0;padding-top:18px;border-top:1px solid #d1dccf;font-size:11px;font-weight:600;letter-spacing:.08em;color:#667c68}
#development .ws-development-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
#development .ws-development-item{display:flex;flex-direction:column;align-items:flex-start;min-height:220px;padding:30px;border:1px solid #d4dfd2;border-radius:14px;background:#fff}
#development .ws-development-item h2{font-size:24px;margin:8px 0 12px}
#development .ws-development-item p{color:#586b5d;line-height:1.8}
#development .ws-development-item a{margin-top:auto;min-height:44px;display:inline-flex;align-items:center;font-weight:600}
@media(min-width:1380px){#workspace .la-workspace-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:1000px){body.ws-wide main{padding-left:22px;padding-right:22px}}
@media(max-width:600px){body.ws-wide main{padding-left:18px;padding-right:18px}#workspace .la-workspace-grid,#development .ws-development-grid{grid-template-columns:1fr;gap:14px}#workspace .la-card,#development .ws-development-item{padding:22px;min-height:170px}}
</style>"""

DEVELOPMENT = """<!--WORKSPACE-SPLIT-V1:development-->
<section class="panel workspace-panel" data-la-owner="development" data-la-title="开发工作台" hidden="" id="development">
  <header class="la-heading"><p class="la-kicker">DEVELOPMENT</p><h1>开发工作台</h1><p>网站与内容维护，集中在这里。</p></header>
  <div class="ws-development-grid">
    <article class="ws-development-item"><h2>网站文件</h2><p>查看已发布的网页文件和内容版本。</p><a href="https://github.com/duf5391-ux/ielts-learning" target="_blank" rel="noopener noreferrer">打开项目仓库 ↗</a></article>
    <article class="ws-development-item"><h2>发布记录</h2><p>查看每次网站更新的发布结果。</p><a href="https://github.com/duf5391-ux/ielts-learning/actions" target="_blank" rel="noopener noreferrer">查看发布记录 ↗</a></article>
  </div>
</section>
<!--/WORKSPACE-SPLIT-V1:development-->"""


def _replace_one(html: str, old: str, new: str, label: str) -> str:
    if html.count(old) != 1:
        raise ValueError(f"{label}: expected one source boundary, found {html.count(old)}")
    return html.replace(old, new, 1)


def transform(html: str) -> str:
    """Return a targeted candidate; preserve every existing field, ID and route."""
    if f'id="{STYLE_ID}"' in html:
        if html.count('id="development"') != 1 or html.count('data-go="development"') != 1:
            raise ValueError("Workspace split marker exists but development destination is incomplete")
        return html
    if re.search(r'\bid=[\"\']development[\"\']', html):
        raise ValueError("The development ID is already owned by another integration")

    nav = '<button data-go="workspace" type="button"><span>工作区</span></button>'
    split_nav = ('<button data-go="workspace" type="button"><span>学习工作台</span></button>'
                 '<span class="ws-nav-divider" aria-hidden="true">开发与维护</span>'
                 '<button data-go="development" type="button"><span>开发工作台</span></button>')
    html = _replace_one(html, nav, split_nav, "workspace navigation")

    # This section contains cards only, not nested sections or answer fields.
    match = re.search(r'<section\b[^>]*\bid="workspace"[^>]*>[\s\S]*?</section>', html)
    if not match or len(re.findall(r'<section\b', match.group())) != 1:
        raise ValueError("Workspace section boundary changed")
    original = match.group()
    if "data-save=" in original:
        raise ValueError("Unexpected answer fields in the workspace navigation section")
    updated = _replace_one(original, 'data-la-title="工作区"', 'data-la-title="学习工作台"', "workspace title")
    updated = _replace_one(updated, '<h1>工作区</h1>', '<h1>学习工作台</h1>', "workspace heading")
    updated = _replace_one(updated, 'IELTS / MY STUDY', 'MY STUDY DESK', "workspace kicker")
    html = html[:match.start()] + updated + DEVELOPMENT + html[match.end():]
    html = html.replace('← 返回工作区', '← 返回学习工作台')
    html = html.replace('请先到工作区导出记录。', '请先到学习工作台导出记录。')
    html = _replace_one(html, "workspace:'工作区'", "workspace:'学习工作台',development:'开发工作台'", "navigation owner label")
    owner = "const owner=data.navigationVersion&&u?u.mode:panel.dataset.laOwner||panel.id;"
    html = _replace_one(html, owner, owner + "document.body.classList.toggle('ws-wide',owner==='workspace'||owner==='development');", "navigation width state")
    html = _replace_one(html, '</head>', STYLE + '</head>', "head")
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output:
        parser.error("The output must be an isolated candidate, not the source")
    raw = source.read_bytes()
    candidate = transform(raw.decode("utf-8")).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    print(json.dumps({"source": str(source), "output": str(output),
                      "source_sha256": hashlib.sha256(raw).hexdigest(),
                      "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
                      "bytes_added": len(candidate) - len(raw)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
