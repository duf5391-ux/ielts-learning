"""Minimal composition only. Root publisher owns formal file backups and writes."""
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def apply(page):
    original = page
    before_fields = re.findall(r'\bdata-save="([^"]+)"', page)
    signature = 'window.IELTSRecordStore={commit(values){'
    updated = 'window.IELTSRecordStore={commit(values, options = {}){'
    if signature in page:
        assert page.count(signature) == 1
        page = page.replace(signature, updated, 1)
        call = "if(!save({fields:Object.keys(values)},false)){state=previous;return false}"
        assert page.count(call) == 1
        page = page.replace(call, "if(!save({fields:Object.keys(values),expectedFields:options.expectedFields||{}},false)){state=previous;return false}", 1)
    else:
        assert page.count(updated) == 1, 'Unexpected record controller; inspect before integrating'
    recorder = (HERE / 'speaking-recorder.js').read_text(encoding='utf8')
    start_marker, end_marker = '/*SPEAKING-RECORDER-FIX:START*/', '/*SPEAKING-RECORDER-FIX:END*/'
    block = start_marker + '\n' + recorder + '\n' + end_marker
    if start_marker in page:
        page, count = re.subn(re.escape(start_marker)+r'.*?'+re.escape(end_marker), lambda _: block, page, flags=re.S)
        assert count == 1
    else:
        begin = page.index('const recorders={},urls={};function showAudio(')
        end = page.index("$$('.review-stage details').forEach", begin)
        assert 'getUserMedia' in page[begin:end] and 'data-upload' in page[begin:end]
        page = page[:begin]+block+'\n'+page[end:]
    writing = (ROOT / 'writing-workbench.js').read_text(encoding='utf8')
    marker = r'(<!--WRITING-WORKBENCH-V1:script--><script>).*?(</script><!--/WRITING-WORKBENCH-V1-->)'
    page, count = re.subn(marker, lambda m: m[1]+writing+m[2], page, flags=re.S)
    assert count == 1, 'Unexpected writing script marker'
    style = '<style id="speaking-recorder-visibility">.recorder [data-preview][hidden],.recorder [data-download][hidden]{display:none!important}</style>'
    if 'id="speaking-recorder-visibility"' not in page:
        page = page.replace('</head>', style+'</head>', 1)
    assert re.findall(r'\bdata-save="([^"]+)"', page) == before_fields
    for key in ['record-concurrency-model-script', 'health-study-', 'energy-control-script', 'DAILY-STUDY-V1']:
        assert original.count(key) == page.count(key), key
    return page


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source, target = Path(args.input), Path(args.output)
    assert source.resolve() != target.resolve(), 'Use parent publication flow to write formal source'
    result = apply(source.read_text(encoding='utf8'))
    assert apply(result) == result
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result, encoding='utf8')
    print(str(target))
