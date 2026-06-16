"""
Qoder Autopilot — Captcha Solving Sub-package
===============================================
Multiple strategies for solving Aliyun slide CAPTCHAs:

- **AI Vision**: Use Gemini/OpenAI to identify the gap position
- **OpenCV**: 4-method computer vision approach (brightness, edge, template match)
- **Manual**: Pause and let the user solve it in the visible browser
- **Slider**: Human-like mouse movement simulation for sliding the puzzle piece
"""

from .solver import CaptchaSolver

__all__ = ["CaptchaSolver"]
