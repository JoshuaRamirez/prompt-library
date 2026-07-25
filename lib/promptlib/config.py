"""Where the library lives on disk.

Resolution order, most specific first:
    1. explicit constructor argument
    2. $PROMPT_LIBRARY_CSV   — full path to the CSV file
    3. $PROMPT_LIBRARY_HOME  — directory holding prompts.csv
    4. ~/.claude/prompt-library/prompts.csv

The data deliberately sits outside the plugin directory: deleting or reinstalling
the plugin must not take the library with it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DIRECTORY = Path.home() / ".claude" / "prompt-library"
DEFAULT_FILENAME = "prompts.csv"

ENV_CSV = "PROMPT_LIBRARY_CSV"
ENV_HOME = "PROMPT_LIBRARY_HOME"


@dataclass(frozen=True)
class LibraryPaths:
    """Filesystem locations used by the library."""

    csv_path: Path

    @property
    def home(self) -> Path:
        return self.csv_path.parent

    @property
    def backup_directory(self) -> Path:
        return self.home / "backups"

    @classmethod
    def resolve(cls, csv_path: str | os.PathLike[str] | None = None) -> "LibraryPaths":
        """Apply the documented resolution order and return the paths."""
        if csv_path:
            return cls(Path(csv_path).expanduser())
        env_csv = os.environ.get(ENV_CSV, "").strip()
        if env_csv:
            return cls(Path(env_csv).expanduser())
        env_home = os.environ.get(ENV_HOME, "").strip()
        if env_home:
            return cls(Path(env_home).expanduser() / DEFAULT_FILENAME)
        return cls(DEFAULT_DIRECTORY / DEFAULT_FILENAME)
