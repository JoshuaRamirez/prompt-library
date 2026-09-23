"""`promptlib` command-line interface.

Argument parsing and exit codes only; every operation delegates to
`PromptLibraryService`. `promptlib --json <command>` emits the raw service
payload, which is also what the MCP tools return — one behaviour, two renderings.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from .. import __version__
from ..errors import PromptLibraryError, PromptNotFoundError
from ..service import PromptLibraryService
from .formatters import JsonFormatter, TextFormatter, plural

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2  # argparse's own code for a malformed command line
EXIT_NOT_FOUND = 3

_EPILOG = """exit status: 0 ok, 1 error, 2 bad command line, 3 no prompt with that id.
put --json anywhere to get the payload the MCP tools return."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptlib",
        description="A prompt library in one CSV file: save, search, fill in and reuse prompts.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--csv", metavar="PATH", help="the library file (default: $PROMPT_LIBRARY_CSV, "
                        "then $PROMPT_LIBRARY_HOME/prompts.csv, then ~/.claude/prompt-library/prompts.csv)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--version", action="version", version=f"promptlib {__version__}")
    # --json is accepted after the command too, where people tend to type it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print JSON instead of text")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    def command(name: str, summary: str, description: str | None = None) -> argparse.ArgumentParser:
        return subparsers.add_parser(name, parents=[common], help=summary, description=description or summary)

    listing = command("list", "List prompts, optionally narrowed by tag, category or model.")
    _add_facets(listing)
    listing.add_argument("--limit", type=int, metavar="N", help="show at most N")
    listing.add_argument("--full", action="store_true", help="include each prompt's text")

    search = command("search", "Find prompts by keyword, best match first.",
                     "Find prompts by keyword, best match first. Title counts most, then tags, "
                     "category, the prompt text and notes.")
    search.add_argument("query", nargs="+", help="words to look for")
    search.add_argument("--limit", type=int, default=10, metavar="N", help="show at most N (default 10)")
    search.add_argument("--full", action="store_true", help="include each prompt's text")
    _add_facets(search)

    get = command("get", "Show one prompt in full.")
    get.add_argument("id")
    get.add_argument("--body-only", action="store_true", help="print only the prompt text, for piping")

    add = command("add", "Save a new prompt.",
                  "Save a new prompt. The id is made from the title (or the text) unless you give one; "
                  "{{placeholders}} in the text are recorded as its variables.")
    add.add_argument("--id", help="the id to use (default: made from the title)")
    add.add_argument("--title", default="")
    add.add_argument("--prompt", metavar="TEXT", help="the prompt text; omit or use '-' to read stdin")
    add.add_argument("--tags", default="", metavar="A,B", help="comma-separated tags")
    add.add_argument("--category", default="")
    add.add_argument("--model", default="", help="the model the prompt is written for")
    add.add_argument("--notes", default="")
    add.add_argument("--source", default="", help="where the prompt came from")
    add.add_argument("--version", default="", help="your own version label for the prompt")
    add.add_argument("--set", action="append", default=[], metavar="COLUMN=VALUE",
                     help="set any column, including a new one; repeatable")

    update = command("update", "Change fields of a saved prompt; the rest stay as they are.")
    update.add_argument("id")
    for option, text in (
        ("title", None), ("prompt", "new prompt text (its variables are re-read)"),
        ("tags", "comma-separated tags, replacing the old ones"), ("category", None),
        ("model", None), ("notes", None), ("source", None), ("version", None),
    ):
        update.add_argument(f"--{option}", metavar="TEXT" if option == "prompt" else None, help=text)
    update.add_argument("--set", action="append", default=[], metavar="COLUMN=VALUE",
                        help="set any column, including a new one; repeatable")

    delete = command("delete", "Delete a prompt.",
                     "Delete a prompt. Asks first when run in a terminal; --yes skips the question.")
    delete.add_argument("id")
    delete.add_argument("--yes", action="store_true", help="do not ask for confirmation")

    render = command("render", "Fill in a prompt's {{placeholders}} and print it.")
    render.add_argument("id")
    render.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                        help="a value for one placeholder; repeatable")
    render.add_argument("--strict", action="store_true", help="fail if any placeholder is left unfilled")

    command("stats", "Summarise the library: size, columns, tags, categories.")

    import_cmd = command("import", "Add or update prompts from a JSON file.",
                         "Add or update prompts from a JSON array of objects. A record whose id "
                         "exists updates that prompt, changing only the fields it has; any other "
                         "record is added. Nothing is written unless every record is valid.")
    import_cmd.add_argument("path", help="the JSON file, or '-' for stdin")

    command("path", "Print where the library file is.")
    parser.set_defaults(commands=subparsers.choices)
    return parser


def _add_facets(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tag", action="append", default=[], dest="tags", metavar="TAG",
                        help="only prompts with this tag; repeat or comma-separate, all must match")
    parser.add_argument("--category", help="only prompts in this category")
    parser.add_argument("--model", help="only prompts for this model")


