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
| Source Tag | No | 2-3 UNIQUE identifiers: Request IDs, full names, specific codes (NOT generic terms) |
| History | Yes | Record of all updates (date + time, source, content) |
| Note | No | Additional details |

*History Format:*
- `YYYY-MM-DD HH:MM | Source | Content`
- Source: Email / User / System / Meeting / Other

*Due Time:*
- Format: `YYYY-MM-DD HH:MM`
- If not specified: Ask user for due time
- If unknown: Use `TBD`

*Source Tag Guidelines:*
- Use SPECIFIC identifiers only (Request IDs, unique names, exact codes)
- Avoid generic terms (certification, approval, email, project)
- 2-3 terms max. See `SOUL.md` for detailed guidelines and examples.

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

## Download Settings
- Default download path: `./downloads/` (project downloads folder)
- Email attachments: Save to project downloads folder
- Purpose: Downloaded files (Excel, PPT, etc.) can be directly processed by skills
