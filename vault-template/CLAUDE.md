# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Personal technical knowledge base / Obsidian vault for structured notes on coding and technical work.

## Structure

Flat structure - all notes live in root. Only folder is `templates/`.

**Organization is via tags and links, not folders:**
- `#topic` - Concept/reference notes
- `#project/name` - Project-specific (nested tags)
- `#log` - Work logs, debugging sessions
- `#til` - Today I Learned snippets
- `[[wiki-links]]` - Connect related notes

## Note Conventions

- Frontmatter with `tags:` array preferred
- Add `aliases:` for alternative names (improves linking)
- Code blocks use triple backticks with language
- Links use `[[note-name]]` or `[[note-name|display text]]`
- Every note should link to at least 2-3 other notes
- Mark unwritten notes as `(TODO)` in links

## Templates

Located in `templates/`:
- `topic.md` - Concept/reference notes
- `project.md` - Project tracking
- `debug-session.md` - Problem -> investigation -> solution
- `til.md` - Quick learnings

## Claude Note Integration

This vault uses claude-note for automatic session logging.

**Session notes** are auto-generated as `claude-session-YYYY-MM-DD-XXXXXXXX.md`

**Inbox** at `claude-note-inbox.md` receives synthesized knowledge to review

**Open questions** tracked in `open-questions.md`

### Commands

```bash
claude-note status    # Check worker status
claude-note drain     # Force-process pending sessions
claude-note clean     # Cleanup and deduplicate
claude-note index     # Rebuild vault index
```

## Related

- [[obsidian-workflow]] - How to use this vault
- [[open-questions]] - Things to investigate
