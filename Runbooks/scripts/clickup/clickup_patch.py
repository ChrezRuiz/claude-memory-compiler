#!/usr/bin/env python3
"""Incremental patcher for the FERDG ClickUp vault mirror.

Reads a patch descriptor (JSON on stdin or --patch-file) and applies the
listed operations to the list markdown files under knowledge/ClickUp/.
Only files with at least one op are touched.

Patch descriptor schema:

{
  "snapshot_date": "2026-04-23",
  "run_ts": "2026-04-23T06:03:17-08:00",
  "ops": [
    {"op": "upsert", "task": <full ClickUp task dict>,
     "prior_list": {"space": "NEO-S Rocket", "list": "Kanban Board"} | null,
     "classification": "new" | "update" | "completed" | "reopened"},
    {"op": "move",   "task": <full ClickUp task dict>,
     "prior_list": {"space": "...", "list": "..."}},
    {"op": "delete", "task_id": "86d24bykx",
     "prior_list": {"space": "...", "list": "..."}},
    {"op": "archive", "task": <full ClickUp task dict>,
     "prior_list": {"space": "...", "list": "..."}}
  ]
}

`upsert` covers new + update + completed + reopened — the patcher reads the
task's current list from `task.list.id` and rewrites / inserts the H3 block
there. `move` removes from `prior_list` and upserts into current list.
`archive` removes from the active list file and appends to `<List>-archive.md`.
`delete` removes from the mirror entirely (reconciler only).

Exit codes:
  0  success (ops applied or nothing to do)
  2  patch descriptor invalid
  3  unresolved list file (unknown space/list id)
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

# ---------- configuration ----------

VAULT_ROOT_DEFAULT = "/sessions/intelligent-vibrant-turing/mnt/FERDG Second Brain"
CLICKUP_SUBDIR = os.path.join("knowledge", "ClickUp")

ASSIGNEE_MAP = {
    100988547: "Kent Justine Legada",
    100987392: "Berazon Onuoha",
    100987391: "Zakk Familar",
    61669071:  "Chrezler MJ Ruiz",
}

MILESTONE_KW = [
    "Launch", "Assembly & Secondary", "Testing & Analysis",
    "Assembly and Modifications", "Fabrication & MR Waiting",
    "Design Review & Deliberation", "MR & Fabrication Release",
]

STATUS_ORDER = {"in progress": 0, "to do": 1, "done": 2}

TASKS_START = "<!-- clickup-tasks-start -->"
TASKS_END = "<!-- clickup-tasks-end -->"

# ---------- helpers ----------

def safe_name(s: str) -> str:
    return s.replace("/", "-").replace(":", "-")

def ms_to_date(ms) -> str:
    if not ms:
        return ""
    try:
        ts = int(ms) / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""

def fmt_priority(p):
    if not p:
        return "_none_"
    if isinstance(p, dict):
        return p.get("priority") or p.get("name") or "_none_"
    return str(p)

def fmt_assignees(assignees):
    if not assignees:
        return "_unassigned_"
    names = []
    for a in assignees:
        aid = a.get("id") if isinstance(a, dict) else a
        try:
            aid = int(aid)
        except (TypeError, ValueError):
            pass
        vault = ASSIGNEE_MAP.get(aid)
        if vault:
            names.append(f"[[{vault}]]")
        else:
            uname = a.get("username") if isinstance(a, dict) else str(a)
            names.append(f"{uname} _unknown-assignee_")
    return ", ".join(names)

def fmt_tags(tags):
    if not tags:
        return "_none_"
    out = []
    for t in tags:
        if isinstance(t, dict):
            out.append(t.get("name", ""))
        else:
            out.append(str(t))
    return ", ".join(x for x in out if x) or "_none_"

def is_milestone(name: str) -> bool:
    return any(kw in name for kw in MILESTONE_KW)

def render_block(task: dict) -> list[str]:
    """Render a task's H3 block with comment anchor."""
    prefix = "MILESTONE — " if is_milestone(task["name"]) else ""
    due = ms_to_date(task.get("due_date"))
    lines = [
        f"<!-- clickup-id: {task['id']} -->",
        f"### {prefix}{task['name']}",
        "",
        f"- **ID:** `{task['id']}`",
        f"- **Status:** {task.get('status', '')}",
        f"- **Priority:** {fmt_priority(task.get('priority'))}",
        f"- **Assignees:** {fmt_assignees(task.get('assignees', []))}",
        f"- **Due:** {due if due else '_none_'}",
        f"- **Tags:** {fmt_tags(task.get('tags'))}",
        f"- **URL:** {task.get('url', '')}",
        "",
    ]
    return lines

def task_sort_key(task: dict):
    ms = 0 if is_milestone(task["name"]) else 1
    status = (task.get("status") or "").lower()
    so = STATUS_ORDER.get(status, 3)
    due = task.get("due_date")
    try:
        due_i = int(due) if due else 9 * 10**15
    except (TypeError, ValueError):
        due_i = 9 * 10**15
    return (ms, so, due_i, task.get("name", ""))

# ---------- file parsing ----------

