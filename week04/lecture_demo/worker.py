"""Run only registered read-only Week 3 tools in a child process. No shell execution."""
import asyncio, json, sys, time
from executor import Executor
from schemas import fail

def main():
    request = json.loads(sys.stdin.read())
    # Delay is set ONLY by the teacher's local scenario, never by model arguments.
    if request.get('teaching_delay_s', 0):
        time.sleep(float(request['teaching_delay_s']))
    executor = Executor()
    result = asyncio.run(executor.execute(request['name'], json.dumps(request['arguments'])))
    sys.stdout.write(json.dumps(result, ensure_ascii=False, allow_nan=False))

if __name__=='__main__':
    main()
