# Cortex 0.1 build plan

1. Audit the Mac and research current SDK/client capabilities and prior art.
2. Implement a vault-only storage boundary, safe YAML metadata, atomic writes and a process lock.
3. Build a disposable SQLite FTS and wikilink index; retrieval includes source, status, confidence and staleness.
4. Expose the eleven requested tools via the official MCP SDK over stdio. Writes are opt-in; model-created memories remain candidates.
5. Build the CLI, truthful diagnostics, private backup, and a lightweight graph export.
6. Test boundaries, concurrent access, reindex recovery, retrieval, real MCP client calls and synthetic benchmarks.
7. Install locally, initialize the private vault, back up configs, register Codex and prepare reviewed lifecycle hooks. Install Obsidian through Homebrew's official cask. Document optional clients.
8. Complete independent Claude review, clean-install checks and release checks before public source publication. Verify GitHub CI separately from local tests.

The source root is `~/Developer/cortex` because the existing workspace and teamwork service use that root. `~/Code` does not exist. The private vault is `~/Brain`. Never publish local audit/config backups or vault content.

Python 3.11+ with the official MCP SDK, PyYAML, Rich and standard-library SQLite avoids a separate Node runtime or database service. Semantic retrieval remains deferred until benchmark evidence supports it. Docker is not required.
