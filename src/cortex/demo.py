"""Synthetic, isolated demonstration and retrieval benchmark. Never populates the private vault."""

from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from cortex.brain import Brain
from cortex.notes import render_note
from cortex.security import CortexError

SAMPLES = [
    (
        "Project Atlas",
        "project",
        "A fictional field-notes app. [[Mira Chen]] leads the project. [[Authentication decision]] and [[Offline storage]] define the design. [[Autumn launch]] is the next milestone.",
    ),
    (
        "Project Solstice",
        "project",
        "A fictional observatory dashboard. [[Jon Bell]] owns [[Sensor pipeline]]. [[Data retention]] applies to all observations.",
    ),
    (
        "Mira Chen",
        "person",
        "Fictional product lead for [[Project Atlas]]. Works with [[Jon Bell]] on [[Field research]].",
    ),
    (
        "Jon Bell",
        "person",
        "Fictional engineer on [[Project Solstice]]. Also reviews [[Offline storage]].",
    ),
    (
        "Authentication decision",
        "decision",
        "Use passkeys plus OAuth fallback for [[Project Atlas]]. Supersedes [[Legacy password decision]].",
    ),
    (
        "Offline storage",
        "decision",
        "Use SQLite and local Markdown for [[Project Atlas]]. See [[Sync experiment]].",
    ),
    (
        "Data retention",
        "decision",
        "Keep synthetic sensor observations for 30 days in [[Project Solstice]].",
    ),
    (
        "Autumn launch",
        "goal",
        "Ship a fictional private beta of [[Project Atlas]] after [[Field research]].",
    ),
    (
        "Field research",
        "research",
        "Interview fictional testers about disconnected work. [[Mira Chen]] owns this study.",
    ),
    (
        "Sync experiment",
        "research",
        "Test deterministic conflict handling for [[Offline storage]].",
    ),
    (
        "Sensor pipeline",
        "reference",
        "Ingest fictional weather readings for [[Project Solstice]]. Follow [[Data retention]].",
    ),
    (
        "Codex implementation log",
        "session",
        "Agent: codex\nProject: Atlas\nTask: synthetic fixture\nOutcome: implemented a sample authentication flow.\nDecision: [[Authentication decision]]\nLesson: preserve provenance.",
    ),
    (
        "Claude review log",
        "session",
        "Agent: claude\nProject: Atlas\nTask: synthetic review\nOutcome: reviewed sample [[Offline storage]] constraints.\nOpen question: [[Sync experiment]].",
    ),
    (
        "Legacy password decision",
        "decision",
        "Old password-only login for [[Project Atlas]]. Superseded by [[Authentication decision]].",
    ),
    (
        "Archived cache research",
        "research",
        "The old cache vendor has not been evaluated recently. [[Project Solstice]].",
    ),
]


def create_demo(path: Path) -> Brain:
    if path.expanduser().exists():
        raise CortexError("Demo requires a new directory; it will never modify an existing vault.")
    brain = Brain.initialize(path)
    for title, kind, content in SAMPLES:
        note = brain.remember(
            title,
            content,
            kind=kind,
            source="synthetic-demo",
            source_ref="cortex:demo",
            tags=["synthetic"],
            confirmed=True,
        )
        if title == "Legacy password decision":
            brain.update(note["id"], expected_hash=note["hash"], status="superseded")
        if title == "Archived cache research":
            note["updated"] = "2020-01-01T00:00:00+00:00"
            brain.boundary.write(note["path"], render_note(note), replace=True)
    brain.reindex()
    return brain


def benchmark() -> dict[str, Any]:
    with TemporaryDirectory(prefix="cortex-benchmark-") as temporary:
        brain = create_demo(Path(temporary) / "synthetic")
        started = time.perf_counter()
        checks = []

        def record(name: str, success: bool) -> None:
            checks.append({"case": name, "passed": success})

        result = brain.search("Authentication decision", limit=1)
        record(
            "exact title at rank 1",
            bool(result) and result[0]["title"] == "Authentication decision",
        )
        result = brain.search("passkeys", limit=3)
        record("keyword retrieval", any(n["title"] == "Authentication decision" for n in result))
        result = brain.search("passkeys", limit=1)
        record(
            "source provenance",
            bool(result) and result[0]["source"] == "synthetic-demo" and bool(result[0]["path"]),
        )
        context_result = brain.context("Project Atlas", limit=1, depth=1)
        record(
            "graph relationship traversal",
            any(n["title"] == "Mira Chen" for n in context_result["memories"]),
        )
        record(
            "old conflicting decision excluded",
            all(n["title"] != "Legacy password decision" for n in brain.search("password")),
        )
        record(
            "stale knowledge filtered",
            all(
                n["title"] != "Archived cache research"
                for n in brain.search("Archived cache research", include_stale=False)
            ),
        )
        record("recent activity", len(brain.recent(activity=True)) == 2)
        result = brain.search("sign in without a memorized credential", limit=3)
        record(
            "semantic paraphrase (no embeddings)",
            any(n["title"] == "Authentication decision" for n in result),
        )
        return {
            "dataset": "15 synthetic linked notes plus 6 starter notes",
            "checks": checks,
            "passed": sum(c["passed"] for c in checks),
            "total": len(checks),
            "query_ms": round((time.perf_counter() - started) * 1000, 2),
            "limitations": "Small deterministic smoke benchmark, not a general retrieval evaluation. Semantic paraphrase is expected to miss; embeddings are not implemented.",
        }
