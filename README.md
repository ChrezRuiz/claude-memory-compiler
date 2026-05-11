# FERDG Second Brain

Persistent-memory knowledgebase for the FERDG aerospace department, built on top of the Obsidian vault and operated by Claude Cowork.

Architecture adapted from [coleam00/claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler) (which adapts [Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) for Claude Cowork — see `AGENTS.md` for the full spec.

## What it does

Conversations with Claude in this vault are captured into dated logs (`daily/`), then compiled by the LLM into a structured knowledgebase (`knowledge/`) with cross-references and an index. Future questions are answered against the index, not by re-reading every conversation.

```
daily/         = source code        (raw conversation logs)
Claude (LLM)   = compiler           (extracts and organizes)
knowledge/     = executable         (queryable knowledgebase)
Runbooks/lint  = test suite         (consistency checks)
```

## The four operations

All operations are runbooks Claude executes inline. No Python, no CLI, no separate API.

| Operation | Runbook | Trigger |
|---|---|---|
| **Flush** — capture conversation → `daily/` | `Runbooks/flush.md` | "flush memory" / scheduled |
| **Compile** — `daily/` → `knowledge/` | `Runbooks/compile.md` | "compile" / scheduled (daily 6 PM) |
| **Query** — index-guided answer | `Runbooks/query.md` | any KB question |
| **Lint** — 7 health checks | `Runbooks/lint.md` | "lint" / weekly |

## Quick start

1. **Have a conversation** with Claude in this vault about FERDG work — a project, member, decision, lesson, anything.
2. **Say "flush memory"** at the end. Claude appends a session block to `daily/YYYY-MM-DD.md`.
3. **Say "compile"** (or wait for the 6 PM scheduled task). Claude reads the daily log, creates/updates concept articles in `knowledge/concepts/`, refreshes `knowledge/index.md`.
4. **Ask the KB anything later** — "what did we decide about X?" Claude reads `knowledge/index.md`, picks relevant articles, synthesizes an answer with `[[wikilink]]` citations.
5. **Open in Obsidian** — wikilinks, graph view, backlinks all work natively.

## Layout

```
FERDG Second Brain/
├── AGENTS.md              # Schema + technical reference (read this for the full spec)
├── README.md              # You are here
├── FERDG Notes.md         # Root dashboard (open this in Obsidian)
│
├── daily/                 # Per-day session logs (source for the compiler)
├── weekly/                # End-of-week reflections (YYYY-Www.md)
├── knowledge/             # Compiled knowledgebase — LLM-owned
│   ├── index.md
│   ├── log.md
│   ├── concepts/
│   ├── connections/
│   └── qa/
│
├── FERDG/                 # Department operating data
│   ├── FERDG Projects/    #   Per-project folders (e.g. NEO-S v1/)
│   ├── FERDG Members/
│   ├── FERDG Job Orders/
│   ├── FERDG Work Meetings/   # Minutes of the meeting
│   └── FERDG WPR/         #   Formal Work Progress Reports
│
├── standards/             # Research / design / operating standards (renamed from Knowledge Base)
│   ├── ANSYS/
│   ├── Instrumentation/
│   ├── Mechanical Systems/
│   └── Propulsion/
│
├── Miscellaneous/         # External people & organizations
├── Bases/                 # Obsidian Bases (tag-filtered tables)
├── Templates/             # Note templates
├── Attachments/           # PDFs, pasted images
├── Runbooks/              # flush / compile / query / lint
├── reports/               # Lint output
└── Archive/               # Dept-wide tombstones (permission-blocked deletes)
```

FERDG department data, standards, miscellaneous notes, bases, templates, and attachments are curated material. The compiler reads them as context but owns only `knowledge/`.

## Why no RAG

At ~50–500 articles the master index fits in context. The LLM reading a structured index understands intent better than cosine similarity does. Reconsider only above ~2,000 articles. See `AGENTS.md → Why no RAG` for detail.

## Attribution

- Compiler architecture: Andrej Karpathy
- Conversation-source adaptation + hook design: Cole Medin
- Cowork adaptation: this vault
