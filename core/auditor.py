import json
import time
from datetime import datetime, timezone
from pathlib import Path
from .ssh import test_credentials

RESULTS = Path(__file__).resolve().parent.parent / "results"
RESULTS.mkdir(exist_ok=True)


def audit_passwords(host, port, username, passwords, timeout, delay, max_attempts, on_attempt):
    return _audit_pairs(
        host, port, ((username, password) for password in passwords),
        timeout, delay, max_attempts, on_attempt
    )


def audit_usernames(host, port, password, usernames, timeout, delay, max_attempts, on_attempt):
    return _audit_pairs(
        host, port, ((username, password) for username in usernames),
        timeout, delay, max_attempts, on_attempt
    )


def audit_ssh(host, port, username, usernames, passwords, timeout, delay, max_attempts, on_attempt):
    """Run an authorized SSH credential audit.

    A supplied username is tested against every password. If username is empty,
    every username/password combination is tested.
    """
    if username:
        pairs = ((username, password) for password in passwords)
    else:
        pairs = ((user, password) for user in usernames for password in passwords)
    return _audit_pairs(host, port, pairs, timeout, delay, max_attempts, on_attempt)


def _audit_pairs(host, port, pairs, timeout, delay, max_attempts, on_attempt):
    started = time.time()
    limit = max_attempts if max_attempts > 0 else None
    result = {
        "status": "not_found",
        "attempts": 0,
        "elapsed": 0,
        "username": None,
        "password": None,
        "connection_errors": 0,
    }

    # A temporary SSH banner/transport problem should not kill the whole audit.
    # Stop only after several consecutive transport failures, which usually means
    # the target is unavailable or port 22 is not actually serving SSH.
    consecutive_connection_errors = 0
    max_consecutive_connection_errors = 3

    for username, password in pairs:
        if limit is not None and result["attempts"] >= limit:
            break

        status, error = test_credentials(host, port, username, password, timeout)
        result["attempts"] += 1
        result["elapsed"] = time.time() - started

        if status == "error":
            result["connection_errors"] += 1
            consecutive_connection_errors += 1
            on_attempt(result["attempts"], username, status, error)

            if consecutive_connection_errors >= max_consecutive_connection_errors:
                result.update(
                    status="error",
                    error=(
                        f"SSH connection failed {max_consecutive_connection_errors} "
                        f"times consecutively. Last error: {error}"
                    ),
                )
                break

            # Give a server that is throttling/resetting connections a chance
            # to recover before the next candidate.
            if delay:
                time.sleep(delay)
            continue

        # A successful authentication or a normal authentication rejection
        # means the SSH service is responding, so reset the transport-error run.
        consecutive_connection_errors = 0
        on_attempt(result["attempts"], username, status, error)

        if status == "success":
            result.update(status="success", username=username, password=password)
            break

        if delay:
            time.sleep(delay)

    result["elapsed"] = time.time() - started
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
