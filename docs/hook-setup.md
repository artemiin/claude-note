# Claude Code Hook Setup

Claude Note integrates with Claude Code through hooks. This document explains how to configure them.

## Overview

Claude Code fires hooks at key moments:
- **PostToolUse**: After any tool is used
- **UserPromptSubmit**: When user sends a message
- **Stop**: When session ends

Claude Note listens to these events to track sessions and trigger synthesis.

## Configuration

### Option 1: Global Settings

Edit `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          { "type": "command", "command": "claude-note enqueue", "timeout": 5000 }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "claude-note enqueue", "timeout": 5000 }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "claude-note enqueue", "timeout": 5000 }
        ]
      }
    ]
  }
}
```

### Option 2: Per-Project Settings

Create `.claude/settings.json` in your project root with the same content.

## Hook Details

### PostToolUse

Fired after every tool use (file read, edit, bash command, etc.).

Used for:
- Keeping session state fresh
- Detecting activity patterns

### UserPromptSubmit

Fired when the user sends a message.

Used for:
- Question detection (adds to open questions tracker)
- Session activity tracking

### Stop

Fired when the session ends (user exits or session times out).

Used for:
- Triggering synthesis
- Finalizing session log

## Environment Variables

Claude Code provides these variables to hooks:

| Variable | Description |
|----------|-------------|
| `CLAUDE_SESSION_ID` | Unique session identifier |
| `CLAUDE_WORKING_DIR` | Current working directory |

## Verifying Setup

1. Start a Claude Code session
2. Check the queue:
   ```bash
   claude-note status
   ```
3. You should see pending events

## Troubleshooting

### Hooks not firing

1. Verify settings.json location and syntax:
   ```bash
   cat ~/.claude/settings.json | jq .
   ```

2. Check if claude-note is in PATH:
   ```bash
   which claude-note
   ```

3. Test hook manually:
   ```bash
   claude-note enqueue test "test-session-id"
   ```

### Events queued but not processed

1. Check if worker is running:
   ```bash
   # macOS
   launchctl list | grep claude-note

   # Linux
   systemctl --user status claude-note
   ```

2. Check worker logs:
   ```bash
   tail -f /path/to/vault/.claude-note/logs/worker-*.log
   ```

### Synthesis not running

1. Verify Claude CLI is installed:
   ```bash
   which claude
   ```

2. Check if you're authenticated:
   ```bash
   claude --version
   ```

3. Check synthesis mode in config:
   ```bash
   cat ~/.config/claude-note/config.toml
   ```

## Minimal Setup

If you only want session logging (no synthesis), you can use just the Stop hook:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "claude-note enqueue", "timeout": 5000 }
        ]
      }
    ]
  }
}
```

And set mode to "log":

```toml
[synthesis]
mode = "log"
```

## Advanced: Filtering by Directory

To only capture sessions in specific directories, add a `matcher` regex:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "/Users/you/work/.*",
        "hooks": [
          { "type": "command", "command": "claude-note enqueue", "timeout": 5000 }
        ]
      }
    ]
  }
}
```

The `matcher` is a regex against the working directory.
