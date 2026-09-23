"""Behavioural tests for the prompt library core and its adapters.

Standard library unittest only, so the suite runs anywhere the plugin runs:
    python3 tests/test_promptlib.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from promptlib.clock import FrozenClock  # noqa: E402
from promptlib.domain.prompt import Prompt  # noqa: E402
from promptlib.domain.prompt_filter import PromptFilter  # noqa: E402
from promptlib.errors import (  # noqa: E402
    DuplicatePromptError,
    InvalidArgumentError,
    InvalidPromptError,
    PromptNotFoundError,
    RenderError,
)
from promptlib.identifiers import SlugFactory  # noqa: E402
from promptlib.mcp.jsonrpc import StdioTransport  # noqa: E402
from promptlib.mcp.server import McpServer  # noqa: E402
from promptlib.rendering.template_renderer import TemplateRenderer  # noqa: E402
from promptlib.search.keyword_strategy import KeywordSearchStrategy  # noqa: E402
from promptlib.service import PromptLibraryService  # noqa: E402
from promptlib.storage.table_schema import TableSchema  # noqa: E402


class ServiceTestCase(unittest.TestCase):
    """Base fixture: a service over a throwaway CSV with a frozen clock."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.csv_path = Path(self._tmp.name) / "prompts.csv"
        self.service = PromptLibraryService.open(
            self.csv_path, clock=FrozenClock("2026-07-25T00:00:00+00:00")
        )
        self.addCleanup(self._tmp.cleanup)

    def read_csv(self) -> tuple[list[str], list[dict[str, str]]]:
        with self.csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or []), list(reader)


class SlugFactoryTests(unittest.TestCase):
    def test_slugify_normalizes_text(self) -> None:
        factory = SlugFactory()
        self.assertEqual(factory.slugify("  Code Review: Strict!  "), "code-review-strict")
        self.assertEqual(factory.slugify("Café Résumé"), "cafe-resume")
        self.assertEqual(factory.slugify("!!!"), "prompt")

    def test_unique_suffixes_on_collision(self) -> None:
        factory = SlugFactory()
        self.assertEqual(factory.unique("Review", {"review"}), "review-2")
        self.assertEqual(factory.unique("Review", {"review", "review-2"}), "review-3")


class TableSchemaTests(unittest.TestCase):
    def test_discovered_columns_follow_declared(self) -> None:
        schema = TableSchema(("id", "prompt"), ("id", "owner", "prompt", "rating"))
        self.assertEqual(schema.columns, ("id", "prompt", "owner", "rating"))

    def test_normalize_fills_absent_columns(self) -> None:
        schema = TableSchema(("id", "prompt"))
        self.assertEqual(schema.normalize({"id": "x"}), {"id": "x", "prompt": ""})


class PromptRecordTests(unittest.TestCase):
    def test_round_trip_through_row(self) -> None:
        original = Prompt.from_fields(
            {"id": "a", "prompt": "body", "tags": ["x", "y"], "owner": "joshua"}
        )
        restored = Prompt.from_row(original.to_row())
        self.assertEqual(restored.tags, ("x", "y"))
        self.assertEqual(restored.extras, {"owner": "joshua"})

    def test_merge_routes_unknown_keys_to_extras(self) -> None:
        merged = Prompt.from_fields({"id": "a", "prompt": "b"}).merged_with({"rating": "5"})
        self.assertEqual(merged.extras["rating"], "5")

    def test_merge_ignores_managed_columns(self) -> None:
        merged = Prompt.from_fields({"id": "a", "prompt": "b"}).merged_with({"id": "z"})
        self.assertEqual(merged.id, "a")

    def test_validation_rejects_empty_body(self) -> None:
        with self.assertRaises(InvalidPromptError):
            Prompt.from_fields({"id": "a", "prompt": "  "}).validate()


