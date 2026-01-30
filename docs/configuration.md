# Configuration Reference

Claude Note uses a TOML configuration file with environment variable overrides.

## Config File Location

```
~/.config/claude-note/config.toml
```

This follows the XDG Base Directory specification.

## Required Settings

### vault_root

Path to your Obsidian vault (or markdown notes directory).

```toml
vault_root = "/Users/you/Documents/notes"
```

Or via environment variable:
```bash
export CLAUDE_NOTE_VAULT="/Users/you/Documents/notes"
```

## Optional Settings

### open_questions_file

Path to your open questions tracker, relative to vault root.

```toml
open_questions_file = "open-questions.md"  # default
```

Environment: `CLAUDE_NOTE_OPEN_QUESTIONS`

## Synthesis Settings

```toml
[synthesis]
mode = "route"
model = "claude-sonnet-4-5-20250929"
```

### mode

How synthesized knowledge is handled:

| Mode | Behavior |
|------|----------|
| `log` | Only write session log, no synthesis |
| `inbox` | Append all knowledge to inbox |
| `route` | Smart routing to specific notes or inbox (default) |

Environment: `CLAUDE_NOTE_MODE`

### model

Claude model to use for synthesis.

```toml
model = "claude-sonnet-4-5-20250929"
```

Environment: `CLAUDE_NOTE_MODEL`

## QMD Integration

```toml
[qmd]
enabled = false
synth_max_notes = 5
```

### enabled

Whether to use qmd for semantic search during synthesis. Requires qmd to be installed and your vault indexed.

### synth_max_notes

Maximum number of related notes to include as context during synthesis.

## Complete Example

```toml
# Required
vault_root = "/Users/you/Documents/notes"

# Optional
open_questions_file = "meta/questions.md"

[synthesis]
mode = "route"
model = "claude-sonnet-4-5-20250929"

[qmd]
enabled = true
synth_max_notes = 5
```

## Environment Variables

All settings can be overridden with environment variables:

| Variable | Setting |
|----------|---------|
| `CLAUDE_NOTE_VAULT` | vault_root |
| `CLAUDE_NOTE_OPEN_QUESTIONS` | open_questions_file |
| `CLAUDE_NOTE_MODE` | synthesis.mode |
| `CLAUDE_NOTE_MODEL` | synthesis.model |
| `CLAUDE_NOTE_QMD_ENABLED` | qmd.enabled |

Environment variables take precedence over config file values.

## Multiple Vaults

To use different vaults for different projects, set `CLAUDE_NOTE_VAULT` per-project:

```bash
# In project A
export CLAUDE_NOTE_VAULT="/path/to/project-a/notes"

# In project B
export CLAUDE_NOTE_VAULT="/path/to/project-b/notes"
```

You can add this to project-specific shell configs or direnv.

## Config Validation

Run `claude-note status` to verify your configuration:

```bash
claude-note status
```

This shows:
- Configured vault path
- Worker status
- Queue status
- Any configuration errors
