"""Automatic context isolation and fail-closed client config registration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cortex import integrations
from cortex.brain import Brain
from cortex.security import CortexError


def test_session_start_only_injects_confirmed_identity_preferences_and_goals(
    tmp_path: Path,
) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    allowed = [
        brain.remember("Identity", "SYNTHETIC_CONFIRMED_IDENTITY", kind="identity", confirmed=True),
        brain.remember(
            "Preference", "SYNTHETIC_CONFIRMED_PREFERENCE", kind="preference", confirmed=True
        ),
        brain.remember("Goal", "SYNTHETIC_CONFIRMED_GOAL", kind="goal", confirmed=True),
    ]
    excluded = [
        brain.remember("Candidate identity", "SYNTHETIC_CANDIDATE_IDENTITY", kind="identity"),
        brain.remember(
            "Recent session", "SYNTHETIC_RECENT_SESSION", kind="session", confirmed=True
        ),
        brain.remember("Recent note", "SYNTHETIC_RECENT_NOTE", confirmed=True),
        brain.remember("Candidate goal", "SYNTHETIC_CANDIDATE_GOAL", kind="goal"),
    ]
    result = integrations.hook_response({"hook_event_name": "SessionStart"}, brain.root)
    text = result["hookSpecificOutput"]["additionalContext"]
    context = json.loads(text.split("\n", 1)[1])
    assert {note["id"] for note in context["memories"]} == {note["id"] for note in allowed}
    assert context["trust"] == "untrusted_data"
    assert "NOT instructions" in text
    for note in context["memories"]:
        assert note["status"] == "confirmed"
        assert note["trust"] == "untrusted_data"
        assert {"path", "source", "source_ref", "confidence", "updated"} <= note.keys()
    for note in excluded:
        assert note["content"].strip() not in text
        # Explicit retrieval still provides access to relevant candidate/session records.
        assert brain.read(note["id"])["id"] == note["id"]


def test_session_start_is_bounded_and_does_not_capture_event_fields(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    for index in range(4):
        brain.remember(
            f"Preference {index}",
            "Detailed synthetic preference. " * 40,
            kind="preference",
            source="manual-user",
            source_ref="synthetic:" + "p" * 850,
            confirmed=True,
        )
    raw = "SYNTHETIC_RAW_EVENT_MUST_NOT_BE_READ_OR_SAVED"
    transcript = tmp_path / "private-transcript.jsonl"
    transcript.write_text(raw)
    before = dict(brain.snapshot())
    result = integrations.hook_response(
        {
            "hook_event_name": "SessionStart",
            "prompt": raw,
            "last_assistant_message": raw,
            "transcript_path": str(transcript),
            "cwd": raw,
            "session_id": raw,
        },
        brain.root,
    )
    text = result["hookSpecificOutput"]["additionalContext"]
    context = json.loads(text.split("\n", 1)[1])
    assert len(text) <= 4000
    assert context["truncated"] is True
    assert raw not in json.dumps(result)
    assert dict(brain.snapshot()) == before


@pytest.mark.parametrize(
    ("client", "content"),
    [
        ("codex", "mcp_servers = []\n"),
        ("codex", 'mcp_servers = "invalid"\n'),
        ("codex", "[mcp_servers]\ncortex = []\n"),
        ("codex", '[mcp_servers]\ncortex = "invalid"\n'),
        ("codex", "[mcp_servers]\ncortex = true\n"),
        ("codex", "[mcp_servers\n"),
        ("lm-studio", "[]"),
        ("lm-studio", '{"mcpServers": []}'),
        ("lm-studio", '{"mcpServers": {"cortex": []}}'),
        ("lm-studio", '{"mcpServers": {"cortex": "invalid"}}'),
        ("lm-studio", '{"mcpServers": {"cortex": null}}'),
        ("lm-studio", '{"mcpServers": {"cortex": false}}'),
        ("lm-studio", '{"mcpServers":'),
    ],
)
def test_malformed_client_config_is_rejected_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, client: str, content: str
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    brain = Brain.initialize(tmp_path / "Brain")
    path = integrations.client_path(client)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    before = path.read_bytes()
    before_files = sorted(p.name for p in path.parent.iterdir())

    def must_not_be_called(*args: object, **kwargs: object) -> None:
        pytest.fail("Invalid config must not trigger subprocesses, backups, or writes")

    monkeypatch.setattr(integrations.subprocess, "run", must_not_be_called)
    monkeypatch.setattr(integrations, "backup_config", must_not_be_called)
    monkeypatch.setattr(integrations, "write_config", must_not_be_called)

    with pytest.raises(CortexError):
        integrations.connect(client, brain.root, apply=True)

    assert path.read_bytes() == before
    assert sorted(p.name for p in path.parent.iterdir()) == before_files


def test_valid_existing_codex_table_remains_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    brain = Brain.initialize(tmp_path / "Brain")
    config = integrations.server_config(brain.root, writable=False)
    path = integrations.client_path("codex")
    path.parent.mkdir()
    text = (
        "# Preserve comments and unrelated registration.\n"
        '[mcp_servers.existing]\ncommand = "unrelated"\n'
        "[mcp_servers.cortex]\n"
        f"command = {json.dumps(config['command'])}\n"
        f"args = {json.dumps(config['args'])}\n"
    )
    path.write_text(text)
    result = integrations.connect("codex", brain.root, apply=True)
    assert "already registered" in result["status"]
    assert path.read_text() == text
    assert list(path.parent.iterdir()) == [path]
