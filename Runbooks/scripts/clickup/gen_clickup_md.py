#!/usr/bin/env python3
"""Generate Obsidian markdown files from cached ClickUp JSON task data."""
import json
import os
from datetime import datetime, timezone
from collections import defaultdict

VAULT_ROOT = "/sessions/intelligent-vibrant-turing/mnt/FERDG Second Brain"
CLICKUP_ROOT = os.path.join(VAULT_ROOT, "knowledge", "ClickUp")
SNAPSHOT_DATE = "2026-04-22"

# Load metadata
with open("/tmp/clickup_data.json") as f:
    meta = json.load(f)

# Map assignee id -> vault wikilink name
ASSIGNEE_MAP = {m["id"]: m["vault"] for m in meta["members"]}

# Load all task JSONs
task_files = ["/tmp/neo_s_p0.json", "/tmp/neo_s_p1.json",
              "/tmp/facility.json", "/tmp/admin.json"]
all_tasks = []
for path in task_files:
    with open(path) as f:
        all_tasks.extend(json.load(f)["tasks"])

# Build list lookup: list_id -> (space_name, list_name)
list_lookup = {}
for sp in meta["spaces"]:
    for lst in sp["lists"]:
        list_lookup[lst["id"]] = (sp["name"], lst["name"])

# Group tasks by (space_name, list_name)
grouped = defaultdict(list)
for t in all_tasks:
    lid = t["list"]["id"]
    if lid in list_lookup:
        key = list_lookup[lid]
    else:
        key = ("Unknown Space", t["list"]["name"])
    grouped[key].append(t)

# Milestone-ish keywords
MILESTONE_KW = ["Launch", "Assembly & Secondary", "Testing & Analysis",
                "Assembly and Modifications", "Fabrication & MR Waiting",
                "Design Review & Deliberation", "MR & Fabrication Release"]

def ms_to_date(ms):
    if not ms:
        return ""
    try:
        ts = int(ms) / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""

def fmt_assignees(assignees):
    if not assignees:
        return "_unassigned_"
    names = []
    for a in assignees:
        vault_name = ASSIGNEE_MAP.get(a["id"], a.get("username", f"id:{a['id']}"))
        names.append(f"[[{vault_name}]]")
    return ", ".join(names)

def fmt_priority(p):
    return p if p else "_none_"

def is_milestone(name):
    return any(kw in name for kw in MILESTONE_KW)

def status_emoji(s):
    s = (s or "").lower()
    if s == "done":
        return "[x]"
    if s == "in progress":
        return "[~]"
    return "[ ]"

def safe_name(s):
    return s.replace("/", "-").replace(":", "-")

# Ensure directories
for sp in meta["spaces"]:
    os.makedirs(os.path.join(CLICKUP_ROOT, safe_name(sp["name"])), exist_ok=True)

