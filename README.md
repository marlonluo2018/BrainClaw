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
3. Paste the content of [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md)
4. Set your workspace to the BrainClaw folder

### Daily Use

1. Open your AI IDE
2. Say **"start"** or **"启动"** to activate the full assistant
3. The assistant loads brain files and is ready to help

(Or just say "hi"/"你好" for a quick greeting without full startup)

**No installation. No configuration. No command line.**

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  AI IDE (Claude / Cursor / etc.)                    │
│  ┌───────────────────────────────────────────────┐  │
│  │  Custom System Prompt                         │  │
│  │  (SYSTEM_PROMPT.md)                          │  │
│  │                                               │  │
│  │  "On startup, read brain files..."           │  │
│  │  "Commands: start, hi..."                    │  │
│  └───────────────────────────────────────────────┘  │
│                        ↓                            │
│  ┌───────────────────────────────────────────────┐  │
│  │  Brain Files (assistant_brain/)               │  │
│  │  ├── SOUL.md               (identity & values)         │  │
│  │  ├── OPERATIONAL_RULES.md  (strategies & rules)        │  │
│  │  ├── CONFIG.md             (system parameters)         │  │
│  │  ├── recurring_tasks.md    (scheduled tasks)           │  │
│  │  ├── memory/      (learned preferences & policies)     │  │
│  │  ├── skills/      (modular capabilities)               │  │
│  │  └── tasks/       (task queue & history)               │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## What Can It Do?

| Feature | Description |
|---------|-------------|
| **Task Management** | Detailed task tracking with Status, Priority, Category, Geo, Due Time, Keywords, History, Parent-Child relationships |
| **Email Management** | Check, send, reply, forward emails via Microsoft Graph Skill |
| **Calendar Management** | Schedule meetings, check availability, manage events |
| **Memory System** | Learns preferences, remembers contacts, tracks things to avoid, maintains policy index |
| **Policy Management** | Structured policy files with indexing and reference system |
| **Recurring Tasks** | Auto-create scheduled tasks (monthly reports, quarterly invoices, etc.) |
| **Office Documents** | Create/edit Word, Excel, PowerPoint files via OfficeCLI skill |
| **Keyword Extraction** | Automatically extract relevant keywords from emails and documents |
| **Extensible Skills** | Add new capabilities through modular skill system |

## Skills

BrainClaw includes 4+ built-in skills:

| Skill | Purpose |
|-------|---------|
| **keyword-extraction** | Extract priority-ordered keywords from any text |
| **microsoft-graph-skill** | Email, calendar, and user operations via Microsoft Graph API |
| **OfficeCLI** | Create/edit Office documents (.docx, .xlsx, .pptx) with 7 specialized sub-skills |
| **skill-creator** | Create new skills for any workflow or automation need |

### OfficeCLI Sub-Skills
- officecli-docx - Word documents (reports, letters, memos)
- officecli-academic-paper - Research papers with TOC, equations, footnotes
- officecli-pptx - Presentations and slide decks
- officecli-pitch-deck - Investor decks with charts
- morph-ppt - Cinematic presentations with morph animations
- officecli-xlsx - Excel spreadsheets and financial models
- officecli-data-dashboard - CSV to Excel dashboards with KPI cards and charts

## Project Structure

```
BrainClaw/
├── SYSTEM_PROMPT.md                    # Entry point - for AI IDE integration
├── SYSTEM_PROMPT_STANDALONE.md         # Standalone version
├── README.md                            # This file
└── assistant_brain/
    ├── SOUL.md               # Identity & values (unchanging core)
    ├── OPERATIONAL_RULES.md  # Strategies & decision rules
    ├── CONFIG.md             # System parameters (user info, formats)
    ├── recurring_tasks.md    # Scheduled recurring tasks
    ├── memory/           # Learned experiences
    │   ├── preferences.md    # User preferences
    │   ├── things_to_avoid.md # Mistakes to remember
    │   ├── contacts.md       # External contacts
    │   ├── tracking.md       # Cross-session monitoring
    │   └── policy/           # Policy management
    │       └── README.md     # Policy index
    ├── stakeholders/     # Key stakeholder profiles
    │   ├── README.md         # Module documentation
    │   ├── registry.md       # Stakeholder index
    │   └── SH0xx-xxx.md      # Individual stakeholder files
    ├── skills/           # Modular capabilities
    │   ├── keyword-extraction/
    │   ├── microsoft-graph-skill/
    │   ├── OfficeCLI/
    │   └── skill-creator/
    ├── tasks/            # Task queue & history
    │   ├── queue.md          # Active task list + Recent Events (last 7 days)
    │   ├── T0xx-xxx.md       # Active task details
    │   └── history/          # Completed tasks & monthly timeline archives
    └── backups/          # Configuration backups
```

## Commands

| Command | Trigger | What it does |
|---------|---------|--------------|
| Startup | "start", "启动", "start assistant", "帮我", "help me" | Load brain files, skills, and show today's tasks |
| Greeting | "hi", "hello", "你好", "在吗", "助手" | Quick greeting (lightweight, no full startup) |

## Task Management Features

BrainClaw provides enterprise-grade task tracking:

- **Rich Task Cards**: Status, Priority, Category, Geo (geographic tracking), Due Time, Contact, Keywords, History, Notes
- **Auto-Detection**: Automatically determines Due Time and Priority from context
- **Smart Keywords**: 2-3 unique identifiers (Request IDs, full names, specific codes) for easy source tracing
- **History Tracking**: Cumulative record of all task updates with timestamp and source
- **Parent-Child Tasks**: Master tasks can have subtasks for complex project management
- **Geographic Tracking**: Track tasks by region (Philippines, India, China, Singapore, APAC, Global)
- **Recent Events**: Last 7 days overview in queue.md, with monthly archives
- **Recurring Tasks**: Auto-create scheduled tasks (monthly reports, quarterly processes)

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
| preferences.md | User preferences (timezone, tone, formats) |
| things_to_avoid.md | Failed patterns to learn from |
| contacts.md | External contacts (non-colleagues) |
| tracking.md | Items requiring cross-session monitoring |
| policy/ | Structured policy files with index |

## System Capabilities & Limitations

### What It Can Do

| Capability | Description |
|------------|-------------|
| **State Persistence** | File-based storage keeps memory, logs, and config across sessions |
| **Interactive Response** | Execute tasks when triggered by user (request-response pattern) |
| **Modular Extension** | Add new capabilities through `skills/` without modifying core |
| **Local Autonomy** | All data stays local; no external services required (except AI IDE) |
| **Learning System** | Learns from interactions and updates memory files |
| **Policy Management** | Structured policy tracking with reference system |
| **Scheduled Tasks** | Recurring tasks auto-trigger on schedule |

### What It Cannot Do

| Limitation | Reason |
|------------|--------|
| **Autonomous Execution** | No independent process; requires user presence |
| **Background Operations** | No daemon; no continuous monitoring |
| **Remote Access** | No API endpoint; cannot be triggered from IM or external systems |
| **Async Execution** | No scheduled tasks; no delayed actions; no event-driven execution |

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

## Extending with Skills

Skills are modular capabilities stored in `assistant_brain/skills/`. Each skill adds new abilities without requiring code changes. Use the `skill-creator` skill to build your own.

---

*Built with the belief that AI should serve everyone, not just the technical elite.*
