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

### Proactive Task Hints

**When:** After listing emails, checking calendar, or user mentions work items.

**Process:**
1. Extract keywords using keyword-extraction skill
2. Compare with tags in `tasks/queue.md`
3. Count only SPECIFIC identifier matches (names, emails, IDs, codes)
4. If 2+ matches → suggest update | If 0-1 match → suggest new task
5. Get user approval

### Add Tasks from Emails

**When:** Approval emails, delegation emails, direct action requests, urgent executive requests

**Criteria:** Email TO you, clear action request, requires your role/expertise, identifiable deliverable

**Skip:** FYI emails, general announcements, unclear discussion threads

### Priority Detection
- **P1 (High):** Urgent keywords, executive sender, deadline ≤ 2 days
- **P2 (Medium):** Normal work, deadline ≤ 1 week
- **P3 (Low):** FYI items, no strict deadline

### Email Display Format
**When summarizing emails after list/search operations:**
- ALWAYS include email reference numbers (e.g., #1, #2, #3)
- Format: Use "#X" prefix in summary text
- Purpose: Enable quick reference for follow-up actions (reply, forward, get details)
- Example: "#17 Manjula (LearnQuest) - Azure APIM clarifications"

### Source Tags
- Extract 2-3 UNIQUE identifiers using keyword-extraction skill
- Format: P1(Ticket) + P2(Names) + P3(TaskType) + P4(Keywords)
- Use SPECIFIC identifiers, avoid generic terms

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
