---
title: "AGENTS.md — FERDG Second Brain Schema"
purpose: "Compiler specification for the persistent-memory knowledgebase"
adapted_from: "https://github.com/coleam00/claude-memory-compiler (Cole Medin)"
upstream_origin: "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (Andrej Karpathy)"
runtime: "Claude Code CLI (migrated from Cowork 2026-05-04)"
created: 2026-04-22
---

# AGENTS.md — FERDG Second Brain Schema

> Adapted from Cole Medin's `claude-memory-compiler` (which itself adapts Karpathy's LLM Knowledge Base architecture). Migrated to **Claude Code CLI** (2026-05-04) with Agent SDK scripts (`flush.py`, `compile.py`, `query.py`, `lint.py`), shell hooks (`SessionStart`, `PreCompact`, `SessionEnd`), and slash commands (`/flush`, `/compile`, `/query`, `/lint`).
>
> **Source material is conversations with Claude inside the FERDG Second Brain Obsidian vault.** Compiled outputs are Obsidian-native markdown with `[[wikilinks]]` so the graph view, backlinks, and search work with zero extra config.

---

## The Compiler Analogy

```
daily/          = source code      (raw conversation logs — append-only, immutable)
Claude (LLM)    = compiler         (extracts, organizes, cross-references)
knowledge/      = executable       (structured queryable knowledgebase)
Runbooks/lint   = test suite       (consistency + health checks)
queries         = runtime          (using the knowledge to answer questions)
```

Humans converse. The LLM synthesizes, cross-references, and maintains the structure. Manual editing of `knowledge/` is allowed but rare — the compiler owns it.

---

## Three-Layer Architecture

### Layer 1 — `daily/` (Immutable Source Logs)

Append-only logs of what happened in each Cowork session. One file per calendar day.

```
daily/
├── 2026-04-22.md
├── 2026-04-23.md
└── ...
```

Format of each daily log:

```markdown
# Daily Log: YYYY-MM-DD

## Sessions

### Session (HH:MM) — Brief Title

**Context:** What MJ was working on (project, file, problem).

**Key Exchanges:**
- User asked X, assistant explained Y
- Decided Z because...
- Discovered W doesn't work when...

**Decisions Made:**
- Chose approach A over B because...
- Architecture / methodology choice...

**Lessons Learned:**
- Always do X before Y to avoid...
- Gotcha with Z: ...

**Action Items:**
- [ ] Follow up on X
- [ ] Refactor Y when time permits
```

### Layer 2 — `knowledge/` (LLM-Owned Compiled Output)

```
knowledge/
├── index.md              # Master catalog — read FIRST on every query
├── log.md                # Append-only build log (compiles, queries, lints)
├── concepts/             # Atomic knowledge articles
├── connections/          # Cross-cutting insights linking 2+ concepts
└── qa/                   # Filed Q&A answers (compounding knowledge)
```

### Layer 3 — `AGENTS.md` (This File)

The schema. Tells Claude how to compile, query, and lint. The "compiler specification."

---

## Structural Files

### `knowledge/index.md` — Master Catalog

Primary retrieval mechanism. Every article gets one row. Read this FIRST to answer any query, then pull the relevant articles in full.

Format:

```markdown
# Knowledge Base Index

| Article | Summary | Compiled From | Updated |
|---------|---------|---------------|---------|
| [[concepts/ansys-mesh-quality-thresholds]] | Default skewness/aspect-ratio limits MJ uses on rocket nozzle CFD | daily/2026-04-22.md | 2026-04-22 |
| [[connections/daq-noise-and-grounding]] | Why ESP32 ADC noise traces back to shared analog/digital ground in MJ's test stand wiring | daily/2026-04-22.md, daily/2026-04-25.md | 2026-04-25 |
```

### `knowledge/log.md` — Build Log

Append-only chronological record of every compile, query, and lint operation.

```markdown
# Build Log

## [2026-04-22T18:00:00] compile | Daily Log 2026-04-22
- Source: daily/2026-04-22.md
- Articles created: [[concepts/ansys-mesh-quality-thresholds]]
- Articles updated: (none)

## [2026-04-23T09:14:00] query | "What ADC noise floor have I measured on ESP32?"
- Consulted: [[concepts/esp32-adc-noise]], [[connections/daq-noise-and-grounding]]
- Filed to: [[qa/esp32-adc-measured-noise-floor]]
```

---

## Article Formats

### Concept Articles — `knowledge/concepts/`

One article per atomic piece of knowledge: a fact, pattern, decision, preference, or lesson.

```markdown
---
title: "Concept Name"
aliases: [alternate-name, abbreviation]
tags: [domain, topic]
sources:
  - "daily/2026-04-22.md"
  - "daily/2026-04-25.md"
created: 2026-04-22
updated: 2026-04-25
---

# Concept Name

[2–4 sentence core explanation]

## Key Points

- [Self-contained bullets]

## Details

[Encyclopedia-style paragraphs]

## Related Concepts

- [[concepts/related-concept]] — How it connects

## Sources

- [[daily/2026-04-22]] — Initial discovery during nozzle CFD setup
- [[daily/2026-04-25]] — Updated after debug session
```

