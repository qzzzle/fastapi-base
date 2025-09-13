from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

def get_now_tehran() -> datetime:
    """Return an aware datetime in Asia/Tehran."""
    return datetime.now(TEHRAN_TZ)

def get_now_tehran_iso() -> str:
    """Return ISO-8601 like '2025-09-02T10:31:00+03:30'."""
    return datetime.now(TEHRAN_TZ).isoformat(timespec="seconds")
