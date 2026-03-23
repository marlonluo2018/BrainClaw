
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
3. Paste the content of `Personal_Assistant_System_Prompt.md`
4. Set your workspace to the BrainClaw folder

### Daily Use

1. Open your AI IDE
2. Say "hi" or "你好"
3. The assistant loads and is ready to help

**No installation. No configuration. No command line.**

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  AI IDE (Claude / Cursor / etc.)                    │
│  ┌───────────────────────────────────────────────┐  │
│  │  Custom System Prompt                         │  │
│  │  (Personal_Assistant_System_Prompt.md)        │  │
│  │                                               │  │
│  │  "On startup, read brain files..."           │  │
│  │  "Commands: hi, end of day..."               │  │
│  └───────────────────────────────────────────────┘  │
│                        ↓                            │
│  ┌───────────────────────────────────────────────┐  │
│  │  Brain Files (assistant_brain/)               │  │
│  │  ├── SOUL.md      (personality)               │  │
│  │  ├── CONFIG.md    (your settings)             │  │
│  │  ├── memory/      (learned preferences)       │  │
│  │  ├── skills/      (capabilities)              │  │
│  │  └── logs/        (daily tasks)               │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## What Can It Do?

| Feature | Description |
|---------|-------------|
| **Task Management** | Detailed task tracking with Status, Priority, Category, Due Time, Contact, Keywords, History |
| **Email Management** | Check, send, reply emails (via Microsoft Graph Skill) |
| **Memory System** | Learns your preferences over time |
| **Calendar** | Schedule management (with skills) |
| **Extensible** | Add new capabilities through skills |

### Task Queue Features

- **Rich Task Cards**: Each task includes Status, Priority, Category, Due Time, Contact, Keywords, History, Note
- **Auto-Detection**: Automatically determines Due Time and Priority from context
- **Smart Keywords**: 2-3 unique identifiers (Request IDs, full names, specific codes) for easy source tracing
- **History Tracking**: Cumulative record of all task updates with timestamp and source
- **Smart Carry-Over**: End of Day preserves uncompleted tasks with all fields

### Keywords System

BrainClaw uses a smart keyword system to help you trace tasks back to their source:

- **What**: 2-3 unique identifiers per task (Request IDs, full names, specific codes)
- **Why**: Quickly find the original email/document that created the task
- **How**: Avoid generic terms, use specific identifiers only

**Examples:**
- ✅ Good: `CRT282911, Ashish Sah, Platform Developer II` → finds exact email
- ✅ Good: `Req 11695, Informatica PowerCenter` → unique request
- ❌ Bad: `certification, approval, Salesforce` → finds hundreds of emails

## Project Structure

```
BrainClaw/
├── Personal_Assistant_System_Prompt.md  # Entry point - open this first
├── README.md                            # This file
└── assistant_brain/
    ├── SOUL.md          # Core personality
    ├── CONFIG.md        # Your settings
    ├── memory/          # Learned experiences
    ├── skills/          # Modular capabilities
    └── logs/            # Daily activity logs
```

## Commands

| Command | Trigger | What it does |
|---------|---------|--------------|
| Startup | "hi", "你好" | Load brain files, show today's tasks |
| End of Day | "end of day", "收工" | Archive today's log, carry over tasks |

## Language Support

- **Files**: English (for consistency)
- **Commands**: English + Chinese
- **User content**: Any language

## System Capabilities & Limitations

### What It Can Do

| Capability | Description |
|------------|-------------|
| **State Persistence** | File-based storage keeps memory, logs, and config across sessions |
| **Interactive Response** | Execute tasks when triggered by user (request-response pattern) |
| **Modular Extension** | Add new capabilities through `skills/` without modifying core |
| **Local Autonomy** | All data stays local; no external services required (except AI IDE) |

### What It Cannot Do

| Limitation | Reason |
|------------|--------|
| **Autonomous Execution** | No independent process; requires user presence |
| **Background Operations** | No daemon; no continuous monitoring |
| **Remote Access** | No API endpoint; cannot be triggered from IM or external systems |
| **Async Execution** | No scheduled tasks; no delayed actions; no event-driven execution |

### System Nature

```
BrainClaw = Stateless Request-Response System
         ≠ Stateful Continuously Running System
```

**Core Constraint: No process, only conversation.**

## Philosophy

> "AI should be accessible to everyone, not just developers."

BrainClaw bridges the gap between powerful AI tools and everyday office workers. By using AI IDEs as the interface, we bypass traditional barriers while keeping the capabilities users need.

## Extending with Skills

Skills are modular capabilities stored in `assistant_brain/skills/`. Each skill adds new abilities without requiring code changes. See `skill-creator` skill to build your own.

---

*Built with the belief that AI should serve everyone, not just the technical elite.*
