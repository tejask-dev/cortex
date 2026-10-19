"""Human-facing Cortex CLI; machine-readable output is always available with --json."""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cortex import __version__
from cortex.brain import Brain
from cortex.security import CortexError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="cortex",
        description="One brain. Every model. Local Markdown memory for humans and agents.",
    )
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument(
        "--brain",
        type=Path,
        default=Path.home() / "Brain",
        help="Private vault root (default: ~/Brain)",
    )
    root.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Initialize without overwriting existing notes")
    init.add_argument("path", type=Path, nargs="?")
    for name in ("status", "doctor", "reindex", "open", "benchmark"):
        commands.add_parser(name)
    search = commands.add_parser("search", help="Exact and full-text retrieval")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--type", action="append", dest="types")
    search.add_argument("--tag", action="append", dest="tags")
    search.add_argument("--status", choices=["candidate", "confirmed", "superseded", "expired"])
    search.add_argument("--since")
    search.add_argument("--exclude-stale", action="store_true")
    read = commands.add_parser("read")
    read.add_argument("identifier")
    context = commands.add_parser("context")
    context.add_argument("query", nargs="?", default="")
    context.add_argument("--limit", type=int, default=6)
    context.add_argument("--depth", type=int, default=1)
    context.add_argument("--max-chars", type=int, default=12000)
    remember = commands.add_parser("remember", help="Store a concise candidate memory")
    remember.add_argument("text")
    remember.add_argument("--title", default="New memory")
    remember.add_argument("--type", default="note")
    remember.add_argument("--source", default="user")
    remember.add_argument("--source-ref", default="manual-cli")
    remember.add_argument("--tag", action="append", default=[])
    remember.add_argument(
        "--confirmed",
        action="store_true",
        help="Explicit human confirmation; agents must not use this flag",
    )
    for name in ("recent", "activity"):
        command = commands.add_parser(name)
        command.add_argument("--limit", type=int, default=10)
    log = commands.add_parser(
        "log", help="Record an explicit provider-neutral candidate activity summary"
    )
    log.add_argument("summary")
    log.add_argument("--agent", required=True)
    log.add_argument("--project", required=True)
    log.add_argument("--task", required=True)
    update = commands.add_parser("update")
    update.add_argument("identifier")
    update.add_argument("--hash", required=True, dest="expected_hash")
    update.add_argument("--content")
    update.add_argument("--status", choices=["candidate", "confirmed", "superseded", "expired"])
    update.add_argument(
        "--confirm",
        action="store_true",
        help="Explicit human confirmation, never inferred by a model",
    )
    link = commands.add_parser("link")
    link.add_argument("identifier")
    link.add_argument("target")
    link.add_argument("--hash", required=True, dest="expected_hash")
    forget = commands.add_parser("forget", help="Expire reversibly; never deletes Markdown")
    forget.add_argument("identifier")
    forget.add_argument("--hash", required=True, dest="expected_hash")
    serve = commands.add_parser("serve", help="Run the local stdio MCP server")
    serve.add_argument(
        "--write",
        action="store_true",
        help="Enable explicit candidate writes and reversible updates",
    )
    connect = commands.add_parser(
        "connect", help="Preview or apply a client registration, preserving existing config"
    )
    connect.add_argument("client", choices=["codex", "claude", "cursor", "lm-studio"])
    connect.add_argument("--apply", action="store_true")
    connect.add_argument("--write", action="store_true")
    hooks = commands.add_parser(
        "hooks", help="Preview or install lifecycle hooks; trust review is separate"
    )
    hooks.add_argument("--install", action="store_true")
    hook = commands.add_parser("hook", help=argparse.SUPPRESS)
    hook.add_argument("client", choices=["codex"])
    backup = commands.add_parser(
        "backup", help="Private Markdown backup (contains vault data; do not publish)"
    )
    backup.add_argument("--output", type=Path)
    graph = commands.add_parser(
        "graph", help="Export a local graph snapshot (contains vault titles)"
    )
    graph.add_argument("--output", type=Path)
    demo = commands.add_parser("demo", help="Create synthetic example data in a NEW separate vault")
    demo.add_argument("path", type=Path)
    return root


