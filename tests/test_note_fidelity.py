"""Synthetic Markdown fidelity regressions through public storage operations."""

from __future__ import annotations

from pathlib import Path

import yaml

from cortex.brain import Brain


def test_status_only_update_preserves_initial_indented_code(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    body = "    print('first')\n    print('second')\n\nFinal line  \n\n"
    path = brain.root / "inbox/indented.md"
    path.write_text(body, encoding="utf-8")
    original = brain.read("inbox/indented.md")

    updated = brain.update(original["id"], expected_hash=original["hash"], status="superseded")

    assert updated["status"] == "superseded"
    assert updated["content"] == body
    assert brain.read(original["id"])["content"] == body


def test_status_update_preserves_custom_yaml_values_and_body(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    body = "    sample_code()\n\nA line with a hard break.  \nNext line.\n"
    custom = {"review": {"owner": "Synthetic Reviewer", "approved": False}, "aliases": ["Demo"]}
    metadata = {"title": "YAML fidelity", "status": "candidate", **custom}
    path = brain.root / "inbox/custom.md"
    path.write_text(
        "---\n# Human-authored comment\n"
        + yaml.safe_dump(metadata, sort_keys=False)
        + "---\n\n"
        + body,
        encoding="utf-8",
    )
    original = brain.read("inbox/custom.md")

    updated = brain.update(original["id"], expected_hash=original["hash"], status="expired")

    written_metadata = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])
    assert {key: written_metadata[key] for key in custom} == custom
    assert written_metadata["status"] == "expired"
    assert updated["content"] == body


def test_new_memory_preserves_code_indentation(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    body = "\tprint('tab-indented code')\n    print('space-indented code')"

    note = brain.remember("Code sample", body, source_ref="synthetic:fidelity")

    assert note["content"] == body + "\n"
    assert brain.read(note["id"])["content"] == body + "\n"


def test_capture_does_not_deduplicate_markdown_with_different_indentation(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    plain = brain.remember("Example", "sample()")
    code = brain.remember("Example", "    sample()")
    assert code["id"] != plain["id"]
    repeated = brain.remember("Example", "    sample()\n")
    assert repeated["id"] == code["id"]
    assert repeated["deduplicated"] is True
