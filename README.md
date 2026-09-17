# SSH Auditor v1.1

Interactive terminal SSH credential auditing application for authorized systems.

## Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

In Username Audit, leaving **Username wordlist** blank automatically selects:
`wordlists/usernames.txt`

In Password Audit, leaving **Password wordlist** blank automatically selects:
`wordlists/passwords.txt`

Use only against systems you own or are authorized to test.