class RendererTests(unittest.TestCase):
    def test_substitutes_and_reports_unfilled(self) -> None:
        result = TemplateRenderer().render("Hi {{name}}, {{missing}}", {"name": "Joshua"})
        self.assertEqual(result.text, "Hi Joshua, {{missing}}")
        self.assertEqual(result.substituted, ("name",))
        self.assertEqual(result.unfilled, ("missing",))

    def test_strict_mode_raises(self) -> None:
        with self.assertRaises(RenderError):
            TemplateRenderer().render("{{a}}", {}, strict=True)

    def test_single_braces_are_left_alone(self) -> None:
        body = 'Return {"ok": true} and {{value}}'
        result = TemplateRenderer().render(body, {"value": "1"})
        self.assertEqual(result.text, 'Return {"ok": true} and 1')


class FilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompts = [
            Prompt.from_fields({"id": "a", "prompt": "x", "tags": "review, code", "category": "Eng"}),
            Prompt.from_fields({"id": "b", "prompt": "y", "tags": "review", "category": "docs"}),
        ]

    def test_tag_conjunction(self) -> None:
        matched = PromptFilter.build(tags=["review", "code"]).apply(self.prompts)
        self.assertEqual([p.id for p in matched], ["a"])

    def test_category_is_case_insensitive(self) -> None:
        matched = PromptFilter.build(category="eng").apply(self.prompts)
        self.assertEqual([p.id for p in matched], ["a"])

    def test_empty_filter_passes_everything(self) -> None:
        self.assertEqual(len(PromptFilter.build().apply(self.prompts)), 2)


class KeywordSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompts = [
            Prompt.from_fields(
                {"id": "code-review", "title": "Strict code review", "prompt": "Review the diff.",
                 "tags": "review, engineering"}
            ),
            Prompt.from_fields(
                {"id": "recipe", "title": "Dinner ideas", "prompt": "Suggest a recipe.", "tags": "home"}
            ),
        ]
        self.strategy = KeywordSearchStrategy()

    def test_title_outranks_body(self) -> None:
        hits = self.strategy.search("code review", self.prompts)
        self.assertEqual(hits[0].prompt.id, "code-review")
        self.assertIn("title", hits[0].matched_fields)

    def test_non_matching_query_returns_nothing(self) -> None:
        self.assertEqual(self.strategy.search("quantum chromodynamics", self.prompts), [])

    def test_limit_is_honoured(self) -> None:
        hits = self.strategy.search("review recipe", self.prompts, limit=1)
        self.assertEqual(len(hits), 1)


