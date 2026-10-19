# Contributing

Cortex is a small local knowledge layer. Preserve readable Markdown, private data boundaries, inspectable retrieval and interchangeable clients. Read [the architecture](docs/architecture.md), [memory model](docs/memory-model.md) and [security design](docs/security.md) before changing behavior.

## Development

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/). From the source checkout:

```sh
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run cortex benchmark
```

Use a temporary synthetic vault for manual checks. Never point tests at your private brain or commit private notes, exports, backups, credentials, client configuration or raw chat history. Dependency installation may access package registries; the Cortex runtime should not require a network connection.

## Changes and reviews

Keep CLI and MCP behavior in the shared core. Add regression tests for the failure a change fixes, especially path handling, note metadata, stale writes, indexing consistency and MCP permissions. Show the exact commands and results you ran. Distinguish local checks from CI, configuration from live connection, and source review from runtime evidence.

For integration changes, cite current official documentation, use absolute launch paths, preserve unrelated configuration and keep trust approval under the client's control. Do not bypass sandbox, approval or hook-trust protections. Capture public demos with synthetic data only.

Explain the user-visible problem, the resulting behavior, important tradeoffs and remaining limits in a pull request. Keep dependency additions justified by measured benefit. New retrieval methods should improve a benchmark rather than only add infrastructure.

Contribute original code or identify reused material and its license. Do not copy incompatible upstream implementations into this MIT project. Document architectural influences in [prior art](docs/prior-art.md).

Report potential vulnerabilities using [SECURITY.md](SECURITY.md). Community participation follows [the code of conduct](CODE_OF_CONDUCT.md).
