"""
Qoder Autopilot — Doctor (Health Check)
=========================================
Verify all dependencies and configurations are working correctly
before running registrations.

Usage:
    qoder-autopilot doctor

Checks:
    1. Python version
    2. Camoufox browser availability
    3. Node.js + Wrangler (for deploy)
    4. Temp mail worker connectivity
    5. 9Router DB availability
    6. Relay server connectivity (if configured)
    7. AI captcha solver (if configured)
"""

import os
import shutil
import subprocess
import sys

from . import config

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
NC = "\033[0m"

_pass = 0
_fail = 0
_warn = 0


def _ok(msg: str) -> None:
    global _pass  # noqa: PLW0603
    _pass += 1
    print(f"  {GREEN}✅{NC} {msg}")


def _fail(msg: str) -> None:
    global _fail  # noqa: PLW0603
    _fail += 1
    print(f"  {RED}❌{NC} {msg}")


def _warn(msg: str) -> None:
    global _warn  # noqa: PLW0603
    _warn += 1
    print(f"  {YELLOW}⚠️{NC}  {msg}")


def _info(msg: str) -> None:
    print(f"  {BOLD}ℹ️{NC}  {msg}")


def run_doctor() -> None:
    """Run all health checks and print results."""
    global _pass, _fail, _warn  # noqa: PLW0603
    _pass = _fail = _warn = 0

    print()
    print(f"  {BOLD}🩺 qoder-autopilot doctor{NC}")
    print(f"  {'─' * 44}")
    print()

    # 1. Python version
    print(f"  {BOLD}[1/7] Python{NC}")
    ver = sys.version_info
    ver_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    if ver >= (3, 10):
        _ok(f"Python {ver_str} (≥ 3.10 required)")
    else:
        _fail(f"Python {ver_str} — need ≥ 3.10")
    print()

    # 2. Camoufox browser
    print(f"  {BOLD}[2/7] Camoufox Browser{NC}")
    try:
        import camoufox  # noqa: F401

        _ok(f"camoufox {getattr(camoufox, '__version__', 'installed')}")
    except ImportError:
        _fail("camoufox not installed — pip install camoufox")

    # Check if browser binaries are fetched
    try:
        result = subprocess.run(
            [sys.executable, "-m", "camoufox", "fetch", "--check"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            _ok("Browser binaries downloaded")
        else:
            _warn("Browser binaries not fetched — run: python -m camoufox fetch")
    except Exception:
        _warn("Could not verify browser binaries — run: python -m camoufox fetch")
    print()

    # 3. Node.js + Wrangler
    print(f"  {BOLD}[3/7] Node.js + Wrangler{NC}")
    node = shutil.which("node")
    if node:
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=5
            )
            _ok(f"Node.js {result.stdout.strip()}")
        except Exception:
            _warn("Node.js found but version check failed")
    else:
        _warn("Node.js not found (needed for deploy)")

    wrangler = shutil.which("wrangler") or shutil.which("npx")
    if wrangler:
        _ok("Wrangler/npx available")
    else:
        _warn("Wrangler not found (needed for deploy)")
    print()

    # 4. Temp mail worker connectivity
    print(f"  {BOLD}[4/7] Temp Mail Worker{NC}")
    worker_url = config.settings.worker_url
    if not worker_url:
        _fail("No worker URL configured")
    else:
        _info(f"URL: {worker_url}")
        try:
            import requests

            resp = requests.get(f"{worker_url}/api/health", timeout=10)
            if resp.status_code == 200:
                _ok(f"Worker reachable (HTTP {resp.status_code})")
            else:
                _warn(f"Worker returned HTTP {resp.status_code}")
        except ImportError:
            _fail("requests not installed")
        except Exception as e:
            _fail(f"Worker unreachable: {e}")
    print()

    # 5. 9Router DB
    print(f"  {BOLD}[5/7] 9Router Database{NC}")
    db_path = os.path.expanduser(config.settings.ninerouter_db)
    _info(f"Path: {db_path}")
    if os.path.exists(db_path):
        _ok("Database file exists")
        # Check if writable
        if os.access(db_path, os.W_OK):
            _ok("Database is writable")
        else:
            _warn("Database is read-only")
    else:
        _warn("Database not found (9Router insert will be skipped)")
    print()

    # 6. Relay server
    print(f"  {BOLD}[6/7] Relay Server{NC}")
    relay_url = config.settings.ninerouter_relay_url
    relay_token = config.settings.ninerouter_relay_token
    if relay_url and relay_token:
        _info(f"URL: {relay_url}")
        try:
            from .relay import check_relay_connection

            if check_relay_connection(relay_url, relay_token):
                _ok("Relay server reachable")
            else:
                _fail("Relay server unreachable")
        except ImportError:
            _warn("requests not installed — cannot test relay")
        except Exception as e:
            _fail(f"Relay check failed: {e}")
    else:
        _info("Relay not configured (using local 9Router or skipping)")
    print()

    # 7. AI captcha solver
    print(f"  {BOLD}[7/7] AI Captcha Solver{NC}")
    api_key = config.AI_API_KEY
    if api_key:
        _ok(f"API key configured (model: {config.AI_MODEL})")
        _info(f"Base URL: {config.AI_BASE_URL}")
        # Quick connectivity test
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=config.AI_BASE_URL)
            client.models.list()
            _ok("AI API reachable")
        except ImportError:
            _warn("openai not installed — pip install qoder-autopilot[captcha]")
        except Exception as e:
            _warn(f"AI API test failed: {e}")
    else:
        _info("AI captcha not configured (manual/opencv mode only)")
    print()

    # Summary
    print(f"  {'─' * 44}")
    print(f"  {GREEN}{_pass} passed{NC}  {YELLOW}{_warn} warnings{NC}  {RED}{_fail} failed{NC}")
    print()

    if _fail > 0:
        print(f"  {RED}Some checks failed. Fix them before running registrations.{NC}")
        print()
    elif _warn > 0:
        print(f"  {YELLOW}Warnings found but core functionality should work.{NC}")
        print()
    else:
        print(f"  {GREEN}All checks passed! Ready to register. 🚀{NC}")
        print()
