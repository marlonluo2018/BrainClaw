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
3. Paste the content of [`CLAUDE.md`](CLAUDE.md) (Claude Code auto-loads it; other IDEs need it pasted manually)
4. Set your workspace to the BrainClaw folder

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
│  │  System Prompt  (CLAUDE.md)                            │  │
│  │  "On startup, read brain files..."                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Brain Files (assistant_brain/)                        │  │
│  │  ├── SOUL.md               (identity & values)         │  │
│  │  ├── OPERATIONAL_RULES.md  (strategies)                │  │
│  │  ├── CONFIG.md             (parameters)                │  │
│  │  ├── workflows/            (orchestration + logic)     │  │
│  │  │   ├── TASK_WORKFLOW.md                              │  │
│  │  │   ├── EMAIL_WORKFLOW.md                             │  │
│  │  │   ├── PROCESS_WORKFLOW.md                            │  │
│  │  │   ├── FOLLOWUP_WORKFLOW.md                          │  │
│  │  │   ├── RECORDING_WORKFLOW.md                         │  │
│  │  │   ├── WEB_WORKFLOW.md                               │  │
│  │  │   └── VIEWS_WORKFLOW.md                             │  │
│  │  ├── skills/               (I/O — external systems)    │  │
│  │  │   ├── outlook-skill/    (Outlook COM backend)       │  │
│  │  │   ├── minimax-xlsx/     (Excel I/O)                 │  │
│  │  │   └── skill-creator/    (scaffold new skills)       │  │
│  │  ├── tasks/                (task queue)                │  │
│  │  ├── memory/               (preferences)               │  │
│  │  └── process/              (operational processes)      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## What Can It Do?

| Feature | Description |
|---------|-------------|
| **Task Management** | Detailed task tracking with Status, Priority, Category, Geo, Due Time, RACI stakeholders, Parent-Child relationships, structured `Asks` (owed by me / owed to me) |
| **Views Engine** | `status T###` (or bare `T###`), `owed`, `waiting`, `before {person}`, `review`, `digest`, `timesheet` — surface what's overdue, owed, and 述职-worthy across all tasks |
| **Email Management** | Find, search, thread-track, compose emails via native Outlook COM. Three-tier matching: ConversationID thread → task contacts → keyword+geo. Auto-extracts asks/decisions/deadlines into task slots |
| **Email Thread Tracking** | ConversationID-based thread matching — once an email is linked to a task, all future emails in the same thread auto-match |
| **Related Email Discovery** | Multi-strategy search (thread + sender + keyword) for cross-thread discovery |
| **Memory System** | Preferences, cognitive blind-spot patterns, contacts, achievements (述职 fact base) |
| **Achievement Auto-capture** | Task completion prompts the AI to extract 述职 material from `[decision]` / `[milestone]` / `[delivery]` Timeline entries |
| **Process Intelligence** | Auto-match tasks to process templates, suggest next actions + contacts. Detect undocumented process steps during email sync and codify recurring patterns into process files |
| **Follow-up Automation** | Detect stale tasks, draft follow-up emails with tone-aware templates, track chase history |
| **Web Search & Browse** | Search the web, extract page content, crawl sites, deep research via Tavily MCP |
| **Weekly Digest** | Auto-generated weekly summary of task activity, completions, and key events |
| **Timesheet Generation** | Top-down hour allocation across tasks grouped by Geo → Category with EPD numbers |
| **Recurring Tasks** | Auto-create scheduled tasks (monthly reports, quarterly invoices, etc.) |
| **Office Documents** | Create/read/edit/analyze Excel files via `minimax-xlsx` skill |
| **Extensible Skills** | Add new capabilities through modular skill system |

## Skills

Skills are reserved for I/O against external systems. Business logic (task lifecycle, RACI, event recording, email composition rules) lives in workflow files directly.

| Skill | Purpose | External system |
|-------|---------|-----------------|
| **outlook-skill** | Find, thread, related, compose, reply, batch-forward | Microsoft Outlook (COM) |
| **minimax-xlsx** | Create, read, edit, analyze Excel/spreadsheet files | `.xlsx`, `.xlsm`, `.csv` |
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

**Strategy:** Sent emails are tracked in task files (`## Email References`). `find` and `find-recent` default to Inbox only. Thread and related search auto-include Sent Items for completeness.

**Email↔Task Matching (3-tier priority):**
1. **Thread match** — email's ConversationID already in a task's Email References → instant hit
2. **Contact match** — sender appears in a task's `## Contacts` section → high confidence
3. **Keyword + geo** — fallback to keyword overlap + email domain geo detection

## Project Structure

Files marked with ⭐ are loaded at **startup**. Others are loaded **on-demand**.

