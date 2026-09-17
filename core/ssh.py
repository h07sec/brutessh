import paramiko

def test_credentials(host, port, username, password, timeout):
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
    except (paramiko.SSHException, OSError, TimeoutError) as exc:
        return "error", str(exc)
    finally:
        client.close()
