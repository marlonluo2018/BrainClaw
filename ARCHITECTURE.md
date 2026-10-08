# BrainClaw System Architecture

> Personal AI Assistant System Design Document

---

## 1. System Overview

BrainClaw is a personal AI assistant system designed for office productivity. It uses a **Brain File System** architecture where knowledge, workflows, and skills are stored as markdown files, enabling the AI to read and execute operations dynamically.

### Key Features
- **Workflow orchestration**: Multi-step operations guided by workflow files
- **Skill-based extensibility**: Modular skills for specific functionalities
- **Task management**: Comprehensive task tracking with RACI stakeholder mapping
- **Process awareness**: Company-specific operational processes

---

## 2. Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Canonical Prompt                         │
│       assistant_brain/prompts/SYSTEM_PROMPT.md               │
│          Startup & On-Demand Loading Rules                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Brain Files                               │
│  ┌──────────────────────────────────────────┐              │
│  │         Core Context & Tasks             │              │
│  │  contacts | tasks | process definitions  │              │
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
│       Skills Layer (I/O - separate repositories)            │
│  outlook_com_skill | xlsx-ibm | docx-ibm | pptx-ibm         │
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
├── AGENTS.md                     # Generated tool-compatible prompt copy
├── CLAUDE.md                    # Generated tool-compatible prompt copy
├── README.md                     # User documentation (EN)
├── README_CN.md                  # User documentation (CN)
├── ARCHITECTURE.md               # This file
│
├── assistant_brain/              # Core brain directory
│   ├── prompts/SYSTEM_PROMPT.md  # Canonical system prompt
│   ├── recurring_tasks.md        # Recurring task definitions
│   ├── views_config.md           # View thresholds & display config
│   │
│   ├── workflows/                # Orchestration + business logic
│   │   ├── TASK_WORKFLOW.md
│   │   ├── EMAIL_WORKFLOW.md
│   │   ├── PROCESS_WORKFLOW.md
│   │   ├── REDHAT_WORKFLOW.md
│   │   └── VIEWS_WORKFLOW.md
│   │
│   ├── scripts/                  # Allowlisted runtime and quality tooling
│   │   ├── dashboard.py          # Startup display, taskboard, pending, digest, timesheet
│   │   ├── run_email_sync.py     # Stable Outlook sync entry point
│   │   ├── email_sync.py         # Structured evidence orchestration + Schema validation
│   │   ├── email_sync_catalog.py # Task catalog and archived thread markers
│   │   ├── email_sync_candidates.py # Candidate evidence + diagnostic rendering
│   │   ├── email_sync_apply.py   # Schema validation + atomic plan application
│   │   ├── update_task.py        # Idempotent structured task mutations
│   │   ├── followup.py           # Stale task detection for follow-up workflow
│   │   ├── generate_prompts.py   # Regenerate AGENTS.md and CLAUDE.md
│   │   ├── validate_processes.py # Process Schema/index validation
│   │   ├── validate_tasks.py     # Active-task Markdown -> Draft 2020-12 validation
│   │   ├── check_links.py        # Local Markdown link validation
│   │   └── doctor.py             # Local environment diagnostics
│   │
│   ├── skills/                   # Separate repositories mounted here (Git-ignored)
│   │   ├── outlook_com_skill/    # Outlook COM (find/thread/compose)
│   │   ├── xlsx-ibm/             # Excel file I/O
│   │   ├── docx-ibm/             # Word document I/O
│   │   └── ...                   # Other independently versioned skills
│   │
│   ├── tasks/                    # Task management
│   │   ├── FORMATS.md            # Task format spec
│   │   ├── T001-xxx.md           # Active task files (scanned directly)
│   │   └── history/              # Completed tasks
│   │
│   ├── contacts.md               # Local/private people data
│   ├── contacts.example.md       # Sanitized version-controlled template
│   │
│   ├── process/                  # Operational processes (by geo)
│   │   ├── README.md             # Process index
│   │   ├── process.schema.json   # Version-controlled metadata schema
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

### 4.1 Canonical System Prompt

**Purpose**: Single source of truth for all system rules — identity, values, user config, operational rules, workflow routing, on-demand loading gates.

