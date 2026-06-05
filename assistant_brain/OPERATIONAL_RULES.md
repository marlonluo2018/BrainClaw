# Operational Rules

> Core behavior strategies - See workflows/ for procedures, skills/ for implementations

---

## Date/Time Query

**MUST query OS for LOCAL time with weekday:**
- Windows: `powershell -Command "Get-Date -Format 'dddd yyyy-MM-dd HH:mm'"`
- Unix/Linux/Mac: `date "+%A %Y-%m-%d %H:%M"`

**Output format:** `[weekday] [YYYY-MM-DD] [HH:mm]` (e.g., "Thursday 2026-04-09 11:15")

### Relative Date Calculation

> ⚠️ **CRITICAL:** When user mentions relative dates → MUST execute PowerShell to calculate BEFORE using in commands. NO mental arithmetic!

**Trigger patterns:** "Friday", "yesterday", "last week", "昨天", "上周", "3 days ago", etc.

**Mandatory process:**
1. Detect relative date in user request → **STOP**
2. Execute PowerShell command to calculate exact date
3. Use PowerShell output (do NOT calculate mentally)
4. Proceed with operation using calculated date

**Common patterns (Windows):**
```powershell
# Yesterday
powershell -Command "(Get-Date).AddDays(-1).ToString('yyyy-MM-dd')"

# Last Friday (most recent)
powershell -Command "$d=Get-Date; $days=($d.DayOfWeek.value__+2)%7; if($days -eq 0){$days=7}; $d.AddDays(-$days).ToString('yyyy-MM-dd')"

# N days ago (e.g., 3)
powershell -Command "(Get-Date).AddDays(-3).ToString('yyyy-MM-dd')"
```

---

## Skills Architecture

**Two-layer design:**
- **Workflow Layer**: Orchestration, business logic, guidelines (workflow .md files)
- **I/O Layer**: External system interactions (skills with code/scripts)

**Pattern:** Workflows contain all business logic and call I/O skills for data access.

---

## Workflow Reference

| Operation | Trigger Commands | Workflow |
|-----------|------------------|----------|
| Email operations | "check email", "list emails", "show emails", "emails from", "process email", "draft email", "reply", "forward", "update tasks", "update progress", "email sync", "sync emails", "check and update" | [`workflows/EMAIL_WORKFLOW.md`](workflows/EMAIL_WORKFLOW.md) |
| Task operations | "create task", "update task", "complete task", "block task" | [`workflows/TASK_WORKFLOW.md`](workflows/TASK_WORKFLOW.md) |
| Process intelligence | "next step", "推进", "下一步", "what process", "固化流程" | [`workflows/PROCESS_WORKFLOW.md`](workflows/PROCESS_WORKFLOW.md) |
| Event recording | "record event", "archive events" | [`workflows/RECORDING_WORKFLOW.md`](workflows/RECORDING_WORKFLOW.md) |
| **Views (cross-task / per-task)** | `status T###` (or bare `T###`), `pending`, `pending out`/`owed`/`待我处理`, `pending in`/`waiting`/`等待`, `before {person}`, `见 X 前`, `review {period}`, `述职`, `半年述职`, `annual review`, `taskboard`, `全部任务` | [`workflows/VIEWS_WORKFLOW.md`](workflows/VIEWS_WORKFLOW.md) |

**⚠️ CRITICAL:** ALWAYS load and follow the workflow BEFORE executing operations. Do NOT skip workflow loading.

**Note on Views:** The startup task list renders automatically as Step 9 of CLAUDE.md startup. All view operations also read [`views_config.md`](views_config.md) for thresholds and defaults before producing output.

---

## Autonomous Actions Policy

### Requires User Approval
- Sending emails/messages
- Completing tasks
- Deleting files or tasks
- Making calendar changes
- Any destructive operations

### Autonomous (No Approval Needed)
- Reading emails/calendar
- Searching/listing information
- Viewing task details
- Creating drafts for review

---

## Display Formats

> For startup Active Tasks display format (priority ordering, P1 warnings, master/subtask hierarchy), see [`CONFIG.md` → Startup Display Format](../CONFIG.md)

### Task References
**Always format task IDs as clickable links WITH the task name:**
```
[T025](assistant_brain/tasks/T025-pmp-renewal-futurenow-q2.md) PMP Renewal - FutureNow Center Philippines
```

**Rule:** Never display a bare task ID (e.g., `T025`) without both a link AND the task name. Users cannot recognize tasks by ID alone.

**Format:** `[TID](path) Task Name`

---

## Task Formats

> **See [`tasks/FORMATS.md`](tasks/FORMATS.md) for all task format specifications:**
> - Directory structure & file naming
> - Status symbols (📋 ⏳ 🔴 ✅) & priority levels (P1/P2/P3)
> - Queue format & task template
> - Tag guidelines & master-subtask organization
>
> **Load on-demand:** When creating or updating tasks

---

**Note:** This file contains core policies only. For step-by-step procedures, read the relevant workflow file. For implementation details, read the relevant skill file.
