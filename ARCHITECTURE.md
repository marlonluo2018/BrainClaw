# BrainClaw System Architecture

> Personal AI Assistant System Design Document

---

## 1. System Overview

BrainClaw is a personal AI assistant system designed for office productivity. It uses a **Brain File System** architecture where knowledge, workflows, and skills are stored as markdown files, enabling the AI to read and execute operations dynamically.

### Key Features
- **Memory-driven learning**: Remembers user preferences and avoids past mistakes
- **Workflow orchestration**: Multi-step operations guided by workflow files
- **Skill-based extensibility**: Modular skills for specific functionalities
- **Task management**: Comprehensive task tracking with RACI stakeholder mapping
- **Process awareness**: Company-specific operational processes

---

## 2. Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  System Prompt (CLAUDE.md)                   │
│          Startup & On-Demand Loading Rules                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Brain Files                               │
│  ┌──────────────────────────────────────────┐              │
│  │         Memory Files                     │              │
│  │  preferences | things_to_avoid |         │              │
│  │  contacts | achievements                 │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         Workflow Layer (orchestration + business logic)     │
│  TASK_WORKFLOW | EMAIL_WORKFLOW | PROCESS_WORKFLOW |        │
│  REDHAT_WORKFLOW | VIEWS_WORKFLOW                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Skills Layer (I/O — external systems)             │
│  outlook-com-skill | minimax-xlsx | skill-creator                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  Tasks | Stakeholders | Processes | Memory | Downloads      │
└─────────────────────────────────────────────────────────────┘
```

**Two-layer separation:**
- **Workflow layer** holds all business logic (task lifecycle, RACI suggestion, event recording, email composition rules) directly inside the workflow `.md` files.
- **Skills layer** is reserved for I/O against external systems (Outlook COM, Excel files). Skills are self-contained, project-agnostic, and have no business logic.

There is no "workflow skill" middleware tier — workflows call I/O skills directly.

---

## 3. Directory Structure

```
BrainClaw/
├── CLAUDE.md                     # System prompt — single source of truth
├── README.md                     # User documentation (EN)
├── README_CN.md                  # User documentation (CN)
├── ARCHITECTURE.md               # This file
│
├── assistant_brain/              # Core brain directory
│   ├── recurring_tasks.md        # Recurring task definitions
│   ├── views_config.md           # View thresholds & display config
│   │
│   ├── memory/                   # Learning & persistence
│   │   ├── preferences.md        # User preferences
│   │   ├── things_to_avoid.md    # Cognitive blind-spot patterns
│   │   ├── achievements.md       # 述职 fact base
│   │   └── vendor-accounts.md    # Vendor portal credentials
│   │
│   ├── workflows/                # Orchestration + business logic
│   │   ├── TASK_WORKFLOW.md
│   │   ├── EMAIL_WORKFLOW.md
│   │   ├── PROCESS_WORKFLOW.md
│   │   ├── REDHAT_WORKFLOW.md
│   │   └── VIEWS_WORKFLOW.md
│   │
│   ├── scripts/                  # Python automation
│   │   ├── dashboard.py          # Startup display, taskboard, pending, digest, timesheet
│   │   └── followup.py           # Stale task detection for follow-up workflow
│   │
│   ├── skills/                   # I/O against external systems
│   │   ├── outlook-com-skill/        # Outlook COM (find/thread/compose)
│   │   ├── minimax-xlsx/         # Excel file I/O
│   │   └── skill-creator/        # Author new skills
│   │
│   ├── tasks/                    # Task management
│   │   ├── queue.md              # Active task queue
│   │   ├── FORMATS.md            # Task format spec
│   │   ├── T001-xxx.md           # Task files
│   │   └── history/              # Completed tasks
│   │
│   ├── contacts.md               # Single source of truth for people (tone, email, role)
│   │
│   ├── process/                  # Operational processes (by geo)
│   │   ├── README.md             # Process index
│   │   ├── philippines/          # PH processes
│   │   ├── china/                # CN processes
│   │   └── global/               # Global processes
│   │
│   └── backups/                  # Backup files
│
└── downloads/                    # Downloaded files
```

---

## 4. Component Details

### 4.1 CLAUDE.md (Root)

**Purpose**: Single source of truth for all system rules — identity, values, user config, operational rules, workflow routing, on-demand loading gates.

All behavioral rules, user config, and operational policies live in `CLAUDE.md` (always in context). Workflows and skills are loaded on-demand per the routing table in CLAUDE.md.

### 4.2 Memory System

The memory system enables persistent learning across sessions. Memory files hold **user-derived data** that the system learns over time — distinct from system config (which lives at `assistant_brain/` root).

| File | Trigger | Purpose |
|------|---------|---------|
| `memory/preferences.md` | User explicitly states preference | Store work preferences (tone, language, formatting) |
| `memory/things_to_avoid.md` | Recurring failure mode (Pattern) OR composition Don't | Drives blind-spot prompts; tactical output Don'ts |
| `memory/achievements.md` | Auto-fed from Complete Task; manual additions also welcome | 述职 fact base, used by `review` view command |
| `memory/vendor-accounts.md` | Vendor portal credentials discovered | Vendor login info for procurement portals |

**Note:** `views_config.md` (view thresholds + defaults) is **not** memory — it's system config. Lives at `assistant_brain/` root.

**Recording Threshold**: See `TASK_WORKFLOW.md` (Event & Memory Recording)

### 4.3 Workflows

Workflows hold **all business logic** and step-by-step procedures. They orchestrate work and call I/O skills directly when external system access is needed.

| Workflow | Purpose | I/O Skills Used |
|----------|---------|-----------------|
| `TASK_WORKFLOW.md` | Task CRUD, keyword extraction, achievement extraction on completion, event & memory recording | (none — pure file ops) |
| `EMAIL_WORKFLOW.md` | Email processing, geo detection, composition rules, email→task asks/decisions extraction, Key Email Criteria for EntryID tracking, stale-task follow-up | `outlook-com-skill` |
| `PROCESS_WORKFLOW.md` | Process matching, auto-advance suggestions, process learning from email patterns, codification | (none — pure file ops) |
| `REDHAT_WORKFLOW.md` | Red Hat audience targeting & shortlisting (4-phase lifecycle, course exclusion tables), TU ledger sync, Smartsheet balance | `redhat-audience-processor`, `enrollment-downloader`, `outlook-com-skill` |
| `VIEWS_WORKFLOW.md` | Per-task and cross-task views: status, owed, waiting, before, review/述職, digest, timesheet | (none — pure file ops) |

**Design Pattern:**
```markdown
## Operation Name

