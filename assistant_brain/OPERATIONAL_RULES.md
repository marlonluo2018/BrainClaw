# Operational Policies

> Behavior strategies and decision rules for task management.

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

## Task Management

### Email Operations

#### Email Display Format
**When summarizing emails after list/search operations:**
- ALWAYS include email reference numbers (e.g., #1, #2, #3)
- Format: Use "#X" prefix in summary text
- Purpose: Enable quick reference for follow-up actions (reply, forward, get details)
- Example: "#17 Manjula (LearnQuest) - Azure APIM clarifications"

#### Proactive Task Hints

**When:** After listing emails, checking calendar, or user mentions work items.

**Process:**
1. Extract keywords using keyword-extraction skill
2. Compare with tags in `tasks/queue.md`
3. Count only SPECIFIC identifier matches (names, emails, IDs, codes)
4. **Suggest user to review relevant emails:**
   - If 2+ matches → "Email #X may relate to task TY, would you like to review?"
   - If 0-1 match → "Email #X may need new task, would you like to review?"
5. **If meeting invites found → Remind user to check calendar:**
   - List meeting invite dates
   - Suggest: "You have X meeting invites on [dates], would you like to check your calendar for those days?"
6. Get user approval

#### Add Tasks from Emails

**When:** Approval emails, delegation emails, direct action requests, urgent executive requests

**Criteria:** Email TO you, clear action request, requires your role/expertise, identifiable deliverable

**Skip:** FYI emails, general announcements, unclear discussion threads

### Task Operations

#### Priority Detection
- **P1 (High):** Urgent keywords, executive sender, deadline ≤ 2 days
- **P2 (Medium):** Normal work, deadline ≤ 1 week
- **P3 (Low):** FYI items, no strict deadline

#### Task Workflow

> **Format definitions in CONFIG.md** - Read for: status symbols, priority levels, file naming, templates

**Adding a Task:**
1. Read `Last Task ID` from queue.md header → increment for new ID → update header
2. **Extract keywords using `keyword-extraction` skill**
   - Extract 2-3 UNIQUE identifiers
   - Format: P1(Ticket) + P2(Names) + P3(TaskType) + P4(Keywords)
   - Use SPECIFIC identifiers, avoid generic terms
3. **Identify Geography (Geo)** from context (email sender, requester location, organization)
   - Examples: Philippines, India, China, Singapore, APAC, Global
   - Helps prevent matching emails to wrong geographic region
4. Create `T{ID}-{keywords}.md` in tasks/ (use template from CONFIG.md with Geo field)
5. If task is from recurring_tasks.md, include "Recurring Task ID" field in task file and queue.md (use "id" value, e.g., R001)
6. Add entry to queue.md table with Created, Priority, Due, Tags (and Recurring Task ID only if from recurring_tasks.md)
7. Confirm with user

**Updating a Task:**
1. Read current task file to see existing content
2. Check if incoming information already exists in the file
3. If new: Show user what will be added and ask for approval
4. If duplicate: Notify user that info already exists (skip adding)
5. After approval: Update status in queue.md + add new entry to task file
6. ⚠️ NEVER update task files without checking for duplicates and notifying user

**Completing a Task:**
1. Update status to ✅
2. If task has "Recurring Task ID" (e.g., R001), find matching "id" in recurring_tasks.md and update its "last_completed" field
3. Move to history/ → remove from queue.md → add Completion section

**Task Matching:** When user mentions keyword → search queue.md → show matching tasks → read task file if details needed

---

## Draft Email Command

When user says "draft email", "draft reply", "起草邮件", or "草拟邮件":

1. **Gather info** - Collect To, Subject, Body
2. **Format draft** - Prepare content with signature
3. **Present draft** - Show email with signature, offer suggestions for improving the email content, ask for approval
4. **Iterate or send** - If changes requested → revise; If approved → send
5. **Confirm** - Report email sent

---

## Recent Events Recording Policy

### Purpose & Separation

**queue.md Recent Events:**
- Purpose: Quick overview of recent activities across ALL tasks
- Scope: Task creation/completion milestones + Non-task events
- Audience: User asking "what did I do recently?"

**Task File Timeline:**
- Purpose: Complete history of SINGLE task
- Scope: All task-related events (detailed)
- Audience: User asking "what happened with this task?"

### What to Record

#### queue.md Recent Events (Last 7 Days)

| Event Type | Icon | Record? |
|------------|------|---------|
| Task Created | 📋 | ✅ Yes |
| Task Completed | ✅ | ✅ Yes |
| Important Email Sent | 📧 | ❌ No (in task file) |
| Important Email Received | 📥 | ❌ No (in task file) |
| Meeting/Decision | 🤝 | ✅ Yes (non-task events only) |
| Tracking Issue | 📊 | ✅ Yes |
| Task Updates | - | ❌ No (in task file) |

#### Task File Timeline

Record ALL task-related events in detail:
- Task creation
- Email sent/received
- Status changes
- Updates and progress
- Completion

### Recording Format

**queue.md Recent Events:**
```markdown
- **{YYYY-MM-DD}**: {icon} {description} {task_link}
```

**Task File Timeline:**
```markdown
- **{YYYY-MM-DD HH:mm}** [{source}]: {detailed description}
```

### Query Flow

**User: "What did I do recently?"**
1. Read queue.md Recent Events
2. Show last 7 days activities (task creation/completion + non-task events)

**User: "What happened with T019?"**
1. Read queue.md Recent Events → find T019 creation/completion
2. Read T019.md Timeline → get detailed history
3. Combine information

### Archiving

- Keep last 7 days in queue.md
- Move older events to `tasks/history/timeline_YYYY-MM.md`
- One file per month
- Keep last 12 months
- Delete files older than 12 months (optional)

---

## Memory Recording Policy

### What to Record

| Memory File | Trigger | Skip |
|-------------|---------|------|
| preferences.md | User explicitly states preference | Technical details |
| things_to_avoid.md | Work mistake repeats 2+ times | Technical errors |
| contacts.md | External contact mentioned 3+ times or user requests | Internal colleagues |
| tracking.md | Item requires cross-session monitoring | Temporary states |

### Recording Workflow

1. Detect candidate → Check threshold
2. Filter → Work-related only
3. Show user → Ask for approval
4. Record → If approved

### things_to_avoid.md Format

**Trigger:** Work mistake repeats 2+ times (not technical errors)

**Entry Template:**
```markdown
## {Title}
- Context: {When/where}
- What went wrong: {What failed}
- Correction: {Right way}
- Count: {X}/2 [✓ VERIFIED when 2/2]
```

**Footer:** `Entries: {N} | Updated: {YYYY-MM-DD}`
