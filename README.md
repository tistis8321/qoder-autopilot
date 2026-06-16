# 🤖 Qoder Autopilot

Automated [Qoder](https://qoder.com) account registration with anti-detect browser, multi-strategy captcha solving, and [9Router](https://github.com/nicepkg/9router) OAuth device token integration.

> Register Qoder accounts → solve captchas → verify OTP → auto-connect to 9Router. All in one command.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Camoufox](https://img.shields.io/badge/browser-Camoufox-orange.svg)](https://camoufox.com/)

---

## ✨ Features

- **🦊 Anti-detect Browser** — Uses [Camoufox](https://camoufox.com/) (stealth Firefox fork) with C++-level fingerprinting to bypass bot detection
- **🧩 Multi-strategy Captcha Solving**
  - AI Vision (Gemini/GPT via OpenAI-compatible API)
  - OpenCV (4-method computer vision: brightness, edge, template match, SQDIFF)
  - Manual mode (pause and solve it yourself)
- **📧 Auto Email + OTP** — Generates temp email via Cloudflare Worker, auto-extracts OTP
- **🔐 OAuth Device Flow** — PKCE-based device token flow (reverse-engineered from 9Router)
- **🔌 9Router Auto-Connect** — Inserts device tokens directly into 9Router's SQLite database
- **⚡ Parallel Mode** — Register multiple accounts concurrently with 2×2 window grid tiling
- **🪟 macOS Grid Tiling** — Auto-arranges browser windows in a 2×2 grid via AppleScript

## 📦 Installation

### From source (recommended)

```bash
git clone https://github.com/Daivageralda/qoder-autopilot.git
cd qoder-autopilot

# Basic install (manual captcha only)
pip install -e .

# With AI captcha solver
pip install -e ".[captcha]"

# Full install + dev tools
pip install -e ".[dev]"
```

### Via pip (coming soon)

```bash
pip install qoder-autopilot
```

### Post-install

```bash
# Download Camoufox browser binary
python -m camoufox fetch

# Download Playwright browsers (if needed)
playwright install firefox
```

## 🚀 Quick Start

### 1. Configure

```bash
cp .env.example .env
# Edit .env with your settings (temp mail worker URL, AI API key, etc.)
```

### 2. Run

```bash
# Single account, manual captcha (most reliable)
qoder-autopilot --manual-captcha

# 5 accounts in parallel, manual captcha
qoder-autopilot -n 5 --manual-captcha --parallel

# Headless mode (requires AI captcha solver configured)
qoder-autopilot -n 3

# Just register, skip 9Router connection
qoder-autopilot --manual-captcha --no-oauth
```

### 3. Or use as a library

```python
import asyncio
from qoder_autopilot import run_one

async def main():
    result = await run_one(
        headless=False,
        manual_captcha=True,
        use_oauth=True,
    )
    if result:
        print(f"Registered: {result['email']}")

asyncio.run(main())
```

## 📋 CLI Options

| Flag | Description |
|---|---|
| `-n`, `--count N` | Number of accounts to create (default: 1) |
| `--no-headless` | Show browser windows |
| `--no-oauth` | Skip 9Router OAuth flow, just register |
| `--manual-captcha` | Pause for manual captcha solving (forces non-headless) |
| `--parallel` | Run all accounts concurrently |
| `--delay N` | Delay between sequential accounts (default: 30s) |

## ⚙️ Configuration

All settings via environment variables or `.env` file:

| Variable | Description | Default |
|---|---|---|
| `QODER_WORKER_URL` | Cloudflare Worker URL for temp mail | *(required)* |
| `QODER_AI_API_KEY` | API key for AI captcha solver | *(empty = manual mode)* |
| `QODER_AI_BASE_URL` | OpenAI-compatible API base URL | `https://ai.sumopod.com/v1` |
| `QODE...` | AI model name | `gemini/gemini-2.5-flash` |
| `QODER_NINEROUTER_DB` | Path to 9Router SQLite database | `~/.9router/db/data.sqlite` |
| `QODER_NINEROUTER_URL` | 9Router dashboard URL | `http://localhost:20128` |

## 🏗️ Architecture

```
qoder-autopilot/
├── src/qoder_autopilot/
│   ├── cli.py              # CLI entry point
│   ├── config.py           # Environment configuration
│   ├── register.py         # Main registration flow
│   ├── temp_mail.py        # Temp email client
│   ├── oauth.py            # PKCE device auth flow
│   ├── otp.py              # Email OTP extraction
│   ├── identity.py         # Random identity generation
│   ├── credentials.py      # Account credential storage
│   ├── ninerouter.py       # 9Router SQLite integration
│   ├── logger.py           # Context-aware logging
│   ├── browser/
│   │   ├── camoufox.py     # Anti-detect browser launcher
│   │   └── window_tiler.py # macOS window grid positioning
│   └── captcha/
│       ├── solver.py       # Orchestrator (AI → OpenCV → manual)
│       ├── ai_vision.py    # AI vision gap detection
│       ├── opencv_detect.py# 4-method OpenCV detection
│       ├── slider.py       # Human-like mouse movement
│       └── manual.py       # Manual solve pause/poll
```

## 📄 License

MIT — see [LICENSE](LICENSE)

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Use responsibly and in accordance with applicable terms of service.
