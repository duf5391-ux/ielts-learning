"""Small byte-preserving health patch; import apply_health_study_bridge(html).

CLI writes a separate candidate only. The caller must validate and publish against
the latest formal-file SHA; this tool never overwrites the input HTML.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
MARK = 'HEALTH-STUDY-BRIDGE-V1'


def _script(html, ident):
    pattern = re.compile(r'(<script\b[^>]*\bid=["\']' + re.escape(ident) + r'["\'][^>]*>)(.*?)(</script>)', re.S)
    matches = list(pattern.finditer(html))
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one script #{ident}; found {len(matches)}')
    return pattern, matches[0]


def apply_health_study_bridge(html):
    """Replace only Energy's adapter contents and our own marked bridge block."""
    energy = (ROOT / 'energy-control.js').read_text(encoding='utf-8')
    bridge = (ROOT / 'health-study-bridge.js').read_text(encoding='utf-8')
    if '</script' in energy.lower() or '</script' in bridge.lower():
        raise ValueError('Unsafe embedded script boundary')
    _script(html, 'daily-study-script')
    pattern, old = _script(html, 'energy-control-script')
    own = re.compile(r'<!--' + MARK + r'-->.*?<!--/' + MARK + r'-->', re.S)
    if len(own.findall(html)) > 1:
        raise ValueError('Duplicate health bridge blocks')
    baseline = own.sub('', html)
    if 'id="health-study-bridge-script"' in baseline or "id='health-study-bridge-script'" in baseline:
        raise ValueError('Unmarked health bridge script must be reviewed before replacement')
    changed = pattern.sub(lambda m: m[1] + '\n' + energy + '\n' + m[3], baseline, count=1)
    block = '<!--' + MARK + '--><script id="health-study-bridge-script">\n' + bridge + '\n</script><!--/' + MARK + '-->'
    if changed.count('</body>') != 1:
        raise ValueError('Expected one closing body')
    changed = changed.replace('</body>', block + '</body>', 1)
    # Every byte outside the two owned script areas must survive, including daily and saved fields.
    restored = own.sub('', changed)
    restored = pattern.sub(lambda m: m[1] + old[2] + m[3], restored, count=1)
    if restored != baseline:
        raise AssertionError('Unowned HTML changed')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise SystemExit('Write a separate candidate; do not overwrite the source.')
    before = args.source.read_bytes()
    after = apply_health_study_bridge(before.decode('utf-8')).encode('utf-8')
    args.output.write_bytes(after)
    print(json.dumps({'source': str(args.source), 'sourceSHA256': hashlib.sha256(before).hexdigest(), 'candidate': str(args.output), 'sha256': hashlib.sha256(after).hexdigest(), 'unownedBytesPreserved': True}, ensure_ascii=False))
