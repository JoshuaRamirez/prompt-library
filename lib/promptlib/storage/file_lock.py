"""Advisory inter-process lock guarding the CSV file.

Several Claude sessions may hold the library open at once. `flock` on a sidecar
file serialises read-modify-write cycles without touching the data file itself,
so a crashed holder cannot leave the CSV truncated.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
from types import TracebackType


class FileLock:
    """Context-managed exclusive advisory lock on `<target>.lock`."""

    def __init__(self, target: Path) -> None:
        self._lock_path = target.with_name(target.name + ".lock")
        self._handle: int | None = None

    @property
    def path(self) -> Path:
        return self._lock_path

    def __enter__(self) -> "FileLock":
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(self._handle, fcntl.LOCK_EX)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._handle is None:
            return
        try:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
        finally:
            os.close(self._handle)
            self._handle = None
