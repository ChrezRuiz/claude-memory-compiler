---
runbook: clickup_sync
purpose: "Daily incremental delta sync of FERDG ClickUp workspace into knowledge/ClickUp/ mirror. Touches only tasks that changed in last 24h — does NOT regenerate all list files."
inputs: "ClickUp MCP (workspace 90161503255); existing knowledge/ClickUp/ mirror with comment-anchor markup; daily/YYYY-MM-DD.md"
outputs: "Patched knowledge/ClickUp/<Space>/<List>.md files (only touched where tasks changed); appended ClickUp Delta section to daily/YYYY-MM-DD.md; refreshed index.md task counts"
invoke_when:
  - User says "sync clickup", "pull clickup", "update clickup mirror"
  - Daily scheduled task `ferdg-clickup-sync` fires (06:00 local)
companion_runbook: clickup_reconcile.md
---

# Runbook: ClickUp Incremental Sync

## Purpose

Keep the Obsidian mirror of the FERDG ClickUp workspace in lockstep with the live tool **by patching only the tasks that changed** since the last run. Scales O(delta), not O(workspace).

This runbook handles: new tasks, status changes, metadata edits (assignee/due/priority/tags), task moves between lists, and completions. It does **not** detect deletions or do sort-order reconciliation — that is the weekly `clickup_reconcile` runbook's job.

This is **read-only against ClickUp**. Do not create, update, move, delete, or comment on any ClickUp task, list, folder, or space.

## Preconditions

- ClickUp MCP connector authenticated; workspace ID `90161503255` reachable
- `knowledge/ClickUp/` mirror exists with comment-anchor markup (`<!-- clickup-id: ... -->` before each H3, `<!-- clickup-tasks-start -->` / `<!-- clickup-tasks-end -->` delimiters in each list file)
- `knowledge/ClickUp/index.md` exists
- `Runbooks/scripts/clickup/clickup_patch.py` exists and is executable with `python3`
- `daily/` directory exists at vault root

## Workspace reference (frozen 2026-05-04)

```
workspace_id: 90161503255
members:
  100988547 Kent Justine Legada → [[Kent Justine Legada]]
  100987392 Berazon Onuoha     → [[Berazon Onuoha]]
  100987391 Zakk               → [[Zakk Familar]]  (name mismatch — hardcoded)
  61669071  Chrezler MJ Ruiz   → [[Chrezler MJ Ruiz]]
spaces:
  NEO-S Rocket (90166432837)
    lists: 901613738499 Agile Ceremonies | 901613738498 Backlog | 901613738500 Kanban Board
  FERDG Testing Facility (90166455735)  [renamed from "FERDG Facility" 2026-05-04; vault folder path unchanged]
    lists: 901613781775 Agile Ceremonies | 901613781774 Backlog | 901613781776 Kanban Board
  Administrative Tasks (90166458142)
    lists: 901613786437 Agile Ceremonies | 901613786434 Backlog | 901613786439 Kanban Board
```

If hierarchy changed (new space / new list / member removed), **stop** and invoke `clickup_reconcile` instead — it rebuilds the reference block and regenerates all files.

## Steps

### 1. Resolve time window

`TODAY` = date from `<env>` (YYYY-MM-DD).
`NOW_MS` = current epoch-ms.
`SINCE_MS` = `NOW_MS - (26 * 3600 * 1000)` — 26h buffer to tolerate run-time jitter + cron delay.
`SINCE_ISO`, `NOW_ISO` = ISO-8601 strings of each for the daily log header.

### 2. Pull delta per space

For each space (`90166432837`, `90166455735`, `90166458142`):

```
mcp__14cc4894-...__clickup_filter_tasks
  space_id: <space>
  date_updated_gt: <SINCE_MS>
  subtasks: true
  include_closed: true
  page: 0
```

Paginate with `page: 1`, `page: 2` until a page returns `<` 100 tasks or returns empty. Collect every changed task into `delta_tasks` (deduped by id — if a task crosses page boundaries use the last copy).

