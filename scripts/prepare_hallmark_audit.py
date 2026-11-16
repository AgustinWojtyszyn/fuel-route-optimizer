"""Stage equivalent Django templates with filesystem-resolvable CSS for Hallmark.
--local-assets lets file:// previews load the real local fonts/scripts, without changing
production files. The render URLs still examine the real Django pages.
"""
import argparse
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--out', default='docs/redesign/audit')
parser.add_argument('--origin', default='', help='Legacy flag enabling local asset staging')
parser.add_argument('--local-assets', action='store_true')
args = parser.parse_args()
output = Path(args.out)
output.mkdir(parents=True, exist_ok=True)
static = Path('routes/static/routes')
if args.origin or args.local_assets:
    (output / 'assets').mkdir(exist_ok=True)
    for css in static.glob('*.css'):
        content = css.read_text().replace('/static/routes/', os.path.relpath(static, output/'assets')+'/')
        for font in static.glob('*.ttf'):
            content = content.replace(f'url("{font.name}")', f'url("{os.path.relpath(font, output / "assets")}")')
        (output / 'assets' / css.name).write_text(content)
for name in ('landing', 'demo'):
    source = Path(f'routes/templates/routes/{name}.html').read_text()
    if args.origin or args.local_assets:
        for css in static.glob('*.css'):
            source = source.replace(f'href="/static/routes/{css.name}"', f'href="assets/{css.name}"')
        source = source.replace('/static/routes/', os.path.relpath(static, output)+'/')
    else:
        relative = os.path.relpath(static, output)
        source = source.replace('/static/routes/', relative+'/')
    (output / f'{name}.html').write_text(source)
