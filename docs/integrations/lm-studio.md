# LM Studio

LM Studio is optional. Its official [MCP documentation](https://lmstudio.ai/docs/app/mcp) describes local and remote server support from version 0.3.17 build 10. It uses `mcp.json`; the app exposes the file through **Program → Install → Edit mcp.json**.

For the local installation path supported by Cortex:

```sh
cortex --brain "$HOME/Brain" connect lm-studio
cortex --brain "$HOME/Brain" connect lm-studio --apply
```

The first command previews a JSON entry. The second merges only `mcpServers.cortex` into `~/.lmstudio/mcp.json`, backing up the existing file. A conflicting Cortex entry is refused; unrelated servers remain. Confirm that the file opened by your LM Studio version is this file before applying. If your app uses another location, merge the preview into that actual file instead.

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

Use the absolute paths from the generated preview. Do not paste this entire object over existing configuration. Default access is read-only; `connect lm-studio --write` generates the optional mutation-enabled server arguments. Mutations create candidates and cannot perform human confirmation.

Load a model capable of tool calling, enable Cortex in LM Studio, inspect its tool list and request `brain_status` followed by a known-note search. A saved config and a loaded model do not prove a successful tool call. Tool behavior varies by model; keep retrieval bounded to fit its context window.

This setup does not install LM Studio, download a model or imply the current machine has been tested with it. The Cortex process itself makes no network calls. The privacy of any additional model/provider connection remains a client-level choice.

For an optional user-reviewed installation link, LM Studio documents its [MCP deeplink format](https://lmstudio.ai/docs/app/mcp/deeplink). Cortex does not require that path or remote hosting.
