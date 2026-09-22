"""Build a lossless, cooperative bootstrap for the published static learning book.

This is deliberately a build transform, not a second content source.  The complete
DOM is assembled before any original controller runs: existing saved-field maps
and direct event bindings must never see an incomplete document.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

PREFIX = "ielts-progressive-"
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
MAX_OPERATION_BYTES = 24 * 1024
MAX_OPERATION_ELEMENTS = 150
PACK_BYTES = 128 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


@dataclass
class Node:
    tag: str
    attrs: list
    start: int
    open_end: int
    close_start: int = 0
    end: int = 0
    children: list = field(default_factory=list)
    elements: int = 1
    executable: bool = False
    contains_executable: bool = False


class SourceTree(HTMLParser):
    """Keep original source ranges instead of serializing an HTML parser's output."""
    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0] + [m.end() for m in re.finditer("\n", source)]
        self.root = Node("__root__", [], 0, 0, len(source), len(source), elements=0)
        self.stack = [self.root]
        self.nodes = []
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            raise ValueError("Unclosed HTML elements: " + ", ".join(n.tag for n in self.stack[1:]))

    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.source_offset()
        node = Node(tag, attrs, start, start + len(self.get_starttag_text()))
        typ = (dict(attrs).get("type") or "").lower().strip()
        if tag == "script" and typ not in ("application/json", "application/ld+json"):
            if typ not in ("", "text/javascript", "application/javascript"):
                raise ValueError("Unsupported executable script type: " + typ)
            if "async" in dict(attrs) or "defer" in dict(attrs) or "nomodule" in dict(attrs):
                raise ValueError("Async/deferred scripts require an explicit execution contract")
            node.executable = node.contains_executable = True
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if tag in VOID:
            node.end = node.close_start = node.open_end
        else:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            node = self.stack.pop()
            node.end = node.close_start = node.open_end

    def handle_endtag(self, tag):
        if len(self.stack) < 2 or self.stack[-1].tag != tag:
            raise ValueError(f"Non-nested closing tag </{tag}> at {self.getpos()}")
        node = self.stack.pop()
        node.close_start = self.source_offset()
        node.end = self.source.index(">", node.close_start) + 1
        node.elements += sum(n.elements for n in node.children)
        node.contains_executable |= any(n.contains_executable for n in node.children)


def fingerprint(source: str):
    tree = SourceTree(source)
    fields = [(dict(n.attrs).get("data-save"), n.tag) for n in tree.nodes if "data-save" in dict(n.attrs)]
    ids = [dict(n.attrs)["id"] for n in tree.nodes if "id" in dict(n.attrs)]
    references = []
    for node in tree.nodes:
        for name, value in node.attrs:
            if name in ("src", "href", "poster") and value:
                references.append({"tag": node.tag, "attribute": name, "value": value})
    return {"fields": fields, "ids": ids, "references": references,
            "json_script_ids": [dict(n.attrs).get("id") for n in tree.nodes if n.tag == "script" and not n.executable]}


