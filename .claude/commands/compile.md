Compile daily logs into the knowledge base.

Run `uv run python scripts/compile.py` to process any uncompiled daily log entries into `knowledge/concepts/` and `knowledge/connections/`, updating `knowledge/index.md` and `knowledge/log.md`.

Report the output to the user. If compilation produces new or updated articles, list them.