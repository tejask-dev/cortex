"""Bounded, safe frontmatter parsing and provenance-aware note records."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

import yaml
from yaml.tokens import AliasToken, AnchorToken

from cortex.security import CortexError, check_secrets

STATUSES = {"candidate", "confirmed", "superseded", "expired"}
TYPES = {
    "note",
    "identity",
    "preference",
    "goal",
    "project",
    "person",
    "company",
    "decision",
    "idea",
    "research",
    "reference",
    "session",
    "lesson",
    "correction",
}


def now() -> str:
    return datetime.now(UTC).isoformat()


def timestamp(value: Any) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    except (TypeError, ValueError, OverflowError) as exc:
        raise CortexError("Invalid ISO 8601 timestamp.") from exc


def parse_note(path: str, raw: bytes, modified: float) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CortexError("Note is not valid UTF-8.") from exc
    check_secrets(text)
    metadata: dict[str, Any] = {}
    body = text
    if text.startswith("---\n") or text.startswith("---\r\n"):
        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) != 3 or len(parts[1]) > 32_768:
            raise CortexError("Malformed or oversized YAML frontmatter.")
        try:
            if any(isinstance(token, (AliasToken, AnchorToken)) for token in yaml.scan(parts[1])):
                raise CortexError("YAML aliases and anchors are not supported.")
            parsed = yaml.safe_load(parts[1])
        except (yaml.YAMLError, RecursionError, ValueError, TypeError, OverflowError) as exc:
            raise CortexError("Malformed YAML frontmatter.") from exc
        if parsed is not None and not isinstance(parsed, dict):
            raise CortexError("Frontmatter must be a mapping.")
        metadata = parsed or {}
        if any(not isinstance(key, str) for key in metadata):
            raise CortexError("Frontmatter keys must be strings.")
        body = parts[2].lstrip("\r\n")
    fallback = datetime.fromtimestamp(modified, UTC).isoformat()
    match = re.search(r"^#[ \t]+(.+)$", body, re.MULTILINE)
    title = metadata.get("title", match.group(1) if match else path.rsplit("/", 1)[-1][:-3])
    status = metadata.get("status", "candidate")
    kind = metadata.get("type", "note")
    confidence = metadata.get("confidence", 0.5)
    tags = metadata.get("tags", [])
    if (
        not isinstance(status, str)
        or not isinstance(kind, str)
        or status not in STATUSES
        or kind not in TYPES
    ):
        raise CortexError("Unknown memory status or type.")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise CortexError("Confidence must be between zero and one.")
    if (
        not isinstance(tags, list)
        or len(tags) > 50
        or any(not isinstance(t, str) or len(t) > 80 for t in tags)
    ):
        raise CortexError("Tags must be a bounded list of strings.")
    fields = {
        "id": metadata.get("id", "file_" + hashlib.sha256(path.encode()).hexdigest()[:24]),
        "title": title,
        "source": metadata.get("source", "filesystem"),
        "source_ref": metadata.get("source_ref", path),
        "sensitivity": metadata.get("sensitivity", "private"),
    }
    if any(not isinstance(v, str) or not v or len(v) > 1000 for v in fields.values()):
        raise CortexError("Invalid metadata string.")
    links = sorted(set(re.findall(r"\[\[([^\[\]\n]{1,500})\]\]", body)))
    links = [link.split("|", 1)[0].split("#", 1)[0].strip() for link in links]
    return {
        **fields,
        "path": path,
        "type": kind,
        "created": timestamp(metadata.get("created", fallback)),
        "updated": timestamp(metadata.get("updated", fallback)),
        "file_modified": fallback,
        "status": status,
        "confidence": float(confidence),
        "tags": tags,
        "links": sorted({link for link in links if link}),
        "content": body,
        "hash": hashlib.sha256(raw).hexdigest(),
        "trust": "untrusted_data",
        "_extra_yaml": yaml.safe_dump(
            {
                key: value
                for key, value in metadata.items()
                if key
                not in {
                    "id",
                    "title",
                    "type",
                    "created",
                    "updated",
                    "source",
                    "source_ref",
                    "confidence",
                    "sensitivity",
                    "status",
                    "tags",
                }
            },
            sort_keys=False,
            allow_unicode=True,
        ),
    }


def render_note(note: dict[str, Any]) -> bytes:
    fields = {
        k: note[k]
        for k in (
            "id",
            "title",
            "type",
            "created",
            "updated",
            "source",
            "source_ref",
            "confidence",
            "sensitivity",
            "status",
            "tags",
        )
    }
    extra = yaml.safe_load(note.get("_extra_yaml", "")) or {}
    fields = {**extra, **fields}
    result: str = (
        "---\n"
        + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + note["content"].strip()
        + "\n"
    )
    check_secrets(result)
    return result.encode("utf-8")


def public_note(
    note: dict[str, Any], *, full: bool = False, stale_days: int = 90
) -> dict[str, Any]:
    result = dict(note)
    result.pop("_extra_yaml", None)
    age = max(
        0.0, (datetime.now(UTC) - datetime.fromisoformat(note["updated"])).total_seconds() / 86400
    )
    result["age_days"] = round(age, 2)
    result["stale"] = age >= stale_days
    if not full:
        result["excerpt"] = result.pop("content")[:600]
    return result
