import pytest

from app.core.password import (
    generate_secure_password,
    validate_password_strength,
)

# ── Valid passwords ──────────────────────────────────────────────────────────


def test_valid_password():
    assert validate_password_strength("Abcdef1!") == "Abcdef1!"


def test_valid_password_with_non_ascii_special():
    """Non-ASCII, non-alphanumeric chars should count as special."""
    assert validate_password_strength("Abcdef1€") == "Abcdef1€"


# ── Length ───────────────────────────────────────────────────────────────────


def test_too_short():
    with pytest.raises(ValueError, match="at least .* characters long"):
        validate_password_strength("Ab1!")


def test_min_length_floor(monkeypatch):
    """Even if MIN_PASSWORD_LENGTH is 2, the floor of 4 still applies."""
    from app.core import config

    monkeypatch.setattr(config.settings, "MIN_PASSWORD_LENGTH", 2)
    with pytest.raises(ValueError, match="at least 4 characters long"):
        validate_password_strength("A1!")


def test_exactly_four_chars_with_low_min(monkeypatch):
    """Length 4 should pass when MIN_PASSWORD_LENGTH <= 4."""
    from app.core import config

    monkeypatch.setattr(config.settings, "MIN_PASSWORD_LENGTH", 2)
    assert validate_password_strength("Ab1!") == "Ab1!"


# ── Missing character classes ────────────────────────────────────────────────


def test_missing_uppercase():
    with pytest.raises(ValueError, match="uppercase"):
        validate_password_strength("abcdef1!")


def test_missing_lowercase():
    with pytest.raises(ValueError, match="lowercase"):
        validate_password_strength("ABCDEF1!")


def test_missing_digit():
    with pytest.raises(ValueError, match="digit"):
        validate_password_strength("Abcdefg!")


def test_missing_special():
    with pytest.raises(ValueError, match="special"):
        validate_password_strength("Abcdefg1")


# ── generate_secure_password ─────────────────────────────────────────────────


def test_generated_password_passes_validation():
    pwd = generate_secure_password(12)
    assert validate_password_strength(pwd) == pwd


def test_generated_password_respects_min_floor(monkeypatch):
    """Even if length=2, the generated password must be at least 4 chars."""
    from app.core import config

    monkeypatch.setattr(config.settings, "MIN_PASSWORD_LENGTH", 2)
    pwd = generate_secure_password(2)
    assert len(pwd) >= 4
    assert validate_password_strength(pwd) == pwd
