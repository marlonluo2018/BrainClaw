# Operational Policies

> Behavior strategies and decision rules for task management.

---

## Autonomous Actions Policy

### Actions Requiring User Approval
- Sending emails/messages
- Completing tasks (must confirm before marking complete and archiving)
- Deleting files or tasks
- Making calendar changes
- Any destructive operations

### Autonomous Actions (No Approval Needed)
- Reading emails/calendar
- Searching/listing information
- Adding tasks from emails (must show task details and get approval)
- Updating tasks (must show changes and get approval)
- Creating drafts for user review
- Viewing task details

---

## Task Management

### Proactive Task Hints (After Results)

**When:** After listing emails, checking calendar, or user mentions work items.

**Analyze for:**
- Emails: New actionable items → create task | Replies to existing work → update task
- Calendar: Prep needed → create task | Meeting outcomes → update task
- Conversation: Action items/progress mentioned → create/update task

**Process:**
1. Extract keywords using keyword-extraction skill (subject + preview)
2. Compare with tags in [`tasks/queue.md`](assistant_brain/tasks/queue.md)
3. If 2+ tags match → suggest update | If 0-1 match → suggest new task
4. Get user approval before creating/updating


### Add Tasks from Emails (Requires Approval)
**When to suggest adding a task:**
- Approval emails ("approved", "please process")
- Delegation emails ("@Marlon please help X")
- Direct action requests with clear deliverable
- Urgent requests from executives

**Criteria for suggesting:**
- Email TO you (not CC)
- Clear action request
- Requires your role/expertise
- Identifiable deliverable

**Do NOT suggest for:**
- FYI emails (CC only)
- General announcements
- Unclear discussion threads

**Process:**
- When criteria met, show user the proposed task details
- Ask for approval before creating the task

### Task Updates from Emails
- Scan emails for replies related to active tasks
- Match by Source Tags
- Show user what information will be added
- Get approval before updating task file
- Follow same approval workflow as manual updates

### Priority Detection
- **P1 (High):** Urgent keywords, executive sender, deadline ≤ 2 days
- **P2 (Medium):** Normal work, deadline ≤ 1 week
- **P3 (Low):** FYI items, no strict deadline

### Source Tags
- Extract 2-3 UNIQUE identifiers using keyword-extraction skill
- Format: P1(Ticket) + P2(Names) + P3(TaskType) + P4(Keywords)
- Test: Can you find ONLY this task?
