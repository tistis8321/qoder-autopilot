"""
Qoder Autopilot — Logger
==========================
Colored, structured logging with per-account context tags for parallel mode.
Zero extra dependencies — uses ANSI escape codes directly.

Usage:
    from qoder_autopilot.logger import log, log_ok, log_err, log_step, log_warn
    from qoder_autopilot.logger import set_account_tag, get_account_tag
"""

import contextvars
import sys
from datetime import datetime

# ── ANSI Colors ───────────────────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_COLORS = {
    "reset":  _RESET,
    "bold":   _BOLD,
    "dim":    _DIM,
    "red":    "\033[31m",
    "green":  "\033[32m",
    "yellow": "\033[33m",
    "blue":   "\033[34m",
    "cyan":   "\033[36m",
    "white":  "\033[37m",
    "gray":   "\033[90m",
}

# Level → (color, label)
_LEVELS: dict[str, tuple[str, str]] = {
    "DEBUG": ("gray",   "DBG"),
    "INFO":  ("white",  "INF"),
    "OK":    ("green",  " OK"),
    "WARN":  ("yellow", "WRN"),
    "ERROR": ("red",    "ERR"),
    "STEP":  ("cyan",   "STP"),
}

# Context variable for parallel mode account labeling
_acct_tag: contextvars.ContextVar[str] = contextvars.ContextVar(
    "acct_tag", default=""
)

# Whether to use colors (auto-detect terminal)
_use_colors: bool = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(color: str, text: str) -> str:
    """Wrap text in ANSI color codes (no-op if colors disabled)."""
    if not _use_colors:
        return text
    return f"{_COLORS.get(color, '')}{text}{_RESET}"


# ── Public API ────────────────────────────────────────────────────────────

def log(
    msg: str,
    level: str = "INFO",
    acct: str | None = None,
) -> None:
    """Log a message with timestamp, level badge, and optional account tag.

    Args:
        msg: The message to log.
        level: Log level (DEBUG, INFO, OK, WARN, ERROR, STEP).
        acct: Override account tag for this message.
    """
    ts = datetime.now().strftime("%H:%M:%S")
    color, label = _LEVELS.get(level, ("white", level[:3]))

    tag = acct if acct else _acct_tag.get()
    tag_str = _c("bold", f"[{tag}]") + " " if tag else ""

    timestamp = _c("gray", ts)
    badge = _c(color, f"{_BOLD}{label}")
    message = _c(color, msg) if level in ("ERROR", "WARN") else msg

    print(f"{timestamp} {badge} {tag_str}{message}")


def log_ok(msg: str) -> None:
    """Log a success message (green ✅)."""
    log(f"✅ {msg}", "OK")


def log_err(msg: str) -> None:
    """Log an error message (red ❌)."""
    log(f"❌ {msg}", "ERROR")


def log_warn(msg: str) -> None:
    """Log a warning message (yellow ⚠️)."""
    log(f"⚠️  {msg}", "WARN")


def log_step(step: int, total: int, msg: str) -> None:
    """Log a step in a multi-step process (cyan 📋)."""
    log(f"📋 Step {step}/{total}: {msg}", "STEP")


def log_debug(msg: str) -> None:
    """Log a debug message (gray, dim)."""
    log(msg, "DEBUG")


def set_account_tag(tag: str) -> None:
    """Set the account tag for all subsequent log calls in this async context."""
    _acct_tag.set(tag)


def get_account_tag() -> str:
    """Get the current account tag."""
    return _acct_tag.get()