All behavioral rules, user config, and operational policies live in `assistant_brain/prompts/SYSTEM_PROMPT.md`. Run `py -3 assistant_brain/scripts/generate_prompts.py` to generate `AGENTS.md` and `CLAUDE.md`, which are compatibility copies for tools that auto-load those filenames. Workflows and skills are loaded on demand per the canonical routing table.

### 4.2 Workflows

Workflows hold **all business logic** and step-by-step procedures. They orchestrate work and call I/O skills directly when external system access is needed.

| Workflow | Purpose | I/O Skills Used |
|----------|---------|-----------------|
| `TASK_WORKFLOW.md` | Task CRUD, keyword extraction, event recording | (none — pure file ops) |
| `EMAIL_WORKFLOW.md` | Email processing, geo detection, composition rules, email→task asks/decisions extraction, Key Email Criteria for EntryID tracking, stale-task follow-up | `outlook_com_skill` |
| `PROCESS_WORKFLOW.md` | Process matching, auto-advance suggestions, process learning from email patterns, codification | (none — pure file ops) |
| `REDHAT_WORKFLOW.md` | Red Hat audience targeting & shortlisting (4-phase lifecycle, course exclusion tables) | `redhat-audience-processor`, `enrollment-downloader`, `outlook_com_skill` |
| `VIEWS_WORKFLOW.md` | Per-task and cross-task views: status, owed, waiting, before, digest, timesheet | (none — pure file ops) |

**Design Pattern:**
```markdown
## Operation Name

**Trigger:** When to execute

**Steps:**
1. Action → (inline business logic, e.g. scan active `tasks/T*.md`)
2. Action → Call `outlook_com_skill` find-recent
3. ...
```

### 4.3 Runtime and Quality Scripts

`assistant_brain/scripts/` is private by default and uses an explicit `.gitignore` allowlist for reviewed, reusable runtime entry points and quality gates without embedded task/contact datasets. Task-specific delivery scripts remain local. Root `/scripts/` is reserved for disposable local experiments and remains Git-ignored. See `assistant_brain/scripts/README.md` for the classification and promotion policy.

Key quality commands validate generated prompts, process metadata/index integrity, active task structure/matching metadata, local Markdown links, tests, lint, and Python syntax. `validate_tasks.py` extracts Markdown into a structured record and executes `task_file.schema.json`; `doctor.py` runs these local readiness checks without requiring Outlook.

### 4.4 Workflow vs Skill — Division of Responsibility

| Aspect | Workflow | Skill |
|--------|----------|-------|
| **Role** | **Orchestrator + business logic** | **I/O against external systems** |
| **Content** | Step sequence, decision rules, process matching, format rules | CLI commands, file format readers/writers |
| **Examples** | "Create Task," "Next Step," "Codify Process" | Read Outlook inbox, parse .xlsx |
| **Coupling** | Project-specific (knows about tasks/, process/, views config) | Project-agnostic (no BrainClaw imports) |

**Why this split:** Business logic that is markdown-readable belongs in workflows so the AI can read and follow it without code execution. External-system I/O (COM, file formats, APIs) requires real code, so it lives in skills.

**Example — Creating a Task** (entirely workflow-resident; no I/O skill needed):

```markdown
# TASK_WORKFLOW.md → Create Task
1. Scan active and archived task filenames → Get highest Task ID, increment
2. Extract keywords (rules in workflow itself)
3. Match contacts against contacts.md, suggest RACI
4. Present RACI matrix → Get user confirmation
5. Generate filename: T{ID}-{kw1}-{kw2}.md
6. Write task file using template from tasks/FORMATS.md
7. Let `dashboard.py` derive active views directly from task metadata
8. Let `dashboard.py` derive recent events directly from task timelines
```

### 4.5 Email Sync Pipeline

Email sync separates three concerns: deterministic evidence collection, model-based semantic judgment, and deterministic mutation.

```text
run_email_sync.py [--days N]   # exactly once after each explicit full-sync trigger
        | public outlook_com_skill find-recent --json contract
        | fresh Outlook fetch -> latest-input.json + latest-meta.json
        v
email_sync.py
        | builds a structured active-task catalog
        | collects EntryID, ConversationID, identifier, contact, lexical, and scope evidence
        | filters only strict noise and exact semantic-ignore EntryIDs
        | writes latest-candidates.json + diagnostic latest.md
        v
exactly one email-classifier
        | semantically reviews every review item, including calendar and zero-candidate mail
        | reads every plausible task file and exact key/outbound messages
        | may link one email to multiple tasks when the content supports it
        | writes latest-plan.json against email_sync_plan.schema.json
        v
email_sync_apply.py
        | executes Draft 2020-12 JSON Schema validation
        | rejects stale/mismatched snapshots and invalid cross-record relationships
        | requires a five-part matching_review audit on every task update
        | atomically applies timeline, asks, fields, tags, contacts, RACI, notes, and ignore changes
        | writes latest-applied.json
        v
classifier verifies files and renders summary from applied results
```

