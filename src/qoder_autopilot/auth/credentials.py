"""
Qoder Autopilot — Credential Storage
======================================
Save and load registered account credentials to/from JSON.

Security:
    - File permissions restricted to owner-only (chmod 600)
    - File locking for concurrent writes in parallel mode
"""

import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..infra import config
from ..utils.logger import log

# Cross-platform file locking (fcntl is Unix-only)
_is_unix = sys.platform != "win32"
if _is_unix:
    import fcntl


def _lock(f):
    """Acquire exclusive file lock (no-op on Windows)."""
    if _is_unix:
        fcntl.flock(f, fcntl.LOCK_EX)


def _unlock(f):
    """Release file lock (no-op on Windows)."""
    if _is_unix:
        fcntl.flock(f, fcntl.LOCK_UN)


def save_creds(data: dict[str, Any], path: Path | None = None) -> None:
    """Append account credentials to the JSON storage file.

    Uses file locking to prevent corruption in parallel mode.
    File is saved with owner-only permissions (600).
    """
    path = path or config.CREDENTIALS_FILE

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic read-modify-write with file locking
    with open(path, "a+") as f:
        _lock(f)
        try:
            f.seek(0)
            content = f.read()
            accounts: list[dict] = []
            if content:
                try:
                    accounts = json.loads(content)
                except json.JSONDecodeError:
                    accounts = []

            accounts.append(
                {
                    **data,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            f.seek(0)
            f.truncate()
            f.write(json.dumps(accounts, indent=2))
        finally:
            _unlock(f)

    # Restrict file permissions: owner read/write only
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError:
        pass  # Windows may not support

    log(f"   💾 Saved to {path}")


def load_creds(path: Path | None = None) -> list[dict[str, Any]]:
    """Load all stored credentials from the JSON file."""
    path = path or config.CREDENTIALS_FILE
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
