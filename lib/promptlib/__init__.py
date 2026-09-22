"""promptlib — CSV-backed prompt library core.

Layering (lower layers know nothing of higher ones):

    storage/    generic CSV table persistence (no prompt semantics)
    domain/     Prompt record, canonical schema, repository
    search/     SearchStrategy port + keyword implementation
    rendering/  variable substitution
    service     facade composing the above
    cli/, mcp/  interface adapters over the service

The SearchStrategy port is the designated seam for a future vector-database
backend; see docs/VECTOR-DB.md.
"""

__version__ = "0.1.2"
