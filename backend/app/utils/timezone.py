"""SpiderGPT Timezone and Date Utility.

Computes current date strings based on configurable timezones for atomic limit tracking.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from backend.app.core.config import settings
from backend.app.core.logging import logger


def get_current_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.TIMEZONE)
    except Exception:
        logger.warning("Invalid timezone '%s', defaulting to UTC", settings.TIMEZONE)
        return ZoneInfo("UTC")


def get_current_date_str() -> str:
    """Returns the current date in YYYY-MM-DD format for daily quota tracking."""
    tz = get_current_timezone()
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def get_current_month_str() -> str:
    """Returns the current month in YYYY-MM format for monthly customization tracking."""
    tz = get_current_timezone()
    now = datetime.now(tz)
    return now.strftime("%Y-%m")


def get_utc_now() -> datetime:
    """Returns timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)