# Write per-list markdown
counts_by_list = {}
for (space, lst), tasks in grouped.items():
    # Sort: milestones first, then in-progress, to-do, done; then by due date
    def sort_key(t):
        ms = 0 if is_milestone(t["name"]) else 1
        status_order = {"in progress": 0, "to do": 1, "done": 2}.get(
            (t["status"] or "").lower(), 3)
        due = int(t["due_date"]) if t["due_date"] else 9e15
        return (ms, status_order, due)
    tasks_sorted = sorted(tasks, key=sort_key)

    # Count statuses
    status_counts = defaultdict(int)
    for t in tasks:
        status_counts[(t["status"] or "unknown").lower()] += 1

    out_dir = os.path.join(CLICKUP_ROOT, safe_name(space))
    out_path = os.path.join(out_dir, f"{safe_name(lst)}.md")

    lines = []
    lines.append("---")
    lines.append(f"source: ClickUp")
    lines.append(f"space: \"{space}\"")
    lines.append(f"list: \"{lst}\"")
    lines.append(f"snapshot_date: {SNAPSHOT_DATE}")
    lines.append(f"task_count: {len(tasks)}")
    lines.append("tags: [clickup, backfill]")
    lines.append("---")
    lines.append("")
    lines.append(f"# {space} — {lst}")
    lines.append("")
    lines.append(f"**Snapshot:** {SNAPSHOT_DATE}  |  **Tasks:** {len(tasks)}")
    sc_str = ", ".join(f"{k}: {v}" for k, v in sorted(status_counts.items()))
    lines.append(f"**Status breakdown:** {sc_str}")
    lines.append("")

    # Milestones section
    milestones = [t for t in tasks_sorted if is_milestone(t["name"])]
    if milestones:
        lines.append("## Milestones")
        lines.append("")
        for t in milestones:
            due = ms_to_date(t["due_date"])
            due_str = f" — **due {due}**" if due else ""
            lines.append(f"- {status_emoji(t['status'])} **{t['name']}**{due_str} "
                         f"([{t['id']}]({t['url']}))")
        lines.append("")

    lines.append("## Tasks")
    lines.append("")
    lines.append("<!-- clickup-tasks-start -->")
    lines.append("")
    for t in tasks_sorted:
        if is_milestone(t["name"]):
            header_prefix = "MILESTONE — "
        else:
            header_prefix = ""
        # Comment anchor makes each H3 block findable by ID even if name changes
        lines.append(f"<!-- clickup-id: {t['id']} -->")
        lines.append(f"### {header_prefix}{t['name']}")
        lines.append("")
        lines.append(f"- **ID:** `{t['id']}`")
        lines.append(f"- **Status:** {t['status']}")
        lines.append(f"- **Priority:** {fmt_priority(t['priority'])}")
        lines.append(f"- **Assignees:** {fmt_assignees(t['assignees'])}")
        due = ms_to_date(t["due_date"])
        lines.append(f"- **Due:** {due if due else '_none_'}")
        tags = t.get("tags") or []
        tag_str = ", ".join(tg.get("name", str(tg)) if isinstance(tg, dict) else str(tg)
                            for tg in tags) if tags else "_none_"
        lines.append(f"- **Tags:** {tag_str}")
        lines.append(f"- **URL:** {t['url']}")
        lines.append("")
    lines.append("<!-- clickup-tasks-end -->")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    counts_by_list[(space, lst)] = len(tasks)
    print(f"wrote {out_path} ({len(tasks)} tasks)")

# Write index.md
idx_path = os.path.join(CLICKUP_ROOT, "index.md")
lines = []
lines.append("---")
lines.append("source: ClickUp")
lines.append(f"snapshot_date: {SNAPSHOT_DATE}")
lines.append(f"workspace_id: {meta['workspace_id']}")
lines.append("tags: [clickup, index]")
lines.append("---")
lines.append("")
lines.append("# ClickUp Workspace Mirror")
lines.append("")
lines.append(f"Raw mirror of the FERDG ClickUp workspace `{meta['workspace_id']}`. "
             f"Snapshot: **{SNAPSHOT_DATE}**.")
lines.append("")
lines.append("## Members")
lines.append("")
for m in meta["members"]:
    lines.append(f"- [[{m['vault']}]] — ClickUp handle: *{m['name']}* (id {m['id']})")
lines.append("")
lines.append("## Spaces & Lists")
lines.append("")
total = 0
for sp in meta["spaces"]:
    lines.append(f"### {sp['name']}")
    lines.append("")
    if sp["folders"]:
        fnames = ", ".join(f["name"] for f in sp["folders"])
        lines.append(f"**Folders (doc containers, no active tasks):** {fnames}")
        lines.append("")
    for lst in sp["lists"]:
        key = (sp["name"], lst["name"])
        count = counts_by_list.get(key, 0)
        total += count
        link = f"[[{safe_name(sp['name'])}/{safe_name(lst['name'])}|{lst['name']}]]"
        lines.append(f"- {link} — {count} tasks")
    lines.append("")
lines.append(f"**Workspace task total:** {total}")
lines.append("")
lines.append("## Notes")
lines.append("")
lines.append("- Source of truth is ClickUp. This mirror is read-only backfill.")
lines.append("- Daily delta sync appends changes to `daily/` activity log "
             "and updates list files in place.")
lines.append("- Task IDs map directly to ClickUp URLs "
             "(`https://app.clickup.com/t/<id>`).")

with open(idx_path, "w") as f:
    f.write("\n".join(lines))
print(f"wrote {idx_path}")
print(f"TOTAL tasks written: {total}")
