# Security and privacy

Cortex's supported trust boundary is one local user, a dedicated private vault and explicitly configured clients. It is designed to reject unsafe paths and constrain tool writes. It is not an operating-system sandbox, a multi-user service or protection against a malicious process already running as the same user.

## What stays local

The Cortex runtime does not call cloud APIs, download models or send telemetry. Canonical notes, the SQLite index and local history remain on disk. Installing packages can use the network. A connected AI client receives requested context and may send it to its own cloud model provider. Using a local MCP server does not make a cloud client offline.

Vault contents are plaintext. Cortex does not implement encryption at rest. Use the Mac's existing account, filesystem and backup protections according to your needs. Keep the vault, exports and backups outside the public source repository.

## Filesystem restrictions

Note APIs accept vault-relative `.md` paths or known memory IDs. They reject absolute paths, traversal, control characters, hidden namespaces, and reserved credential/dependency directories. The vault must be a dedicated non-hidden directory, not the home directory or an ancestor of it. Commands require the `.cortex/config.json` marker created by an explicit `cortex init PATH`; merely pointing a client at an ordinary directory does not adopt or index it.

Descriptor-relative access and no-follow flags reject symlinks, hardlinks and non-regular note files. Notes are limited to 1 MiB; frontmatter is limited to 32 KiB. The YAML parser uses safe loading and rejects anchors and aliases. Invalid files are excluded with diagnostic paths and safe error messages, not echoed contents.

Cortex creates new vault directories with restrictive permissions and new files with owner-only access. Existing directories or files may retain their existing permissions; no blanket claim is made that every pre-existing file is private. SQLite is local derived state; path checks do not defend against every race a malicious same-user process could create. Atomic creation requires a filesystem that supports hardlinks, such as APFS or common Linux filesystems; exFAT and some network volumes are unsupported.

## Writes and confirmation

MCP is read-only unless launched with `serve --write`. Read-only here means no canonical note mutations through MCP; derived indexes may be created or refreshed while serving reads. Client approval settings are additional controls, not substitutes for the server's write mode.

Agent writes create candidate memories. Human-facing CLI commands can explicitly confirm a new memory or promote an existing one. This distinction is an application workflow, not an identity or authorization service: another process with shell access as the user can invoke that CLI or edit Markdown directly.

Updates require the hash returned by a previous read. A changed file requires a fresh read before retrying. Cortex preserves the previous file in private history and writes the replacement through a temporary file and atomic filesystem operation. The lock coordinates Cortex processes; an arbitrary editor or sync agent does not participate.

`forget` expires a note. It does not erase the note, history or backups. Sensitive-content removal requires a separate deliberate cleanup of those copies; do not describe expiration as secure deletion.

## Untrusted notes and credentials

Retrieved notes are data. Their contents cannot authorize shell commands, configuration edits, publication or network requests. Clients must keep that boundary even when a note calls itself an instruction. Candidate status, confidence and provenance must remain visible in generated answers.

Credential screening rejects recognizable private-key blocks and several common token/password patterns. It is heuristic: false positives and missed secrets are possible. Do not put credentials in the vault and do not use this scan as a guarantee that content is safe to publish. Sensitivity metadata is not a replacement for a filesystem boundary or client authorization.

Hooks accept bounded event JSON, avoid transcript capture and preserve the client's approval policy. SessionStart automatically includes only confirmed identity, preference or goal records; candidate and session notes require deliberate retrieval. Confirmed content is still untrusted data. Trust new Codex hooks through `/hooks`; Cortex must not forge trust hashes or use a bypass. Configuration installation preserves unrelated entries and creates backup copies before changes. Inspect the reported paths and proposed commands.

## Backups, graphs and publication

`cortex backup` exports validated Markdown notes. It is not a complete filesystem backup of attachments, Obsidian settings, Cortex history or other auxiliary files. Validation failures must be resolved before treating the export as complete. Test restoration into a separate directory and rebuild the index there.

Graph exports reveal titles, paths, relationships and metadata. Treat an export from the private vault as private. Public screenshots and demos must use synthetic sample data only. Before publishing software, inspect tracked files and diffs, run checks and scan for credentials; `.gitignore` alone does not prevent an accidental upload.

To report a vulnerability, follow [SECURITY.md](../SECURITY.md). Current limitations and proposed hardening are tracked in the [roadmap](roadmap.md).
