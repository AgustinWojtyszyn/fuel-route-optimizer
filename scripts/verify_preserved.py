"""Check the redesign against the original committed UI contract."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess

class Contract(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links, self.fields, self.ids, self.scripts = set(), set(), set(), []
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'a' and 'href' in a:
            self.links.add(a['href'])
        if tag in ('input', 'select', 'form', 'button') and 'id' in a:
            self.fields.add((tag, a['id'], a.get('name'), a.get('type')))
        if tag == 'script':
            self.scripts.append((a.get('type'), a.get('src')))

report = {}
for page in ('landing', 'demo'):
    path = f'routes/templates/routes/{page}.html'
    old_source = subprocess.check_output(['git', 'show', f'f1a7602:{path}'], text=True)
    source = Path(path).read_text()
    old, new = Contract(old_source), Contract(source)
    assert old.links <= new.links, (page, 'lost links', old.links-new.links)
    assert old.fields <= new.fields, (page, 'lost fields', old.fields-new.fields)
    assert old.ids - {'grid'} <= new.ids, (page, 'lost ids', old.ids-new.ids)
    assert old.scripts == new.scripts, (page, 'changed script loading')
    assert source.count('<option value=') == 4
    if page == 'demo':
        for endpoint in ('/api/v1/cities/?q=', '/api/v1/routes/optimize/', 'https://tiles.openfreemap.org/styles/liberty'):
            assert endpoint in source
        pattern = r'const translations = (\{.*?\});\s*const supported'
        catalogs = json.loads(re.search(pattern, source, re.S)[1])
        originals = json.loads(re.search(pattern, old_source, re.S)[1])
        for language, messages in catalogs.items():
            assert originals[language].keys() <= messages.keys()
            # Safety caveats remain verbatim in every language.
            for key in ('approxBody', 'disclaimer'):
                assert originals[language][key] == messages[key]
    report[page] = {'links_preserved':len(old.links), 'controls_preserved':len(old.fields), 'ids_preserved':len(old.ids-{'grid'}), 'scripts_preserved':len(old.scripts)}
Path('docs/redesign/preserved-results.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
