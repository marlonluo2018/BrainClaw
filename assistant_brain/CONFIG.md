# Configuration

## User
```json
{
  "name": "Marlon Luo",
  "email": "luomn@cn.ibm.com",
  "title": "Learning Consultant",
  "organization": "Learning & Knowledge(L&K)",
  "timezone": "Asia/Shanghai",
  "language": "English",
  "tone": "Friendly"
}
```

## Email Signature
```
Marlon
Learning Consultant
Learning & Knowledge(L&K) - IBM Consulting
Slack - @Marlon Luo
```

## Memory
- Max entries: 100
- Success threshold: 3
- Failure threshold: 2
- Expiry: 6 months

## Logs
- Max files in logs/: 5 (current.md + 4 date files)
- Overflow destination: logs/archive/
- Archive cleanup: manual (no auto-delete)

**Task Queue Format:**

*Checkbox:*
- `[ ]` Not completed
- `[⏳]` In progress
- `[x]` Completed

*Fields:*
| Field | Required | Values |
|-------|----------|--------|
| **Title** | Yes | Task title (bold) |
| Status | Yes | Not Started / In Progress / Pending Review / Waiting Info / Blocked / Completed |
| Priority | Yes | High / Medium / Low |
| Category | Yes | Email / Project / Admin / Meeting / Other |
| Due Time | Yes* | YYYY-MM-DD HH:MM or TBD (*ask user if not specified) |
| Contact | No | Related person |
| History | Yes | Record of all updates (date + time, source, content) |
| Note | No | Additional details |

*History Format:*
- `YYYY-MM-DD HH:MM | Source | Content`
- Source: Email / User / System / Meeting / Other

*Due Time:*
- Format: `YYYY-MM-DD HH:MM`
- If not specified: Ask user for due time
- If unknown: Use `TBD`

*Example:*
```markdown
- [ ] **Task title**
  - Status: In Progress
  - Priority: High
  - Category: Email
  - Due Time: 2026-03-25 17:00
  - Contact: John Doe
  - History:
    - 2026-03-20 14:30 | Email | Received request
    - 2026-03-21 09:15 | User | Need to review
  - Note: Additional details
```

## Backup
- Auto backup: enabled
- Retention: 7 days

## Workflow
- Quick mode: confirmation, thank you, brief
- Full mode: proposal, urgent, executive

## System
- OS: Windows 11
- Python command: `py -3`
- Shell: PowerShell

## Paths
- Windows: `%USERPROFILE%/assistant_brain/`
- Unix: `~/.assistant_brain/`
- Current: `./assistant_brain/`