For each `t` in `delta_tasks`, call `clickup_get_task` with `task_id=t.id` to get the canonical, fully-hydrated record (correct assignees, parent, custom_fields, description, date_closed). Overwrite the filter-response copy with this.

For each `t`, also call `clickup_get_task_comments` with `task_id=t.id`. Keep only comments with `date > SINCE_MS`.

If `delta_tasks` is empty, skip to step 6 — still write the daily log block.

### 3. Classify each delta task

For each task `t`:

1. **Find prior location.** Grep across `knowledge/ClickUp/**/*.md` for the exact string `<!-- clickup-id: {t.id} -->`. There should be at most one hit (patcher invariant).
   - If hit: parse the path to get `prior_list = { space, list }` (folder name is space, filename stem is list name).
   - If no hit: `prior_list = null` (task is new to the mirror).
2. **Resolve current location.** `t.list.id` → lookup via frozen reference block → `current_list = { space, list }`. If `t.list.id` is unknown, stop — hierarchy drifted, escalate to reconcile.
3. **Pick op:**
   - `prior_list is null` → `op = "upsert"` with `prior_list = null` (patcher treats as insert into `current_list`).
   - `prior_list != null` AND `prior_list == current_list` → `op = "upsert"` (in-place patch).
   - `prior_list != null` AND `prior_list != current_list` → `op = "move"` (remove from prior file, insert into current file).

Do **not** emit `delete` or `archive` ops from this runbook — those only come out of the weekly reconcile. A task that was deleted in ClickUp will stop appearing in `filter_tasks`, so it simply won't be in `delta_tasks` — it will linger in the mirror until the weekly full-snapshot pass removes it.

### 4. Build patch descriptor

Write `/tmp/clickup_patch_<TODAY>.json` with schema:

```json
{
  "snapshot_date": "<TODAY>",
  "ops": [
    {
      "op": "upsert",
      "task": { "<full ClickUp task dict>" },
      "current_list": { "space": "NEO-S Rocket", "list": "Kanban Board" },
      "prior_list":   null
    },
    {
      "op": "move",
      "task": { "<full ClickUp task dict>" },
      "current_list": { "space": "NEO-S Rocket", "list": "Kanban Board" },
      "prior_list":   { "space": "NEO-S Rocket", "list": "Backlog" }
    }
  ]
}
```

The `task` field must carry the full object ClickUp returned from `clickup_get_task` — `clickup_patch.py` re-renders the H3 block from it using the canonical `render_block()` formatter.

### 5. Apply the patch

```
python3 "/sessions/intelligent-vibrant-turing/mnt/FERDG Second Brain/Runbooks/scripts/clickup/clickup_patch.py" \
  --patch-file /tmp/clickup_patch_<TODAY>.json \
  --vault-root "/sessions/intelligent-vibrant-turing/mnt/FERDG Second Brain"
```

On first pass use `--dry-run` to print the planned file edits; if plan looks right, re-run without `--dry-run` to apply. For the scheduled task this dry-run phase is skipped — run direct.

The patcher:

- Opens each affected `knowledge/ClickUp/<Space>/<List>.md`.
- Finds the block bounded by `<!-- clickup-id: {id} -->` and the next `<!-- clickup-id:` or `<!-- clickup-tasks-end -->`.
- Replaces it (upsert) or removes it (move-out) or inserts a new block in sort order (upsert-new, move-in).
- Rewrites the frontmatter `task_count` and `snapshot_date`, and the H1 summary line's `**Tasks:** N` and `**Status breakdown:**`.
- Re-sorts the `## Milestones` section if any milestone changed.

No other files are touched.

### 6. Refresh index.md counts

Rewrite `knowledge/ClickUp/index.md`:

