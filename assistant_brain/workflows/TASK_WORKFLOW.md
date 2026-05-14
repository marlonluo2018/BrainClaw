# Task Workflow

> Task operations workflow
>
> **Format Reference:** See [`../tasks/FORMATS.md`](../tasks/FORMATS.md) for task templates, status symbols, priority levels, and other format specifications (load on-demand when creating/updating tasks)

---

## Create Task

**Trigger:** User requests new task, email action item detected

**Steps:**
1. Read queue.md header → Get "Last Task ID" and increment by 1 for new task ID
2. Extract keywords from content (see [Keyword Extraction Rules](#keyword-extraction-rules))
3. Match contacts against [`stakeholders/registry.md`](../stakeholders/registry.md) and suggest RACI roles (see [RACI Rules](#raci-rules-by-task-type))
4. Present RACI matrix to user for confirmation
5. Generate filename: `T{ID}-{keyword1}-{keyword2}.md`
6. Create task file using template from [`tasks/FORMATS.md`](../tasks/FORMATS.md)
7. Add entry to queue.md (see [Queue Update](#queue-update))
8. Update "Last Task ID" in queue.md header
9. Record in Recent Events: `- **{date}**: 📋 Created [TID](path) - {title}`
10. Confirm with user

---

## Update Task

**Trigger:** User provides new info, email relates to existing task

**Steps:**
1. Read current task file
2. Check if incoming information already exists (duplicate check)
3. If duplicate → Notify user and skip
4. If new → Show changes and get approval
5. After approval, update task file and timeline entry
6. Update queue.md if status/priority/due changed (see [Queue Update](#queue-update))
7. Notify user of changes

**Update Types:**

| Field | Action |
|-------|--------|
| status | Update status field + queue.md |
| timeline | Append new entry |
| notes | Append to notes section |
| stakeholders | Update RACI matrix |
| due_date | Update due field + queue.md |
| priority | Update priority + queue.md |

---

## Complete Task

**Trigger:** User confirms task done

**Steps:**
1. Read task file → Get RACI matrix → Identify Accountable (A) and Informed (I) stakeholders
2. Update status to ✅
3. If task has "Recurring Task ID" → Update recurring_tasks.md "last_completed"
4. Move task file to `tasks/history/`
5. Remove from queue.md (see [Queue Update](#queue-update))
6. Record in Recent Events: `- **{date}**: ✅ Completed [TID](path) - {title}`
7. Ask user: "Draft notification email to [stakeholders]?"
8. If yes → Follow [EMAIL_WORKFLOW](EMAIL_WORKFLOW.md) to draft and send

---

## Block Task

**Trigger:** Task cannot proceed due to dependency

**Steps:**
1. Set status to 🔴 Blocked, update queue.md
2. Record in Recent Events: `- **{date}**: 🔴 Blocked [TID](path) - {title}`
3. Read task RACI matrix → Identify Accountable (A) stakeholder
4. Draft notification email to Accountable stakeholder
5. Present drafted email: "Task blocked. Notification email drafted for [Stakeholder] (Accountable):"
6. If approved → Follow [EMAIL_WORKFLOW](EMAIL_WORKFLOW.md) to send
7. If declined → Skip notification (but record blocker reason in task)

---

## Master-Subtask Operations

### Create Master Task
1. Follow Create Task workflow
2. Add "(Master)" to title
3. Add "**Subtasks:**" field

### Create Subtask
1. Follow Create Task workflow
2. Add "**Parent Task: TXXX**" field
3. Place under master with `### ↳` prefix in queue.md
4. Update master's Subtasks field

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

## Queue Update

### Add to Queue
1. Increment Last Task ID in queue.md header
2. Add task entry in correct section:
   - Standalone tasks: "Standalone Tasks" section
   - Master tasks: "Master Task with Subtasks" section
   - Subtasks: Under parent task with `### ↳` prefix

### Remove from Queue
1. Remove task entry from queue
2. If subtask: Update parent's "Subtasks:" field
3. If master: Move all subtasks to standalone

### Update in Queue
1. Find task entry
2. Update specified fields (status, priority, due)
3. Preserve queue structure

---

## Keyword Extraction Rules

**Priority Order (Highest First):**

| Priority | Type | Examples |
|----------|------|----------|
| 1 Highest | Ticket Number | INC0012345, SR0006789, CHG0054321, RITM123456 |
| 2 Second | Person Names | Jexer Poblete, Marlon Luo (exclude frequent approvers) |
| 3 Third | Task Type | voucher request, access request, approval task |
| 4 Fourth | Task Keywords | AZ-900, certificate, ITIL, error |
| 5 Fifth | Attachments | certificate.pdf, proof_of_training.docx |

**Output:** 3-8 keywords, sorted by priority. Skip any level without matches.

---

## RACI Rules by Task Type

| Task Type | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|-----------|-----------------|-----------------|---------------|--------------|
| Budget | Task owner | High-power approver | Finance team | Other managers |
| Procurement | Requester | Budget owner | Procurement team | End users |
| Training | Trainee | Manager | Training provider | HR |
| Approval | Executor | Approver | Subject experts | Stakeholders |
| Technical | Developer | Tech lead | Architect | Product owner |
| General | To/From → R | High Power → A | - | CC → I |

**Power-Based Rules:**

| Power Level | Typical RACI Role |
|-------------|-------------------|
| High | A (Accountable) or I (Informed) |
| Medium | C (Consulted) or R (Responsible) |
| Low | R (Responsible) or I (Informed) |
