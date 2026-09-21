"""Merge the added lesson catalogue into the existing materials panel.

The callable only transforms the supplied HTML.  Running this module accepts an
explicit input and output path, so importing it never writes the live workbook.
"""
from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Comment


STYLE_ID = "merged-resource-directory-style"
CSS = """#library>.chapter-head{margin-bottom:22px}
.library-jumps{display:flex;flex-wrap:wrap;gap:10px 22px;margin:0 0 34px;padding:0 0 20px;border-bottom:1px solid var(--line,#dedbd2)}
.library-jumps a{font-size:14px;text-underline-offset:4px}
#library #resource-update{max-width:none;margin:0 0 48px;scroll-margin-top:110px}
#resource-update>.chapter-head{margin:0 0 24px;padding:0;border:0}
#resource-update>.chapter-head h2{margin:8px 0 12px;font-size:28px;line-height:1.4}
#resource-update>.chapter-head p{max-width:780px}
#resource-new-list,#library-materials,#library-rules,#library-files{scroll-margin-top:110px}
#library>.new-library-entry{margin-top:28px}
@media(max-width:700px){.library-jumps{gap:12px 20px;margin-bottom:26px}#resource-update>.chapter-head h2{font-size:24px}#library #resource-update{margin-bottom:32px}}
"""


def _replace_once(page: str, old: str, new: str, description: str) -> str:
    """Accept both first application and the already-patched script."""
    if old in page:
        assert page.count(old) == 1, "Ambiguous " + description
        return page.replace(old, new, 1)
    assert new in page, "Missing " + description
    return page


def _remove_marked(page: str, key: str, namespace: str = "RESOURCE") -> str:
    return re.sub(
        rf"<!--{namespace}-20260916:{re.escape(key)}-->.*?<!--/{namespace}-20260916-->",
        "", page, flags=re.S,
    )


