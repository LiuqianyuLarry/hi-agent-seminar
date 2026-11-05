"""Run tests in a separate process; prevent a broken student loop from hanging forever."""
import subprocess,sys

def main():
    try:
        return subprocess.run([sys.executable,'-m','pytest',*sys.argv[1:]],timeout=180).returncode
    except subprocess.TimeoutExpired:
        print('External test watchdog: stopped pytest after 180 seconds. Inspect your loop.',file=sys.stderr)
        return 124
if __name__=='__main__':raise SystemExit(main())
