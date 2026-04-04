# Configuration

## User
```json
{
  "name": "Marlon Luo",
  "email": "luomn@cn.ibm.com",
  "title": "Learning Consultant",
  "organization": "Learning & Knowledge(L&K)",
  "language": "English",
  "tone": "Friendly",
  "timezone": "+08:00",
  "timezone_name": "Asia/Shanghai (UTC+8)"
}
```

## Email Signature
```
Marlon Luo
Learning Consultant
Learning & Knowledge(L&K) - IBM Consulting
Slack - @Marlon Luo
```

## System
- OS: Windows 11
- Python command: `py -3 full/path/script.py` (from project root, no `cd`, no `&&`)
- Shell: PowerShell
- PowerShell syntax: `;` for sequential, `-and` for conditional (no `&&`)
- Bash syntax: `&&` for conditional chaining
- Recent Events Window: 14 days (events older than this are archived to timeline)

## Tasks

### Directory Structure
```
tasks/
├── queue.md               # Active task queue (table view)
├── T001-xxx.md            # Active task details
└── history/               # Completed task archives
```

### File Naming
```
T{ID}-{keyword1}-{keyword2}.md
```
- **ID**: 3-digit incrementing number (T001, T002...)
- **Source**: Use `Last Task ID` from queue.md header (increment from this)
- **Keywords**: 2-4 keywords connected with `-`

### Status System
|| Symbol | Status | Description |
||--------|--------|-------------|
|| 📋 | Not Started | Needs action |
|| ⏳ | In Progress | Actively working on task |
|| 🔴 | Blocked | Waiting on external dependency / Unable to proceed |
|| ✅ | Completed | Move to history/ |

Flow: `📋 → ⏳ → (🔴 optional) → ✅ → history/`

**Note:** 🔴 Blocked status distinguishes tasks waiting on others (blocked) from tasks being actively worked (in progress).

### Priority System
|| Level | Meaning |
||-------|---------|
|| P1 | High |
|| P2 | Medium |
|| P3 | Low |

### Queue Format (tasks/queue.md)
List format (human-friendly):
```
## T{ID} {status} [{title}](T{ID}-xxx.md)
- **Created:** {YYYY-MM-DD}
- **Priority:** P{1-3}
- **Geo:** {Philippines/India/China/Singapore/APAC/Global}
- **Due:** {date or TBD}
- **Recurring Task ID:** {recurring task ID (e.g., R001)} (only if from recurring_tasks.md)
- **Tags:** `tag1`, `tag2`
```

### Task Template
```markdown
# T{ID}: {Title}

**Status:** 📋 Not Started
**Created:** {YYYY-MM-DD}
**Priority:** P{1-3}
**Category:** {Email/Slack/Meeting/Other}
**Geo:** {Philippines/India/China/Singapore/APAC/Global}
**Due:** {Date or TBD}
**Recurring Task ID:** {recurring task ID (e.g., R001)} (only if from recurring_tasks.md)

---

## Contacts
- **Requester:** Name (email)
- **Approver:** Name (email)

## Stakeholders

### RACI Matrix
*List stakeholders involved in this task and their role.*

| Stakeholder | Role |
|-------------|------|

**Legend:** R=Responsible, A=Accountable, C=Consulted, I=Informed

### Engagement Log

## Tags
`tag1`, `tag2`

---

## Timeline
- **{date}** [{source}]: {action}

---

## Current State
- [ ] Todo item 1
- [ ] Todo item 2

## Notes
Notes here
```

### Tag Guidelines
- Use SPECIFIC identifiers (names, IDs, codes)
- Avoid generic terms (certification, approval, email)
- Max 3 tags

## Paths
- Windows: `%USERPROFILE%/assistant_brain/`
- Unix: `~/.assistant_brain/`
- Current: `./assistant_brain/`

## Download Settings
- Default download path: `./downloads/` (project downloads folder)
- Email attachments: Save to project downloads folder
- Purpose: Downloaded files (Excel, PPT, etc.) can be directly processed by skills
