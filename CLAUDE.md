# FERDG Second Brain — Cowork → Claude Code Handoff

> **Generated:** 2026-05-04  
> **Source:** Claude Cowork auto-memory (44 files), vault structure scan, 7 skills, 6 runbooks, AGENTS.md schema  
> **Purpose:** Full context transfer so Claude Code can operate this Obsidian vault with zero ramp-up

---

## 1. User Profile

**Name:** MJ (Chrezler MJ Ruiz)  
**Email:** chrezlermj@gmail.com  
**Role:** Aerospace design engineer, FERDG department — aircraft, rocketry, propulsion systems  
**Technical stack:** ANSYS simulation (Fluent, Mechanical), Python, MATLAB, embedded systems (Arduino/ESP32), propulsion instrumentation/DAQ  
**Also acts as:** Project manager for FERDG via ClickUp; this Obsidian vault is the department's second brain  

### Response Style — "Caveman Mode" (ALWAYS ACTIVE)

```
Rules:
- Drop articles (a, an, the), filler (just, really, basically), pleasantries (sure, certainly)
- Short synonyms (big not extensive, fix not "implement a solution for")
- No hedging. Fragments fine.
- Technical terms stay exact. Code blocks unchanged. Caveman only in conversational prose.
- "stop caveman" or "normal mode" → revert immediately

Pattern:
  [thing] [action] [reason]. [next step].

Example:
  Bug in auth middleware. Token expiry check use < not <=. Fix: [code block]
```

### Collaboration Style

MJ wants a collaborator that challenges reasoning directly, flags weak assumptions, cites sources for empirical claims, and states when uncertain. If fishing for validation, call it out.

---

## 2. Vault Structure

```
FERDG Second Brain/
├── AGENTS.md                        # Memory-compiler schema (Karpathy/Medin architecture)
├── .claude/                         # Claude agent config
│   ├── settings.local.json
│   ├── skills/                      # 7 vault-level skills (memory-flush/compile/query/lint, new-meeting/wpr/job-order)
│   └── agents/vault-health.md       # Structural health reviewer agent
│
├── daily/                           # Layer 1 — immutable per-day session logs (10 files, 2026-04-22 through 2026-05-04)
├── knowledge/                       # Layer 2 — LLM-compiled KB
│   ├── index.md                     # Master catalog — READ FIRST on every query
│   ├── log.md                       # Append-only build log
│   ├── concepts/ (21 articles)      # Atomic knowledge articles
│   ├── connections/ (2 articles)    # Cross-cutting insights
│   ├── ClickUp/                     # ClickUp workspace mirror (read/write enabled 2026-05-05)
│   │   ├── index.md
│   │   ├── NEO-S Rocket/ (Agile Ceremonies, Backlog, Kanban Board)
│   │   ├── FERDG Facility/ (Kanban Board)
│   │   └── Administrative Tasks/ (Kanban Board)
│   ├── FERDG-TDoc-Format.md        # Standard document format spec
│   ├── FERDG-WPR-Format.md         # WPR presentation format spec
│   ├── FERDG-TPLAN-Format.md       # Testing plan format spec
│   └── Attachments/WPR_Format.pptx
│
├── FERDG/                           # Department operating data (human-authored, compiler reads but doesn't write)
│   ├── FERDG Projects/
│   │   ├── Neo-S Rocket.md, Neo-H.md, ANSYS Training.md, etc.
│   │   └── NEO-S v1/               # Active rocket project subfolder
│   │       ├── NEO-S v1.md, SRM Static Thrust Test Plan.md, SRM Procedure and Safety.md
│   │       ├── Flight Computer TDD v2.1.md
│   │       ├── Research/ (RRL/, Analysis/, References/)
│   │       └── Archive/
│   ├── FERDG Members/ (4 people: MJ, Kent, Berazon, Zakk)
│   ├── FERDG Job Orders/ (~22 notes)
│   ├── FERDG Work Meetings/ (~14 notes)
│   └── FERDG WPR/ (~10 notes)
│
├── standards/                       # Engineering reference notes
│   ├── ANSYS/ (Fluent, Mechanical, mesh quality, errors)
│   ├── Propulsion/ (test procedures, post-test protocols)
│   ├── Instrumentation/ (load cells, NAU7802, PlatformIO)
│   └── Mechanical Systems/ (stepper motors, NEMA 17, A4988)
│
├── Runbooks/                        # Operation procedures (6 runbooks)
│   ├── flush.md                     # transcript → daily/
│   ├── compile.md                   # daily/ → knowledge/
│   ├── query.md                     # index-guided KB retrieval
│   ├── lint.md                      # 7 health checks
│   ├── clickup_sync.md              # Daily incremental ClickUp mirror update
│   ├── clickup_reconcile.md         # Weekly full-snapshot reconciliation
│   └── scripts/clickup/
│       ├── gen_clickup_md.py        # Full-regen renderer with anchor emission
│       └── clickup_patch.py         # Incremental patcher (--patch-file, --vault-root, --dry-run)
│
├── reports/                         # Lint output (lint-YYYY-MM-DD.md)
├── Miscellaneous/People/, Organizations/
├── Bases/ (5 Obsidian database views)
├── Templates/ (6 templates: People, WPR, Job Order, Work Meeting, Project, Weekly Log)
├── Attachments/ (~52 files: screenshots, PDFs, docx)
│
└── Root files:
    ├── NEOS-v1_SRM_StatThrust_Checklist.docx
    ├── TPLAN_Template.docx
    ├── NEOS-v1_SRM_PerfAnalysis_WPR.pptx
    ├── NEOS-v1_SRM_PerfAnalysis_TestPlan.pptx
    └── WPR_04-24-26_Ruiz.pptx
```

