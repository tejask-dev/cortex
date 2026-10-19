# Codex

Cortex uses a local stdio MCP server. Codex configuration is separate from hook trust and from whether an already-open chat has loaded that configuration. The official [MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) documents local servers and the `/mcp` interface.

## Register the server

```sh
cortex --brain "$HOME/Brain" connect codex
cortex --brain "$HOME/Brain" connect codex --apply
```

The first command previews the entry; the second applies it to `~/.codex/config.toml` with a backup. Existing unrelated settings are retained. An exact existing Cortex entry is left alone; a conflicting entry must be reviewed instead of silently replaced.

A read-only entry has this shape; use the absolute executable emitted by your installation:

```toml
[mcp_servers.cortex]
command = "/absolute/install/bin/cortex"
args = ["--brain", "/Users/you/Brain", "serve"]
```

For an alternative manual route, the official Codex CLI accepts:

```sh
codex mcp add cortex -- /absolute/install/bin/cortex --brain /Users/you/Brain serve
```

Choose one registration route. Retain the client's normal approvals and sandbox configuration. To intentionally enable candidate-memory writes, include `--write` in the Cortex connection command before applying its entry. If a read-only entry already exists, review the proposed difference and make that narrow change manually; a conflict is not permission to overwrite it.

Start a fresh Codex session, inspect `/mcp`, and ask it to call `brain_status`, then search for a note you deliberately created. Report the actual tool result before calling the connection verified. A successful standalone protocol test proves the server, not this client session.

## Lifecycle hooks

```sh
cortex --brain "$HOME/Brain" hooks
cortex --brain "$HOME/Brain" hooks --install
```

Preview first. Installation adds Cortex's hook definitions and concise durable-memory guidance while preserving unrelated configuration. New or changed hook definitions need review in a Codex CLI session through **`/hooks`**. Until the user trusts them and observes execution, describe them as configured and awaiting trust. Never set trust hashes directly or use a trust bypass. See the official [hook configuration and trust model](https://learn.chatgpt.com/docs/hooks).

| Event | Cortex behavior |
| --- | --- |
| `SessionStart` | Return bounded context and retrieval guidance. |
| `UserPromptSubmit` | Return a brief memory-workflow reminder without persisting the prompt. |
| `PreCompact`, `Stop`, `SessionEnd` | Safe no-ops in v0.1. They do not extract facts from a transcript. |

Useful memories are captured during authorized work by explicit `brain_remember` calls or the CLI `log` command, which write candidate Markdown immediately. There is no background summarizer or pending-summary queue. A session ending is not evidence that useful work happened, so Cortex does not invent an activity entry for it.

The initial hook design was checked against [Codex 0.160.1's generated schemas](https://github.com/openai/codex/tree/rust-v0.160.1/codex-rs/hooks/schema/generated). Recheck official schemas when upgrading client compatibility. SessionEnd has a short advisory lifecycle; it cannot guarantee a final model-generated summary.

## Privacy and recovery

Hook handlers must not read `transcript_path`, persist prompt text or capture raw assistant responses. Retrieved notes remain untrusted evidence, including confirmed notes. Candidate status must not disappear when context is summarized.

To undo installation, remove only Cortex's MCP entry and hook handlers, and remove the marked Cortex guidance if no longer wanted. The installer reports backup locations; inspect a backup before restoring it, since replacing the whole file could discard later unrelated changes. Removing configuration does not delete the private vault.
