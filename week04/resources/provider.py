"""Read private DeepSeek settings locally. Never print a key."""
import os
from pathlib import Path

def load_environment():
    path = Path(__file__).resolve().parent / '.env'
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                name, value = line.split('=', 1)
                if name.strip() in {'DEEPSEEK_API_KEY', 'DEEPSEEK_MODEL'}:
                    os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

if __name__ == '__main__':
    import getpass
    path = Path(__file__).resolve().parent / '.env'
    if path.exists():
        raise SystemExit('A private configuration already exists. It was not overwritten.')
    key = getpass.getpass('DeepSeek API key (hidden; do not paste it in chat): ').strip()
    if not key or any(c in key for c in '\r\n'):
        raise SystemExit('A non-empty single-line key is required.')
    path.write_text('DEEPSEEK_API_KEY=' + key + '\nDEEPSEEK_MODEL=deepseek-flash\n', encoding='utf-8')
    print('Private configuration saved. No API request was made.')
