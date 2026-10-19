# Roadmap

Version 0.1 prioritizes a local Markdown vault, transparent SQLite retrieval, explicit links, provenance, candidate memory and a small stdio MCP interface. Its package version is not proof that a release has been published or that every client has passed a live integration check.

## Next: v0.2 candidates

| Work | Evidence required before adoption |
| --- | --- |
| Better incremental indexing | Large synthetic vault benchmarks, crash recovery, duplicate-ID handling and concurrent-reader/writer tests. |
| Optional local embeddings | A meaningful improvement on held-out paraphrase questions, with measured latency, disk use and model-download size. Retain full-text-only operation. |
| Better Markdown fidelity | Parser fixtures covering code fences, escaped aliases, headings, duplicate titles and custom-frontmatter preservation. |
| Memory review interface | Human review of candidates, competing decisions and stale notes without silent confirmation or loss of provenance. |
| Attachment ingestion | Explicit opt-in formats, file limits, source/page citations and no background crawl outside the vault. |
| Backup and restore improvements | Manifest, integrity checks, attachment/history options and restoration into a fresh directory. |
| Broader client verification | Repeatable setup and actual read/write tests for specific versions of Codex, Claude, Cursor and LM Studio. |
| Optional Open WebUI path | A reviewed transport/proxy design with loopback binding, authentication and end-to-end checks. |

## Deliberately deferred

No paid cloud requirement, automatic subscription, unattended whole-Mac ingestion, raw chat harvesting, inferred truth promotion, remote multi-user server or mandatory graph/vector database is planned for the baseline. Obsidian remains the primary optional UI; a visualization must never become the storage layer.

Track proposals with reproducible examples and clear failure cases. An impressive graph screenshot or a configured MCP entry is not a substitute for retrieval quality, safety tests or a verified client call.
