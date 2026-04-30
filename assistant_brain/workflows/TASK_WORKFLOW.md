# Task Workflow

> Task operations workflow - orchestrates skills for task management
>
> **Format Reference:** See [`../tasks/FORMATS.md`](../tasks/FORMATS.md) for task templates, status symbols, priority levels, and other format specifications (load on-demand when creating/updating tasks)

---

## Create Task

**Trigger:** User requests new task, email action item detected

**Steps:**
1. Read queue.md header → Get "Last Task ID" and increment by 1 for new task ID
2. Call `keyword-extraction` → Get keywords from content
3. Call `stakeholder` (operation: match) → Match contacts to stakeholders, get RACI suggestions
4. Present RACI matrix to user for confirmation
5. Call `task` (operation: create) → Create task file with new task ID and confirmed details (uses format from tasks/FORMATS.md) + Add entry to queue.md + Update "Last Task ID" in queue.md header
5. Call `recording` (operation: event-record, type: task_created) → Record in Recent Events
6. Confirm with user

---

## Update Task

**Trigger:** User provides new info, email relates to existing task

**Steps:**
1. Read current task file
2. Check for duplicates (information already exists?)
3. If duplicate → Notify user and skip
4. If new → Show changes and get approval
5. Call `task` (operation: update) → Update task file and timeline + Update queue.md entry
6. If significant change → Call `email` (operation: info-detect) to check stakeholder notification need
7. Notify user of changes

---

## Complete Task

**Trigger:** User confirms task done

**Steps:**
1. Call `task` (operation: complete) → Get stakeholders to notify (A + I roles), move task file to history/ + Remove from queue.md
2. Ask user: "Draft notification email to [stakeholders]?"
3. If yes → Call `email` (operation: compose) for each stakeholder
4. Call `recording` (operation: event-record, type: task_completed) → Record completion
5. If recurring task → Update recurring_tasks.md last_completed

---

## Block Task

**Trigger:** Task cannot proceed due to dependency

**Steps:**
1. Call `task` (operation: update) → Set status 🔴 Blocked + Update queue.md status
2. Call `recording` (operation: event-record, type: task_blocked) → Record in Recent Events
3. Read task RACI matrix → Identify Accountable (A) stakeholder
4. Automatically call `email` (operation: compose) → Draft notification email to Accountable stakeholder
5. Present drafted email: "Task blocked. Notification email drafted for [Stakeholder] (Accountable):"
6. If approved → Follow [EMAIL_WORKFLOW: Draft Email](../workflows/EMAIL_WORKFLOW.md#draft-email-newreplyforward) to send
7. If declined → Skip notification (but record blocker reason in task)

---

## Master-Subtask Operations

### Create Master Task
1. Follow Create Task workflow
2. Add "(Master)" to title
3. Add "**Subtasks:**" field

### Create Subtask
1. Follow Create Task workflow
2. Add "**Parent Task: TXXX" field
3. Call `task` (operation: create) → Place under master with `### ↳` prefix
4. Call `task` (operation: update) on master → Add subtask to Subtasks field

### Update Relationships
- **Add subtask**: Update master's Subtasks field + queue placement
- **Remove subtask**: Update master + move/archive subtask
- **Convert to master**: Add (Master) + Subtasks field + move section

---

## Task Queries

### By Keyword
1. Search queue.md for keyword
2. Show matching tasks with links
3. If details needed → Read specific task file

### By Stakeholder
1. Search all task files for stakeholder name in Stakeholders section
2. Group by status: ⏳ In Progress → 📋 Not Started → 🔴 Blocked
3. Display with RACI role

---

## Skills Used

|| Skill | Operations Used | Purpose |
||-------|-----------------|---------|
|| `keyword-extraction` | - | Extract task keywords |
|| `stakeholder` | match, raci-suggest | Match contacts, suggest RACI |
|| `task` | create, update, complete | Task lifecycle management |
|| `recording` | event-record | Record events |
|| `email` | compose, info-detect | Notification emails, detection |
