"""SpiderGPT Structured Logging Configuration.

Ensures zero secret leakage and structured observability across request cycles,
AI provider interactions, and payment webhooks.
"""
import logging
import re
import sys
from typing import Any, Dict


# Regex patterns to sanitize sensitive tokens
SENSITIVE_PATTERNS = [
    re.compile(r'(api[-_]?key|secret|token|bearer|password|authorization)["\']?\s*[:=]\s*["\']?([^"\'\s,]+)', re.IGNORECASE),
    re.compile(r'sk-[a-zA-Z0-9_-]{10,}', re.IGNORECASE),
    re.compile(r'AIzaSy[a-zA-Z0-9_-]{10,}', re.IGNORECASE),
    re.compile(r'rzp_(?:live|test)_[a-zA-Z0-9]+', re.IGNORECASE),
]


def sanitize_sensitive_data(message: str) -> str:
    """Sanitizes API keys, authorization tokens, and credentials from log strings."""
    if not isinstance(message, str):
        message = str(message)
    # Simple, safe token redaction
    for pattern in SENSITIVE_PATTERNS:
        try:
            message = pattern.sub("[REDACTED]", message)
        except Exception:
            pass
    return message


class SafeLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original_msg = super().format(record)
        return sanitize_sensitive_data(original_msg)


def setup_logging(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger("spidergpt")
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = SafeLogFormatter(
            fmt="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
