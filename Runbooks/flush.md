---
runbook: flush
purpose: "Capture recent Cowork conversation context into a dated daily log"
inputs: "Recent session transcript(s) accessible via mcp__session_info"
outputs: "Appended session block in daily/YYYY-MM-DD.md"
invoke_when:
  - User says "flush memory", "flush", "capture this session", "save what we did"
  - Daily scheduled task fires (auto-runs flush + compile in sequence)
---

# Runbook: Flush

## Purpose

Move ephemeral conversation context into the persistent `daily/` layer before it is lost. Equivalent to `flush.py` in upstream `claude-memory-compiler`, but executed inline by Claude inside the live Cowork session.

## Preconditions

- `daily/` directory exists at vault root
- This file (`AGENTS.md`) is readable for schema reference

## Steps

### 1. Resolve today's date

Use the date in `<env>` (today is `YYYY-MM-DD`). The target file is `daily/YYYY-MM-DD.md`.

### 2. Identify which session(s) to flush

Default behavior: flush the **current session** (the conversation Claude is in right now). The current conversation is already in context — no MCP call needed.

If the user says "flush all sessions from today" or similar, list sessions first:

```
mcp__session_info__list_sessions
```

Then for each session of interest:

```
mcp__session_info__read_transcript(session_id=...)
```

Skip sessions where `cwd` is not the FERDG Second Brain vault.

### 3. Decide what's worth saving

Read the transcript (or the in-context conversation). Extract only items that meet **at least one** bar:

- A decision was made (and the rationale)
- A new fact about a project, system, member, or process was established
- A gotcha or counter-intuitive lesson was learned
- An action item was created or assigned
- A reference to an external resource (Linear ticket, Gong call, ANSYS run, datasheet, etc.) that future sessions will need

Skip:
- Pleasantries, clarifications, repeated context
- Errors that were debugged in-session and don't generalize
- Anything already documented in `knowledge/`

If nothing meets the bar, write a single line `- (No persistent items this session)` under today's date and exit. Do NOT skip writing the file entirely — its mere existence signals "Claude looked."

### 4. Format the session block

Append to `daily/YYYY-MM-DD.md` using this structure (create the file with the `# Daily Log: YYYY-MM-DD` H1 if it does not exist; otherwise just append a new `### Session` block under the existing `## Sessions` header):

```markdown
### Session (HH:MM) — Brief Title

**Context:** [1–2 sentences on what MJ was working on]

**Key Exchanges:**
- [bullet] [bullet]
- ...

**Decisions Made:**
- ...

**Lessons Learned:**
- ...

**Action Items:**
- [ ] ...
```

Time is local 24h, derived from current session start time if known, otherwise current time.

### 5. Confirm to the user

One-line summary: `Flushed N items to daily/YYYY-MM-DD.md`. Do not paste the full appended block — user can open the file.

## Deduplication

Before appending, scan today's daily log. If a session block with the same `Brief Title` and overlapping `Context` already exists from the same hour, **update** that block in place instead of appending a duplicate. Use `Edit` for surgical replacement.

## Failure modes

- **Empty transcript** → write nothing, report "Nothing to flush."
- **Wrong vault cwd** → skip; this runbook only flushes FERDG sessions.
- **`mcp__session_info` unavailable** → fall back to in-context conversation only.

## Next step

If invoked by the daily scheduled task, immediately proceed to `Runbooks/compile.md`. If invoked manually, suggest: "Want me to compile now? (`Runbooks/compile.md`)"
