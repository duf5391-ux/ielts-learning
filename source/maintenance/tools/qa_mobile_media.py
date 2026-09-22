"""Verify extracted media against the actual prior inline bytes, independently of the builder."""
import base64
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

from prepare_mobile_media import BOOK, STAGE


class Inventory(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.media, self.fields = [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag in ('img', 'audio', 'source'):
            self.media.append((tag, data))
        if 'data-save' in data:
            self.fields.append(data['data-save'])


def verify(candidate=None):
    candidate = Path(candidate) if candidate else STAGE / '开始学习.html'
    original = Inventory((BOOK / '开始学习.html').read_text(encoding='utf-8'))
    actual = Inventory(candidate.read_text(encoding='utf-8'))
    assert original.fields == actual.fields
    assert len(actual.fields) == 3353
    assert len(original.media) == len(actual.media)
    extracted = []
    for (old_tag, old), (tag, new) in zip(original.media, actual.media):
        assert old_tag == tag
        if tag == 'img':
            assert new['loading'] == 'lazy' and new['decoding'] == 'async'
        if tag == 'audio':
            assert new['preload'] == 'none'
        source = old.get('src') or ''
        if source.startswith('data:'):
            payload = base64.b64decode(source.split(',', 1)[1], validate=True)
            target = (STAGE / new['src']).resolve()
            assert target.is_relative_to(STAGE.resolve())
            assert target.read_bytes() == payload
            extracted.append({'path': new['src'], 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
        else:
            assert new.get('src') == old.get('src')
    assert len(extracted) == 24
    report = {'candidate': str(candidate), 'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
              'passed': True, 'save_fields': len(actual.fields), 'media_elements': len(actual.media),
              'byte_identical_extracted_media': extracted, 'other_media_src_unchanged': True,
              'browser_evidence': 'Initial media-only candidate: CUA at loopback origin; audio #listening-first played to 13.380105s of 154.592653s, readyState4, no error, paused; four Miles Davis PNGs loaded at 951x1345; phone-width document had no horizontal overflow. Combined release needs its own UI verification.'}
    output = STAGE / 'media-qa.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'byte_identical_extracted_media'}, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    import sys
    verify(sys.argv[1] if len(sys.argv) > 1 else None)
