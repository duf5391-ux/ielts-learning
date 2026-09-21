"""Source-verified corrections for generated IELTS transcription text."""
from pathlib import Path
import json,re

_rules=json.loads(Path(__file__).with_name('proofreading-corrections.json').read_text(encoding='utf8'))['rules']

def correct_transcription(text):
    for rule in _rules:
        old=rule['old']
        if old=='fo r':
            text=re.sub(r'(?<![A-Za-z])fo r(?![A-Za-z])',rule['new'],text)
        else:
            text=text.replace(old,rule['new'])
    return text
