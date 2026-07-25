"""Time source.

Injected rather than called directly so persistence behaviour is deterministic
under test.
"""

from __future__ import annotations

from datetime import datetime, timezone


class Clock:
    """UTC wall-clock reader."""

    def now_iso(self) -> str:
        """Return the current instant as an ISO-8601 UTC string (seconds)."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class FrozenClock(Clock):
    """Fixed time source for tests."""

    def __init__(self, stamp: str) -> None:
        self._stamp = stamp

    def now_iso(self) -> str:
        return self._stamp