```
BrainClaw/
├── CLAUDE.md                           # System prompt (single source of truth)
├── README.md                           # This file
├── README_CN.md                        # Chinese documentation
├── ARCHITECTURE.md                     # System architecture
└── assistant_brain/
    ├── SOUL.md               ⭐ # Identity & values (unchanging core)
    ├── OPERATIONAL_RULES.md  ⭐ # Core operational strategies
    ├── CONFIG.md             ⭐ # System parameters (user info, formats)
    ├── views_config.md       ⭐ # Thresholds + defaults for view ops
    ├── recurring_tasks.md    ⭐ # Scheduled recurring tasks
    ├── process/
    │   └── README.md         ⭐ # Process index (grouped by geo)
    ├── workflows/               # Orchestration + business logic (on-demand)
    │   ├── TASK_WORKFLOW.md
    │   ├── EMAIL_WORKFLOW.md
    │   ├── PROCESS_WORKFLOW.md        # Process matching, auto-advance, learning
    │   ├── FOLLOWUP_WORKFLOW.md       # Chase / nudge / remind stakeholders
    │   ├── RECORDING_WORKFLOW.md
    │   ├── WEB_WORKFLOW.md            # Web search & page extraction (Tavily)
    │   └── VIEWS_WORKFLOW.md           # status/owed/waiting/before/review
    ├── contacts.md          ⭐ # Single source of truth for people (tone, email, role, process roles)
    ├── scripts/                 # Python automation scripts
    │   ├── dashboard.py            # Startup display, taskboard, pending, digest, timesheet
    │   └── followup.py             # Stale task detection for follow-up workflow
    ├── memory/                  # User-derived data (learned over time)
    │   ├── preferences.md       ⭐ # User preferences (tone, time format, etc.)
    │   ├── things_to_avoid.md   ⭐ # Cognitive blind-spot patterns + tactical Don'ts
    │   ├── achievements.md         # 述职 fact base (auto-fed from Complete Task)
    │   └── vendor-accounts.md      # Vendor portal accounts & credentials
    ├── skills/                  # I/O against external systems
    │   ├── outlook-skill/        # Outlook COM — Python backend + CLI
    │   │   ├── SKILL.md          #   Command reference
    │   │   ├── scripts/          #   CLI entry point
    │   │   └── backend/          #   Search, compose, session mgmt
    │   ├── minimax-xlsx/         # Excel/spreadsheet I/O
    │   └── skill-creator/        # Scaffold new skills
    └── tasks/                   # Task queue & history
        ├── queue.md          ⭐ # Active tasks + Recent Events
        ├── FORMATS.md            # Task format specification
        ├── T0xx-xxx.md           # Active task details (on-demand)
        └── history/              # Completed tasks & monthly archives
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
| **Prep before a meeting** | "见 Beng 之前", "明天和 Mridul 开会前", "before Beng", "prep for X" | Pull all open items with that person + suggested agenda |
| **Performance review / 述职** | "述职", "半年述职", "Q2 做了啥", "总结这半年", "review Q2 2026" | Bullet summary + narrative draft from achievements.md |
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

## Memory System

BrainClaw learns and remembers across sessions:

| Memory File | Purpose |
|-------------|---------|
| `memory/preferences.md` | User preferences (timezone, tone, time format) |
| `memory/things_to_avoid.md` | **Patterns** (cognitive blind spots) + **Tactical Don'ts** (output-format mistakes) |
| `memory/achievements.md` | 述职 fact base — auto-fed from Complete Task; 2-axis structure (quarter × category) |
| `memory/vendor-accounts.md` | Vendor portal accounts & credentials reference |
| `views_config.md` | (NOT memory — system config) Thresholds + defaults for view ops. Lives at `assistant_brain/` root, not in memory/. |

## Architecture: Workflows & Skills

BrainClaw uses a layered architecture with clear separation of concerns:

```
CLAUDE.md (Startup rules)
        ↓
OPERATIONAL_RULES.md (Core policies)
        ↓
┌──────────────────────────────────────────┐
│    Workflows (orchestration + logic)     │  ← All business logic lives here
│  - TASK_WORKFLOW                         │     Process matching, auto-advance,
│  - EMAIL_WORKFLOW                        │     keyword extraction, composition
│  - PROCESS_WORKFLOW                      │     guidelines, achievement extraction,
│  - FOLLOWUP_WORKFLOW                     │     process learning & codification,
│  - RECORDING_WORKFLOW                    │     follow-up automation, web search,
│  - WEB_WORKFLOW                          │     digest & timesheet generation,
│  - VIEWS_WORKFLOW                        │     views (status/owed/waiting/...)
└──────────────┬───────────────────────────┘
               ↓ (only when external I/O needed)
┌──────────────────────────────────────────┐
│   Skills (I/O — external systems)        │
│  - outlook-skill/  Outlook COM           │
│  - minimax-xlsx/   Excel files           │
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
