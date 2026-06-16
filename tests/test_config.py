"""Tests for configuration module."""

from qoder_autopilot.infra.config import Settings, settings


class TestSettings:
    """Test pydantic Settings class."""

    def test_default_worker_url(self):
        s = Settings()
        assert "workers.dev" in s.worker_url or s.worker_url.startswith("http")

    def test_default_timeouts(self):
        s = Settings()
        assert s.captcha_timeout == 120
        assert s.otp_timeout == 20
        assert s.max_captcha_attempts == 8
        assert s.parallel_delay == 30

    def test_default_qoder_urls(self):
        s = Settings()
        assert "qoder.com" in s.qoder_signup_url
        assert "qoder.com" in s.qoder_signin_url
        assert "openapi.qoder.sh" in s.qoder_device_token_url

    def test_has_ai_captcha_empty(self):
        s = Settings(ai_api_key="")
        assert s.has_ai_captcha is False

    def test_has_ai_captcha_set(self):
        s = Settings(ai_api_key="sk-test-123")
        assert s.has_ai_captcha is True

    def test_ninerouter_db_path_expanded(self):
        s = Settings(ninerouter_db="~/test.db")
        assert "~" not in s.ninerouter_db_path
        assert s.ninerouter_db_path.endswith("test.db")

    def test_singleton_exists(self):
        """Module-level settings singleton should be accessible."""
        assert isinstance(settings, Settings)

    def test_model_fields_count(self):
        """Settings should have all expected fields."""
        field_names = set(Settings.model_fields.keys())
        expected = {
            "worker_url",
            "qoder_signup_url",
            "qoder_signin_url",
            "qoder_login_url",
            "qoder_device_token_url",
            "qoder_userinfo_url",
            "ninerouter_url",
            "ninerouter_password",
            "ninerouter_db",
            "ai_api_key",
            "ai_base_url",
            "ai_model",
            "captcha_timeout",
            "otp_timeout",
            "max_captcha_attempts",
            "parallel_delay",
            "screenshots_dir",
            "credentials_file",
        }
        assert expected.issubset(field_names)


class TestSettingsWithEnv:
    """Test Settings with mock environment variables."""

    def test_env_override(self, mock_env_vars):
        s = Settings()
        assert s.worker_url == "https://test-worker.example.com"
        assert s.captcha_timeout == 60
        assert s.otp_timeout == 90
