# Memory model

A memory is a UTF-8 Markdown file with optional YAML frontmatter. Cortex-written notes include explicit identity, attribution, dates and status. Plain Markdown remains readable and searchable, but receives conservative fallback metadata.

```yaml
---
id: mem_0123456789abcdef0123456789abcdef
title: Atlas storage decision
type: decision
created: '2026-10-19T14:30:00+00:00'
updated: '2026-10-19T14:30:00+00:00'
source: user
source_ref: manual-example
confidence: 1.0
sensitivity: private
status: confirmed
tags:
  - atlas
  - storage
---
```

```markdown
# Atlas storage decision

Use Markdown for durable project knowledge.

## Relations
- related-to [[Atlas]]
- supersedes [[Old storage proposal]]
```

This is synthetic example content, not a statement about the owner's projects.

## Fields

| Field | Meaning |
| --- | --- |
| `id` | Stable identity for Cortex-created memories. Files without an ID receive a path-derived ID, so renaming such a file changes that fallback identity. |
| `title`, `type`, `tags` | Display name and retrieval filters. |
| `created`, `updated` | ISO 8601 timestamps normalized to UTC. Missing dates fall back to filesystem modification time. |
| `source`, `source_ref` | Who or what supplied the claim and a concise reference that allows its origin to be checked. These are attribution, not proof by themselves. |
| `confidence` | A value from 0 to 1. It records confidence, not a calibrated probability or independent fact check. |
| `sensitivity` | Descriptive metadata. It does not encrypt the note or by itself establish an access-control policy. |
| `status` | Candidate, confirmed, superseded or expired. |

Retrieval adds the relative path, file hash, filesystem modification timestamp, links, age, stale flag and an untrusted-data label. A normal search returns a bounded excerpt; `read` returns full validated content.

Supported types are `note`, `identity`, `preference`, `goal`, `project`, `person`, `company`, `decision`, `idea`, `research`, `reference`, `session`, `lesson` and `correction`. Unknown types/statuses and invalid metadata are reported during indexing. Cortex mutations update the documented fields and retain unknown frontmatter values. YAML formatting and key order can be normalized.

## Lifecycle

| Status | Interpretation and default retrieval |
| --- | --- |
| `candidate` | Unconfirmed information, including agent-generated summaries. Included, with status visible. |
| `confirmed` | Explicitly accepted through the human workflow. Included, but still subject to provenance and staleness. |
| `superseded` | Replaced by later knowledge. Excluded by default; request this status to inspect it. |
| `expired` | Retained for history but no longer current. Excluded by default; `forget` sets this status. |

`remember` defaults to a candidate with confidence 0.5. Human CLI `remember --confirmed` records explicit confirmation with confidence 1.0. Updating content without human confirmation demotes it to candidate and caps confidence at 0.5. Promotion requires the explicit confirmation path; MCP tools do not expose human confirmation.

There is no automatic promotion based on repeated model statements. Manual edits remain possible because Markdown is canonical; a manually entered `confirmed` value is not evidence that Cortex independently verified the claim.

## Example workflow

Global options precede the subcommand:

```sh
cortex --brain "$HOME/Brain" remember "Use Markdown for Atlas knowledge" \
  --title "Atlas storage decision" --type decision \
  --source user --source-ref manual-example --tag atlas
cortex --brain "$HOME/Brain" search "Atlas" --status candidate
cortex --brain "$HOME/Brain" --json read MEMORY_ID
cortex --brain "$HOME/Brain" update MEMORY_ID --hash HASH_FROM_READ \
  --status confirmed --confirm
```

Replace the example text with deliberately chosen information. `MEMORY_ID` and `HASH_FROM_READ` are placeholders returned by the preceding commands. A stale hash requires a new read and review; do not automatically retry a conflicting write.

Identical captures with the same title, content, provenance, type, status and tags are deduplicated. A missing final newline is normalized; indentation and trailing spaces remain significant Markdown content. This is exact deduplication, not semantic merging. Contradictory notes remain separate evidence until someone resolves them. To retire an old decision, link the replacement first, then use the returned hash to set the old note's status to superseded. Adding a link changes content and returns the note to candidate status, so the order matters.

## Relations, age and activity

Wiki links support titles and relative note paths; aliases and heading suffixes are stripped for note-level graph resolution. Ambiguous targets remain unresolved. The graph is explicit linkage, not an LLM-inferred ontology. Cortex does not claim complete Obsidian Markdown semantics.

A note becomes stale at 90 days after its `updated` timestamp. Staleness is a review signal, not a declaration that a statement is false. `--exclude-stale` filters these records. External editors should maintain `updated` when changing dated knowledge; filesystem modification is returned separately.

`activity` reads session memories. `log` writes a concise candidate session summary with agent, project and task attribution. Record work actually performed, useful results and follow-up context. Avoid raw conversation transcripts, credentials, entire logs and empty session-close events. Each client shares these ordinary files.
