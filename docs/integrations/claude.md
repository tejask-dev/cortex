# Claude

## Claude Desktop

`connect claude` targets **Claude Desktop**, not Claude Code:

```sh
cortex --brain "$HOME/Brain" connect claude
cortex --brain "$HOME/Brain" connect claude --apply
```

Preview first. Applying merges `mcpServers.cortex` into `~/Library/Application Support/Claude/claude_desktop_config.json`, preserving unrelated entries and creating a backup. A conflicting Cortex entry requires review instead of replacement.

The official [local MCP tutorial](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers) documents this configuration location and the Desktop **Settings → Developer → Edit Config** entry point. A Cortex configuration has this shape:

```json
{
  "mcpServers": {
    "cortex": {
      "command": "/absolute/install/bin/cortex",
      "args": ["--brain", "/Users/you/Brain", "serve"]
    }
  }
}
```

Use generated absolute paths. Quit and reopen Claude Desktop, inspect the Cortex tools, then ask for `brain_status` and a known-note search. Follow the app's approval prompts. Configuration does not prove connection or successful retrieval.

Read-only access is the default. `connect claude --write` previews an entry with candidate-write tools enabled; applying a changed entry still requires resolving a conflict deliberately. Human confirmation remains outside MCP. The vault is local, but content returned to Claude may be processed by its cloud provider.

## Claude Code

For Claude Code, use its own supported CLI, substituting the verified absolute Cortex executable:

```sh
claude mcp add --transport stdio --scope user cortex -- \
  /absolute/install/bin/cortex --brain /Users/you/Brain serve
claude mcp get cortex
```

The `--` separates Claude options from Cortex arguments. User scope makes this a personal registration; do not commit a private brain path into a shared project configuration. Inspect `/mcp` inside Claude Code and perform a read/search before calling it verified. This separate route is documented in [Claude Code's official MCP reference](https://code.claude.com/docs/en/mcp).

Cortex does not install Claude hooks in v0.1. Clients can share explicitly saved candidate memories through the same Markdown vault without sharing raw conversation histories.
