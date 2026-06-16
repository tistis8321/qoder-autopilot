"""
Qoder Autopilot — CLI Entry Point
===================================
Command-line interface for automated Qoder account registration
with optional 9Router integration.

Usage:
    qoder-autopilot -n 5 --manual-captcha --parallel
    python -m qoder_autopilot -n 3 --no-headless
"""

import argparse
import asyncio
import platform
import random

from . import config
from .errors import NineRouterError, NineRouterDBNotFound
from .logger import log, log_ok, log_err, log_step, log_warn, set_account_tag
from .temp_mail import TempMail
from .identity import gen_identity
from .credentials import save_creds
from .oauth import initiate_device_flow, poll_device_token
from .ninerouter import add_to_9router_device
from .register import register_and_verify
from .browser.camoufox import launch_browser, setup_page
from .browser.window_tiler import get_screen_size


async def run_one(
    headless: bool = True,
    use_oauth: bool = True,
    manual_captcha: bool = False,
    acct_num: int = 0,
) -> dict | None:
    """Register a single Qoder account and optionally connect to 9Router.

    Args:
        headless: Run browser in headless mode.
        use_oauth: Use OAuth device flow for 9Router connection.
        manual_captcha: Pause for manual captcha solving.
        acct_num: Account number for parallel mode logging.

    Returns:
        Dict with email and token on success, None on failure.
    """
    tag = f"#{acct_num}" if acct_num else ""
    if tag:
        set_account_tag(tag)

    # Force non-headless when manual captcha is enabled
    if manual_captcha:
        headless = False

    log("=" * 60)
    log(f"🚀 QODER AUTOPILOT — Register + 9Router Connect {tag}")
    if manual_captcha:
        log("🧑 Manual captcha mode — browser will stay visible")
    log("=" * 60)

    # 1. Generate temp email
    log("📋 Step 1/4: Generating temp email...")
    tm = TempMail()
    edata = tm.generate()
    email = edata["address"]
    log_ok(f"Email: {email}")

    # 2. Generate identity
    log("📋 Step 2/4: Generating identity...")
    ident = gen_identity()
    log_ok(f"{ident['display_name']} | pw: {ident['password']}")

    # 3. Register + verify
    log("📋 Step 3/4: OAuth register + device token flow...")
    flow = initiate_device_flow() if use_oauth else None
    auth_url = flow["auth_url"] if flow else None

    if auth_url:
        log(f"   🔗 OAuth URL: {auth_url[:80]}...")

    # Calculate grid slot window size
    if platform.system() == "Darwin":
        sw, sh = get_screen_size()
        win_w = sw // 2
        win_h = sh // 2
    else:
        win_w, win_h = 900, 600

    async with launch_browser(
        headless=headless,
        window_width=win_w,
        window_height=win_h,
    ) as browser:
        page = await browser.new_page()
        await setup_page(page)
        verified = await register_and_verify(
            page, email, ident,
            auth_url=auth_url,
            manual_captcha=manual_captcha,
            acct_num=acct_num,
        )

        # Keep browser open briefly for redirect
        await asyncio.sleep(2)
        await page.screenshot(
            path=str(config.SCREENSHOTS_DIR / "final_state.png")
        )
        final_url = page.url
        log(f"   📍 Final URL: {final_url}")

    if not verified:
        log_err("Registration/verification failed!")
        save_creds({
            "email": email,
            "password": ident["password"],
            "display_name": ident["display_name"],
            "status": "failed",
        })
        return None

    log_ok("Account registered & verified! ✅")

    # 4. Poll for device token + connect to 9Router
    if flow:
        log("📋 Step 4/4: Polling device token...")
        device_token = poll_device_token(
            flow["nonce"], flow["verifier"],
            max_attempts=60, interval=3,
        )

        if device_token:
            log_ok(f"🎉 Device token obtained! token={device_token['token'][:20]}...")

            # Add to 9Router
            router_ok = False
            try:
                add_to_9router_device(
                    email, ident["display_name"],
                    device_token, flow["machine_id"],
                )
                router_ok = True
            except NineRouterDBNotFound as e:
                log_err(f"9Router DB missing: {e}")
            except NineRouterError as e:
                log_err(f"9Router insert failed: {e}")

            save_creds({
                "email": email,
                "password": ident["password"],
                "display_name": ident["display_name"],
                "access_token": device_token["token"],
                "refresh_token": device_token.get("refresh_token", ""),
                "user_id": device_token.get("user_id", ""),
                "machine_id": flow["machine_id"],
                "9router": router_ok,
                "status": "success",
            })
            if router_ok:
                log_ok(f"🎉 {email} → 9Router connected")
            else:
                log_warn(f"{email} registered but 9Router failed")
            return {"email": email, "token": device_token["token"]}
        else:
            log_err("Device token poll failed — account verified but no token")
            save_creds({
                "email": email,
                "password": ident["password"],
                "display_name": ident["display_name"],
                "status": "verified_no_token",
            })
            return None
    else:
        log("⚠️ No OAuth flow — just registration done")
        save_creds({
            "email": email,
            "password": ident["password"],
            "display_name": ident["display_name"],
            "status": "verified_no_oauth",
        })
        return {"email": email}