def apply_progressive_loading(stage_dir) -> dict:
    stage = Path(stage_dir).resolve()
    index = stage / "index.html"
    original_bytes = index.read_bytes()
    source = original_bytes.decode("utf-8")
    if PREFIX in source:
        raise ValueError("The source already contains a progressive bootstrap")
    tree = SourceTree(source)
    bodies = [n for n in tree.nodes if n.tag == "body"]
    heads = [n for n in tree.nodes if n.tag == "head"]
    if len(bodies) != 1 or len(heads) != 1:
        raise ValueError("Exactly one head and body are required")
    body, head = bodies[0], heads[0]
    if any(n.executable and n.start < body.start for n in tree.nodes):
        raise ValueError("Head controllers cannot run before progressive content assembly")
    before = fingerprint(source)
    operations, scripts, anchors = [], [], []
    generated = []
    external = []

    def write_asset(stem, extension, data, directory=None):
        folder = stage / (directory or "progressive")
        folder.mkdir(parents=True, exist_ok=True)
        digest = sha(data)
        dest = folder / f"{stem}.{digest[:20]}.{extension}"
        dest.write_bytes(data)
        item = {"path": dest.relative_to(stage).as_posix(), "sha256": digest, "bytes": len(data)}
        generated.append(item)
        return item

    def anchor():
        name = f"{PREFIX}anchor-{len(anchors)}"
        anchors.append(name)
        return name

    def marker(name):
        return f"<!--{name}-->"

    def script_piece(node):
        name = f"{PREFIX}script-{len(scripts)}"
        attrs = dict(node.attrs)
        descriptor = {"marker": name, "attrs": node.attrs, "source_start": node.start,
                      "code": source[node.open_end:node.close_start],
                      "original": source[node.start:node.end]}
        if attrs.get("src"):
            parsed = urlsplit(attrs["src"])
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or parsed.path.startswith("/"):
                raise ValueError("External controller must be a plain local relative source: " + attrs["src"])
            src = (stage / unquote(parsed.path)).resolve()
            if not src.is_relative_to(stage) or not src.is_file():
                raise ValueError("Missing/unsafe controller: " + attrs["src"])
            data = src.read_bytes()
            # Keep the same directory: dictionary-engine uses document.currentScript.src.
            directory = src.parent.relative_to(stage)
            asset = write_asset(src.stem, src.suffix.lstrip("."), data, directory)
            descriptor["runtime_src"] = asset["path"]
            descriptor["integrity"] = "sha256-" + __import__("base64").b64encode(bytes.fromhex(asset["sha256"])).decode()
            external.append({"original_src": attrs["src"], **asset})
        scripts.append(descriptor)
        return marker(name)

    def fill(container, target):
        deferred = []
        pieces = []
        cursor = container.open_end
        for child in container.children:
            if child.start > cursor:
                pieces.append((source[cursor:child.start], 0))
            raw = source[child.start:child.end]
            if child.executable:
                pieces.append((script_piece(child), 0))
            elif child.children and (child.contains_executable or len(raw.encode("utf-8")) > MAX_OPERATION_BYTES or child.elements > MAX_OPERATION_ELEMENTS):
                child_anchor = anchor()
                pieces.append((source[child.start:child.open_end] + marker(child_anchor) + source[child.close_start:child.end], 1))
                deferred.append((child, child_anchor))
            else:
                pieces.append((raw, child.elements))
            cursor = child.end
        if cursor < container.close_start:
            pieces.append((source[cursor:container.close_start], 0))
        buf, size, count = [], 0, 0
        for text, elements in pieces:
            length = len(text.encode("utf-8"))
            if buf and (size + length > MAX_OPERATION_BYTES or count + elements > MAX_OPERATION_ELEMENTS):
                operations.append({"target": target, "html": "".join(buf)})
                buf, size, count = [], 0, 0
            buf.append(text)
            size += length
            count += elements
        if buf:
            operations.append({"target": target, "html": "".join(buf)})
        for child, child_anchor in deferred:
            fill(child, child_anchor)

    root_anchor = anchor()
    fill(body, root_anchor)
    # Traversal into deferred containers may encounter scripts out of document order.
    scripts.sort(key=lambda s: s["source_start"])
    reconstructed = marker(root_anchor)
    for operation in operations:
        needle = marker(operation["target"])
        if reconstructed.count(needle) != 1:
            raise AssertionError("Ambiguous or missing assembly anchor")
        reconstructed = reconstructed.replace(needle, operation["html"] + needle, 1)
    for name in anchors:
        reconstructed = reconstructed.replace(marker(name), "")
    for descriptor in scripts:
        reconstructed = reconstructed.replace(marker(descriptor["marker"]), descriptor["original"])
    original_body = source[body.open_end:body.close_start]
    if reconstructed != original_body:
        raise AssertionError("Progressive body did not reconstruct the exact input")
    rebuilt = source[:body.open_end] + reconstructed + source[body.close_start:]
    if rebuilt != source or fingerprint(rebuilt) != before:
        raise AssertionError("Fields, IDs, references or source changed during assembly")

    packs, pack, pack_size = [], [], 0
    for operation in operations:
        size = len(json_bytes(operation))
        if pack and pack_size + size > PACK_BYTES:
            packs.append(write_asset("content", "json", json_bytes(pack)))
            pack, pack_size = [], 0
        pack.append(operation)
        pack_size += size
    if pack:
        packs.append(write_asset("content", "json", json_bytes(pack)))
    runtime_scripts = [{k: v for k, v in descriptor.items() if k not in ("original", "source_start")} for descriptor in scripts]
    controllers = write_asset("controllers", "json", json_bytes(runtime_scripts))
    manifest = {"version": 1, "source_sha256": sha(original_bytes), "body_sha256": sha(original_body.encode("utf-8")),
                "root_anchor": root_anchor, "anchors": anchors, "packs": packs, "controllers": controllers,
                "operation_count": len(operations), "field_count": len(before["fields"]),
                "script_count": len(scripts), "json_script_ids": before["json_script_ids"]}
    manifest_asset = write_asset("manifest", "json", json_bytes(manifest))
    loader = write_asset("loader", "js", Path(__file__).with_name("progressive_loader.js").read_bytes())
    css = Path(__file__).with_name("progressive_loader.css").read_text(encoding="utf-8")
    config = json.dumps({"manifest": manifest_asset}, ensure_ascii=False).replace("<", "\\u003c")
    shell = f'''<div id="{PREFIX}boot" role="region" aria-label="准备学习内容">
<div class="pb-wrap"><a class="pb-brand" href="#study" data-pb-route="#study">IELTS<span>学习册</span></a>
<p class="pb-eyebrow">按自己的节奏</p><h1>今天，学一小段。</h1><p class="pb-intro">先选好想去的地方，内容准备好后就会打开。</p>
<nav aria-label="选择学习入口"><button data-pb-route="#guide">直接开始</button><button data-pb-route="#study">学习内容</button><button data-pb-route="#practice">练习</button></nav>
<p id="{PREFIX}status" role="status" aria-live="polite">正在准备学习内容…</p><progress id="{PREFIX}progress" max="100" value="0" aria-label="内容准备进度"></progress>
<button id="{PREFIX}retry" type="button" hidden>重新打开</button><noscript><p>请在浏览器中开启 JavaScript，然后刷新此页。</p></noscript></div></div>'''
    new_source = source[:head.close_start] + f'<style id="{PREFIX}style">{css}</style>' + source[head.close_start:body.open_end]
    # Apply the gate before the browser sees any asynchronously assembled content.
    new_source = re.sub(r"<body(?=[\s>])", '<body data-progressive-state="loading"', new_source, count=1, flags=re.I)
    new_source += shell + marker(root_anchor)
    new_source += f'<script id="{PREFIX}config" type="application/json">{config}</script><script id="{PREFIX}loader" src="{html.escape(loader["path"], quote=True)}" defer></script>'
    new_source += source[body.close_start:]
    index.write_bytes(new_source.encode("utf-8"))
    report = {"version": 1, "status": "validated-build", "source_html_sha256": sha(original_bytes),
              "entry_sha256": sha(index.read_bytes()), "source_bytes": len(original_bytes), "entry_bytes": index.stat().st_size,
              "reconstructed_source_sha256": sha(rebuilt.encode("utf-8")), "exact_reassembly": True,
              "saved_field_count": len(before["fields"]), "saved_field_order_sha256": sha(json_bytes(before["fields"])),
              "id_count": len(before["ids"]), "id_order_sha256": sha(json_bytes(before["ids"])),
              "executable_script_count": len(scripts), "original_script_order_sha256": sha(json_bytes([s["original"] for s in scripts])),
              "json_script_ids": before["json_script_ids"], "operation_count": len(operations),
              "max_operation_bytes": max(len(o["html"].encode("utf-8")) for o in operations),
              "content_packs": packs, "manifest": manifest_asset, "external_controllers": external,
              "generated_assets": generated, "reference_base": "site-root (the receiving index.html document)",
              "original_references": before["references"],
              "limitations": ["The complete DOM is assembled before existing controllers initialize; hidden panels are not unloaded.",
                              "Build validation is not real-device responsiveness verification."]}
    (stage / "progressive-build.json").write_bytes(json_bytes(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage_dir")
    args = parser.parse_args()
    result = apply_progressive_loading(args.stage_dir)
    print(json.dumps({k: result[k] for k in ("status", "source_bytes", "entry_bytes", "saved_field_count", "operation_count", "exact_reassembly")}, ensure_ascii=False))
