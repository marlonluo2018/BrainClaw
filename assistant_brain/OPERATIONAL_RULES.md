# Operational Policies

> Core behavior strategies loaded at startup - See workflows/ for detailed procedures

---

## Quick Reference to Detailed Workflows

For detailed step-by-step procedures, read these on-demand:

- **Task operations** → [`workflows/TASK_WORKFLOW.md`](workflows/TASK_WORKFLOW.md)
- **Email operations** → [`workflows/EMAIL_WORKFLOW.md`](workflows/EMAIL_WORKFLOW.md)
- **Stakeholder management** → [`workflows/STAKEHOLDER_WORKFLOW.md`](workflows/STAKEHOLDER_WORKFLOW.md)
- **Recording events/memory** → [`workflows/RECORDING_WORKFLOW.md`](workflows/RECORDING_WORKFLOW.md)

---

## Autonomous Actions Policy

### Actions Requiring User Approval
- Sending emails/messages
- Completing tasks
- Deleting files or tasks
- Making calendar changes
- Any destructive operations

### Autonomous Actions (No Approval Needed)
- Reading emails/calendar
- Searching/listing information
- Adding tasks from emails (must show details and get approval)
- Updating tasks (must show changes and get approval)
- Creating drafts for user review
- Viewing task details

---

## Core Display Formats

### Task Display Format
**When mentioning tasks in any response:**
- ALWAYS format task IDs as clickable links: `[TID](assistant_brain/tasks/TID-keywords.md)`
- Example: `[T025](assistant_brain/tasks/T025-pmp-renewal-futurenow-q2.md)`
- Purpose: Enable quick access to task files
- Apply to: All task mentions (summaries, lists, queries, updates, completions)

### Email Display Format
**When summarizing emails:**
- ALWAYS include email reference numbers (e.g., #1, #2, #3)
- Format: Use "#X" prefix in summary text
- Purpose: Enable quick reference for follow-up actions
- Example: "#17 Manjula (LearnQuest) - Azure APIM clarifications"

---

## Core Stakeholder Rules

**Before drafting any email:**
1. Read [`stakeholders/registry.md`](stakeholders/registry.md) → find recipient
2. Read recipient's detailed file (e.g., `SH001-beng-paulino.md`)
3. Use profile (power, style, interests, concerns) to tailor email tone and content

**When creating tasks:**
- Auto-detect stakeholders from email contacts
- Suggest RACI roles based on stakeholder power level and task type
- Present suggested RACI matrix to user for confirmation

**When changing task status:**
- Check task RACI matrix for relevant stakeholders
- Remind to notify Accountable (A) stakeholders when blocked
- Remind to notify Accountable (A) and Informed (I) stakeholders when complete
- Offer to draft notification email

**For detailed procedures:** Read [`workflows/STAKEHOLDER_WORKFLOW.md`](workflows/STAKEHOLDER_WORKFLOW.md)

---

## Core Task Rules

**Task Workflow Summary:**
- Extract keywords using keyword-extraction skill
- Identify geography from context
- Auto-detect stakeholders and suggest RACI roles
- Format all task IDs as clickable links
- Check for duplicates before updating
- Notify stakeholders when status changes
- **Master-Subtask organization:** Group master tasks with subtasks in queue.md using hierarchical format

**Priority levels:**
- P1 (High): Urgent, executive sender, deadline ≤ 2 days
- P2 (Medium): Normal work, deadline ≤ 1 week
- P3 (Low): FYI items, no strict deadline

**Master-Subtask Relationships:**
- Master task: Complex task with multiple subtasks (mark as "Master" in title)
- Subtask: Component task with "Parent Task: TXXX" field
- Queue organization: Group master with subtasks using `### ↳` prefix for subtasks
- Update both master and subtask when relationships change

**For detailed procedures:** Read [`workflows/TASK_WORKFLOW.md`](workflows/TASK_WORKFLOW.md)

---

## Core Email Rules

**Email Workflow Summary:**
- Read stakeholder profile before drafting
- Include reference numbers in email summaries (#1, #2, #3)
- Suggest task creation from action emails (approval, delegation, direct requests)
- Draft with appropriate tone based on stakeholder power and style
- Skip FYI emails, announcements, unclear threads

**For detailed procedures:** Read [`workflows/EMAIL_WORKFLOW.md`](workflows/EMAIL_WORKFLOW.md)

---

## When to Load Detailed Workflows

Load workflow files on-demand when you need:

- **Step-by-step task procedures** → Read [`workflows/TASK_WORKFLOW.md`](workflows/TASK_WORKFLOW.md)
  - Adding a Task (detailed 8-step procedure)
  - Updating a Task (duplicate checking)
  - Marking as Blocked (notification procedures)
  - Completing a Task (5-step procedure)
  - Stakeholder-based task queries

- **Email operation details** → Read [`workflows/EMAIL_WORKFLOW.md`](workflows/EMAIL_WORKFLOW.md)
  - Proactive Task Hints (6-step process)
  - Draft Email Command (detailed procedure)
  - Add Tasks from Emails (criteria)

- **Stakeholder procedures** → Read [`workflows/STAKEHOLDER_WORKFLOW.md`](workflows/STAKEHOLDER_WORKFLOW.md)
  - Auto-detect stakeholders logic
  - RACI suggestion rules by task type
  - Notification reminder procedures
  - Communication tailoring by stakeholder type

- **Recording procedures** → Read [`workflows/RECORDING_WORKFLOW.md`](workflows/RECORDING_WORKFLOW.md)
  - Recent Events Recording Policy
  - Memory Recording Policy
  - Recording formats and archiving

---

**Note:** Core rules above are loaded at startup. Detailed workflows are read on-demand when needed.