**Trigger:** When to execute

**Steps:**
1. Action → (inline business logic, e.g. read queue.md)
2. Action → Call `outlook-com-skill` find-recent
3. ...
```

### 4.4 Workflow vs Skill — Division of Responsibility

| Aspect | Workflow | Skill |
|--------|----------|-------|
| **Role** | **Orchestrator + business logic** | **I/O against external systems** |
| **Content** | Step sequence, decision rules, process matching, format rules | CLI commands, file format readers/writers |
| **Examples** | "Create Task," "Next Step," "Codify Process" | Read Outlook inbox, parse .xlsx |
| **Coupling** | Project-specific (knows about queue.md, tasks/, registry.md) | Project-agnostic (no BrainClaw imports) |

**Why this split:** Business logic that is markdown-readable belongs in workflows so the AI can read and follow it without code execution. External-system I/O (COM, file formats, APIs) requires real code, so it lives in skills.

**Example — Creating a Task** (entirely workflow-resident; no I/O skill needed):

```markdown
# TASK_WORKFLOW.md → Create Task
1. Read queue.md header → Get Last Task ID, increment
2. Extract keywords (rules in workflow itself)
3. Match contacts against contacts.md, suggest RACI
4. Present RACI matrix → Get user confirmation
5. Generate filename: T{ID}-{kw1}-{kw2}.md
6. Write task file using template from tasks/FORMATS.md
7. Update queue.md
8. Record event in queue.md "Recent Events"
```

### 4.5 Email Sync Pipeline (`email_sync.py`)

The email sync pre-processor offloads deterministic matching work from the AI context window into Python, reducing context consumption by ~78%.

```
outlook_skill.py find-recent --days 1 --json
        │ JSON via stdout
        ▼
email_sync.py  (reads stdin → builds task index → matches → filters noise)
        │ Compact pre-matched markdown (~250 lines)
        ▼
