# Cursor

Cursor supports local stdio MCP servers and personal configuration in `~/.cursor/mcp.json`. See its official [MCP reference](https://cursor.com/docs/mcp).

```sh
cortex --brain "$HOME/Brain" connect cursor
cortex --brain "$HOME/Brain" connect cursor --apply
```

The first command prints a preview. The second merges only the Cortex server entry, preserves unrelated configuration and creates a backup. Repeating an identical registration is harmless; a conflicting Cortex entry is refused for review.

```json
{
  "mcpServers": {
    "cortex": {
      "type": "stdio",
      "command": "/absolute/install/bin/cortex",
      "args": ["--brain", "/Users/you/Brain", "serve"]
    }
  }
}
```

Use the actual absolute paths emitted by Cortex. A global personal entry avoids committing a private vault path into project `.cursor/mcp.json`. Project settings can override personal settings, so inspect the active server if behavior differs by workspace.

Open Cursor's Customize/MCP controls, enable Cortex and inspect its available tools. Ask the agent to call `brain_status`, then search for a known note. Follow normal tool approvals; do not weaken client policy to make setup easier. A configured entry is not a verified call.

The default entry cannot mutate canonical notes through MCP. To intentionally enable candidate writes, preview `connect cursor --write`; review and apply that change. The server does not offer human confirmation. Candidate results remain unconfirmed when another agent reads them.

This guide does not assert that Cursor is installed or that this integration has run on the current machine. Cortex does not install Cursor hooks in v0.1. Requested note context may leave the Mac through Cursor's configured model provider.
