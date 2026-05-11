"""
Manual flush - capture the current session's conversation into the daily log.

Run this when you want to explicitly mark a conversation topic as "done"
and flush its knowledge into the daily log without ending the session.

Usage:
    uv run python scripts/flush-now.py

Finds the most recent active session transcript, extracts context,
and spawns flush.py in the background (same as the automatic hooks).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
DAILY_DIR = ROOT / "daily"

# Claude Code stores transcripts under projects and sessions
CLAUDE_DIR = Path.home() / ".claude"

MAX_TURNS = 30
MAX_CONTEXT_CHARS = 15_000


def find_latest_transcript() -> Path | None:
    """Find the most recently modified JSONL transcript file (skip subagents)."""
    if not CLAUDE_DIR.exists():
        return None

    candidates: list[tuple[float, Path]] = []
    for jsonl in CLAUDE_DIR.rglob("*.jsonl"):
        # Skip subagent transcripts, plugin fixtures, and non-session files
        parts_str = str(jsonl)
        if "subagents" in parts_str or "fixtures" in parts_str:
            continue
        if jsonl.name == "history.jsonl":
            continue
        candidates.append((jsonl.stat().st_mtime, jsonl))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def extract_conversation_context(transcript_path: Path) -> tuple[str, int]:
    """Read JSONL transcript and extract last ~N conversation turns as markdown."""
    turns: list[str] = []

    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = entry.get("message", {})
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                role = entry.get("role", "")
                content = entry.get("content", "")

            if role not in ("user", "assistant"):
                continue

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)

            if isinstance(content, str) and content.strip():
                label = "User" if role == "user" else "Assistant"
                turns.append(f"**{label}:** {content.strip()}\n")

    recent = turns[-MAX_TURNS:]
    context = "\n".join(recent)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[-MAX_CONTEXT_CHARS:]
        boundary = context.find("\n**")
        if boundary > 0:
            context = context[boundary + 1:]

    return context, len(recent)


def main() -> None:
    transcript = find_latest_transcript()
    if not transcript:
        print("No session transcript found.")
        sys.exit(1)

    print(f"Found transcript: {transcript.name}")

    context, turn_count = extract_conversation_context(transcript)
    if not context.strip():
        print("No conversation content to flush.")
        return

    if turn_count < 1:
        print("Not enough turns to flush.")
        return

    print(f"Extracted {turn_count} turns ({len(context)} chars)")

    # Write context to temp file
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    session_id = f"manual-{timestamp}"
    context_file = SCRIPTS_DIR / f"flush-context-{session_id}.md"
    context_file.write_text(context, encoding="utf-8")

    # Spawn flush.py in background
    flush_script = SCRIPTS_DIR / "flush.py"
    cmd = [
        "uv", "run", "--directory", str(ROOT),
        "python", str(flush_script), str(context_file), session_id,
    ]

    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        print(f"Flush started in background. Check daily/ for results.")
    except Exception as e:
        print(f"Failed to spawn flush: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
