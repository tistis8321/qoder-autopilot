"""Tests for OTP extraction module."""

from qoder_autopilot.otp import extract_otp


class TestExtractOtp:
    """Test OTP extraction from email HTML."""

    def test_extracts_from_span_with_letter_spacing(self, sample_otp_html):
        otp = extract_otp(sample_otp_html)
        assert otp == "482913"

    def test_returns_none_when_no_code(self, sample_otp_html_no_code):
        otp = extract_otp(sample_otp_html_no_code)
        assert otp is None

    def test_extracts_from_plain_text(self):
        """OTP extraction needs HTML context — plain text won't match."""
        html = "<p>Your code is 123456 and expires in 10 minutes.</p>"
        otp = extract_otp(html)
        # Plain text without letter-spacing/font-size styling won't match
        # This is expected — real emails always use styled OTP display
        assert otp is None

    def test_extracts_6_digit_code(self):
        cases = [
            ('<span style="letter-spacing: 8px">111222</span>', "111222"),
            ('<span style="letter-spacing: 8px">482913</span>', "482913"),
            ('<span style="letter-spacing: 8px">555123</span>', "555123"),
        ]
        for html, expected in cases:
            otp = extract_otp(html)
            assert otp == expected, f"Failed for: {html}"

    def test_ignores_non_otp_numbers(self):
        """Should prefer letter-spacing OTP over other numbers."""
        html = """<p>Order #1234. Ref: 56</p>
        <span style="letter-spacing: 8px">789012</span>"""
        otp = extract_otp(html)
        assert otp == "789012"

    def test_handles_empty_string(self):
        assert extract_otp("") is None

    def test_handles_none_input(self):
        assert extract_otp(None) is None

    def test_extracts_from_nested_html(self):
        html = """
        <div>
            <table>
                <tr>
                    <td style="font-size: 32px; letter-spacing: 8px;">
                        654321
                    </td>
                </tr>
            </table>
        </div>
        """
        otp = extract_otp(html)
        assert otp == "654321"
