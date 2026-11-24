"""Повторная сборка текущих SVG/PNG в изолированной папке."""
import hashlib
import json
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from project_model import ROOT, SRC, FIG
from concise_catalog import FIGURES


def main():
    filenames = [item['path']+suffix for item in FIGURES for suffix in ('.svg', '.png')]
    expected = {name: hashlib.sha256((FIG/name).read_bytes()).hexdigest() for name in filenames}
    with TemporaryDirectory(prefix='.repro-concise-', dir=ROOT) as temporary:
        from pathlib import Path
        target = Path(temporary)
        (target/'src').mkdir()
        (target/'figures').mkdir()
        for source in SRC.iterdir():
            if source.suffix in ('.py', '.mjs') or source.name == 'figures_manifest.json':
                shutil.copy2(source, target/'src'/source.name)
        for source in FIG.glob('*.svg'):
            shutil.copy2(source, target/'figures'/source.name)
        subprocess.run([sys.executable, str(target/'src/prepare_concise_figures.py')], check=True)
        subprocess.run(['node', str(target/'src/render_concise.mjs')], check=True)
        actual = {name: hashlib.sha256((target/'figures'/name).read_bytes()).hexdigest() for name in filenames}
        assert expected == actual, [name for name in expected if expected[name] != actual[name]]
    (SRC/'reproducibility_concise.json').write_text(json.dumps({
        'figures': len(FIGURES), 'svg_png_compared': len(expected), 'all_hashes_match': True,
        'hashes': {'figures/'+name: digest for name, digest in expected.items()},
        'scope': 'Повторная кодовая генерация печатных SVG/PNG на Mac. Не испытания банковского ПО.'
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Identical SVG/PNG: {len(expected)}')


if __name__ == '__main__':
    main()
