"""Render the Week 5 lecture pages used by the review path."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PAGES = (5, 6, 7, 8, 11, 12, 14, 15, 16, 17, 20, 21, 23, 24,
         27, 28, 29, 30, 31, 32, 33, 34, 35, 36)


def export(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    for number in PAGES:
        prefix = destination / f'slide-{number:02d}'
        subprocess.run(['pdftoppm', '-f', str(number), '-l', str(number), '-singlefile',
                        '-scale-to', '1440', '-png', str(source), str(prefix)], check=True, timeout=30)
        path = prefix.with_suffix('.png')
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {'source': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'pages': PAGES, 'files': files}
    (destination / 'SOURCE.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'week05/slides')
    args = parser.parse_args()
    export(args.source, args.out)
