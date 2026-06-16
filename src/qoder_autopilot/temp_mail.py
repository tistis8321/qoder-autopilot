"""
Qoder Autopilot — Temporary Email Client
==========================================
Client for Cloudflare Worker-based temporary email service.
Supports generating addresses, checking inbox, and reading messages.
"""

import time
from urllib.parse import quote as url_quote

import requests

from . import config
from .errors import TempMailError
from .logger import log, log_ok, log_err


class TempMail:
    """Client for the Cloudflare Worker temp mail API."""

    def __init__(self, worker_url: str | None = None):
        self.url = (worker_url or config.WORKER_URL).rstrip("/")

    def generate(self) -> dict:
        """Generate a new temporary email address.

        Returns:
            dict with at least 'address' key containing the email address.

        Raises:
            TempMailError: If the API returns an error or request fails.
        """
        try:
            r = requests.post(f"{self.url}/api/generate", timeout=15)
            r.raise_for_status()
        except requests.RequestException as e:
            raise TempMailError("Failed to generate email", str(e)) from e

        d = r.json()
        if d.get("code") != 0:
            raise TempMailError(
                "Generate failed",
                d.get("error", "unknown error"),
            )
        return d["data"]

    def inbox(self, address: str) -> list[dict]:
        """Fetch inbox messages for the given email address.

        Returns:
            List of message dicts with at least 'id' key.

        Raises:
            TempMailError: If the request fails.
        """
        try:
            r = requests.get(
                f"{self.url}/api/inbox/{url_quote(address)}", timeout=15
            )
            r.raise_for_status()
        except requests.RequestException as e:
            raise TempMailError("Inbox fetch failed", str(e)) from e

        d = r.json()
        return d["data"].get("rows", []) if d.get("code") == 0 else []

    def message(self, msg_id: str) -> dict | None:
        """Fetch a single message by ID.

        Returns:
            Message dict with 'html' and/or 'text' keys, or None on failure.
        """
        try:
            r = requests.get(f"{self.url}/api/message/{msg_id}", timeout=15)
            r.raise_for_status()
        except requests.RequestException as e:
            raise TempMailError("Message fetch failed", str(e)) from e

        d = r.json()
        return d["data"] if d.get("code") == 0 else None

    def wait_for_email(
        self,
        address: str,
        timeout: int = 180,
        interval: int = 5,
    ) -> list[dict]:
        """Poll inbox until at least one email arrives or timeout is reached.

        Returns:
            List of messages if received, empty list on timeout.
        """
        log(f"   ⏳ Waiting for email at {address}...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                msgs = self.inbox(address)
                if msgs:
                    log_ok(f"Got {len(msgs)} email(s)!")
                    return msgs
            except TempMailError as e:
                log(f"   ⚠️ Inbox error (will retry): {e}")
            time.sleep(interval)
        log_err("Timeout waiting for email")
        return []
