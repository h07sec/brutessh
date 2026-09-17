import json
import time
from datetime import datetime, timezone
from pathlib import Path
from .ssh import test_credentials

RESULTS = Path(__file__).resolve().parent.parent / "results"
RESULTS.mkdir(exist_ok=True)

def audit_passwords(host, port, username, passwords, timeout, delay, max_attempts, on_attempt):
    return _audit(host, port, passwords, timeout, delay, max_attempts,
                  on_attempt, fixed_username=username)

def audit_usernames(host, port, password, usernames, timeout, delay, max_attempts, on_attempt):
    return _audit(host, port, usernames, timeout, delay, max_attempts,
                  on_attempt, fixed_password=password)

def _audit(host, port, items, timeout, delay, max_attempts, on_attempt,
           fixed_username=None, fixed_password=None):
    started = time.time()
    limit = min(max_attempts, len(items)) if max_attempts else len(items)
    result = {"status": "not_found", "attempts": 0, "elapsed": 0,
              "username": None, "password": None}

    for idx, item in enumerate(items[:limit], 1):
        username = fixed_username if fixed_username is not None else item
        password = item if fixed_username is not None else fixed_password
        status, error = test_credentials(host, port, username, password, timeout)
        result["attempts"] = idx
        result["elapsed"] = time.time() - started
        on_attempt(idx, limit, username, status, error)

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
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(),
               "target": f"{host}:{port}", **result}
    (RESULTS / f"result_{int(time.time()*1000)}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")

def recent_results():
    return sorted(RESULTS.glob("result_*.json"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