Claude  (semantic judgment: scope validation, ask extraction, task updates)
```

#### Matching Signals (priority order)

| Signal | Confidence | How it works |
| ------ | ---------- | ------------ |
| Thread match | 1.0 | Email entry_id found in task's `<!-- email:XXX -->` timeline comments |
| Contact match | 0.8 | Sender/recipient email in task's Contacts or RACI table |
| Keyword+geo | 0.5+ | Subject/preview tokens overlap task keywords; geo agrees |

#### Keyword Scoring Weights

| Token type | Weight | Example |
| ---------- | ------ | ------- |
| EPD (plan row ID, 6-8 digits) | 3.0 | `1032769` — unique per task, highest discriminator |
| Alphanumeric codes | 1.5 | `DO288`, `IG291921` — course/PO codes |
| English words | 1.0 | `training`, `procurement` |
| Chinese 3+ char | 1.0 | `培训计划` |
| Chinese 2-char | 0.5 | `培训` — too common to score full weight |

#### Task Index Sources

`build_task_index()` extracts matching signals from each active task file:

- **`## Contacts`** section → email addresses, names (via `followup.parse_task_file()`)
- **RACI table** → additional `<email>` addresses and names not in Contacts
- **`## Tags`** → backtick-delimited curated keywords (e.g., `` `Red Hat`, `FNC India` ``)
- **`**EPD:**`** field → pure numeric plan row IDs (stored separately for weight boost)
- **Full content** → alphanumeric codes (`[A-Za-z]+\d+[\w]*`)
- **Timeline** → `<!-- email:ENTRY_ID -->` markers (for thread-match signal)

#### Subject Line Strategy (outgoing emails)

To maximize reply auto-matching, outgoing emails include the highest-priority identifier in the subject:

1. EPD: `[1032769] Red Hat Q3 TU Order` (weight 3.0 on all replies)
2. Course code: `DO288 Schedule Update — FNC India W5` (weight 1.5)
3. Vendor + geo: `Temenos TLC — China User Setup` (weight 1.0 each)

Replies inherit the subject → entire thread auto-matches back to the correct task.

---

### 4.6 Skills

Skills are **modular I/O implementations** that workflows call when they need to touch external systems.

#### Current skills

| Skill | Purpose | External system |
|-------|---------|-----------------|
| `outlook-com-skill` | Find/thread/compose/forward email | Microsoft Outlook (COM) |
| `minimax-xlsx` | Create/read/edit/analyze Excel files | `.xlsx`, `.xlsm`, `.csv` |
| `skill-creator` | Scaffold new skills | (meta) |

#### Skill structure

```
skills/
└── <skill-name>/
    ├── SKILL.md          # YAML frontmatter (name, description, triggers) + command reference
    └── [implementation]  # scripts/, backend/, etc. — varies per skill
```

### 4.7 Outlook Skill Architecture

The `outlook-com-skill` is a self-contained Python application that interfaces with Microsoft Outlook via COM. It is **decoupled from BrainClaw** — the skill has its own config, backend, and CLI and can run standalone.

```
skills/outlook-com-skill/
├── SKILL.md                  # Command reference & triggers for AI
├── scripts/
│   └── outlook_skill.py      # CLI entry point (all commands)
├── backend/
│   ├── config.py             # Centralized configuration
│   ├── email_search/         # Search engine
│   │   ├── unified_search.py # find, find-thread, find-related
│   │   ├── server_search.py  # Outlook SQL/AdvancedSearch
│   │   ├── email_listing.py  # find-recent
│   │   └── search_common.py  # Shared extraction utilities
│   ├── email_composition.py  # Compose & reply
│   ├── outlook_session/      # COM session management
│   └── ...
└── .gitignore
```

**CLI Commands:**

| Command | Purpose | Scope |
|---------|---------|-------|
| `find-recent` | Recent emails | Inbox (default) |
| `find` | Search by subject/sender/body | Inbox (default) |
| `find-thread` | All emails in conversation | Inbox + Sent Items (auto) |
| `find-related` | Cross-thread discovery | Inbox + Sent Items (auto) |
| `get-email` | Full email by entry_id | — |
| `compose` | Compose and send new email | — |
| `reply` | Reply to an email (default: reply-all; `--only`: From only) | — |
| `forward` / `redirect` | Forward/redirect an email | — |
| `batch-forward` | Mass BCC forward | — |

All send commands (`compose`, `reply`, `forward`, `redirect`) auto-output the sent email's `EntryID` after sending via the `_print_sent_entry_id()` helper. This enables workflows to capture the ID and write `<!-- email:ID -->` markers in task timeline entries.

**Design Principles:**
- **Decoupled**: No imports from BrainClaw. Works standalone with `py -3 scripts/outlook_skill.py`.
- **Workflow-agnostic**: Workflows reference skills abstractly ("use outlook-com-skill to find emails"); exact CLI commands are in SKILL.md.
- **Command convention**: All search uses `find-*` prefix (`find`, `find-recent`, `find-thread`, `find-related`).
- **Scope strategy**: Regular search defaults to Inbox only (sent emails are tracked in tasks); thread/related auto-include Sent Items.
- **Event detection**: Meeting invites detected via Outlook `MeetingStatus`; event announcements via subject/sender heuristics.

