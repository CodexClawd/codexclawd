# SKILL.md — NeuroSec Technical Modules

## Module 1: Secret Scanner

### Purpose
Detect exposed secrets, credentials, and sensitive tokens in files and git history.

### Capabilities

#### Entropy Analysis
```python
# Shannon entropy calculation
# Flag strings with entropy >4.5 (high randomness = potential secret)
def calculate_entropy(string):
    import math
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy
```

#### Known Pattern Detection
| Pattern | Regex | Severity |
|---------|-------|----------|
| AWS Access Key | `AKIA[0-9A-Z]{16}` | CRITICAL |
| AWS Secret Key | `[0-9a-zA-Z/+]{40}` (contextual) | CRITICAL |
| GitHub Token | `gh[pousr]_[A-Za-z0-9_]{36,}` | CRITICAL |
| GitHub Classic | `ghp_[a-zA-Z0-9]{36}` | CRITICAL |
| Slack Token | `xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}` | CRITICAL |
| Slack Webhook | `https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{10,}/[a-zA-Z0-9_]{24}` | HIGH |
| Generic API Key | `[aA][pP][iI][_-]?[kK][eE][yY][\s]*[=:]+[\s]*['"][a-zA-Z0-9]{16,}['"]` | HIGH |
| Private Key PEM | `-----BEGIN (RSA \|EC \|OPENSSH \|PGP )?PRIVATE KEY-----` | CRITICAL |
| Database URL | `(postgres\|mysql\|mongodb\|redis)://[^:]+:[^@]+@` | CRITICAL |
| JWT Token | `eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*` | MEDIUM |
| Bearer Token | `[Bb]earer\s+[a-zA-Z0-9_\-\.=]+` | MEDIUM |

#### Git History Scanning
```bash
# Scan git history for secrets
git log --all --full-history --pretty=format:'%H' | \
  while read commit; do
    git show $commit --no-patch --format='%H %an %ae %ad'
    git show $commit -p | grep -E '(AKIA|ghp_|xoxb-|-----BEGIN)'
  done
```

#### Scan Targets
- Files modified since last scan (mtime comparison)
- All text files in workspace (Deep Audit)
- Git commit messages and diffs
- Environment files (.env, .env.local, .env.production)
- Configuration files (config.json, secrets.yaml)
- Source code files (contextual scanning for embedded secrets)

#### Output
- Alert with secret type, location, partial redaction
- Entropy score for high-entropy strings
- Git commit hash if found in history

---

## Module 2: Permission Auditor

### Purpose
Monitor file permissions and detect dangerous configurations.

### Capabilities

#### Critical File Permission Baselines
| File Pattern | Expected Mode | Severity if Violated |
|--------------|---------------|----------------------|
| `~/.ssh/*` | 600 | CRITICAL |
| `~/.ssh/` directory | 700 | HIGH |
| `~/.env*` | 600 | CRITICAL |
| `~/.aws/credentials` | 600 | CRITICAL |
| `~/.docker/config.json` | 600 | HIGH |
| `*.pem` | 600 | CRITICAL |
| `*.key` | 600 | CRITICAL |
| `id_rsa*` | 600 | CRITICAL |
| `.htpasswd` | 600 | HIGH |

#### Dangerous Permission Detection
```bash
# Find world-writable files
find /workspace -type f -perm -002

# Find SUID/SGID binaries
find /workspace -type f \( -perm -4000 -o -perm -2000 \)

# Find group-writable sensitive files
find /workspace -type f -perm -020

# Find files with no owner
find /workspace -type f -nouser
```

#### SSH Directory Audit
```bash
# Check SSH directory permissions
ls -la ~/.ssh/
# Expected: drwx------ (700) for directory
# Expected: -rw------- (600) for private keys
# Expected: -rw-r--r-- (644) for public keys
```

#### Baseline Comparison
```python
# Compare current permissions to baseline
def audit_permissions(current, baseline):
    deviations = []
    for filepath, current_mode in current.items():
        expected_mode = baseline.get(filepath)
        if expected_mode and current_mode != expected_mode:
            deviations.append({
                'file': filepath,
                'current': current_mode,
                'expected': expected_mode
            })
    return deviations
```

#### Output
- Alert with file path, current mode, expected mode
- Risk assessment based on file type
- Recommended chmod command

---

## Module 3: Network Monitor

### Purpose
Detect network exposure, unexpected listeners, and communication anomalies.

### Capabilities

#### Listening Port Detection
```bash
# Capture listening ports
netstat -tlnp 2>/dev/null || ss -tlnp

# Output format: Proto Recv-Q Send-Q Local Address State PID/Program
# 0.0.0.0:* = binding all interfaces (HIGH risk)
# 127.0.0.1:* = localhost only (acceptable)
# 10.0.0.x:* = private network (MEDIUM risk)
```

