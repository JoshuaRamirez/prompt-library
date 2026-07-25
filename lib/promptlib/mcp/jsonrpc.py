"""Newline-delimited JSON-RPC 2.0 transport over stdio.

Transport concerns only: framing, parsing, and response construction. It knows
nothing of MCP methods, which keeps the protocol layer above testable without a
pipe.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Iterator, TextIO

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class JsonRpcError(Exception):
    """A failure that must be reported as a JSON-RPC error object."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_object(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error


@dataclass(frozen=True)
class Request:
    """One inbound JSON-RPC message."""

    method: str
    params: dict[str, Any]
    id: Any = None

    @property
    def is_notification(self) -> bool:
        return self.id is None


class StdioTransport:
    """Reads requests from stdin and writes responses to stdout."""

    def __init__(self, stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout

    def requests(self) -> Iterator[Request | JsonRpcError]:
        """Yield parsed requests; malformed lines yield a JsonRpcError."""
        for line in self._stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                yield JsonRpcError(PARSE_ERROR, f"invalid JSON: {exc}")
                continue
            if not isinstance(payload, dict) or "method" not in payload:
                yield JsonRpcError(INVALID_REQUEST, "not a JSON-RPC request object")
                continue
            params = payload.get("params") or {}
            if not isinstance(params, dict):
                params = {"value": params}
            yield Request(method=str(payload["method"]), params=params, id=payload.get("id"))

    def send_result(self, request_id: Any, result: Any) -> None:
        self._write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def send_error(self, request_id: Any, error: JsonRpcError) -> None:
        self._write({"jsonrpc": "2.0", "id": request_id, "error": error.to_object()})

    def _write(self, payload: dict[str, Any]) -> None:
        self._stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._stdout.flush()
