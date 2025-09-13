"""
DI helper decorator (optional).
- If your services follow a "BaseService.close_scoped_session()" convention,
  this wrapper ensures cleanup after a call.
- Kept minimal and tolerant: does nothing if no such services are injected.
"""

import logging
from functools import wraps

from dependency_injector.wiring import inject as di_inject

logger = logging.getLogger(__name__)


def inject(func):
    """Wrap a function with DI injection and optional service cleanup."""

    @di_inject
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # Optional cleanup: if injected args have 'close_scoped_session', call it safely
        for arg in kwargs.values():
            close = getattr(arg, "close_scoped_session", None)
            if callable(close):
                try:
                    close()
                except Exception as e:
                    logger.error("Failed to close scoped session: %s", e)
        return result

    return wrapper
