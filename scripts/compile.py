"""
Compile daily conversation logs into structured knowledge articles.

This is the "LLM compiler" - it reads daily logs (source code) and produces
organized knowledge articles (the executable).

Usage:
    uv run python compile.py                    # compile new/changed logs only
    uv run python compile.py --all              # force recompile everything
    uv run python compile.py --file daily/2026-04-01.md  # compile a specific log
    uv run python compile.py --dry-run          # show what would be compiled
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from config import AGENTS_FILE, CONCEPTS_DIR, CONNECTIONS_DIR, DAILY_DIR, KNOWLEDGE_DIR, now_iso
from utils import (
    file_hash,
    list_raw_files,
    list_wiki_articles,
    load_state,
    save_state,
)

# ── Paths for the LLM to use ──────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent


async def compile_daily_log(log_path: Path, state: dict) -> float:
    """Compile a single daily log into knowledge articles.

    Returns the API cost of the compilation.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    log_content = log_path.read_text(encoding="utf-8")
    timestamp = now_iso()

    static_context = f"""You are a knowledge compiler. Read a daily conversation log
and extract knowledge into structured wiki articles.

## Reference files (Read these first, before writing anything)

- **Schema:** `{AGENTS_FILE}` — article format spec (YAML frontmatter, sections, naming)
- **Wiki catalog:** `{KNOWLEDGE_DIR / 'index.md'}` — list of all existing articles, summaries, sources
- **Existing articles:** under `{CONCEPTS_DIR}` and `{CONNECTIONS_DIR}`.
  Use Glob to enumerate, Read individual files when updating.

## Workflow

1. Read AGENTS.md and knowledge/index.md before writing anything.
2. Extract 3–7 distinct concepts from the daily log worth their own article.
3. For each concept:
   - **If a matching article already exists** (per the index) → Read it, then Edit
     to merge new information; add the daily log filename to the `sources:` frontmatter
     and bump `updated:`.
   - **If new** → Write a new file in `{CONCEPTS_DIR}` following the AGENTS.md schema
     (YAML frontmatter, encyclopedia-style prose, `[[concepts/slug]]` wikilinks).
4. If the log reveals non-obvious links between 2+ existing concepts, write a
   connection article in `{CONNECTIONS_DIR}`.
5. Update `{KNOWLEDGE_DIR / 'index.md'}` — add a row for each new article using the
   timestamp date from the user message:
   `| [[path/slug]] | One-line summary | source-file | YYYY-MM-DD |`
6. Append to `{KNOWLEDGE_DIR / 'log.md'}` using the timestamp from the user message:
   ```
   ## [<timestamp>] compile | <log filename>
   - Source: daily/<log filename>
   - Articles created: [[concepts/x]], [[concepts/y]]
   - Articles updated: [[concepts/z]] (if any)
   ```

## Quality standards

- Complete YAML frontmatter (title, sources, created, updated, tags, aliases)
- At least 2 `[[wikilinks]]` to other articles
- Key Points: 3–5 bullets; Details: 2+ paragraphs; Related Concepts: 2+ entries
- Sources section cites the daily log with specific claims extracted
- **IMPORTANT:** Reference daily logs as plain text `daily/YYYY-MM-DD.md` —
  do NOT use `[[daily/...]]` wikilinks (daily/ is at vault root, not under knowledge/,
  so wikilinks break).
"""

    prompt = f"""## Daily Log to Compile

**File:** {log_path.name}
**Timestamp:** {timestamp}

{log_content}

Compile this log per the rules in the system prompt. Use the timestamp above for the
index row date and the `log.md` entry header."""

    cost = 0.0

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=str(ROOT_DIR),
                system_prompt={
                    "type": "preset",
                    "preset": "claude_code",
                    "append": static_context,
                },
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],
                permission_mode="acceptEdits",
                max_turns=30,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        pass  # compilation output - LLM writes files directly
            elif isinstance(message, ResultMessage):
                cost = message.total_cost_usd or 0.0
                print(f"  Cost: ${cost:.4f}")
    except Exception as e:
        print(f"  Error: {e}")
        return 0.0

    # Update state
    rel_path = log_path.name
    state.setdefault("ingested", {})[rel_path] = {
        "hash": file_hash(log_path),
        "compiled_at": now_iso(),
        "cost_usd": cost,
    }
    state["total_cost"] = state.get("total_cost", 0.0) + cost
    save_state(state)

    return cost


def main():
    parser = argparse.ArgumentParser(description="Compile daily logs into knowledge articles")
    parser.add_argument("--all", action="store_true", help="Force recompile all logs")
    parser.add_argument("--file", type=str, help="Compile a specific daily log file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compiled")
    args = parser.parse_args()

    state = load_state()

    # Determine which files to compile
    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = DAILY_DIR / target.name
        if not target.exists():
            # Try resolving relative to project root
            target = ROOT_DIR / args.file
        if not target.exists():
            print(f"Error: {args.file} not found")
            sys.exit(1)
        to_compile = [target]
    else:
        all_logs = list_raw_files()
        if args.all:
            to_compile = all_logs
        else:
            to_compile = []
            for log_path in all_logs:
                rel = log_path.name
                prev = state.get("ingested", {}).get(rel, {})
                if not prev or prev.get("hash") != file_hash(log_path):
                    to_compile.append(log_path)

    if not to_compile:
        print("Nothing to compile - all daily logs are up to date.")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Files to compile ({len(to_compile)}):")
    for f in to_compile:
        print(f"  - {f.name}")

    if args.dry_run:
        return

    # Compile each file sequentially
    total_cost = 0.0
    for i, log_path in enumerate(to_compile, 1):
        print(f"\n[{i}/{len(to_compile)}] Compiling {log_path.name}...")
        cost = asyncio.run(compile_daily_log(log_path, state))
        total_cost += cost
        print(f"  Done.")

    articles = list_wiki_articles()
    print(f"\nCompilation complete. Total cost: ${total_cost:.2f}")
    print(f"Knowledge base: {len(articles)} articles")


if __name__ == "__main__":
    main()
