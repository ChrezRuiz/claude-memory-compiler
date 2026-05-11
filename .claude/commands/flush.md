Flush the current session's conversation into today's daily log.

Run `uv run python scripts/flush-now.py` to extract recent conversation turns and spawn the flush agent in the background. Report the output to the user.

After running, confirm:
1. How many turns were extracted
2. That the flush was spawned successfully
3. Remind user to check `daily/` for the appended entry