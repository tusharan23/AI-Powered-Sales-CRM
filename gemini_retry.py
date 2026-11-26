"""Bounded retries and model failover for Gemini text generation."""
import time

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"
RETRYABLE_CODES = {500, 502, 503, 504}


def error_code(exc):
    try:
        return int(getattr(exc, "code", None))
    except (TypeError, ValueError):
        status = getattr(exc, "status", None)
        return {"UNAVAILABLE": 503, "DEADLINE_EXCEEDED": 504,
                "INTERNAL": 500, "NOT_FOUND": 404,
                "RESOURCE_EXHAUSTED": 429}.get(str(status))


def generate_with_retry(client, contents, *, notify=None, sleep=time.sleep):
    """Try the primary model up to 3 times, then the fallback up to twice.

    Only transient server errors are retried. A missing primary model
    switches immediately to the fallback. Auth and quota errors propagate.
    """
    models = ((PRIMARY_MODEL, 3), (FALLBACK_MODEL, 2))
    for model_index, (model, attempts) in enumerate(models):
        for attempt in range(attempts):
            try:
                return client.models.generate_content(model=model, contents=contents)
            except Exception as exc:
                code = error_code(exc)
                is_primary = model_index == 0
                if code == 404 and is_primary:
                    break
                if code not in RETRYABLE_CODES:
                    raise
                if attempt + 1 < attempts:
                    delay = 2 ** attempt
                    if notify:
                        notify(f"AI service busy. Retrying in {delay} second(s)...")
                    sleep(delay)
                elif is_primary:
                    break
                else:
                    raise
        if model_index == 0 and notify:
            notify("Switching to the backup Gemini model...")
