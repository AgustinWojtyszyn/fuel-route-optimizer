"""Validate every executable inline script in both Django presentation templates."""
import json
from pathlib import Path
import re
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='fuel-js-') as directory:
    checked = 0
    for template in sorted(Path('routes/templates/routes').glob('*.html')):
        scripts = re.findall(r'<script(?:\s+type="(module|importmap)")?>(.*?)</script>', template.read_text(), re.S)
        if not scripts:
            raise SystemExit(f'Missing JavaScript in {template.name}')
        for index, (kind, source) in enumerate(scripts):
            if kind == 'importmap':
                json.loads(source)
                continue
            path = Path(directory) / f'{template.stem}_{index}.{ "mjs" if kind == "module" else "js" }'
            path.write_text(source)
            subprocess.run(['node', '--check', str(path)], check=True)
            checked += 1
    print(f'JavaScript syntax: {checked} executable scripts checked across both pages; import maps valid.')
