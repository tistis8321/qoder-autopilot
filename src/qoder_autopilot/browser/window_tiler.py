"""
Qoder Autopilot — Window Grid Tiling
======================================
Tile Camoufox browser windows into a 2×2 grid layout.
Uses macOS AppleScript for window positioning.

Grid layout:
    ┌──────────┬──────────┐
    │  Slot 1  │  Slot 2  │  (top row)
    ├──────────┼──────────┤
    │  Slot 3  │  Slot 4  │  (bottom row)
    └──────────┴──────────┘

Windows cycle through slots: 5th window → slot 1, 6th → slot 2, etc.
"""

import platform
import subprocess

from ..logger import log

_screen_size_cache: tuple[int, int] | None = None


def get_screen_size() -> tuple[int, int]:
    """Get main screen dimensions via osascript (cached).

    Returns:
        Tuple of (width, height) in pixels.
    """
    global _screen_size_cache
    if _screen_size_cache:
        return _screen_size_cache

    try:
        result = subprocess.run(
            [
                "osascript", "-e",
                'tell application "Finder" to get bounds of window of desktop',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        parts = [int(x.strip()) for x in result.stdout.strip().split(",")]
        _screen_size_cache = (parts[2], parts[3])
    except Exception:
        _screen_size_cache = (1920, 1080)

    return _screen_size_cache


def tile_all_camoufox_windows() -> None:
    """Tile ALL open Camoufox windows into a 2×2 grid.

    Call this after all browsers have been launched.
    Only works on macOS (uses AppleScript).
    """
    if platform.system() != "Darwin":
        return

    sw, sh = get_screen_size()
    half_w = sw // 2
    half_h = sh // 2
    menubar = 25

    # Grid positions: (left, top, right, bottom)
    grid = [
        (0, menubar, half_w, half_h + menubar),                     # top-left
        (half_w, menubar, sw, half_h + menubar),                    # top-right
        (0, half_h + menubar, half_w, sh),                          # bottom-left
        (half_w, half_h + menubar, sw, sh),                         # bottom-right
    ]

    # Build AppleScript grid list
    g = grid
    grid_str = (
        "{"
        + "{" + f"{g[0][0]}, {g[0][1]}, {g[0][2]}, {g[0][3]}" + "}, "
        + "{" + f"{g[1][0]}, {g[1][1]}, {g[1][2]}, {g[1][3]}" + "}, "
        + "{" + f"{g[2][0]}, {g[2][1]}, {g[2][2]}, {g[2][3]}" + "}, "
        + "{" + f"{g[3][0]}, {g[3][1]}, {g[3][2]}, {g[3][3]}" + "}"
        + "}"
    )

    script = f'''
    tell application "camoufox"
        set winCount to count of windows
        set grid to {grid_str}
        repeat with i from 1 to winCount
            set posIdx to ((i - 1) mod 4) + 1
            set bounds of window i to item posIdx of grid
        end repeat
        return winCount
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        count = result.stdout.strip()
        log(f"   🪟 Tiled {count} Camoufox windows into 2×2 grid")
    except Exception as e:
        log(f"   ⚠️ Grid tiling failed: {e}", "WARN")