def _split_tags(values: Sequence[str]) -> list[str]:
    return [tag.strip() for value in values for tag in value.split(",") if tag.strip()]


def _parse_assignments(pairs: Sequence[str], label: str = "COLUMN=VALUE") -> dict[str, str]:
    values: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise PromptLibraryError(f"--set expects {label}, got {pair!r}")
        key, _, value = pair.partition("=")
        key = key.strip()
        if not key:
            raise PromptLibraryError(f"--set has an empty name in {pair!r}")
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
            tags=_split_tags(args.tags),
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
            tags=_split_tags(args.tags),
            category=args.category,
            model=args.model,
            include_body=args.full,
        )
        return self._emit(payload, self._text.search)

    def _cmd_get(self, args: argparse.Namespace) -> int:
        payload = self._service.get(args.id)
        if args.body_only:
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
        return self._emit(payload, lambda record: _saved("added", record))

    def _cmd_update(self, args: argparse.Namespace) -> int:
        changes: dict[str, Any] = {
            key: getattr(args, key)
            for key in ("title", "prompt", "tags", "category", "model", "notes", "source", "version")
            if getattr(args, key) is not None
        }
        changes.update(_parse_assignments(args.set))
        if not changes:
            raise PromptLibraryError("nothing to change: give at least one of --title, --prompt, --tags, … or --set")
        payload = self._service.update(args.id, changes)
        return self._emit(payload, lambda record: _saved("updated", record))

    def _cmd_delete(self, args: argparse.Namespace) -> int:
        if not args.yes and sys.stdin.isatty():
            self._service.get(args.id)  # fail on an unknown id before asking
            try:
                answer = input(f"delete prompt {args.id!r}? [y/N] ").strip().lower()
            except EOFError:
                answer = ""
                sys.stderr.write("\n")
            if answer not in ("y", "yes"):
                sys.stderr.write("not deleted\n")
                return EXIT_ERROR
        payload = self._service.delete(args.id)
        return self._emit(payload, lambda record: f"deleted {record['id']}")

    def _cmd_render(self, args: argparse.Namespace) -> int:
        payload = self._service.render(
            args.id, _parse_assignments(args.set, "NAME=VALUE"), strict=args.strict
        )
        if not self._as_json:
            notes = []
            if payload.get("unfilled"):
                notes.append(f"unfilled: {', '.join(payload['unfilled'])}")
            if payload.get("unused"):
                notes.append(f"not in this prompt: {', '.join(payload['unused'])}")
            if notes:
                sys.stderr.write(f"promptlib: warning: {'; '.join(notes)}\n")
        return self._emit(payload, lambda result: str(result.get("text", "")))

    def _cmd_stats(self, _args: argparse.Namespace) -> int:
        return self._emit(self._service.stats(), self._text.stats)

    def _cmd_import(self, args: argparse.Namespace) -> int:
        try:
            if args.path == "-":
                raw = sys.stdin.read()
            else:
                with open(args.path, encoding="utf-8") as handle:
                    raw = handle.read()
            rows = json.loads(raw)
        except OSError as exc:
            raise PromptLibraryError(f"cannot read {args.path}: {exc.strerror or exc}") from exc
        except json.JSONDecodeError as exc:
            raise PromptLibraryError(f"{args.path} is not valid JSON: {exc}") from exc
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise PromptLibraryError("import expects a JSON array of objects")
        payload = self._service.import_rows(rows)
        return self._emit(payload, lambda result: f"imported {plural(result['written'], 'prompt')}")

    def _cmd_path(self, _args: argparse.Namespace) -> int:
        return self._emit({"csv_path": str(self._service.csv_path)}, lambda payload: payload["csv_path"])

    # -- output ----------------------------------------------------------

    def _emit(self, payload: Any, render_text) -> int:
        if self._as_json:
            sys.stdout.write(self._json.render(payload) + "\n")
        else:
            sys.stdout.write(render_text(payload) + "\n")
        return EXIT_OK


def _saved(verb: str, record: dict[str, Any]) -> str:
    line = f"{verb} {record['id']}"
    if record.get("new_columns"):
        line += f" (new column: {', '.join(record['new_columns'])})"
    return line


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_USAGE
    if extra:
        hint = ""
        if args.command == "render" and any("=" in item and not item.startswith("-") for item in extra):
            hint = " (values go in as --set name=value)"
        args.commands[args.command].error(f"unrecognized arguments: {' '.join(extra)}{hint}")
    try:
        service = PromptLibraryService.open(args.csv)
        return CommandRunner(service, args.json).run(args)
    except PromptLibraryError as exc:
        sys.stderr.write(f"promptlib: error: {exc}\n")
        return EXIT_NOT_FOUND if isinstance(exc, PromptNotFoundError) else EXIT_ERROR
    except BrokenPipeError:
        return EXIT_OK
    except OSError as exc:
        where = f" {exc.filename}" if exc.filename else ""
        sys.stderr.write(f"promptlib: error: cannot use{where}: {exc.strerror or exc}\n")
        return EXIT_ERROR
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
