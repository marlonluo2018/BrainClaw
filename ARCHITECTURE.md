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
- **Policy awareness**: Company-specific rules and procedures

---

## 2. Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     System Prompt                            │
│          (Startup & On-Demand Loading Rules)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Brain Files                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  SOUL    │  │ CONFIG   │  │OPERATIONAL│                  │
│  │          │  │          │  │  RULES   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│  ┌──────────────────────────────────────────┐              │
│  │         Memory Files                     │              │
│  │  preferences | things_to_avoid |         │              │
│  │  contacts | tracking | achievements      │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Workflows                                  │
│  TASK_WORKFLOW | EMAIL_WORKFLOW | STAKEHOLDER_WORKFLOW |    │
│  RECORDING_WORKFLOW                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Skills                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Workflow   │  │  Workflow   │  │    User     │        │
│  │   Skills    │  │   Skills    │  │   Skills    │        │
│  │(task/email) │  │(stakeholder)│  │ (xlsx/graph)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  Tasks | Stakeholders | Policies | Memory | Downloads       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```
BrainClaw/
├── SYSTEM_PROMPT.md              # Main system prompt (for IDE)
├── SYSTEM_PROMPT_STANDALONE.md   # Standalone system prompt
├── README.md                     # User documentation (EN)
├── README_CN.md                  # User documentation (CN)
├── ARCHITECTURE.md               # This file
│
├── assistant_brain/              # Core brain directory
│   ├── SOUL.md                   # Personality & core principles
│   ├── CONFIG.md                 # User settings & formats
│   ├── OPERATIONAL_RULES.md      # Operational policies
│   ├── recurring_tasks.md        # Recurring task definitions
│   │
│   ├── memory/                   # Learning & persistence
│   │   ├── preferences.md        # User preferences
│   │   ├── things_to_avoid.md    # Mistakes to avoid
│   │   ├── contacts.md           # External contacts
│   │   ├── tracking.md           # Cross-session tracking
│   │   └── achievements.md       # Accomplishments
│   │
│   ├── workflows/                # Operation procedures
│   │   ├── TASK_WORKFLOW.md
│   │   ├── EMAIL_WORKFLOW.md
│   │   ├── STAKEHOLDER_WORKFLOW.md
│   │   └── RECORDING_WORKFLOW.md
│   │
│   ├── skills/                   # Modular capabilities
│   │   ├── README.md             # Skill index (auto-generated)
│   │   ├── _TEMPLATE_/           # Skill template
│   │   ├── email/                # Email workflow skill
│   │   ├── task/                 # Task workflow skill
│   │   ├── stakeholder/          # Stakeholder workflow skill
│   │   ├── recording/            # Recording workflow skill
│   │   └── [user skills]/        # User-accessible skills
│   │
│   ├── tasks/                    # Task management
│   │   ├── queue.md              # Active task queue
│   │   ├── T001-xxx.md           # Task files
│   │   └── history/              # Completed tasks
│   │
│   ├── stakeholders/             # Stakeholder management
│   │   ├── README.md             # Module documentation
│   │   ├── registry.md           # Central stakeholder DB
│   │   └── SH001-xxx.md          # Detailed profiles
│   │
│   ├── policy/                   # Company policies
│   │   ├── README.md             # Policy index
│   │   └── [topic-name]/         # Policy folders
│   │       └── policy.md
│   │
│   └── backups/                  # Backup files
│
└── downloads/                    # Downloaded files
```

---

## 4. Component Details

### 4.1 Brain Files

#### SOUL.md
**Purpose**: Defines AI personality and unchanging values
**Content**:
- Identity statement
- Core principles (User-Centric, Memory-Driven, Professional Excellence)
- Unchanging values (approval requirements, security)

#### CONFIG.md
**Purpose**: User settings and format definitions
**Content**:
- User profile (name, email, title, timezone)
- Email signature
- System settings (OS, shell, paths)
- Task format definitions (status, priority, naming, template)
- Download settings

#### OPERATIONAL_RULES.md
**Purpose**: Core behavior strategies and policies
**Content**:
- Workflow reference table
- Autonomous actions policy (what needs approval)
- Display format rules
- Task status change actions

### 4.2 Memory System

The memory system enables persistent learning across sessions.

| File | Trigger | Purpose |
|------|---------|---------|
| `preferences.md` | User explicitly states preference | Store work preferences |
| `things_to_avoid.md` | Work mistake repeats 2+ times | Record mistakes to avoid |
| `contacts.md` | External contact mentioned 3+ times | Track important contacts |
| `tracking.md` | Item requires cross-session monitoring | Track ongoing items |
| `achievements.md` | Significant accomplishment | Record successes |

