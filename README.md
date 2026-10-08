# BrainClaw - Personal Assistant System

**Bringing AI automation to non-technical office workers through AI IDEs.**

## Why BrainClaw?

OpenClaw and similar AI automation tools require technical setup (binaries, environment variables, command line) that creates barriers for regular office workers. Additionally, many corporate IT policies restrict installing such tools.

**BrainClaw solves this by:**
- Running inside AI IDEs that are already approved for corporate use
- Eliminating technical setup - just open a markdown file and start
- Providing natural language commands instead of scripts
- Learning user preferences through simple memory files

## Who Is This For?

- Office workers who want AI assistance but don't know programming
- Employees in corporate environments with restricted software installation
- Teams that want to automate Microsoft 365 tasks without coding
- Anyone who wants a personal assistant that learns their preferences

## Quick Start

### Setup (One-time)

1. Open your AI IDE (Claude, Cursor, etc.)
2. Go to custom instructions / system prompt settings
3. Use [`assistant_brain/prompts/SYSTEM_PROMPT.md`](assistant_brain/prompts/SYSTEM_PROMPT.md) as the canonical prompt. `AGENTS.md` and `CLAUDE.md` are generated compatibility copies for tools that auto-load those filenames
4. Set your workspace to the BrainClaw folder

### Reproducible developer setup (optional)

The core runtime uses the Python standard library. For tests and linting:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 assistant_brain/scripts/doctor.py
```

Optional extras are declared in `pyproject.toml`: `documents` for workbook/Word utilities and `outlook` for Windows Outlook COM.

> **Privacy:** Keep the real `assistant_brain/contacts.md` local. For a new environment, copy `assistant_brain/contacts.example.md` and populate it privately. If `contacts.md` was already tracked in an older clone, `.gitignore` alone does not remove it from the index or history; handle that as a separate privacy migration.

### Daily Use

1. Open your AI IDE
2. Say **"start"**, **"启动"**, or **"start assistant"** to activate the full assistant
3. The assistant loads brain files and is ready to help

(Greetings like "hi"/"你好" or generic phrases like "help me"/"帮我" do NOT auto-start the assistant — use an explicit trigger.)

**No installation. No configuration. No command line.**

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│  AI IDE (Claude / Cursor / etc.)                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  System Prompt (prompts/SYSTEM_PROMPT.md)               │  │
│  │  "On startup, read brain files..."                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Brain Files (assistant_brain/)                        │  │
│  │  ├── workflows/            (orchestration + logic)     │  │
│  │  │   ├── TASK_WORKFLOW.md                              │  │
│  │  │   ├── EMAIL_WORKFLOW.md                             │  │
│  │  │   ├── PROCESS_WORKFLOW.md                           │  │
│  │  │   ├── REDHAT_WORKFLOW.md                            │  │
│  │  │   └── VIEWS_WORKFLOW.md                             │  │
│  │  ├── skills/               (I/O — external systems)    │  │
│  │  │   ├── outlook_com_skill/    (Outlook COM backend)   │  │
│  │  │   ├── xlsx-ibm/            (Excel I/O)               │  │
│  │  │   ├── bluepage-skill/   (W3 Unified Profile)        │  │
│  │  │   ├── enrollment-downloader/ (Classroom rosters)    │  │
│  │  │   └── skill-creator/    (scaffold new skills)       │  │
│  │  ├── tasks/                (task queue)                │  │
│  │  └── process/              (operational processes)     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## What Can It Do?

| Feature | Description |
|---------|-------------|
| **Task Management** | Detailed task tracking with Status, Priority, Category, Geo, Due Time, RACI stakeholders, Parent-Child relationships, structured `Asks` (owed by me / owed to me) |
| **Task-First Rule** | When asked about a task's status, schedule, or progress, the system ALWAYS checks the task file first (the single source of truth) before checking email or other resources. |
| **Views Engine** | `status T###` (or bare `T###`), `owed`, `waiting`, `before {person}`, `digest`, `timesheet` — surface what's overdue, owed, and pending across all tasks |
| **Email Management** | Find, search, thread-track, and compose via native Outlook COM. Email sync uses a guarded pipeline: public Outlook-skill JSON contract -> fresh snapshot + metadata -> structured evidence bundle -> one semantic classifier decides ownership and emits a JSON plan -> Draft 2020-12 Schema/staleness validation -> atomic apply -> verified summary. ConversationID and EntryID support direct thread matching; unmatched mail is never auto-ignored. All send commands output EntryID for timeline tracking. |
| **Streamlined 4-Step Email Flow** | Mandatory sequential flow for replies/sends: 1. Get thread/context → 2. Read thread completely via `get-email` (No assumptions, no guessing) → 3. Draft the email (To/CC, Subject, Body as plain text; "no-redundancy" rule prevents repeating thread facts) → 4. Send ONLY after explicit, turn-specific user approval. |
| **Email Thread Tracking** | ConversationID-based continuity evidence — once an email is linked to a task, future messages in the same thread become strong candidates for semantic review |
| **Related Email Discovery** | Multi-strategy search (thread + sender + keyword) for cross-thread discovery |
| **Enrollment & Shortlisting** | Playwright-backed automated downloader of YourLearning classroom rosters. Evaluates registrations, automatically cross-references headcount databases, excludes duplicates/non-regular/non-geo staff, scores candidates by band/role, and exports beautifully highlighted, color-coded participant shortlists to Excel for LDM sharing. |
| **Blue Pages & Employee Lookup** | Queries CNUM, employee types, reporting structure (managers and direct reports), Slack handles, and active statuses via the IBM W3 Unified Profile/Blue Pages API. |
| **Process Intelligence** | Auto-match tasks to process templates, suggest next actions + contacts. Detect undocumented process steps during email sync and codify recurring patterns into process files |
| **Follow-up Automation** | Detect stale tasks, draft follow-up emails with tone-aware templates, track chase history |
| **Web Search & Browse** | Search the web, extract page content, crawl sites, deep research via Tavily MCP |
| **Weekly Digest** | Auto-generated weekly summary of task activity, completions, and key events |
| **Timesheet Generation** | Top-down hour allocation across tasks grouped by Geo → Category with EPD numbers |
| **Recurring Tasks** | Auto-create scheduled tasks (monthly reports, quarterly invoices, etc.) |
| **Office Documents** | Create/read/edit/analyze Excel files via `xlsx-ibm` skill |
| **Extensible Skills** | Add new capabilities through modular skill system |

