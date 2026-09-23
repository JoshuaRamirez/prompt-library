"""Error taxonomy for the prompt library.

One exception family so interface adapters (CLI, MCP) can translate domain
failures into their own error conventions without inspecting messages.
"""


class PromptLibraryError(Exception):
    """Base class for all library-originated failures."""


class PromptNotFoundError(PromptLibraryError):
    """No record exists for the requested id."""

    def __init__(self, prompt_id: str) -> None:
        super().__init__(f"no prompt with id {prompt_id!r}")
        self.prompt_id = prompt_id


class DuplicatePromptError(PromptLibraryError):
    """A record already exists for the requested id."""

    def __init__(self, prompt_id: str) -> None:
        super().__init__(f"prompt id {prompt_id!r} already exists")
        self.prompt_id = prompt_id


class InvalidPromptError(PromptLibraryError):
    """A record failed validation before persistence."""


class InvalidArgumentError(PromptLibraryError):
    """A caller passed an argument the operation cannot accept."""


class StoreCorruptionError(PromptLibraryError):
    """The CSV file is unreadable or structurally inconsistent."""


class RenderError(PromptLibraryError):
    """Template substitution could not be completed."""