---

## 3. Memory-Compiler Architecture

Adapted from Karpathy's LLM Knowledge Base gist via Cole Medin's `claude-memory-compiler`. Original targets Claude Code CLI with hooks; this runs inside Claude using skills + runbooks.

### The Compiler Analogy

```
daily/          = source code      (raw conversation logs — append-only, immutable)
Claude (LLM)    = compiler         (extracts, organizes, cross-references)
knowledge/      = executable       (structured queryable knowledgebase)
Runbooks/lint   = test suite       (consistency + health checks)
queries         = runtime          (using the knowledge to answer questions)
```

### Four Operations

| Op | Trigger | Runbook | What it does |
|---|---|---|---|
| **Flush** | "flush memory" or daily scheduled | `Runbooks/flush.md` | transcript → `daily/YYYY-MM-DD.md` |
| **Compile** | "compile" or after flush | `Runbooks/compile.md` | `daily/` → `knowledge/concepts/`, `connections/`; update `index.md` + `log.md` |
| **Query** | "query the kb for X" | `Runbooks/query.md` | Read `index.md` → pick 3-10 articles → synthesize answer with `[[wikilink]]` citations |
| **Lint** | "lint" or weekly scheduled | `Runbooks/lint.md` | 7 checks (broken links, orphans, stale, sparse, contradictions) → `reports/lint-YYYY-MM-DD.md` |

### Article Formats (schema authority: AGENTS.md)

**Concept articles** (`knowledge/concepts/`): YAML frontmatter (title, sources, created, updated, tags, aliases) → core explanation → Key Points (3-5 bullets) → Details (2+ paragraphs) → Related Concepts → Sources.

**Connection articles** (`knowledge/connections/`): links 2+ concepts with frontmatter `connects:` field.

**Q&A articles** (`knowledge/qa/`): filed answers from queries, compound future retrieval.

### Conventions

- Wikilinks: `[[path/to/article]]` relative to `knowledge/`, no `.md` extension
- File naming: lowercase, hyphens (`esp32-adc-noise.md`)
- Dates: ISO 8601 (`YYYY-MM-DD`; full ISO for `log.md`)
- Writing style: encyclopedia-style, factual, self-contained
- Every article must link back to source daily log(s)
- No RAG needed at current scale (~50-500 articles); index-guided retrieval outperforms embeddings

