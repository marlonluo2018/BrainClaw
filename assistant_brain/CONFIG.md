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
| Keywords | No | 2-3 UNIQUE identifiers: Request IDs, full names, specific codes (NOT generic terms) |
| History | Yes | Record of all updates (date + time, source, content) |
| Note | No | Additional details |

*History Format:*
- `YYYY-MM-DD HH:MM | Source | Content`
- Source: Email / User / System / Meeting / Other

*Due Time:*
- Format: `YYYY-MM-DD HH:MM`
- If not specified: Ask user for due time
- If unknown: Use `TBD`

*Keywords Guidelines:*
- Use SPECIFIC identifiers only (Request IDs, unique names, exact codes)
- Avoid generic terms (certification, approval, email, project)
- 2-3 terms max, prioritize: Request ID > Full name > Unique identifier
- Test: Can you find ONLY this task's source with these keywords?

*Example:*
```markdown
- [ ] **Approve certification request for Ritu Arora**
  - Status: In Progress
  - Priority: High
  - Category: Email
  - Due Time: 2026-03-25 17:00
  - Contact: Ritu Arora
  - Keywords: CRT282456, Ritu Arora, Mulesoft Platform Architect I
  - History:
    - 2026-03-20 14:30 | Email | Received certification approval request
    - 2026-03-21 09:15 | User | Need to review and decide before deadline
  - Note: Request ID CRT282456, approve at https://lrt.yourlearning.ibm.com/requests/view/CRT282456
```

*Bad Keywords Examples (too generic):*
- ❌ "certification, approval, Salesforce" → finds hundreds of emails
- ❌ "AWS, CCP, voucher" → too many results
- ❌ "project, meeting, John" → useless for search

*Good Keywords Examples (specific & unique):*
- ✅ "CRT282911, Ashish Sah, Platform Developer II" → finds exact email
- ✅ "Req 11695, Informatica PowerCenter" → unique request
- ✅ "Brief ID 5021519, Citi double ILC" → specific project issue

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
