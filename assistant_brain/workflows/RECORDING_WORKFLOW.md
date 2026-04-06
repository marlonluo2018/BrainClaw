# Recording Workflow

> Detailed procedures for recording events and memory

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

#### queue.md Recent Events (Configurable Window)

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
- **{YYYY-MM-DD}**: {icon} {description} [[{filename.md}]]
```

**Task File Timeline:**
```markdown
- **{YYYY-MM-DD HH:mm}** [{source}]: {detailed description}
```

### Query Flow

**User: "What did I do recently?"**
1. Read queue.md Recent Events
2. Show activities within Recent Events window (see CONFIG.md) (task creation/completion + non-task events)

**User: "What happened with T019?"**
1. Read queue.md Recent Events → find T019 creation/completion
2. Read T019.md Timeline → get detailed history
3. Combine information

### Archiving

- Keep events within Recent Events window (see CONFIG.md, default: 14 days) in queue.md
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