### Legacy Folders (READ-ONLY for compiler)

`FERDG/`, `standards/`, `Miscellaneous/`, `Templates/`, `Archive/`, `Attachments/`, `Bases/` — compiler reads for context but does NOT reorganize. Migration into `knowledge/` is opt-in only.

---

## 4. ClickUp Integration

### Mirror Architecture

Workspace `90161503255` mirrored into `knowledge/ClickUp/`. Comment-anchor markup: `<!-- clickup-id: X -->` before each H3 task block, `<!-- clickup-tasks-start/end -->` delimiters.

### Member Mapping

| ClickUp ID | Name | Vault Wikilink |
|---|---|---|
| 61669071 | Chrezler MJ Ruiz | `[[Chrezler MJ Ruiz]]` |
| 100988547 | Kent Justine Legada | `[[Kent Justine Legada]]` |
| 100987392 | Berazon Onuoha | `[[Berazon Onuoha]]` |
| 100987391 | Zakk | `[[Zakk Familar]]` **(name pinned — hardcoded)** |

### Sync Machinery

- **Daily sync** (`clickup_sync.md`): delta via `clickup_filter_tasks` with `date_updated_gt = now - 26h`, classify as upsert/move, apply via `clickup_patch.py`, append delta to daily log
- **Weekly reconcile** (`clickup_reconcile.md`): full snapshot for deletion detection, 90-day archival, sort-drift fix, hierarchy refresh; regenerates list files via `gen_clickup_md.py`

### Write Access Policy (enabled 2026-05-05)

Full read/write access to ClickUp workspace. All `clickup_*` MCP tools are permitted — create, update, assign, move, delete, comment.

**Safety guardrails:**
1. Confirm with MJ before deleting any task
2. Always verify task IDs with `clickup_get_task` before updating (ghost ID protection)
3. Log all write operations to `daily/YYYY-MM-DD.md`
4. Never batch-delete — one at a time with confirmation

### Known Issues

- **OAuth token doesn't persist across sessions** — automated sync skips + writes SKIPPED entry; MJ must re-auth manually
- **clickup_patch.py BLOCK_RE field order mismatch** — legacy mirror files (pre-2026-04-27) use different field order; causes silent data loss on upsert. Safe fix: pass ALL tasks as upserts. Reconcile run fixes format.
- **Ghost task IDs** — deleted tasks leave IDs in memory with no API tombstone. Always call `clickup_get_task` to verify before acting on stored IDs.

---

## 5. Automation (Claude Code Hooks)

Cowork scheduled tasks (`ferdg-daily-compile`, `ferdg-weekly-lint`, `ferdg-clickup-sync`, `ferdg-clickup-reconcile`) were retired during the 2026-05-04 migration. Automation now runs via Claude Code hooks in `.claude/settings.json`:

| Hook | Script | Replaces |
|---|---|---|
| `SessionStart` | `hooks/session-start.py` | — (new; injects KB index + recent daily log) |
| `PreCompact` | `hooks/pre-compact.py` | — (new; captures conversation before context compression) |
| `SessionEnd` | `hooks/session-end.py` | `ferdg-daily-compile` (flush + auto-compile after 6 PM) |

**Not yet replaced:**
- **Weekly lint** — run manually via `uv run python scripts/lint.py --structural-only`, or set up a Claude Code scheduled task
- **ClickUp sync/reconcile** — manual only; blocked by OAuth token expiry across sessions

**Critical rule:** Every automated task that edits files or produces new learnings MUST end with a flush-memory step.

---

## 6. Document Format Standards

### TDOC (Technical Documents)

- **Paper:** A4 (not US Letter), 1" margins
- **Font:** Helvetica 10pt body; H1-H4 = 16/13/11/10pt Bold
- **Footer:** right-aligned 9pt — `FERDG | Technical Design Document | Page X of Y`
- **Cover:** FEATI seal + institution name + doc type + project title + metadata table (TDOC-YYYY-NNN)
- **Structure:** I. Accomplishment Declaration → II. Executive Summary → III. System Architecture → IV. [L2 System] (repeated) → V. Drawing Register → VI. References (IEEE)
- **Full spec:** `knowledge/FERDG-TDoc-Format.md`; template: `Attachments/tdoc_format.docx`