def merge_html(page: str) -> str:
    """Return one catalogue in #library, preserving anchors and saved fields.

    #resource-update remains a section, but is no longer an independent panel.
    This keeps old bookmarks and the technique integrator's catalogue marker and
    heading lookup usable on subsequent runs.
    """
    for key in ("nav", "library"):
        page = _remove_marked(page, key)
    for key in ("guide", "resource-update"):
        page = _remove_marked(page, key, "TECHNIQUES")

    soup = BeautifulSoup(page, "html.parser")
    library = soup.select_one("main > #library.panel")
    catalogue = soup.select_one("#resource-update")
    assert library is not None and catalogue is not None, "Missing resource panels"
    original_fields = [x.get("data-save") for x in soup.select("[data-save]")]
    original_cards = [x.get("href") for x in soup.select(".res-card")]
    original_files = [str(x) for x in library.select(".source-file")]
    rules = library.select_one(".official-rules")
    assert rules is not None, "Missing existing exam requirements"
    original_rules = rules.decode_contents()

    # Remove the repeated sidebar item even if its old comment markers are gone.
    for node in soup.select('.sidebar [data-go="resource-update"]'):
        node.decompose()
    for node in soup.select("#guide .technique-entry, #resource-update .technique-entry"):
        node.decompose()
    buttons = soup.select('.sidebar [data-go="library"]')
    assert len(buttons) == 1, "Expected one original materials navigation button"
    label = buttons[0].find("span")
    assert label is not None
    label.string = "资源目录"

    # The former catalogue keeps its stable ID and child IDs, without panel
    # visibility.  It no longer needs a large link back to its own search area.
    catalogue["class"] = [c for c in catalogue.get("class", []) if c != "panel"]
    if "library-catalog" not in catalogue["class"]:
        catalogue["class"].append("library-catalog")
    catalogue.attrs.pop("hidden", None)
    for node in catalogue.select(":scope > .res-dual"):
        node.decompose()
    catalogue_header = catalogue.select_one(":scope > header.chapter-head")
    assert catalogue_header is not None, "Missing catalogue heading"
    catalogue_title = catalogue_header.find(["h1", "h2"])
    assert catalogue_title is not None
    catalogue_title.name = "h2"
    catalogue_title.string = "话题与学习技巧"
    badge = catalogue_header.select_one(".res-badge")
    if badge is not None:
        badge.decompose()

    # If there are old catalogue boundary comments outside the moved node, move
    # their ownership with it.  The existing cards' technique markers survive.
    for node in list(soup.find_all(string=lambda s: isinstance(s, Comment))):
        if str(node).strip() == "RESOURCE-20260916:catalog":
            next_node = node.next_sibling
            if next_node is catalogue:
                end_node = catalogue.next_sibling
                if isinstance(end_node, Comment) and str(end_node).strip() == "/RESOURCE-20260916":
                    end_node.extract()
                node.extract()

    header = library.select_one(":scope > header.chapter-head")
    assert header is not None, "Missing existing materials heading"
    header.find("h1").string = "资源目录"
    kicker = header.select_one(".ui-kicker")
    if kicker is not None:
        kicker.string = "LEARNING RESOURCES"
    description = header.find_all("p", recursive=False)[-1]
    description.string = "按话题和技能选学；题目、音频、学习册和考试要求也在这里。"

    # One set of small same-page links keeps original files accessible after the
    # 44-card teaching section is moved here.
    for node in library.select(":scope > .library-jumps"):
        node.decompose()
    jumps = soup.new_tag("nav", attrs={"class": "library-jumps", "aria-label": "资源目录分区"})
    for anchor, text in (
        ("resource-update", "话题与学习技巧"),
        ("library-materials", "学习材料"),
        ("library-rules", "考试要求"),
        ("library-files", "原始文件"),
    ):
        link = soup.new_tag("a", href="#" + anchor)
        link.string = text
        jumps.append(link)
    catalogue.extract()
    header.insert_after(jumps)
    jumps.insert_after(Comment("RESOURCE-20260916:catalog"))
    jumps.next_sibling.insert_after(catalogue)
    catalogue.insert_after(Comment("/RESOURCE-20260916"))

    # The earlier notice belongs beside downloadable material.  It stays a
    # useful file link, below the unified heading and lesson directory.
    downloads = library.select_one(":scope > .download-shelf")
    file_heading = library.select_one(":scope > .section-heading")
    assert downloads is not None and file_heading is not None
    downloads["id"] = "library-materials"
    rules["id"] = "library-rules"
    file_heading["id"] = "library-files"
    extension_entry = library.select_one(":scope > .new-library-entry")
    if extension_entry is not None:
        extension_entry.extract()
        downloads.insert_before(extension_entry)

    style = soup.find(id=STYLE_ID)
    if style is None:
        style = soup.new_tag("style", id=STYLE_ID)
        soup.head.append(style)
    style.string = CSS
    page = str(soup)

    # Infer the panel from the actual target.  This covers both legacy hashes
    # and the new short same-page links while retaining every chapter rule.
    page = _replace_once(
        page,
        "let id=h;if(h.startsWith('topic-'))",
        "let id=document.getElementById(h)?.closest('main>.panel')?.id||h;if(h.startsWith('topic-'))",
        "main hash router",
    )
    page = _replace_once(
        page,
        "let pageId=hash;if(hash.startsWith('topic-'))",
        "let pageId=document.getElementById(hash)?.closest('main>.panel')?.id||hash;if(hash.startsWith('topic-'))",
        "page label router",
    )
    page = _replace_once(page, "library:'材料与规则'", "library:'资源目录'", "library page name")
    old_resource_route = "function route(){const hash=decodeURIComponent(location.hash.slice(1));if(hash==='resource-update'){$('#current-page-label').textContent='话题与学习资源';document.title='话题与学习资源 · IELTS Work';}if(hash==='resource-new-list'){location.hash='resource-update';requestAnimationFrame(()=>$('#resource-new-list').scrollIntoView({block:'start'}));}records();}"
    new_resource_route = "function route(){records();}"
    page = _replace_once(page, old_resource_route, new_resource_route, "resource records router")
    # The removed sidebar item has no active-page colour rule to maintain.
    page = re.sub(r'\.sidebar nav button\[data-go="resource-update"\]\[aria-current="page"\]\{[^}]*\}', "", page)

    result = BeautifulSoup(page, "html.parser")
    assert original_fields == [x.get("data-save") for x in result.select("[data-save]")]
    assert original_cards == [x.get("href") for x in result.select(".res-card")]
    assert original_files == [str(x) for x in result.select("#library .source-file")]
    assert original_rules == result.select_one("#library .official-rules").decode_contents()
    assert len(result.select("#library #resource-update")) == 1
    assert not result.select("#resource-update.panel, .sidebar [data-go=resource-update]")
    assert len(result.select("#library > .library-jumps")) == 1
    assert len(result.select("#library h1")) == 1
    ids = [x["id"] for x in result.select("[id]")]
    assert len(ids) == len(set(ids)), "Duplicate ID after resource merge"
    return page


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert args.input.resolve() != args.output.resolve(), "Use a separate output path for manual QA"
    args.output.write_text(merge_html(args.input.read_text(encoding="utf-8")), encoding="utf-8")
    print(args.output)