#### SKILL.md Template

```markdown
---
name: skill-name
description: One-line description
triggers: ["keyword1", "keyword2"]
operations: ["op1", "op2"]
---

# Skill Name

## Commands
### Command 1
### Command 2

## Example
```

### 4.8 Tasks

#### Task File Naming
```
T{ID}-{keyword1}-{keyword2}.md
```
- **ID**: 3-digit incrementing number (T001, T002...)
- **Keywords**: 2-4 keywords from content

#### Status System
| Symbol | Status | Description |
|--------|--------|-------------|
| 📋 | Not Started | Needs action |
| ⏳ | In Progress | Actively working |
| 🔴 | Blocked | Waiting on dependency |
| ✅ | Completed | Move to history/ |

#### Master-Subtask Organization
- **Master task**: Title contains "(Master)", has Subtasks field
- **Subtask**: Has "Parent Task: TXXX" field
- **Queue display**: Subtasks indented under master with `↳` prefix

### 4.9 Process Intelligence

#### How It Works
The process workflow connects tasks to operational processes:
1. **Match**: Task Category + Geo → process file (from `process/README.md` index)
2. **Track**: Scan task Current State → determine which step is complete
3. **Suggest**: Output next action + responsible contact
4. **Learn**: During email sync, detect steps not in existing process files
5. **Codify**: When ≥2 tasks follow the same undocumented pattern → suggest creating a process file

#### contacts.md Process Roles
A quick-reference table maps process steps to responsible contacts by geo, enabling instant lookup during auto-advance suggestions.

#### RACI in Tasks
Tasks include RACI matrix:
- **R** = Responsible (does the work)
- **A** = Accountable (decision maker)
- **C** = Consulted (provides input)
- **I** = Informed (kept updated)

### 4.10 Processes

Operational processes grouped by geography.

```
process/
├── README.md              # Process index
├── philippines/           # PH processes
├── china/                 # CN processes
└── global/                # Global processes
```

---

## 5. Extension Guide

### 5.1 Adding a New Skill

Skills are reserved for I/O against external systems. If a capability can be expressed as steps the AI follows by reading markdown, put it in a workflow instead.

1. **Confirm it needs a skill**: External system access (COM, file format, API)? → skill. Pure logic over existing files? → workflow.

2. **Create skill directory and SKILL.md**: `skills/<skill-name>/SKILL.md`

3. **Write SKILL.md**:
   ```markdown
   ---
   name: skill-name
   description: One-line description
   triggers: ["keyword1", "keyword2"]
   operations: ["op1", "op2"]
   ---

   # Skill Name
   ## Commands
   ## Example
   ```

4. **Reference from a workflow**: Add a step like `Call <skill-name> <command>` in the relevant workflow.

**Example**: A `calendar` skill would be justified (it talks to Outlook/Graph). A `process-suggest` skill would NOT — that's pure logic and belongs in `PROCESS_WORKFLOW.md`.

### 5.2 Adding a New Workflow

1. **Create workflow file**: `workflows/XXX_WORKFLOW.md`

2. **Define structure**:
   ```markdown
   # Workflow Name
   
   > One-line description
   
   ---
   
   ## Operation 1
   **Trigger:** ...
   **Steps:**
   1. ...
   
   ## Skills Used
   | Skill | Purpose |
   |-------|---------|
   ```

3. **Update `CLAUDE.md`** workflow table if adding new triggers

### 5.3 Adding a New Process

1. **Identify geo**: Determine which geo folder (`philippines/`, `china/`, `global/`) the process belongs to

2. **Create process file**: `process/{geo}/{descriptive-name}.md`
   ```markdown
   # Process Title

   **Effective:** YYYY-MM-DD
   **Geo:** Philippines | China | Global
   **Keywords:** comma, separated, matching, keywords

   ## When This Applies
   Brief description of trigger

   ## Steps
   1. **Action** — details

   ## Key Rules
   - Critical constraint
   ```

3. **Register in `process/README.md`** index — add one row filling Process / File / **Keywords** / Description columns. This is the single authoritative registration point: `scripts/shared_config.py` parses the README table at import time to build `PROCESS_MATCH_RULES` (used by followup/dashboard), so no script edits are needed. Do NOT hardcode process mappings anywhere else.

