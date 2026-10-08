"""DeepSeek Chat Completions. Every successful model result comes from an API call."""
from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from lesson_core import ROOT, LessonError, save_record

BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"

@dataclass
class TextResult:
    text: str
    metadata: dict[str, Any]

def load_settings() -> tuple[dict[str, Any], dict[str, Any]]:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise LessonError("DeepSeek key missing. Run python configure.py, then run this demonstration again.")
    if any(ch.isspace() for ch in key):
        raise LessonError("The API key contains whitespace. Run python configure.py again.")
    try:
        budget = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))
        timeout = float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "40"))
        retries = int(os.getenv("DEEPSEEK_MAX_RETRIES", "1"))
    except ValueError:
        raise LessonError("Token budget, timeout and retries must be numeric.") from None
    if not 1 <= budget <= 16000 or not 0 < timeout <= 120 or not 0 <= retries <= 2:
        raise LessonError("Use 1-16000 output tokens, a timeout up to 120 seconds and 0-2 retries.")
    client_options = {"api_key": key, "base_url": BASE_URL, "timeout": timeout, "max_retries": retries}
    request_options = {"model": os.getenv("DEEPSEEK_MODEL", "").strip() or DEFAULT_MODEL,
                       "max_tokens": budget, "extra_body": {"thinking": {"type": "disabled"}}}
    return client_options, request_options

def make_client() -> tuple[Any, dict[str, Any]]:
    try:
        from openai import OpenAI
        options, request = load_settings()
        return OpenAI(**options), request
    except ImportError:
        raise LessonError("Install dependencies: python -m pip install -r requirements.txt") from None

def safe_api_error(exc: Exception) -> LessonError:
    status = getattr(exc, "status_code", None)
    if status in (401, 403): advice = "Check your DeepSeek key and permissions; authentication failures are not retried."
    elif status == 402: advice = "Check your DeepSeek account balance."
    elif status == 429: advice = "Check DeepSeek quota and rate limits."
    elif status in (400, 404, 422): advice = "Check the DeepSeek model and request parameters."
    else: advice = "Check your network and DeepSeek service availability."
    return LessonError(f"DeepSeek request failed ({type(exc).__name__}, status={status}). {advice} No example reply was substituted.")

def completion_choice(response: Any, allow_tools: bool = False) -> Any:
    choices = getattr(response, "choices", [])
    if not choices: raise LessonError("DeepSeek returned no completion choices.")
    choice = choices[0]
    if getattr(choice.message, "refusal", None): raise LessonError("The model refused the request.")
    reason = choice.finish_reason
    if reason == "tool_calls" and allow_tools:
        if not choice.message.tool_calls: raise LessonError("Tool-call finish reason has no tool calls.")
        return choice
    if reason != "stop":
        raise LessonError(f"DeepSeek output was not completed: finish_reason={reason}. No report was delivered.")
    if getattr(choice.message, "tool_calls", None): raise LessonError("Unexpected tool calls in a final-text response.")
    if not isinstance(choice.message.content, str) or not choice.message.content.strip():
        raise LessonError("DeepSeek returned empty text. No example reply was substituted.")
    return choice

def public_response(response: Any) -> dict[str, Any]:
    # Keep visible content and tool calls; do not store hidden reasoning content.
    return {"id": response.id, "model": response.model,
            "choices": [{"finish_reason": c.finish_reason,
                         "content": c.message.content,
                         "tool_calls": [t.model_dump(exclude_none=True) for t in c.message.tool_calls or []]}
                        for c in response.choices]}

def chat_request(messages: list[dict[str, Any]], *, temperature: float | None = None,
                 json_output: bool = False, tools: list[dict[str, Any]] | None = None,
                 client: Any = None, options: dict[str, Any] | None = None,
                 output_dir: Path | None = None) -> tuple[Any, dict[str, Any]]:
    owned = client is None
    if owned: client, options = make_client()
    settings = dict(options or {})
    settings["temperature"] = 0.2 if temperature is None else temperature
    settings["messages"] = messages
    if json_output:
        if not any("json" in str(m.get("content", "")).lower() for m in messages):
            if owned: client.close()
            raise LessonError("JSON mode needs an explicit JSON instruction.")
        settings["response_format"] = {"type": "json_object"}
    if tools: settings.update(tools=tools, tool_choice="auto")
    # Request settings contain no API key, headers or client configuration.
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(**settings)
        usage = response.usage.model_dump() if response.usage else None
        metadata = {"mode": "live_deepseek", "provider": "DeepSeek", "request_id": response.id,
                    "requested_model": settings.get("model"), "model": response.model,
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                    "usage": usage, "elapsed_seconds": round(time.perf_counter() - start, 3)}
        if output_dir is not None:
            logged_settings = {**settings, "messages": [{k:v for k,v in m.items() if k != "reasoning_content"} for m in messages]}
            path = save_record(output_dir, "api_exchange", {"request": logged_settings, "response": public_response(response), "metadata": metadata})
            print("Saved API exchange:", path)
        completion_choice(response, allow_tools=bool(tools))
        return response, metadata
    except Exception as exc:
        error = exc if isinstance(exc, LessonError) else safe_api_error(exc)
        if output_dir is not None:
            logged_settings = {**settings, "messages": [{k:v for k,v in m.items() if k != "reasoning_content"} for m in messages]}
            save_record(output_dir, "api_failure", {"request": logged_settings, "status": "failed", "error": str(error)})
        raise error from None
    finally:
        if owned: client.close()

def request_text(instructions: str, input_data: Any, temperature: float | None = None,
                 *, json_output: bool = False, client: Any = None,
                 options: dict[str, Any] | None = None, output_dir: Path | None = None) -> TextResult:
    if isinstance(input_data, list):
        user_messages = input_data
    else:
        content = input_data if isinstance(input_data, str) else json.dumps(input_data, ensure_ascii=False)
        user_messages = [{"role": "user", "content": content}]
    response, metadata = chat_request([{"role": "system", "content": instructions}, *user_messages],
        temperature=temperature, json_output=json_output, client=client, options=options, output_dir=output_dir)
    return TextResult(completion_choice(response).message.content, metadata)