### TPLAN (Testing Plans)

- **Numbering:** TPLAN-YYYY-NNN
- **8 sections:** Overview → Site & Procedural Alignment → Progressive Testing Sequence → Instrumentation → Success Criteria → Safety & Risk → Integration with Engineering Standards → References
- **10 standard tables** (Doc Cross-Ref, RTM, Testing Sequence, Instrumentation Register, DAQ Channel Map, Success Criteria Matrix, Hazard Register, Personnel, Analysis Correlation)
- **Full spec:** `knowledge/FERDG-TPLAN-Format.md`; template: `TPLAN_Template.docx`

### WPR (Presentations)

- **Size:** 16:9, 13.333 × 7.5 in, dark background
- **Font:** Inter
- **Palette:** cream `#F0EEE6` text, coral `#CC785C` accent, sage `#8FA68E`, gold `#C8A97E`, warm grays
- **CEO program-review structure (7 slides):** Cover → Agenda (01/OVERVIEW) → Status (02/STATUS) → Milestones (03/SCHEDULE) → Technical (04/TECHNICAL) → Risk (05/RISK) → Next Steps (06/NEXT)
- **Personal WPR structure (8 slides):** Cover → Agenda → Week Summary → Tasks → Deliverables → Technical Progress → Approvals & Milestones → Next Steps
- **Naming:** `WPR_MM-DD-YY_Ruiz.pptx` in vault root
- **Full spec:** `knowledge/FERDG-WPR-Format.md`; template: `knowledge/Attachments/WPR_Format.pptx`

---

## 7. Behavioral Rules (Feedback Memories)

These are hard-won lessons from iterating with MJ. Follow strictly.

### Document Generation

1. **No pre-fill in templates.** Leave all metadata/ID fields blank in generated .docx templates. No default values.
2. **Theme = colors/fonts only, not structure.** When MJ says "use X template," apply visual theme (palette, typography, motifs) — content structure follows source document, not template's native framework.
3. **Decks use minimal slide text + speaker notes.** Slides carry headlines/numbers/tables only. All narrative lives in `addNotes()`. Title slide uses filename.
4. **Test plans integrate D.2 + D.3 dual scope.** Propulsion test-plan decks/docs must integrate performance + structural into every content slide, not separate sections.

### pptxgenjs Build Gotchas

