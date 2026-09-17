import json
import time
from datetime import datetime, timezone
from pathlib import Path
from .ssh import test_credentials

RESULTS = Path(__file__).resolve().parent.parent / "results"
RESULTS.mkdir(exist_ok=True)

def audit_passwords(host, port, username, passwords, timeout, delay, max_attempts, on_attempt):
    return _audit(
        host, port, username, passwords, timeout, delay, max_attempts,
        lambda item: item, on_attempt
    )

def audit_usernames(host, port, password, usernames, timeout, delay, max_attempts, on_attempt):
    return _audit(
        host, port, None, usernames, timeout, delay, max_attempts,
        lambda item: (item, password), on_attempt, username_mode=True
    )

def _audit(host, port, fixed_username, items, timeout, delay, max_attempts, pair_builder, on_attempt, username_mode=False):
    started = time.time()
    limit = len(items) if not max_attempts else min(max_attempts, len(items))
    result = {"status": "not_found", "attempts": 0, "elapsed": 0, "username": None, "password": None}

    for idx, item in enumerate(items[:limit], 1):
        username, password = (item, None)
        if username_mode:
            username, password = pair_builder(item)
        else:
            username, password = fixed_username, pair_builder(item)

        status, error = test_credentials(host, port, username, password, timeout)
        result["attempts"] = idx
        result["elapsed"] = time.time() - started
        on_attempt(idx, limit, username, password, status, error)

        if status == "success":
            result.update(status="success", username=username, password=password)
            break
        if status == "error":
            result.update(status="error", error=error)
            break

        if delay:
            time.sleep(delay)

    save_result(host, port, result)
    return result

def save_result(host, port, result):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": f"{host}:{port}",
        **result,
    }
    filename = RESULTS / f"result_{int(time.time() * 1000)}.json"
    filename.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def recent_results():
    return sorted(RESULTS.glob("result_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
