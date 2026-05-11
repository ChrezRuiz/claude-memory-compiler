---
runbook: clickup_reconcile
purpose: "Weekly full-snapshot reconciliation of FERDG ClickUp mirror. Detects deletions, archives closed-and-aged tasks, repairs sort drift, and rebuilds reference block if hierarchy changed."
inputs: "ClickUp MCP (workspace 90161503255); existing knowledge/ClickUp/ mirror"
outputs: "Regenerated knowledge/ClickUp/<Space>/<List>.md files; archived tasks appended to <List>-archive.md; rewritten index.md; reconcile entry in daily/YYYY-MM-DD.md"
invoke_when:
  - User says "reconcile clickup", "full refresh clickup", "rebuild clickup mirror"
  - Weekly scheduled task `ferdg-clickup-reconcile` fires (Sunday 05:30 local)
  - Incremental `clickup_sync` escalates (hierarchy drift, anchor collision, etc.)
companion_runbook: clickup_sync.md
---

# Runbook: ClickUp Full Reconciliation

## Purpose

Catch everything the daily incremental sync cannot:

1. **Deletions.** `clickup_filter_tasks` with `date_updated_gt` never returns tasks that were deleted — they silently linger in the mirror. Full snapshot finds them.
2. **Archival.** Tasks with `status=done` **and** `date_closed` older than 90 days are moved out of the active list file into a sibling `<List>-archive.md` so active files stay lean.
3. **Sort drift.** After many in-place patches, milestone ordering and in-progress-first ordering can drift. Full regen restores canonical sort.
4. **Hierarchy drift.** New space, list, folder, or member → rebuild reference block + index.
5. **Anchor collisions / mirror corruption.** Rewriting list files from scratch erases any leftover duplicates.

This runbook **overwrites** list files. It is destructive to derived state (the mirror) but **read-only against ClickUp**.

## Preconditions

- ClickUp MCP connector authenticated; workspace ID `90161503255` reachable
- `knowledge/ClickUp/` mirror exists (any state — runbook will normalize it)
- `Runbooks/scripts/clickup/gen_clickup_md.py` exists
- `daily/` directory exists at vault root

## Steps

### 1. Resolve hierarchy

Call `clickup_get_workspace_hierarchy` with `workspace_id=90161503255`. Compare spaces, lists, folders, and member list to the reference block in `clickup_sync.md`.

If anything changed:

- Update the reference block in `clickup_sync.md` (edit in place).
- Update the Members section and Spaces/Lists scaffold in `knowledge/ClickUp/index.md`.
- Log the change under a `### Hierarchy changes` subsection of today's daily reconcile block.

Refresh the in-memory `ASSIGNEE_MAP` from current member data. Note: Zakk's vault name is pinned — do NOT let a ClickUp rename of `Zakk` overwrite `[[Zakk Familar]]` unless the member id (`100987391`) changed.

### 2. Pull full snapshot

For each space (`90166432837`, `90166455735`, `90166458142`):

```
mcp__14cc4894-...__clickup_filter_tasks
  space_id: <space>
  subtasks: true
  include_closed: true
  page: 0
```

Paginate until a page returns `<` 100 or returns empty. Collect into `all_tasks` (deduped by id).

Call `clickup_get_task` only for tasks whose filter-response payload is missing fields the render expects (assignees array, date_closed, parent). The filter response is usually sufficient — only hydrate on-demand.

### 3. Detect deletions

Build `mirror_ids` = set of every `<!-- clickup-id: X -->` occurrence in `knowledge/ClickUp/**/*.md` (excluding `-archive.md` files).
Build `live_ids` = set of ids in `all_tasks`.

`deleted_ids = mirror_ids - live_ids`

These are tasks that exist in the mirror but no longer in ClickUp — remove them. Record each under a `### Deleted tasks` subsection of the daily reconcile block with id, last-known name (read from the block about to be removed), and the list file it lived in.

### 4. Segregate for archival

For each task `t` in `all_tasks`:

- If `t.status.status == "done"` AND `t.date_closed` is set AND `(NOW_MS - int(t.date_closed)) > 90 * 86400 * 1000` → add to `archive_tasks[(space, list)]`.
- Else → add to `active_tasks[(space, list)]`.

90 days is a knob — adjust here if the vault starts feeling stale.

### 5. Regenerate active list files

For each `(space, list)` key in `active_tasks`, invoke the canonical renderer:

```
python3 "/sessions/intelligent-vibrant-turing/mnt/FERDG Second Brain/Runbooks/scripts/clickup/gen_clickup_md.py"
```

