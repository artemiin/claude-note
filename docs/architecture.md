# Architecture

Deep dive into how Claude Note works internally.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │
│  │ToolUse │  │ Prompt  │  │  Stop   │  (Hooks)                 │
│  └────┬────┘  └────┬────┘  └────┬────┘                         │
└───────┼────────────┼────────────┼───────────────────────────────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      claude-note enqueue                         │
│  - Receives event via stdin                                      │
│  - Writes to queue file                                          │
│  - Returns immediately (non-blocking)                            │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Queue Directory                               │
│  .claude-note/queue/                                             │
│  ├── 2024-01-15.jsonl    (today's events)                       │
│  └── 2024-01-14.jsonl    (yesterday's events)                   │
└─────────────────────────────────────────────────────────────────┘
        │
        │ (watches)
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Background Worker                             │
│  - Runs as launchd/systemd service                              │
│  - Monitors queue directory                                      │
│  - Manages session state                                         │
│  - Triggers synthesis on session end                            │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Synthesizer                                 │
│  - Reads session transcript                                      │
│  - Gathers vault context (via qmd)                              │
│  - Calls Claude API for analysis                                 │
│  - Returns structured knowledge                                  │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Note Router                                  │
│  - Matches knowledge to existing notes                          │
│  - Decides: update / create / inbox                             │
│  - Handles managed blocks                                        │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Note Writer                                  │
│  - Writes/updates markdown files                                │
│  - Manages frontmatter                                           │
│  - Handles concurrent access                                     │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Vault                                     │
│  your-vault/                                                     │
│  ├── claude-note-inbox.md                                       │
│  ├── topic-note.md                                               │
│  └── new-topic.md                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### Enqueue (`enqueue.py`)

The entry point for hook events. Designed to be fast and non-blocking.

**Responsibilities:**
- Parse stdin JSON from Claude Code
- Extract session metadata from environment
- Write event to daily queue file
- Return immediately (hooks have timeout)

**Input:**
```json
{
  "type": "tool_use",
  "tool": "Read",
  "file": "/path/to/file.py",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Environment:**
```bash
CLAUDE_SESSION_ID=abc-123-def
CLAUDE_WORKING_DIR=/Users/you/project
```

**Output:** Appends to `.claude-note/queue/2024-01-15.jsonl`

### Queue Manager (`queue_manager.py`)

Handles queue file I/O with proper locking.

**Features:**
- Atomic writes (write to temp, rename)
- File locking for concurrent access
- Automatic daily rotation
- Queue compaction (removes processed events)

**Queue file format:**
```jsonl
{"session_id":"abc","event":"tool_use","timestamp":"...","data":{...}}
{"session_id":"abc","event":"prompt","timestamp":"...","data":{...}}
{"session_id":"abc","event":"stop","timestamp":"...","data":{}}
```

### Session Tracker (`session_tracker.py`)

Maintains state for active sessions.

**State file:** `.claude-note/state/{session_id}.json`

```json
{
  "session_id": "abc-123-def",
  "working_dir": "/Users/you/project",
  "started_at": "2024-01-15T10:30:00Z",
  "last_activity": "2024-01-15T11:45:00Z",
  "event_count": 47,
  "status": "active",
  "tools_used": ["Read", "Edit", "Bash"],
  "files_touched": ["/path/to/file.py"]
}
```

**Session lifecycle:**
```
first event ──► active ──► stop event ──► synthesizing ──► completed
                  │                            │
                  └── timeout (30min) ─────────┘
```

### Worker (`worker.py`)

Long-running background process that orchestrates everything.

**Main loop:**
```python
while True:
    events = queue.get_pending()
    for event in events:
        session = tracker.update(event)
        if session.should_synthesize():
            synthesizer.process(session)
            tracker.mark_completed(session)
    sleep(poll_interval)
```

**Configuration:**
- Poll interval: 5 seconds
- Session timeout: 30 minutes of inactivity
- Max concurrent syntheses: 1 (sequential processing)

### Transcript Reader (`transcript_reader.py`)

Reads Claude Code session transcripts from disk.

**Transcript location:** `~/.claude/projects/{project_hash}/{session_id}.jsonl`

**Format:**
```jsonl
{"role":"user","content":"How do I fix this?"}
{"role":"assistant","content":"Looking at the code...","tool_calls":[...]}
{"role":"tool","content":"[file contents]"}
```

**Processing:**
- Filters out binary/large tool results
- Truncates very long messages
- Extracts conversation structure

### Synthesizer (`synthesizer.py`)

Core AI processing component.

**Process:**
1. Load transcript
2. Gather context (vault index, relevant notes via qmd)
3. Build synthesis prompt
4. Call Claude API
5. Parse structured response
6. Return knowledge pack

**Synthesis prompt structure:**
```
<system>
You are analyzing a coding session. Extract:
- Key learnings and insights
- Decisions made and rationale
- Code patterns worth remembering
- Open questions raised
</system>

<context>
Relevant existing notes:
{qmd search results}
</context>

<transcript>
{session transcript}
</transcript>

Output as JSON:
{schema}
```

### Knowledge Pack (`knowledge_pack.py`)

Data structure for synthesized knowledge.

```python
@dataclass
class KnowledgePack:
    session_id: str
    summary: str
    learnings: List[Learning]
    decisions: List[Decision]
    code_patterns: List[CodePattern]
    questions: List[Question]
    suggested_notes: List[NoteSuggestion]
```

### Note Router (`note_router.py`)

Decides where each piece of knowledge should go.

**Routing algorithm:**
```python
def route(item: Learning) -> RouteDecision:
    # 1. Semantic search for similar notes
    matches = qmd.search(item.content, limit=5)

    # 2. Score matches
    best = max(matches, key=lambda m: m.score)

    # 3. Decision
    if best.score > 0.8:
        return RouteDecision.UPDATE(best.note)
    elif item.is_novel_concept:
        return RouteDecision.CREATE(item.suggested_title)
    else:
        return RouteDecision.INBOX()
```

**Route decisions:**
- `UPDATE`: Append to existing note's "From Sessions" section
- `CREATE`: Generate new topic note
- `INBOX`: Append to inbox for manual review

### Note Writer (`note_writer.py`)

Handles all file I/O for notes.

**Features:**
- Frontmatter preservation
- Managed block updates (won't overwrite manual edits)
- Atomic writes
- Concurrent access handling

**Managed blocks:**
```markdown
<!-- claude-note:start:sessions -->
Content managed by Claude Note.
Don't edit manually.
<!-- claude-note:end:sessions -->
```

### Managed Blocks (`managed_blocks.py`)

System for updating specific sections without touching manual content.

**Block types:**
- `sessions`: Session-derived learnings
- `questions`: Open questions from sessions
- `related`: Auto-generated related links

**Update modes:**
- `append`: Add new content
- `replace`: Replace entire block
- `merge`: Intelligent merge (dedupe)

### Vault Indexer (`vault_indexer.py`)

Builds searchable index of vault contents.

**Index file:** `.claude-note/vault_index.json`

```json
{
  "notes": {
    "topic-note.md": {
      "title": "Topic Note",
      "aliases": ["topic", "the topic"],
      "tags": ["topic", "reference"],
      "summary": "First paragraph...",
      "links_to": ["other-note.md"],
      "linked_from": ["another-note.md"]
    }
  },
  "tags": {
    "topic": ["topic-note.md", "another.md"],
    "reference": ["topic-note.md"]
  },
  "indexed_at": "2024-01-15T10:00:00Z"
}
```

### QMD Search (`qmd_search.py`)

Interface to qmd semantic search.

**Usage:**
```python
# Search for related notes
results = qmd_search.search("JWT token validation", limit=5)
# Returns: [{"file": "auth.md", "score": 0.85, "excerpt": "..."}]
```

**Fallback:** If qmd not available, falls back to keyword matching against vault index.

### Open Questions (`open_questions.py`)

Tracks questions that arise during sessions.

**Format in `open-questions.md`:**
```markdown
## Active Questions

### Authentication
- [ ] Should we implement refresh token rotation?
  - *Source: 2024-01-15 project session*
- [x] How does JWT expiration work?
  - *Found: 2024-01-15 - `exp` is Unix timestamp in seconds*

### Performance
- [ ] Why is the API slow on first request?
```

---

## Data Flow Examples

### Tool Use Event

```
User uses Read tool in Claude Code
         │
         ▼
Hook fires: claude-note enqueue
         │
         ▼
Event written to queue/2024-01-15.jsonl
         │
         ▼
Worker picks up event (within 5s)
         │
         ▼
Session tracker updates last_activity
         │
         ▼
(no synthesis yet - session still active)
```

### Session End

```
User exits Claude Code (or 30min timeout)
         │
         ▼
Stop event received
         │
         ▼
Session marked for synthesis
         │
         ▼
Transcript loaded from ~/.claude/projects/...
         │
         ▼
qmd searches for relevant notes (if enabled)
         │
         ▼
Claude API call with transcript + context
         │
         ▼
KnowledgePack returned
         │
         ▼
Note Router processes each item
         │
         ├──► Update: vim-tips.md (append to "From Sessions")
         ├──► Create: jwt-auth.md (new topic note)
         └──► Inbox: unclear items appended
         │
         ▼
Session marked completed
```

---

## File Locations

### Installation

| Path | Contents |
|------|----------|
| `~/.local/share/claude-note/` | Source code |
| `~/.local/bin/claude-note` | CLI shim |
| `~/.config/claude-note/config.toml` | Configuration |

### Vault

| Path | Contents |
|------|----------|
| `{vault}/.claude-note/queue/` | Event queue files |
| `{vault}/.claude-note/state/` | Session state files |
| `{vault}/.claude-note/logs/` | Worker logs |
| `{vault}/.claude-note/vault_index.json` | Note index |

### Claude Code

| Path | Contents |
|------|----------|
| `~/.claude/settings.json` | Hook configuration |
| `~/.claude/projects/{hash}/` | Session transcripts |

---

## Error Handling

### Queue errors
- Corrupt queue file: Archived, new file created
- Write failure: Event logged to stderr, retry next cycle

### Synthesis errors
- Claude API error: Logged, session kept for retry
- Parse error: Raw response saved, falls back to inbox mode

### File errors
- Note locked: Retry with backoff
- Disk full: Alert in status, pause processing
