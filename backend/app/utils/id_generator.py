"""SpiderGPT ID Generation Utility.

Generates clean, prefixed, URL-safe UUIDs for database entities.
"""
import uuid


def generate_id(prefix: str) -> str:
    """Generates a prefixed UUID4 string (e.g. usr_1234567890abcdef...)."""
    hex_str = uuid.uuid4().hex
    return f"{prefix}_{hex_str}"


def generate_short_code() -> str:
    """Generates a random short alphanumeric code."""
    return uuid.uuid4().hex[:8].upper()