#### Binding Address Risk Matrix
| Bind Address | Risk Level | Notes |
|--------------|------------|-------|
| `0.0.0.0` | HIGH | Accessible from all interfaces |
| `::` | HIGH | IPv6 all interfaces |
| `127.0.0.1` | INFO | Localhost only (acceptable) |
| `10.x.x.x` | MEDIUM | Private network |
| `172.16-31.x.x` | MEDIUM | Private network |
| `192.168.x.x` | MEDIUM | Private network |

#### Docker Exposure Check
```bash
# Check for Docker socket access
test -S /var/run/docker.sock && ls -la /var/run/docker.sock

# Expected: srw-rw---- 1 root docker
# World-accessible Docker socket = CRITICAL

# Check container runtime exposure
curl -s --unix-socket /var/run/docker.sock http://localhost/containers/json
```

#### Connection Tracking
```bash
# Active connections (read-only)
netstat -tn 2>/dev/null || ss -tn

# ESTABLISHED connections to external IPs
# Flag connections to unexpected countries/TOR exit nodes
```

#### Baseline Deviation Detection
```python
# Compare current listeners to baseline
def check_listeners(current_listeners, baseline):
    alerts = []
    for listener in current_listeners:
        if listener not in baseline:
            alerts.append({
                'port': listener.port,
                'bind': listener.address,
                'process': listener.process,
                'status': 'NEW_LISTENER'
            })
    return alerts
```

#### Output
- Alert with port, bind address, process name
- Risk level based on binding address
- Recommended remediation (bind to 127.0.0.1)

---

## Module 4: Dependency Checker

### Purpose
Audit package manifests for supply chain risks and security issues.

### Capabilities

#### Manifest Parsing
| Ecosystem | File | Lockfile |
|-----------|------|----------|
| Node.js | `package.json` | `package-lock.json`, `yarn.lock` |
| Python | `requirements.txt`, `pyproject.toml` | `poetry.lock`, `Pipfile.lock` |
| Rust | `Cargo.toml` | `Cargo.lock` |
| Go | `go.mod` | `go.sum` |
| Ruby | `Gemfile` | `Gemfile.lock` |
| Java | `pom.xml` | N/A (embedded) |
| PHP | `composer.json` | `composer.lock` |

#### Lockfile Verification
```bash
# Check lockfile existence
find /workspace -name "package-lock.json" -o -name "yarn.lock" -o -name "poetry.lock"

# Verify lockfile is up-to-date
# (Compare hash of manifest with hash in lockfile)
```

#### Unpinned Version Detection
```python
# Dangerous version patterns
dangerous_patterns = [
    r'^\^',      # Caret (^1.0.0) - allows minor updates
    r'^~',       # Tilde (~1.0.0) - allows patch updates
    r'>=',       # Greater than or equal
    r'>',        # Greater than
    r'latest',   # Latest tag
    r'\*',       # Wildcard
    r'x\.x\.x',  # Wildcard versions
]

def check_pinned(version):
    for pattern in dangerous_patterns:
        if re.match(pattern, version):
            return False  # Not pinned
    return True  # Pinned (exact version)
```

#### Git URL Detection
```python
# Detect dependencies from git repositories
git_url_patterns = [
    r'git\+https?://',
    r'git@github\.com:',
    r'github:[^/]+/[^/]+',
    r'^git://',
]

# Risk: No integrity verification, mutable refs
```

#### Local Path Detection
```python
# Detect local path dependencies
local_path_patterns = [
    r'^file:',
    r'^\.\./',
    r'^\.\/',
    r'^[a-zA-Z]:',  # Windows paths
]

# Risk: Non-portable, potential path traversal
```

#### Output
- Alert with manifest file, dependency name
- Risk type (unpinned, git URL, local path)
- Recommended remediation (exact version, registry package)

---

## Module 5: Process Watcher

### Purpose
Monitor running processes for suspicious activity and resource abuse.

### Capabilities

#### Process Tree Capture
```bash
# Capture process tree with relationships
ps auxf

# Key fields: USER, PID, %CPU, %MEM, COMMAND
```

#### Suspicious Pattern Detection
| Pattern | Risk | Description |
|---------|------|-------------|
| `/bin/sh -i` | EMERGENCY | Interactive shell (reverse shell) |
| `nc -e /bin/sh` | EMERGENCY | Netcat backdoor |
| `python.*pty.spawn` | HIGH | PTY upgrade technique |
| `socat.*exec` | HIGH | Socat backdoor |
| `/dev/tcp/` | EMERGENCY | Bash network redirection |
| `bash -c.*base64` | HIGH | Encoded payload |
| `curl.*\|.*bash` | HIGH | Pipe to shell |
| `wget.*\|.*sh` | HIGH | Pipe to shell |
| `perl.*-e.*socket` | HIGH | Perl reverse shell |
| `ruby.*-rsocket` | HIGH | Ruby reverse shell |