def diagnostics(brain: Brain) -> dict[str, Any]:
    from cortex.integrations import client_path

    state = brain.status()
    clients = {}
    for client in ["codex", "claude", "cursor", "lm-studio"]:
        path = client_path(client)
        try:
            if not path.exists():
                clients[client] = "not configured"
                continue
            document = (
                tomllib.loads(path.read_text())
                if client == "codex"
                else json.loads(path.read_text())
            )
            config = document.get("mcp_servers" if client == "codex" else "mcpServers", {}).get(
                "cortex"
            )
            if not config:
                clients[client] = "not configured"
                continue
            args = config.get("args", [])
            expected = ["--brain", str(brain.root), "serve"]
            executable = Path(config.get("command", ""))
            valid = (
                args[:3] == expected
                and executable.is_file()
                and os.access(executable, os.X_OK)
                and config.get("enabled", True)
            )
            clients[client] = (
                "registered; live connection unverified"
                if valid
                else "registration mismatch or unavailable executable"
            )
        except (OSError, ValueError, TypeError, AttributeError):
            clients[client] = "configuration unreadable"
    obsidian = (
        Path("/Applications/Obsidian.app").exists()
        or Path.home().joinpath("Applications/Obsidian.app").exists()
    )
    return {
        **state,
        "version": __version__,
        "clients": clients,
        "obsidian": "installed" if obsidian else "not installed",
        "lm_studio_app": "installed"
        if Path("/Applications/LM Studio.app").exists()
        else "not installed (optional)",
        "open_webui": "not configured (HTTP bridge required)",
        "hooks": "file present; trust/activation unverified"
        if Path.home().joinpath(".codex/hooks.json").exists()
        else "not configured",
        "privacy": "vault-only file access; no runtime network or telemetry; connected clients control model data use",
        "health": "healthy"
        if state["fts"] and state["integrity"] == "ok" and not state["errors"]
        else "needs attention",
    }


def backup(brain: Brain, output: Path | None) -> dict[str, Any]:
    notes = brain.snapshot()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = (
        (output or brain.root / ".cortex/backups" / f"brain-{stamp}-{uuid.uuid4().hex[:6]}.tar.gz")
        .expanduser()
        .absolute()
    )
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for path, data in notes:
            item = tarfile.TarInfo(path)
            item.size = len(data)
            item.mode = 0o600
            archive.addfile(item, io.BytesIO(data))
    return {
        "backup": str(destination),
        "notes": len(notes),
        "contents": "private canonical Markdown only; index is rebuilt on restore",
    }


