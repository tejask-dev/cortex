"""Regression coverage for explicit vault scope and deterministic identity lookup."""

from pathlib import Path

import pytest

from cortex.brain import Brain
from cortex.security import Boundary, CortexError


def test_uninitialized_existing_directory_is_not_adopted(tmp_path: Path) -> None:
    target = tmp_path / "ordinary-documents"
    target.mkdir()
    (target / "private.md").write_text("# Synthetic private note\n")
    with pytest.raises(CortexError, match="not initialized"):
        Brain(target)
    assert not (target / ".cortex").exists()
    assert (target / "private.md").read_text() == "# Synthetic private note\n"
    assert Brain.initialize(target).read("private.md")["title"] == "Synthetic private note"


@pytest.mark.parametrize("marker", ["[]", "{}", '{"schema":2}', '{"schema":true}', "broken"])
def test_invalid_marker_fails_without_creating_index(tmp_path: Path, marker: str) -> None:
    target = tmp_path / "Brain"
    (target / ".cortex").mkdir(parents=True)
    (target / ".cortex/config.json").write_text(marker)
    with pytest.raises(CortexError):
        Brain(target)
    assert not (target / ".cortex/brain.sqlite").exists()


def test_vault_cannot_be_home_ancestor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_home = tmp_path / "Users" / "test-user"
    fake_home.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    for target in [fake_home, fake_home.parent, tmp_path]:
        with pytest.raises(CortexError):
            Boundary(target)
        with pytest.raises(CortexError):
            Brain.initialize(target)
        assert not (target / ".cortex").exists()


def test_exact_path_wins_over_another_notes_id(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    (brain.root / "inbox/a.md").write_text("---\nid: inbox/b.md\ntitle: Shadow\n---\nWrong body\n")
    (brain.root / "inbox/b.md").write_text("# Intended note\nCorrect body\n")
    result = brain.read("inbox/b.md")
    assert result["path"] == "inbox/b.md"
    assert "Correct body" in result["content"]


def test_link_checks_read_hash_before_building_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    note = brain.remember("Stable version", "Expected source body")
    original = brain.read

    def intermediate(identifier: str):
        result = original(identifier)
        result["hash"] = "different-intermediate-version"
        result["content"] = "A transient edit that must never be copied"
        return result

    monkeypatch.setattr(brain, "read", intermediate)
    with pytest.raises(CortexError, match="before linking"):
        brain.link(note["id"], "Home", expected_hash=note["hash"])
    assert original(note["id"])["hash"] == note["hash"]