#### Resource Abuse Detection
```bash
# High CPU processes (>80% for >60 seconds)
ps aux --sort=-%cpu | head -10

# High memory processes
ps aux --sort=-%mem | head -10

# Processes in temporary directories
ls -la /proc/*/cwd 2>/dev/null | grep -E '/tmp\|/dev/shm\|/var/tmp'
```

#### Network-Enabled Process Detection
```bash
# Processes with network connections
lsof -i 2>/dev/null | grep -v COMMAND

# Processes listening on ports
ss -tnlp 2>/dev/null
```

#### Shell Process Detection
```bash
# Shell processes without TTY
ps aux | grep -E 'bash\|sh\|zsh\|fish' | grep -v 'tty'

# Suspicious: Shell without terminal = potential backdoor
```

#### Output
- Alert with PID, command, parent process
- Risk level based on pattern match
- Recommended action (investigate, terminate)

---

## Module 6: Alert Writer

### Purpose
Format and write alerts to filesystem with atomic guarantees.

### Capabilities

#### Alert Formatting
- YAML frontmatter generation
- Content redaction for secrets
- Markdown body formatting
- SHA256 digest calculation

#### Atomic Write Protocol
```python
def write_alert_atomic(alert_content, filepath):
    """
    Atomic write using temp file + rename.
    Prevents partial/corrupted alerts.
    """
    import tempfile
    import os
    
    # Create temp file in same directory
    temp_fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(filepath),
        prefix='.tmp-alert-'
    )
    
    try:
        # Write content
        with os.fdopen(temp_fd, 'w') as f:
            f.write(alert_content)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        os.rename(temp_path, filepath)
        
    except Exception as e:
        # Cleanup on failure
        os.unlink(temp_path)
        raise e
```

#### Fallback to stdout
```python
def write_alert(alert_content, filepath):
    """
    Write alert with fallback to stdout on failure.
    """
    try:
        write_alert_atomic(alert_content, filepath)
    except Exception as e:
        # Fallback: output to stdout for capture
        print("--- ALERT_WRITE_FAILED ---")
        print(f"Target: {filepath}")
        print(f"Error: {e}")
        print("--- ALERT CONTENT ---")
        print(alert_content)
        print("--- END ALERT ---")
```

#### Content Redaction
```python
def redact_secret(content, secret_type):
    """
    Redact sensitive content while preserving structure.
    """
    redaction_patterns = {
        'aws_key': (r'(AKIA[0-9A-Z]{16})', r'\1<SECRET_KEY>'),
        'github_token': (r'(ghp_[a-zA-Z0-9]{36})', r'\1<SECRET_KEY>'),
        'generic': (r'([a-zA-Z0-9]{8})[a-zA-Z0-9]{20,}([a-zA-Z0-9]{8})', r'\1<SECRET>\2'),
    }
    
    pattern, replacement = redaction_patterns.get(secret_type, redaction_patterns['generic'])
    return re.sub(pattern, replacement, content)
```

#### Alert Deduplication
```python
def is_duplicate(alert_key, known_alerts, window_seconds=3600):
    """
    Check if alert is duplicate within time window.
    """
    import time
    import hashlib
    
    # Generate unique key
    alert_hash = hashlib.sha256(alert_key.encode()).hexdigest()[:16]
    
    current_time = time.time()
    
    if alert_hash in known_alerts:
        last_seen = known_alerts[alert_hash]
        if current_time - last_seen < window_seconds:
            return True  # Duplicate
    
    # Update timestamp
    known_alerts[alert_hash] = current_time
    return False
```

#### Digest Generation
```python
def generate_daily_digest(alerts, date):
    """
    Generate daily digest from alert list.
    """
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for alert in alerts:
        severity_counts[alert.severity] += 1
    
    digest = f"""---
digest_date: "{date}"
alert_count: {len(alerts)}
critical: {severity_counts['CRITICAL']}
high: {severity_counts['HIGH']}
medium: {severity_counts['MEDIUM']}
low: {severity_counts['LOW']}
---

# NeuroSec Daily Digest — {date}

## Executive Summary

{len(alerts)} alerts generated across {sum(1 for c in severity_counts.values() if c > 0)} severity levels.
...
"""
    return digest
```

#### Output
- Atomic file write to alerts/ directory
- Fallback stdout output on failure
- Deduplication tracking
- Digest generation for periodic summaries

---

## Module Integration

### Execution Flow
```
1. Trigger (Heartbeat/PostWrite/DeepAudit)
   ↓
2. Secret Scanner → Alerts
3. Permission Auditor → Alerts
4. Network Monitor → Alerts
5. Dependency Checker → Alerts (DeepAudit only)
6. Process Watcher → Alerts
   ↓
7. Alert Writer → File output
   ↓
8. Update alert_history.log
```

### Resource Management
- Each module has independent timeout
- Sequential execution (single-threaded)
- Partial results on timeout
- Memory limit enforced per module

---

_Last updated: 2026-02-08
Version: NeuroSec v1.0
Classification: INTERNAL USE ONLY_
