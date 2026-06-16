"""
Qoder Autopilot — Human-like Slider Movement
===============================================
Simulates realistic human mouse movement for sliding captcha puzzle pieces.
Includes variable speed, slight vertical wobble, and overshoot correction.
"""

import asyncio
import random

from ..logger import log


async def slide_puzzle(
    page,
    target_x: float,
    track_width: float,
) -> None:
    """Slide the puzzle piece to the target position with human-like movement.

    Args:
        page: Playwright/Camoufox page object.
        target_x: Target X position on the track.
        track_width: Total width of the sliding track.
    """
    # Find the slider element
    slider = await page.evaluate("""() => {
        const sels = ['#aliyunCaptcha-sliding-slider',
                      '#aliyunCaptcha-sliding .aliyunCaptcha-sliding-btn',
                      '.nc_iconfont.btn_slide', '.slide-verify-slider',
                      '[class*="slider-move"]', '[id*="sliding-slider"]',
                      '[class*="slider"] [class*="btn"]', '[class*="drag"]',
                      '[class*="slide"] [class*="handle"]'];
        for (const s of sels) {
            const el = document.querySelector(s);
            if (el) { const r = el.getBoundingClientRect();
                return {x: r.x, y: r.y, w: r.width, h: r.height}; }
        }
        return null;
    }""")

    if not slider:
        log("   ⚠️  No slider found")
        return

    sx = slider["x"] + slider["w"] / 2
    sy = slider["y"] + slider["h"] / 2

    log(f"   🖱️  Sliding {target_x:.0f}/{track_width:.0f}px")

    # Move to slider start position
    await page.mouse.move(sx, sy)
    await asyncio.sleep(random.uniform(0.3, 0.5))
    await page.mouse.down()
    await asyncio.sleep(random.uniform(0.1, 0.2))

    # ─── Main slide with variable speed ───
    cx = 0
    steps = random.randint(25, 45)

    for i in range(steps):
        p = (i + 1) / steps
        # Fast in the middle, slow at start and end
        if p < 0.7:
            speed = random.uniform(3, 8)
        elif p < 0.9:
            speed = random.uniform(1, 3)
        else:
            speed = random.uniform(0.3, 1)
        dx = min(speed, target_x - cx)
        cx += dx
        # Add slight vertical wobble
        await page.mouse.move(
            sx + cx,
            sy + random.uniform(-1.5, 1.5),
            steps=1,
        )
        await asyncio.sleep(random.uniform(0.01, 0.04))

    # ─── Overshoot + correct (mimics human behavior) ───
    await page.mouse.move(
        sx + cx + random.uniform(3, 10), sy, steps=2
    )
    await asyncio.sleep(random.uniform(0.1, 0.3))
    await page.mouse.move(sx + target_x, sy, steps=3)
    await asyncio.sleep(random.uniform(0.1, 0.2))
    await page.mouse.up()
    await asyncio.sleep(2)