1. Write build scripts via `bash cat <<EOF` heredoc, not Write tool (path resolution differs)
2. Multi-column `addText` needs `valign: 'top'` (prevents vertical centering misalignment)
3. QA artifacts render to `/tmp/qaN/`, not outputs dir (can't `rm` in outputs, files stick in vault)
4. 3+ stacked bulleted groups → switch to 3-column layout (height overflow)
5. Slide canvas: 13.333 × 7.5 in; usable content zone y=2.1 to y=6.9; margins >= 0.5"

### Lucid Diagram Preferences

- `use_assisted_layout: false` (fixed positioning)
- Normalize shape geometry by class: process 300x70, decision 300x120, terminator 300x70
- Vertical pitch 90px; inter-container gap >= 50px
- Color bands: terminators green `#C8E6C9`, pre-test blue `#BBDEFB`, firing orange `#FFCC80`, post-test purple `#D1C4E9`, decisions yellow `#FFF59D`, hazards red `#FFCDD2`, data teal `#E0F7FA`
- Decision exits: solid black = YES, dashed red `#D32F2F` = NO
- Self-loop fix: route through intermediate waypoint shape
- Status signals vs. gates: status signals = process/hexagon blocks (no blocking); decision diamonds ONLY for actual conditional branches
- Line spec: use `lineType` + `stroke` (NOT `style`) for appearance; endpoint definitions require `style` field

### Vault & Automation

1. **Flush memory required on ALL automated tasks** that edit files or produce new learnings
2. **Verify ClickUp task IDs before acting** — call `clickup_get_task` first; deleted tasks leave ghost IDs
3. **Vault lint recurring patterns:**
   - Tombstone `superseded_by:` placeholders never filled → broken links
   - `knowledge/index.md` not auto-updated after compile → verify after every compile
   - `[[daily/YYYY-MM-DD]]` wikilinks in concept articles are systemically broken (knowledge/ vs vault root path resolution) → use plain text for daily log citations
   - ClickUp mirror generates person wikilinks with no target articles → create stubs or emit plain text

### Cowork-Specific (may not apply in Claude Code)

- Skip computer-use for simple copy-paste — provide text blocks + instructions instead
- Cowork artifact `callMcpTool` returns MCP content wrapper not plain JSON — needs universal `parse()` + `safeTool()`
- CLAUDE.md write-protected from non-vault-cwd sessions — daily compile catches missed flushes

---

## 8. Active Project State — NEO-S v1

### Overview

NEO-S V1 is an active FERDG sounding rocket. Primary document: Technical Design Document (TDD) in Google Docs.

**TDD Google Doc:** https://docs.google.com/document/d/1kDX2wQE6I3oPpyGFjwpCj-LHJxPFAn0s/edit

### Current Phase: Experimental Testing + Fabrication Prep

- Analytical analysis + digital simulation (OpenMotor + ANSYS FLUENT) = COMPLETE
- SRM test plan APPROVED by Engr. K. J. Legada (2026-04-23)
- Avionics + Recovery test plans APPROVED by MJ (2026-04-27)
- Structure testing plan = STILL OPEN
- Subsystem parent tasks (Recovery, Avionics, Airframe) = ALL DONE (2026-04-30)
- MR & Fabrication Release (Kent, 86d24bwab) = IN PROGRESS, due 2026-05-27

### SRM Performance Analysis (TDD D.2)

- Simulation outputs: Fmax=108N, Favg=105.627N, ta=1.218s, Itotal=132.3Ns (from original 7075-T6 + phenolic material set)
- Propellant: KNSU/sugar, BATES grain geometry, graphite nozzle
- N >= 5 firings (N=7 preferred), same propellant batch
- **Known TDD errors (UNFIXED):** D.2.1 table — Average Thrust column reads "s" (should be "N"); Action Time reads "MPa" (should be "s")

### SRM Test Procedure Decisions

- Each firing = self-contained process in per-motor SOP
- GO/NO-GO gate = hard abort on NO (no loop-back)
- Countdown: T-10 s
- Misfire: wait >= 5 min → do NOT reuse motor → disposal → sample excluded
- Replacement motor: same propellant batch, full pre-test measurement sequence

### Material Substitution (2026-04-24)

| Component | Original | Substituted | Reason |
|---|---|---|---|
| Aluminum structural | 7075-T6 | 6061-T6 | Local fabricator can't source/machine 7075 |
| Liner/insulator | Phenolic | Fibra equiv (ANSYS) | Phenolic not locally available |

**Fabricator sourcing leads:** JLCNC (direct), Jiga.io (marketplace/aggregator, Todd Miner = account manager, onboarded 2026-04-28)

### OPEN CONTRADICTION (unresolved since 2026-04-27)

- `neos-v1-srm-performance-study-status.md` says OpenMotor "overpredicts" F_max
- `neos-v1-srm-test-plan-methodology.md` says simulation "under-predicts" F_max
- Same mechanism cited (ignition transient), opposite conclusion. Likely: test-plan-methodology is correct (missing ignition transient → sim ramps slower → real peak > sim → underpredicts). Needs MJ confirmation.

### Flight Computer TDD v2.1

- Architecture: Feather M0 Adalogger + RFM95W LoRa Breakout + Ultimate GPS V3 + BMP280
- 27-item BOM (15 Core, 1 Optional, 11 Upgrade); BOM xlsx in vault
- Status: Design Phase — Pre-Build
- **Apogee detection:** BMP280 dh/dt (no accelerometer); climb threshold 15 ft/s; misfire gate 12 ft AGL; Vh <= 0 → 3s delay → servo release → spring ejection
- **7 status signals:** IDLE → ARMED → LAUNCH DETECTED → APOGEE DET. ENABLED → APOGEE DETECTED → RECOVERY DEPLOY → DESCENT
- **Open gaps:** MA/Kalman filter spec not in TDD; apogee section missing from TDD v2.1

### Test Stand

- Berazon completed all design tasks (2026-04-25): load cell 20 kgf, platform mods, mount
- Motor accommodation tasks ALL DONE (2026-04-30): design mods, cutting list, BOM
- Test stand physically ready pending fabrication/procurement

### Other Completed Items

- Avionics bay mod for new FC (DONE 2026-04-25)
- Airframe System + Concept + Simulation (ALL DONE 2026-04-30)
- KNO3+Sugar shelf life study (DONE)
- Fabrication Plan (Zakk, DONE 2026-04-30): propellant composition + procedure + QC criteria
- Test Phase flowchart TDD §5.3 (DONE 2026-04-30): P1 validation + P2 alt material
- PRV stepper motor mount mod (Berazon, DONE 2026-04-27)

### Active/Open Tasks (as of 2026-05-04)

- MJ: Mesh convergence TDD integration — airframe (86d2uypfg) + propulsion (86d2uypej) — status unconfirmed
- MJ: Design Review & Deliberation (86d24bykx) — Urgent
- MJ: Technical Documentation (86d2pa8ug) — in progress
- Berazon: Assign Reference Numbers to Engineering Drawing Pages (86d2v29t1) — due 2026-05-04
- Kent: MR & Fabrication Release (86d24bwab) — due 2026-05-27
- Sprint Review & Retrospective — overdue since 2026-05-01

---

## 9. Team Members

| Name | ClickUp ID | Role Context |
|---|---|---|
| **Chrezler MJ Ruiz** | 61669071 | Lead engineer, PM, simulation, documentation |
| **Kent Justine Legada** | 100988547 | Simulation (airframe), MR & fabrication release |
| **Berazon Onuoha** | 100987392 | Hardware design (test stand, avionics bay, mods), engineering drawings |
| **Zakk Familar** | 100987391 | Propellant (KNO3 study, fabrication plan, shelf life) |

---

## 10. External References

| What | Where |
|---|---|
| NEO-S v1 TDD Google Doc | https://docs.google.com/document/d/1kDX2wQE6I3oPpyGFjwpCj-LHJxPFAn0s/edit |
| NotebookLM notebook | https://notebooklm.google.com/notebook/c070c117-2abc-498a-ad56-1994121c5798 |
| SRM Procedure workflow v3 | lucid.app/lucidchart/f3acca7a-0135-4840-8d41-af4cfa71b181 |
| SRM Procedure workflow v4 | lucid.app/lucidchart/db14991e-c265-4445-97a5-f19af10af2ff |
| Performance Analysis Framework | lucid.app/lucidchart/9efce62f-0c15-4a2f-942a-784455ea98fe |
| Test Phase Flowchart v3 | Lucid doc 2d53ea6b-5aae-40d2-984b-890091deb56a |
| FC Apogee Detection flowchart v3 | lucid.app/lucidchart/7a5ff36f-d7f6-442f-b3f1-4634eda544be |
| Jiga.io | Fabricator marketplace; Todd Miner = account manager |
| JLCNC | Direct fabricator for 6061-T6 parts |
| FEATI University | Manila PH; potential academic partner; `knowledge/connections/FEATI-University.md` |

---

## 11. Skills Reference (vault-level, in `.claude/skills/`)

### Memory Operations

| Skill | Trigger | Delegates To |
|---|---|---|
| `memory-flush` | "flush memory", "capture this session" | `Runbooks/flush.md` |
| `memory-compile` | "compile", "build the kb" | `Runbooks/compile.md` |
| `memory-query` | "query the kb for X", "what did we decide about Y" | `Runbooks/query.md` |
| `memory-lint` | "lint", "check kb health" | `Runbooks/lint.md` |

### Note Creation

| Skill | Trigger | Output Location |
|---|---|---|
| `new-meeting` | Create work meeting note | `FERDG/FERDG Work Meetings/Work Meeting - Mon DD, YYYY.md` |
| `new-wpr` | Create WPR note | `FERDG/FERDG WPR/WPR - Mon DD, YYYY.md` |
| `new-job-order` | Create job order note | `FERDG/FERDG Job Orders/{Task Name}.md` |

All note-creation skills use wiki-linked attendees/assignees and FERDG-standard tags.

---

## 12. Cowork Artifacts (may need reimplementation for Claude Code)

Two live Cowork sidebar artifacts existed:

1. **ferdg-mission-control** — department status dashboard: active tasks, team workload bars, calendar events, Gmail unread, action radar
2. **ferdg-wpr-prestager** — WPR prep tool: auto-maps ClickUp completed/active tasks + calendar into WPR slide structure

Both used `window.cowork.callMcpTool` with universal `parse()` + `safeTool()` pattern. Will need different implementation in Claude Code context.

---

## 13. WPR Weekly Cadence

First shipped 2026-04-24. Every Friday → one deck.

- **Naming:** `WPR_MM-DD-YY_Ruiz.pptx`
- **Location:** vault root
- **Data sources:** ClickUp filter (done + new tasks this week) + daily/ session logs + memory files
- **Build tool:** pptxgenjs via Node.js build script

---

## 14. Complete Memory File Listing

Below is every memory from the Cowork auto-memory system, organized by type. These represent accumulated project knowledge that should be preserved.

### User Memories

- **User role and tooling** — MJ is FERDG aerospace design engineer; ANSYS/Python/MATLAB/ESP32/propulsion DAQ; caveman-style replies

### Feedback Memories (Behavioral Rules)

- **Flush memory required on all edit/learning automations** — every automated task must end with flush-memory step
- **Skip computer-use for simple copy-paste** — provide text blocks + instructions instead of browser control
- **No pre-fill in templates** — leave all metadata/ID fields blank
- **FERDG test plans integrate D.2 + D.3 dual scope** — performance + structural in every content slide
- **Theme is colors/fonts — not structure** — "use X template" = visual theme only
- **Decks use minimal slide text + speaker notes** — headlines/numbers/tables on slides, narrative in addNotes
- **pptxgenjs build-script gotchas** — heredoc for build.js, valign:top, QA to /tmp
- **Lucid diagram style preferences** — fixed layout, uniform geometry, color bands, self-loop fix, status signals vs gates
- **FERDG vault lint recurring patterns** — tombstone placeholders, index not auto-updated, broken daily wikilinks, missing person articles
- **CLAUDE.md write-protected from non-vault-cwd sessions** — daily compile catches missed flushes
- **clickup_patch.py legacy mirror format mismatch** — BLOCK_RE field order mismatch silently wipes tasks
- **Cowork artifact callMcpTool requires universal parser** — MCP content wrapper, not plain JSON
- **ClickUp MCP OAuth token expiry** — doesn't persist across sessions; automated sync skips
- **Verify ClickUp task IDs before acting** — deleted tasks leave ghost IDs

### Project Memories

- **NEO-S v1 TDD Google Doc** — D.2 structure, sim values, unit errors, NLM gap
- **NEO-S v1 SRM Study Phase** — study done 2026-04-23; TPLAN complete 2026-04-27; T-10 countdown, hard abort
- **NEO-S v1 Subsystem Testing Phase** — Avionics+Recovery+Airframe parent tasks DONE 2026-04-30; Structure plan still open
- **NEO-S v1 Flight Computer TDD v2.1** — Feather M0 + RFM95W + GPS + BMP280; apogee detection algorithm
- **NEO-S v1 Avionics + Recovery test plan approvals** — both approved 2026-04-27
- **NEO-S v1 SRM Test Checklist** — compact per-firing .docx from Lucid workflow
- **NEO-S v1 SRM PerfAnalysis Test-Plan Deck** — 15-slide WPR theme + D.2 structure
- **NEO-S v1 SRM Test Plan approval** — Engr. Legada approved 2026-04-23
- **FERDG WPR weekly cadence** — first shipped 2026-04-24; 8-slide personal structure
- **NEO-S v1 SRM Material Substitution** — 7075→6061, phenolic→fibra; JLCNC + Jiga leads
- **NEO-S v1 SRM F_max contradiction (OPEN)** — overpredicts vs underpredicts; needs MJ resolution
- **NEO-S v1 Test stand modifications** — Berazon completed all design tasks 2026-04-25
- **NEO-S v1 Avionics bay mod** — both DONE 2026-04-25
- **NEO-S v1 KNO3 shelf life testing** — DONE; original planning tasks deleted
- **NEO-S v1 Airframe subtasks** — Concept + Simulation all DONE 2026-04-30
- **Testing Facility PRV stepper mount** — ALL DONE 2026-04-27
- **NEO-S v1 Test stand motor accommodation** — ALL DONE 2026-04-30
- **NEO-S v1 Fabrication Plan** — Zakk, DONE 2026-04-30
- **NEO-S v1 Test Phase section (TDD 5.3)** — DONE 2026-04-30; Lucid v3 flowchart
- **NEO-S v1 TDD Mesh Convergence tasks** — MJ; status unconfirmed
- **NEO-S v1 Avionics + Recovery combined TDOC** — target completion 2026-04-29

### Reference Memories

- **FERDG TDoc Format** — `knowledge/FERDG-TDoc-Format.md`; A4 Helvetica 10pt
- **FERDG TPLAN Format** — `knowledge/FERDG-TPLAN-Format.md`; TPLAN-YYYY-NNN
- **FERDG WPR Format** — `knowledge/FERDG-WPR-Format.md`; 16:9 Inter dark theme
- **FEATI University** — `knowledge/connections/FEATI-University.md`
- **FERDG ClickUp vault mirror** — architecture at `knowledge/ClickUp/`
- **FERDG memory-compiler** — Karpathy/Medin architecture in this vault
- **FERDG live Cowork artifacts** — ferdg-mission-control + ferdg-wpr-prestager
- **Jiga.io account** — Todd Miner, onboarded 2026-04-28

---

## 15. Migration Notes for Claude Code

### What transfers directly

- All vault files, runbooks, skills, AGENTS.md — these are vault-native markdown and Python scripts
- Memory-compiler pipeline (flush/compile/query/lint) — designed to work with Read/Write/Edit/Glob/Grep
- ClickUp sync/reconcile scripts (`gen_clickup_md.py`, `clickup_patch.py`)
- All document format specs

### What needs adaptation

1. **Scheduled tasks** — Cowork used `mcp__scheduled-tasks`; Claude Code needs hooks or cron equivalents
2. **Session transcript access** — Flush runbook uses `mcp__session_info__list_sessions` / `read_transcript`; Claude Code may have different mechanism
3. **ClickUp MCP** — OAuth flow differs; may need API token approach instead
4. **Cowork artifacts** — sidebar dashboards don't exist in Claude Code; consider HTML file generation or terminal dashboard alternatives
5. **Path references** — Runbooks reference `/sessions/<id>/mnt/FERDG Second Brain/`; Claude Code uses actual filesystem paths
6. **Note-creation skills — paths updated to vault-relative (2026-05-04)
7. **Auto-memory system** — Cowork had `.auto-memory/MEMORY.md`; Claude Code has its own `CLAUDE.md` + memory mechanisms

### CLAUDE.md for Claude Code

This entire document can serve as the initial `CLAUDE.md` for Claude Code, or be condensed into one. Key sections to keep in CLAUDE.md: User Profile (section 1), Behavioral Rules (section 7), Document Format Standards (section 6), and the ClickUp read-only constraint (section 4).

---

*End of handoff document. Generated from 44 Cowork memory files, 7 skills, 6 runbooks, AGENTS.md, and full vault scan.*
