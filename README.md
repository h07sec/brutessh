# SSH Auditor

A polished terminal UI for authorized SSH credential auditing of systems you own or are explicitly permitted to test.

## Features

- Interactive terminal dashboard
- Password audit: fixed username + password wordlist
- Username audit: fixed password + username wordlist
- SSH connection test
- Configurable host, port, timeout, delay and attempt limit
- Animated progress display
- Stops on successful authentication
- Clean handling of connection/network errors
- Local JSON result history

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

On Windows:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Use only against systems you own or have explicit permission to test.
