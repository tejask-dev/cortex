# Security policy

The latest 0.1.x code line is the initial maintenance target. Cortex is early software; no formal security audit or response-time guarantee is claimed. The security boundary and known limitations are described in [docs/security.md](docs/security.md).

## Reporting a vulnerability

Use the repository's **Security → Report a vulnerability** option if private reporting is enabled. If that option is unavailable, open an issue asking a maintainer for a private reporting channel and omit exploit details. Do not post private vault contents, tokens, raw conversations or credentials.

Include the affected version or commit, operating system, a minimal synthetic reproduction, expected behavior, observed behavior and the impact. Filesystem escapes, unexpected network access, unsafe writes and credential disclosure are particularly relevant. Keep demonstrations confined to data you own or have permission to test.

Maintainers should reproduce reports with synthetic data, agree on a fix and regression test, and coordinate disclosure before publishing details that would expose users. This document does not assert that GitHub private reporting is enabled; check the actual repository UI.

## Scope

Cortex restricts its own APIs to a configured local vault. It does not provide an OS sandbox or isolate a malicious same-user process. The vault, index, history and backups are plaintext. Connected cloud clients can transmit retrieved content to their model providers. Forgetting expires a record; it is not secure erasure.