## Skills

Skills are reserved for I/O against external systems. They are mounted as separate repositories under `assistant_brain/skills/` and are intentionally excluded from this repository. Business logic lives in workflow files directly.

| Skill | Purpose | External system |
|-------|---------|-----------------|
| **outlook_com_skill** | Find, thread, related, compose, reply, forward, redirect, batch-forward | Microsoft Outlook (COM) |
| **xlsx-ibm** | Create, read, edit, analyze Excel/spreadsheet files | `.xlsx`, `.xlsm`, `.csv` |
| **bluepage-skill** | Look up IBM employee profiles, Slack handles, reporting structures, active statuses | IBM Blue Pages (W3 Unified Profile API) |
| **enrollment-downloader** | Playwright-backed browser to download and shortlist classroom rosters | IBM YourLearning / E&C Manager |
| **skill-creator** | Scaffold a new skill | (meta) |

## Email Commands

All commands use the `find-*` naming convention:

| Command | Default Scope | Use Case |
|---------|--------------|----------|
| `find-recent` | Inbox only | Check what's new |
| `find` | Inbox only | Search by subject/sender/body |
| `find-thread` | Inbox + Sent Items | Pull entire conversation chain |
| `find-related` | Inbox + Sent Items | Discover cross-thread related emails |
| `get-email` | — | View full email by entry_id |
| `compose` / `reply` / `forward` / `redirect` | — | Send emails (all output EntryID after send) |

**Strategy:** Sent emails are tracked in task files (`## Email References`). `find` and `find-recent` default to Inbox only. Thread and related search auto-include Sent Items for completeness.

**EntryID Tracking:** All send commands (`compose`, `reply`, `forward`, `redirect`) automatically output the sent email's `EntryID` after sending. This enables reliable timeline tracking with `<!-- email:ID -->` markers in task files. Tracking follows unified **Key Email Criteria** (same for inbound and outbound): emails containing an ask/approval/decision/commitment, delivering/requesting a deliverable, representing a task milestone, or likely needing future reply/forward. Pure FYI acknowledgements ("noted", "thanks", "got it") are exempt.

**Email-to-Task Classification (model-centric):**

1. **Deterministic evidence preparation** - build the active-task catalog and collect EntryID, ConversationID, identifier, contact, lexical, and scope evidence.
2. **Semantic ownership decision** - one classifier reviews every non-noise item, including calendar and zero-candidate messages, and reads every plausible task file completely.
3. **Validated mutation** - the classifier writes a Schema-conforming plan with an explicit matching-metadata review; deterministic code validates freshness and atomically applies timeline, asks, fields, tags, contacts, RACI, notes, and ignore changes.

