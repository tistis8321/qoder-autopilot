"""Tests for custom exceptions module."""

from qoder_autopilot.errors import (
    CaptchaAIFailed,
    CaptchaError,
    CaptchaTimeoutError,
    DeviceTokenTimeout,
    FormSubmitError,
    NineRouterDBNotFound,
    NineRouterError,
    OAuthError,
    OTPTimeoutError,
    QoderAutopilotError,
    RegistrationError,
    TempMailError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_all_inherit_base(self):
        exceptions = [
            TempMailError,
            CaptchaError,
            CaptchaTimeoutError,
            CaptchaAIFailed,
            RegistrationError,
            OTPTimeoutError,
            FormSubmitError,
            OAuthError,
            DeviceTokenTimeout,
            NineRouterError,
            NineRouterDBNotFound,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, QoderAutopilotError)

    def test_captcha_subclasses(self):
        assert issubclass(CaptchaTimeoutError, CaptchaError)
        assert issubclass(CaptchaAIFailed, CaptchaError)

    def test_registration_subclasses(self):
        assert issubclass(OTPTimeoutError, RegistrationError)
        assert issubclass(FormSubmitError, RegistrationError)

    def test_oauth_subclasses(self):
        assert issubclass(DeviceTokenTimeout, OAuthError)

    def test_ninerouter_subclasses(self):
        assert issubclass(NineRouterDBNotFound, NineRouterError)


class TestExceptionFormatting:
    """Test exception message formatting."""

    def test_base_error_message(self):
        e = QoderAutopilotError("test error")
        assert str(e) == "test error"

    def test_base_error_with_detail(self):
        e = QoderAutopilotError("error", "some detail")
        assert "error" in str(e)
        assert "some detail" in str(e)

    def test_captcha_timeout_message(self):
        e = CaptchaTimeoutError(60)
        assert "60" in str(e)

    def test_captcha_ai_failed_message(self):
        e = CaptchaAIFailed("model not found")
        assert "model not found" in str(e)

    def test_otp_timeout_message(self):
        e = OTPTimeoutError("test@mail.com", 90)
        assert "test@mail.com" in str(e)
        assert "90" in str(e)

    def test_form_submit_error(self):
        e = FormSubmitError("step 2", "button not found")
        assert "step 2" in str(e)

    def test_device_token_timeout(self):
        e = DeviceTokenTimeout(300)
        assert "300" in str(e)

    def test_ninerouter_db_not_found(self):
        e = NineRouterDBNotFound("/tmp/missing.db")
        assert "/tmp/missing.db" in str(e)

    def test_catchable_as_base(self):
        """All exceptions should be catchable as QoderAutopilotError."""
        try:
            raise CaptchaTimeoutError(120)
        except QoderAutopilotError as e:
            assert "120" in str(e)