**Recording Threshold**: See `RECORDING_WORKFLOW.md`

### 4.3 Workflows

Workflows define **step-by-step procedures** for multi-step operations.

| Workflow | Purpose | Skills Used |
|----------|---------|-------------|
| `TASK_WORKFLOW.md` | Task CRUD operations | task (create/update/complete), stakeholder (match) |
| `EMAIL_WORKFLOW.md` | Email processing & drafting | email (compose/info-detect), microsoft-graph-skill |
| `STAKEHOLDER_WORKFLOW.md` | Stakeholder matching & RACI | stakeholder (match/raci-suggest), email (compose) |
| `RECORDING_WORKFLOW.md` | Event & memory recording | recording (event-record) |

**Design Pattern**:
```markdown
## Operation Name

**Trigger:** When to execute

**Steps:**
1. Action → Call `skill/name`
2. Action → Result
3. ...
```

### 4.4 Workflow vs Skill - Division of Responsibility

| Aspect | Workflow | Skill |
|--------|----------|-------|
| **Role** | **Orchestrator** | **Executor** |
| **What** | Defines WHAT steps to do | Defines HOW to do it |
| **Content** | Step sequence, decision points | Processing logic, algorithms |
| **Scope** | Multi-step, multi-skill operations | Single, focused functionality |
| **Analogy** | Conductor (coordinates musicians) | Musician (plays instrument) |
| **Example** | "Create Task" workflow | `task/create` skill |

**Workflow Responsibilities:**
- Define operation sequence
- Call appropriate skills at each step
- Handle decision points (if/else)
- Coordinate between skills
- Present results to user

**Skill Responsibilities:**
- Implement specific functionality
- Process inputs and generate outputs
- Handle errors and edge cases
- Return results to caller

**Example - Creating a Task:**

```markdown
# Workflow (TASK_WORKFLOW.md)
## Create Task
1. Call `keyword-extraction` → Get keywords
2. Call `stakeholder` (operation: match) → Get stakeholders
3. Present RACI to user for confirmation
4. Call `task` (operation: create) → Create file
5. Call `recording` (operation: event-record) → Record event

# Skill (task/SKILL.md)
## Operations
### Create
**Processing Logic:**
1. Generate task ID from queue.md
2. Create file with template
3. Fill in provided fields
4. Update queue.md
5. Return file path
```

### 4.5 Skills

Skills are **modular implementations** of specific functionalities.

#### Skill Structure

```
skills/
├── README.md              # Index file
├── _TEMPLATE_/            # Template for new skills
│   └── SKILL.md
├── [workflow-skill]/      # Workflow skills (support workflows)
│   └── SKILL.md
└── [user-skill]/          # User skills (direct user access)
    └── SKILL.md
```

#### Skill Categories

**1. Workflow Skills** - Internal skills supporting workflows (not shown to users)

| Domain | Operations | Purpose |
|--------|------------|---------|
| `task` | create, update, complete | Task lifecycle management |
| `email` | compose, info-detect | Email drafting and analysis |
| `stakeholder` | match, raci-suggest | Stakeholder matching and RACI |
| `recording` | event-record | Event recording |

**2. User Skills** - Direct user-accessible tools

| Skill | Purpose |
|------|---------|
| `keyword-extraction` | Extract keywords from text |
| `skill-creator` | Create new skills |
| `minimax-xlsx` | Excel/spreadsheet operations |
| `microsoft-graph-skill` | Microsoft Graph API |

#### SKILL.md Template

```markdown
---
name: skill-name
description: One-line description
triggers: ["keyword1", "keyword2"]
operations: ["op1", "op2"]  # For domain skills
inputs:
  - name: param1
    type: string
    required: true
outputs:
  - name: result1
    type: object
---

# Skill Name

## Operations  # For domain skills
### Operation 1
### Operation 2

## Inputs
## Processing Logic
## Output Format
## Example
```

### 4.5 Tasks

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

### 4.6 Stakeholders

#### Registry Structure
Each stakeholder has:
- **ID**: SH001, SH002...
- **Identity**: Name, Email, Title, Organization, Geo
- **Influence**: Power Level, Interest Level, Role Type
- **Communication**: Preferred channel, Style, Timezone
- **Profile**: Interests, Concerns, Decision Criteria

#### RACI Integration
Tasks include RACI matrix:
- **R** = Responsible (does the work)
- **A** = Accountable (decision maker)
- **C** = Consulted (provides input)
- **I** = Informed (kept updated)

