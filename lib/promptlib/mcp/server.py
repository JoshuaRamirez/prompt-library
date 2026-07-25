"""MCP protocol handling: method dispatch over the JSON-RPC transport.

Handles the subset of MCP a tools-only server needs — initialize, tools/list,
tools/call, ping — and reports domain failures as tool-level errors (isError on
the result) rather than protocol errors, which is what the specification calls
for so the model can see and recover from them.
"""

from __future__ import annotations

import json
import traceback
from typing import Any

from .. import __version__
from ..errors import PromptLibraryError
from ..service import PromptLibraryService
from .jsonrpc import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JsonRpcError,
    Request,
    StdioTransport,
)
from .tool_registry import ToolRegistry

SERVER_NAME = "prompt-library"
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")


class McpServer:
    """Serves the prompt library as MCP tools over stdio."""

    def __init__(
        self,
        service: PromptLibraryService,
        transport: StdioTransport | None = None,
    ) -> None:
        self._service = service
        self._transport = transport or StdioTransport()
        self._registry = ToolRegistry(service)

    def serve_forever(self) -> None:
        """Consume requests until stdin closes."""
        for message in self._transport.requests():
            if isinstance(message, JsonRpcError):
                self._transport.send_error(None, message)
                continue
            self._handle(message)

    # -- dispatch --------------------------------------------------------

    def _handle(self, request: Request) -> None:
        try:
            result = self._dispatch(request)
        except JsonRpcError as exc:
            if not request.is_notification:
                self._transport.send_error(request.id, exc)
            return
        except Exception as exc:  # noqa: BLE001 - boundary: never kill the server
            if not request.is_notification:
                self._transport.send_error(
                    request.id,
                    JsonRpcError(INTERNAL_ERROR, str(exc), {"traceback": traceback.format_exc()}),
                )
            return
        if request.is_notification or result is None:
            return
        self._transport.send_result(request.id, result)

    def _dispatch(self, request: Request) -> Any:
        handlers = {
            "initialize": self._initialize,
            "ping": lambda _params: {},
            "tools/list": lambda _params: {"tools": self._registry.list()},
            "tools/call": self._call_tool,
        }
        if request.method.startswith("notifications/"):
            return None
        handler = handlers.get(request.method)
        if handler is None:
            raise JsonRpcError(METHOD_NOT_FOUND, f"unsupported method: {request.method}")
        return handler(request.params)

    # -- methods ---------------------------------------------------------

    def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        requested = str(params.get("protocolVersion", "") or "")
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": __version__},
            "instructions": (
                "Prompt library backed by a single CSV table. Use prompt_search to find "
                "a stored prompt, prompt_get to read one in full, prompt_add to save a "
                "new one, and prompt_render to fill its {{placeholders}}."
            ),
        }

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        name = str(params.get("name", "") or "")
        tool = self._registry.resolve(name)
        if tool is None:
            raise JsonRpcError(INVALID_PARAMS, f"unknown tool: {name}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise JsonRpcError(INVALID_PARAMS, "arguments must be an object")
        try:
            payload = tool.invoke(arguments)
        except PromptLibraryError as exc:
            return self._text_result(f"{type(exc).__name__}: {exc}", is_error=True)
        except Exception as exc:  # noqa: BLE001 - surface to the model, not the wire
            return self._text_result(f"unexpected failure in {name}: {exc}", is_error=True)
        return self._text_result(json.dumps(payload, indent=2, ensure_ascii=False))

    @staticmethod
    def _text_result(text: str, is_error: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
        if is_error:
            result["isError"] = True
        return result
