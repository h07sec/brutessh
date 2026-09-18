# SSH Auditor v1.1

A lightweight, interactive terminal-based **SSH credential auditing tool** written in Python.

SSH Auditor is designed for **authorized security testing, penetration-testing labs, and systems you own or have explicit permission to assess**.

---

## Features

* 🔐 SSH username/password auditing
* 👤 Known-username mode
* 📋 Automatic username wordlist mode
* 🔑 Password wordlist support
* ⏱️ Configurable connection timeout
* 🕒 Configurable delay between attempts
* 🔢 Maximum-attempt limit
* 📊 Live audit progress
* ⚠️ Connection-error handling
* 💾 Automatic JSON result storage
* 🗂️ Recent-audit result viewer
* 🖥️ Interactive terminal interface
* 🐍 Python virtual-environment support

---

## How It Works

SSH Auditor supports two main auditing modes.

### 1. Known Username

If you already know the SSH username, enter it when prompted.

For example:

```text
Username: root
```

The auditor will test:

```text
root + password1
root + password2
root + password3
...
```

against the configured password wordlist.

---

### 2. Username Wordlist

If you leave the username field empty:

```text
Username: [ENTER]
```

the application automatically loads:

```text
wordlists/usernames.txt
```

It then tests username/password combinations from the configured wordlists.

For example:

```text
admin + password1
admin + password2
root + password1
root + password2
pi + password1
pi + password2
...
```

The default password list is:

```text
wordlists/passwords.txt
```

---

# Requirements

* Python 3.9+
* Network access to the authorized SSH server
* SSH server listening on the configured port
* Python dependencies listed in `requirements.txt`

The application uses **Paramiko** for SSH communication.

---

# Installation

Clone or extract the project:

```bash
cd ssh-auditor-v1.1
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it.

### Linux / macOS

```bash
source venv/bin/activate
```

### Windows

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
python3 main.py
```

On Windows, you can use:

```powershell
python main.py
```

---

# Main Menu

After starting the application, the main menu provides:

```text
[1] SSH Password Audit
[2] SSH Connection Test
[3] View Recent Results
[0] Exit
```

### SSH Password Audit

Runs the credential audit using the configured username and wordlists.

### SSH Connection Test

Tests whether the target SSH service can be reached without running the full audit.

### View Recent Results

Displays previously saved audit results.

### Exit

Closes the application.

---

# Audit Configuration

When starting an audit, the application asks for several parameters.

### Target IP / hostname

The SSH server to test.

Example:

```text
192.168.1.13
```

### SSH Port

The SSH service port.

Default:

```text
22
```

### Timeout

Maximum time allowed for an individual SSH connection.

Example:

```text
5
```

### Delay

Time to wait between connection attempts.

Example:

```text
3
```

Using a delay can reduce connection churn and help prevent the SSH server from temporarily rejecting or resetting repeated connections.

### Maximum Attempts

Controls how many credential pairs can be tested.

```text
0 = use the complete wordlist
```

For example:

```text
Maximum attempts: 5
```

limits the audit to five credential attempts.

For testing and troubleshooting, using a small limit first is recommended.

---

# Wordlists

The project includes:

```text
wordlists/
├── usernames.txt
└── passwords.txt
```

### usernames.txt

Contains candidate SSH usernames.

Example:

```text
root
admin
pi
user
```

### passwords.txt

Contains candidate passwords.

Example:

```text
password
password123
admin123
...
```

You can replace these files with wordlists appropriate for your **authorized test environment**.

---

# Project Structure

```text
ssh-auditor-v1.1/
│
├── main.py
├── requirements.txt
├── README.md
│
├── wordlists/
│   ├── usernames.txt
│   └── passwords.txt
│
├── core/
│   ├── __init__.py
│   ├── ssh.py
│   ├── auditor.py
│   └── wordlist.py
│
├── ui/
│   └── app.py
│
└── results/
    └── result_*.json
```

### `main.py`

Application entry point.

### `ui/app.py`

Contains the interactive terminal interface and user input handling.

### `core/ssh.py`

Handles individual SSH connection and authentication tests.

### `core/auditor.py`

Controls the audit process, attempt counting, delays, connection-error handling, and result storage.

### `core/wordlist.py`

Loads and processes wordlists.

### `wordlists/`

Contains username and password candidates.

### `results/`

Stores audit results as JSON files.

---

# Results

Completed audits are automatically saved in:

```text
results/
```

Each result is stored as a JSON file similar to:

```text
result_1726651234567.json
```

A result contains information such as:

```json
{
    "timestamp": "...",
    "target": "192.168.1.13:22",
    "status": "not_found",
    "attempts": 30,
    "elapsed": 15.42,
    "username": null,
    "password": null,
    "connection_errors": 0
}
```

Possible audit states include:

```text
success
not_found
error
```

A successful audit records the username and password that produced a successful authentication.

---

# Connection Errors

SSH servers may temporarily reject or reset repeated connections.

For example, the client may report:

```text
Error reading SSH protocol banner
Connection reset by peer
```

This does **not necessarily mean that SSH is offline**.

Possible causes include:

* excessive connection rate
* SSH server connection limits
* temporary connection throttling
* network interruptions
* SSH service configuration
* server-side resource limitations

If this occurs, first verify the SSH service independently:

```bash
ssh user@TARGET
```

You can also check the service with:

```bash
nmap -sV -p 22 TARGET
```

For an authorized test environment, increase the audit delay, for example:

```text
Delay: 3
```

and test with a small maximum-attempt value before running a larger audit.

---

# Troubleshooting

## Check whether SSH is running

On the target Linux system:

```bash
sudo systemctl status ssh
```

You can also inspect recent SSH logs:

```bash
sudo journalctl -u ssh.service --since "30 minutes ago"
```

On systems where the service is named differently:

```bash
sudo journalctl -u sshd.service --since "30 minutes ago"
```

---

## Check the SSH port

From the auditing machine:

```bash
nmap -sV -p 22 TARGET
```

Expected output should indicate that the port is open:

```text
22/tcp open ssh
```

---

## Test SSH manually

Before troubleshooting the auditor, test the same target with the normal SSH client:

```bash
ssh username@TARGET
```

For more detailed connection information:

```bash
ssh -vvv username@TARGET
```

This helps distinguish an SSH-server problem from an application-level problem.

---

# Recommended Testing Workflow

For a new target, don't immediately run a large audit.

Use this workflow:

```text
1. Verify the target is reachable
          ↓
2. Verify TCP/22 is open
          ↓
3. Test normal SSH manually
          ↓
4. Run SSH Auditor with a small attempt limit
          ↓
5. Increase the delay if connection errors occur
          ↓
6. Review the saved result
```

Example conservative test configuration:

```text
Target:             192.168.1.13
SSH Port:           22
Timeout:            5
Delay:              3
Maximum Attempts:   5
```

Once the connection behavior is confirmed, the test parameters can be adjusted for the authorized environment.

---

# Security & Authorization

**Use SSH Auditor only on systems you own or have explicit authorization to test.**

Testing credentials against systems without permission may violate:

* organizational security policies
* terms of service
* local laws
* computer misuse/access-control laws

You are responsible for ensuring that you have permission before performing an audit.

For learning, use a dedicated lab, virtual machine, or other system where you have explicit authorization.

---

# Disclaimer

This project is provided for **authorized security testing and educational purposes**.

The authors are not responsible for misuse, unauthorized access, service disruption, or damage resulting from use of this software.

Always obtain appropriate authorization before testing a system.

---

# License

Add your preferred open-source license here.

For example:

```text
MIT License
```

if the project is intended to be released under the MIT License.
