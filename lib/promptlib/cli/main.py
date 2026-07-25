"""`promptlib` command-line interface.

Argument parsing and exit codes only; every operation delegates to
`PromptLibraryService`. `--json` on any subcommand emits the raw service payload,
which is also what the MCP tools return — one behaviour, two renderings.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from ..errors import PromptLibraryError
from ..service import PromptLibraryService
from .formatters import JsonFormatter, TextFormatter

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_FOUND = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptlib",
        description="CSV-backed prompt library.",
    )
    parser.add_argument("--csv", help="Path to the prompts CSV (overrides env and default).")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    listing = subparsers.add_parser("list", help="List prompts.")
    _add_facets(listing)
    listing.add_argument("--limit", type=int)
    listing.add_argument("--full", action="store_true", help="Include prompt bodies.")

    search = subparsers.add_parser("search", help="Rank prompts against a query.")
    search.add_argument("query", nargs="+")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--full", action="store_true")
    _add_facets(search)

    get = subparsers.add_parser("get", help="Show one prompt in full.")
    get.add_argument("id")
    get.add_argument("--body-only", action="store_true", help="Print only the prompt text.")

    add = subparsers.add_parser("add", help="Store a new prompt.")
    add.add_argument("--id")
    add.add_argument("--title", default="")
    add.add_argument("--prompt", help="Prompt text; omit or use '-' to read stdin.")
    add.add_argument("--tags", default="")
    add.add_argument("--category", default="")
    add.add_argument("--model", default="")
    add.add_argument("--notes", default="")
    add.add_argument("--source", default="")
    add.add_argument("--version", default="")
    add.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="COLUMN=VALUE",
        help="Set any column, including new ones. Repeatable.",
    )

    update = subparsers.add_parser("update", help="Patch an existing prompt.")
    update.add_argument("id")
    for option in ("title", "prompt", "tags", "category", "model", "notes", "source", "version"):
        update.add_argument(f"--{option}")
    update.add_argument("--set", action="append", default=[], metavar="COLUMN=VALUE")

    delete = subparsers.add_parser("delete", help="Remove a prompt.")
    delete.add_argument("id")
    delete.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")

    render = subparsers.add_parser("render", help="Fill a prompt's {{placeholders}}.")
    render.add_argument("id")
    render.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    render.add_argument("--strict", action="store_true")

    subparsers.add_parser("stats", help="Summarise the library.")

    import_cmd = subparsers.add_parser("import", help="Upsert records from a JSON array file.")
    import_cmd.add_argument("path", help="JSON file containing an array of objects, or '-'.")

    subparsers.add_parser("path", help="Print the CSV location.")
    return parser


def _add_facets(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tag", action="append", default=[], dest="tags")
    parser.add_argument("--category")
    parser.add_argument("--model")


def _parse_assignments(pairs: Sequence[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise PromptLibraryError(f"expected COLUMN=VALUE, got {pair!r}")
        key, _, value = pair.partition("=")
        key = key.strip()
        if not key:
            raise PromptLibraryError(f"empty column name in {pair!r}")
        values[key] = value
    return values


def _read_body(supplied: str | None) -> str:
    if supplied is None or supplied == "-":
        if sys.stdin.isatty():
            raise PromptLibraryError("no prompt text supplied (use --prompt or pipe stdin)")
        return sys.stdin.read()
    return supplied


class CommandRunner:
    """Maps parsed arguments onto service calls and formats the outcome."""

    def __init__(self, service: PromptLibraryService, as_json: bool) -> None:
        self._service = service
        self._as_json = as_json
        self._json = JsonFormatter()
        self._text = TextFormatter()

    def run(self, args: argparse.Namespace) -> int:
        handler = getattr(self, f"_cmd_{args.command.replace('-', '_')}", None)
        if handler is None:
            raise PromptLibraryError(f"unhandled command: {args.command}")
        return handler(args)

    # -- commands --------------------------------------------------------

    def _cmd_list(self, args: argparse.Namespace) -> int:
        rows = self._service.list(
            tags=args.tags,
            category=args.category,
            model=args.model,
            limit=args.limit,
            include_body=args.full,
        )
        return self._emit(rows, lambda payload: self._text.summaries(payload))

    def _cmd_search(self, args: argparse.Namespace) -> int:
        payload = self._service.search(
            query=" ".join(args.query),
            limit=args.limit,
            tags=args.tags,
            category=args.category,
            model=args.model,
            include_body=args.full,
        )
        return self._emit(payload, self._text.search)

    def _cmd_get(self, args: argparse.Namespace) -> int:
        payload = self._service.get(args.id)
        if args.body_only and not self._as_json:
            sys.stdout.write(str(payload.get("prompt", "")) + "\n")
            return EXIT_OK
        return self._emit(payload, self._text.record)

    def _cmd_add(self, args: argparse.Namespace) -> int:
        fields: dict[str, Any] = {
            "title": args.title,
            "prompt": _read_body(args.prompt),
            "tags": args.tags,
            "category": args.category,
            "model": args.model,
            "notes": args.notes,
            "source": args.source,
            "version": args.version,
        }
        fields.update(_parse_assignments(args.set))
        payload = self._service.add(fields, prompt_id=args.id)
        return self._emit(payload, lambda record: f"added {record['id']}")

    def _cmd_update(self, args: argparse.Namespace) -> int:
        changes: dict[str, Any] = {
            key: getattr(args, key)
            for key in ("title", "prompt", "tags", "category", "model", "notes", "source", "version")
            if getattr(args, key) is not None
        }
        changes.update(_parse_assignments(args.set))
        if not changes:
            raise PromptLibraryError("no changes supplied")
        payload = self._service.update(args.id, changes)
        return self._emit(payload, lambda record: f"updated {record['id']}")

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        if not args.yes and sys.stdin.isatty():
            answer = input(f"delete prompt {args.id!r}? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                sys.stderr.write("aborted\n")
                return EXIT_ERROR
        payload = self._service.delete(args.id)
        return self._emit(payload, lambda record: f"deleted {record['id']}")

    def _cmd_render(self, args: argparse.Namespace) -> int:
        payload = self._service.render(
            args.id, _parse_assignments(args.set), strict=args.strict
        )
        return self._emit(payload, lambda result: str(result.get("text", "")))

    def _cmd_stats(self, _args: argparse.Namespace) -> int:
        return self._emit(self._service.stats(), self._text.stats)

    def _cmd_import(self, args: argparse.Namespace) -> int:
        raw = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise PromptLibraryError("import expects a JSON array of objects")
        payload = self._service.import_rows(rows)
        return self._emit(payload, lambda result: f"wrote {result['written']} prompts")

    def _cmd_path(self, _args: argparse.Namespace) -> int:
        sys.stdout.write(str(self._service.csv_path) + "\n")
        return EXIT_OK

    # -- output ----------------------------------------------------------

    def _emit(self, payload: Any, render_text) -> int:
        if self._as_json:
            sys.stdout.write(self._json.render(payload) + "\n")
        else:
            sys.stdout.write(render_text(payload) + "\n")
        return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        service = PromptLibraryService.open(args.csv)
        return CommandRunner(service, args.json).run(args)
    except PromptLibraryError as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return EXIT_NOT_FOUND if type(exc).__name__ == "PromptNotFoundError" else EXIT_ERROR
    except BrokenPipeError:
        return EXIT_OK
    except KeyboardInterrupt:
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
