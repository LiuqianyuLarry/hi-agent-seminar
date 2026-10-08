"""Slide 26: a real DeepSeek call. Configure only DEEPSEEK_API_KEY."""
import sys
from lesson_core import ROOT, LessonError
from live_client import make_client, completion_choice, safe_api_error

def main() -> int:
    client = None
    try:
        client, settings = make_client()
        response = client.chat.completions.create(
            **settings,
            messages=[
                {"role": "system", "content": "Write in English. Extract supplied facts and missing information. Do not guess a fault cause."},
                {"role": "user", "content": (ROOT / "data/conv3_log.txt").read_text(encoding="utf-8")},
            ],
        )
        print("LIVE DEEPSEEK RESPONSE:")
        print(completion_choice(response).message.content)
        print("Request ID:", response.id)
        return 0
    except LessonError as exc:
        print("CALL STOPPED:", exc, file=sys.stderr); return 1
    except Exception as exc:
        print("CALL STOPPED:", safe_api_error(exc), file=sys.stderr); return 1
    finally:
        if client is not None: client.close()

if __name__ == "__main__": raise SystemExit(main())
