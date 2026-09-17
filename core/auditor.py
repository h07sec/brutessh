import json
import time
from datetime import datetime, timezone
from pathlib import Path
from .ssh import test_credentials

RESULTS = Path(__file__).resolve().parent.parent / "results"
RESULTS.mkdir(exist_ok=True)


def audit_passwords(host, port, username, passwords, timeout, delay, max_attempts, on_attempt):
    """Test one known username against a password list."""
    return _audit_pairs(
        host, port, [(username, password) for password in passwords],
        timeout, delay, max_attempts, on_attempt
    )


def audit_usernames(host, port, password, usernames, timeout, delay, max_attempts, on_attempt):
    """Test a username list against one known password."""
    return _audit_pairs(
        host, port, [(username, password) for username in usernames],
        timeout, delay, max_attempts, on_attempt
    )


def audit_ssh(host, port, username, usernames, passwords, timeout, delay, max_attempts, on_attempt):
    """
    Main SSH brute-force audit.

    If username is supplied, test that username against every password.
    If username is blank/None, test every username/password combination.
    """
    if username:
        pairs = ((username, password) for password in passwords)
    else:
        pairs = ((user, password) for user in usernames for password in passwords)
    return _audit_pairs(host, port, pairs, timeout, delay, max_attempts, on_attempt)


def _audit_pairs(host, port, pairs, timeout, delay, max_attempts, on_attempt):
    started = time.time()
    limit = max_attempts if max_attempts else None
    result = {
        "status": "not_found",
        "attempts": 0,
        "elapsed": 0,
        "username": None,
        "password": None,
    }

    for username, password in pairs:
        if limit is not None and result["attempts"] >= limit:
            break

        status, error = test_credentials(host, port, username, password, timeout)
        result["attempts"] += 1
        result["elapsed"] = time.time() - started
        on_attempt(result["attempts"], username, status, error)

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
    (RESULTS / f"result_{int(time.time() * 1000)}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def recent_results():
    return sorted(
        RESULTS.glob("result_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
