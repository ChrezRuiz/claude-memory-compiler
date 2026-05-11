---
runbook: lint
purpose: "Health checks across the knowledgebase — structural + LLM-judged"
inputs: "Entire knowledge/ tree + daily/ tree + log.md"
outputs: "reports/lint-YYYY-MM-DD.md with severity-tagged findings"
invoke_when:
  - User says "lint", "lint the kb", "check the kb", "audit the kb"
  - After a large compile (3+ articles touched)
  - Weekly cadence (consider a separate scheduled task)
---

# Runbook: Lint

## Purpose

Catch rot before it compounds. Seven checks — six deterministic structural, one LLM-judged.

## Steps

### 1. Initialize the report

Create `reports/lint-YYYY-MM-DD.md`:

```markdown
# Lint Report — YYYY-MM-DD

Run by: Claude (Cowork)
Vault: FERDG Second Brain
Articles scanned: <N concepts + M connections + K qa>
Daily logs scanned: <P>

---
```

### 2. Run the seven checks

For each finding, append to the report under the appropriate section with severity:
- `error` — must fix (broken link, contradiction)
- `warning` — should fix (orphan, stale, missing backlink)
- `suggestion` — nice to fix (sparse article)

#### Check 1 — Broken links (error)

```
Glob knowledge/**/*.md
For each file: Grep -E "\[\[[^\]]+\]\]" → list all wikilinks
For each wikilink [[path/to/article]]:
  verify knowledge/path/to/article.md exists
  if not → record (file, line, target, "broken link")
```

#### Check 2 — Orphan pages (warning)

Build inbound-link map: for each article A, count how many other articles contain `[[A]]`. Articles with 0 inbound links and not in `index.md`'s top section are orphans.

QA articles are exempt (they're terminal).

#### Check 3 — Orphan sources (warning)

```
Glob daily/*.md → set of daily slugs
Grep "compile | Daily Log" knowledge/log.md → set of compiled slugs
diff → daily logs not yet compiled
```

#### Check 4 — Stale articles (warning)

For each concept/connection article:
- Read `sources` from frontmatter
- For each source `daily/YYYY-MM-DD.md`, get its `mtime`
- Read `updated` from frontmatter
- If any source's `mtime` is newer than `updated` → stale

#### Check 5 — Missing backlinks (warning)

For each article A linking to B (`[[B]]`), check that B contains `[[A]]` somewhere. If not → missing backlink.

Exempt: links from `qa/` articles (Q&A is one-way).

#### Check 6 — Sparse articles (suggestion)

For each article: word count (excluding frontmatter and headings). If < 200 words → suggestion to expand.

#### Check 7 — Contradictions (LLM-judged)

This is the only non-deterministic check. Group articles by `tags:` overlap. Within each group of related articles, scan for conflicting claims:
- Different decisions on the same question
- Contradictory facts (e.g., "noise floor is 5 mV" vs. "noise floor is 12 mV" without a date/condition qualifier)
- Mutually exclusive recommendations

Record each as `contradiction` severity `error` with `between [[A]] and [[B]]` plus the conflicting passages quoted.

If the user invoked with `--structural-only`, skip this check.

### 3. Summary at top of report

After all checks, prepend a summary table:

```markdown
## Summary

| Severity | Count |
|---|---|
| error | <n> |
| warning | <n> |
| suggestion | <n> |

## Findings

[the per-check sections]
```

### 4. Append to log.md

```markdown
## [YYYY-MM-DDTHH:MM:SS] lint | reports/lint-YYYY-MM-DD.md
- error: <n>, warning: <n>, suggestion: <n>
```

### 5. Surface to user

One-line summary: `Lint complete — N errors, M warnings, K suggestions. See reports/lint-YYYY-MM-DD.md`.

If errors > 0, name the top 3 inline so the user knows what to fix first.

## Auto-fix policy

This runbook is **read-only by default**. Do not auto-fix structural issues without explicit user approval — broken links may be intentional placeholders, orphans may be intentional indexes. Exception: if a sparse article exists and a relevant new daily log is available, suggest a recompile rather than silently expanding it.

## Cadence recommendation

Weekly. Add a second scheduled task if desired:

```
mcp__scheduled-tasks__create_scheduled_task(
  name="Weekly KB lint",
  schedule="0 9 * * 1",   # Mondays 9 AM
  prompt="Run Runbooks/lint.md against the FERDG Second Brain vault."
)
```
