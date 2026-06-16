"""
Qoder Autopilot — Credential Storage
======================================
Save and load registered account credentials to/from JSON.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config
from .logger import log


def save_creds(data: dict[str, Any], path: Path | None = None) -> None:
    """Append account credentials to the JSON storage file."""
    path = path or config.CREDENTIALS_FILE
    accounts: list[dict] = []
    if path.exists():
        try:
            accounts = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            accounts = []

    accounts.append({
        **data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    path.write_text(json.dumps(accounts, indent=2))
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
