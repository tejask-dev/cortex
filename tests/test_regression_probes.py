"""Focused regression candidates discovered by independent behavior review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from cortex.brain import Brain
from cortex.security import CortexError


def test_context_budget_includes_echoed_query(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    result = brain.context("q" * 1500, max_chars=1000)
    assert len(json.dumps(result, ensure_ascii=False)) <= 1000


def test_editor_change_before_original_backup_is_not_silently_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    note = brain.remember("Shared decision", "Initial text.")
    path = brain.root / note["path"]
    original_read = brain.boundary.read
    note_read_count = 0

    def editor_racing_read(identifier: str, **kwargs: Any) -> bytes:
        nonlocal note_read_count
        if identifier == note["path"]:
            note_read_count += 1
            if note_read_count == 2:
                # First read: index refresh. Second read: original backup during update.
                path.write_text(path.read_text().replace("Initial text.", "Human edit arrived."))
        return original_read(identifier, **kwargs)

    monkeypatch.setattr(brain.boundary, "read", editor_racing_read)
    with pytest.raises(CortexError, match="changed"):
        brain.update(note["id"], expected_hash=note["hash"], content="Agent replacement.")
    assert "Human edit arrived." in path.read_text()
