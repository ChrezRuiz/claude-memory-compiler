Query the knowledge base for a topic.

Run `uv run python scripts/query.py "$ARGUMENTS"` to perform index-guided retrieval against the compiled knowledge base.

If no argument is provided, ask the user what they want to query.

Report the synthesized answer to the user, including any wikilink citations to source articles.