There are no artificial confidence scores or deterministic ownership thresholds. Candidate reasons are explicit evidence only. One email can update multiple tasks when its content contains independently supported events; uniqueness is enforced per `(task, entry_id)`. Each task update rechecks Scope, Exclude, Tags, Contacts/RACI, and identifiers so newly learned matching evidence is not stranded in timeline prose. Active task structure is validated by `validate_tasks.py` against `task_file.schema.json`. `latest-candidates.json` is the authoritative classifier input, while `latest.md` is a diagnostic rendering. Outgoing subjects should use recognizable public identifiers, but never EPD numbers or Class IDs. See [ARCHITECTURE.md section 4.5](ARCHITECTURE.md).

## Project Structure

Files marked with ⭐ are loaded at **startup**. Others are loaded **on-demand**.

```
BrainClaw/
├── AGENTS.md                     # Generated compatibility prompt
├── CLAUDE.md                     # Generated compatibility prompt
├── README.md                     # This file
├── README_CN.md                  # Chinese documentation
├── ARCHITECTURE.md               # System architecture
└── assistant_brain/
    ├── prompts/
    │   └── SYSTEM_PROMPT.md      # Canonical system prompt
    ├── views_config.md       ⭐  # View thresholds and defaults
    ├── recurring_tasks.md    ⭐  # Scheduled recurring tasks
    ├── contacts.md           ⭐  # Local/private people data
    ├── contacts.example.md       # Sanitized setup template
    ├── formats/
    │   ├── EMAIL_SYNC_FORMAT.md          # Email sync layout specification
    │   ├── email_sync_candidates.schema.json
    │   ├── email_sync_plan.schema.json
    │   └── task_file.schema.json         # Active-task contract
    ├── process/
    │   ├── README.md         ⭐  # Local process index
    │   └── process.schema.json   # Version-controlled process schema
    ├── workflows/                # Orchestration and business logic
    ├── scripts/                  # Allowlisted runtime/quality tools; task scripts stay local
    ├── skills/                   # Separate repositories; Git-ignored here
    └── tasks/                    # Local/private task files and history
```

## Commands

> Just say what you want in plain language — these are example phrasings, not rigid commands. The AI matches by intent, not exact keywords.

| What you want | Say something like... | What happens |
|---------------|------------------------|--------------|
| **Start the assistant** | "start", "启动", "start assistant" | Load brain files, render the full task list grouped by country → priority, with overdue tasks flagged |
| **Just greeting** | "hi", "你好", "help me", "帮我" | Quick greeting only — no auto-startup on ambiguous phrases |
| **Check one task's status** | "T033", "T033 状态", "查 T033", "T033 怎么样了", "看下 T033", "status T033" | Per-task view: current blocker, what's owed, recent decisions |
| **What did I promise / owe?** | "我欠谁啥", "待我处理", "我答应过啥", "我有啥没回的", "owed", "what do I owe" | Cross-task: my open promises, grouped by recipient, sorted by overdue |
| **Who's blocking me / haven't replied?** | "等待", "我在等谁", "啥事卡着", "谁还没回我", "waiting" | Cross-task: who owes me what, grouped by person, sorted by wait time |
| **Prep before a meeting** | "见 Beng 之前", "明天 and Mridul 开会前", "before Beng", "prep for X" | Pull all open items with that person + suggested agenda |
| **Corporate lookups** | "who is Beng", "bluepages HONG YANG", "reports to X" | Search profiles, Slack handles, roles, and teams via Blue Pages |
| **Class shortlisting** | "download roster T134", "check enrollment 10580795", "evaluate roster" | Connects via browser, downloads waitlist, cross-references and outputs styled Excel shortlisted rosters |
| **See full task list** | "show all", "全部任务", "完整队列" | Same output as startup — re-render the grouped task list |
| **Task operations** | "新建任务", "完成 T033", "block T040", "create/update/complete/block task" | Task lifecycle |
| **Process / next step** | "next step T033", "推进 T033", "下一步", "固化流程" | Match task to process template, suggest next action + contact; codify recurring patterns |
| **Follow-up / chase** | "follow up", "催办", "chase", "nudge T033", "提醒一下" | Detect stale tasks, draft follow-up emails with appropriate tone |
| **Email operations** | "查邮件", "找 X 的邮件", "draft email", "reply", "forward" | Email lifecycle (now with auto-extraction into tasks) |
| **Web search** | "search DO188", "搜索", "查一下", "look up", "查看网页" | Search the web or extract content from URLs via Tavily |
| **Weekly digest** | "digest", "周报", "weekly summary", "this week" | Auto-generated summary of task activity over the past 7 days |
| **Timesheet** | "timesheet", "工时", "time allocation" | Hour allocation across tasks grouped by Geo → Category |