### Connection Articles — `knowledge/connections/`

Cross-cutting synthesis linking 2+ concepts. Created when a conversation reveals a non-obvious relationship.

```markdown
---
title: "Connection: X and Y"
connects:
  - "concepts/concept-x"
  - "concepts/concept-y"
sources:
  - "daily/2026-04-25.md"
created: 2026-04-25
updated: 2026-04-25
---

# Connection: X and Y

## The Connection

[What links these concepts]

## Key Insight

[The non-obvious relationship]

## Evidence

[Specific examples from conversations]

## Related Concepts

- [[concepts/concept-x]]
- [[concepts/concept-y]]
```

### Q&A Articles — `knowledge/qa/`

Filed answers from queries. Every non-trivial question answered against the KB can be persisted, compounding future retrieval quality.

```markdown
---
title: "Q: Original Question"
question: "The exact question asked"
consulted:
  - "concepts/article-1"
  - "concepts/article-2"
filed: 2026-04-25
---

# Q: Original Question

## Answer

[Synthesized answer with [[wikilink]] citations]

## Sources Consulted

- [[concepts/article-1]] — Relevant because...
- [[concepts/article-2]] — Provided context on...

## Follow-Up Questions

- What about edge case X?
- How does this change if Y?
```

---

## Core Operations

The four operations live in `Runbooks/`. Each runbook is a markdown procedure Claude follows step-by-step. Invoke by saying things like "flush memory", "compile the daily logs", "query the kb for X", "lint the kb".

### 1. Flush — Capture (transcript → `daily/`)

Detailed steps: see `Runbooks/flush.md`.

Summary: list recent Cowork sessions via `mcp__session_info__list_sessions`, read transcripts via `mcp__session_info__read_transcript`, decide what's worth saving, append a session block to `daily/YYYY-MM-DD.md`.

### 2. Compile — Synthesize (`daily/` → `knowledge/`)

Detailed steps: see `Runbooks/compile.md`.

Summary: for each un-compiled daily log, read this AGENTS.md schema, read `knowledge/index.md`, read affected existing articles, then create or update `concepts/`, `connections/`, refresh `index.md`, append to `log.md`.

**Key guidelines:**
- A single daily log may touch 3–10 articles
- Prefer updating existing articles over creating near-duplicates
- Use Obsidian `[[wikilinks]]` with full relative paths from `knowledge/`
- Write encyclopedia-style — factual, concise, self-contained
- Every article must have YAML frontmatter
- Every article must link back to its source daily log(s)

### 3. Query — Retrieve (index-guided, no RAG)

Detailed steps: see `Runbooks/query.md`.

Summary: read `knowledge/index.md`, pick 3–10 relevant articles, read in full, synthesize an answer with `[[wikilink]]` citations. With `--file-back`, also create a `knowledge/qa/` article and update `index.md` + `log.md`.

**Why no RAG:** at personal-vault scale (50–500 articles) the LLM reading a structured index outperforms cosine similarity. The LLM understands intent; embeddings just find similar tokens. Revisit if the vault crosses ~2,000 articles.

### 4. Lint — Health Checks (7 checks)

Detailed steps: see `Runbooks/lint.md`.

| Check | Type | Catches |
|-------|------|---------|
| Broken links | Structural | `[[wikilinks]]` to non-existent articles |
| Orphan pages | Structural | Articles with zero inbound links |
| Orphan sources | Structural | Daily logs not yet compiled |
| Stale articles | Structural | Source logs changed after article was last compiled |
| Missing backlinks | Structural | A links to B but B doesn't link back |
| Sparse articles | Structural | Under 200 words, likely incomplete |
| Contradictions | LLM | Conflicting claims across articles |

Reports written to `reports/lint-YYYY-MM-DD.md`.

---

## Conventions

- **Wikilinks:** Obsidian-style `[[path/to/article]]`, no `.md` extension, relative to `knowledge/`
- **Writing style:** encyclopedia-style, factual, third-person where appropriate
- **Dates:** ISO 8601 (`YYYY-MM-DD`; full ISO `YYYY-MM-DDTHH:MM:SS` for `log.md`)
- **File naming:** lowercase, hyphens for spaces (e.g., `esp32-adc-noise.md`)
- **Frontmatter:** every article has YAML frontmatter with at minimum `title`, `sources`, `created`, `updated`
- **Sources:** every article links back to the daily log(s) that contributed to it

---

## Differences From Upstream (`claude-memory-compiler`)