def dispatch(args: argparse.Namespace) -> Any:
    from cortex import integrations

    if args.command == "hook":
        try:
            raw = sys.stdin.read(65537)
            event = json.loads(raw) if len(raw) <= 65536 else {}
            result = integrations.hook_response(
                event if isinstance(event, dict) else {}, args.brain
            )
        except (ValueError, OSError):
            result = {}
        print(json.dumps(result))
        return None
    if args.command == "benchmark":
        from cortex.demo import benchmark

        return benchmark()
    if args.command == "demo":
        from cortex.demo import create_demo

        return create_demo(args.path).status()
    if args.command == "init":
        return Brain.initialize(args.path or args.brain).status()
    brain = Brain(args.brain)
    if args.command == "serve":
        from cortex.mcp_server import create_server

        create_server(brain, writable=args.write).run(transport="stdio")
        return None
    if args.command == "connect":
        return integrations.connect(args.client, brain.root, apply=args.apply, writable=args.write)
    if args.command == "hooks":
        return integrations.install_hooks(brain.root, install=args.install)
    if args.command == "doctor":
        return diagnostics(brain)
    if args.command == "status":
        return brain.status()
    if args.command == "reindex":
        return brain.reindex()
    if args.command == "search":
        return brain.search(
            args.query,
            limit=args.limit,
            types=args.types,
            tags=args.tags,
            status=args.status,
            since=args.since,
            include_stale=not args.exclude_stale,
        )
    if args.command == "read":
        return brain.read(args.identifier)
    if args.command == "context":
        return brain.context(
            args.query, limit=args.limit, depth=args.depth, max_chars=args.max_chars
        )
    if args.command == "remember":
        return brain.remember(
            args.title,
            args.text,
            kind=args.type,
            source=args.source,
            source_ref=args.source_ref,
            tags=args.tag,
            confirmed=args.confirmed,
        )
    if args.command == "log":
        return brain.remember(
            args.task,
            f"Agent: {args.agent}\nProject: {args.project}\nTask: {args.task}\n\n{args.summary}",
            kind="session",
            source=args.agent,
            source_ref=f"{args.project}/{args.task}",
        )
    if args.command in {"recent", "activity"}:
        return brain.recent(args.limit, activity=args.command == "activity")
    if args.command == "update":
        return brain.update(
            args.identifier,
            expected_hash=args.expected_hash,
            content=args.content,
            status=args.status,
            human_confirm=args.confirm,
        )
    if args.command == "link":
        return brain.link(args.identifier, args.target, expected_hash=args.expected_hash)
    if args.command == "forget":
        return brain.forget(args.identifier, expected_hash=args.expected_hash)
    if args.command == "backup":
        return backup(brain, args.output)
    if args.command == "graph":
        from cortex.visualization import graph_html

        html = graph_html(brain.graph())
        if args.output:
            destination = args.output.expanduser().absolute()
            with destination.open("x", encoding="utf-8") as stream:
                stream.write(html)
            os.chmod(destination, 0o600)
        else:
            destination = brain.root / ".cortex/graph.html"
            brain.boundary.write(".cortex/graph.html", html.encode(), internal=True, replace=True)
        return {
            "graph": str(destination),
            "privacy": "contains vault titles; do not publish real private graph exports",
        }
    if args.command == "open":
        opener = shutil.which("open" if sys.platform == "darwin" else "xdg-open")
        if not opener:
            raise CortexError("No desktop opener found. Open the vault folder in a text editor.")
        if sys.platform == "darwin" and Path("/Applications/Obsidian.app").exists():
            target = "obsidian://open?path=" + quote(str(brain.root), safe="")
        else:
            target = str(brain.root)
        subprocess.run([opener, target], check=True)
        return {"opened": str(brain.root), "status": "open request sent; verify in the app"}
    raise CortexError("Unknown command.")


def display(result: Any, args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console = Console(highlight=False, markup=False)
    if args.command == "doctor":
        table = Table(show_header=False, box=None, padding=(0, 2))
        for key, value in [
            ("Brain", result["brain"]),
            ("Markdown memories", result["notes"]),
            ("Graph edges", result["edges"]),
            ("FTS index", "healthy" if result["fts"] else "mismatch"),
            ("SQLite integrity", result["integrity"]),
            ("Skipped notes", len(result["errors"])),
            ("Semantic retrieval", result["semantic"]),
            ("Obsidian", result["obsidian"]),
            ("LM Studio", result["lm_studio_app"]),
            *result["clients"].items(),
            ("Hooks", result["hooks"]),
        ]:
            table.add_row(str(key), str(value))
        console.print(
            Panel(
                table,
                title="CORTEX // SYSTEM DIAGNOSTIC",
                subtitle=result["health"].upper(),
                border_style="green" if result["health"] == "healthy" else "yellow",
            )
        )
    elif isinstance(result, list):
        if not result:
            console.print("No matching memories.")
        for note in result:
            console.print(
                Panel(
                    f"{note.get('excerpt', '')}\n\nSource: {note['path']}\n{note['status']} · {note['source']} · updated {note['updated'][:10]}"
                    + (" · STALE" if note["stale"] else ""),
                    title=Text(note["title"]),
                )
            )
    else:
        console.print_json(json.dumps(result, ensure_ascii=False))


def main() -> None:
    args = parser().parse_args()
    try:
        result = dispatch(args)
        if result is not None:
            display(result, args)
        if isinstance(result, dict) and (
            result.get("health") == "needs attention"
            or (args.command == "reindex" and result.get("errors"))
        ):
            raise SystemExit(1)
    except (CortexError, OSError, ValueError, subprocess.SubprocessError) as exc:
        message = (
            str(exc)
            if isinstance(exc, CortexError)
            else f"{type(exc).__name__}: operation failed; inspect the target path/configuration."
        )
        if args.json:
            print(json.dumps({"error": message}))
        else:
            Console(stderr=True).print("Cortex: " + message, markup=False)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