`latest-candidates.json` is the classifier's authoritative input. `latest.md` is only a human-readable diagnostic rendering. There is no fallback or reprocessing mode: a failed fetch stops the sync, and `email_sync_apply.py` rejects any plan that leaves a `review` email without an outcome.

#### Evidence contract, not heuristic ownership

The deterministic layer never emits confidence scores and never decides task ownership. It records explicit evidence:

| Evidence | Meaning |
| -------- | ------- |
| Exact EntryID | The message is already recorded in a task timeline |
| ConversationID | The Outlook thread is already associated with one or more tasks |
| Identifier overlap | Stable course, certification, PO, EPD, or other business identifiers overlap |
| Contact overlap | Sender or recipient appears in task Contacts/RACI |
| Lexical overlap | Subject/preview terms help retrieve plausible tasks; they are not a match decision |
| Scope warning | Exclusion terms or date-window differences require model review; they never auto-reject |

Every non-noise, non-ignored message remains visible to the classifier, even when no candidate task is retrieved. Calendar items use the same path as normal mail. A single email may legitimately update multiple task files; the apply invariant is unique `(task, entry_id)`, while the same EntryID still cannot be both task-updated and ignored/unresolved.

#### Task catalog sources

`build_task_catalog()` extracts evidence from each active task file:

- **`## Contacts`** and RACI tables -> addresses, names, and roles
- **`## Tags`**, title, category, and positive scope -> retrieval terms
- **`**EPD:**`** and alphanumeric course/cert identifiers -> stable identifiers
- **`**Exclude:**`** / `NOT` scope clauses -> warnings for semantic review
- **Timeline** -> `<!-- email:ENTRY_ID -->` and `<!-- conversation:CONVERSATION_ID -->` markers

Every update re-audits those sources. New identifiers, aliases, participants, responsibilities, task boundaries, exclusions, geo/category/due changes, and thread IDs are promoted into their structured fields instead of remaining only in timeline prose.

#### Subject line strategy (outgoing emails)

Outgoing subjects should contain clear public identifiers while protecting internal administrative data. Never put EPD numbers or Class IDs in subjects. Prefer a course code, vendor/geo label, or recognizable topic so future replies provide useful thread and identifier evidence.

---

### 4.6 Skills

Skills are **modular I/O implementations** that workflows call when they need to touch external systems.

#### Common mounted skills

Skill directories are separate repositories and may vary by installation. The current workspace mounts examples including:

| Skill | Purpose | External system |
|-------|---------|-----------------|
| `outlook_com_skill` | Find/thread/compose/forward email | Microsoft Outlook (COM) |
| `xlsx-ibm` | Create/read/edit/analyze Excel files | `.xlsx`, `.xlsm`, `.csv` |
| `docx-ibm` / `pptx-ibm` | Create and edit Office documents | `.docx`, `.pptx` |
| `bluepage-skill` | Look up employee profile data | IBM Blue Pages |
| `enrollment-downloader` | Download classroom rosters | IBM YourLearning |
| `redhat-audience-processor` | Process Red Hat audience data | Local files |
| `business-process` | Process-related utilities | Local files |
| `skill-creator` | Scaffold new skills | (meta) |

#### Skill structure

```
skills/
└── <skill-name>/
    ├── SKILL.md          # YAML frontmatter (name, description, triggers) + command reference
    └── [implementation]  # scripts/, backend/, etc. — varies per skill
```

### 4.7 Outlook Skill Architecture

The `outlook_com_skill` is a self-contained Python application that interfaces with Microsoft Outlook via COM. It is **decoupled from BrainClaw** — the skill has its own config, backend, and CLI and can run standalone.

