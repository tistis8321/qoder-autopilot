"""
Qoder Autopilot — OpenCV Captcha Gap Detection
================================================
4-method computer vision approach to find the gap position in
Aliyun slide CAPTCHAs without requiring an AI API:

1. Column brightness drop analysis
2. Edge density analysis
3. Masked template matching (TM_CCOEFF_NORMED)
4. Masked SQDIFF matching (TM_SQDIFF_NORMED)

Results are combined via voting to find the most likely gap position.
"""

import base64
import urllib.request

import numpy as np

from ..logger import log


async def detect_gap_position(page) -> float | None:
    """Use OpenCV to detect the puzzle gap position in the captcha image.

    Args:
        page: Playwright/Camoufox page object with the captcha loaded.

    Returns:
        The X offset scaled to track width, or None on failure.
    """
    try:
        import cv2

        # Get image URLs from the page
        img_urls = await page.evaluate("""() => {
            const bg = document.querySelector('#aliyunCaptcha-img');
            const pz = document.querySelector('#aliyunCaptcha-puzzle');
            return {
                bgSrc: bg?.src || '',
                pzSrc: pz?.src || '',
                bgW: bg?.getBoundingClientRect()?.width || 300,
                bgH: bg?.getBoundingClientRect()?.height || 200,
                pzW: pz?.getBoundingClientRect()?.width || 52,
            };
        }""")

        if not img_urls.get("bgSrc") or not img_urls.get("pzSrc"):
            return None

        # Parse base64 data URIs
        def parse_data_uri(uri: str) -> bytes:
            if uri.startswith("data:"):
                _, b64data = uri.split(",", 1)
                return base64.b64decode(b64data)
            else:
                return urllib.request.urlopen(uri).read()

        bg_data = parse_data_uri(img_urls["bgSrc"])
        pz_data = parse_data_uri(img_urls["pzSrc"])

        bg_img = cv2.imdecode(np.frombuffer(bg_data, np.uint8), cv2.IMREAD_COLOR)
        pz_img = cv2.imdecode(np.frombuffer(pz_data, np.uint8), cv2.IMREAD_UNCHANGED)

        if bg_img is None or pz_img is None:
            return None

        # Convert puzzle to grayscale + edge detection
        if pz_img.shape[2] == 4:
            pz_gray = pz_img[:, :, 3]  # Use alpha channel
            _, pz_mask = cv2.threshold(pz_gray, 127, 255, cv2.THRESH_BINARY)
            pz_bgr = pz_img[:, :, :3]
        else:
            pz_gray = cv2.cvtColor(pz_img, cv2.COLOR_BGR2GRAY)
            pz_mask = None
            pz_bgr = pz_img

        bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
        bg_h, bg_w = bg_gray.shape
        pz_h, pz_w = pz_bgr.shape[:2]

        # ─── Method 1: Column brightness drop analysis ───
        col_brightness = np.mean(bg_gray, axis=0)
        kernel_size = max(3, pz_w // 4)
        if kernel_size % 2 == 0:
            kernel_size += 1
        smoothed = cv2.GaussianBlur(col_brightness.reshape(1, -1), (kernel_size, 1), 0).flatten()

        window = pz_w
        min_brightness = float("inf")
        min_col = bg_w // 2

        start_col = int(bg_w * 0.15)  # Skip first 15% (puzzle piece start area)
        for col in range(start_col, bg_w - pz_w):
            left = max(0, col - window // 2)
            right = min(bg_w, col + window // 2)
            region_brightness = np.mean(smoothed[left:right])

            other_left = smoothed[:left] if left > 0 else np.array([])
            other_right = smoothed[right:] if right < bg_w else np.array([])
            other = np.concatenate([other_left, other_right])
            if len(other) > 0:
                other_brightness = np.mean(other)
                drop = other_brightness - region_brightness
                if drop > (np.mean(smoothed) - min_brightness):
                    min_brightness = region_brightness
                    min_col = col

        gap_x_method1 = min_col

        # ─── Method 2: Edge density analysis ───
        bg_edges = cv2.Canny(bg_gray, 50, 150)
        col_edge_density = np.sum(bg_edges > 0, axis=0).astype(float)
        edge_smoothed = cv2.GaussianBlur(
            col_edge_density.reshape(1, -1), (kernel_size, 1), 0
        ).flatten()

        max_edge = 0
        max_edge_col = bg_w // 2
        for col in range(start_col, bg_w - pz_w):
            left = max(0, col - window // 2)
            right = min(bg_w, col + window // 2)
            edge_sum = np.sum(edge_smoothed[left:right])
            if edge_sum > max_edge:
                max_edge = edge_sum
                max_edge_col = col

        gap_x_method2 = max_edge_col

        # ─── Method 3: Masked template matching ───
        pz_gray_tmpl = cv2.cvtColor(pz_bgr, cv2.COLOR_BGR2GRAY)
        tm_mask = (
            pz_mask if pz_mask is not None else np.ones(pz_bgr.shape[:2], dtype=np.uint8) * 255
        )

        result_masked = cv2.matchTemplate(bg_gray, pz_gray_tmpl, cv2.TM_CCOEFF_NORMED, mask=tm_mask)
        _, max_val_masked, _, max_loc_masked = cv2.minMaxLoc(result_masked)
        gap_x_method3 = max_loc_masked[0]

        # ─── Method 4: SQDIFF masked ───
        result_sqdiff = cv2.matchTemplate(bg_gray, pz_gray_tmpl, cv2.TM_SQDIFF_NORMED, mask=tm_mask)
        _, _, min_loc_sq, _ = cv2.minMaxLoc(result_sqdiff)
        gap_x_method4 = min_loc_sq[0]

        # ─── Combine via voting ───
        methods = {
            "brightness": gap_x_method1,
            "edge": gap_x_method2,
            "maskedTM": gap_x_method3,
            "sqdiffTM": gap_x_method4,
        }

        best_votes = {}
        for name, x in methods.items():
            votes = sum(1 for other_x in methods.values() if abs(x - other_x) < 25)
            best_votes[name] = votes

        winner = max(best_votes.keys(), key=lambda k: k and best_votes[k])
        gap_x = methods[winner]

        agreeing = [x for x in methods.values() if abs(x - gap_x) < 25]
        if len(agreeing) >= 2:
            gap_x = int(np.mean(agreeing))
            confidence = min(0.9, len(agreeing) * 0.25)
        else:
            gap_x = gap_x_method3
            confidence = max_val_masked

        method_str = f"winner={winner}(votes={best_votes[winner]}) | {methods}"
        log(f"   🔍 Gap: x={gap_x}px | {method_str}")

        bg_img_width = bg_img.shape[1]
        track_width = img_urls["bgW"]
        scaled_x = (gap_x / bg_img_width) * track_width

        log(
            f"   🔍 Gap: x={gap_x}px (img {bg_img_width}px) "
            f"→ track {scaled_x:.0f}/{track_width:.0f}px, conf={confidence:.2f}"
        )
        return scaled_x

    except Exception as e:
        log(f"   ⚠️  Gap detection failed: {e}")
        return None
