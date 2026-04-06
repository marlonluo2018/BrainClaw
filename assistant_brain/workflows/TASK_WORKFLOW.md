# Task Workflow

> Detailed procedures for task operations

---

## Priority Detection

- **P1 (High):** Urgent keywords, executive sender, deadline ≤ 2 days
- **P2 (Medium):** Normal work, deadline ≤ 1 week
- **P3 (Low):** FYI items, no strict deadline

---

## Adding a Task

> **Format definitions in CONFIG.md** - Read for: status symbols, priority levels, file naming, templates

1. Read `Last Task ID` from queue.md header → increment for new ID → update header
2. **Extract keywords using `keyword-extraction` skill**
   - Extract 2-3 UNIQUE identifiers
   - Format: P1(Ticket) + P2(Names) + P3(TaskType) + P4(Keywords)
   - Use SPECIFIC identifiers, avoid generic terms
3. **Identify Geography (Geo)** from context (email sender, requester location, organization)
   - Examples: Philippines, India, China, Singapore, APAC, Global
   - Helps prevent matching emails to wrong geographic region
4. **Auto-detect stakeholders and suggest RACI roles:**
   - Check email contacts (To, CC, From) against [`stakeholders/registry.md`](../stakeholders/registry.md)
   - Auto-suggest RACI roles based on:
     - Email role: To/From = likely R or A, CC = likely I
     - Stakeholder power: High Power = likely A (Accountable)
     - Task type: Budget task → budget approver = A, Procurement task → procurement team = C
   - Present suggested RACI matrix to user for confirmation
5. Create `T{ID}-{keywords}.md` in tasks/ (use template from CONFIG.md with Geo field)
6. If task is from recurring_tasks.md, include "Recurring Task ID" field in task file and queue.md (use "id" value, e.g., R001)
7. Add entry to queue.md table with Created, Priority, Due, Tags (and Recurring Task ID only if from recurring_tasks.md)
8. Confirm with user

---

## Master Tasks and Subtasks

**Creating a Master Task:**
1. Follow standard "Adding a Task" procedure
2. Add "(Master)" to task title
3. Add "**Subtasks:**" field listing subtask IDs in both task file and queue.md
4. Place in "Master Task with Subtasks" section of queue.md

**Creating a Subtask:**
1. Follow standard "Adding a Task" procedure
2. Add "**Parent Task:** TXXX" field in both task file and queue.md
3. Place under master task in queue.md using `### ↳` prefix
4. Update master task's "**Subtasks:**" field to include this subtask ID

**Updating Relationships:**
- Adding subtask: Update master's "**Subtasks:**" field + place subtask under master in queue.md
- Removing subtask: Update master's "**Subtasks:**" field + move/archive subtask
- Converting to master: Add "(Master)" + "**Subtasks:**" field + move to "Master Task with Subtasks" section

**Queue.md Organization:**
- Standalone tasks: `##` heading in "Standalone Tasks" section
- Master tasks: `##` heading in "Master Task with Subtasks" section
- Subtasks: `### ↳` heading directly under master task
- Keep master and all subtasks grouped together

---

## Updating a Task

1. Read current task file to see existing content
2. Check if incoming information already exists in the file
3. If new: Show user what will be added and ask for approval
4. If duplicate: Notify user that info already exists (skip adding)
5. After approval: Update status in queue.md + add new entry to task file
6. ⚠️ NEVER update task files without checking for duplicates and notifying user

---

## Marking Task as Blocked

- Use 🔴 Blocked status when task cannot proceed due to external dependency
- Always document in task file: what is blocking, who is responsible, expected resolution
- **Before marking blocked:** Check task RACI matrix → remind to notify Accountable (A) stakeholder about blocker
- Suggest: "Task blocked. [Stakeholder Name] (Accountable) should be notified. Draft email?"

---

## Completing a Task

1. **Before marking complete:** Check task RACI matrix → remind to notify Accountable (A) and Informed (I) stakeholders
2. Suggest: "Task complete. Should I draft notification email to [Stakeholder Names]?"
3. Update status to ✅
4. If task has "Recurring Task ID" (e.g., R001), find matching "id" in recurring_tasks.md and update its "last_completed" field
5. Move to history/ → remove from queue.md → add Completion event to Recent Events using format: `- **YYYY-MM-DD**: ✅ Completed [[./history/T###-xxx.md]] (Task Title)`

---

## Task Matching

When user mentions keyword → search queue.md → show matching tasks → read task file if details needed

---

## Stakeholder-Based Task Queries

When user asks about tasks for a specific stakeholder:
- "Show tasks for [stakeholder name]"
- "What tasks is [stakeholder] involved in?"
- "List all tasks where [stakeholder] is Accountable"

**Process:**
1. Search all active task files (T###-xxx.md) for stakeholder name in Stakeholders section
2. Extract: Task ID, Title, Status, Stakeholder's Role (R/A/C/I)
3. Group by status: ⏳ In Progress → 📋 Not Started → 🔴 Blocked
4. Display format:
   ```
   Tasks for [Stakeholder Name]:
   
   In Progress (⏳):
   - [T025](../tasks/T025-pmp-renewal-futurenow-q2.md): PMP Renewal - Role: A (Accountable)
   
   Not Started (📋):
   - [T019](../tasks/T019-q2-budget-python-beng-lani.md): Q2 Budget Master - Role: A (Accountable)
   
   Total: 2 tasks (1 in progress, 1 not started)
   ```
5. If user wants details → offer to read specific task files