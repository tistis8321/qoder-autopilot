"""Tests for identity generation module."""

from qoder_autopilot.auth.identity import gen_identity, gen_password


class TestGenPassword:
    """Test password generation."""

    def test_default_length(self):
        pw = gen_password()
        assert len(pw) == 16

    def test_custom_length(self):
        for length in [8, 12, 20, 32]:
            pw = gen_password(length=length)
            assert len(pw) == length

    def test_contains_uppercase(self):
        for _ in range(20):
            pw = gen_password()
            assert any(c.isupper() for c in pw), f"No uppercase in {pw}"

    def test_contains_lowercase(self):
        for _ in range(20):
            pw = gen_password()
            assert any(c.islower() for c in pw), f"No lowercase in {pw}"

    def test_contains_digit(self):
        for _ in range(20):
            pw = gen_password()
            assert any(c.isdigit() for c in pw), f"No digit in {pw}"

    def test_contains_special(self):
        special = set("!@#$%^&*")
        for _ in range(20):
            pw = gen_password()
            assert any(c in special for c in pw), f"No special in {pw}"

    def test_uniqueness(self):
        """Passwords should be unique across generations."""
        passwords = {gen_password() for _ in range(100)}
        assert len(passwords) > 95, "Too many duplicate passwords"


class TestGenIdentity:
    """Test identity generation."""

    def test_returns_all_fields(self):
        ident = gen_identity()
        assert "first_name" in ident
        assert "last_name" in ident
        assert "display_name" in ident
        assert "password" in ident

    def test_display_name_is_combined(self):
        ident = gen_identity()
        assert ident["display_name"] == f"{ident['first_name']} {ident['last_name']}"

    def test_password_is_16_chars(self):
        ident = gen_identity()
        assert len(ident["password"]) == 16

    def test_names_are_nonempty(self):
        for _ in range(20):
            ident = gen_identity()
            assert len(ident["first_name"]) > 0
            assert len(ident["last_name"]) > 0

    def test_uniqueness(self):
        """Identities should be unique."""
        names = {gen_identity()["display_name"] for _ in range(50)}
        assert len(names) > 45, "Too many duplicate names"
