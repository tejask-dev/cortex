# Open WebUI

Open WebUI is optional and is not installed by Cortex. The v0.1 Cortex server is stdio-only, so there is no direct native Open WebUI connection to configure.

The official [Open WebUI MCP guide](https://docs.openwebui.com/features/extensibility/mcp/) documents native support from v0.6.31 for **Streamable HTTP only**. Administrators configure that transport under **Settings → Admin → Integrations → External Tool Servers**. A local `command`/`args` entry cannot be used there as a stdio launcher.

Two future options are a reviewed HTTP transport for Cortex or the first-party [`mcpo` proxy](https://github.com/open-webui/mcpo). The latter starts a stdio MCP command and exposes its tools through **OpenAPI**. Its output must be registered as an OpenAPI connection, not as native MCP. Do not paste an `mcpServers` JSON object into an OpenAPI URL field.

The upstream proxy accepts a command of this form:

```text
mcpo --port PORT --api-key KEY -- /absolute/install/bin/cortex --brain /absolute/Brain serve
```

This is a shape reference, not a command to run unchanged. No proxy dependency is installed or launched by the default Cortex setup. Before adopting it, verify the actual version's loopback binding, authentication, process lifecycle, schema and a read-only tool request. Keep the Cortex child read-only until deliberate write access is needed.

When Open WebUI runs in Docker, its `localhost` names the container. Official documentation describes `host.docker.internal` for host services, which requires an explicit network design. Do not silently widen a private service's bind address just to make a container reach it.

Treat this integration as **documented, not configured or verified**, unless a separate end-to-end test establishes otherwise. Docker, a proxy, model downloads and any cloud provider account are outside the v0.1 local-brain requirements.