### 5.4 Adding a New Memory Type

1. **Create file**: `memory/[type].md`

2. **Define structure and purpose**

3. **Update `TASK_WORKFLOW.md`** memory types table (Event & Memory Recording section)

4. **Update `CLAUDE.md`** to load at startup

---

## 6. Design Principles

### 6.1 Separation of Concerns

| Layer | Responsibility | Example |
|-------|---------------|---------|
| System Prompt | Startup & loading rules | CLAUDE.md |
| Memory | Learned preferences & patterns | preferences, things_to_avoid, achievements |
| Workflows | Orchestration + business logic | TASK_WORKFLOW, EMAIL_WORKFLOW, PROCESS_WORKFLOW, REDHAT_WORKFLOW, VIEWS_WORKFLOW |
| Skills | I/O against external systems | outlook-com-skill, minimax-xlsx |
| Data | Persistence | Task files, contacts, processes |

**Key principle**: Workflows reference skills abstractly ("use outlook-com-skill to find thread"). Exact CLI commands live in `SKILL.md`. Skills are self-contained and project-agnostic.

### 6.2 On-Demand Loading

- **Do NOT load all skills at startup**
- Load workflow/skill **only when needed**
- Read files completely before execution

### 6.3 User Approval Required

- Sending emails/messages
- Completing tasks
- Deleting files
- Calendar changes
- Destructive operations

### 6.4 Memory-Driven Learning

- Read memory files at startup
- Learn from interactions
- Update memory after significant events
- Avoid repeated mistakes

### 6.5 Clickable References

Always format IDs as clickable links:
```
[T025](assistant_brain/tasks/T025-pmp-renewal-futurenow-q2.md)
[Beng PAULINO](assistant_brain/contacts.md)
```

---

## 7. Best Practices

### 7.1 File Naming

- **Tasks**: `T{ID}-{keyword1}-{keyword2}.md`
- **Stakeholders**: `SH{ID}-{name}.md`
- **Skills**: `skills/{domain}/{skill-name}/SKILL.md`
- **Processes**: `process/{geo}/{descriptive-name}.md`

### 7.2 Skill Triggers

- Use specific keywords
- Avoid generic terms
- Document in SKILL.md frontmatter
- Frontmatter is scanned at startup for trigger routing

### 7.3 Workflow Steps

- Always use `Call \`skill-name\`` format
- Be explicit about which skill performs each action
- Keep steps atomic and clear

### 7.4 Memory Recording

- Check thresholds before recording
- Get user approval for new memories
- Keep entries concise and actionable
- Review and clean periodically

### 7.5 Task Management

- Use correct status symbols
- Update status promptly
- Link related tasks
- Include RACI matrix for multi-stakeholder tasks

---

## 8. Startup Process

```
1. Run dashboard script (py -3 assistant_brain/scripts/dashboard.py)
2. Load memory files (preferences, things_to_avoid)
3. Load task context (queue.md, recurring_tasks.md)
4. Load contacts (contacts.md)
5. Load process index (process/README.md)
6. Query OS for local date/time
7. Archive old events
8. Parse recurring tasks
9. Scan skill frontmatter (skills/*/SKILL.md)
10. Output startup status
```

**Output Format**:
```
✅ Ready | [weekday] [date/time] | User: [Name] | OS: [OS Name]
• Skills: [count] ([list of skill names])
• Processes: [count] | Stakeholders: [count]
```
- **Count skills:** Count directories under `assistant_brain/skills/` that have a `SKILL.md`
- **List skills:** Extract `name:` from each skill's frontmatter
- Example: `• Skills: 3 (outlook-com-skill, minimax-xlsx, skill-creator)`

---

## 9. Future Enhancements

### Potential Additions
- Calendar integration skill
- Meeting notes workflow
- Project portfolio view
- Analytics dashboard
- Multi-language support

### Extension Points
- New skill domains
- Additional workflows
- Enhanced memory types
- Process versioning

---

## 10. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Skill not found | Check skills/*/SKILL.md frontmatter triggers |
| Workflow not loaded | Read workflow file before execution |
| Memory not persisting | Check recording threshold |
| Task ID conflict | Verify Last Task ID in queue.md header |

### Debug Tips
- Check file paths are relative to assistant_brain/
- Verify markdown syntax in all files
- Ensure frontmatter is properly formatted
- Check skill triggers match user input

---

**Last Updated:** 2026-06-09
**Version:** 1.3