async def main_async(args: argparse.Namespace) -> None:
    """Async main entry point."""
    headless = not args.no_headless
    use_oauth = not args.no_oauth
    manual_captcha = args.manual_captcha
    parallel = args.parallel

    log(
        f"🎯 Creating {args.count} account(s) | "
        f"headless={headless} | oauth={use_oauth} | "
        f"manual_captcha={manual_captcha} | parallel={parallel}"
    )

    if parallel and args.count > 1:
        # ═══ PARALLEL MODE ═══
        log(f"⚡ Parallel mode: launching {args.count} browser windows")

        async def staggered_run(i: int) -> dict | None:
            if i > 0:
                await asyncio.sleep(i * 2)
            return await run_one(
                headless=headless,
                use_oauth=use_oauth,
                manual_captcha=manual_captcha,
                acct_num=i + 1,
            )

        tasks = [staggered_run(i) for i in range(args.count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, r in enumerate(results):
            if isinstance(r, Exception):
                log_err(f"Account #{i + 1} crashed: {r}")
                results[i] = None
    else:
        # ═══ SEQUENTIAL MODE ═══
        results = []
        for i in range(args.count):
            log(f"\n{'─' * 60}\n📦 Account {i + 1}/{args.count}\n{'─' * 60}")
            r = await run_one(
                headless=headless,
                use_oauth=use_oauth,
                manual_captcha=manual_captcha,
                acct_num=i + 1 if args.count > 1 else 0,
            )
            results.append(r)
            if i < args.count - 1:
                d = config.PARALLEL_DELAY + random.randint(0, 15)
                log(f"⏳ Waiting {d}s...")
                await asyncio.sleep(d)

    s = sum(1 for r in results if r)
    log(f"\n{'═' * 60}\n📊 DONE: {s}/{len(results)} succeeded\n{'═' * 60}")


def main() -> None:
    """CLI entry point."""
    p = argparse.ArgumentParser(
        prog="qoder-autopilot",
        description="Automated Qoder account registration with 9Router integration",
    )
    p.add_argument(
        "-n", "--count", type=int, default=1,
        help="Number of accounts to create",
    )
    p.add_argument(
        "--no-headless", action="store_true",
        help="Show browser windows",
    )
    p.add_argument(
        "--no-oauth", action="store_true",
        help="Skip OAuth flow, just register",
    )
    p.add_argument(
        "--manual-captcha", action="store_true",
        help="Pause for manual captcha solving (forces non-headless)",
    )
    p.add_argument(
        "--parallel", action="store_true",
        help="Run all accounts concurrently",
    )
    p.add_argument(
        "--delay", type=int, default=config.PARALLEL_DELAY,
        help=f"Delay between sequential accounts (default: {config.PARALLEL_DELAY}s)",
    )
    args = p.parse_args()

    asyncio.run(main_async(args))