BLOCK_RE = re.compile(
    r"<!-- clickup-id: (?P<id>[a-zA-Z0-9_-]+) -->\n"
    r"### (?P<header>.*?)\n\n"
    r"- \*\*ID:\*\* `(?P=id)`\n"
    r"- \*\*Status:\*\* (?P<status>.*?)\n"
    r"- \*\*Priority:\*\* (?P<priority>.*?)\n"
    r"- \*\*Assignees:\*\* (?P<assignees>.*?)\n"
    r"- \*\*Due:\*\* (?P<due>.*?)\n"
    r"- \*\*Tags:\*\* (?P<tags>.*?)\n"
    r"- \*\*URL:\*\* (?P<url>.*?)\n",
    re.MULTILINE,
)

def load_file_tasks(path: str) -> dict:
    """Return {task_id: raw_block_text} by scanning comment anchors."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    tasks = {}
    for m in BLOCK_RE.finditer(text):
        tasks[m.group("id")] = {
            "raw": m.group(0),
            "header": m.group("header"),
            "status": m.group("status"),
            "due": m.group("due"),
        }
    return tasks

def frontmatter_count(path: str) -> int | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        text = f.read()
    m = re.search(r"^task_count:\s*(\d+)", text, re.MULTILINE)
    return int(m.group(1)) if m else None

# ---------- file mutation ----------

def _write_list_file(path: str, space: str, lst: str, tasks_by_id: dict,
                     snapshot_date: str):
    """Rewrite the list file from the given tasks dict (id -> full task)."""
    ordered = sorted(tasks_by_id.values(), key=task_sort_key)
    status_counts = defaultdict(int)
    for t in ordered:
        status_counts[(t.get("status") or "unknown").lower()] += 1

    lines = [
        "---",
        "source: ClickUp",
        f'space: "{space}"',
        f'list: "{lst}"',
        f"snapshot_date: {snapshot_date}",
        f"task_count: {len(ordered)}",
        "tags: [clickup, backfill]",
        "---",
        "",
        f"# {space} — {lst}",
        "",
        f"**Snapshot:** {snapshot_date}  |  **Tasks:** {len(ordered)}",
        f"**Status breakdown:** {', '.join(f'{k}: {v}' for k, v in sorted(status_counts.items()))}",
        "",
    ]
    milestones = [t for t in ordered if is_milestone(t["name"])]
    if milestones:
        lines.append("## Milestones")
        lines.append("")
        for t in milestones:
            due = ms_to_date(t.get("due_date"))
            due_str = f" — **due {due}**" if due else ""
            stat = (t.get("status") or "").lower()
            mark = "[x]" if stat == "done" else ("[~]" if stat == "in progress" else "[ ]")
            lines.append(f"- {mark} **{t['name']}**{due_str} "
                         f"([{t['id']}]({t.get('url','')}))")
        lines.append("")
    lines.append("## Tasks")
    lines.append("")
    lines.append(TASKS_START)
    lines.append("")
    for t in ordered:
        lines.extend(render_block(t))
    lines.append(TASKS_END)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))

def _load_existing_full_tasks(path: str) -> dict:
    """Rebuild best-effort full task dicts from a list file, for round-tripping.

    Returns {id: task_dict} where task_dict has the fields needed by
    render_block and task_sort_key. We cannot recover the original assignee
    ID list (we only stored wikilinks), so assignees are emitted back as-is
    by preserving the raw block when possible. Callers that pass in fresh
    task dicts from ClickUp overwrite these entries.
    """
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    result = {}
    for m in BLOCK_RE.finditer(text):
        tid = m.group("id")
        # Extract due date ms from the YYYY-MM-DD text if possible
        due_str = m.group("due").strip()
        due_ms = None
        if re.match(r"^\d{4}-\d{2}-\d{2}$", due_str):
            dt = datetime.strptime(due_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            due_ms = int(dt.timestamp() * 1000)
        # Reconstruct assignees placeholder list from wikilinks
        wl = re.findall(r"\[\[([^\]]+)\]\]", m.group("assignees"))
        name_to_id = {v: k for k, v in ASSIGNEE_MAP.items()}
        assignees = [{"id": name_to_id[n], "username": n}
                     for n in wl if n in name_to_id]
        # Strip MILESTONE prefix from header
        name = re.sub(r"^MILESTONE — ", "", m.group("header"))
        # Tags
        tag_txt = m.group("tags").strip()
        tags = [] if tag_txt == "_none_" else [
            {"name": t.strip()} for t in tag_txt.split(",") if t.strip()]
        # Priority
        pri_txt = m.group("priority").strip()
        priority = None if pri_txt == "_none_" else pri_txt
        result[tid] = {
            "id": tid,
            "name": name,
            "status": m.group("status").strip(),
            "priority": priority,
            "assignees": assignees,
            "due_date": due_ms,
            "tags": tags,
            "url": m.group("url").strip(),
        }
    return result

def _list_path(vault_root: str, space: str, lst: str) -> str:
    return os.path.join(vault_root, CLICKUP_SUBDIR,
                        safe_name(space), f"{safe_name(lst)}.md")

def _archive_path(vault_root: str, space: str, lst: str) -> str:
    return os.path.join(vault_root, CLICKUP_SUBDIR,
                        safe_name(space), f"{safe_name(lst)}-archive.md")

# ---------- op application ----------

def apply_patch(patch: dict, vault_root: str) -> dict:
    snapshot = patch.get("snapshot_date") or datetime.now(
        tz=timezone.utc).strftime("%Y-%m-%d")

    # Group ops by target list file
    affected_lists = defaultdict(list)  # (space, list) -> [op, ...]
    for op in patch.get("ops", []):
        kind = op["op"]
        if kind in ("upsert",):
            task = op["task"]
            # Must have list.id resolved to names — prompt that the runbook
            # passes `op["current_list"] = {"space": ..., "list": ...}` so
            # we don't need to re-resolve.
            cl = op["current_list"]
            affected_lists[(cl["space"], cl["list"])].append(op)
            # If moved from prior list, also flag the prior for removal
            prior = op.get("prior_list")
            if prior and prior != cl:
                affected_lists[(prior["space"], prior["list"])].append(
                    {"op": "remove", "task_id": task["id"]})
        elif kind == "move":
            task = op["task"]
            prior = op["prior_list"]
            cl = op["current_list"]
            affected_lists[(prior["space"], prior["list"])].append(
                {"op": "remove", "task_id": task["id"]})
            affected_lists[(cl["space"], cl["list"])].append(
                {"op": "upsert", "task": task, "current_list": cl})
        elif kind == "delete":
            prior = op["prior_list"]
            affected_lists[(prior["space"], prior["list"])].append(
                {"op": "remove", "task_id": op["task_id"]})
        elif kind == "archive":
            task = op["task"]
            prior = op["prior_list"]
            affected_lists[(prior["space"], prior["list"])].append(
                {"op": "remove", "task_id": task["id"]})
            affected_lists[(prior["space"], prior["list"], "archive")].append(
                {"op": "archive", "task": task})
        else:
            raise ValueError(f"unknown op: {kind}")

    report = {"files_written": [], "tasks_added": 0, "tasks_removed": 0,
              "tasks_updated": 0, "tasks_archived": 0}

    # Apply per-file
    for key, ops in affected_lists.items():
        is_archive_bucket = len(key) == 3 and key[2] == "archive"
        space, lst = key[0], key[1]
        path = (_archive_path(vault_root, space, lst)
                if is_archive_bucket else _list_path(vault_root, space, lst))

        if is_archive_bucket:
            # Append archive blocks to <List>-archive.md
            _append_archive(path, space, lst, [o["task"] for o in ops], snapshot)
            report["tasks_archived"] += len(ops)
            report["files_written"].append(path)
            continue

        tasks = _load_existing_full_tasks(path)
        before = set(tasks.keys())
        for o in ops:
            if o["op"] == "remove":
                tasks.pop(o["task_id"], None)
            elif o["op"] == "upsert":
                t = o["task"]
                tasks[t["id"]] = t

        # Count deltas
        after = set(tasks.keys())
        added = after - before
        removed = before - after
        updated = (after & before)
        report["tasks_added"] += len(added)
        report["tasks_removed"] += len(removed)
        # rough: count 'updated' as in-both and any upsert op
        upsert_ids = {o["task"]["id"] for o in ops if o["op"] == "upsert"}
        report["tasks_updated"] += len(upsert_ids & updated)

        _write_list_file(path, space, lst, tasks, snapshot)
        report["files_written"].append(path)

    return report

def _append_archive(path: str, space: str, lst: str, tasks: list, snapshot: str):
    if not os.path.exists(path):
        header = [
            "---",
            "source: ClickUp",
            f'space: "{space}"',
            f'list: "{lst}"',
            "archive: true",
            "tags: [clickup, archive]",
            "---",
            "",
            f"# {space} — {lst} (archived)",
            "",
            "Tasks closed ≥ 90 days ago, moved here to keep the live list lean. "
            "Append-only. Each task retains its original H3 + comment anchor.",
            "",
        ]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("\n".join(header))
    with open(path, "a") as f:
        for t in tasks:
            closed_ms = t.get("date_closed")
            closed = ms_to_date(closed_ms) if closed_ms else "_unknown_"
            f.write(f"\n> **Archived on {snapshot}** — closed {closed}\n")
            f.write("\n")
            f.write("\n".join(render_block(t)))
            f.write("\n")

# ---------- cli ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch-file", help="path to patch JSON; default: stdin")
    ap.add_argument("--vault-root", default=VAULT_ROOT_DEFAULT)
    ap.add_argument("--dry-run", action="store_true",
                    help="parse + print plan without writing")
    args = ap.parse_args()

    if args.patch_file:
        with open(args.patch_file) as f:
            patch = json.load(f)
    else:
        patch = json.load(sys.stdin)

    if not isinstance(patch, dict) or "ops" not in patch:
        print("patch descriptor missing 'ops' array", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        print(json.dumps({"planned_ops": len(patch["ops"]),
                          "snapshot_date": patch.get("snapshot_date")}, indent=2))
        return

    report = apply_patch(patch, args.vault_root)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
