# Third-party notices

Cortex's implementation is original and licensed under MIT. No implementation files from the prior-art repositories are vendored.

Direct runtime dependencies are installed separately by the package manager and retain their own copyright and license files:

| Dependency | License | Source |
|---|---|---|
| MCP Python SDK (`mcp`, including `mcp-types`) | MIT | https://github.com/modelcontextprotocol/python-sdk |
| PyYAML | MIT | https://github.com/yaml/pyyaml |
| Rich | MIT | https://github.com/Textualize/rich |
| Python standard library | PSF license and included notices | https://docs.python.org/3/license.html |
| SQLite | Public domain | https://www.sqlite.org/copyright.html |

The locked dependency graph is in `uv.lock`. Python package distributions include their upstream license files; retain those when redistributing a bundled environment. Cortex's MIT license does not replace any dependency license.

Obsidian is an optional separately installed proprietary application. Cortex does not redistribute it. Referenced AGPL projects are prior art only, not code dependencies. See [prior art](docs/prior-art.md) for project-specific licenses and architectural influence.