Or — if calling the script directly is inconvenient in-session — inline the same logic: write `knowledge/ClickUp/<space>/<list>.md` with:

- Frontmatter (`source`, `space`, `list`, `snapshot_date`, `task_count`, `tags: [clickup, backfill]`)
- H1 `<space> — <list>`
- Summary line + status breakdown
- `## Milestones` section (milestone keywords: `Launch`, `Assembly & Secondary`, `Testing & Analysis`, `Assembly and Modifications`, `Fabrication & MR Waiting`, `Design Review & Deliberation`, `MR & Fabrication Release`)
- `## Tasks` section wrapped in `<!-- clickup-tasks-start -->` / `<!-- clickup-tasks-end -->`, each task preceded by `<!-- clickup-id: {id} -->` anchor.

Sort: milestones first, then `in progress` → `to do` → `done`, ties broken by due_date ascending.

**Overwrite in place.** Do not preserve prior body content — derived state.

### 6. Append archived tasks to archive files

For each `(space, list)` key in `archive_tasks`, open
`knowledge/ClickUp/<space>/<list>-archive.md`. Create with this frontmatter if absent:

```
---
source: ClickUp
space: "<space>"
list: "<list>"
archive_of: "<list>.md"
tags: [clickup, archive]
---

# <space> — <list> (archive)

Tasks with `status=done` and `date_closed` older than 90 days. Append-only.
```

For each task in `archive_tasks[(space, list)]`, append a block in the same H3 format as active files (including `<!-- clickup-id: ... -->` anchor) **only if the id is not already present**. Grep first to avoid duplicates across reconcile runs.

Do **not** sort archive files — they are append-only chronological by archive date. Add a leading `<!-- archived: YYYY-MM-DD -->` comment on the line above the anchor so future reconciles can prune by archive date if ever needed.

### 7. Rewrite index.md

Regenerate `knowledge/ClickUp/index.md` from scratch:

- Frontmatter: `source: ClickUp`, `snapshot_date: <TODAY>`, `workspace_id: 90161503255`, `tags: [clickup, index]`
- Members section (from current workspace members)
- Spaces & Lists section — count `<!-- clickup-id:` occurrences in each list file after regen (not in archive files)
- Notes section — unchanged prose about read-only source of truth

### 8. Append reconcile block to today's daily log

Target: `daily/<TODAY>.md`. Create if absent.

Append:

```
## ClickUp Reconcile — <HH:MM local>

**Snapshot:** <NOW_ISO>  |  **Workspace tasks live:** <len(all_tasks)>  |  **Active in mirror:** <sum active>  |  **Archived this run:** <sum archive>  |  **Deleted:** <len(deleted_ids)>

### Hierarchy changes
- <only if step 1 found any>

### Deleted tasks
- `<id>` **<name>** — last seen in <space> / <list>

### Archived tasks (status=done, closed > 90 days)
- `<id>` **<name>** — closed <YYYY-MM-DD>, moved to <list>-archive.md

### List file regeneration
- <space> / <list>: <n_active> active tasks (prior: <prior_n>)
...

**Reconcile complete:** <NOW_ISO>
```

Omit any subsection with zero entries.

## Guardrails

- **Read-only against ClickUp.** Same rules as `clickup_sync.md` — no write tools, ever.
- **Archive files are append-only.** Never overwrite `<List>-archive.md` wholesale. Use grep-then-append to avoid duplicates.
- **Do not archive unless BOTH conditions hold:** `status == "done"` and `date_closed` is set and age > 90 days. A task with `status=done` but missing `date_closed` (shouldn't happen, but possible for legacy data) stays active.
- **Preserve Zakk's pinned mapping.** `100987391` → `[[Zakk Familar]]` regardless of what ClickUp reports as the username.
- **Backlinks from project notes in `FERDG/FERDG Projects/*.md`** point at list files (not archive files). Do not break those paths — regen keeps filenames stable.
- **Large runs are fine.** This runbook is expected to take longer than the daily sync. Budget ~2 min for 200-300 tasks.

## Failure modes

- **MCP auth fails** → skip run, append `## ClickUp Reconcile — SKIPPED (auth error at <HH:MM>)` to daily log. Leave mirror untouched.
- **Snapshot incomplete** (one space fails after another succeeds) → abort the write phase. Do not mix fresh one-space data with stale two-space data. Retry or surface error.
- **File write fails mid-regen** → log the partial state under `### PARTIAL REGEN` with list of files touched. Next run fully restores from fresh snapshot (idempotent).
- **Archive dupe check grep fails** → err on the side of not appending; log under `### Skipped archive (dupe-check error)`.