class ServiceLifecycleTests(ServiceTestCase):
    def test_initialize_writes_header_only(self) -> None:
        header, rows = self.read_csv()
        self.assertEqual(header[0], "id")
        self.assertEqual(rows, [])

    def test_add_derives_id_from_title(self) -> None:
        record = self.service.add({"title": "Code Review Strict", "prompt": "Review it."})
        self.assertEqual(record["id"], "code-review-strict")
        self.assertEqual(record["created_at"], "2026-07-25T00:00:00+00:00")

    def test_add_rejects_duplicate_explicit_id(self) -> None:
        self.service.add({"prompt": "one"}, prompt_id="dup")
        with self.assertRaises(DuplicatePromptError):
            self.service.add({"prompt": "two"}, prompt_id="dup")

    def test_add_detects_declared_variables(self) -> None:
        record = self.service.add({"title": "T", "prompt": "Hello {{name}} and {{place}}"})
        self.assertEqual(record["variables"], ["name", "place"])

    def test_unknown_field_becomes_a_new_column(self) -> None:
        self.service.add({"title": "T", "prompt": "body", "rating": "5"})
        header, rows = self.read_csv()
        self.assertIn("rating", header)
        self.assertEqual(rows[0]["rating"], "5")

    def test_extra_columns_survive_unrelated_updates(self) -> None:
        record = self.service.add({"title": "T", "prompt": "body", "rating": "5"})
        self.service.add({"title": "Other", "prompt": "second"})
        self.service.update(record["id"], {"notes": "checked"})
        _, rows = self.read_csv()
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id[record["id"]]["rating"], "5")
        self.assertEqual(by_id[record["id"]]["notes"], "checked")

    def test_update_missing_id_raises(self) -> None:
        with self.assertRaises(PromptNotFoundError):
            self.service.update("nope", {"notes": "x"})

    def test_delete_removes_row(self) -> None:
        record = self.service.add({"title": "T", "prompt": "body"})
        self.service.delete(record["id"])
        self.assertEqual(self.service.list(), [])
        with self.assertRaises(PromptNotFoundError):
            self.service.get(record["id"])

    def test_multiline_and_comma_bodies_round_trip(self) -> None:
        body = 'Line one, with comma\nLine "two"\n\nLine three'
        record = self.service.add({"title": "Tricky", "prompt": body})
        self.assertEqual(self.service.get(record["id"])["prompt"], body)

    def test_render_fills_placeholders(self) -> None:
        record = self.service.add({"title": "Greet", "prompt": "Hi {{name}}"})
        rendered = self.service.render(record["id"], {"name": "Joshua"})
        self.assertEqual(rendered["text"], "Hi Joshua")
        self.assertEqual(rendered["declared_variables"], ["name"])

    def test_search_reports_strategy_and_candidates(self) -> None:
        self.service.add({"title": "Code review", "prompt": "Review the diff", "tags": "eng"})
        self.service.add({"title": "Dinner", "prompt": "Suggest a recipe", "tags": "home"})
        payload = self.service.search("review")
        self.assertEqual(payload["strategy"], "keyword")
        self.assertEqual(payload["candidates"], 2)
        self.assertEqual(payload["results"][0]["id"], "code-review")

    def test_search_facets_constrain_before_ranking(self) -> None:
        self.service.add({"title": "Code review", "prompt": "Review the diff", "tags": "eng"})
        self.service.add({"title": "Doc review", "prompt": "Review the doc", "tags": "docs"})
        payload = self.service.search("review", tags=["docs"])
        self.assertEqual(payload["candidates"], 1)
        self.assertEqual(payload["results"][0]["id"], "doc-review")

    def test_stats_reports_extra_columns(self) -> None:
        self.service.add({"title": "T", "prompt": "b", "tags": "a, b", "rating": "5"})
        stats = self.service.stats()
        self.assertEqual(stats["count"], 1)
        self.assertIn("rating", stats["extra_columns"])
        self.assertEqual(stats["tags"], {"a": 1, "b": 1})

    def test_import_upserts_by_id(self) -> None:
        self.service.add({"prompt": "original"}, prompt_id="p1")
        result = self.service.import_rows([
            {"id": "p1", "prompt": "replaced"},
            {"id": "p2", "prompt": "new"},
        ])
        self.assertEqual(result["written"], 2)
        self.assertEqual(self.service.get("p1")["prompt"], "replaced")
        self.assertEqual(len(self.service.list()), 2)

    def test_reopening_sees_persisted_state(self) -> None:
        self.service.add({"title": "Persisted", "prompt": "body", "rating": "5"})
        reopened = PromptLibraryService.open(self.csv_path)
        record = reopened.get("persisted")
        self.assertEqual(record["extras"]["rating"], "5")


class McpServerTests(ServiceTestCase):
    """Drives the MCP server over in-memory pipes."""

    def _exchange(self, messages: list[dict]) -> list[dict]:
        stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
        stdout = io.StringIO()
        McpServer(self.service, StdioTransport(stdin, stdout)).serve_forever()
        return [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]

    def test_initialize_advertises_tools(self) -> None:
        responses = self._exchange([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("tools", responses[0]["result"]["capabilities"])
        names = {tool["name"] for tool in responses[1]["result"]["tools"]}
        self.assertEqual(
            names,
            {
                "prompt_search", "prompt_list", "prompt_get", "prompt_add",
                "prompt_update", "prompt_delete", "prompt_render", "prompt_stats",
            },
        )

    def test_notifications_produce_no_response(self) -> None:
        self.assertEqual(self._exchange([{"jsonrpc": "2.0", "method": "notifications/initialized"}]), [])

    def test_tool_call_round_trip(self) -> None:
        responses = self._exchange([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "prompt_add",
                        "arguments": {"title": "Via MCP", "prompt": "Do {{thing}}", "owner": "j"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "prompt_search", "arguments": {"query": "via mcp"}}},
        ])
        added = json.loads(responses[0]["result"]["content"][0]["text"])
        self.assertEqual(added["id"], "via-mcp")
        self.assertEqual(added["extras"], {"owner": "j"})
        found = json.loads(responses[1]["result"]["content"][0]["text"])
        self.assertEqual(found["results"][0]["id"], "via-mcp")

    def test_domain_error_returns_tool_error_not_protocol_error(self) -> None:
        responses = self._exchange([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "prompt_get", "arguments": {"id": "absent"}}},
        ])
        self.assertTrue(responses[0]["result"]["isError"])
        self.assertIn("PromptNotFoundError", responses[0]["result"]["content"][0]["text"])

    def test_unknown_method_is_a_protocol_error(self) -> None:
        responses = self._exchange([{"jsonrpc": "2.0", "id": 1, "method": "nope/nope"}])
        self.assertEqual(responses[0]["error"]["code"], -32601)

    def test_server_version_matches_plugin_manifest(self) -> None:
        manifest = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
        responses = self._exchange([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
        ])
        self.assertEqual(
            responses[0]["result"]["serverInfo"]["version"],
            json.loads(manifest.read_text(encoding="utf-8"))["version"],
        )

    def test_bad_limit_is_a_clean_tool_error(self) -> None:
        responses = self._exchange([
            {"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": tool, "arguments": args}}
            for i, (tool, args) in enumerate([
                ("prompt_list", {"limit": "abc"}),
                ("prompt_search", {"query": "x", "limit": -1}),
            ], start=1)
        ])
        for response in responses:
            text = response["result"]["content"][0]["text"]
            self.assertTrue(response["result"]["isError"])
            self.assertTrue(text.startswith("InvalidArgumentError: limit must be a positive integer"), text)

    def test_malformed_line_does_not_kill_the_server(self) -> None:
        stdin = io.StringIO("{not json}\n" + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}) + "\n")
        stdout = io.StringIO()
        McpServer(self.service, StdioTransport(stdin, stdout)).serve_forever()
        responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[1]["result"], {})



class PolishRegressionTests(ServiceTestCase):
    """Rough edges found in the 0.1.3 review, each pinned so it stays fixed."""

    def setUp(self) -> None:
        super().setUp()
        self.service.add(
            {"title": "Summarise", "prompt": "Summarise {{doc}}", "tags": ["reading"], "category": "writing"},
            prompt_id="summarise",
        )

    def test_import_changes_only_the_fields_it_supplies(self) -> None:
        self.service.import_rows([{"id": "summarise", "tags": "new"}])
        record = self.service.get("summarise")
        self.assertEqual(record["tags"], ["new"])
        self.assertEqual(record["title"], "Summarise")
        self.assertEqual(record["prompt"], "Summarise {{doc}}")
        self.assertEqual(record["category"], "writing")

    def test_import_derives_variables_from_a_new_body(self) -> None:
        self.service.import_rows([{"id": "n1", "prompt": "hi {{who}}"}, {"id": "summarise", "prompt": "Read {{url}}"}])
        self.assertEqual(self.service.get("n1")["variables"], ["who"])
        self.assertEqual(self.service.get("summarise")["variables"], ["url"])

    def test_import_names_the_record_that_failed_and_writes_nothing(self) -> None:
        with self.assertRaisesRegex(InvalidPromptError, r"^record 2 \(empty\): prompt body must not be empty$"):
            self.service.import_rows([{"id": "ok", "prompt": "fine"}, {"id": "empty", "title": "x"}])
        self.assertEqual([row["id"] for row in self.service.list()], ["summarise"])

    def test_import_round_trips_the_full_json_listing(self) -> None:
        exported = self.service.list(include_body=True)
        self.service.import_rows(exported)
        self.assertEqual(self.service.get("summarise")["title"], "Summarise")

    def test_update_refuses_managed_columns(self) -> None:
        with self.assertRaisesRegex(InvalidArgumentError, "'id' is managed"):
            self.service.update("summarise", {"id": "renamed"})
        with self.assertRaisesRegex(InvalidArgumentError, "'created_at' is managed"):
            self.service.add({"prompt": "x", "created_at": "2000-01-01"})

    def test_empty_update_is_an_error(self) -> None:
        with self.assertRaisesRegex(InvalidArgumentError, "no changes supplied"):
            self.service.update("summarise", {})

    def test_object_values_are_refused(self) -> None:
        with self.assertRaisesRegex(InvalidArgumentError, "'notes' must be text, not dict"):
            self.service.update("summarise", {"notes": {"k": 1}})

    def test_writes_report_new_columns(self) -> None:
        self.assertEqual(self.service.update("summarise", {"team": "docs"})["new_columns"], ["team"])
        self.assertNotIn("new_columns", self.service.update("summarise", {"team": "ops"}))

    def test_blank_extras_are_not_reported(self) -> None:
        self.service.update("summarise", {"team": "docs"})
        self.assertNotIn("extras", self.service.add({"prompt": "other"}))

    def test_stats_count_tags_and_categories_ignoring_case(self) -> None:
        self.service.add({"prompt": "b", "tags": ["Reading"], "category": "Writing"})
        stats = self.service.stats()
        self.assertEqual(stats["tags"], {"reading": 2})
        self.assertEqual(stats["categories"], {"writing": 2})

    def test_render_reports_values_nothing_used(self) -> None:
        result = self.service.render("summarise", {"dco": "typo"})
        self.assertEqual(result["unused"], ["dco"])
        self.assertEqual(result["unfilled"], ["doc"])

    def test_unreadable_files_are_store_errors(self) -> None:
        from promptlib.errors import StoreCorruptionError

        binary = Path(self._tmp.name) / "binary.csv"
        binary.write_bytes(b"id,prompt\n\xff\xfe,x\n")
        with self.assertRaisesRegex(StoreCorruptionError, "not UTF-8 text"):
            PromptLibraryService.open(binary).list()
        foreign = Path(self._tmp.name) / "foreign.csv"
        foreign.write_text("name,email\nx,y\n", encoding="utf-8")
        with self.assertRaisesRegex(StoreCorruptionError, "no 'id' column"):
            PromptLibraryService.open(foreign).list()


class CliTests(ServiceTestCase):
    """Exercises the CLI end to end against the temporary CSV."""

    def _run(self, *argv: str) -> tuple[int, str]:
        from promptlib.cli.main import main

        buffer = io.StringIO()
        original = sys.stdout
        sys.stdout = buffer
        try:
            code = main(["--csv", str(self.csv_path), *argv])
        finally:
            sys.stdout = original
        return code, buffer.getvalue()

    def _run_err(self, *argv: str) -> tuple[int, str, str]:
        err = io.StringIO()
        original = sys.stderr
        sys.stderr = err
        try:
            try:
                code, out = self._run(*argv)
            except SystemExit as exit_:
                code, out = int(exit_.code or 0), ""
        finally:
            sys.stderr = original
        return code, out, err.getvalue()

    def test_json_is_accepted_after_the_command(self) -> None:
        self._run("add", "--prompt", "x {{y}}", "--title", "T")
        code, out = self._run("list", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]["id"], "t")
        code, out = self._run("path", "--json")
        self.assertEqual(json.loads(out)["csv_path"], str(self.csv_path))

    def test_unknown_flag_names_the_subcommand(self) -> None:
        code, _, err = self._run_err("search", "review", "--limt", "2")
        self.assertEqual(code, 2)
        self.assertIn("usage: promptlib search", err)
        self.assertIn("unrecognized arguments: --limt 2", err)
        _, _, err = self._run_err("render", "x", "language=Go")
        self.assertIn("values go in as --set name=value", err)

    def test_errors_are_plain_sentences(self) -> None:
        code, _, err = self._run_err("get", "absent")
        self.assertEqual(err, "promptlib: error: no prompt with id 'absent'\n")

    def test_render_warns_about_unfilled_and_unused_names(self) -> None:
        self._run("add", "--id", "r", "--prompt", "Review {{language}} code")
        code, out, err = self._run_err("render", "r", "--set", "langauge=Go")
        self.assertEqual(code, 0)
        self.assertEqual(out, "Review {{language}} code\n")
        self.assertIn("unfilled: language; not in this prompt: langauge", err)

    def test_tag_filter_accepts_commas(self) -> None:
        self._run("add", "--id", "a", "--prompt", "x", "--tags", "review,code")
        self._run("add", "--id", "b", "--prompt", "y", "--tags", "review")
        _, out = self._run("--json", "list", "--tag", "review,code")
        self.assertEqual([row["id"] for row in json.loads(out)], ["a"])

    def test_listing_shows_each_tag_and_untitled_rows(self) -> None:
        self._run("add", "--id", "a", "--prompt", "x", "--tags", "review,code")
        _, out = self._run("list")
        self.assertIn("(untitled)  #review #code", out)

    def test_no_command_prints_help(self) -> None:
        code, out, _ = self._run_err()
        self.assertEqual(code, 2)
        self.assertIn("<command>", out)

    def test_add_then_get_body_only(self) -> None:
        code, _ = self._run("add", "--title", "CLI Prompt", "--prompt", "Body here", "--tags", "a,b")
        self.assertEqual(code, 0)
        code, out = self._run("get", "cli-prompt", "--body-only")
        self.assertEqual(out.strip(), "Body here")

    def test_set_creates_arbitrary_column(self) -> None:
        self._run("add", "--title", "X", "--prompt", "b", "--set", "rating=5", "--set", "owner=j")
        code, out = self._run("--json", "get", "x")
        payload = json.loads(out)
        self.assertEqual(payload["extras"], {"rating": "5", "owner": "j"})

    def test_search_json_payload(self) -> None:
        self._run("add", "--title", "Refactor helper", "--prompt", "Refactor this module")
        code, out = self._run("--json", "search", "refactor")
        payload = json.loads(out)
        self.assertEqual(payload["results"][0]["id"], "refactor-helper")

    def test_render_writes_filled_text(self) -> None:
        self._run("add", "--title", "Greet", "--prompt", "Hi {{name}}")
        code, out = self._run("render", "greet", "--set", "name=Joshua")
        self.assertEqual(out.strip(), "Hi Joshua")

    def test_missing_prompt_exits_not_found(self) -> None:
        code, _ = self._run("get", "absent")
        self.assertEqual(code, 3)

    def test_limited_search_reports_all_matches(self) -> None:
        self._run("add", "--title", "Review code", "--prompt", "review a")
        self._run("add", "--title", "Review docs", "--prompt", "review b")
        _, out = self._run("search", "review", "--limit", "1")
        self.assertTrue(out.startswith("2 of 2 prompts matched 'review', showing the top 1"), out)

    def test_nonpositive_limit_is_rejected(self) -> None:
        code, _ = self._run("list", "--limit", "-1")
        self.assertEqual(code, 1)

    def test_empty_body_message_is_plain(self) -> None:
        with self.assertRaisesRegex(InvalidPromptError, "^prompt body must not be empty$"):
            self.service.add({"prompt": ""})

    def test_list_full_prints_bodies(self) -> None:
        self._run("add", "--title", "Multi", "--prompt", "first line\nsecond line")
        _, summary = self._run("list")
        _, full = self._run("list", "--full")
        self.assertNotIn("second line", summary)
        self.assertIn("    first line\n    second line", full)

    def test_import_rejects_bad_input_without_traceback(self) -> None:
        bad = self.csv_path.parent / "bad.json"
        for content in ("{not json", "[1, 2]"):
            bad.write_text(content, encoding="utf-8")
            code, _ = self._run("import", str(bad))
            self.assertEqual(code, 1)
        code, _ = self._run("import", str(self.csv_path.parent / "missing.json"))
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
