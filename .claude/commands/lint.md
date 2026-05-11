Run a structural health check on the knowledge base.

Run `uv run python scripts/lint.py --structural-only` to perform the 7 health checks (broken links, orphans, stale articles, sparse articles, missing backlinks, contradictions, source coverage).

Report the summary to the user: error/warning/suggestion counts and top findings. If errors are found, suggest remediation steps.