### 4.7 Policies

Policies are company-specific rules stored in structured folders.

```
policy/
├── README.md              # Policy index
└── [topic-name]/
    ├── policy.md          # Policy content
    └── [attachments]      # Related files
```

---

## 5. Extension Guide

### 5.1 Adding a New Skill

1. **Determine skill type**:
   - **Workflow skill**: Supports workflows with multiple operations (e.g., `calendar` with schedule/query operations)
   - **User skill**: Direct user access with single purpose (e.g., `pdf-converter`)

2. **Create skill directory and SKILL.md**:
   ```
   skills/[workflow-skill]/SKILL.md  # Workflow skill
   # OR
   skills/[user-skill]/SKILL.md      # User skill
   ```

3. **Write SKILL.md**:
   ```markdown
   ---
   name: skill-name
   description: One-line description
   triggers: ["keyword1", "keyword2"]
   operations: ["op1", "op2"]  # Only for workflow skills
   ---
   
   # Skill Name
   ## Operations  # For workflow skills
   ## Function   # For user skills
   ```

4. **Update `skills/README.md`**

**Example**: Adding `calendar` workflow skill
```markdown
## calendar (workflow skill)
- **Operations:** schedule, query, check-availability
- **Triggers:** `schedule meeting`, `check calendar`, `my availability`
```

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

3. **Update `OPERATIONAL_RULES.md`** reference table

### 5.3 Adding a New Policy

1. **Create policy folder**: `policy/[topic-name]/`

2. **Create policy.md**:
   ```markdown
   # Policy Title
   
   **Effective Date:** YYYY-MM-DD
   **Contact:** Name (email)
   
   ## Summary
   Brief description
   
   ## Details
   Full policy content
   ```

3. **Update `policy/README.md`** index

### 5.4 Adding a New Memory Type

1. **Create file**: `memory/[type].md`

2. **Define structure and purpose**

3. **Update `RECORDING_WORKFLOW.md`** memory types table

4. **Update `SYSTEM_PROMPT.md`** to load at startup

---

## 6. Design Principles

### 6.1 Separation of Concerns

| Layer | Responsibility | Example |
|-------|---------------|---------|
| System Prompt | Startup & loading rules | When to load what |
| Brain Files | Knowledge & settings | SOUL, CONFIG, memory |
| Workflows | Step-by-step procedures | TASK_WORKFLOW |
| Skills | Implementation logic | task/create SKILL.md |
| Data | Persistence | Task files, registry |

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
[SH001](assistant_brain/stakeholders/SH001-beng-paulino.md)
```

---

## 7. Best Practices

### 7.1 File Naming

- **Tasks**: `T{ID}-{keyword1}-{keyword2}.md`
- **Stakeholders**: `SH{ID}-{name}.md`
- **Skills**: `skills/{domain}/{skill-name}/SKILL.md`
- **Policies**: `policy/{topic-name}/policy.md`

### 7.2 Skill Triggers

- Use specific keywords
- Avoid generic terms
- Document in SKILL.md frontmatter
- Update skills/README.md

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
1. Load core files (SOUL, CONFIG, OPERATIONAL_RULES)
2. Load memory files (preferences, things_to_avoid, contacts, tracking)
3. Load task context (queue.md, recurring_tasks.md)
4. Load stakeholder context (registry.md)
5. Load policy index (policy/README.md)
6. Query OS for local date/time
7. Archive old events
8. Parse recurring tasks
9. Load skill index (skills/README.md)
10. Output startup status
```

**Output Format**:
```
✅ Ready | [weekday] [date/time] | User: [Name] | OS: [OS Name]
• Skills: [count] ([list of user skill names])
• Policies: [count] | Stakeholders: [count]
```
- **Count skills:** Count items under "## User Skills" section only (NOT workflow skills)
- **List skills:** Extract skill names from "User Skills" section (e.g., keyword-extraction, skill-creator, etc.)
- Example: If README.md has 4 user skills, output: `• Skills: 4 (keyword-extraction, skill-creator, minimax-xlsx, microsoft-graph-skill)`

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
- Policy versioning

---

## 10. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Skill not found | Check skills/README.md index |
| Workflow not loaded | Read workflow file before execution |
| Memory not persisting | Check recording threshold |
| Task ID conflict | Verify Last Task ID in queue.md header |

### Debug Tips
- Check file paths are relative to assistant_brain/
- Verify markdown syntax in all files
- Ensure frontmatter is properly formatted
- Check skill triggers match user input

---

**Last Updated:** 2026-04-09
**Version:** 1.0
