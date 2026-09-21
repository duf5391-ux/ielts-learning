"""Keep verified source quotations intact and explain source errors beside them."""
from pathlib import Path
from html import escape, unescape
import json
import re

NOTES = json.loads(Path(__file__).with_name('source-copy-notes.json').read_text(encoding='utf8'))['notes']

def note_html(note):
    return ('<p class="source-copy-note" data-copy-note="' + escape(note['id'], quote=True)
            + '" lang="zh-CN"><strong>原页文字提示：</strong>' + escape(note['text']) + '</p>')

def annotate_source_html(html):
    """Append notes after matching paragraphs without serializing or changing quotes."""
    def annotate(match):
        paragraph = match.group(0)
        if 'data-copy-note=' in paragraph:
            return paragraph
        additions = []
        plain = unescape(re.sub(r'<[^>]+>', '', paragraph))
        for note in NOTES:
            triggers = note.get('triggers', [note['trigger']])
            if any(trigger in plain for trigger in triggers):
                rendered = note_html(note)
                following = html[match.end():match.end()+len(rendered)+100].lstrip()
                if not following.startswith(rendered):
                    additions.append(rendered)
        return paragraph + ''.join(additions)
    return re.sub(r'<p\b[^>]*>.*?</p>', annotate, html, flags=re.S)
