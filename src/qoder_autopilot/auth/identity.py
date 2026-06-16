"""
Qoder Autopilot — Identity Generator
======================================
Generate random but realistic Indonesian identities for registration.
Uses Faker with id_ID locale for authentic-sounding names.
"""

import random
import string

from faker import Faker

# Indonesian locale for realistic names
fake = Faker("id_ID")

# Special chars that work in passwords without causing issues
SPECIAL = "!@#$%^&*"


def gen_password(length: int = 16) -> str:
    """Generate a strong password with upper, lower, digit, and special chars.

    Args:
        length: Password length (default 16).

    Returns:
        Random password string guaranteed to contain all char types.
    """
    pw = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice(SPECIAL),
    ]
    all_chars = string.ascii_letters + string.digits + SPECIAL
    pw.extend(random.choices(all_chars, k=length - len(pw)))
    random.shuffle(pw)
    return "".join(pw)


def gen_identity() -> dict:
    """Generate a random identity with Indonesian name and strong password.

    Uses Faker to generate realistic Indonesian names.
    First name and last name are generated separately to ensure
    natural-sounding full names.

    Returns:
        Dict with first_name, last_name, display_name, password.

    Example:
        {
            'first_name': 'Rizky',
            'last_name': 'Saputra',
            'display_name': 'Rizky Saputra',
            'password': 'k9#mP$xL2nQ!wR8v'
        }
    """
    first = fake.first_name()
    last = fake.last_name()
    return {
        "first_name": first,
        "last_name": last,
        "display_name": f"{first} {last}",
        "password": gen_password(),
    }
