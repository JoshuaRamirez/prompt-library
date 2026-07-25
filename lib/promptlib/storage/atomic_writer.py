"""Whole-file replacement with crash-consistent semantics.

The CSV is rewritten in full on every mutation. Writing to a sibling temporary
file and renaming makes the replacement atomic within the filesystem, so an
interrupted write leaves the previous generation intact rather than a partial
table.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable, TextIO


class AtomicFileWriter:
    """Replaces a file's contents atomically via write-temp-then-rename."""

    def __init__(self, target: Path, encoding: str = "utf-8") -> None:
        self._target = target
        self._encoding = encoding

    def write(self, emit: Callable[[TextIO], None]) -> None:
        """Invoke `emit` with a handle to a temp file, then rename over target."""
        self._target.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding=self._encoding,
            newline="",
            dir=str(self._target.parent),
            prefix=self._target.name + ".",
            suffix=".tmp",
            delete=False,
        )
        temp_path = Path(handle.name)
        try:
            with handle:
                emit(handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self._target)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise
