from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from cortex.brain import Brain
from cortex.integrations import connect, hook_response, install_hooks
from cortex.notes import parse_note
from cortex.security import Boundary, CortexError
from cortex.visualization import graph_html


def test_adversarial_text_is_bounded_and_linear(tmp_path):
    brain = Brain.initialize(tmp_path / "Brain")
    started = time.monotonic()
    for body in ["a" + "\n" * 200_000 + "b", "[" * 200_000]:
        note = brain.remember("Adversarial note", body)
        assert brain.read(note["id"])["content"].strip() == body.strip()
    assert time.monotonic() - started < 5


def test_directory_reads_do_not_leak_descriptors(tmp_path):
    brain = Brain.initialize(tmp_path / "Brain")
    (brain.root / "directory.md").mkdir()
    # Repetition exceeds usual macOS default FD limit if failed reads leak handles.
    for _ in range(600):
        with pytest.raises(CortexError):
            brain.boundary.read("directory.md")
    assert brain.status()["integrity"] == "ok"


@pytest.mark.parametrize(
    "body",
    [
        "created: 9999-12-31T23:00:00-05:00",
        "created: 2024-13-45",
        "status: [x]",
        "type: {a: 1}",
        "id: " + ("1" * 5000),
    ],
)
def test_malformed_metadata_has_domain_error(body):
    with pytest.raises(CortexError):
        parse_note("malformed.md", ("---\n" + body + "\n---\nbody").encode(), 0)


@pytest.mark.parametrize("path", ["./note.md", "inbox//note.md", "inbox/./note.md"])
def test_path_aliases_rejected(path):
    with pytest.raises(CortexError):
        Boundary.parts(path)


def test_graph_escapes_script_breakout():
    html = graph_html({"nodes": [{"title": "</script><script>alert(1)</script>"}], "edges": []})
    assert "</script><script>alert(1)" not in html
    data = html.split('id="graph-data">')[1].split("</script>")[0]
    assert json.loads(data)["nodes"][0]["title"].startswith("</script>")
    assert "connect-src" in html and "textContent" in html


def test_hook_never_reads_transcript_or_saves_prompt(tmp_path):
    brain = Brain.initialize(tmp_path / "Brain")
    marker = "RAW_PROMPT_SHOULD_NOT_BE_STORED"
    transcript = tmp_path / "private.jsonl"
    transcript.write_text(marker)
    before = sorted(brain.boundary.note_paths())
    for event in ["SessionStart", "UserPromptSubmit", "PreCompact", "Stop", "SessionEnd"]:
        result = hook_response(
            {
                "hook_event_name": event,
                "prompt": marker,
                "last_assistant_message": marker,
                "transcript_path": str(transcript),
            },
            brain.root,
        )
        assert marker not in json.dumps(result)
        if event in {"PreCompact", "Stop", "SessionEnd"}:
            assert result == {}
    assert before == brain.boundary.note_paths()
    assert marker not in "".join(p.read_text() for p in brain.root.rglob("*.md"))


def test_client_merge_backup_and_hooks_idempotency(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    brain = Brain.initialize(tmp_path / "Brain")
    target = tmp_path / ".lmstudio/mcp.json"
    target.parent.mkdir()
    original = {"mcpServers": {"existing": {"command": "do-not-touch"}}}
    target.write_text(json.dumps(original))
    result = connect("lm-studio", brain.root, apply=True)
    assert json.loads(Path(result["backup"]).read_text()) == original
    assert (
        json.loads(target.read_text())["mcpServers"]["existing"]
        == original["mcpServers"]["existing"]
    )
    assert "already registered" in connect("lm-studio", brain.root, apply=True)["status"]
    with pytest.raises(CortexError, match="different"):
        connect("lm-studio", brain.root, apply=True, writable=True)
    agents = tmp_path / ".codex/AGENTS.md"
    agents.parent.mkdir()
    agents.write_text("Existing user rules.\n")
    existing_hook = {
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo existing"}]}]}
    }
    (agents.parent / "hooks.json").write_text(json.dumps(existing_hook))
    result = install_hooks(brain.root, install=True)
    first = (agents.parent / "hooks.json").read_text()
    install_hooks(brain.root, install=True)
    assert first == (agents.parent / "hooks.json").read_text()
    assert agents.read_text().count("<!-- cortex:start -->") == 1
    assert agents.read_text().startswith("Existing user rules.")
    assert "echo existing" in first and "trusted_hash" not in first
    assert all(os.stat(p).st_mode & 0o777 == 0o600 for p in result["backups"])


def test_cli_human_and_machine_flow(tmp_path):
    root = str(tmp_path / "Brain")

    def run(*arguments):
        return subprocess.run(
            [sys.executable, "-m", "cortex.cli", "--brain", root, *arguments],
            capture_output=True,
            text=True,
            timeout=10,
        )

    assert run("init").returncode == 0
    result = run("--json", "remember", "A test memory.", "--title", "[red]literal title[/red]")
    note = json.loads(result.stdout)
    assert note["status"] == "candidate"
    assert run("search", "test").returncode == 0
    assert "[red]literal title[/red]" in run("search", "test").stdout
    assert run("doctor").returncode == 0
    assert run("--json", "read", "../escape.md").returncode == 1
    assert json.loads(run("--json", "read", "../escape.md").stdout)["error"]
    backed_up = json.loads(run("--json", "backup").stdout)
    assert Path(backed_up["backup"]).exists()
    graph = json.loads(run("--json", "graph").stdout)
    assert Path(graph["graph"]).exists()


def test_real_mcp_stdio_read_and_write(tmp_path):
    brain = Brain.initialize(tmp_path / "Brain")

    async def exercise(writable):
        args = ["-m", "cortex.cli", "--brain", str(brain.root), "serve"]
        if writable:
            args.append("--write")
        async with Client(StdioServerParameters(command=sys.executable, args=args)) as client:
            tools = await client.list_tools()
            assert len(tools.tools) == 11
            by_name = {tool.name: tool for tool in tools.tools}
            assert by_name["brain_read"].annotations.read_only_hint is True
            assert by_name["brain_remember"].annotations.read_only_hint is False
            assert "expected_hash" in by_name["brain_update"].input_schema["required"]
            result = await client.call_tool(
                "brain_remember",
                {
                    "title": "Shared MCP memory",
                    "content": "MCP fixture result.",
                    "source": "test-agent",
                    "source_ref": "test:stdio",
                },
            )
            if not writable:
                assert result.is_error
                return
            assert not result.is_error
            record = result.structured_content
            assert record["status"] == "candidate"
            search = await client.call_tool(
                "brain_search", {"query": "Shared MCP memory", "limit": 1}
            )
            assert search.structured_content["results"][0]["id"] == record["id"]
            reading = await client.call_tool("brain_read", {"identifier": record["path"]})
            assert reading.structured_content["source"] == "test-agent"
            traversal = await client.call_tool("brain_read", {"identifier": "../../.ssh/id_rsa"})
            assert traversal.is_error
            invalid = await client.call_tool("brain_search", {"query": "x", "limit": 101})
            assert invalid.is_error
            expire = await client.call_tool(
                "brain_forget", {"identifier": record["id"], "expected_hash": record["hash"]}
            )
            assert expire.structured_content["status"] == "expired"
            status = await client.call_tool("brain_status")
            assert status.structured_content["integrity"] == "ok"

    asyncio.run(exercise(False))
    asyncio.run(exercise(True))


def test_custom_frontmatter_values_survive_mutations(tmp_path):
    import yaml

    brain = Brain.initialize(tmp_path / "Brain")
    target = brain.root / "inbox/custom.md"
    target.write_text(
        "---\ntitle: Custom\ncssclasses: [dashboard]\ncustom:\n  nested: value\n  enabled: true\naliases: [Alternate]\n---\nOriginal body."
    )
    note = brain.read("inbox/custom.md")
    assert "_extra_yaml" not in note
    brain.update(note["id"], expected_hash=note["hash"], content="New body.")
    frontmatter = yaml.safe_load(target.read_text().split("---")[1])
    assert frontmatter["cssclasses"] == ["dashboard"]
    assert frontmatter["custom"] == {"nested": "value", "enabled": True}
    assert frontmatter["aliases"] == ["Alternate"]
