"""
Qoder Autopilot — Camoufox Browser Launcher
==============================================
Launch and configure Camoufox (anti-detect Firefox fork) browser instances.
Camoufox provides C++-level stealth fingerprinting to bypass bot detection.
"""

import random
from contextlib import asynccontextmanager
from typing import AsyncIterator

from ..logger import log


@asynccontextmanager
async def launch_browser(
    headless: bool = True,
    window_width: int = 900,
    window_height: int = 600,
) -> AsyncIterator:
    """Launch a Camoufox browser instance with stealth settings.

    Args:
        headless: Run in headless mode (no visible window).
        window_width: Browser window width in pixels.
        window_height: Browser window height in pixels.

    Yields:
        Camoufox browser context manager.
    """
    from camoufox.async_api import AsyncCamoufox

    os_choice = random.choice(["windows", "macos", "linux"])
    log(f"   🦊 Launching Camoufox (headless={headless}, os={os_choice})...")

    async with AsyncCamoufox(
        headless=headless,
        os=os_choice,
        window=(window_width, window_height),
    ) as browser:
        yield browser


async def setup_page(page) -> None:
    """Apply standard page setup for stealth and stability.

    - Suppresses uncaught JS errors from target sites
    - Forces 100% zoom on every page load

    Args:
        page: Playwright/Camoufox page object.
    """
    from ..logger import log as _log

    # Suppress uncaught JS errors from target pages
    page.on(
        "pageerror",
        lambda err: _log(f"⚠️ Page JS error (suppressed): {err}", "WARN"),
    )

    # Force 100% zoom on every page load
    await page.add_init_script("""() => {
        document.addEventListener('DOMContentLoaded', () => {
            document.body.style.zoom = '100%';
        });
    }""")
