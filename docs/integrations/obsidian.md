# Obsidian

Obsidian is the primary optional graphical interface for the private Markdown vault. Cortex does not require an Obsidian account, subscription or community plugin.

Initialize the folder, then open it:

```sh
cortex init "$HOME/Brain"
cortex --brain "$HOME/Brain" open
```

If it is not registered as a vault, use Obsidian's vault switcher and **Open folder as vault**, selecting `~/Brain`. Open the existing folder rather than creating a nested vault or replacing another vault. This is the workflow described in [Obsidian's vault guide](https://obsidian.md/help/vault).

Use the built-in Files, Backlinks, Outgoing links, Tags and Graph view. Local graph helps inspect relationships around one note. Standard `[[Wiki links]]` connect notes; frontmatter is visible in Properties. Cortex's own link resolution is deliberately smaller than the full Obsidian feature set, so an Obsidian-only query or plugin feature may not have a Cortex equivalent.

Edit an identity template only with information you choose to store. Cortex's starter templates are candidates, not established personal facts. When changing a dated decision, maintain its `updated` field and status. Cortex refreshes its index from eligible files on subsequent operations:

```sh
cortex --brain "$HOME/Brain" reindex
cortex --brain "$HOME/Brain" doctor
```

Obsidian's `.obsidian` configuration is separate from Cortex's `.cortex` state. Cortex's note scanner excludes hidden directories. Notes remain usable in any text editor when either application is closed.

Opening Obsidian is not proof it selected the intended vault: check the displayed folder and a known note. Any exported graph or screenshot from your private brain may reveal personal information. Use `cortex demo PATH` with a separate synthetic directory for public demonstrations.

Cloud sync, plugins and attachments are outside the v0.1 baseline. No sync purchase or plugin installation is necessary. See [security and backup limits](../security.md) before sharing exports or using a synced directory.
