"""Synthetic backup regression tests; import the implementation under test normally."""

from __future__ import annotations

import stat
import tarfile
from pathlib import Path

import pytest

from cortex.brain import Brain
from cortex.cli import backup
from cortex.security import CortexError


def test_default_backup_rejects_symlinked_backups_directory(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    brain.remember("Private choice", "Synthetic private note stays within the chosen vault.")
    outside = tmp_path / "unselected-destination"
    outside.mkdir()
    (brain.root / ".cortex/backups").symlink_to(outside, target_is_directory=True)

    with pytest.raises(CortexError, match="Unsafe|inaccessible"):
        backup(brain, None)

    assert list(outside.iterdir()) == []
    assert brain.status()["integrity"] == "ok"


def test_default_backup_preserves_canonical_notes_and_private_modes(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    note = brain.remember("Synthetic decision", "Use the Markdown source of truth.")
    expected = dict(brain.snapshot())

    result = backup(brain, None)

    path = Path(result["backup"])
    assert path.parent == brain.root / ".cortex/backups"
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert result["notes"] == len(expected)
    with tarfile.open(path, mode="r:gz") as archive:
        assert set(archive.getnames()) == set(expected)
        assert note["path"] in archive.getnames()
        assert all(member.isfile() and member.mode == 0o600 for member in archive.getmembers())
        assert all(not name.startswith(".cortex/") for name in archive.getnames())
        for name, data in expected.items():
            extracted = archive.extractfile(name)
            assert extracted is not None
            assert extracted.read() == data


def test_explicit_backup_output_can_be_external_but_cannot_overwrite(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    destination = tmp_path / "user-chosen-export" / "private.tar.gz"

    result = backup(brain, destination)

    assert result["backup"] == str(destination)
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    original = destination.read_bytes()
    with pytest.raises(FileExistsError):
        backup(brain, destination)
    assert destination.read_bytes() == original


def test_explicit_backup_output_does_not_follow_destination_symlink(tmp_path: Path) -> None:
    brain = Brain.initialize(tmp_path / "Brain")
    existing = tmp_path / "existing-private-data"
    existing.write_bytes(b"preserve this synthetic data")
    chosen = tmp_path / "chosen-output.tar.gz"
    chosen.symlink_to(existing)

    with pytest.raises(FileExistsError):
        backup(brain, chosen)

    assert existing.read_bytes() == b"preserve this synthetic data"
    assert chosen.is_symlink()
