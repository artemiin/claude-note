# Synthesis Modes

Claude Note supports three synthesis modes that control how session knowledge is processed and stored.

## Overview

| Mode | Processing | Output | Best for |
|------|------------|--------|----------|
| `log` | None | Raw session transcript | Archival, debugging |
| `inbox` | Full synthesis | Appends to inbox file | Review-then-file workflow |
| `route` | Full synthesis + routing | Creates/updates notes | Automated knowledge base |

Set the mode in `~/.config/claude-note/config.toml`:

```toml
[synthesis]
mode = "route"  # log | inbox | route
```

---

## Log Mode

**No synthesis. Just saves the raw session transcript.**

### How it works

1. Session ends
2. Full transcript saved to `claude-session-{id}.md`
3. No AI processing

### Output format

```markdown
---
session_id: abc-123-def
working_dir: /Users/you/project
started: 2024-01-15T10:30:00
ended: 2024-01-15T11:45:00
---

# Claude Session: project

## Transcript

**User:** How do I fix this authentication bug?

**Claude:** Looking at the code...

[full transcript continues]
```

### When to use

- Claude CLI not installed
- You want raw transcripts for reference
- Debugging Claude Note itself
- Privacy-conscious (no data sent to Claude API)

### Configuration

```toml
[synthesis]
mode = "log"
```

---

## Inbox Mode

**Full synthesis, appends everything to a single inbox file.**

### How it works

1. Session ends
2. Claude analyzes the transcript
3. Extracts: learnings, decisions, code patterns, questions
4. Appends structured summary to `claude-note-inbox.md`

### Output format

In `claude-note-inbox.md`:

```markdown
## Session: 2024-01-15 10:30 - project

### Summary
Fixed authentication bug in login flow by correcting JWT token validation.

### Learnings
- JWT `exp` claim is in seconds, not milliseconds
- Always validate token before checking claims

### Decisions
- Use `jsonwebtoken` library instead of manual parsing
- Add token refresh endpoint

### Code Patterns
```python
# Correct JWT validation
import jwt
try:
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
except jwt.ExpiredSignatureError:
    return None
```

### Open Questions
- [ ] Should we implement refresh token rotation?

---
```

### When to use

- You prefer to review and manually file knowledge
- Getting started (simpler than route mode)
- Smaller vaults without much existing structure

### Configuration

```toml
[synthesis]
mode = "inbox"
```

### Customizing inbox location

```toml
vault_root = "/path/to/vault"
inbox_file = "custom-inbox.md"  # relative to vault_root
```

---

## Route Mode

**Full synthesis with intelligent routing to existing and new notes.**

### How it works

1. Session ends
2. Claude analyzes the transcript
3. Extracts knowledge (same as inbox mode)
4. **Routes each piece of knowledge:**
   - Updates existing notes if relevant
   - Creates new topic notes for novel concepts
   - Appends unroutable items to inbox

### Routing logic

```
For each extracted insight:
├── Find related existing notes (via qmd or title matching)
├── If strong match found:
│   └── Append to that note's "## From Sessions" section
├── If novel concept:
│   └── Create new topic note
└── If unclear:
    └── Append to inbox for manual review
```

### Output examples

**Updating existing note** (`vim-tips.md`):

```markdown
<!-- existing content -->

## From Sessions

### 2024-01-15: project
- Use `ciw` to change inner word (faster than `bcw`)
- `gq` reformats text to textwidth

<!-- rest of note -->
```

**Creating new note** (`jwt-authentication.md`):

```markdown
---
tags: [topic, security, auth]
created: 2024-01-15
source: session
---

# JWT Authentication

## Overview
JSON Web Tokens for stateless authentication.

## Key Points
- `exp` claim is Unix timestamp in seconds
- Always validate signature before trusting claims
- Use `HS256` or `RS256` algorithms

## Code Examples
[extracted from session]

## Related
- [[authentication]]
- [[security]]
```

**Inbox fallback** (when unsure):

```markdown
## Unrouted: 2024-01-15 - project

> "The customer mentioned they want offline support"

*Couldn't find a relevant note. Consider creating [[offline-support]] or filing manually.*
```

### When to use

- Established vault with existing topic notes
- You want automated knowledge organization
- qmd is installed (greatly improves routing accuracy)

### Configuration

```toml
[synthesis]
mode = "route"
model = "claude-sonnet-4-5-20250929"

[qmd]
enabled = true           # Highly recommended for route mode
synth_max_notes = 5      # Context notes for routing decisions
```

---

## Comparison

### Processing Pipeline

```
Session Ends
     │
     ▼
┌─────────┐
│  Mode?  │
└─────────┘
     │
     ├── log ──────────► Save transcript ──► Done
     │
     ├── inbox ────────► Synthesize ──► Append to inbox ──► Done
     │
     └── route ────────► Synthesize ──► Route knowledge ──┬──► Update notes
                                                          ├──► Create notes
                                                          └──► Inbox fallback
```

### Resource Usage

| Mode | Claude API | Disk | Processing Time |
|------|------------|------|-----------------|
| log | None | Low | Instant |
| inbox | ~1 call | Low | 10-30 sec |
| route | ~2-3 calls | Medium | 30-60 sec |

### Privacy

| Mode | Data sent to Claude |
|------|---------------------|
| log | Nothing |
| inbox | Session transcript |
| route | Session transcript + relevant note excerpts |

---

## Switching Modes

You can switch modes anytime by editing the config:

```bash
# Edit config
vim ~/.config/claude-note/config.toml

# Change mode
[synthesis]
mode = "inbox"  # was "route"
```

Changes take effect for the next session. No restart needed.

### Re-processing with different mode

```bash
# Re-synthesize a session with different mode
claude-note resynth abc-123 --mode route
```

---

## Best Practices

### Starting out

1. Start with `inbox` mode
2. Review synthesized content
3. Manually organize into notes
4. Learn what kinds of notes you create

### Moving to route mode

1. Build up ~20-30 topic notes manually
2. Install and enable qmd for semantic search
3. Switch to `route` mode
4. Review the inbox for mis-routed items
5. Create missing topic notes as needed

### Hybrid approach

Some users keep `inbox` mode but periodically run:

```bash
# Re-synthesize recent sessions with routing
claude-note resynth $(claude-note status --recent) --mode route
```

This gives you control over when routing happens.