| Upstream (Claude Code) | This vault (Claude Cowork) |
|---|---|
| `.claude/settings.json` hooks (`SessionStart`, `SessionEnd`, `PreCompact`) | `mcp__scheduled-tasks` for daily auto-compile + on-demand `flush` runbook |
| `hooks/session-end.py` spawns detached `flush.py` | User says "flush memory" or scheduled task fires; Claude executes `Runbooks/flush.md` inline |
| `scripts/compile.py` runs Claude Agent SDK headlessly | `Runbooks/compile.md` — Claude executes inline using Read/Write/Edit/Glob/Grep |
| `scripts/query.py` | `Runbooks/query.md` — invoked when user asks the KB anything |
| `scripts/lint.py` | `Runbooks/lint.md` — invoked manually or on a weekly schedule |
| Python `state.json` for compile dedup | Compile runbook checks `knowledge/log.md` for what's already been compiled |
| `~/.claude/.credentials.json` for Agent SDK billing | No SDK calls — work happens inside the live Cowork session |

**Implication:** there is no background process. Capture and compile happen either when the user explicitly asks, or when the daily scheduled task wakes Claude. This is acceptable at personal scale and avoids the SDK-credential / sandbox-mount problems Cowork would otherwise face.

---

## Full Project Structure

```
FERDG Second Brain/
├── AGENTS.md                        # This file — schema + technical reference
├── README.md                        # Quick start + layout
├── FERDG Notes.md                   # Root dashboard (entry point for Obsidian)
│
├── daily/                           # Layer 1 — immutable per-day session logs
├── weekly/                          # End-of-week reflection (YYYY-Www.md)
├── knowledge/                       # Layer 2 — compiled KB (LLM-owned)
│   ├── index.md                     #   Master catalog — primary retrieval
│   ├── log.md                       #   Append-only build log
│   ├── concepts/                    #   Atomic knowledge articles
│   ├── connections/                 #   Cross-cutting insights
│   └── qa/                          #   Filed Q&A answers
│
├── FERDG/                           # Department operating data
│   ├── FERDG Projects/              #   Active + archived project notes
│   │   └── NEO-S v1/                #     Per-project folder with nested Research/, Planning/
│   ├── FERDG Members/               #   People profiles
│   ├── FERDG Job Orders/            #   Individual job orders
│   ├── FERDG Work Meetings/         #   Minutes of the meeting
│   └── FERDG WPR/                   #   Formal Work Progress Reports
│
├── standards/                       # Research / design / operating standards (renamed from Knowledge Base)
│   ├── ANSYS/
│   ├── Instrumentation/
│   ├── Mechanical Systems/
│   └── Propulsion/
│
├── Miscellaneous/
│   ├── People/                      # External people (non-FERDG)
│   └── Organizations/               # External orgs (vendors, consultancies)
│
├── Bases/                           # Obsidian Bases (tag-filtered tables)
├── Templates/                       # Note templates (project, WPR, meeting, job order, weekly)
├── Attachments/                     # PDFs and pasted images
├── Runbooks/                        # Operation procedures
│   ├── flush.md                     #   transcript → daily/
│   ├── compile.md                   #   daily/ → knowledge/
│   ├── query.md                     #   index-guided retrieval
│   └── lint.md                      #   7 health checks
├── reports/                         # Lint output (lint-YYYY-MM-DD.md)
└── Archive/                         # Dept-wide tombstones for deprecated notes
```

The FERDG department-data tree (`FERDG/`), `standards/`, and `Miscellaneous/` are curated human-authored notes. The compiler in `Runbooks/compile.md` treats them as read-only context — it reads them to ground concept articles but does not reorganize them. The compiler owns `knowledge/`.

### Renamed / new in 2026-04-22 cleanup

- `Knowledge Base/` → `standards/` (separates curated standards from LLM-compiled `knowledge/`)
- `weekly/` created (end-of-week reflection, distinct from formal `FERDG/FERDG WPR/`)
- `Templates/Weekly Log.md` added
- NEO-S v1 `Archive/` tombstoned (planning + meeting + literature-review moved to live locations)
- Root-level strays (`Feb 23.md`, `Untitled.md`) relocated or tombstoned
- Gemini CLI artifacts (`GEMINI.md`) tombstoned — they're from a prior non-Claude tool

## ClickUp Integration (planned)

A future runbook `Runbooks/clickup-sync.md` will pull ClickUp tasks, comments, and status changes into the daily/ logs so the compiler can cross-reference project-tracker activity against Cowork conversations. Integration target: custom fields on `FERDG Projects` bases mirror ClickUp list IDs.

---

## Customization Knobs (For MJ)

- **Additional article types.** Add directories like `knowledge/people/`, `knowledge/projects/`, `knowledge/memos/`. Document the article format here in AGENTS.md and update `Runbooks/compile.md`'s "where to file new content" section.
- **FERDG-specific tags.** Use the `tags:` frontmatter field for department dimensions (e.g., `propulsion`, `daq`, `cfd`, `firmware`, `audit`).
- **Existing notes migration.** A future runbook (`Runbooks/migrate-existing.md`) can lift existing FERDG notes into `knowledge/` while preserving their original location as the "source."
- **Scaling beyond ~2,000 articles.** Add hybrid retrieval (keyword + semantic) before the index becomes too large for context. Not needed today.

---

## Attribution

- Compiler architecture: [Andrej Karpathy — LLM Knowledge Base gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Conversation-source adaptation + hook design: [Cole Medin — claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler)
- Cowork adaptation: this vault