## Task Management Features

BrainClaw provides enterprise-grade task tracking:

- **Rich Task Cards**: Status, Priority, Category, Geo, Due Time, Contact, Keywords, History, Notes
- **Auto-Detection**: Automatically determines Due Time and Priority from context
- **Smart Keywords**: 2-3 unique identifiers (Request IDs, full names, specific codes) for easy source tracing
- **History Tracking**: Cumulative record of all task updates with timestamp and source
- **Parent-Child Tasks**: Master tasks can have subtasks for complex project management
- **Geographic Tracking**: Track tasks by region (Philippines, India, China, Singapore, APAC, Global)
- **Recurring Tasks**: Auto-create scheduled tasks (monthly reports, quarterly processes)
- **Email References**: Tasks link to related emails via Outlook entry_id for instant lookup

### Keywords System

BrainClaw uses a smart keyword system to help you trace tasks back to their source:

- **What**: 2-3 unique identifiers per task (Request IDs, full names, specific codes)
- **Why**: Quickly find the original email/document that created the task
- **How**: Avoid generic terms, use specific identifiers only

**Examples:**
- ✅ Good: `CRT282911, Ashish Sah, Platform Developer II` → finds exact email
- ✅ Good: `Req 11695, Informatica PowerCenter` → unique request
- ❌ Bad: `certification, approval, Salesforce` → finds hundreds of emails

## Architecture: Workflows & Skills

BrainClaw uses a layered architecture with clear separation of concerns:

```
assistant_brain/prompts/SYSTEM_PROMPT.md (canonical rules)
        ↓ generated compatibility copies: AGENTS.md + CLAUDE.md
        ↓
┌──────────────────────────────────────────┐
│    Workflows (orchestration + logic)     │  ← All business logic lives here
│  - TASK_WORKFLOW                         │     Process matching, auto-advance,
│  - EMAIL_WORKFLOW                        │     keyword extraction, composition
│  - PROCESS_WORKFLOW                      │     guidelines, process learning & codification,
│  - REDHAT_WORKFLOW                       │     digest & timesheet generation,
│  - VIEWS_WORKFLOW                        │     views (status/owed/waiting/...),
│                                         │     Red Hat audience targeting & shortlist
└──────────────┬───────────────────────────┘
               ↓ (only when external I/O needed)
┌──────────────────────────────────────────┐
│   Skills (I/O — external systems)        │
│  - outlook_com_skill/  Outlook COM       │
│  - xlsx-ibm/   Excel files           │
│  - bluepage-skill/  Blue Pages API       │
│  - enrollment-downloader/  YourLearning  │
│  - skill-creator/  meta                  │
└──────────────────────────────────────────┘
```

**Key Principle:** Workflows hold all business logic in markdown so the AI can read and follow it. Skills exist only where real code is required to talk to an external system. Both are loaded **on-demand**.

## System Capabilities & Limitations

### What It Can Do

| Capability | Description |
|------------|-------------|
| **State Persistence** | File-based storage keeps memory, logs, and config across sessions |
| **Interactive Response** | Execute tasks when triggered by user (request-response pattern) |
| **Modular Extension** | Add new capabilities through `skills/` without modifying core |
| **Web Search & Browse** | Search the web, extract pages, deep research via Tavily MCP server |
| **Local Autonomy** | All data stays local; no external services required (except AI IDE + Tavily API) |
| **Learning System** | Learns from interactions and updates memory files |
| **Process Management** | Structured process tracking grouped by geography |
| **Scheduled Tasks** | Recurring tasks auto-trigger on schedule |
| **Native Outlook** | Direct Outlook COM integration — no cloud, no API keys |

### What It Cannot Do

| Limitation | Reason |
|------------|--------|
| **Autonomous Execution** | No independent process; requires user presence |
| **Background Operations** | No daemon; no continuous monitoring |
| **Remote Access** | No API endpoint; cannot be triggered from IM or external systems |

### System Nature

```
BrainClaw = Stateful Request-Response System
         ≠ Continuously Running System
```

**Core Constraint: No process, only conversation.**

## Language Support

- **Files**: English (for consistency)
- **Commands**: English + Chinese
- **User content**: Any language

## Philosophy

> "AI should be accessible to everyone, not just developers."

BrainClaw bridges the gap between powerful AI tools and everyday office workers. By using AI IDEs as the interface, we bypass traditional barriers while keeping the capabilities users need.

---
*Built with the belief that AI should serve everyone, not just the technical elite.*
