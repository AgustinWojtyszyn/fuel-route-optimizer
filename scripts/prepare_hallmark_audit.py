"""Stage the exact templates with filesystem paths Hallmark can resolve.
Django's /static/ URLs are virtual; no product markup or logic is changed.
Run sloplint against these files with --url pointing at the real Django pages.
"""
from pathlib import Path
for name in ('landing', 'demo'):
    source = Path(f'routes/templates/routes/{name}.html').read_text()
    source = source.replace('/static/routes/', '../../../routes/static/routes/')
    Path('docs/redesign/audit').mkdir(parents=True, exist_ok=True)
    Path(f'docs/redesign/audit/{name}.html').write_text(source)
