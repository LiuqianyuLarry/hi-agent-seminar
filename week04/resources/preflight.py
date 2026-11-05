"""Check the existing environment and supplied data. This does not grade unfinished exercises."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import sys


def main():
    result = {'python': platform.python_version(), 'platform': platform.platform(),
              'gpu_required': False, 'api_key_required_for_core': False, 'checks': []}
    result['checks'].append({'name': 'Python 3.11 or later', 'passed': sys.version_info >= (3, 11)})
    for name, major in [('pydantic', '2'), ('pytest', None)]:
        try:
            version = importlib.metadata.version(name)
            passed = major is None or version.split('.')[0] == major
        except importlib.metadata.PackageNotFoundError:
            version, passed = 'not installed', False
        result['checks'].append({'name': name, 'version': version, 'passed': passed})
    data = Path(__file__).resolve().parent / 'data'
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        path = data / name
        result['checks'].append({'name': name, 'passed': path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected})
    result['checks'].append({'name': 'local database (run build_data.py first)', 'passed': (data / 'engineering.sqlite').is_file()})
    try:
        result['optional_deepseek_client'] = importlib.metadata.version('openai')
    except importlib.metadata.PackageNotFoundError:
        result['optional_deepseek_client'] = 'not installed; teacher-record analysis still works'
    result['success'] = all(c['passed'] for c in result['checks'])
    result['note'] = 'The four student exercises begin unfinished. Their tests are run after each exercise, not as an environment check.'
    print(json.dumps(result, indent=2))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