```
skills/outlook_com_skill/
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
- **Workflow-agnostic**: Workflows reference skills abstractly ("use outlook_com_skill to find emails"); exact CLI commands are in SKILL.md.
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

#### Task-file contract and validation

New active tasks require Category, Geo, Due, EPD, positive Scope, explicit Exclude, 1–4 discriminating Tags, verified contact addresses, RACI, Asks, Timeline, Current State, and Notes. Email-sourced timeline entries preserve exact source time, direction, EntryID, and ConversationID when Outlook provides it. `validate_tasks.py` enforces the versioned Draft 2020-12 contract; legacy timeline entries missing ConversationID remain warnings.

Structured mutations use `update_task.py`. Each mutation carries `matching_review` states for Scope, Exclude, Tags, Contacts, and Identifiers, making metadata maintenance explicit and auditable.

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
├── process.schema.json   # Version-controlled metadata schema
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

3. **Update `assistant_brain/prompts/SYSTEM_PROMPT.md`** if adding new global triggers, then regenerate compatibility copies

### 5.3 Adding a New Process

1. **Identify geo**: Determine which geo folder (`philippines/`, `china/`, `global/`) the process belongs to

2. **Create process file**: `process/{geo}/{descriptive-name}.md`
   ```markdown
   ---
   id: global-process-name
   version: 1
   effective: YYYY-MM-DD
   geo: Global
   status: active
   keywords:
     - specific keyword
   ---

   # Process Title

   ## When This Applies
   Brief description of trigger

   ## Steps
   1. **Action** — details

   ## Key Rules
   - Critical constraint
   ```

3. **Register in `process/README.md`** index — add one row filling Process / File / **Keywords** / Description columns. This is the single authoritative registration point: `scripts/shared_config.py` parses the README table at import time to build `PROCESS_MATCH_RULES` (used by followup/dashboard), so no script edits are needed. Do NOT hardcode process mappings anywhere else.

---

## 6. Design Principles

### 6.1 Separation of Concerns

| Layer | Responsibility | Example |
|-------|---------------|---------|
| System Prompt | Startup & loading rules | `prompts/SYSTEM_PROMPT.md` (generated to AGENTS/CLAUDE) |
| Workflows | Orchestration + business logic | TASK_WORKFLOW, EMAIL_WORKFLOW, PROCESS_WORKFLOW, REDHAT_WORKFLOW, VIEWS_WORKFLOW |
| Skills | I/O against external systems | outlook_com_skill, xlsx-ibm, docx-ibm, pptx-ibm |
| Data | Persistence | Task files, contacts, processes |

**Key principle**: Workflows reference skills abstractly ("use outlook_com_skill to find thread"). Exact CLI commands live in `SKILL.md`. Skills are self-contained and project-agnostic.

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

### 6.4 Clickable References

Always format IDs as clickable links:
```
[T025](assistant_brain/tasks/history/2026-Q2/T025-pmp-renewal-futurenow-q2.md)
`Beng PAULINO` (resolve private contact details from local `assistant_brain/contacts.md`)
```

---

## 7. Best Practices

### 7.1 File Naming

- **Tasks**: `T{ID}-{keyword1}-{keyword2}.md`
- **Skills**: `assistant_brain/skills/{skill-name}/SKILL.md` (separate repository)
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

### 7.4 Task Management

- Use correct status symbols
- Update status promptly
- Link related tasks
- Include RACI matrix for multi-stakeholder tasks

---

## 8. Startup Process

```
1. Run dashboard script (py -3 assistant_brain/scripts/dashboard.py)
2. Scan active `tasks/T*.md` files and recent archived metadata
3. Load recurring task definitions
4. Read local contacts/process files only when required
5. Query OS for local date/time
6. Output startup status
```

**Output Format**:
```
✅ Ready | [weekday] [date/time] | User: [Name] | OS: [OS Name]
• Skills: [count] ([list of skill names])
• Processes: [count] | Stakeholders: [count]
```
- **Count skills:** Count directories under `assistant_brain/skills/` that have a `SKILL.md`
- **List skills:** Extract `name:` from each skill's frontmatter

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
| Task ID conflict | Scan active and archived `T*.md` files for duplicate/highest IDs |

### Debug Tips
- Check file paths are relative to assistant_brain/
- Verify markdown syntax in all files
- Ensure frontmatter is properly formatted
- Check skill triggers match user input

---

**Last Updated:** 2026-09-22
**Version:** 1.3
