"""Compare teaching content while excluding independent review overlays."""
from bs4 import BeautifulSoup
import hashlib
import json
import re

_indexes = {}

def find_node(s, selector):
    if re.fullmatch(r'#[A-Za-z_][\w-]*', selector):
        if id(s) not in _indexes:
            _indexes[id(s)] = {n['id']: n for n in s.find_all(id=True)}
        return _indexes[id(s)].get(selector[1:])
    return s.select_one(selector)

def clean(node):
    clone = BeautifulSoup(str(node), 'html.parser')
    for n in list(clone.select('[data-learning-audit],[data-content-audit],script,style')):
        n.decompose()
    return clone

def content_fingerprint(node):
    if node is None:
        return None
    s = clean(node)
    payload = {
        'text': ' '.join(s.get_text(' ', strip=True).split()),
        'links': [n.get('href') for n in s.select('a[href]')],
        'audio': [n.get('src') for n in s.select('audio[src],audio source')],
        'images': [n.get('src') for n in s.select('img')],
        'fields': [n.get('data-save') for n in s.select('[data-save]')],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def item_fingerprints(s, item):
    selectors = [item['selector']]
    selectors += [e['selector'] for e in item.get('evidence', []) if e.get('selector')]
    target = find_node(s, item['selector'])
    if target:
        # The linked lesson cases are part of the evidence, not just the visible summary.
        for a in clean(target).select('a[href^="#"]'):
            ref = a['href']
            if ref != '#' and find_node(s, ref):
                selectors.append(ref)
    result = {}
    for sel in dict.fromkeys(selectors):
        try:
            result[sel] = content_fingerprint(find_node(s, sel))
        except Exception:
            result[sel] = None
    return result