- Set frontmatter `snapshot_date: <TODAY>`.
- For each list, re-count tasks by parsing `<!-- clickup-id:` occurrences in the corresponding list file (authoritative — don't trust cached counts).
- Leave Members and Notes sections alone unless membership changed.

### 7. Append delta block to today's daily log

Target: `daily/<TODAY>.md`. Create with frontmatter `{ tags: [daily], date: <TODAY> }` if absent.

Append:

```
## ClickUp Delta — <HH:MM local>

**Window:** <SINCE_ISO> → <NOW_ISO>  |  **Changed tasks:** <len(delta_tasks)>

### New tasks
- `<id>` **<name>** (<space> / <list>) — created <YYYY-MM-DD>, assignee [[<vault>]]

### Status changes
- `<id>` **<name>** (<space> / <list>) — <old_status> → <new_status> (assignee [[<vault>]])

### Completed tasks
- `<id>` **<name>** — closed <YYYY-MM-DD>, assignee [[<vault>]]

### Moved tasks
- `<id>` **<name>** — <prior space/list> → <current space/list>

### Metadata edits
- `<id>` **<name>** — <field>: <old> → <new>

### New comments
- `<id>` **<name>** — <commenter>: "<first 120 chars>…" (<YYYY-MM-DD HH:MM>)
```

Classification rules against the *pre-patch* state of the list file (read before step 5 runs):

- No prior hit → **New tasks**.
- `prior_status != "done"` AND `new_status == "done"` → **Completed tasks**.
- `prior_status != new_status` (and neither transition above) → **Status changes**.
- `prior_list != current_list` → **Moved tasks**.
- Only assignee / priority / due_date / tags / name changed → **Metadata edits** (list which field changed).

A task can appear in more than one subsection (a move that also changed status belongs in both).

Omit any subsection with zero entries. If `delta_tasks` is empty, write the block anyway with `**Changed tasks:** 0` and single line `No activity.` — the daily log should always show the sync ran.

### 8. Record the run

At the end of the ClickUp Delta block, add:

```
**Sync complete:** <NOW_ISO> — <len(delta_tasks)> tasks changed, <n_files_touched> list files patched
```

Then delete `/tmp/clickup_patch_<TODAY>.json` (leave no tmpfiles behind — the JSON can be large).

## Guardrails

- **Read-only.** Never call `clickup_create_*`, `clickup_update_task`, `clickup_delete_task`, `clickup_move_task`, `clickup_add_*`, `clickup_remove_*`, `clickup_send_chat_message`, or `clickup_create_task_comment`. If a user reply mid-run requests a write, stop and surface the request.
- **Do not regenerate list files from scratch in this runbook.** Only `clickup_patch.py` should modify list files. A full regen is the reconcile runbook's job — mixing them breaks the append-only daily log invariant.
- **Assignee mapping is exact.** Zakk (id 100987391) → `[[Zakk Familar]]`, not `[[Zakk]]`. Unknown ids fall back to the ClickUp username with a trailing `_unknown-assignee_` italic note.
- **Timestamps are epoch-ms.** Convert via `datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')` — never trust wall-clock strings from ClickUp.
- **Pagination.** `filter_tasks` page size is ~100. Always loop until a page returns `<` 100 or returns empty.
- **Anchor uniqueness.** Every `<!-- clickup-id: X -->` must appear in exactly one file. If grep returns 2+ hits the mirror is corrupt — stop and escalate to reconcile.

## Failure modes

- **MCP auth fails** → skip the run, write `daily/<TODAY>.md` entry: `## ClickUp Delta — SKIPPED (auth error at <HH:MM>)`. Do **not** run the patcher with an incomplete delta.
- **`clickup_get_task` 404** on a task that appeared in `filter_tasks` (deleted between calls) → drop it from `delta_tasks`, log under a `### Deleted mid-run` subsection of the daily block with `<id>` and the filter-response name. Weekly reconcile will purge it from the mirror.
- **Patcher exits non-zero** → do **not** write the daily log success line. Write `## ClickUp Delta — FAILED (<stderr tail>)` and leave the patch JSON on disk at `/tmp/` for debugging.
- **Workspace hierarchy mismatch** (new space / list / folder with tasks) → stop, escalate to `clickup_reconcile` — that runbook regenerates the reference block, index, and all list files.
- **Anchor collision** (same id found in 2+ files after a prior move bug) → stop. Escalate to `clickup_reconcile` which rebuilds from scratch.
