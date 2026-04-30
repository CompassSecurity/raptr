import secrets
import string

from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

# Complexity rules require at least one of each: uppercase, lowercase, digit,
# special character.  That means the absolute minimum viable length is 4,
# regardless of what MIN_PASSWORD_LENGTH is set to.
_MIN_COMPLEXITY_LENGTH = 4


def hash_password(password: str) -> str:
    """
    Hash a password
    """
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password
    """
    return password_hash.verify(password, hashed_password)


def validate_password_strength(password: str) -> str:
    """
    Validate password strength.

    Enforces:
    - Minimum length (at least ``_MIN_COMPLEXITY_LENGTH``, or
      ``settings.MIN_PASSWORD_LENGTH`` if larger)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one non-alphanumeric (special) character
    """
    effective_min = max(settings.MIN_PASSWORD_LENGTH, _MIN_COMPLEXITY_LENGTH)
    if len(password) < effective_min:
        raise ValueError("Password must be at least %d characters long" % effective_min)
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")
    if not any(not char.isalnum() for char in password):
        raise ValueError("Password must contain at least one special character")
    return password


def generate_secure_password(length: int = settings.MIN_PASSWORD_LENGTH) -> str:
    """
    Generate a secure random password that satisfies all complexity rules.
    """
    effective_length = max(length, _MIN_COMPLEXITY_LENGTH)

    letters_upper = string.ascii_uppercase
    letters_lower = string.ascii_lowercase
    digits = string.digits
    special = string.punctuation

    password = [
        secrets.choice(letters_upper),
        secrets.choice(letters_lower),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    all_chars = letters_upper + letters_lower + digits + special
    password += [secrets.choice(all_chars) for _ in range(effective_length - 4)]

    secrets.SystemRandom().shuffle(password)

    return "".join(password)
