import paramiko


def test_credentials(host, port, username, password, timeout):
    """Test one SSH credential pair and return (status, error).

    Status is one of: success, failed, error.
    Transport/banner/time-out problems are reported as error so the caller can
    decide whether to retry or continue the audit.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            banner_timeout=timeout,
            auth_timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        return "success", None
    except paramiko.AuthenticationException:
        return "failed", None
    except (paramiko.SSHException, OSError, TimeoutError, EOFError) as exc:
        return "error", str(exc) or exc.__class__.__name__
    finally:
        try:
            client.close()
        except Exception:
            pass
