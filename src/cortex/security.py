"""Vault-scoped, descriptor-relative filesystem operations (macOS/Linux)."""

from __future__ import annotations

import os
import re
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

MAX_NOTE_BYTES = 1_048_576


class CortexError(ValueError):
    """An actionable, safe-to-display Cortex error."""


def check_secrets(text: str) -> None:
    """Reject obvious credentials; this is a heuristic, not a secret detector guarantee."""
    if len(text) > MAX_NOTE_BYTES or len(text.encode("utf-8")) > MAX_NOTE_BYTES:
        raise CortexError("Note exceeds the 1 MiB limit.")
    patterns = (
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----",
        r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
        r"\b(?:ghp|gho|ghs|ghu|ghr|github_pat)_[A-Za-z0-9_]{20,}\b",
        r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b",
        r"(?im)^[ \t]*(?:api[_-]?key|secret[_-]?key|password|access[_-]?token)[ \t]*[:=][ \t]*\S{8,}",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise CortexError(
            "Possible credential detected; remove it before storing or reading this note."
        )


class Boundary:
    """Reject hidden paths, traversal, symlinks, hardlinks and non-Markdown note access."""

    def __init__(self, root: Path) -> None:
        expanded = root.expanduser().absolute()
        if expanded.is_symlink():
            raise CortexError("Vault root must not be a symlink.")
        self.root = expanded.resolve()
        home = Path.home().resolve()
        if home.is_relative_to(self.root) or any(p.startswith(".") for p in self.root.parts):
            raise CortexError(
                "Use a dedicated, non-hidden vault directory, not a home/system root."
            )
        if not self.root.is_dir():
            raise CortexError("Vault not initialized. Run cortex init PATH first.")

    @staticmethod
    def parts(path: str, *, internal: bool = False) -> tuple[str, ...]:
        if not path or "\\" in path or any(ord(c) < 32 for c in path):
            raise CortexError("Invalid vault path.")
        parts = PurePosixPath(path).parts
        if (
            "/".join(parts) != path
            or path.startswith("/")
            or ".." in parts
            or any(p.startswith(".") for p in parts if not (internal and p == ".cortex"))
            or any(p.casefold() in {"node_modules", "credentials", "secrets"} for p in parts)
        ):
            raise CortexError("Path is outside the permitted vault namespace.")
        if not internal and (not path.endswith(".md") or len(path) > 512):
            raise CortexError("Only relative Markdown paths are accepted.")
        return parts

    @contextmanager
    def parent(
        self, path: str, *, create: bool = False, internal: bool = False
    ) -> Iterator[tuple[int, str]]:
        parts = self.parts(path, internal=internal)
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                new_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = new_fd
            yield fd, parts[-1]
        except OSError as exc:
            raise CortexError("Unsafe or inaccessible vault path.") from exc
        finally:
            os.close(fd)

    def read(self, path: str, *, internal: bool = False) -> bytes:
        with self.parent(path, internal=internal) as (parent, name):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise CortexError("Only regular, non-linked files are permitted.")
                with os.fdopen(fd, "rb", closefd=False) as stream:
                    data = stream.read(MAX_NOTE_BYTES + 1)
                    if len(data) > MAX_NOTE_BYTES:
                        raise CortexError("Note exceeds the 1 MiB limit.")
                    return data
            finally:
                os.close(fd)

    def write(
        self, path: str, data: bytes, *, replace: bool = False, internal: bool = False
    ) -> None:
        if len(data) > MAX_NOTE_BYTES:
            raise CortexError("Note exceeds the 1 MiB limit.")
        with self.parent(path, create=True, internal=internal) as (parent, name):
            try:
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                current = None
            if current is not None and (
                not stat.S_ISREG(current.st_mode) or current.st_nlink != 1 or not replace
            ):
                raise CortexError("Destination exists or is unsafe; refusing to overwrite.")
            temporary = f".cortex-tmp-{uuid.uuid4().hex}"
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                if replace:
                    os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
                else:
                    # link is an atomic create-if-absent; the temporary name is removed immediately.
                    os.link(
                        temporary, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False
                    )
                    os.unlink(temporary, dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass

    def note_paths(self) -> list[str]:
        paths: list[str] = []
        for directory, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(
                d for d in dirs if not d.startswith(".") and not (Path(directory) / d).is_symlink()
            )
            for name in sorted(files):
                if name.endswith(".md") and not name.startswith("."):
                    path = (Path(directory) / name).relative_to(self.root).as_posix()
                    try:
                        self.parts(path)
                    except CortexError:
                        continue
                    paths.append(path)
        return sorted(paths)
