---
runbook: query
purpose: "Answer a question against the compiled knowledgebase using index-guided retrieval (no RAG)"
inputs: "Natural-language question; optional --file-back flag"
outputs: "Synthesized answer with [[wikilink]] citations; optionally a new knowledge/qa/ article"
invoke_when:
  - User asks something that the KB likely already covers ("what's our DAQ noise floor?", "what did we decide on the nozzle mesh?", "who owns the Project X memo?")
  - User explicitly says "query the kb", "ask the kb", "look this up"
---

# Runbook: Query

## Purpose

Use the compiled knowledge layer to answer factual or contextual questions about FERDG work, decisions, members, or systems — without re-reading every conversation. Equivalent to `query.py` in upstream.

## Preconditions

- `knowledge/index.md` exists and has entries (otherwise: tell user the KB is empty, run `Runbooks/compile.md` first)

## Steps

### 1. Read the index

```
Read knowledge/index.md
```

### 2. Select candidate articles

Based on the question, pick **3–10** rows from the index that most plausibly contain the answer. Prefer:
- Articles whose `Article` slug or `Summary` semantically matches the question
- Articles tagged with the same domain as the question
- Connection articles that link multiple relevant concepts

If the index has fewer than 3 plausible matches, read all of them. If more than 10 match, read the top 10 by recency (`Updated` descending) and note in the answer that more exist.

### 3. Read the candidates in full

```
Read knowledge/concepts/<slug>.md      (for each)
Read knowledge/connections/<slug>.md   (for each)
```

### 4. Synthesize

Compose an answer that:
- Directly addresses the question (lead with the answer, not the framing)
- Cites every load-bearing claim with `[[wikilink]]` to its source article
- Names the daily log only when the article is sparse and the daily log adds material
- Calls out uncertainty explicitly — if the KB doesn't cover something, say so; do NOT fabricate

### 5. Optional: file the Q&A back

If the user invoked with `--file-back`, "save this answer", or this question is one MJ is likely to ask again, create:

```
knowledge/qa/<question-slug>.md
```

Format per `AGENTS.md` Q&A schema. Then:
- Append a row to `knowledge/index.md` under the qa/ section
- Append to `knowledge/log.md`:

```markdown
## [YYYY-MM-DDTHH:MM:SS] query | "<original question>"
- Consulted: [[concepts/...]], [[connections/...]]
- Filed to: [[qa/<slug>]]
```

### 6. Surface follow-ups

If the answer revealed gaps (a referenced concept didn't exist, a daily log was uncompiled), suggest one of:
- "I should compile daily/YYYY-MM-DD.md — it has related context"
- "Concept `[[concepts/foo]]` is sparse, want me to flesh it out from sources?"

## Why no RAG / embeddings

At ~50–500 articles the index fits in context. The LLM reading a structured index understands intent (e.g. "noise floor" → ADC characterization concept, not "noise pollution"). Cosine similarity matches tokens, not meaning. Reconsider only above ~2,000 articles.

## Failure modes

- **Empty KB** → tell the user, point them at `Runbooks/compile.md`.
- **No plausible matches in index** → answer from general knowledge only, label clearly as "not from KB."
- **Index out of sync** (article exists on disk but not in index) → fix during this pass: re-read article, append index row, note in `log.md`.
