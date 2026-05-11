---
runbook: compile
purpose: "Transform daily/ logs into structured knowledge/ articles + maintain index"
inputs: "Un-compiled or changed daily/*.md files; existing knowledge/ state"
outputs: "Created/updated articles in knowledge/concepts/, knowledge/connections/; updated index.md and log.md"
invoke_when:
  - User says "compile", "compile the kb", "build the kb", "process today's log"
  - Daily scheduled task fires (after flush completes)
---

# Runbook: Compile

## Purpose

Promote raw daily-log content into atomic concept articles, cross-cutting connection articles, and an updated master index. Equivalent to `compile.py` in upstream — but executed by Claude inline using `Read`, `Write`, `Edit`, `Glob`, `Grep`.

## Preconditions

- `AGENTS.md` schema is loaded (read it once at the start of this runbook to refresh the article format spec)
- `knowledge/index.md` and `knowledge/log.md` exist (initialize if missing)

## Steps

### 1. Determine which daily logs to compile

```
Glob: daily/*.md
```

For each log, check `knowledge/log.md` for a prior compile entry:

```
Grep "compile | Daily Log YYYY-MM-DD" knowledge/log.md
```

A log needs (re)compilation if:
- It has no prior compile entry, OR
- Its file `mtime` is newer than the timestamp of the latest matching compile entry

If the user passed a specific file (e.g. "compile daily/2026-04-22.md"), use only that.

If no logs need compilation, write `- (Nothing to compile)` and exit.

### 2. For each log to compile

#### 2a. Read the schema

```
Read AGENTS.md          (sections: "Article Formats", "Conventions", "Core Operations")
```

#### 2b. Read current KB state

```
Read knowledge/index.md
Glob knowledge/concepts/*.md      → list of existing concept slugs
Glob knowledge/connections/*.md   → list of existing connection slugs
```

#### 2c. Read the daily log in full

```
Read daily/YYYY-MM-DD.md
```

#### 2d. Extract and route

Walk the log. For every distinct piece of knowledge, decide:

| What it is | Where it goes |
|---|---|
| Atomic fact, pattern, lesson, decision rationale | `concepts/<slug>.md` — create or update |
| Non-obvious relationship between 2+ existing concepts | `connections/<slug>.md` — create |
| Already covered by an existing article | UPDATE that article — append to `Sources`, refresh `updated`, expand `Details` only if the log adds genuinely new info |

Slug rule: lowercase, hyphenated, descriptive (`esp32-adc-noise`, not `esp32`).

A typical daily log produces 3–10 article writes. Prefer updating over duplicating.

#### 2e. Article frontmatter — required fields

Every concept or connection article must have valid YAML frontmatter:

```yaml
---
title: "..."
sources:
  - "daily/YYYY-MM-DD.md"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Plus `tags:`, `aliases:`, `connects:` (for connections), as appropriate.

When updating an existing article: append the new daily log to `sources`, set `updated` to today's date, leave `created` unchanged.

#### 2f. Update index.md

Append a row (or update the existing row) for every article touched:

```markdown
| [[concepts/<slug>]] | <one-line summary> | daily/<all sources> | YYYY-MM-DD |
```

Keep rows sorted by `Updated` descending so the most recent activity is at the top.

#### 2g. Append to log.md

```markdown
## [YYYY-MM-DDTHH:MM:SS] compile | Daily Log YYYY-MM-DD
- Source: daily/YYYY-MM-DD.md
- Articles created: [[concepts/...]], [[concepts/...]]
- Articles updated: [[concepts/...]]
- Connections: [[connections/...]] (if any)
```

### 3. Confirm to user

One-line summary per compiled log: `Compiled daily/YYYY-MM-DD.md → N created, M updated.`

## Quality bar

- **No empty stubs.** If a topic only has 1–2 sentences of substance, fold it into the most relevant existing concept rather than creating a sparse new article. Lint check #6 will flag stubs anyway.
- **Wikilinks must resolve.** Before writing a `[[concepts/foo]]` link, verify `concepts/foo.md` exists or is being created in the same compile pass.
- **Backlinks.** When concept A references concept B, B's `Related Concepts` section should also reference A. The compile pass is the right time to enforce this.

## Failure modes

- **Schema drift.** If an existing article has no frontmatter or wrong fields, fix it during this pass (don't leave broken articles in place).
- **Conflicting claims.** If today's log contradicts an existing article, flag in `log.md` under a `## ⚠ Contradiction` block but do NOT silently overwrite. Lint check #7 catches these for human review.

## Next step

Suggest: "Want me to lint? (`Runbooks/lint.md`)" — recommended after every compile that touched 3+ articles.
